#!/usr/bin/env python3

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
POST = ROOT / "Fusion Post" / "pocketnc-motionX 3.cps"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def scan_balanced(source):
    pairs = {"(": ")", "[": "]", "{": "}"}
    closing = {value: key for key, value in pairs.items()}
    stack = []
    state = "code"
    quote = None
    index = 0
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if state == "line_comment":
            if char == "\n":
                state = "code"
        elif state == "block_comment":
            if char == "*" and next_char == "/":
                state = "code"
                index += 1
        elif state == "string":
            if char == "\\":
                index += 1
            elif char == quote:
                state = "code"
        else:
            if char == "/" and next_char == "/":
                state = "line_comment"
                index += 1
            elif char == "/" and next_char == "*":
                state = "block_comment"
                index += 1
            elif char in ('"', "'"):
                state = "string"
                quote = char
            elif char in pairs:
                stack.append((char, index))
            elif char in closing:
                require(stack, f"unexpected {char!r} at byte {index}")
                opening, opening_index = stack.pop()
                require(opening == closing[char], f"mismatched {opening!r} at {opening_index} and {char!r} at {index}")
        index += 1
    require(state not in ("string", "block_comment"), f"unterminated {state}")
    require(not stack, f"unclosed delimiter {stack[-1] if stack else 'unknown'}")


def function_body(source, name):
    marker = f"function {name}("
    start = source.find(marker)
    require(start >= 0, f"missing function {name}")
    brace = source.find("{", start)
    require(brace >= 0, f"missing body for function {name}")
    depth = 0
    state = "code"
    quote = None
    index = brace
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if state == "line_comment":
            if char == "\n":
                state = "code"
        elif state == "block_comment":
            if char == "*" and next_char == "/":
                state = "code"
                index += 1
        elif state == "string":
            if char == "\\":
                index += 1
            elif char == quote:
                state = "code"
        else:
            if char == "/" and next_char == "/":
                state = "line_comment"
                index += 1
            elif char == "/" and next_char == "*":
                state = "block_comment"
                index += 1
            elif char in ('"', "'"):
                state = "string"
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return source[brace + 1:index]
        index += 1
    raise AssertionError(f"unterminated body for function {name}")


def main():
    source = POST.read_text(encoding="ascii")
    scan_balanced(source)

    for legacy in ("M254", "activeM254", "rotatedWorkOffsetsWCS"):
        require(legacy not in source, f"legacy rotated-WCS token remains: {legacy}")

    require("useTWP:" in source, "missing explicit TWP property")
    require("var lengthCompensationActive = false;" in source, "missing ordinary TLO state")
    require("var tcpcActive = false;" in source, "missing public TCPC state")
    require("var twpDefined = false;" in source, "missing TWP-defined state")
    require("var twpActive = false;" in source, "missing TWP-active state")
    require("EULER_ZXZ_R" in source, "wrong or missing Fusion Euler convention")
    require("TWP_MAX_COMMISSIONED_B_DEG = 30.0" in source, "missing commissioned B limit")
    require("range:[-100, 100]" in source, "embedded B machine range is wrong")
    require("range:[-359, 359]" in source, "embedded C machine range is wrong")
    require("var performRewinds = false" in source, "automatic rotary rewind is not fail-closed")

    for forbidden_length_source in (
        "getOptimizedPosition",
        "operation:tool_assemblyGaugeLength",
        "tool.bodyLength",
        "tool.holderLength",
    ):
        require(forbidden_length_source not in source, f"TWP depends on Fusion tool length: {forbidden_length_source}")

    activate = function_body(source, "activateTWP")
    require(activate.count("writeRetract(Z)") == 2, "TWP entry must retract before and after B/C indexing")
    require(activate.index("writeRetract(Z)") < activate.index("positionTWPRotaries(machineABC)"), "B/C indexes before world retract")
    require(activate.index("positionTWPRotaries(machineABC)") < activate.rindex("writeRetract(Z)"), "missing reached-pose world retract")
    require(activate.index("gFormat.format(68.2)") < activate.index("gFormat.format(53.1)"), "G53.1 is not after G68.2")
    require("twpDefined = true" in activate and "twpActive = true" in activate, "TWP entry does not update both states")
    require("setTCPMode(true)" not in activate and "gFormat.format(43.4)" not in activate, "TWP entry incorrectly uses public TCPC")

    validate_entry = function_body(source, "validateTWPEntry")
    require("lengthCompensationActive" in validate_entry, "TWP does not require ordinary G43 H")
    require("tcpcActive" in validate_entry, "TWP does not reject active public TCPC")
    require("TWP_MAX_COMMISSIONED_B_DEG" in validate_entry, "TWP does not enforce the commissioned B limit")

    cancel = function_body(source, "cancelTWP")
    require(cancel.index("zOutput.format(localClearanceZ)") < cancel.index("gFormat.format(69)"), "G69 precedes local clearance")
    require("twpActive = false" in cancel and "twpDefined = false" in cancel, "G69 does not clear both TWP states")

    circular = function_body(source, "onCircular")
    require(circular.index("if (twpActive)") < circular.index("linearize(tolerance)"), "TWP arcs are not linearized first")

    cycle = function_body(source, "onCyclePoint")
    require(cycle.index("if (twpActive)") < cycle.index("expandCyclePoint(x, y, z)"), "TWP cycles are not expanded first")

    for callback in ("onRapid5D", "onLinear5D"):
        body = function_body(source, callback)
        require("isTWPStateSet()" in body and "error(" in body, f"{callback} does not reject TWP rotary motion")

    section = function_body(source, "onSection")
    require(section.index("writeBlock(gFormat.format(43)") < section.index("activateTWP("), "ordinary G43 H is not established before TWP")
    require("currentSection.workPlane.getEuler2(EULER_ZXZ_R)" in section, "TWP Euler angles do not come from the CAM plane")
    require("Simultaneous multi-axis sections require Use TCPC mode" in section, "raw simultaneous output is not rejected")

    section_end = function_body(source, "onSectionEnd")
    require(section_end.index("cancelTWP()") < section_end.index("setCoolant(COOLANT_OFF)"), "TWP is not cancelled before section-end state changes")

    close = function_body(source, "onClose")
    require(close.index("cancelTWP()") < close.index("gFormat.format(53)"), "TWP is not cancelled before closeout G53")
    require(close.index("setTCPMode(false)") < close.index("gFormat.format(53)"), "TCPC is not cancelled before closeout G53")

    retract = function_body(source, "writeRetract")
    require("!isTWPStateSet()" in retract, "machine-coordinate retract is not guarded against active TWP")

    print("MotionX Fusion post static contract: PASS")


if __name__ == "__main__":
    main()
