#!/usr/bin/env python3

"""Generate a simple tilted-work-plane validation program for the head-head sim."""

from pathlib import Path

from twp_transform import twp_to_world, load_zero_offsets


OUTFILE = Path(__file__).with_name("twp_test_sequence.ngc")


def line(text=""):
    return text.rstrip() + "\n"


def move(x, y, z, b, c, feed=1200.0, comment=None):
    words = [f"X{x:.3f}", f"Y{y:.3f}", f"Z{z:.3f}", f"B{b:.3f}", f"C{c:.3f}", f"F{feed:.1f}"]
    if comment:
        return line(f"G1 {' '.join(words)} ({comment})")
    return line(f"G1 {' '.join(words)}")


def pause(msg):
    return line(f"M0 ({msg})")


def generate():
    b_deg = 45.0
    c_deg = 90.0
    origin = (1500.0, 850.0, -300.0)
    local_points = [
        ("origin", (0.0, 0.0, 0.0)),
        ("u plus", (150.0, 0.0, 0.0)),
        ("u v corner", (150.0, 150.0, 0.0)),
        ("v plus", (0.0, 150.0, 0.0)),
        ("back origin", (0.0, 0.0, 0.0)),
        ("plane raise", (0.0, 0.0, 50.0)),
        ("back origin", (0.0, 0.0, 0.0)),
    ]

    b_zero, c_zero = load_zero_offsets()

    content = []
    content.append(line("%"))
    content.append(line("(Head-head tilted work-plane validation sequence)"))
    content.append(line("(Plane-local UVW path is transformed offline into world XYZ.)"))
    content.append(line("(B and C remain fixed while the path follows the tilted plane.)"))
    content.append(line("G17 G21 G40 G49 G54 G61 G80 G90 G94"))
    start_xyz = twp_to_world(origin, local_points[0][1], b_deg, c_deg, b_zero, c_zero)
    content.append(line(f"G0 X{start_xyz[0]:.3f} Y{start_xyz[1]:.3f} Z{start_xyz[2]:.3f} B{b_deg:.3f} C{c_deg:.3f}"))
    content.append(pause("Start TWP validation"))
    for label, local in local_points:
        world = twp_to_world(origin, local, b_deg, c_deg, b_zero, c_zero)
        content.append(move(world[0], world[1], world[2], b_deg, c_deg, comment=label))
        content.append(pause(f"Observe tilted-plane move for {label}"))
    content.append(line("M2"))
    content.append(line("%"))
    return "".join(content)


def main():
    OUTFILE.write_text(generate(), encoding="ascii")
    print(f"Wrote {OUTFILE}")


if __name__ == "__main__":
    main()
