#!/usr/bin/env python3
"""Summarize max command/feedback and PID errors from a TCPC motion log."""

import argparse
import csv
import math
import sys


AXES = ("x", "y", "z", "b", "c")


def as_float(value):
    try:
        return float(value)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file")
    args = parser.parse_args()

    stats = {
        axis: {
            "max_cmd_fb": 0.0,
            "max_ferr": 0.0,
            "max_pid_error": 0.0,
            "max_pid_output": 0.0,
            "pid_saturated_samples": 0,
        }
        for axis in AXES
    }
    samples = 0
    invalid_counts = {"b_ssi_invalid": 0, "c_ssi_invalid": 0}

    with open(args.csv_file, newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            samples += 1
            for name in invalid_counts:
                if row.get(name) in ("1", "True", "TRUE", "true"):
                    invalid_counts[name] += 1
            for axis in AXES:
                cmd = as_float(row.get(axis + "_cmd"))
                fb = as_float(row.get(axis + "_fb"))
                ferr = as_float(row.get(axis + "_ferr"))
                pid_error = as_float(row.get(axis + "_pid_error"))
                pid_output = as_float(row.get(axis + "_pid_output"))
                if cmd is not None and fb is not None:
                    stats[axis]["max_cmd_fb"] = max(stats[axis]["max_cmd_fb"], abs(cmd - fb))
                if ferr is not None:
                    stats[axis]["max_ferr"] = max(stats[axis]["max_ferr"], abs(ferr))
                if pid_error is not None:
                    stats[axis]["max_pid_error"] = max(stats[axis]["max_pid_error"], abs(pid_error))
                if pid_output is not None:
                    stats[axis]["max_pid_output"] = max(stats[axis]["max_pid_output"], abs(pid_output))
                if row.get(axis + "_pid_saturated") in ("1", "True", "TRUE", "true"):
                    stats[axis]["pid_saturated_samples"] += 1

    print("samples,%d" % samples)
    for axis in AXES:
        values = stats[axis]
        print(
            "%s,max_cmd_fb=%.6f,max_ferr=%.6f,max_pid_error=%.6f,max_pid_output=%.6f,pid_saturated_samples=%d"
            % (
                axis.upper(),
                values["max_cmd_fb"],
                values["max_ferr"],
                values["max_pid_error"],
                values["max_pid_output"],
                values["pid_saturated_samples"],
            )
        )
    print("b_ssi_invalid_samples,%d" % invalid_counts["b_ssi_invalid"])
    print("c_ssi_invalid_samples,%d" % invalid_counts["c_ssi_invalid"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
