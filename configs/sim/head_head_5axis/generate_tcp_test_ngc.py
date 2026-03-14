#!/usr/bin/env python3

"""Generate a simple TCP validation program for the head-head XYZBC sim."""

from pathlib import Path


OUTFILE = Path(__file__).with_name("tcp_test_sequence.ngc")


def line(text=""):
    return text.rstrip() + "\n"


def move(x, y, z, b, c, feed=None, comment=None):
    words = [f"X{x:.3f}", f"Y{y:.3f}", f"Z{z:.3f}", f"B{b:.3f}", f"C{c:.3f}"]
    if feed is not None:
        words.append(f"F{feed:.1f}")
    prefix = "G1"
    body = " ".join(words)
    if comment:
        return line(f"{prefix} {body} ({comment})")
    return line(f"{prefix} {body}")


def pause(msg):
    return line(f"M0 ({msg})")


def generate():
    # Fixed tool-tip target inside the nominal travel envelope.
    x_tip = 1500.0
    y_tip = 850.0
    z_tip = -300.0

    poses = [
        ("home", 0.0, 0.0),
        ("b plus 45", 45.0, 0.0),
        ("b plus 90", 90.0, 0.0),
        ("back to home", 0.0, 0.0),
        ("c plus 90", 0.0, 90.0),
        ("c minus 90", 0.0, -90.0),
        ("back to home", 0.0, 0.0),
        ("combined b45 c90", 45.0, 90.0),
        ("combined b-45 c180", -45.0, 180.0),
        ("return home", 0.0, 0.0),
    ]

    content = []
    content.append(line("%"))
    content.append(line("(Head-head TCP validation sequence)"))
    content.append(line("(The XYZ tool-tip target is intentionally held constant.)"))
    content.append(line("(If inverse kinematics is correct, the visual tool tip should stay fixed while B/C change.)"))
    content.append(line("G17 G21 G40 G49 G54 G61 G80 G90 G94"))
    content.append(line("G0 X1500.000 Y850.000 Z-300.000 B0.000 C0.000"))
    content.append(pause("Start TCP validation at home orientation"))
    for label, b_deg, c_deg in poses:
        content.append(move(x_tip, y_tip, z_tip, b_deg, c_deg, feed=1200.0, comment=label))
        content.append(pause(f"Observe tool tip for {label}"))
    content.append(line("M2"))
    content.append(line("%"))
    return "".join(content)


def main():
    OUTFILE.write_text(generate(), encoding="ascii")
    print(f"Wrote {OUTFILE}")


if __name__ == "__main__":
    main()
