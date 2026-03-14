#!/usr/bin/env python3

"""Nominal TCP compensation calculator for the head-head XYZBC model."""

import argparse
import configparser
import math
from pathlib import Path


BASELINE = Path(__file__).with_name("geometry_baseline.ini")


def rotate_y(angle_deg, vec):
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    x, y, z = vec
    return (c * x + s * z, y, -s * x + c * z)


def rotate_z(angle_deg, vec):
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    x, y, z = vec
    return (c * x - s * y, s * x + c * y, z)


def vec_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def fmt_vec(vec):
    return f"({vec[0]:8.3f}, {vec[1]:8.3f}, {vec[2]:8.3f})"


def load_geometry():
    cfg = configparser.ConfigParser()
    cfg.read(BASELINE)
    c_to_b = (
        cfg.getfloat("GEOMETRY_NOMINAL", "C_TO_B_X"),
        cfg.getfloat("GEOMETRY_NOMINAL", "C_TO_B_Y"),
        cfg.getfloat("GEOMETRY_NOMINAL", "C_TO_B_Z"),
    )
    b_to_tool = (
        cfg.getfloat("GEOMETRY_NOMINAL", "B_TO_SPINDLE_X"),
        cfg.getfloat("GEOMETRY_NOMINAL", "B_TO_SPINDLE_Y"),
        cfg.getfloat("GEOMETRY_NOMINAL", "B_TO_SPINDLE_Z"),
    )
    b_zero = cfg.getfloat("CALIBRATION_DEFAULTS", "B_ZERO_OFFSET")
    c_zero = cfg.getfloat("CALIBRATION_DEFAULTS", "C_ZERO_OFFSET")
    return c_to_b, b_to_tool, b_zero, c_zero


def tool_offset_world(b_deg, c_deg, c_to_b, b_to_tool, b_zero, c_zero):
    b_rotated = rotate_y(b_deg + b_zero, b_to_tool)
    c_frame = vec_add(c_to_b, b_rotated)
    return rotate_z(c_deg + c_zero, c_frame)


def tool_vector_world(b_deg, c_deg, b_zero, c_zero):
    tool_axis = (0.0, 0.0, -1.0)
    return rotate_z(c_deg + c_zero, rotate_y(b_deg + b_zero, tool_axis))


def main():
    parser = argparse.ArgumentParser(description="Compute nominal TCP XYZ compensation for a B/C move.")
    parser.add_argument("--start-b", type=float, default=0.0)
    parser.add_argument("--start-c", type=float, default=0.0)
    parser.add_argument("--end-b", type=float, default=0.0)
    parser.add_argument("--end-c", type=float, default=0.0)
    args = parser.parse_args()

    c_to_b, b_to_tool, b_zero, c_zero = load_geometry()
    start_offset = tool_offset_world(args.start_b, args.start_c, c_to_b, b_to_tool, b_zero, c_zero)
    end_offset = tool_offset_world(args.end_b, args.end_c, c_to_b, b_to_tool, b_zero, c_zero)
    delta_xyz = vec_sub(start_offset, end_offset)
    start_vec = tool_vector_world(args.start_b, args.start_c, b_zero, c_zero)
    end_vec = tool_vector_world(args.end_b, args.end_c, b_zero, c_zero)

    print(f"Geometry source : {BASELINE}")
    print(f"Start BC        : ({args.start_b:.3f}, {args.start_c:.3f})")
    print(f"End BC          : ({args.end_b:.3f}, {args.end_c:.3f})")
    print(f"Start offset    : {fmt_vec(start_offset)}")
    print(f"End offset      : {fmt_vec(end_offset)}")
    print(f"TCP delta XYZ   : {fmt_vec(delta_xyz)}")
    print(f"Start tool axis : {fmt_vec(start_vec)}")
    print(f"End tool axis   : {fmt_vec(end_vec)}")
    print("")
    print("Interpretation: add TCP delta XYZ to the pivot-center XYZ command")
    print("when changing from start BC to end BC while keeping the tool tip fixed.")


if __name__ == "__main__":
    main()
