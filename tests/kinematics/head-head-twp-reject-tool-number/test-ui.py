#!/usr/bin/env python3

import math
import sys
import time

import hal
import linuxcnc


TIMEOUT = 45.0
POS_TOL = 1e-3


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


def check_errors(error_channel):
    while True:
        error = error_channel.poll()
        if error is None:
            return
        code, text = error
        if code in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
            fail("LinuxCNC error %s: %s" % error)
        log("LinuxCNC message %s: %s" % error)


def world_tool_tuple(status):
    status.poll()
    return (
        hal.get_value("headheadtwp.current_tool_x"),
        hal.get_value("headheadtwp.current_tool_y"),
        hal.get_value("headheadtwp.current_tool_z"),
        status.position[4],
        status.position[5],
    )


def assert_close_tuple(label, actual, expected, tol=POS_TOL):
    for a, e in zip(actual, expected):
        if math.fabs(a - e) > tol:
            fail("%s mismatch: actual=%s expected=%s" % (label, actual, expected))


def wait_for_pause(status, error_channel, label, expected_world):
    start_time = time.time()
    while time.time() - start_time < TIMEOUT:
        status.poll()
        check_errors(error_channel)
        if status.paused:
            assert_close_tuple(label + " world", world_tool_tuple(status), expected_world)
            return
        time.sleep(0.1)
    fail("timeout waiting for pause: %s actual=%s" % (label, world_tool_tuple(status)))


def wait_for_program_done(status, error_channel):
    start_time = time.time()
    while time.time() - start_time < TIMEOUT:
        status.poll()
        check_errors(error_channel)
        if status.interp_state == linuxcnc.INTERP_IDLE and status.inpos:
            return
        time.sleep(0.1)
    fail("timeout waiting for program completion")


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


def assert_twp_state(active, valid, state_code, motion_enabled, normal_rotation, tcpc_enabled):
    actual = (
        bool(hal.get_value("headheadtwp.active")),
        bool(hal.get_value("headheadtwp.valid")),
        int(hal.get_value("headheadtwp.state_code")),
        bool(hal.get_value("headheadtwp.motion_enabled")),
        float(hal.get_value("headheadtwp.twp_normal_rotation")),
        bool(hal.get_value("headheadtwp.tcpc_enabled")),
    )
    expected = (active, valid, state_code, motion_enabled, normal_rotation, tcpc_enabled)
    if (
        actual[0] != expected[0]
        or actual[1] != expected[1]
        or actual[2] != expected[2]
        or actual[3] != expected[3]
        or math.fabs(actual[4] - expected[4]) > POS_TOL
        or actual[5] != expected[5]
    ):
        fail("unexpected TWP state: actual=%s expected=%s" % (actual, expected))


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

assert_twp_state(False, False, 0, False, 0.0, True)

c.program_open("test.ngc")
time.sleep(0.5)
c.mode(linuxcnc.MODE_AUTO)
time.sleep(0.2)
c.auto(linuxcnc.AUTO_RUN, 0)

wait_for_pause(
    s,
    e,
    "starting world pose",
    (1500.0, 850.0, -600.0, 45.0, 90.0),
)
assert_twp_state(False, False, 0, False, 0.0, True)
log("pause 1 ok")

c.auto(linuxcnc.AUTO_RESUME)
wait_for_pause(
    s,
    e,
    "TCPC enabled world pose",
    (1500.0, 850.0, -600.0, 45.0, 90.0),
)
assert_twp_state(False, False, 0, False, 0.0, True)
log("pause 2 ok")

c.auto(linuxcnc.AUTO_RESUME)
error_text = wait_for_expected_error(
    s,
    e,
    "Cannot change current tool number while TWP is active",
)
assert_twp_state(True, True, 3, True, 0.0, True)
assert_close_tuple(
    "post-error world tool position",
    world_tool_tuple(s),
    (1500.0, 850.0, -600.0, 45.0, 90.0),
)
log("expected error ok: %s" % error_text)

sys.exit(0)
