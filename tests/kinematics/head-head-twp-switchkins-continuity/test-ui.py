#!/usr/bin/env python3

import math
from pathlib import Path
import subprocess
import sys
import time
import traceback

import hal
import linuxcnc


TIMEOUT = 60.0
SAMPLER_DRAIN_TIMEOUT = 5.0
SAMPLE_FILE = Path(__file__).resolve().with_name("switchkins.samples")
PERCENT_PROGRAM = Path(__file__).resolve().with_name("percent-terminator.ngc")

MODEL_ID = 2026082601
MODEL_REFERENCE = 229.407000
MODEL_SPAN = 100.800271
G54_OFFSET = (123.456, -78.900, 12.250)
START_XYZ = (400.0, 250.0, -150.0)
B_ZERO_OFFSET = 0.0
C_ZERO_OFFSET = -0.024500

DIRECT_LINEAR_TOL = 1e-5
DIRECT_ROTARY_TOL = 1e-5
SAMPLE_LINEAR_TOL = 5e-6
SAMPLE_ROTARY_TOL = 5e-6
PLANE_VECTOR_TOL = 2e-4
MODEL_TOL = 2e-6

# Fields after the tagged sample number.
JX, JY, JZ, JB, JC = range(5)
TOOL_X, TOOL_Y, TOOL_Z = range(5, 8)
ORIGIN_X, ORIGIN_Y, ORIGIN_Z = range(8, 11)
SWITCH_TYPE = 11
IS_WORLD = 12
IS_TWP = 13
TRANSACTION_ACK = 14
FRAME_READY = 15
MODEL_Q = 16
MODEL_VALID = 17
MODEL_FAULT = 18
EVALUATED_LENGTH = 19
IN_POSITION = 20
SAMPLE_FIELDS = 21

CASES = (
    {
        "name": "T3",
        "tool": 3,
        "length": 128.606729,
        "b": 30.0,
        "reached_c": 90.0,
        "requested_c": 90.0,
        "r": 17.0,
        "q": 1.0,
    },
    {
        "name": "T4-C-wrap",
        "tool": 4,
        "length": 229.407000,
        "b": -30.0,
        "reached_c": -350.0,
        "requested_c": 10.0,
        "r": 0.0,
        "q": 0.0,
    },
)


class TestFailure(RuntimeError):
    pass


def fail(message):
    raise TestFailure(message)


def log(message):
    print(message)
    sys.stdout.flush()


def wait_for_linuxcnc_startup(status, timeout=TIMEOUT):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status.poll()
        if (
            status.angular_units != 0.0
            and status.axis_mask != 0
            and status.exec_state == linuxcnc.EXEC_DONE
            and status.interp_state == linuxcnc.INTERP_IDLE
            and status.inpos
            and status.linear_units != 0.0
            and status.max_velocity != 0.0
            and status.task_state == linuxcnc.STATE_ESTOP
        ):
            return
        time.sleep(0.1)
    fail("timeout waiting for LinuxCNC startup")


def drain_errors(error_channel):
    while error_channel.poll() is not None:
        pass


def check_errors(error_channel):
    while True:
        error = error_channel.poll()
        if error is None:
            return
        code, text = error
        if code in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
            fail("LinuxCNC error %s: %s" % error)
        log("LinuxCNC message %s: %s" % error)


def wait_for_idle(status, error_channel, timeout=TIMEOUT):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status.poll()
        check_errors(error_channel)
        if (
            status.interp_state == linuxcnc.INTERP_IDLE
            and status.exec_state == linuxcnc.EXEC_DONE
            and status.inpos
        ):
            return
        time.sleep(0.05)
    fail("timeout waiting for interpreter idle")


def wait_for_idle_after_expected_error(timeout=TIMEOUT):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status.poll()
        if (
            status.interp_state == linuxcnc.INTERP_IDLE
            and status.exec_state == linuxcnc.EXEC_DONE
            and status.inpos
        ):
            return
        time.sleep(0.05)
    fail("timeout waiting for interpreter idle after expected rejection")


def wait_for_expected_error(expected_text, timeout=TIMEOUT):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status.poll()
        error = errors.poll()
        if error is None:
            time.sleep(0.05)
            continue
        code, text = error
        if code not in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
            log("LinuxCNC message %s: %s" % error)
            continue
        if expected_text not in text:
            fail(
                "unexpected LinuxCNC error %s while waiting for %r"
                % (error, expected_text)
            )
        return text
    fail("timeout waiting for expected error containing: %s" % expected_text)


def wait_for_homed(status, expected_count):
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        status.poll()
        if sum(status.homed[:5]) == expected_count:
            return
        time.sleep(0.05)
    fail("timeout waiting for homing; homed=%s" % (status.homed[:5],))


def wait_for(predicate, label, timeout=TIMEOUT):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    fail("timeout waiting for %s" % label)


def mdi(command):
    drain_errors(errors)
    controller.mode(linuxcnc.MODE_MDI)
    controller.wait_complete()
    controller.mdi(command)
    controller.wait_complete()
    wait_for_idle(status, errors)


def mdi_expect_rejected(command, expected_text):
    drain_errors(errors)
    controller.mode(linuxcnc.MODE_MDI)
    controller.wait_complete()
    controller.mdi(command)
    text = wait_for_expected_error(expected_text)
    wait_for_idle_after_expected_error()
    return text


def auto_expect_rejected(expected_text):
    drain_errors(errors)
    controller.mode(linuxcnc.MODE_AUTO)
    controller.wait_complete()
    controller.auto(linuxcnc.AUTO_RUN, 0)
    text = wait_for_expected_error(expected_text)
    wait_for_idle_after_expected_error()
    return text


def hal_float(name):
    return float(hal.get_value(name))


def hal_bool(name):
    return bool(hal.get_value(name))


def joint_pose():
    return tuple(hal_float("joint.%d.motor-pos-cmd" % joint) for joint in range(5))


def dot_vector(prefix):
    return tuple(hal_float("%s.%s" % (prefix, axis)) for axis in ("x", "y", "z"))


def underscore_vector(prefix):
    return tuple(hal_float("%s_%s" % (prefix, axis)) for axis in ("x", "y", "z"))


def vector_sub(a, b):
    return tuple(a[index] - b[index] for index in range(3))


def physical_tcp():
    joints = joint_pose()
    tool_offset = dot_vector("headheadkins.tool-offset")
    tcpc_origin = underscore_vector("headheadtwp.tcpc_origin")
    return tuple(joints[index] + tool_offset[index] - tcpc_origin[index] for index in range(3))


def assert_scalar(label, actual, expected, tolerance):
    if not math.isfinite(actual) or abs(actual - expected) > tolerance:
        fail(
            "%s mismatch: actual=%.12g expected=%.12g tolerance=%.12g"
            % (label, actual, expected, tolerance)
        )


def assert_vector(label, actual, expected, tolerance):
    if len(actual) != len(expected):
        fail("%s length mismatch: actual=%s expected=%s" % (label, actual, expected))
    deltas = tuple(actual[index] - expected[index] for index in range(len(actual)))
    if any(not math.isfinite(delta) or abs(delta) > tolerance for delta in deltas):
        fail(
            "%s mismatch: actual=%s expected=%s delta=%s tolerance=%.12g"
            % (label, actual, expected, deltas, tolerance)
        )


def assert_joint_continuity(label, before, after):
    assert_vector(label + " linear joints", after[:3], before[:3], DIRECT_LINEAR_TOL)
    assert_vector(label + " rotary joints", after[3:], before[3:], DIRECT_ROTARY_TOL)


def assert_world_mode(label):
    if not hal_bool("headheadkins.kinstype-is-world"):
        fail("%s did not select world kinematics" % label)
    if hal_bool("headheadkins.kinstype-is-twp"):
        fail("%s left TWP kinematics selected" % label)
    if not hal_bool("headheadkins.kinstype-frame-ready"):
        fail("%s world kinematics frame is not ready" % label)


def assert_twp_mode(label):
    if hal_bool("headheadkins.kinstype-is-world"):
        fail("%s left world kinematics selected" % label)
    if not hal_bool("headheadkins.kinstype-is-twp"):
        fail("%s did not select TWP kinematics" % label)
    if not hal_bool("headheadkins.kinstype-frame-ready"):
        fail("%s TWP kinematics frame is not ready" % label)


def assert_model(case):
    if not hal_bool("headheadkins.length-model.configured"):
        fail("%s length model is not configured" % case["name"])
    if not hal_bool("headheadkins.length-model.valid"):
        fail("%s length model is invalid" % case["name"])
    fault = int(hal.get_value("headheadkins.length-model.fault-code"))
    if fault != 0:
        fail("%s length model fault is %d" % (case["name"], fault))
    model_id = int(hal.get_value("headheadkins.length-model.id"))
    expected_id = int(hal.get_value("headheadkins.length-model.expected-id"))
    if model_id != MODEL_ID or expected_id != MODEL_ID:
        fail(
            "%s model ID mismatch: id=%d expected-id=%d"
            % (case["name"], model_id, expected_id)
        )
    assert_scalar(
        case["name"] + " model reference",
        hal_float("headheadkins.length-model.reference"),
        MODEL_REFERENCE,
        1e-9,
    )
    assert_scalar(
        case["name"] + " model span",
        hal_float("headheadkins.length-model.span"),
        MODEL_SPAN,
        1e-9,
    )
    assert_scalar(
        case["name"] + " evaluated length",
        hal_float("headheadkins.tool-offset-eval.length"),
        case["length"],
        1e-9,
    )
    assert_scalar(
        case["name"] + " model q",
        hal_float("headheadkins.length-model.q"),
        case["q"],
        1e-9,
    )


def active_guard_snapshot():
    status.poll()
    return {
        "joints": joint_pose(),
        "physical_tcp": physical_tcp(),
        "state_origin": underscore_vector("headheadtwp.twp_origin"),
        "captured_origin": dot_vector("headheadkins.twp-captured-origin"),
        "coordinate_offset": dot_vector("headheadkins.twp-coordinate-offset"),
        "tool_offset": dot_vector("headheadkins.tool-offset"),
        "canonical_tool_offset": tuple(status.tool_offset),
        "tcpc_origin": underscore_vector("headheadtwp.tcpc_origin"),
        "tool_in_spindle": status.tool_in_spindle,
        "pocket_prepped": status.pocket_prepped,
        "g5x_index": status.g5x_index,
        "g5x_offset": tuple(status.g5x_offset),
        "transaction_ack": int(hal.get_value("headheadtwp.transaction_ack")),
        "state_code": int(hal.get_value("headheadtwp.state_code")),
        "transaction_fault": int(hal.get_value("headheadtwp.transaction_fault")),
        "twp_b": hal_float("headheadtwp.twp_b_angle"),
        "twp_c": hal_float("headheadtwp.twp_c_angle"),
        "twp_r": hal_float("headheadtwp.twp_normal_rotation"),
        "model_q": hal_float("headheadkins.length-model.q"),
        "model_fault": int(hal.get_value("headheadkins.length-model.fault-code")),
    }


def assert_active_guard_unchanged(label, before):
    after = active_guard_snapshot()
    assert_twp_mode(label)
    assert_joint_continuity(label, before["joints"], after["joints"])
    assert_vector(
        label + " physical TCP",
        after["physical_tcp"],
        before["physical_tcp"],
        DIRECT_LINEAR_TOL,
    )
    for field in (
        "state_origin",
        "captured_origin",
        "coordinate_offset",
        "tool_offset",
        "canonical_tool_offset",
        "tcpc_origin",
        "g5x_offset",
    ):
        assert_vector(
            "%s %s" % (label, field.replace("_", " ")),
            after[field],
            before[field],
            DIRECT_LINEAR_TOL,
        )
    for field in (
        "tool_in_spindle",
        "pocket_prepped",
        "g5x_index",
        "transaction_ack",
        "state_code",
        "transaction_fault",
        "model_fault",
    ):
        if after[field] != before[field]:
            fail(
                "%s changed %s: before=%s after=%s"
                % (label, field, before[field], after[field])
            )
    for field in ("twp_b", "twp_c", "twp_r", "model_q"):
        assert_scalar(label + " " + field, after[field], before[field], 1e-9)
    if not (
        hal_bool("headheadtwp.valid")
        and hal_bool("headheadtwp.active")
        and hal_bool("headheadtwp.motion_enabled")
        and hal_bool("headheadtwp.tcpc_enabled")
    ):
        fail("%s did not preserve active TWP/TCPC state" % label)


def exercise_active_guards(case):
    other_tool = 4 if case["tool"] == 3 else 3
    rejected = (
        (
            "rotary-axis word",
            "G1 B%.6f" % (case["b"] + 1.0),
            "Only XYZ linear-axis words are supported while TWP is active",
        ),
        (
            "G53 machine coordinates",
            "G53 G0 X0",
            "Only G4 is supported from modal group 0 while TWP is active",
        ),
        (
            "work-offset selection",
            "G55",
            "Cannot change coordinate systems while TWP is active",
        ),
        (
            "coordinate-parameter write",
            "#5221=[#5221+1.0]",
            "Cannot change coordinate parameter #5221 while TWP is active",
        ),
        (
            "arc motion",
            "G2 X0 Y0 I1 J0",
            "Only G0, G1, G80, and G69 are supported while TWP is active",
        ),
        (
            "tool selection",
            "T%d" % other_tool,
            "Cannot select a tool while TWP is active",
        ),
        (
            "tool-length change",
            "G43 H%d" % other_tool,
            "Cannot change tool length compensation while TWP is active",
        ),
        (
            "program end",
            "M2",
            "Cancel TWP with G69 before ending or restarting a program",
        ),
    )
    for guard_name, command, expected_text in rejected:
        before = active_guard_snapshot()
        mdi_expect_rejected(command, expected_text)
        assert_active_guard_unchanged(
            "%s rejected %s" % (case["name"], guard_name),
            before,
        )
    log("%s passed %d active-TWP fail-closed command guards" % (case["name"], len(rejected)))


def exercise_percent_terminator_guard(case):
    before = active_guard_snapshot()
    auto_expect_rejected("Cancel TWP with G69 before ending the program")
    assert_active_guard_unchanged(
        "%s rejected percent program terminator" % case["name"],
        before,
    )
    log("%s passed active-TWP percent-terminator guard" % case["name"])


def independent_plane_x(b_degrees, c_degrees, r_degrees):
    b = math.radians(b_degrees + B_ZERO_OFFSET)
    c = math.radians(c_degrees + C_ZERO_OFFSET)
    r = math.radians(r_degrees)
    stored_x = (
        math.cos(c) * math.cos(b),
        math.sin(c) * math.cos(b),
        -math.sin(b),
    )
    stored_y = (-math.sin(c), math.cos(c), 0.0)
    return tuple(
        math.cos(r) * stored_x[axis] + math.sin(r) * stored_y[axis]
        for axis in range(3)
    )


def start_sampler():
    try:
        SAMPLE_FILE.unlink()
    except FileNotFoundError:
        pass
    process = subprocess.Popen(
        ["halsampler", "-t", str(SAMPLE_FILE)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(0.1)
    if process.poll() is not None:
        _, stderr_text = process.communicate()
        fail("halsampler failed to start: %s" % stderr_text.strip())
    return process


def stop_sampler(process, strict):
    try:
        hal.set_p("sampler.0.enable", "0")
    except Exception:
        if strict:
            raise

    if strict:
        deadline = time.monotonic() + SAMPLER_DRAIN_TIMEOUT
        while time.monotonic() < deadline:
            if int(hal.get_value("sampler.0.curr-depth")) == 0:
                break
            if process.poll() is not None:
                _, stderr_text = process.communicate()
                fail("halsampler exited while draining: %s" % stderr_text.strip())
            time.sleep(0.01)
        else:
            fail(
                "sampler FIFO did not drain; depth=%s"
                % hal.get_value("sampler.0.curr-depth")
            )
        overruns = int(hal.get_value("sampler.0.overruns"))
        if overruns != 0:
            fail("servo sampler recorded %d overruns" % overruns)

    if process.poll() is None:
        process.terminate()
    try:
        _, stderr_text = process.communicate(timeout=5.0)
    except subprocess.TimeoutExpired:
        process.kill()
        _, stderr_text = process.communicate(timeout=5.0)
        if strict:
            fail("halsampler did not terminate: %s" % stderr_text.strip())


def set_sampling(enabled):
    hal.set_p("sampler.0.enable", "1" if enabled else "0")
    time.sleep(0.025)


def parse_samples():
    if not SAMPLE_FILE.is_file():
        fail("halsampler did not create %s" % SAMPLE_FILE)
    records = []
    previous_tag = None
    with SAMPLE_FILE.open("r", encoding="ascii") as sample_file:
        for line_number, line in enumerate(sample_file, 1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped == "overrun":
                fail("halsampler output contains an overrun marker")
            fields = stripped.split()
            if len(fields) != SAMPLE_FIELDS + 1:
                fail(
                    "sample line %d has %d fields, expected %d: %s"
                    % (line_number, len(fields), SAMPLE_FIELDS + 1, stripped)
                )
            try:
                tag = int(fields[0])
                values = tuple(float(value) for value in fields[1:])
            except ValueError as exc:
                fail("cannot parse sample line %d: %s" % (line_number, exc))
            if previous_tag is not None and tag != previous_tag + 1:
                fail("sample tag gap at line %d: %d followed %d" % (line_number, tag, previous_tag))
            if not all(math.isfinite(value) for value in values):
                fail("sample line %d contains a nonfinite value" % line_number)
            previous_tag = tag
            records.append((tag, values))
    if len(records) < 100:
        fail("too few servo samples captured: %d" % len(records))
    return records


def bit_value(record, field, label):
    value = record[1][field]
    rounded = int(round(value))
    if rounded not in (0, 1) or abs(value - rounded) > 1e-9:
        fail("%s is not binary at sample %d: %s" % (label, record[0], value))
    return rounded


def physical_tcp_sample(record):
    values = record[1]
    return tuple(
        values[JX + axis] + values[TOOL_X + axis] - values[ORIGIN_X + axis]
        for axis in range(3)
    )


def range_of(records, field):
    values = [record[1][field] for record in records]
    return max(values) - min(values)


def transition_indices(records):
    return [
        index
        for index in range(1, len(records))
        if bit_value(records[index - 1], IS_TWP, "kinstype-is-twp")
        != bit_value(records[index], IS_TWP, "kinstype-is-twp")
    ]


def active_runs(records):
    runs = []
    start = None
    for index, record in enumerate(records):
        active = bit_value(record, IS_TWP, "kinstype-is-twp")
        if active and start is None:
            start = index
        elif not active and start is not None:
            runs.append((start, index))
            start = None
    if start is not None:
        runs.append((start, len(records)))
    return runs


def closest_edge_distance(index, edges):
    return min(abs(index - edge) for edge in edges)


def validate_samples(records):
    edges = transition_indices(records)
    if len(edges) != 4:
        fail("expected four switchkins edges, found %d at %s" % (len(edges), edges))

    directions = []
    for edge in edges:
        directions.append(
            (
                bit_value(records[edge - 1], IS_TWP, "kinstype-is-twp"),
                bit_value(records[edge], IS_TWP, "kinstype-is-twp"),
            )
        )
    expected_directions = [(0, 1), (1, 0), (0, 1), (1, 0)]
    if directions != expected_directions:
        fail("switchkins edge order mismatch: actual=%s expected=%s" % (directions, expected_directions))

    previous_ack = None
    for index, record in enumerate(records):
        world = bit_value(record, IS_WORLD, "kinstype-is-world")
        twp = bit_value(record, IS_TWP, "kinstype-is-twp")
        frame_ready = bit_value(record, FRAME_READY, "kinstype-frame-ready")
        valid = bit_value(record, MODEL_VALID, "length-model-valid")
        if world + twp != 1:
            fail("kinematics mode is not one-hot at sample %d" % record[0])
        if not frame_ready:
            fail("kinematics frame is not ready at sample %d" % record[0])
        if not valid or int(round(record[1][MODEL_FAULT])) != 0:
            fail(
                "length model invalid at sample %d: valid=%d fault=%s"
                % (record[0], valid, record[1][MODEL_FAULT])
            )

        ack = int(round(record[1][TRANSACTION_ACK]))
        if previous_ack is not None and ack < previous_ack:
            fail("transaction ack regressed at sample %d: %d -> %d" % (record[0], previous_ack, ack))
        previous_ack = ack

        desired = int(round(record[1][SWITCH_TYPE]))
        if desired not in (0, 1) or abs(record[1][SWITCH_TYPE] - desired) > 1e-9:
            fail("switchkins request is not binary at sample %d" % record[0])
        # Userspace writes the desired type asynchronously. A record at the
        # edge can observe that request just before the following servo cycle
        # applies it; stable samples must agree.
        if desired != twp and closest_edge_distance(index, edges) > 4:
            fail(
                "stable switch state disagrees at sample %d: request=%d actual=%d"
                % (record[0], desired, twp)
            )

        length = record[1][EVALUATED_LENGTH]
        if abs(length - CASES[0]["length"]) <= MODEL_TOL:
            expected_q = CASES[0]["q"]
        elif abs(length - CASES[1]["length"]) <= MODEL_TOL:
            expected_q = CASES[1]["q"]
        else:
            fail("unexpected evaluated length at sample %d: %.9f" % (record[0], length))
        assert_scalar("sample %d model q" % record[0], record[1][MODEL_Q], expected_q, MODEL_TOL)

    for edge_number, edge in enumerate(edges, 1):
        window = records[max(0, edge - 8) : min(len(records), edge + 9)]
        if len(window) < 9:
            fail("switch edge %d lacks a stable sample window" % edge_number)
        if any(not bit_value(record, IN_POSITION, "motion-in-position") for record in window):
            fail("switch edge %d occurred while motion was not in position" % edge_number)
        for field, axis in zip((JX, JY, JZ), "XYZ"):
            span = range_of(window, field)
            if span > SAMPLE_LINEAR_TOL:
                fail("switch edge %d %s joint span %.9g mm" % (edge_number, axis, span))
        for field, axis in zip((JB, JC), "BC"):
            span = range_of(window, field)
            if span > SAMPLE_ROTARY_TOL:
                fail("switch edge %d %s joint span %.9g deg" % (edge_number, axis, span))
        for axis in range(3):
            values = [physical_tcp_sample(record)[axis] for record in window]
            span = max(values) - min(values)
            if span > SAMPLE_LINEAR_TOL:
                fail("switch edge %d physical TCP axis %d span %.9g mm" % (edge_number, axis, span))

    runs = active_runs(records)
    if len(runs) != 2:
        fail("expected two active TWP sample runs, found %s" % (runs,))
    for case, (start, end) in zip(CASES, runs):
        run = records[start:end]
        if len(run) < 20:
            fail("%s active TWP interval is too short: %d samples" % (case["name"], len(run)))
        assert_scalar(
            case["name"] + " sampled length",
            run[len(run) // 2][1][EVALUATED_LENGTH],
            case["length"],
            MODEL_TOL,
        )
        b_span = range_of(run, JB)
        c_span = range_of(run, JC)
        if b_span > SAMPLE_ROTARY_TOL or c_span > SAMPLE_ROTARY_TOL:
            fail(
                "%s rotary branch moved while TWP active: B span %.9g C span %.9g"
                % (case["name"], b_span, c_span)
            )
        assert_scalar(case["name"] + " active B", run[0][1][JB], case["b"], SAMPLE_ROTARY_TOL)
        assert_scalar(
            case["name"] + " active continuous C",
            run[0][1][JC],
            case["reached_c"],
            SAMPLE_ROTARY_TOL,
        )

    log(
        "servo sampler validated %d records, four stationary switch edges, and two fixed B/C branches"
        % len(records)
    )


def run_case(case):
    name = case["name"]
    mdi("G49")
    mdi("T%d M6" % case["tool"])
    mdi("G43 H%d" % case["tool"])
    status.poll()
    if status.tool_in_spindle != case["tool"]:
        fail("%s tool did not enter spindle: %s" % (name, status.tool_in_spindle))
    assert_scalar(
        name + " active G43 length",
        hal_float("motion.tooloffset.z"),
        case["length"],
        1e-9,
    )
    wait_for(
        lambda: abs(hal_float("headheadkins.tool-offset-eval.length") - case["length"]) < 1e-9,
        name + " length-model synchronization",
    )
    assert_model(case)

    mdi(
        "G0 X%.6f Y%.6f Z%.6f B0 C0"
        % (START_XYZ[0], START_XYZ[1], START_XYZ[2])
    )
    assert_world_mode(name + " pre-TCPC")
    pre_tcpc_joints = joint_pose()
    mdi("G43.4")
    assert_joint_continuity(name + " G43.4", pre_tcpc_joints, joint_pose())
    if not hal_bool("headheadtwp.tcpc_enabled"):
        fail("%s G43.4 did not enable TCPC" % name)

    mdi("G0 B%.6f C%.6f" % (case["b"], case["reached_c"]))
    assert_model(case)
    assert_scalar(name + " reached B", joint_pose()[3], case["b"], DIRECT_ROTARY_TOL)
    assert_scalar(name + " reached C", joint_pose()[4], case["reached_c"], DIRECT_ROTARY_TOL)

    before_joints = joint_pose()
    before_tcp = physical_tcp()
    ack_before = int(hal.get_value("headheadtwp.transaction_ack"))
    set_sampling(True)
    mdi(
        "G68.2 B%.6f C%.6f R%.6f"
        % (case["b"], case["requested_c"], case["r"])
    )
    time.sleep(0.025)

    assert_twp_mode(name + " G68.2")
    assert_joint_continuity(name + " G68.2", before_joints, joint_pose())
    assert_vector(name + " G68.2 physical TCP", physical_tcp(), before_tcp, DIRECT_LINEAR_TOL)
    if int(hal.get_value("headheadtwp.transaction_ack")) <= ack_before:
        fail("%s G68.2 did not advance the state transaction" % name)
    if not (
        hal_bool("headheadtwp.valid")
        and hal_bool("headheadtwp.active")
        and hal_bool("headheadtwp.motion_enabled")
        and hal_bool("headheadtwp.tcpc_enabled")
    ):
        fail("%s G68.2 state postcondition is incomplete" % name)

    assert_vector(
        name + " TWP state origin",
        underscore_vector("headheadtwp.twp_origin"),
        before_tcp,
        DIRECT_LINEAR_TOL,
    )
    assert_vector(
        name + " kinematics captured origin",
        dot_vector("headheadkins.twp-captured-origin"),
        before_tcp,
        DIRECT_LINEAR_TOL,
    )
    assert_vector(
        name + " G54 coordinate layer",
        dot_vector("headheadkins.twp-coordinate-offset"),
        G54_OFFSET,
        DIRECT_LINEAR_TOL,
    )
    assert_scalar(
        name + " latched TWP B",
        hal_float("headheadtwp.twp_b_angle"),
        case["b"],
        DIRECT_ROTARY_TOL,
    )
    assert_scalar(
        name + " latched continuous TWP C",
        hal_float("headheadtwp.twp_c_angle"),
        case["reached_c"],
        DIRECT_ROTARY_TOL,
    )
    assert_scalar(
        name + " latched TWP normal rotation",
        hal_float("headheadtwp.twp_normal_rotation"),
        case["r"],
        DIRECT_ROTARY_TOL,
    )

    # Expected MDI errors close the loaded AUTO file, so exercise its closing
    # percent first while the original percent_flag/file position are intact.
    if case is CASES[0]:
        exercise_percent_terminator_guard(case)
    exercise_active_guards(case)

    expected_plane_x = independent_plane_x(
        case["b"],
        case["reached_c"],
        case["r"],
    )
    assert_vector(
        name + " state plane X",
        underscore_vector("headheadtwp.plane_x"),
        expected_plane_x,
        DIRECT_LINEAR_TOL,
    )
    local_start_tcp = physical_tcp()
    mdi("G91")
    mdi("G1 X1.000000 F60.0")
    moved_tcp = physical_tcp()
    assert_vector(
        name + " local X world displacement",
        vector_sub(moved_tcp, local_start_tcp),
        expected_plane_x,
        PLANE_VECTOR_TOL,
    )
    assert_scalar(name + " local move B hold", joint_pose()[3], case["b"], DIRECT_ROTARY_TOL)
    assert_scalar(
        name + " local move C branch hold",
        joint_pose()[4],
        case["reached_c"],
        DIRECT_ROTARY_TOL,
    )
    mdi("G1 X-1.000000")
    mdi("G90")
    assert_vector(name + " reversible local move", physical_tcp(), local_start_tcp, PLANE_VECTOR_TOL)

    before_exit_joints = joint_pose()
    before_exit_tcp = physical_tcp()
    mdi("G69")
    time.sleep(0.025)
    assert_world_mode(name + " G69")
    assert_joint_continuity(name + " G69", before_exit_joints, joint_pose())
    assert_vector(name + " G69 physical TCP", physical_tcp(), before_exit_tcp, DIRECT_LINEAR_TOL)
    if (
        hal_bool("headheadtwp.valid")
        or hal_bool("headheadtwp.active")
        or hal_bool("headheadtwp.motion_enabled")
    ):
        fail("%s G69 did not clear TWP state" % name)
    if not hal_bool("headheadtwp.tcpc_enabled"):
        fail("%s G69 did not preserve TCPC" % name)
    assert_vector(
        name + " cleared TWP coordinate layer",
        dot_vector("headheadkins.twp-coordinate-offset"),
        (0.0, 0.0, 0.0),
        DIRECT_LINEAR_TOL,
    )
    set_sampling(False)

    mdi("G0 B0 C0")
    mdi("G49.1")
    if hal_bool("headheadtwp.tcpc_enabled"):
        fail("%s G49.1 did not disable TCPC" % name)
    mdi("G49")
    log(
        "%s passed: length %.6f q %.1f reached B%.1f C%.1f asserted C%.1f R%.1f"
        % (
            name,
            case["length"],
            case["q"],
            case["b"],
            case["reached_c"],
            case["requested_c"],
            case["r"],
        )
    )


def main():
    global controller, status, errors

    controller = linuxcnc.command()
    status = linuxcnc.stat()
    errors = linuxcnc.error_channel()
    ui = hal.component("test-ui")
    ui.ready()

    wait_for_linuxcnc_startup(status)
    controller.state(linuxcnc.STATE_ESTOP_RESET)
    controller.state(linuxcnc.STATE_ON)
    time.sleep(0.5)
    controller.mode(linuxcnc.MODE_MANUAL)
    controller.wait_complete()
    controller.teleop_enable(0)
    time.sleep(0.2)
    for joint in range(5):
        controller.home(joint)
        time.sleep(0.1)
    wait_for_homed(status, 5)
    controller.teleop_enable(1)
    time.sleep(0.2)

    controller.program_open(str(PERCENT_PROGRAM))
    controller.wait_complete()
    mdi("G17 G21 G40 G49 G54 G64 P0.01 G80 G90 G92.1 G94")
    mdi(
        "G10 L2 P1 X%.6f Y%.6f Z%.6f"
        % (G54_OFFSET[0], G54_OFFSET[1], G54_OFFSET[2])
    )
    mdi("G54")
    assert_world_mode("startup")

    sampler_process = None
    try:
        sampler_process = start_sampler()
        for case in CASES:
            run_case(case)
        stop_sampler(sampler_process, strict=True)
        sampler_process = None
        validate_samples(parse_samples())
    finally:
        if sampler_process is not None:
            stop_sampler(sampler_process, strict=False)

    log("production-remap T3/T4 switchkins and C-wrap continuity test complete")


if __name__ == "__main__":
    try:
        main()
    except TestFailure as exc:
        print("TEST FAILURE: %s" % exc)
        sys.stdout.flush()
        sys.exit(1)
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()
        sys.exit(1)
