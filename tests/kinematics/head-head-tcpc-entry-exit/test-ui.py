#!/usr/bin/env python3

import math
import sys
import time

import hal
import linuxcnc


TIMEOUT = 45.0
POS_TOL = 1e-3
ORIGIN_TOL = 1e-3
START_POSE = (1500.0, 850.0, -600.0, 0.0, 0.0)
ROTATED_POSE = (1500.0, 850.0, -600.0, 30.0, 90.0)
ENTRY_ORIGIN = (2.0, -22.0, -575.517)


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
    return (s.position[0], s.position[1], s.position[2], s.position[4], s.position[5])


def joint_pose():
    return tuple(hal.get_value("joint.%d.motor-pos-cmd" % joint) for joint in range(5))


def tcpc_origin():
    return (
        hal.get_value("headheadtwp.tcpc_origin_x"),
        hal.get_value("headheadtwp.tcpc_origin_y"),
        hal.get_value("headheadtwp.tcpc_origin_z"),
    )


def current_tcp_pose():
    return (
        hal.get_value("headheadtwp.current_tcp_x"),
        hal.get_value("headheadtwp.current_tcp_y"),
        hal.get_value("headheadtwp.current_tcp_z"),
        hal.get_value("headheadtwp.current_joint_b"),
        hal.get_value("headheadtwp.current_joint_c"),
    )


def assert_close_tuple(label, actual, expected, tol=POS_TOL):
    for a, ex in zip(actual, expected):
        if math.fabs(a - ex) > tol:
            fail("%s mismatch: actual=%s expected=%s" % (label, actual, expected))


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

mdi("G17 G21 G40 G49 G54 G64 P0.01 G80 G90 G92.1 G94")
mdi("G0 X%.6f Y%.6f Z%.6f B%.6f C%.6f" % START_POSE)
assert_close_tuple("start program pose", program_pose(), START_POSE)
start_joints = joint_pose()
log("start pose ok")

mdi("G43.4")
assert_state(False, False, False, True)
assert_close_tuple("G43.4 program pose continuity", program_pose(), START_POSE)
assert_close_tuple("G43.4 joint continuity", joint_pose(), start_joints)
assert_close_tuple("G43.4 TCPC origin", tcpc_origin(), ENTRY_ORIGIN, ORIGIN_TOL)
assert_close_tuple("G43.4 current TCP", current_tcp_pose(), START_POSE)
log("G43.4 entry continuity ok")

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
assert_close_tuple("rotated current TCP", current_tcp_pose(), ROTATED_POSE)
if math.fabs(joint_pose()[0] - start_joints[0]) < 1.0:
    fail("TCPC rotary move did not compensate X joint as expected")
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

error_text = mdi_expect_error("G68.2 B0 C0", "TCPC mode is not enabled")
assert_state(False, False, False, False)
log("G68.2 requires TCPC ok: %s" % error_text)

mdi("G43.4")
mdi("G68.2 B0 C0")
assert_state(True, True, True, True)
error_text = mdi_expect_error("G49.1", "run G69 first")
assert_state(True, True, True, True)
log("G49.1 while TWP active rejected ok: %s" % error_text)

mdi("G69")
assert_state(False, False, False, True)
mdi("G49.1")
assert_state(False, False, False, False)
log("post-G69 TCPC exit ok")

sys.exit(0)
