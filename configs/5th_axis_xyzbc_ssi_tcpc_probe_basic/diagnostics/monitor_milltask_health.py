#!/usr/bin/env python3

"""Passively record milltask process and LinuxCNC heartbeat state."""

import argparse
import csv
import os
from pathlib import Path
import time

import linuxcnc


def process_state(pid):
    try:
        fields = Path(f"/proc/{pid}/stat").read_text(encoding="ascii").split()
    except (FileNotFoundError, ProcessLookupError):
        return False, "missing", "", "", "", "", ""
    if len(fields) < 22:
        return True, "invalid", "", "", "", "", ""
    voluntary = ""
    nonvoluntary = ""
    try:
        for line in Path(f"/proc/{pid}/status").read_text(encoding="ascii").splitlines():
            if line.startswith("voluntary_ctxt_switches:"):
                voluntary = line.split(":", 1)[1].strip()
            elif line.startswith("nonvoluntary_ctxt_switches:"):
                nonvoluntary = line.split(":", 1)[1].strip()
    except (FileNotFoundError, ProcessLookupError):
        pass
    return (
        fields[2] != "Z",
        fields[2],
        fields[21],
        fields[13],
        fields[14],
        voluntary,
        nonvoluntary,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    status = linuxcnc.stat()
    fields = [
        "epoch",
        "monotonic",
        "pid_alive",
        "proc_state",
        "proc_start_ticks",
        "proc_utime_ticks",
        "proc_stime_ticks",
        "proc_voluntary_ctxt_switches",
        "proc_nonvoluntary_ctxt_switches",
        "poll_ok",
        "echo_serial",
        "task_state",
        "task_mode",
        "interp_state",
        "exec_state",
        "enabled",
        "estop",
        "inpos",
        "current_velocity",
        "selected_file",
    ]

    with args.output.open("w", newline="", encoding="ascii", buffering=1) as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        while True:
            (
                alive,
                proc_state,
                start_ticks,
                utime_ticks,
                stime_ticks,
                voluntary_ctxt,
                nonvoluntary_ctxt,
            ) = process_state(args.pid)
            row = {
                "epoch": f"{time.time():.6f}",
                "monotonic": f"{time.monotonic():.6f}",
                "pid_alive": int(alive),
                "proc_state": proc_state,
                "proc_start_ticks": start_ticks,
                "proc_utime_ticks": utime_ticks,
                "proc_stime_ticks": stime_ticks,
                "proc_voluntary_ctxt_switches": voluntary_ctxt,
                "proc_nonvoluntary_ctxt_switches": nonvoluntary_ctxt,
                "poll_ok": 0,
                "echo_serial": "",
                "task_state": "",
                "task_mode": "",
                "interp_state": "",
                "exec_state": "",
                "enabled": "",
                "estop": "",
                "inpos": "",
                "current_velocity": "",
                "selected_file": "",
            }
            try:
                status.poll()
                row.update({
                    "poll_ok": 1,
                    "echo_serial": status.echo_serial_number,
                    "task_state": status.task_state,
                    "task_mode": status.task_mode,
                    "interp_state": status.interp_state,
                    "exec_state": status.exec_state,
                    "enabled": int(bool(status.enabled)),
                    "estop": int(bool(status.estop)),
                    "inpos": int(bool(status.inpos)),
                    "current_velocity": f"{status.current_vel:.9f}",
                    "selected_file": status.file,
                })
            except Exception:
                pass
            writer.writerow(row)
            stream.flush()
            os.fsync(stream.fileno())
            if not alive:
                break
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
