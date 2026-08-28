#!/usr/bin/env python3
"""Read-only electrical qualification for the TCPC wireless probe."""

from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from pathlib import Path

import hal
import linuxcnc


SIGNALS = (
    "toolset-in",
    "t_probe-in",
    "probe-mux",
    "tcpc-probe-gate-enable",
    "tcpc-probe-ignore-active",
    "tcpc-probe-abnormal-level",
    "tcpc-probe-fault-pause",
    "tcpc-probe-gated",
    "motion.probe-input",
    "motion.motion-enabled",
)
FAULT_TIME_LEFT = "tcpc_probe_fault_pause.time-left"
FORBIDDEN_ACTIVE = (
    "tcpc-probe-gate-enable",
    "tcpc-probe-ignore-active",
    "tcpc-probe-gated",
    "motion.probe-input",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Observe probe/HAL state without commanding LinuxCNC. Exit 0 only "
            "when the requested touch count and all no-motion guards pass."
        )
    )
    parser.add_argument("--duration", type=float, required=True, help="test duration in seconds")
    parser.add_argument("--expected-touches", type=int, default=0)
    parser.add_argument("--sample-hz", type=float, default=10.0)
    parser.add_argument("--min-touch-gap", type=float, default=0.0)
    parser.add_argument("--min-touch-width", type=float, default=0.20)
    parser.add_argument("--max-touch-width", type=float, default=3.0)
    parser.add_argument(
        "--allow-machine-on",
        action="store_true",
        help="permit task_state ON for the final powered-idle soak",
    )
    parser.add_argument("--output", type=Path, help="optional sample CSV path")
    args = parser.parse_args()
    if args.duration <= 0 or args.sample_hz <= 0:
        parser.error("duration and sample-hz must be positive")
    if args.expected_touches < 0:
        parser.error("expected-touches cannot be negative")
    if args.min_touch_gap < 0 or args.min_touch_width < 0:
        parser.error("touch timing values cannot be negative")
    if args.max_touch_width <= args.min_touch_width:
        parser.error("max-touch-width must exceed min-touch-width")
    return args


def bool_value(name: str) -> bool:
    return bool(hal.get_value(name))


def snapshot(stat: linuxcnc.stat) -> dict[str, object]:
    stat.poll()
    values: dict[str, object] = {name: bool_value(name) for name in SIGNALS}
    values[FAULT_TIME_LEFT] = float(hal.get_value(FAULT_TIME_LEFT))
    values["task_state"] = int(stat.task_state)
    values["task_mode"] = int(stat.task_mode)
    values["interp_state"] = int(stat.interp_state)
    values["queue"] = int(stat.queue)
    values["inpos"] = bool(stat.inpos)
    values["current_vel"] = float(stat.current_vel)
    values["motion_type"] = int(stat.motion_type)
    values["file"] = stat.file
    return values


def preflight(values: dict[str, object], allow_machine_on: bool) -> list[str]:
    failures: list[str] = []
    if values["interp_state"] != linuxcnc.INTERP_IDLE:
        failures.append("interpreter is not IDLE")
    if values["queue"] != 0:
        failures.append("motion queue is not empty")
    if not values["inpos"]:
        failures.append("machine is not in position")
    if abs(float(values["current_vel"])) > 1e-9:
        failures.append("machine velocity is not zero")
    if values["motion_type"] != 0:
        failures.append("motion type is not idle")
    if not allow_machine_on and values["task_state"] == linuxcnc.STATE_ON:
        failures.append("machine is enabled; apply LinuxCNC E-stop/disable")
    if not allow_machine_on and values["motion.motion-enabled"]:
        failures.append("motion is enabled")
    for name in SIGNALS[:-1]:
        if values[name]:
            failures.append(f"{name} is active at test start")
    if float(values[FAULT_TIME_LEFT]) > 0.001:
        failures.append("probe event latch has not expired")
    return failures


def main() -> int:
    args = parse_args()
    component = hal.component(f"tcpc_probe_qual_{int(time.time())}")
    component.ready()
    stat = linuxcnc.stat()
    output_handle = None

    try:
        first = snapshot(stat)
        failures = preflight(first, args.allow_machine_on)
        if failures:
            for failure in failures:
                print(f"PRECONDITION FAIL: {failure}", flush=True)
            return 2

        fieldnames = ["elapsed"] + list(SIGNALS) + [
            FAULT_TIME_LEFT,
            "task_state",
            "task_mode",
            "interp_state",
            "queue",
            "inpos",
            "current_vel",
            "motion_type",
            "file",
        ]
        writer = None
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            output_handle = args.output.open("w", newline="", encoding="ascii")
            writer = csv.DictWriter(output_handle, fieldnames=fieldnames)
            writer.writeheader()

        print(
            f"READY duration={args.duration:.1f}s expected_touches={args.expected_touches} "
            f"machine_on_allowed={args.allow_machine_on}",
            flush=True,
        )

        interval = 1.0 / args.sample_hz
        started = time.monotonic()
        deadline = started + args.duration
        previous = first
        previous_fault_time = float(first[FAULT_TIME_LEFT])
        touch_started: float | None = None
        touch_starts: list[float] = []
        touch_widths: list[float] = []
        latch_events: list[float] = []
        runtime_failures: list[str] = []
        next_progress = started + 10.0

        while True:
            now = time.monotonic()
            if now >= deadline:
                break
            values = snapshot(stat)
            elapsed = now - started

            if writer:
                row = {"elapsed": f"{elapsed:.6f}"}
                row.update(values)
                writer.writerow(row)

            if values["interp_state"] != linuxcnc.INTERP_IDLE:
                runtime_failures.append(f"{elapsed:.3f}s interpreter left IDLE")
                break
            if values["queue"] != 0 or not values["inpos"]:
                runtime_failures.append(f"{elapsed:.3f}s queue/in-position state changed")
                break
            if abs(float(values["current_vel"])) > 1e-9 or values["motion_type"] != 0:
                runtime_failures.append(f"{elapsed:.3f}s motion was detected")
                break
            if not args.allow_machine_on and (
                values["task_state"] == linuxcnc.STATE_ON or values["motion.motion-enabled"]
            ):
                runtime_failures.append(f"{elapsed:.3f}s machine/motion became enabled")
                break

            for name in FORBIDDEN_ACTIVE:
                if values[name]:
                    runtime_failures.append(f"{elapsed:.3f}s forbidden {name} became active")
                    break
            if runtime_failures:
                break

            raw = bool(values["t_probe-in"])
            prior_raw = bool(previous["t_probe-in"])
            if raw and not prior_raw:
                touch_started = elapsed
                touch_starts.append(elapsed)
                print(f"EDGE {elapsed:.3f}s t_probe-in RISE", flush=True)
            elif not raw and prior_raw:
                if touch_started is None:
                    runtime_failures.append(f"{elapsed:.3f}s raw falling edge without recorded rise")
                    break
                width = elapsed - touch_started
                touch_widths.append(width)
                touch_started = None
                print(f"EDGE {elapsed:.3f}s t_probe-in FALL width={width:.3f}s", flush=True)

            if bool(values["probe-mux"]) != raw or bool(values["toolset-in"]):
                runtime_failures.append(
                    f"{elapsed:.3f}s source mismatch: raw={raw} "
                    f"mux={values['probe-mux']} toolsetter={values['toolset-in']}"
                )
                break

            fault_time = float(values[FAULT_TIME_LEFT])
            if fault_time > previous_fault_time + max(0.02, 0.25 * interval):
                latch_events.append(elapsed)
                print(f"LATCH {elapsed:.3f}s time-left reset to {fault_time:.3f}s", flush=True)
            previous_fault_time = fault_time
            previous = values

            if now >= next_progress:
                print(
                    f"PROGRESS {elapsed:.1f}s touches={len(touch_starts)} "
                    f"raw={int(raw)} latch={fault_time:.3f}s",
                    flush=True,
                )
                next_progress += 10.0

            sleep_for = started + (math.floor(elapsed / interval) + 1) * interval - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)

        final = snapshot(stat)
        final_elapsed = time.monotonic() - started
        if writer:
            row = {"elapsed": f"{final_elapsed:.6f}"}
            row.update(final)
            writer.writerow(row)

        if touch_started is not None:
            runtime_failures.append("test ended while t_probe-in remained active")
        if len(touch_starts) != args.expected_touches:
            runtime_failures.append(
                f"expected {args.expected_touches} touches but observed {len(touch_starts)}"
            )
        if len(touch_widths) != len(touch_starts):
            runtime_failures.append("not every touch produced a release edge")
        if len(latch_events) != len(touch_starts):
            runtime_failures.append(
                f"observed {len(latch_events)} event-latch resets for "
                f"{len(touch_starts)} raw rises"
            )
        for index, (touch_time, latch_time) in enumerate(
            zip(touch_starts, latch_events), start=1
        ):
            if abs(touch_time - latch_time) > 2.0 / args.sample_hz:
                runtime_failures.append(
                    f"touch {index} and event latch differ by "
                    f"{abs(touch_time - latch_time):.3f}s"
                )
        for index, width in enumerate(touch_widths, start=1):
            if not args.min_touch_width <= width <= args.max_touch_width:
                runtime_failures.append(
                    f"touch {index} width {width:.3f}s outside "
                    f"{args.min_touch_width:.3f}-{args.max_touch_width:.3f}s"
                )
        for index, (left, right) in enumerate(zip(touch_starts, touch_starts[1:]), start=2):
            gap = right - left
            if gap < args.min_touch_gap:
                runtime_failures.append(
                    f"touch {index} started only {gap:.3f}s after the prior touch"
                )
        for name in FORBIDDEN_ACTIVE:
            if final[name]:
                runtime_failures.append(f"final {name} is active")
        if final["t_probe-in"] or final["probe-mux"] or final["toolset-in"]:
            runtime_failures.append("probe/toolsetter input is active at test end")
        if final["tcpc-probe-fault-pause"] or float(final[FAULT_TIME_LEFT]) > 0.001:
            runtime_failures.append("probe event latch is active at test end")

        if runtime_failures:
            for failure in runtime_failures:
                print(f"FAIL: {failure}", flush=True)
            return 1

        print(
            f"PASS duration={final_elapsed:.1f}s touches={len(touch_starts)} "
            f"widths={','.join(f'{width:.3f}' for width in touch_widths) or 'none'}",
            flush=True,
        )
        return 0
    finally:
        if output_handle:
            output_handle.close()
        component.exit()


if __name__ == "__main__":
    sys.exit(main())
