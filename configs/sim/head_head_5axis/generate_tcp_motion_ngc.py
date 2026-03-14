#!/usr/bin/env python3

"""Generate a moving TCP validation program for the head-head XYZBC sim."""

from pathlib import Path


OUTFILE = Path(__file__).with_name("tcp_motion_sequence.ngc")


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
    moves = [
        (1500.0, 850.0, -300.0, 0.0,   0.0,   "start home"),
        (1650.0, 850.0, -300.0, 45.0,  0.0,   "linear X with B tilt"),
        (1650.0, 1000.0, -300.0, 45.0, 90.0,  "linear Y with C swivel"),
        (1500.0, 1000.0, -250.0, 0.0,  90.0,  "return X with Z raise"),
        (1500.0, 850.0, -250.0, -45.0, 180.0, "combined B/C rotation"),
        (1500.0, 850.0, -300.0, 0.0,   0.0,   "return home"),
    ]

    content = []
    content.append(line("%"))
    content.append(line("(Head-head moving TCP validation sequence)"))
    content.append(line("(The tool-tip path and the tool orientation both change.)"))
    content.append(line("(Use this after the fixed-tip TCP validation passes.)"))
    content.append(line("G17 G21 G40 G49 G54 G61 G80 G90 G94"))
    content.append(line("G0 X1500.000 Y850.000 Z-300.000 B0.000 C0.000"))
    content.append(pause("Start moving TCP validation"))
    for x, y, z, b, c, label in moves:
        content.append(move(x, y, z, b, c, comment=label))
        content.append(pause(f"Observe TCP motion for {label}"))
    content.append(line("M2"))
    content.append(line("%"))
    return "".join(content)


def main():
    OUTFILE.write_text(generate(), encoding="ascii")
    print(f"Wrote {OUTFILE}")


if __name__ == "__main__":
    main()
