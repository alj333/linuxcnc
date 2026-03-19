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


def axis_position_tuple(status):
    status.poll()
    return (
        status.position[0],
        status.position[1],
        status.position[2],
        status.position[4],
        status.position[5],
    )


def assert_close_tuple(label, actual, expected, tol=POS_TOL):
    for a, e in zip(actual, expected):
        if math.fabs(a - e) > tol:
            fail("%s mismatch: actual=%s expected=%s" % (label, actual, expected))


def wait_for_pause(status, error_channel, label, expected_pos):
    start_time = time.time()
    while time.time() - start_time < TIMEOUT:
        status.poll()
        check_errors(error_channel)
        if status.paused:
            actual = axis_position_tuple(status)
            assert_close_tuple(label, actual, expected_pos)
            return
        time.sleep(0.1)
    status.poll()
    fail(
        "timeout waiting for pause: %s actual=%s paused=%s interp=%s exec=%s"
        % (
            label,
            axis_position_tuple(status),
            status.paused,
            status.interp_state,
            status.exec_state,
        )
    )


def wait_for_program_done(status, error_channel):
    start_time = time.time()
    while time.time() - start_time < TIMEOUT:
        status.poll()
        check_errors(error_channel)
        if status.interp_state == linuxcnc.INTERP_IDLE and status.inpos:
            return
        time.sleep(0.1)
    fail("timeout waiting for program completion")


def wait_for_homed(status, expected_count):
    start_time = time.time()
    while time.time() - start_time < TIMEOUT:
        status.poll()
        if sum(status.homed[:5]) == expected_count:
            return
        time.sleep(0.1)
    fail("timeout waiting for homing; homed=%s" % (status.homed[:5],))


def assert_twp_state(active, valid, state_code):
    actual_active = bool(hal.get_value("headheadtwp.active"))
    actual_valid = bool(hal.get_value("headheadtwp.valid"))
    actual_state = int(hal.get_value("headheadtwp.state_code"))
    if (actual_active, actual_valid, actual_state) != (active, valid, state_code):
        fail(
            "unexpected TWP state: actual=%s expected=%s"
            % (
                (actual_active, actual_valid, actual_state),
                (active, valid, state_code),
            )
        )


def assert_normal_rotation(expected):
    actual = float(hal.get_value("headheadtwp.twp_normal_rotation"))
    if math.fabs(actual - expected) > POS_TOL:
        fail("unexpected twp_normal_rotation: actual=%s expected=%s" % (actual, expected))


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

assert_twp_state(False, False, 0)

c.program_open("test.ngc")
time.sleep(0.5)
c.mode(linuxcnc.MODE_AUTO)
time.sleep(0.2)
c.auto(linuxcnc.AUTO_RUN, 0)

wait_for_pause(s, e, "activation pause", (1500.0, 850.0, -600.0, 45.0, 90.0))
assert_twp_state(True, True, 3)
assert_normal_rotation(0.0)
log("pause 1 ok")

c.auto(linuxcnc.AUTO_RESUME)
wait_for_pause(s, e, "first TWP move", (1522.0, 741.447, -1193.513, 45.0, 90.0))
assert_twp_state(True, True, 3)
assert_normal_rotation(0.0)
log("pause 2 ok")

c.auto(linuxcnc.AUTO_RESUME)
wait_for_pause(s, e, "second TWP move", (1422.0, 741.447, -1193.513, 45.0, 90.0))
assert_twp_state(True, True, 3)
assert_normal_rotation(0.0)
log("pause 3 ok")

c.auto(linuxcnc.AUTO_RESUME)
wait_for_pause(s, e, "third TWP move", (1422.0, 776.802, -1158.158, 45.0, 90.0))
assert_twp_state(True, True, 3)
assert_normal_rotation(0.0)
log("pause 4 ok")

c.auto(linuxcnc.AUTO_RESUME)
wait_for_pause(s, e, "rotated activation pause", (1500.0, 850.0, -600.0, 45.0, 90.0))
assert_twp_state(True, True, 3)
assert_normal_rotation(90.0)
log("pause 5 ok")

c.auto(linuxcnc.AUTO_RESUME)
wait_for_pause(s, e, "first rotated TWP move", (1372.0, 635.381, -1087.447, 45.0, 90.0))
assert_twp_state(True, True, 3)
assert_normal_rotation(90.0)
log("pause 6 ok")

c.auto(linuxcnc.AUTO_RESUME)
wait_for_pause(s, e, "second rotated TWP move", (1372.0, 564.67, -1016.737, 45.0, 90.0))
assert_twp_state(True, True, 3)
assert_normal_rotation(90.0)
log("pause 7 ok")

c.auto(linuxcnc.AUTO_RESUME)
wait_for_pause(s, e, "third rotated TWP move", (1372.0, 600.026, -981.381, 45.0, 90.0))
assert_twp_state(True, True, 3)
assert_normal_rotation(90.0)
log("pause 8 ok")

c.auto(linuxcnc.AUTO_RESUME)
wait_for_program_done(s, e)
assert_twp_state(False, False, 0)
assert_normal_rotation(0.0)
assert_close_tuple(
    "final position",
    axis_position_tuple(s),
    (1372.0, 600.026, -981.381, 45.0, 90.0),
)
log("program complete")

sys.exit(0)
