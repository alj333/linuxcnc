#!/usr/bin/env python3

import csv
import io
import math
import os
from pathlib import Path
import sys
import time
import traceback

import hal
import linuxcnc


ROOT = Path(__file__).resolve().parents[3]
PROGRAM = ROOT / "nc_files/calibration/twp_sphere_grid_low_angle_t4.ngc"
CONFIG = ROOT / "configs/5th_axis_xyzbc_ssi_tcpc_probe_basic"
PASS_CSV = CONFIG / "twp-sphere-grid-low-angle-t4-passes.csv"
POSE_CSV = CONFIG / "twp-sphere-grid-low-angle-t4-poses.csv"
SUMMARY_CSV = CONFIG / "twp-sphere-grid-low-angle-t4-summary.csv"

TIMEOUT = 3600.0
MODEL_ID = 2026082601
TOOL_NUMBER = 4
TOOL_LENGTH = 229.407
MOTOR_LAYER_OFFSETS = (878.642799829, 645.600399981, -280.865200000)


def env_vector(name, default):
    text = os.environ.get(name)
    if text is None:
        return default
    values = tuple(float(value.strip()) for value in text.split(","))
    if len(values) != 3:
        raise ValueError("%s must contain three comma-separated values" % name)
    return values


START_B = 0.0
START_C = 0.0
CAMPAIGN_ID = 2026090103.0
ATTEMPT_ID = 1.0
G54_OFFSET = env_vector("TWP_SPHERE_TEST_G54", (17.125, -31.500, 8.750))
START_WORK = env_vector("TWP_SPHERE_TEST_START_WORK", (40.0, -25.0, 15.0))
SPHERE_RADIUS = 15.0
PROBE_RADIUS = 3.0
PROBE_OFFSET = 0.154742
ENVELOPE_RADIUS = SPHERE_RADIUS + PROBE_RADIUS - PROBE_OFFSET
INITIAL_CLEARANCE = 4.0
TOP_RADIUS = ENVELOPE_RADIUS + 5.0

LINEAR_TOL = 0.012
ROTARY_TOL = 1e-5
CENTER_TOL = 0.012
PREFLIGHT_TOL = 0.035
TRANSITION_CLEARANCE = 50.0


def normalize_angle(angle_deg):
    normalized = (angle_deg + 180.0) % 360.0 - 180.0
    return 180.0 if abs(normalized + 180.0) < 1e-9 else normalized


def pose_table():
    poses = []
    sequence = 0
    for c_deg in (0.0, 90.0, 180.0, 270.0):
        for magnitude in (5.0, 15.0, 30.0):
            for b_deg in (magnitude, -magnitude):
                sequence += 1
                if b_deg > 0.0:
                    euler = (normalize_angle(c_deg + 90.0), b_deg, -90.0)
                else:
                    euler = (normalize_angle(c_deg - 90.0), abs(b_deg), 90.0)
                poses.append((float(sequence), b_deg, c_deg) + euler)
    return tuple(poses)


POSES = pose_table()
EXPECTED_CONTACTS = 16 + 4 * len(POSES)


class TestFailure(RuntimeError):
    pass


def fail(message):
    raise TestFailure(message)


def log(message):
    print(message)
    sys.stdout.flush()


def vector_add(a, b):
    return tuple(a[index] + b[index] for index in range(3))


def vector_sub(a, b):
    return tuple(left - right for left, right in zip(a, b))


def vector_scale(vector, scale):
    return tuple(value * scale for value in vector)


def vector_dot(a, b):
    return sum(a[index] * b[index] for index in range(3))


def vector_norm(vector):
    return math.sqrt(vector_dot(vector, vector))


def dot_vector(prefix):
    return tuple(float(hal.get_value("%s.%s" % (prefix, axis))) for axis in "xyz")


def underscore_vector(prefix):
    return tuple(float(hal.get_value("%s_%s" % (prefix, axis))) for axis in "xyz")


def joint_pose():
    return tuple(float(hal.get_value("joint.%d.pos-cmd" % joint)) for joint in range(5))


def motor_pose():
    return tuple(
        float(hal.get_value("joint.%d.motor-pos-cmd" % joint))
        for joint in range(5)
    )


def assert_coordinate_layers(label):
    joints = joint_pose()
    motors = motor_pose()
    assert_vector(
        label + " XYZ homing motor offsets",
        vector_sub(joints[:3], motors[:3]),
        MOTOR_LAYER_OFFSETS,
        2e-6,
    )
    if max(abs(value) for value in vector_sub(joints[:3], motors[:3])) < 100.0:
        fail(label + " does not reproduce the physical motor/joint separation")
    state_pose = tuple(
        float(hal.get_value("headheadtwp.current_joint_%s" % axis))
        for axis in "xyzbc"
    )
    assert_vector(label + " TWP state machine pose", state_pose, joints, 2e-6)


def physical_tcp():
    joints = joint_pose()
    evaluated_tool = dot_vector("headheadkins.tool-offset")
    return tuple(
        joints[axis] + evaluated_tool[axis]
        for axis in range(3)
    )


def assert_scalar(label, actual, expected, tolerance):
    if not math.isfinite(actual) or abs(actual - expected) > tolerance:
        fail(
            "%s mismatch: actual=%.12g expected=%.12g tolerance=%.12g"
            % (label, actual, expected, tolerance)
        )


def assert_vector(label, actual, expected, tolerance):
    if len(actual) != len(expected):
        fail("%s length mismatch: actual=%s expected=%s" % (label, actual, expected))
    delta = vector_sub(actual, expected)
    if any(not math.isfinite(value) or abs(value) > tolerance for value in delta):
        fail(
            "%s mismatch: actual=%s expected=%s delta=%s tolerance=%.12g"
            % (label, actual, expected, delta, tolerance)
        )


def check_errors(error_channel):
    while True:
        error = error_channel.poll()
        if error is None:
            return
        code, message = error
        if code in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
            fail("LinuxCNC error %s: %s" % (code, message))
        log("LinuxCNC message %s: %s" % (code, message))


def drain_errors(error_channel):
    while error_channel.poll() is not None:
        pass


def wait_for_startup(status):
    deadline = time.monotonic() + TIMEOUT
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
        time.sleep(0.05)
    fail("timeout waiting for LinuxCNC startup")


def wait_for_homed(status):
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        status.poll()
        if sum(status.homed[:5]) == 5:
            return
        time.sleep(0.02)
    fail("timeout waiting for all joints to home: %s" % (status.homed[:5],))


def wait_for_idle(status, errors):
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        status.poll()
        check_errors(errors)
        if (
            status.exec_state == linuxcnc.EXEC_DONE
            and status.interp_state == linuxcnc.INTERP_IDLE
            and status.inpos
        ):
            return
        time.sleep(0.01)
    fail("timeout waiting for interpreter idle")


def mdi(command):
    drain_errors(errors)
    controller.mode(linuxcnc.MODE_MDI)
    controller.wait_complete()
    controller.mdi(command)
    controller.wait_complete()
    wait_for_idle(status, errors)


def csv_rows(data, path):
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        fail("%s is not ASCII CSV: %s" % (path, exc))
    return list(csv.reader(io.StringIO(text)))


def appended_rows(path, baseline):
    current = path.read_bytes()
    if not current.startswith(baseline):
        fail("production CSV prefix changed instead of being append-only: %s" % path)
    baseline_rows = csv_rows(baseline, path)
    current_rows = csv_rows(current, path)
    return current_rows[len(baseline_rows) :]


def parse_numeric_row(label, row, expected_fields):
    if len(row) != expected_fields:
        fail("%s has %d fields, expected %d: %s" % (label, len(row), expected_fields, row))
    try:
        values = tuple(float(value) for value in row)
    except ValueError as exc:
        fail("%s contains a nonnumeric value: %s" % (label, exc))
    if not all(math.isfinite(value) for value in values):
        fail("%s contains a nonfinite value: %s" % (label, values))
    return values


def assert_model_and_tool(label):
    status.poll()
    if status.tool_in_spindle != TOOL_NUMBER:
        fail("%s tool mismatch: %s" % (label, status.tool_in_spindle))
    if int(hal.get_value("iocontrol.0.tool-number")) != TOOL_NUMBER:
        fail("%s iocontrol tool number is not T4" % label)
    assert_scalar(
        label + " canonical tool length",
        float(hal.get_value("motion.tooloffset.z")),
        TOOL_LENGTH,
        2e-6,
    )
    assert_scalar(
        label + " kinematics tool length",
        float(hal.get_value("headheadkins.active-tool-offset.z")),
        TOOL_LENGTH,
        2e-6,
    )
    if not bool(hal.get_value("headheadkins.length-model.configured")):
        fail(label + " length model is not configured")
    if not bool(hal.get_value("headheadkins.length-model.valid")):
        fail(label + " length model is invalid")
    assert_scalar(
        label + " model ID",
        float(hal.get_value("headheadkins.length-model.id")),
        MODEL_ID,
        0.1,
    )
    assert_scalar(
        label + " model q",
        float(hal.get_value("headheadkins.length-model.q")),
        0.0,
        1e-9,
    )
    assert_scalar(
        label + " model fault",
        float(hal.get_value("headheadkins.length-model.fault-code")),
        0.0,
        0.1,
    )
    if not bool(hal.get_value("headheadkins.sim-bharm-enable")):
        fail(label + " commissioned correction is disabled")


def assert_world_final():
    if not bool(hal.get_value("headheadkins.kinstype-is-world")):
        fail("final state is not world kinematics")
    if bool(hal.get_value("headheadkins.kinstype-is-twp")):
        fail("final state still selects TWP kinematics")
    if not bool(hal.get_value("headheadkins.kinstype-frame-ready")):
        fail("final world kinematics frame is not ready")
    if bool(hal.get_value("headheadkins.synchronized-twp-enable")):
        fail("final state retained synchronized TWP authorization")
    for pin in (
        "headheadtwp.valid",
        "headheadtwp.active",
        "headheadtwp.motion_enabled",
        "headheadtwp.synchronized_frame",
        "headheadtwp.origin_defined",
        "headheadtwp.orientation_defined",
    ):
        if bool(hal.get_value(pin)):
            fail("final G69 did not clear %s" % pin)
    if bool(hal.get_value("headheadtwp.tcpc_enabled")):
        fail("final G69 unexpectedly enabled TCPC")


def validate_logs(pass_baseline, pose_baseline, summary_baseline, sphere_center):
    pass_rows = appended_rows(PASS_CSV, pass_baseline)
    pose_rows = appended_rows(POSE_CSV, pose_baseline)
    summary_rows = appended_rows(SUMMARY_CSV, summary_baseline)
    expected_pass_count = len(POSES) + 4
    if len(pass_rows) != expected_pass_count:
        fail("actual program appended %d pass rows, expected %d" % (len(pass_rows), expected_pass_count))
    if len(pose_rows) != len(POSES):
        fail("actual program appended %d pose rows, expected %d" % (len(pose_rows), len(POSES)))
    if len(summary_rows) != 1:
        fail("actual program appended %d summary rows, expected 1" % len(summary_rows))

    summary = parse_numeric_row("grid summary row", summary_rows[0], 23)
    assert_scalar("summary schema", summary[0], 1.0, 0.01)
    assert_scalar("summary campaign", summary[1], CAMPAIGN_ID, 0.1)
    assert_scalar("summary attempt", summary[2], ATTEMPT_ID, 0.01)
    assert_scalar("summary start pose", summary[3], 1.0, 0.01)
    assert_scalar("summary last pose", summary[4], float(len(POSES)), 0.01)
    assert_scalar("summary return B", summary[5], START_B, ROTARY_TOL)
    assert_scalar("summary return C", summary[6], START_C, ROTARY_TOL)
    assert_scalar("summary tool length", summary[7], TOOL_LENGTH, 2e-6)
    assert_scalar("summary probe offset", summary[8], PROBE_OFFSET, 2e-6)
    world_open = summary[9:12]
    world_close = summary[12:15]
    assert_vector("WORLD opening physical center", world_open, sphere_center, CENTER_TOL)
    assert_vector("WORLD closing physical center", world_close, sphere_center, CENTER_TOL)
    if summary[15] > 0.050:
        fail("grid WORLD closure exceeds 0.050 mm: %.9f" % summary[15])
    for field, value in zip(("world open", "world close"), summary[16:18]):
        if value > 0.100:
            fail("%s pair delta exceeds 0.100 mm: %.9f" % (field, value))
    for field, value in zip(("world open", "world close"), summary[18:20]):
        if not 29.9 <= value <= 30.5:
            fail("%s diameter out of range: %.9f" % (field, value))
    for field, value in zip(("world open", "world close"), summary[20:22]):
        if value > 0.250:
            fail("%s residual exceeds 0.250 mm: %.9f" % (field, value))
    assert_scalar("summary gated edges", summary[22], EXPECTED_CONTACTS, 0.1)

    expected_phase = (0.0, 0.0) + tuple(pose[0] for pose in POSES) + (99.0, 99.0)
    expected_pass = (1.0, 2.0) + (1.0,) * len(POSES) + (1.0, 2.0)
    expected_mode = (0.0, 0.0) + (1.0,) * len(POSES) + (0.0, 0.0)
    expected_b = (START_B, START_B) + tuple(pose[1] for pose in POSES) + (START_B, START_B)
    expected_c = (START_C, START_C) + tuple(pose[2] for pose in POSES) + (START_C, START_C)
    for index, row in enumerate(pass_rows):
        values = parse_numeric_row("pass row %d" % (index + 1), row, 14)
        assert_scalar("pass schema", values[0], 1.0, 0.01)
        assert_scalar("pass campaign", values[1], CAMPAIGN_ID, 0.1)
        assert_scalar("pass attempt", values[2], ATTEMPT_ID, 0.01)
        assert_scalar("pass phase", values[3], expected_phase[index], 0.01)
        assert_scalar("pass ID", values[4], expected_pass[index], 0.01)
        assert_scalar("pass TWP mode", values[5], expected_mode[index], 0.01)
        assert_scalar("pass B", values[6], expected_b[index], ROTARY_TOL)
        assert_scalar("pass C", values[7], expected_c[index], ROTARY_TOL)
        if not 29.9 <= values[11] <= 30.5:
            fail("pass %d V diameter out of range: %.9f" % (index + 1, values[11]))
        if values[12] > 0.250:
            fail("pass %d radial residual is %.9f" % (index + 1, values[12]))
        assert_scalar("pass cumulative edges", values[13], 4.0 * (index + 1), 0.1)

    for index, (row, expected) in enumerate(zip(pose_rows, POSES), 1):
        values = parse_numeric_row("pose row %d" % index, row, 21)
        sequence, b_deg, c_deg, i_deg, j_deg, k_deg = expected
        assert_scalar("pose schema", values[0], 1.0, 0.01)
        assert_scalar("pose campaign", values[1], CAMPAIGN_ID, 0.1)
        assert_scalar("pose attempt", values[2], ATTEMPT_ID, 0.01)
        for label, actual, wanted in zip(
            ("sequence", "B", "C", "Euler I", "Euler J", "Euler K"),
            values[3:9],
            (sequence, b_deg, c_deg, i_deg, j_deg, k_deg),
        ):
            assert_scalar("pose %d %s" % (index, label), actual, wanted, ROTARY_TOL)
        assert_scalar("pose tool length", values[9], TOOL_LENGTH, 2e-6)
        assert_scalar("pose probe offset", values[10], PROBE_OFFSET, 2e-6)
        world_center = values[11:14]
        delta = values[14:17]
        assert_vector("pose %d physical center" % index, world_center, sphere_center, CENTER_TOL)
        assert_vector("pose %d opening delta" % index, delta, vector_sub(world_center, world_open), 2e-6)
        assert_scalar("pose %d error norm" % index, values[17], vector_norm(delta), 2e-6)
        if values[17] > 0.050:
            fail("pose %d transformed center error exceeds 0.050 mm: %.9f" % (index, values[17]))
        if not 29.9 <= values[18] <= 30.5:
            fail("pose %d V diameter out of range: %.9f" % (index, values[18]))
        if values[19] > 0.250:
            fail("pose %d residual exceeds 0.250 mm: %.9f" % (index, values[19]))
        assert_scalar("pose cumulative edges", values[20], 8.0 + 4.0 * index, 0.1)
    return summary


def run_actual_program(sphere_center, start_tcp, tool_w, pass_baseline, pose_baseline, summary_baseline):
    global controller, status, errors

    start_joints = joint_pose()
    start_counts = tuple(float(hal.get_value("counter.%d.position" % index)) for index in range(3))
    controller.program_open(str(PROGRAM))
    controller.wait_complete()
    controller.mode(linuxcnc.MODE_AUTO)
    controller.wait_complete()
    drain_errors(errors)
    controller.auto(linuxcnc.AUTO_RUN, 0)

    deadline = time.monotonic() + TIMEOUT
    paused_once = False
    resumed = False
    raw_active = False
    contact_count = 0
    abnormal_seen = False
    fault_seen = False
    minimum_b = START_B
    maximum_b = START_B
    minimum_c = START_C
    maximum_c = START_C
    rotary_motion_seen = False
    minimum_transition_distance = math.inf
    twp_entry_count = 0
    twp_exit_count = 0
    preflight_count = 0
    active_pose = None
    active_contact_start = None
    twp_entry_tcp = None
    plane_z = None
    preflight_max_projection = -math.inf
    preflight_max_perpendicular = 0.0
    prior_twp = False
    prior_probe = False
    min_contact_distance = math.inf
    max_contact_distance = 0.0
    minimum_nonprobe_distance = math.inf
    prior_joints = start_joints
    seen_poses = []

    try:
        while time.monotonic() < deadline:
            status.poll()
            check_errors(errors)
            joints = joint_pose()
            tcp = physical_tcp()
            minimum_b = min(minimum_b, joints[3])
            maximum_b = max(maximum_b, joints[3])
            minimum_c = min(minimum_c, joints[4])
            maximum_c = max(maximum_c, joints[4])
            abnormal_seen = abnormal_seen or bool(hal.get_value("tcpc-probe-abnormal-level"))
            fault_seen = fault_seen or bool(hal.get_value("tcpc_probe_fault_pause.out"))

            twp_active = bool(hal.get_value("headheadkins.kinstype-is-twp"))
            if twp_active and not prior_twp:
                if twp_entry_count >= len(POSES):
                    fail("observed an unexpected extra TWP entry")
                active_pose = POSES[twp_entry_count]
                active_contact_start = 8 + 4 * twp_entry_count
                if contact_count != active_contact_start:
                    fail(
                        "TWP pose %d activated after %d contacts, expected %d"
                        % (twp_entry_count + 1, contact_count, active_contact_start)
                    )
                assert_scalar("TWP entry B", joints[3], active_pose[1], ROTARY_TOL)
                assert_scalar("TWP entry C", joints[4], active_pose[2], ROTARY_TOL)
                twp_entry_tcp = tcp
                plane_z = underscore_vector("headheadtwp.plane_z")
                assert_scalar("captured plane Z norm", vector_norm(plane_z), 1.0, 2e-4)
                preflight_max_projection = -math.inf
                preflight_max_perpendicular = 0.0
                seen_poses.append(active_pose[:3])
                twp_entry_count += 1
            if prior_twp and not twp_active:
                if active_pose is None:
                    fail("TWP exit had no active pose")
                expected_exit_contacts = 8 + 4 * twp_exit_count + 4
                if contact_count != expected_exit_contacts:
                    fail(
                        "TWP pose %d cancelled after %d contacts, expected %d"
                        % (twp_exit_count + 1, contact_count, expected_exit_contacts)
                    )
                assert_scalar("TWP exit B", joints[3], active_pose[1], ROTARY_TOL)
                assert_scalar("TWP exit C", joints[4], active_pose[2], ROTARY_TOL)
                twp_exit_count += 1
                active_pose = None
                active_contact_start = None
                twp_entry_tcp = None
                plane_z = None

            motion_type = int(hal.get_value("motion.motion-type"))
            probing = bool(status.probing) or motion_type == 5
            b_step = abs(joints[3] - prior_joints[3])
            c_step = abs(((joints[4] - prior_joints[4] + 540.0) % 360.0) - 180.0)
            rotary_step = b_step > 1e-7 or c_step > 1e-7
            distance = vector_norm(vector_sub(tcp, sphere_center))
            if rotary_step:
                rotary_motion_seen = True
                minimum_transition_distance = min(minimum_transition_distance, distance)
            if rotary_step and (prior_twp or twp_active):
                fail("B/C moved while TWP kinematics was active")
            if rotary_step and probing:
                fail("B/C moved during a probing motion")
            if rotary_step and not bool(hal.get_value("headheadkins.kinstype-is-world")):
                fail("B/C transition did not remain in world kinematics")
            if joints[3] < -30.0 - ROTARY_TOL or joints[3] > 30.0 + ROTARY_TOL:
                fail("B left the reviewed low-angle range: %.9f" % joints[3])
            if joints[4] < -ROTARY_TOL or joints[4] > 270.0 + ROTARY_TOL:
                fail("C left the reviewed quadrant range: %.9f" % joints[4])
            if twp_active:
                if active_pose is None:
                    fail("active TWP has no expected grid pose")
                assert_scalar("active TWP B", joints[3], active_pose[1], ROTARY_TOL)
                assert_scalar("active TWP C", joints[4], active_pose[2], ROTARY_TOL)

            if (
                twp_active
                and contact_count == active_contact_start
                and twp_entry_tcp is not None
                and not probing
            ):
                displacement = vector_sub(tcp, twp_entry_tcp)
                projection = vector_dot(displacement, plane_z)
                perpendicular = vector_sub(displacement, vector_scale(plane_z, projection))
                preflight_max_projection = max(preflight_max_projection, projection)
                preflight_max_perpendicular = max(
                    preflight_max_perpendicular, vector_norm(perpendicular)
                )
            if (
                twp_active
                and contact_count == active_contact_start
                and probing
                and not prior_probe
            ):
                assert_scalar(
                    "pose %d TWP +Z preflight maximum" % twp_entry_count,
                    preflight_max_projection,
                    1.0,
                    PREFLIGHT_TOL,
                )
                if preflight_max_perpendicular > PREFLIGHT_TOL:
                    fail(
                        "pose %d TWP preflight perpendicular error is %.9f"
                        % (twp_entry_count, preflight_max_perpendicular)
                    )
                assert_vector(
                    "pose %d TWP preflight return closure" % twp_entry_count,
                    tcp,
                    twp_entry_tcp,
                    PREFLIGHT_TOL,
                )
                preflight_count += 1

            gate_open = bool(hal.get_value("tcpc_probe_motion_window.out"))
            if probing and gate_open and not raw_active and distance <= ENVELOPE_RADIUS:
                hal.set_p("and2.0.in0", "1")
                raw_active = True
                contact_count += 1
                min_contact_distance = min(min_contact_distance, distance)
                max_contact_distance = max(max_contact_distance, distance)
            elif not probing and raw_active:
                hal.set_p("and2.0.in0", "0")
                raw_active = False
            if not probing:
                minimum_nonprobe_distance = min(minimum_nonprobe_distance, distance)

            if status.paused and not paused_once:
                paused_once = True
                if contact_count != 0:
                    fail("the actual program contacted the sphere before its M0")
                assert_vector("M0 joint pose", joint_pose(), start_joints, ROTARY_TOL)
                assert_vector("M0 physical TCP", tcp, start_tcp, LINEAR_TOL)
                assert_model_and_tool("M0")
                controller.auto(linuxcnc.AUTO_RESUME)
                resumed = True

            if (
                resumed
                and status.interp_state == linuxcnc.INTERP_IDLE
                and status.exec_state == linuxcnc.EXEC_DONE
                and status.inpos
            ):
                break
            prior_twp = twp_active
            prior_probe = probing
            prior_joints = joints
            time.sleep(0.001)
        else:
            fail(
                "timeout running actual grid program: contacts=%d entries=%d motion-type=%d"
                % (contact_count, twp_entry_count, int(hal.get_value("motion.motion-type")))
            )
    finally:
        hal.set_p("and2.0.in0", "0")

    if not paused_once or not resumed:
        fail("actual grid program did not stop at and resume from its single M0")
    if contact_count != EXPECTED_CONTACTS:
        fail("simulator generated %d contacts, expected %d" % (contact_count, EXPECTED_CONTACTS))
    if abnormal_seen or fault_seen:
        fail("valid simulated contacts entered the abnormal/fault path")
    if not rotary_motion_seen:
        fail("grid did not execute rotary motion")
    if tuple(seen_poses) != tuple(pose[:3] for pose in POSES):
        fail("observed TWP pose order differs from the reviewed grid")
    assert_scalar("minimum reached B", minimum_b, -30.0, ROTARY_TOL)
    assert_scalar("maximum reached B", maximum_b, 30.0, ROTARY_TOL)
    assert_scalar("minimum reached C", minimum_c, 0.0, ROTARY_TOL)
    assert_scalar("maximum reached C", maximum_c, 270.0, ROTARY_TOL)
    if twp_entry_count != len(POSES) or twp_exit_count != len(POSES):
        fail(
            "expected %d TWP entries/exits, observed %d/%d"
            % (len(POSES), twp_entry_count, twp_exit_count)
        )
    if preflight_count != len(POSES):
        fail("validated %d TWP preflights, expected %d" % (preflight_count, len(POSES)))
    if minimum_transition_distance < TRANSITION_CLEARANCE:
        fail(
            "rotary transition approached the sphere to %.9f mm; limit is %.3f mm"
            % (minimum_transition_distance, TRANSITION_CLEARANCE)
        )
    assert_scalar("minimum contact envelope", min_contact_distance, ENVELOPE_RADIUS, 0.006)
    assert_scalar("maximum contact envelope", max_contact_distance, ENVELOPE_RADIUS, 0.006)
    if minimum_nonprobe_distance < ENVELOPE_RADIUS - 0.012:
        fail(
            "non-probing motion penetrated the sphere envelope: minimum distance %.9f"
            % minimum_nonprobe_distance
        )

    final_counts = tuple(float(hal.get_value("counter.%d.position" % index)) for index in range(3))
    for index, label in enumerate(("raw", "mux", "gated")):
        assert_scalar(
            label + " sticky edge delta",
            final_counts[index] - start_counts[index],
            EXPECTED_CONTACTS,
            0.1,
        )
    for pin in (
        "t_probe-in",
        "probe-mux",
        "motion.probe-input",
        "tcpc_probe_gate_ignore.out",
        "tcpc-probe-abnormal-level",
        "tcpc_probe_fault_pause.out",
    ):
        if bool(hal.get_value(pin)):
            fail("probe path did not finish clear: %s" % pin)

    summary = validate_logs(
        pass_baseline,
        pose_baseline,
        summary_baseline,
        sphere_center,
    )
    assert_world_final()
    assert_model_and_tool("final")
    final_joints = joint_pose()
    assert_scalar("final B", final_joints[3], START_B, ROTARY_TOL)
    assert_scalar("final C", final_joints[4], START_C, ROTARY_TOL)

    expected_final = vector_add(
        vector_sub(sphere_center, vector_scale(tool_w, TOP_RADIUS)),
        (0.0, 0.0, 25.0),
    )
    final_tcp = physical_tcp()
    assert_vector("final 25 mm safe lift", final_tcp, expected_final, CENTER_TOL)
    if vector_norm(vector_sub(final_tcp, sphere_center)) <= TOP_RADIUS:
        fail("final physical TCP is not clear of the sphere")

    log(
        "actual TWP low-angle grid passed: 24 poses, 24 entries/exits, "
        "%d contacts, world closure %.6f mm"
        % (EXPECTED_CONTACTS, summary[15])
    )
    log(
        "minimum rotary-transition clearance %.6f mm; final TCP %s"
        % (minimum_transition_distance, tuple(round(value, 6) for value in final_tcp))
    )

def main():
    global controller, status, errors

    if not PROGRAM.is_file():
        fail("actual production program is missing: %s" % PROGRAM)
    pass_baseline = PASS_CSV.read_bytes()
    pose_baseline = POSE_CSV.read_bytes()
    summary_baseline = SUMMARY_CSV.read_bytes()

    controller = linuxcnc.command()
    status = linuxcnc.stat()
    errors = linuxcnc.error_channel()
    ui = hal.component("test-ui")
    ui.ready()

    wait_for_startup(status)
    controller.state(linuxcnc.STATE_ESTOP_RESET)
    controller.state(linuxcnc.STATE_ON)
    time.sleep(0.3)
    controller.mode(linuxcnc.MODE_MANUAL)
    controller.wait_complete()
    controller.teleop_enable(0)
    time.sleep(0.1)
    for joint in range(5):
        controller.home(joint)
        time.sleep(0.05)
    wait_for_homed(status)
    controller.teleop_enable(1)
    time.sleep(0.1)
    assert_coordinate_layers("homed")

    mdi("G17 G21 G40 G49 G54 G64 P0.001 G80 G90 G92.1 G94 M5")
    mdi(
        "G10 L2 P1 X%.6f Y%.6f Z%.6f R0"
        % (G54_OFFSET[0], G54_OFFSET[1], G54_OFFSET[2])
    )
    mdi("G54")
    status.poll()
    assert_vector("nonzero G54 XYZ", tuple(status.g5x_offset[:3]), G54_OFFSET, 1e-6)
    if any(abs(value) > 1e-9 for value in status.g5x_offset[3:9]):
        fail("G54 rotary/UVW layers are not zero: %s" % (tuple(status.g5x_offset),))
    assert_scalar("G54 XY rotation", float(status.rotation_xy), 0.0, 1e-9)

    mdi("M61 Q4")
    mdi("G43 H4")
    mdi("G0 B%.9f C%.9f" % (START_B, START_C))
    mdi("G0 X%.6f Y%.6f Z%.6f" % START_WORK)
    assert_coordinate_layers("sphere setup")
    assert_model_and_tool("setup")
    assert_world_final()

    start_tcp = physical_tcp()
    tool_w = dot_vector("headheadkins.tool-frame-w")
    assert_scalar("world tool W norm", vector_norm(tool_w), 1.0, 2e-4)
    sphere_center = vector_add(
        start_tcp,
        vector_scale(tool_w, ENVELOPE_RADIUS + INITIAL_CLEARANCE),
    )
    log(
        "fixed simulated sphere center %s from start TCP %s at B%.6f C%.6f"
        % (
            tuple(round(value, 6) for value in sphere_center),
            tuple(round(value, 6) for value in start_tcp),
            START_B,
            START_C,
        )
    )
    run_actual_program(
        sphere_center,
        start_tcp,
        tool_w,
        pass_baseline,
        pose_baseline,
        summary_baseline,
    )


if __name__ == "__main__":
    try:
        main()
    except TestFailure as exc:
        print("TEST FAILURE: %s" % exc)
        sys.stdout.flush()
        try:
            hal.set_p("and2.0.in0", "0")
            controller.abort()
        except Exception:
            pass
        sys.exit(1)
    except Exception:
        traceback.print_exc()
        sys.stdout.flush()
        try:
            hal.set_p("and2.0.in0", "0")
            controller.abort()
        except Exception:
            pass
        sys.exit(1)
