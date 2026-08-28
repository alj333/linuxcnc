#!/usr/bin/env python3

import importlib.util
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import hal
import linuxcnc


TIMEOUT = 45.0
POS_TOL = 1e-3
ORIGIN_TOL = 1e-3
START_POSE = (1500.0, 850.0, -600.0, 0.0, 0.0)
ROTATED_POSE = (1500.0, 850.0, -600.0, 30.0, 90.0)
ENTRY_ORIGIN = (2.0, -22.0, -704.123729)
LENGTH_REFERENCE = 229.407000
LENGTH_SPAN = 100.800271
LENGTH_FAULT_CONFIG_INVALID = 1
LENGTH_FAULT_ID_MISMATCH = 2
LENGTH_FAULT_TOOL_XY_UNSUPPORTED = 4
LENGTH_FAULT_OUT_OF_RANGE = 5
LENGTH_FAULT_COMMON_DISABLED = 6
LENGTH_FAULT_DIFF_NORM = 8
LENGTH_FAULT_TOTAL_NORM = 9
LENGTH_FAULT_TRANSFORM_NONFINITE = 10
LENGTH_DIFF = {
    "c_cos": (0.014666078, -0.034936825, -0.000531832),
    "c_sin": (0.037331865, 0.007479807, 0.000596261),
    "b_sin": (-0.009333530, -0.018596090, -0.055267212),
    "sinb_sinc": (0.022658483, 0.036745231, -0.024883253),
    "sinb_cosc": (0.126705142, 0.001218059, 0.017700599),
}

AUDIT_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "5th_axis_xyzbc_ssi_tcpc_probe_basic"
    / "assess_tcpc_length_aware_bounds.py"
)
AUDIT_SPEC = importlib.util.spec_from_file_location("tcpc_length_audit", AUDIT_PATH)
if AUDIT_SPEC is None or AUDIT_SPEC.loader is None:
    raise RuntimeError("cannot load canonical offline length model")
OFFLINE_MODEL = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(OFFLINE_MODEL)

RUNTIME_MODEL_CASES = (
    (13, 99.998000, -100.0, 276.75),
    (3, 100.000000, 90.0, 195.0),
    (10, 114.677000, 100.0, 359.75),
    (1, 128.606729, 30.0, 90.0),
    (11, 229.407000, -100.0, 101.75),
    (12, 411.810000, -100.0, 108.0),
    (6, 425.022000, 90.0, 195.0),
    (4, 430.000000, -100.0, 109.0),
    (14, 430.002000, 57.25, 200.0),
)


def fail(msg):
    print(msg)
    sys.stdout.flush()
    sys.exit(1)


def log(msg):
    print(msg)
    sys.stdout.flush()


def wait_for_linuxcnc_startup(status, timeout=TIMEOUT):
    start_time = time.time()
    while time.time() - start_time < timeout:
        status.poll()
        if (
            status.angular_units != 0.0
            and status.axis_mask != 0
            and status.cycle_time != 0.0
            and status.exec_state == linuxcnc.EXEC_DONE
            and status.interp_state == linuxcnc.INTERP_IDLE
            and status.inpos
            and status.linear_units != 0.0
            and status.max_acceleration != 0.0
            and status.max_velocity != 0.0
            and status.program_units != 0.0
            and status.rapidrate != 0.0
            and status.state == linuxcnc.RCS_DONE
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


def wait_for_idle(status, error_channel):
    start_time = time.time()
    while time.time() - start_time < TIMEOUT:
        status.poll()
        check_errors(error_channel)
        if (
            status.interp_state == linuxcnc.INTERP_IDLE
            and status.exec_state == linuxcnc.EXEC_DONE
            and status.inpos
        ):
            return
        time.sleep(0.1)
    fail("timeout waiting for interpreter idle")


def wait_for_expected_error(status, error_channel, expected_text):
    start_time = time.time()
    while time.time() - start_time < TIMEOUT:
        status.poll()
        error = error_channel.poll()
        if error is None:
            time.sleep(0.1)
            continue
        code, text = error
        if code not in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
            log("LinuxCNC message %s: %s" % error)
            continue
        if expected_text not in text:
            fail("unexpected LinuxCNC error %s: %s" % error)
        return text
    fail("timeout waiting for expected error containing: %s" % expected_text)


def wait_for_homed(status, expected_count):
    start_time = time.time()
    while time.time() - start_time < TIMEOUT:
        status.poll()
        if sum(status.homed[:5]) == expected_count:
            return
        time.sleep(0.1)
    fail("timeout waiting for homing; homed=%s" % (status.homed[:5],))


def mdi(cmd):
    drain_errors(e)
    c.mode(linuxcnc.MODE_MDI)
    c.wait_complete()
    c.mdi(cmd)
    c.wait_complete()
    wait_for_idle(s, e)


def mdi_expect_error(cmd, expected_text):
    drain_errors(e)
    c.mode(linuxcnc.MODE_MDI)
    c.wait_complete()
    c.mdi(cmd)
    text = wait_for_expected_error(s, e, expected_text)
    wait_for_idle_no_error_check()
    return text


def wait_for_idle_no_error_check():
    start_time = time.time()
    while time.time() - start_time < TIMEOUT:
        s.poll()
        if (
            s.interp_state == linuxcnc.INTERP_IDLE
            and s.exec_state == linuxcnc.EXEC_DONE
            and s.inpos
        ):
            return
        time.sleep(0.1)
    fail("timeout waiting for interpreter idle after expected error")


def program_pose():
    s.poll()
    return (
        s.position[0] - s.tool_offset[0],
        s.position[1] - s.tool_offset[1],
        s.position[2] - s.tool_offset[2],
        s.position[4],
        s.position[5],
    )


def joint_pose():
    return tuple(hal.get_value("joint.%d.motor-pos-cmd" % joint) for joint in range(5))


def tcpc_origin():
    return (
        hal.get_value("headheadtwp.tcpc_origin_x"),
        hal.get_value("headheadtwp.tcpc_origin_y"),
        hal.get_value("headheadtwp.tcpc_origin_z"),
    )


def current_tcp_pose():
    s.poll()
    return (
        hal.get_value("headheadtwp.current_tcp_x") - s.tool_offset[0],
        hal.get_value("headheadtwp.current_tcp_y") - s.tool_offset[1],
        hal.get_value("headheadtwp.current_tcp_z") - s.tool_offset[2],
        hal.get_value("headheadtwp.current_joint_b"),
        hal.get_value("headheadtwp.current_joint_c"),
    )


def assert_close_tuple(label, actual, expected, tol=POS_TOL):
    for a, ex in zip(actual, expected):
        if not math.isfinite(a) or not math.isfinite(ex) or math.fabs(a - ex) > tol:
            fail("%s mismatch: actual=%s expected=%s" % (label, actual, expected))


def tool_state():
    s.poll()
    return (s.tool_in_spindle, tuple(s.tool_offset))


def assert_tool_state(label, actual, expected):
    if actual[0] != expected[0]:
        fail("%s tool mismatch: actual=%s expected=%s" % (label, actual, expected))
    assert_close_tuple(label + " offset", actual[1], expected[1])


def assert_length_q(label, length):
    time.sleep(0.05)
    expected = (LENGTH_REFERENCE - length) / LENGTH_SPAN
    actual = hal.get_value("headheadkins.length-model.q")
    if not math.isfinite(actual) or not math.isfinite(expected) or math.fabs(actual - expected) > 1e-9:
        fail("%s q mismatch: actual=%s expected=%s" % (label, actual, expected))


def assert_length_diff(label, b_deg, c_deg, length):
    b_rad = math.radians(b_deg)
    c_rad = math.radians(c_deg)
    bases = {
        "c_cos": math.cos(c_rad) - 1.0,
        "c_sin": math.sin(c_rad),
        "b_sin": math.sin(b_rad),
        "sinb_sinc": math.sin(b_rad) * math.sin(c_rad),
        "sinb_cosc": math.sin(b_rad) * math.cos(c_rad),
    }
    q_value = (LENGTH_REFERENCE - length) / LENGTH_SPAN
    expected = tuple(
        q_value * sum(bases[term] * vector[axis] for term, vector in LENGTH_DIFF.items())
        for axis in range(3)
    )
    actual = tuple(
        hal.get_value("headheadkins.length-model.diff-offset.%s" % axis)
        for axis in ("x", "y", "z")
    )
    assert_close_tuple(label, actual, expected, 1e-8)


def scalar_basis(b_deg, c_deg):
    b_rad = math.radians(b_deg)
    c_rad = math.radians(c_deg + OFFLINE_MODEL.C_ZERO_DEG)
    c_ref_rad = math.radians(OFFLINE_MODEL.C_ZERO_DEG)
    sin_b = math.sin(b_rad)
    omc_b = 1.0 - math.cos(b_rad)
    mid_b = math.sin(2.0 * b_rad) ** 2
    return {
        "c_cos": math.cos(c_rad) - math.cos(c_ref_rad),
        "c_sin": math.sin(c_rad) - math.sin(c_ref_rad),
        "b_sin": sin_b,
        "b_omc": omc_b,
        "b_sin2": math.sin(2.0 * b_rad),
        "bc_sinb_sinc": sin_b * math.sin(c_rad),
        "bc_omcb_sinc": omc_b * math.sin(c_rad),
        "bc_omcb_sin2c": omc_b * math.sin(c_rad) ** 2,
        "bc_sinb_cosc": sin_b * math.cos(c_rad),
        "bc_omcb_cosc": omc_b * math.cos(c_rad),
        "bc_sinb_cos2c": sin_b * math.cos(2.0 * c_rad),
        "bmid_base": mid_b,
        "bmid_cosc": mid_b * math.cos(c_rad),
        "bmid_sinc": mid_b * math.sin(c_rad),
        "bmid_cos2c": mid_b * math.cos(2.0 * c_rad),
    }


def scalar_surface(basis, coefficients):
    return tuple(
        sum(basis[term] * vector[axis] for term, vector in coefficients.items())
        for axis in range(3)
    )


def vector_add(left, right):
    return tuple(a + b for a, b in zip(left, right))


def vector_scale(scale, vector):
    return tuple(scale * value for value in vector)


def vector_norm(vector):
    return math.sqrt(sum(value * value for value in vector))


def set_hal_pin(name, value):
    hal.set_p(name, "%.12g" % value)


def install_canonical_runtime_model():
    hal.set_p("headheadkins.length-model.id", "0")
    for stem in OFFLINE_MODEL.ALL_COMMON_PIN_STEMS:
        for axis in ("x", "y", "z"):
            set_hal_pin("%s.%s" % (stem, axis), 0.0)
    for stem in OFFLINE_MODEL.ALL_LENGTH_PIN_STEMS:
        for axis in ("x", "y", "z"):
            set_hal_pin("%s.%s" % (stem, axis), 0.0)

    common_pins = {}
    for coefficients in (OFFLINE_MODEL.H0, OFFLINE_MODEL.COMMON_INCREMENT):
        for term, vector in coefficients.items():
            stem = OFFLINE_MODEL.MODEL_PIN_STEMS[term]
            for axis, value in zip(("x", "y", "z"), vector):
                pin = "%s.%s" % (stem, axis)
                common_pins[pin] = common_pins.get(pin, 0.0) + value
    for pin, value in common_pins.items():
        set_hal_pin(pin, value)

    for term, vector in OFFLINE_MODEL.LENGTH_DIFFERENTIAL.items():
        stem = OFFLINE_MODEL.LENGTH_PIN_STEMS[term]
        for axis, value in zip(("x", "y", "z"), vector):
            set_hal_pin("%s.%s" % (stem, axis), value)

    set_hal_pin("headheadkins.b-zero-offset", 0.0)
    set_hal_pin("headheadkins.c-zero-offset", OFFLINE_MODEL.C_ZERO_DEG)
    set_hal_pin("headheadkins.length-model.reference", OFFLINE_MODEL.T4_LENGTH_MM)
    set_hal_pin(
        "headheadkins.length-model.span",
        OFFLINE_MODEL.T4_LENGTH_MM - OFFLINE_MODEL.T3_LENGTH_MM,
    )
    set_hal_pin("headheadkins.length-model.minimum", OFFLINE_MODEL.MODEL_MIN_LENGTH_MM)
    set_hal_pin("headheadkins.length-model.maximum", OFFLINE_MODEL.MODEL_MAX_LENGTH_MM)
    set_hal_pin(
        "headheadkins.length-model.tolerance",
        OFFLINE_MODEL.MODEL_LENGTH_TOLERANCE_MM,
    )
    set_hal_pin(
        "headheadkins.length-model.max-diff-norm",
        OFFLINE_MODEL.LENGTH_BANK_CAP_MM,
    )
    set_hal_pin(
        "headheadkins.length-model.max-total-norm",
        OFFLINE_MODEL.TOTAL_SURFACE_CAP_MM,
    )
    hal.set_p("headheadkins.sim-bharm-enable", "1")
    hal.set_p("headheadkins.length-model.id", str(OFFLINE_MODEL.MODEL_ID))


def assert_runtime_model(label, b_deg, c_deg, length, valid=True, fault=0):
    time.sleep(0.05)
    basis = scalar_basis(b_deg, c_deg)
    common = vector_add(
        scalar_surface(basis, OFFLINE_MODEL.H0),
        scalar_surface(basis, OFFLINE_MODEL.COMMON_INCREMENT),
    )
    q_value = OFFLINE_MODEL.q_for_length(length)
    differential = vector_scale(
        q_value,
        scalar_surface(basis, OFFLINE_MODEL.LENGTH_DIFFERENTIAL),
    )
    total = vector_add(common, differential)

    if bool(hal.get_value("headheadkins.length-model.valid")) != valid:
        fail("%s validity mismatch" % label)
    actual_fault = int(hal.get_value("headheadkins.length-model.fault-code"))
    if actual_fault != fault:
        fail("%s fault mismatch: actual=%d expected=%d" % (label, actual_fault, fault))
    assert_close_tuple(
        label + " evaluation stamp",
        (
            hal.get_value("headheadkins.tool-offset-eval.b"),
            hal.get_value("headheadkins.tool-offset-eval.c"),
            hal.get_value("headheadkins.tool-offset-eval.length"),
        ),
        (b_deg, c_deg, length),
        1e-7,
    )
    actual_q = hal.get_value("headheadkins.length-model.q")
    if not math.isfinite(actual_q) or not math.isfinite(q_value) or math.fabs(actual_q - q_value) > 1e-9:
        fail("%s q mismatch" % label)

    if valid or fault in (LENGTH_FAULT_DIFF_NORM, LENGTH_FAULT_TOTAL_NORM):
        actual_diff = tuple(
            hal.get_value("headheadkins.length-model.diff-offset.%s" % axis)
            for axis in ("x", "y", "z")
        )
        actual_total = tuple(
            hal.get_value("headheadkins.empirical-offset.%s" % axis)
            for axis in ("x", "y", "z")
        )
        assert_close_tuple(label + " differential", actual_diff, differential, 1e-9)
        assert_close_tuple(label + " total", actual_total, total, 1e-9)
        actual_diff_norm = hal.get_value("headheadkins.length-model.diff-offset-norm")
        expected_diff_norm = vector_norm(differential)
        if (
            not math.isfinite(actual_diff_norm)
            or not math.isfinite(expected_diff_norm)
            or math.fabs(actual_diff_norm - expected_diff_norm) > 1e-9
        ):
            fail("%s differential norm mismatch" % label)
        actual_total_norm = hal.get_value("headheadkins.empirical-offset-norm")
        expected_total_norm = vector_norm(total)
        if (
            not math.isfinite(actual_total_norm)
            or not math.isfinite(expected_total_norm)
            or math.fabs(actual_total_norm - expected_total_norm) > 1e-9
        ):
            fail("%s total norm mismatch" % label)
    return differential, total


def select_tool_pose(tool, b_deg, c_deg):
    mdi("G49")
    mdi("M61 Q%d" % tool)
    mdi("G43 H%d" % tool)
    mdi("G0 B%.6f C%.6f" % (b_deg, c_deg))


refresh_x = 1500.0


def refresh_kinematics():
    global refresh_x
    refresh_x = 1500.001 if refresh_x == 1500.0 else 1500.0
    mdi("G0 X%.6f" % refresh_x)


def exercise_runtime_model_equivalence():
    install_canonical_runtime_model()
    for tool, length, b_deg, c_deg in RUNTIME_MODEL_CASES:
        select_tool_pose(tool, b_deg, c_deg)
        assert_runtime_model(
            "runtime model T%d L%.6f B%.2f C%.2f" % (tool, length, b_deg, c_deg),
            b_deg,
            c_deg,
            length,
        )

    select_tool_pose(13, 0.0, 0.0)
    _, total = assert_runtime_model("lower tolerance exact reference", 0.0, 0.0, 99.998)
    assert_close_tuple("lower tolerance exact zero", total, (0.0, 0.0, 0.0), 1e-12)
    select_tool_pose(14, 0.0, 0.0)
    _, total = assert_runtime_model("upper tolerance exact reference", 0.0, 0.0, 430.002)
    assert_close_tuple("upper tolerance exact zero", total, (0.0, 0.0, 0.0), 1e-12)

    select_tool_pose(2, 0.0, 0.0)
    assert_runtime_model(
        "below lower tolerance",
        0.0,
        0.0,
        99.997,
        False,
        LENGTH_FAULT_OUT_OF_RANGE,
    )
    select_tool_pose(5, 0.0, 0.0)
    assert_runtime_model(
        "above upper tolerance",
        0.0,
        0.0,
        430.003,
        False,
        LENGTH_FAULT_OUT_OF_RANGE,
    )
    select_tool_pose(7, 0.0, 0.0)
    if bool(hal.get_value("headheadkins.length-model.valid")):
        fail("unsupported XY tool offset remained valid")
    if (
        int(hal.get_value("headheadkins.length-model.fault-code"))
        != LENGTH_FAULT_TOOL_XY_UNSUPPORTED
    ):
        fail("unsupported XY tool offset did not publish its fault")

    select_tool_pose(4, 90.0, 195.0)
    differential, _ = assert_runtime_model("nominal differential cap pose", 90.0, 195.0, 430.0)
    set_hal_pin("headheadkins.length-model.max-diff-norm", vector_norm(differential) * 0.99)
    refresh_kinematics()
    assert_runtime_model(
        "differential cap fault",
        90.0,
        195.0,
        430.0,
        False,
        LENGTH_FAULT_DIFF_NORM,
    )
    set_hal_pin("headheadkins.length-model.max-diff-norm", OFFLINE_MODEL.LENGTH_BANK_CAP_MM)

    select_tool_pose(4, -100.0, 109.0)
    _, total = assert_runtime_model("nominal total cap pose", -100.0, 109.0, 430.0)
    set_hal_pin("headheadkins.length-model.max-total-norm", vector_norm(total) * 0.99)
    refresh_kinematics()
    assert_runtime_model(
        "total cap fault",
        -100.0,
        109.0,
        430.0,
        False,
        LENGTH_FAULT_TOTAL_NORM,
    )
    set_hal_pin("headheadkins.length-model.max-total-norm", OFFLINE_MODEL.TOTAL_SURFACE_CAP_MM)

    hal.set_p("headheadkins.sim-bharm-enable", "0")
    refresh_kinematics()
    if (
        int(hal.get_value("headheadkins.length-model.fault-code"))
        != LENGTH_FAULT_COMMON_DISABLED
    ):
        fail("disabled common surface did not publish its fault")
    hal.set_p("headheadkins.sim-bharm-enable", "1")

    set_hal_pin("headheadkins.length-model.span", 0.0)
    refresh_kinematics()
    if (
        int(hal.get_value("headheadkins.length-model.fault-code"))
        != LENGTH_FAULT_CONFIG_INVALID
    ):
        fail("invalid model configuration did not publish its fault")
    set_hal_pin(
        "headheadkins.length-model.span",
        OFFLINE_MODEL.T4_LENGTH_MM - OFFLINE_MODEL.T3_LENGTH_MM,
    )

    hal.set_p("headheadkins.length-model.id", "0")
    refresh_kinematics()
    if (
        int(hal.get_value("headheadkins.length-model.fault-code"))
        != LENGTH_FAULT_ID_MISMATCH
    ):
        fail("wrong coefficient-set ID did not publish its fault")
    hal.set_p("headheadkins.length-model.id", str(OFFLINE_MODEL.MODEL_ID))

    set_hal_pin(
        "headheadkins.length-model.tolerance",
        OFFLINE_MODEL.MODEL_LENGTH_TOLERANCE_MM + 0.000001,
    )
    refresh_kinematics()
    if (
        int(hal.get_value("headheadkins.length-model.fault-code"))
        != LENGTH_FAULT_CONFIG_INVALID
    ):
        fail("expanded length tolerance did not publish its fault")
    set_hal_pin(
        "headheadkins.length-model.tolerance",
        OFFLINE_MODEL.MODEL_LENGTH_TOLERANCE_MM,
    )

    set_hal_pin(
        "headheadkins.length-model.maximum",
        OFFLINE_MODEL.MODEL_MAX_LENGTH_MM + 0.001,
    )
    refresh_kinematics()
    if (
        int(hal.get_value("headheadkins.length-model.fault-code"))
        != LENGTH_FAULT_CONFIG_INVALID
    ):
        fail("expanded hard length domain did not publish its fault")
    set_hal_pin("headheadkins.length-model.maximum", OFFLINE_MODEL.MODEL_MAX_LENGTH_MM)

    hal.set_p("headheadkins.nominal-c-to-b.x", "nan")
    refresh_kinematics()
    if (
        int(hal.get_value("headheadkins.length-model.fault-code"))
        != LENGTH_FAULT_TRANSFORM_NONFINITE
    ):
        fail("nonfinite complete transform did not publish its fault")
    hal.set_p("headheadkins.nominal-c-to-b.x", "0")
    refresh_kinematics()
    assert_runtime_model("restored runtime model", -100.0, 109.0, 430.0)
    mdi("G0 B0 C0")
    mdi("G49")
    log("canonical offline/runtime length-model equivalence and fault caps ok")


def exercise_process_loss_tooling_guard():
    mdi("T2")
    before_tool = tool_state()
    before_program = program_pose()
    before_joints = joint_pose()
    subprocess.run(["halcmd", "unloadusr", "headheadtwp"], check=True)
    deadline = time.time() + 5.0
    while hal.component_exists("headheadtwp") and time.time() < deadline:
        time.sleep(0.05)
    if hal.component_exists("headheadtwp"):
        fail("headheadtwp remained loaded after unloadusr")
    if hal.pin_has_writer("headheadkins.tcpc-enable"):
        fail("headheadkins.tcpc-enable unexpectedly retained a writer")
    if not bool(hal.get_value("headheadkins.length-model.configured")):
        fail("stable kinematics length-model policy disappeared with headheadtwp")
    if not bool(hal.get_value("headheadkins.tcpc-enable")):
        fail("kinematics TCPC state did not persist after headheadtwp loss")

    rejected = (
        ("M61 Q2", "Cannot change current tool number while TCPC is active"),
        ("M6", "Cannot change tools while TCPC is active"),
        ("G49", "Cannot change tool length compensation while TCPC is active"),
        ("G43 H2", "Cannot change tool length compensation while TCPC is active"),
        ("G43.1 Z200", "Cannot change tool length compensation while TCPC is active"),
        ("G43.2 H2", "Cannot change tool length compensation while TCPC is active"),
    )
    for command, expected in rejected:
        mdi_expect_error(command, expected)
        assert_tool_state("post-process-loss rejected %s" % command, tool_state(), before_tool)
        assert_close_tuple(
            "post-process-loss program pose %s" % command,
            program_pose(),
            before_program,
        )
        assert_close_tuple(
            "post-process-loss joints %s" % command,
            joint_pose(),
            before_joints,
        )
    log("TCPC tooling guards remain fail closed after headheadtwp loss")


def exercise_length_entry(tool, length, accepted, expected_error=None):
    mdi("G49")
    mdi("M61 Q%d" % tool)
    mdi("G43 H%d" % tool)
    before_program = program_pose()
    before_joints = joint_pose()
    if accepted:
        mdi("G43.4")
        assert_state(False, False, False, True)
        assert_close_tuple("length entry program continuity", program_pose(), before_program)
        assert_close_tuple("length entry joint continuity", joint_pose(), before_joints)
        assert_length_q("T%d length entry" % tool, length)
        mdi("G49.1")
        assert_state(False, False, False, False)
        log("T%d length %.6f accepted" % (tool, length))
    else:
        error_text = mdi_expect_error("G43.4", expected_error)
        assert_state(False, False, False, False)
        assert_close_tuple("rejected length program pose", program_pose(), before_program)
        assert_close_tuple("rejected length joints", joint_pose(), before_joints)
        log("T%d length %.6f rejected ok: %s" % (tool, length, error_text))
    mdi("G49")


def exercise_length_tcpc_round_trip(tool, length, b_deg, c_deg):
    mdi("G49")
    mdi("M61 Q%d" % tool)
    mdi("G43 H%d" % tool)
    mdi("G0 B0 C0")
    entry_program = program_pose()
    entry_joints = joint_pose()

    mdi("G43.4")
    assert_state(False, False, False, True)
    assert_close_tuple("T%d TCPC entry program continuity" % tool, program_pose(), entry_program)
    assert_close_tuple("T%d TCPC entry joint continuity" % tool, joint_pose(), entry_joints)

    target_program = entry_program[:3] + (b_deg, c_deg)
    mdi("G0 B%.6f C%.6f" % (b_deg, c_deg))
    assert_close_tuple("T%d TCPC rotated program pose" % tool, program_pose(), target_program)
    time.sleep(0.2)
    assert_close_tuple("T%d TCPC rotated TCP" % tool, current_tcp_pose(), target_program)
    assert_runtime_model(
        "T%d TCPC round trip L%.6f" % (tool, length),
        b_deg,
        c_deg,
        length,
    )
    if not all(math.isfinite(value) for value in joint_pose()):
        fail("T%d TCPC rotated joints are nonfinite" % tool)

    mdi("G0 B0 C0")
    assert_close_tuple("T%d TCPC return program pose" % tool, program_pose(), entry_program)
    return_joints = joint_pose()
    mdi("G49.1")
    assert_state(False, False, False, False)
    assert_close_tuple("T%d TCPC exit program continuity" % tool, program_pose(), entry_program)
    assert_close_tuple("T%d TCPC exit joint continuity" % tool, joint_pose(), return_joints)
    mdi("G49")
    log("T%d length %.6f nonzero-B/C TCPC round trip ok" % (tool, length))


def assert_state(active, valid, motion_enabled, tcpc_enabled):
    actual = (
        bool(hal.get_value("headheadtwp.active")),
        bool(hal.get_value("headheadtwp.valid")),
        bool(hal.get_value("headheadtwp.motion_enabled")),
        bool(hal.get_value("headheadtwp.tcpc_enabled")),
    )
    expected = (active, valid, motion_enabled, tcpc_enabled)
    if actual != expected:
        fail("unexpected TCPC/TWP state: actual=%s expected=%s" % (actual, expected))


c = linuxcnc.command()
s = linuxcnc.stat()
e = linuxcnc.error_channel()
ui = hal.component("test-ui")
ui.ready()

wait_for_linuxcnc_startup(s)

ini = linuxcnc.ini(os.environ["INI_FILE_NAME"])
if str(ini.find("TCPC", "LENGTH_MODEL_REQUIRED") or "").strip() != "1":
    fail("test INI did not load fail-closed LENGTH_MODEL_REQUIRED policy")
if not bool(hal.get_value("headheadkins.length-model.configured")):
    fail("test kinematics did not load lengthmodel=1")
if int(hal.get_value("headheadkins.length-model.expected-id")) != OFFLINE_MODEL.MODEL_ID:
    fail("test kinematics did not load the expected coefficient-set ID")

c.state(linuxcnc.STATE_ESTOP_RESET)
c.state(linuxcnc.STATE_ON)
time.sleep(0.5)
c.mode(linuxcnc.MODE_MANUAL)
time.sleep(0.2)
c.teleop_enable(0)
time.sleep(0.2)
for joint in range(5):
    c.home(joint)
    time.sleep(0.1)
wait_for_homed(s, 5)
c.teleop_enable(1)
time.sleep(0.2)

assert_state(False, False, False, False)
assert_close_tuple("startup TCPC origin", tcpc_origin(), (0.0, 0.0, 0.0), ORIGIN_TOL)
log("startup TCPC off ok")

mdi("T1")
mdi("S1000 M3")
error_text = mdi_expect_error("M6", "spindle is on")
log("M6 while spindle on rejected ok: %s" % error_text)
mdi("M5")
mdi("M6")

mdi("G17 G21 G40 G49 G54 G64 P0.01 G80 G90 G92.1 G94")
error_text = mdi_expect_error("G43.4", "activate a positive tool length offset")
assert_state(False, False, False, False)
log("G43.4 without G43 rejected ok: %s" % error_text)
mdi("G43 H1")
active_length = hal.get_value("motion.tooloffset.z")
if not math.isfinite(active_length) or math.fabs(active_length - 128.606729) > 1e-9:
    fail("T1 G43 length did not apply")
assert_length_q("T1 pre-entry", 128.606729)
mdi("G0 X%.6f Y%.6f Z%.6f B%.6f C%.6f" % START_POSE)
assert_close_tuple("start program pose", program_pose(), START_POSE)
start_joints = joint_pose()
log("start pose ok")

mdi("G0 B1.0 C0.0")
error_text = mdi_expect_error("G43.4", "requires B0.0000 C0.0000")
assert_state(False, False, False, False)
log("G43.4 away from B0/C0 rejected ok: %s" % error_text)
mdi("G0 B0.0 C0.0")
assert_close_tuple("returned to TCPC entry zero pose", program_pose(), START_POSE)
start_joints = joint_pose()
mdi("T2")

mdi("G43.4")
assert_state(False, False, False, True)
assert_close_tuple("G43.4 program pose continuity", program_pose(), START_POSE)
assert_close_tuple("G43.4 joint continuity", joint_pose(), start_joints)
assert_close_tuple("G43.4 TCPC origin", tcpc_origin(), ENTRY_ORIGIN, ORIGIN_TOL)
assert_close_tuple("G43.4 current TCP", current_tcp_pose(), START_POSE)
log("G43.4 entry continuity ok")

tcpc_tool_state = tool_state()
tcpc_program_pose = program_pose()
tcpc_joint_pose = joint_pose()

error_text = mdi_expect_error(
    "M61 Q1",
    "Cannot change current tool number while TCPC is active; exit TCPC with G49.1 first",
)
assert_state(False, False, False, True)
assert_tool_state("post rejected M61", tool_state(), tcpc_tool_state)
assert_close_tuple("post rejected M61 program pose", program_pose(), tcpc_program_pose)
assert_close_tuple("post rejected M61 joints", joint_pose(), tcpc_joint_pose)
log("M61 while TCPC active rejected ok: %s" % error_text)

error_text = mdi_expect_error(
    "M6",
    "Cannot change tools while TCPC is active; exit TCPC with G49.1 first",
)
assert_state(False, False, False, True)
assert_tool_state("post rejected M6", tool_state(), tcpc_tool_state)
assert_close_tuple("post rejected M6 program pose", program_pose(), tcpc_program_pose)
assert_close_tuple("post rejected M6 joints", joint_pose(), tcpc_joint_pose)
log("M6 while TCPC active rejected ok: %s" % error_text)

mdi("G43.4")
assert_state(False, False, False, True)
assert_close_tuple("idempotent G43.4 pose", program_pose(), START_POSE)
assert_close_tuple("idempotent G43.4 origin", tcpc_origin(), ENTRY_ORIGIN, ORIGIN_TOL)
log("idempotent G43.4 ok")

error_text = mdi_expect_error("G49", "TCPC is active")
assert_state(False, False, False, True)
assert_close_tuple("post rejected G49 pose", program_pose(), START_POSE)
log("G49 while TCPC active rejected ok: %s" % error_text)

error_text = mdi_expect_error("G43.1 Z1.0", "TCPC is active")
assert_state(False, False, False, True)
assert_close_tuple("post rejected G43.1 pose", program_pose(), START_POSE)
log("G43.1 while TCPC active rejected ok: %s" % error_text)

mdi("G0 B30.0 C90.0")
assert_state(False, False, False, True)
assert_close_tuple("rotated TCPC program pose", program_pose(), ROTATED_POSE)
time.sleep(0.2)
assert_close_tuple("rotated current TCP", current_tcp_pose(), ROTATED_POSE)
rotated_joint_x = joint_pose()[0]
if not math.isfinite(rotated_joint_x) or math.fabs(rotated_joint_x - start_joints[0]) < 1.0:
    fail("TCPC rotary move did not compensate X joint as expected")
assert_length_q("T1 rotated", 128.606729)
assert_length_diff("T1 length differential", 30.0, 90.0, 128.606729)
log("TCPC rotary compensation ok")

error_text = mdi_expect_error("G49.1", "TCPC entry orientation")
assert_state(False, False, False, True)
assert_close_tuple("post rejected G49.1 pose", program_pose(), ROTATED_POSE)
log("unsafe G49.1 rejected ok: %s" % error_text)

mdi("G0 B0.0 C0.0")
assert_state(False, False, False, True)
assert_close_tuple("returned entry pose", program_pose(), START_POSE)
entry_return_joints = joint_pose()
log("return to entry orientation ok")

mdi("G49.1")
assert_state(False, False, False, False)
assert_close_tuple("G49.1 program pose continuity", program_pose(), START_POSE)
assert_close_tuple("G49.1 joint continuity", joint_pose(), entry_return_joints)
assert_close_tuple("G49.1 TCPC origin cleared", tcpc_origin(), (0.0, 0.0, 0.0), ORIGIN_TOL)
log("G49.1 exit continuity ok")

exercise_length_entry(2, 99.997000, False, "outside the calibrated")
exercise_length_entry(3, 100.000000, True)
exercise_length_entry(4, 430.000000, True)
exercise_length_entry(5, 430.003000, False, "outside the calibrated")
exercise_length_entry(6, 425.022000, True)
exercise_length_entry(7, 128.606729, False, "X/Y offsets are unsupported")
exercise_length_entry(8, 99.999000, True)
exercise_length_entry(9, 430.001000, True)
exercise_length_entry(10, 114.677000, True)
exercise_length_entry(11, 229.407000, True)
exercise_length_entry(12, 411.810000, True)
exercise_length_entry(15, 200.000000, False, "A/B/C/U/V/W offsets are unsupported")
exercise_length_entry(16, 200.000000, False, "X/Y offsets are unsupported")
for tool in (17, 18, 19, 20, 21):
    exercise_length_entry(
        tool,
        200.000000,
        False,
        "A/B/C/U/V/W offsets are unsupported",
    )

exercise_runtime_model_equivalence()
exercise_length_tcpc_round_trip(13, 99.998000, -90.0, 276.75)
exercise_length_tcpc_round_trip(12, 411.810000, -90.0, 108.0)
exercise_length_tcpc_round_trip(6, 425.022000, 90.0, 195.0)
exercise_length_tcpc_round_trip(14, 430.002000, 57.25, 200.0)

error_text = mdi_expect_error("G68.2 B0 C0", "real-machine TWP entry is disabled")
assert_state(False, False, False, False)
log("G68.2 locked out while TCPC off ok: %s" % error_text)

mdi("M61 Q1")
mdi("G43 H1")
mdi("G43.4")
error_text = mdi_expect_error("G68.2 B0 C0", "real-machine TWP entry is disabled")
assert_state(False, False, False, True)
log("G68.2 locked out while TCPC on ok: %s" % error_text)

exercise_process_loss_tooling_guard()

sys.exit(0)
