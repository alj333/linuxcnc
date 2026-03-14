#!/usr/bin/env python3

"""Tilted work-plane transform helpers for the head-head XYZBC simulation."""

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


def vec_scale(s, v):
    return (s * v[0], s * v[1], s * v[2])


def fmt_vec(vec):
    return f"({vec[0]:8.3f}, {vec[1]:8.3f}, {vec[2]:8.3f})"


def load_zero_offsets():
    cfg = configparser.ConfigParser()
    cfg.read(BASELINE)
    return (
        cfg.getfloat("CALIBRATION_DEFAULTS", "B_ZERO_OFFSET"),
        cfg.getfloat("CALIBRATION_DEFAULTS", "C_ZERO_OFFSET"),
    )


def plane_axes_world(b_deg, c_deg, b_zero=0.0, c_zero=0.0):
    b_eff = b_deg + b_zero
    c_eff = c_deg + c_zero
    x_axis = rotate_z(c_eff, rotate_y(b_eff, (1.0, 0.0, 0.0)))
    y_axis = rotate_z(c_eff, rotate_y(b_eff, (0.0, 1.0, 0.0)))
    z_axis = rotate_z(c_eff, rotate_y(b_eff, (0.0, 0.0, 1.0)))
    return x_axis, y_axis, z_axis


def twp_to_world(origin_xyz, local_xyz, b_deg, c_deg, b_zero=0.0, c_zero=0.0):
    plane_x, plane_y, plane_z = plane_axes_world(b_deg, c_deg, b_zero, c_zero)
    u, v, w = local_xyz
    world = origin_xyz
    world = vec_add(world, vec_scale(u, plane_x))
    world = vec_add(world, vec_scale(v, plane_y))
    world = vec_add(world, vec_scale(w, plane_z))
    return world


def main():
    parser = argparse.ArgumentParser(description="Transform a TWP-local point into world XYZ.")
    parser.add_argument("--origin-x", type=float, default=1500.0)
    parser.add_argument("--origin-y", type=float, default=850.0)
    parser.add_argument("--origin-z", type=float, default=-300.0)
    parser.add_argument("--local-u", type=float, default=0.0)
    parser.add_argument("--local-v", type=float, default=0.0)
    parser.add_argument("--local-w", type=float, default=0.0)
    parser.add_argument("--b", type=float, default=45.0)
    parser.add_argument("--c", type=float, default=90.0)
    args = parser.parse_args()

    b_zero, c_zero = load_zero_offsets()
    origin = (args.origin_x, args.origin_y, args.origin_z)
    local = (args.local_u, args.local_v, args.local_w)
    plane_x, plane_y, plane_z = plane_axes_world(args.b, args.c, b_zero, c_zero)
    world = twp_to_world(origin, local, args.b, args.c, b_zero, c_zero)

    print(f"Geometry source : {BASELINE}")
    print(f"Origin XYZ      : {fmt_vec(origin)}")
    print(f"Local UVW       : {fmt_vec(local)}")
    print(f"Plane BC        : ({args.b:.3f}, {args.c:.3f})")
    print(f"Plane X axis    : {fmt_vec(plane_x)}")
    print(f"Plane Y axis    : {fmt_vec(plane_y)}")
    print(f"Plane Z axis    : {fmt_vec(plane_z)}")
    print(f"World XYZ       : {fmt_vec(world)}")


if __name__ == "__main__":
    main()
