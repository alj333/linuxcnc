#!/usr/bin/env python3

import math
import os
from pathlib import Path
import signal
import sys
import time
import traceback

import hal
import linuxcnc


TIMEOUT = 60.0
STATIONARY_TIME = 1.0
LINEAR_TOL = 1e-6
ROTARY_TOL = 1e-6
ZERO_TOL = 1e-12

MODEL_ID = 2026082601
T4_LENGTH = 229.407000
START_XYZ = (400.0, 250.0, -150.0)
G54_OFFSET = (123.456, -78.900, 12.250)
ACTIVE_BC = (5.0, 0.0)

CONFIG_DIR = Path(__file__).resolve().parent
STATE_SCRIPT_NAME = "headhead_twp_state_tcpc_off.py"
STAGE1_MARKER = CONFIG_DIR / ".component-loss-stage1.ok"


class TestFailure(RuntimeError):
    pass


def fail(message):
    raise TestFailure(message)


def log(message):
    print(message)
    sys.stdout.flush()


def hal_float(name):
    return float(hal.get_value(name))


def hal_int(name):
    return int(hal.get_value(name))


def hal_bool(name):
    return bool(hal.get_value(name))


def dot_vector(prefix):
    return tuple(hal_float("%s.%s" % (prefix, axis)) for axis in "xyz")


def underscore_vector(prefix):
    return tuple(hal_float("%s_%s" % (prefix, axis)) for axis in "xyz")


def joint_pose():
    return tuple(hal_float("joint.%d.motor-pos-cmd" % joint) for joint in range(5))


def physical_tcp():
    joints = joint_pose()
    tool_offset = dot_vector("headheadkins.tool-offset")
    return tuple(
        joints[axis] + tool_offset[axis]
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
        fail("%s length mismatch: %s != %s" % (label, actual, expected))
    delta = tuple(actual[index] - expected[index] for index in range(len(actual)))
    if any(not math.isfinite(value) or abs(value) > tolerance for value in delta):
        fail(
            "%s mismatch: actual=%s expected=%s delta=%s tolerance=%.12g"
            % (label, actual, expected, delta, tolerance)
        )


def wait_for_linuxcnc_startup(status):
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
    deadline = time.monotonic() + TIMEOUT
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


def enable_and_home():
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


def assert_world_mode(label):
    world = hal_bool("headheadkins.kinstype-is-world")
    twp = hal_bool("headheadkins.kinstype-is-twp")
    if not world or twp or not hal_bool("headheadkins.kinstype-frame-ready"):
        fail("%s is not ready, one-hot world kinematics" % label)
    assert_scalar(
        label + " requested switchkins type",
        hal_float("motion.switchkins-type"),
        0.0,
        ZERO_TOL,
    )
    if hal_bool("headheadkins.synchronized-twp-enable"):
        fail("%s retained synchronized TWP authorization" % label)


def assert_twp_mode(label):
    world = hal_bool("headheadkins.kinstype-is-world")
    twp = hal_bool("headheadkins.kinstype-is-twp")
    if world or not twp or not hal_bool("headheadkins.kinstype-frame-ready"):
        fail("%s is not ready, one-hot TWP kinematics" % label)
    assert_scalar(
        label + " requested switchkins type",
        hal_float("motion.switchkins-type"),
        1.0,
        ZERO_TOL,
    )
    if not hal_bool("headheadkins.synchronized-twp-enable"):
        fail("%s lacks synchronized TWP authorization" % label)
    if hal_bool("headheadkins.tcpc-enable"):
        fail("%s unexpectedly enabled the separate TCPC mode" % label)


def state_component_pids():
    matches = []
    for proc_entry in Path("/proc").iterdir():
        if not proc_entry.name.isdigit():
            continue
        try:
            raw = (proc_entry / "cmdline").read_bytes()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        arguments = [
            argument.decode("utf-8", errors="replace")
            for argument in raw.split(b"\0")
            if argument
        ]
        if any(Path(argument).name == STATE_SCRIPT_NAME for argument in arguments):
            matches.append(int(proc_entry.name))
    return sorted(matches)


def require_single_state_component(label):
    pids = state_component_pids()
    if len(pids) != 1:
        fail("%s expected one %s process, found %s" % (label, STATE_SCRIPT_NAME, pids))
    return pids[0]


def require_registered_state_component(label):
    if not hal.component_exists("headheadtwp"):
        fail("%s has no registered headheadtwp HAL component" % label)
    if not hal.component_is_ready("headheadtwp"):
        fail("%s headheadtwp HAL component is not ready" % label)


def component_pin_available():
    try:
        hal.get_value("headheadtwp.active")
    except Exception:
        return False
    return True


def commissioned_zero_plane_axes():
    b = math.radians(hal_float("headheadtwp.b_zero_offset"))
    c = math.radians(hal_float("headheadtwp.c_zero_offset"))
    return (
        (math.cos(c) * math.cos(b), math.sin(c) * math.cos(b), -math.sin(b)),
        (-math.sin(c), math.cos(c), 0.0),
        (math.cos(c) * math.sin(b), math.sin(c) * math.sin(b), math.cos(b)),
    )


def assert_stationary(label, duration, expected_joints=None, expected_tcp=None):
    if expected_joints is None:
        expected_joints = joint_pose()
    if expected_tcp is None:
        expected_tcp = physical_tcp()
    deadline = time.monotonic() + duration
    samples = 0
    while time.monotonic() < deadline:
        status.poll()
        if not status.inpos:
            fail("%s left motion.in-position" % label)
        current_joints = joint_pose()
        current_tcp = physical_tcp()
        assert_vector(
            label + " linear joints",
            current_joints[:3],
            expected_joints[:3],
            LINEAR_TOL,
        )
        assert_vector(
            label + " rotary joints",
            current_joints[3:],
            expected_joints[3:],
            ROTARY_TOL,
        )
        assert_vector(label + " physical TCP", current_tcp, expected_tcp, LINEAR_TOL)
        samples += 1
        time.sleep(0.005)
    if samples < 10:
        fail("%s captured too few stationary samples: %d" % (label, samples))


def assert_active_state():
    assert_twp_mode("stage-one active TWP")
    for pin in ("valid", "active", "motion_enabled"):
        if not hal_bool("headheadtwp.%s" % pin):
            fail("stage-one active TWP left headheadtwp.%s false" % pin)
    if hal_bool("headheadtwp.tcpc_enabled"):
        fail("stage-one active TWP unexpectedly enabled public TCPC mode")
    if hal_int("headheadtwp.state_code") != 3:
        fail("stage-one TWP state code is not ACTIVE")
    if hal_int("headheadtwp.transaction_fault") != 0:
        fail("stage-one TWP transaction has a fault")
    if hal_bool("headheadkins.tcpc-enable"):
        fail("stage-one TWP leaked into the kinematics TCPC input")
    assert_scalar("stage-one reached B", joint_pose()[3], ACTIVE_BC[0], ROTARY_TOL)
    assert_scalar("stage-one reached C", joint_pose()[4], ACTIVE_BC[1], ROTARY_TOL)
    if not all(math.isfinite(value) for value in dot_vector("headheadkins.twp-coordinate-offset")):
        fail("stage-one TWP coordinate layer is nonfinite")
    assert_vector(
        "stage-one state/kinematics captured origin agreement",
        dot_vector("headheadkins.twp-captured-origin"),
        underscore_vector("headheadtwp.twp_origin"),
        LINEAR_TOL,
    )


def run_loss_stage():
    enable_and_home()
    mdi("G17 G21 G40 G49 G54 G64 P0.01 G80 G90 G92.1 G94")
    mdi(
        "G10 L2 P1 X%.6f Y%.6f Z%.6f"
        % (G54_OFFSET[0], G54_OFFSET[1], G54_OFFSET[2])
    )
    mdi("G54")
    assert_world_mode("stage-one startup")

    mdi("T4 M6")
    mdi("G43 H4")
    assert_scalar(
        "stage-one active T4 length",
        hal_float("motion.tooloffset.z"),
        T4_LENGTH,
        ZERO_TOL,
    )
    if hal_int("headheadkins.length-model.id") != MODEL_ID:
        fail("stage-one commissioned length-model ID is not active")
    if not hal_bool("headheadkins.length-model.valid"):
        fail("stage-one commissioned length model is invalid")

    mdi(
        "G0 X%.6f Y%.6f Z%.6f B0 C0"
        % (START_XYZ[0], START_XYZ[1], START_XYZ[2])
    )
    before_tcpc = joint_pose()
    mdi("G43.4")
    assert_vector("stage-one G43.4 continuity", joint_pose(), before_tcpc, LINEAR_TOL)
    mdi("G49.1")
    assert_vector("stage-one G49.1 continuity", joint_pose(), before_tcpc, LINEAR_TOL)
    if hal_bool("headheadtwp.tcpc_enabled"):
        fail("stage-one G49.1 did not leave TCPC off")
    mdi("G0 B%.6f C%.6f" % ACTIVE_BC)

    before_entry_joints = joint_pose()
    before_entry_tcp = physical_tcp()
    mdi("G68.2 B%.6f C%.6f R0" % ACTIVE_BC)
    assert_world_mode("stage-one defined TWP")
    if not hal_bool("headheadtwp.valid") or hal_bool("headheadtwp.active"):
        fail("stage-one G68.2 did not leave TWP defined but inactive")
    mdi("G53.1")
    assert_active_state()
    assert_vector("stage-one G53.1 joints", joint_pose(), before_entry_joints, LINEAR_TOL)
    assert_vector("stage-one G53.1 physical TCP", physical_tcp(), before_entry_tcp, LINEAR_TOL)
    assert_stationary("stage-one pre-loss pose", 0.25)

    component_pid = require_single_state_component("stage-one pre-loss")
    require_registered_state_component("stage-one pre-loss")
    retained_joints = joint_pose()
    retained_tcp = physical_tcp()
    retained_origin = dot_vector("headheadkins.twp-captured-origin")
    retained_coordinate_offset = dot_vector("headheadkins.twp-coordinate-offset")

    os.kill(component_pid, signal.SIGKILL)
    wait_for(
        lambda: not state_component_pids(),
        "complete headheadtwp process loss",
        timeout=10.0,
    )
    # A normally exiting HAL userspace component removes its pins. SIGKILL can
    # instead leave the component registration and last signal values in HAL
    # until LinuxCNC tears the whole HAL instance down. Either representation
    # is acceptable here; the owning process is conclusively gone in both.
    pins_vanished = not component_pin_available()

    # No userspace writer remains. HAL retains the last signal values, so the
    # synchronized kinematics frame must stay type 1 and physically still until
    # the whole controller is restarted.
    assert_twp_mode("stage-one post-loss retained TWP")
    if hal_bool("headheadkins.tcpc-enable"):
        fail("stage-one post-loss unexpectedly enabled the TCPC signal")
    assert_vector(
        "stage-one post-loss captured origin",
        dot_vector("headheadkins.twp-captured-origin"),
        retained_origin,
        LINEAR_TOL,
    )
    assert_vector(
        "stage-one post-loss coordinate layer",
        dot_vector("headheadkins.twp-coordinate-offset"),
        retained_coordinate_offset,
        LINEAR_TOL,
    )
    assert_stationary(
        "stage-one post-loss pose",
        STATIONARY_TIME,
        expected_joints=retained_joints,
        expected_tcp=retained_tcp,
    )

    STAGE1_MARKER.write_text("%d\n" % component_pid, encoding="ascii")
    log(
        "stage one passed: killed headheadtwp PID %d in active type 1; "
        "%s and pose stayed stationary"
        % (
            component_pid,
            "pins vanished" if pins_vanished else "HAL retained stale pins without an owner",
        )
    )


def assert_fresh_state(label):
    assert_world_mode(label)
    for pin in (
        "origin_defined",
        "orientation_defined",
        "valid",
        "active",
        "motion_enabled",
        "synchronized_frame",
        "tcpc_enabled",
    ):
        if hal_bool("headheadtwp.%s" % pin):
            fail("%s retained headheadtwp.%s" % (label, pin))
    for pin in ("state_code", "transaction_fault", "transaction_ack"):
        if hal_int("headheadtwp.%s" % pin) != 0:
            fail("%s retained nonzero headheadtwp.%s" % (label, pin))
    for pin in ("transaction_command", "transaction_request"):
        if hal_int("headheadtwp.%s" % pin) != 0:
            fail("%s retained nonzero headheadtwp.%s" % (label, pin))

    if hal_bool("headheadkins.tcpc-enable"):
        fail("%s retained TCPC enable" % label)
    for vector_label, prefix, separator in (
        ("state TWP origin", "headheadtwp.twp_origin", "underscore"),
        ("state TCPC origin", "headheadtwp.tcpc_origin", "underscore"),
        ("kinematics TCPC origin", "headheadkins.tcpc-origin", "dot"),
        ("captured origin", "headheadkins.twp-captured-origin", "dot"),
        ("coordinate layer", "headheadkins.twp-coordinate-offset", "dot"),
    ):
        reader = underscore_vector if separator == "underscore" else dot_vector
        assert_vector(
            label + " " + vector_label,
            reader(prefix),
            (0.0, 0.0, 0.0),
            ZERO_TOL,
        )
    expected_plane_x, expected_plane_y, expected_plane_z = commissioned_zero_plane_axes()
    for axis, expected in zip("XYZ", (expected_plane_x, expected_plane_y, expected_plane_z)):
        assert_vector(
            label + " plane " + axis,
            underscore_vector("headheadtwp.plane_%s" % axis.lower()),
            expected,
            ZERO_TOL,
        )
    for pin in ("twp_b_angle", "twp_c_angle", "twp_normal_rotation"):
        assert_scalar(label + " " + pin, hal_float("headheadtwp.%s" % pin), 0.0, ZERO_TOL)
    assert_vector(
        label + " canonical tool offset",
        dot_vector("motion.tooloffset"),
        (0.0, 0.0, 0.0),
        ZERO_TOL,
    )


def run_recovery_stage():
    if not STAGE1_MARKER.is_file():
        fail("stage-two launch has no successful stage-one marker")
    try:
        killed_pid = int(STAGE1_MARKER.read_text(encoding="ascii").strip())
    except ValueError:
        fail("stage-one marker does not contain a process ID")

    restored_pid = require_single_state_component("stage-two startup")
    require_registered_state_component("stage-two startup")
    wait_for(lambda: component_pin_available(), "restored headheadtwp HAL pins")
    time.sleep(0.15)
    assert_fresh_state("stage-two initial startup")
    status.poll()
    assert_vector(
        "stage-two fresh G54 offset",
        tuple(status.g5x_offset[:3]),
        (0.0, 0.0, 0.0),
        ZERO_TOL,
    )

    enable_and_home()
    assert_fresh_state("stage-two enabled and homed")
    assert_stationary("stage-two recovered world pose", 0.25)
    log(
        "stage two passed: restored headheadtwp PID %d after killed PID %d "
        "in clean type 0 with TWP and TCPC state clear"
        % (restored_pid, killed_pid)
    )


def main():
    global controller, status, errors

    stage = os.environ.get("TWP_RECOVERY_STAGE", "").strip().lower()
    if stage not in ("loss", "recovery"):
        fail("TWP_RECOVERY_STAGE must be loss or recovery")

    controller = linuxcnc.command()
    status = linuxcnc.stat()
    errors = linuxcnc.error_channel()
    ui = hal.component("test-ui")
    ui.ready()
    wait_for_linuxcnc_startup(status)

    if stage == "loss":
        run_loss_stage()
    else:
        run_recovery_stage()


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
