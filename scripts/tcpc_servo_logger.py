#!/usr/bin/env python3
"""Log TCPC work-config servo command/feedback pins to CSV."""

import argparse
import csv
import os
import signal
import sys
import time

import hal
import linuxcnc


AXES = ("x", "y", "z", "b", "c")
JOINTS = {
    "x": "0",
    "y": "1",
    "z": "2",
    "b": "3",
    "c": "4",
}


def pin(axis, suffix):
    return "joint.%s.%s" % (JOINTS[axis], suffix)


PIN_COLUMNS = []
for axis in AXES:
    PIN_COLUMNS.extend(
        [
            (axis + "_cmd", pin(axis, "motor-pos-cmd")),
            (axis + "_fb", pin(axis, "motor-pos-fb")),
            (axis + "_ferr", pin(axis, "f-error")),
            (axis + "_pid_error", "pid.%s.error" % axis),
            (axis + "_pid_output", "pid.%s.output" % axis),
            (axis + "_pid_saturated", "pid.%s.saturated" % axis),
        ]
    )

PIN_COLUMNS.extend(
    [
        ("b_ssi_invalid", "hm2_7i95.0.ssi.00.data-invalid"),
        ("c_ssi_invalid", "hm2_7i95.0.ssi.01.data-invalid"),
        ("c_unwrap_error", "c_ssi_unwrap.error"),
        ("tcpc_enabled", "headheadtwp.tcpc_enabled"),
        ("twp_motion_enabled", "headheadtwp.motion_enabled"),
        ("probe_input", "motion.probe-input"),
    ]
)


stop_requested = False


def stop_handler(signum, frame):
    global stop_requested
    stop_requested = True


def hal_value(name):
    try:
        return hal.get_value(name)
    except Exception:
        return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="", help="CSV output path")
    parser.add_argument("--rate", type=float, default=100.0, help="samples per second")
    parser.add_argument("--duration", type=float, default=0.0, help="seconds; 0 logs until interrupted")
    parser.add_argument("--label", default="", help="label stored in each row")
    args = parser.parse_args()

    if args.rate <= 0:
        parser.error("--rate must be positive")

    out = args.out
    if not out:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        out = "/tmp/tcpc_servo_logs/tcpc-servo-%s.csv" % stamp
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

    component = hal.component("tcpc_servo_logger_%d" % os.getpid())
    component.ready()

    status = linuxcnc.stat()
    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    start = time.monotonic()
    next_sample = start
    period = 1.0 / args.rate
    count = 0

    columns = [
        "sample",
        "time_s",
        "label",
        "task_state",
        "interp_state",
        "exec_state",
        "inpos",
        "enabled",
        "current_vel",
        "feedrate",
        "file",
    ] + [name for name, _ in PIN_COLUMNS]

    with open(out, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        while not stop_requested:
            now = time.monotonic()
            if now < next_sample:
                time.sleep(min(next_sample - now, 0.01))
                continue
            status.poll()
            row = [
                count,
                "%.6f" % (now - start),
                args.label,
                status.task_state,
                status.interp_state,
                status.exec_state,
                int(status.inpos),
                int(status.enabled),
                "%.9f" % status.current_vel,
                "%.9f" % status.feedrate,
                status.file,
            ]
            row.extend(hal_value(pin_name) for _, pin_name in PIN_COLUMNS)
            writer.writerow(row)
            count += 1
            next_sample += period
            if args.duration > 0 and now - start >= args.duration:
                break

    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
