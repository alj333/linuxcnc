#!/usr/bin/env python3
"""Fail-closed structural review for MotionX Fusion-generated NGC files."""

import argparse
import math
import re
import sys
from pathlib import Path


WORD_RE = re.compile(r"([A-Z])\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))", re.IGNORECASE)
SEQUENCE_RE = re.compile(r"^/?\s*N\d+\s*", re.IGNORECASE)


class ValidationError(RuntimeError):
    pass


def strip_comments(line):
    result = []
    depth = 0
    for char in line.split(";", 1)[0]:
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif not depth:
            result.append(char)
    return "".join(result).strip()


def executable_blocks(text):
    blocks = []
    for line_number, raw in enumerate(text.splitlines(), 1):
        code = strip_comments(raw).upper().strip()
        if not code or code == "%":
            continue
        code = SEQUENCE_RE.sub("", code).strip()
        if code:
            blocks.append((line_number, code, [(letter.upper(), float(value)) for letter, value in WORD_RE.findall(code)]))
    return blocks


def codes(words, letter):
    return [value for word_letter, value in words if word_letter == letter]


def has_code(words, letter, value):
    return any(abs(candidate - value) < 1e-6 for candidate in codes(words, letter))


def has_word(words, letter):
    return any(word_letter == letter for word_letter, _ in words)


def word_value(words, letter):
    values = codes(words, letter)
    return values[-1] if values else None


def fail(line_number, message):
    raise ValidationError(f"line {line_number}: {message}")


def matrix_multiply(left, right):
    return tuple(
        tuple(sum(left[row][index] * right[index][column] for index in range(3)) for column in range(3))
        for row in range(3)
    )


def rotation_x(angle_deg):
    angle = math.radians(angle_deg)
    cosine, sine = math.cos(angle), math.sin(angle)
    return ((1.0, 0.0, 0.0), (0.0, cosine, -sine), (0.0, sine, cosine))


def rotation_y(angle_deg):
    angle = math.radians(angle_deg)
    cosine, sine = math.cos(angle), math.sin(angle)
    return ((cosine, 0.0, sine), (0.0, 1.0, 0.0), (-sine, 0.0, cosine))


def rotation_z(angle_deg):
    angle = math.radians(angle_deg)
    cosine, sine = math.cos(angle), math.sin(angle)
    return ((cosine, -sine, 0.0), (sine, cosine, 0.0), (0.0, 0.0, 1.0))


def matrix_column(matrix, column):
    return tuple(matrix[row][column] for row in range(3))


def dot(left, right):
    return sum(a * b for a, b in zip(left, right))


def validate_orientation(line_number, words, reached_b, reached_c):
    euler = matrix_multiply(
        matrix_multiply(rotation_z(word_value(words, "I")), rotation_x(word_value(words, "J"))),
        rotation_z(word_value(words, "K")),
    )
    machine = matrix_multiply(rotation_z(reached_c), rotation_y(reached_b))
    normal_dot = max(-1.0, min(1.0, dot(matrix_column(euler, 2), matrix_column(machine, 2))))
    normal_error = math.degrees(math.acos(normal_dot))
    if normal_error > 0.1001:
        fail(line_number, f"I/J/K normal differs from reached B/C by {normal_error:.6f} degrees")


def validate_text(text, source="<memory>"):
    blocks = executable_blocks(text)
    tlo_active = False
    tcpc_active = False
    twp_defined = False
    twp_active = False
    reached_b = None
    reached_c = None
    rotary_line = None
    world_retract_after_rotary = False
    twp_count = 0
    tcpc_count = 0

    for index, (line_number, code, words) in enumerate(blocks):
        g_codes = codes(words, "G")
        m_codes = codes(words, "M")

        if has_code(words, "G", 68.2):
            if twp_defined or twp_active:
                fail(line_number, "nested G68.2")
            if tcpc_active:
                fail(line_number, "G68.2 appears while public TCPC is active")
            if not tlo_active:
                fail(line_number, "ordinary G43 H is not active before G68.2")
            if reached_b is None or reached_c is None or rotary_line is None:
                fail(line_number, "no complete B/C world preposition precedes G68.2")
            if abs(reached_b) > 30.001:
                fail(line_number, f"B{reached_b:g} exceeds the commissioned TWP envelope")
            if abs(reached_c) > 359.001:
                fail(line_number, f"C{reached_c:g} exceeds the machine branch limit")
            if not world_retract_after_rotary:
                fail(line_number, "no world/machine Z retract follows the B/C preposition")
            for triplet in (("X", "Y", "Z"), ("I", "J", "K")):
                if not all(has_word(words, letter) for letter in triplet):
                    fail(line_number, f"G68.2 is missing the complete {''.join(triplet)} triplet")
            if any(has_word(words, letter) for letter in ("A", "B", "C", "R")):
                fail(line_number, "Fusion G68.2 must use X/Y/Z/I/J/K without A/B/C/R")
            validate_orientation(line_number, words, reached_b, reached_c)
            if index + 1 >= len(blocks):
                fail(line_number, "G68.2 is not followed by G53.1")
            next_line, _, next_words = blocks[index + 1]
            if len(next_words) != 1 or not has_code(next_words, "G", 53.1):
                fail(next_line, "G53.1 must be the separate block immediately after G68.2")
            twp_defined = True
            world_retract_after_rotary = False
            continue

        if has_code(words, "G", 53.1):
            if not twp_defined or twp_active:
                fail(line_number, "G53.1 has no pending G68.2 definition")
            if len(words) != 1:
                fail(line_number, "G53.1 must be on a separate block")
            twp_active = True
            twp_count += 1
            continue

        if has_code(words, "G", 69):
            if not twp_defined:
                fail(line_number, "G69 has no post-tracked TWP to cancel")
            if index == 0:
                fail(line_number, "G69 has no preceding local clearance")
            _, _, previous_words = blocks[index - 1]
            if not has_code(previous_words, "G", 0) or not has_word(previous_words, "Z"):
                fail(line_number, "G69 is not immediately preceded by an explicit local G0 Z clearance")
            twp_defined = False
            twp_active = False
            rotary_line = None
            continue

        if twp_defined and not twp_active:
            fail(line_number, "a block intervenes between G68.2 and G53.1")

        if twp_active:
            if any(has_word(words, letter) for letter in ("A", "B", "C", "U", "V", "W")):
                fail(line_number, "rotary/auxiliary-axis word appears inside active TWP")
            allowed_g = {0.0, 1.0, 4.0, 40.0, 80.0, 90.0, 91.0, 94.0}
            unsupported = [value for value in g_codes if value not in allowed_g]
            if unsupported:
                fail(line_number, f"unsupported active-TWP G code(s): {unsupported}")
            if m_codes or has_word(words, "T"):
                fail(line_number, "M/T machine-state command appears inside active TWP")
            continue

        if has_code(words, "G", 43.4):
            if not tlo_active:
                fail(line_number, "G43.4 appears without ordinary G43 H")
            if tcpc_active:
                fail(line_number, "nested G43.4")
            tcpc_active = True
            tcpc_count += 1
            continue

        if has_code(words, "G", 49.1):
            if not tcpc_active:
                fail(line_number, "G49.1 appears without active public TCPC")
            tcpc_active = False
            rotary_line = None
            continue

        if has_code(words, "G", 43.0):
            if tcpc_active:
                fail(line_number, "ordinary G43 changes while public TCPC is active")
            if not has_word(words, "H") or word_value(words, "H") <= 0:
                fail(line_number, "ordinary G43 requires a positive H number")
            tlo_active = True

        if has_code(words, "G", 49.0):
            if tcpc_active:
                fail(line_number, "plain G49 is used instead of G49.1 for TCPC")
            tlo_active = False

        if has_word(words, "B") or has_word(words, "C"):
            if tcpc_active:
                # Simultaneous TCPC motion is modal and may output either axis.
                reached_b = word_value(words, "B") if has_word(words, "B") else reached_b
                reached_c = word_value(words, "C") if has_word(words, "C") else reached_c
                rotary_line = None
            else:
                if not (has_word(words, "B") and has_word(words, "C")):
                    fail(line_number, "TWP-capable world indexing must output B and C together")
                reached_b = word_value(words, "B")
                reached_c = word_value(words, "C")
                rotary_line = line_number
                world_retract_after_rotary = False

        if rotary_line is not None and has_word(words, "Z") and (
            has_code(words, "G", 28.0) or has_code(words, "G", 53.0)
        ):
            world_retract_after_rotary = True

        if has_code(words, "M", 2.0) or has_code(words, "M", 30.0):
            if twp_defined or twp_active or tcpc_active:
                fail(line_number, "program ends with TWP or TCPC active")

    if twp_defined or twp_active:
        raise ValidationError(f"{source}: file ends with TWP active")
    if tcpc_active:
        raise ValidationError(f"{source}: file ends with public TCPC active")
    return {"blocks": len(blocks), "twp_cycles": twp_count, "tcpc_cycles": tcpc_count}


def self_test():
    valid = """
G43 H4
G28 G91 Z0
G90
G0 B5 C0
G28 G91 Z0
G90
G68.2 X0 Y0 Z0 I90 J5 K-90
G53.1
G90 G0 X1 Y2
G0 Z3
G94 G1 X2 F100
G90 G0 Z10
G69
G49
M30
"""
    result = validate_text(valid)
    assert result["twp_cycles"] == 1
    tcpc = """
G43 H4
G53 G1 B0 C0 F1000
G43.4
G94 G1 X1 B5 F100
G1 X2 C10 F100
G53 G1 B0 C0 F1000
G49.1
G49
M30
"""
    result = validate_text(tcpc)
    assert result["tcpc_cycles"] == 1
    invalid = valid.replace("G94 G1 X2 F100", "G2 X2 Y2 I1 J0 F100")
    try:
        validate_text(invalid)
    except ValidationError:
        pass
    else:
        raise AssertionError("active-TWP arc was not rejected")
    print("MotionX generated-output validator self-test: PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program", nargs="?", type=Path, help="Fusion-generated .ngc file")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.program is None:
        parser.error("provide an NGC program or --self-test")
    try:
        result = validate_text(args.program.read_text(encoding="ascii"), str(args.program))
    except (OSError, UnicodeError, ValidationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        f"PASS: {args.program} ({result['blocks']} blocks, "
        f"{result['twp_cycles']} TWP cycle(s), {result['tcpc_cycles']} TCPC cycle(s))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
