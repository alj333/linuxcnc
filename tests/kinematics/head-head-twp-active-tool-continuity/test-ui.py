#!/usr/bin/env python3

import math
import sys
import time

import hal
import linuxcnc


TIMEOUT = 45.0
POS_TOL = 1e-3
JOINT_CONTINUITY_TOL = 0.005
START_POSE = (468.776624, 323.677576, -137.420448, 0.0, 0.0)


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


def mdi_burst(commands):
    drain_errors(e)
    c.mode(linuxcnc.MODE_MDI)
    c.wait_complete()
    for cmd in commands:
        c.mdi(cmd)
    c.wait_complete()
    wait_for_idle(s, e)


def program_pose():
    s.poll()
    return (s.position[0], s.position[1], s.position[2], s.position[4], s.position[5])


def joint_pose():
    return tuple(hal.get_value("joint.%d.motor-pos-cmd" % joint) for joint in range(5))


def hal_underscore_pose(prefix):
    return (
        hal.get_value("%s_x" % prefix),
        hal.get_value("%s_y" % prefix),
        hal.get_value("%s_z" % prefix),
    )


def hal_dot_pose(prefix):
    return (
        hal.get_value("%s.x" % prefix),
        hal.get_value("%s.y" % prefix),
        hal.get_value("%s.z" % prefix),
    )


def assert_close_tuple(label, actual, expected, tol=POS_TOL):
    for a, ex in zip(actual, expected):
        if math.fabs(a - ex) > tol:
            fail("%s mismatch: actual=%s expected=%s" % (label, actual, expected))


def assert_joint_continuity(label, before, after, tol=JOINT_CONTINUITY_TOL):
    deltas = tuple(after[i] - before[i] for i in range(len(before)))
    if any(math.fabs(delta) > tol for delta in deltas[:3]):
        fail("%s joint jump: before=%s after=%s delta=%s" % (label, before, after, deltas))
    log("%s joint continuity ok: delta=%s" % (label, deltas))


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

mdi("G17 G21 G40 G49 G54 G64 P0.01 G80 G90 G92.1 G94")
mdi("T1 M6")
mdi("G43 H1")
if math.fabs(hal.get_value("motion.tooloffset.z") - 128.606729) > 1e-6:
    fail("active tool offset did not apply: %s" % hal.get_value("motion.tooloffset.z"))
log("active tool length applied")

mdi("G0 X%.6f Y%.6f Z%.6f B%.6f C%.6f" % START_POSE)
start_program_pose = program_pose()
if math.fabs(start_program_pose[3]) > POS_TOL or math.fabs(start_program_pose[4]) > POS_TOL:
    fail("start rotary pose mismatch: actual=%s expected B0/C0" % (start_program_pose,))
start_joints = joint_pose()
log("start program_pose=%s joints=%s tool_offset=%s current_tcp=%s" % (
    start_program_pose,
    start_joints,
    hal_dot_pose("headheadkins.tool-offset"),
    hal_underscore_pose("headheadtwp.current_tcp"),
))

mdi("G69")
mdi("G49.1")
error_text = mdi_expect_error("G68.2 B0 C0", "TCPC mode is not enabled")
if bool(hal.get_value("headheadtwp.tcpc_enabled")) or bool(hal.get_value("headheadtwp.motion_enabled")):
    fail("failed pre-TCPC G68.2 left TCPC/TWP state active")
log("pre-TCPC G68.2 rejected cleanly: %s" % error_text)

mdi("G43.4")
after_tcpc_joints = joint_pose()
assert_joint_continuity("G43.4", start_joints, after_tcpc_joints)
if not bool(hal.get_value("headheadtwp.tcpc_enabled")):
    fail("G43.4 did not enable TCPC")
log("tcpc_origin=%s current_tcp=%s axis_cmd=(%.6f, %.6f, %.6f)" % (
    hal_underscore_pose("headheadtwp.tcpc_origin"),
    hal_underscore_pose("headheadtwp.current_tcp"),
    hal.get_value("axis.x.pos-cmd"),
    hal.get_value("axis.y.pos-cmd"),
    hal.get_value("axis.z.pos-cmd"),
))

mdi("G68.2 B0 C0")
after_twp_joints = joint_pose()
assert_joint_continuity("G68.2 B0 C0", after_tcpc_joints, after_twp_joints)
if not bool(hal.get_value("headheadtwp.motion_enabled")):
    fail("G68.2 did not enable TWP motion")
log("twp_origin=%s twp_motion_origin=(%.6f, %.6f, %.6f) program_pose=%s" % (
    hal_underscore_pose("headheadtwp.twp_origin"),
    hal.get_value("headheadkins.twp-motion-origin.x"),
    hal.get_value("headheadkins.twp-motion-origin.y"),
    hal.get_value("headheadkins.twp-motion-origin.z"),
    program_pose(),
))

mdi("G69")
mdi("G49.1")
if bool(hal.get_value("headheadtwp.tcpc_enabled")) or bool(hal.get_value("headheadtwp.motion_enabled")):
    fail("cleanup after waited TWP path left TCPC/TWP active")

mdi("G0 X%.6f Y%.6f Z%.6f B%.6f C%.6f" % START_POSE)
burst_start_joints = joint_pose()
mdi_burst(("G43.4", "G68.2 B0 C0"))
burst_after_joints = joint_pose()
assert_joint_continuity("burst G43.4/G68.2 B0 C0", burst_start_joints, burst_after_joints)
if not bool(hal.get_value("headheadtwp.motion_enabled")):
    fail("burst G43.4/G68.2 did not enable TWP motion")
log("burst path twp_motion_origin=(%.6f, %.6f, %.6f) program_pose=%s" % (
    hal.get_value("headheadkins.twp-motion-origin.x"),
    hal.get_value("headheadkins.twp-motion-origin.y"),
    hal.get_value("headheadkins.twp-motion-origin.z"),
    program_pose(),
))

mdi("G69")
mdi("G49.1")
log("TWP active tool continuity reproducer complete")

sys.exit(0)
