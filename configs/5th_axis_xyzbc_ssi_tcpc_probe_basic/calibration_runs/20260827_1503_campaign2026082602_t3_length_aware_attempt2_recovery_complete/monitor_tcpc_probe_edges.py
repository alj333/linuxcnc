#!/usr/bin/env python3
"""Timestamp sticky TCPC probe-edge counters without commanding LinuxCNC."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import signal
import sys
import time
from pathlib import Path

import hal
import linuxcnc


HAL_FIELDS = {
    "raw_count": "counter.0.counts",
    "mux_count": "counter.1.counts",
    "gated_count": "counter.2.counts",
    "raw": "t_probe-in",
    "mux": "probe-mux",
    "gate_enable": "tcpc-probe-gate-enable",
    "ignore_active": "tcpc-probe-ignore-active",
    "abnormal_level": "tcpc-probe-abnormal-level",
    "fault_event": "tcpc-probe-fault-pause",
    "gated": "tcpc-probe-gated",
    "motion_probe_input": "motion.probe-input",
    "motion_type": "motion.motion-type",
}

STOP = False


def stop(_signum: int, _frame: object) -> None:
    global STOP
    STOP = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--sample-hz", type=float, default=100.0)
    parser.add_argument("--heartbeat", type=float, default=1.0)
    parser.add_argument("--pin-wait-timeout", type=float, default=30.0)
    parser.add_argument("--pid", type=int, help="exit when this milltask PID exits")
    parser.add_argument(
        "--component-name",
        default=f"tcpc_probe_edge_monitor_{os.getpid()}",
        help="HAL component name used by loadusr -Wn",
    )
    args = parser.parse_args()
    if args.sample_hz <= 0 or args.heartbeat <= 0 or args.pin_wait_timeout <= 0:
        parser.error("sample-hz, heartbeat, and pin-wait-timeout must be positive")
    return args


def process_alive(pid: int | None) -> bool:
    return pid is None or Path(f"/proc/{pid}").exists()


def hal_snapshot() -> dict[str, int]:
    values: dict[str, int] = {}
    for field, pin in HAL_FIELDS.items():
        value = hal.get_value(pin)
        values[field] = int(value)
    return values


def main() -> int:
    args = parse_args()
    component = hal.component(args.component_name)
    stat = linuxcnc.stat()
    # TWOPASS starts loadusr components before it loads realtime components.
    # Become ready first so HAL loading can continue, then wait for the pins.
    component.ready()

    pin_deadline = time.monotonic() + args.pin_wait_timeout
    while True:
        try:
            first = hal_snapshot()
            break
        except Exception as exc:
            if time.monotonic() >= pin_deadline:
                print(f"PRECONDITION FAIL: {exc}", file=sys.stderr)
                component.exit()
                return 2
            time.sleep(0.05)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "epoch",
        "iso_time",
        "monotonic",
        "event",
        *HAL_FIELDS,
        "task_state",
        "task_mode",
        "interp_state",
        "exec_state",
        "current_line",
        "motion_line",
        "probe_val",
        "inpos",
        "current_vel",
        "x",
        "y",
        "z",
        "b",
        "c",
        "file",
    ]

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    interval = 1.0 / args.sample_hz
    next_sample = time.monotonic()
    next_heartbeat = next_sample
    previous = first

    with args.output.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()

        while not STOP and process_alive(args.pid):
            now = time.monotonic()
            if now < next_sample:
                time.sleep(next_sample - now)
                continue
            next_sample += interval
            if now - next_sample > interval:
                next_sample = now + interval

            values = hal_snapshot()
            changed = [name for name in HAL_FIELDS if values[name] != previous[name]]
            heartbeat = now >= next_heartbeat
            if not changed and not heartbeat:
                continue

            stat.poll()
            epoch = time.time()
            position = stat.position
            event = "+".join(changed) if changed else "heartbeat"
            row: dict[str, object] = {
                "epoch": f"{epoch:.6f}",
                "iso_time": dt.datetime.fromtimestamp(epoch).astimezone().isoformat(
                    timespec="milliseconds"
                ),
                "monotonic": f"{now:.6f}",
                "event": event,
                **values,
                "task_state": stat.task_state,
                "task_mode": stat.task_mode,
                "interp_state": stat.interp_state,
                "exec_state": stat.exec_state,
                "current_line": stat.current_line,
                "motion_line": stat.motion_line,
                "probe_val": stat.probe_val,
                "inpos": int(stat.inpos),
                "current_vel": f"{stat.current_vel:.9f}",
                "x": f"{position[0]:.9f}",
                "y": f"{position[1]:.9f}",
                "z": f"{position[2]:.9f}",
                "b": f"{position[4]:.9f}",
                "c": f"{position[5]:.9f}",
                "file": stat.file,
            }
            writer.writerow(row)
            handle.flush()
            if changed:
                print(
                    f"{row['iso_time']} {event} "
                    f"raw/mux/gated={values['raw_count']}/"
                    f"{values['mux_count']}/{values['gated_count']}",
                    flush=True,
                )
            previous = values
            if heartbeat:
                next_heartbeat = now + args.heartbeat

    component.exit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
