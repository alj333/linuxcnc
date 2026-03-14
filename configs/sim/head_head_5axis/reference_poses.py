#!/usr/bin/env python3

"""Reference pose calculator for the head-head XYZBC simulation scaffold."""

import configparser
import math
from pathlib import Path


BASELINE = Path(__file__).with_name("geometry_baseline.ini")


def rotate_y(angle_deg, vec):
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    x, y, z = vec
    return (
        c * x + s * z,
        y,
        -s * x + c * z,
    )


def rotate_z(angle_deg, vec):
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    x, y, z = vec
    return (
        c * x - s * y,
        s * x + c * y,
        z,
    )


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
    c_frame = (
        c_to_b[0] + b_rotated[0],
        c_to_b[1] + b_rotated[1],
        c_to_b[2] + b_rotated[2],
    )
    return rotate_z(c_deg + c_zero, c_frame)


def fmt_vec(vec):
    return f"({vec[0]:8.3f}, {vec[1]:8.3f}, {vec[2]:8.3f})"


def main():
    c_to_b, b_to_tool, b_zero, c_zero = load_geometry()
    poses = [
        ("home", 0.0, 0.0),
        ("b+90", 90.0, 0.0),
        ("b-90", -90.0, 0.0),
        ("c+90", 0.0, 90.0),
        ("c-90", 0.0, -90.0),
        ("b+45 c+90", 45.0, 90.0),
        ("b-45 c+180", -45.0, 180.0),
    ]

    print(f"Geometry source: {BASELINE}")
    print(f"C->B        = {fmt_vec(c_to_b)}")
    print(f"B->tool     = {fmt_vec(b_to_tool)}")
    print(f"Zero offsets = (B={b_zero:.3f}, C={c_zero:.3f})")
    print("")
    print("Tool offset from C pivot center for reference poses:")
    print("  Pose            B(deg)   C(deg)   Offset XYZ (mm)")
    for label, b_deg, c_deg in poses:
        offset = tool_offset_world(b_deg, c_deg, c_to_b, b_to_tool, b_zero, c_zero)
        print(f"  {label:<12} {b_deg:7.1f}  {c_deg:7.1f}   {fmt_vec(offset)}")


if __name__ == "__main__":
    main()
