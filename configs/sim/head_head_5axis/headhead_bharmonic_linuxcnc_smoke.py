#!/usr/bin/env python3
"""Run a fixed-tip B-harmonic smoke test against a running head-head sim."""

from __future__ import annotations

import math
import sys
import time

import hal
import linuxcnc


TIMEOUT = 90.0
TCP_TOL = 1e-4
EXPECTED_BCROSS_SINB_SINC_Y = 0.325723886
TARGET = (1500.0, 850.0, -600.0)
POSES = [
    (0.0, 0.0),
    (30.0, 0.0),
    (-30.0, 0.0),
    (60.0, 0.0),
    (-60.0, 0.0),
    (90.0, 0.0),
    (-90.0, 0.0),
    (0.0, 0.0),
    (90.0, 90.0),
    (-90.0, 90.0),
    (0.0, 90.0),
    (90.0, 180.0),
    (-90.0, 180.0),
    (0.0, 180.0),
    (90.0, 270.0),
    (-90.0, 270.0),
    (0.0, 270.0),
    (0.0, 0.0),
]


def fail(message: str) -> None:
    print(message)
    sys.stdout.flush()
    raise SystemExit(1)


def log(message: str) -> None:
    print(message)
    sys.stdout.flush()


def check_errors(error_channel: linuxcnc.error_channel) -> None:
    while True:
        error = error_channel.poll()
        if error is None:
            return
        code, text = error
        if code in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
            fail(f"LinuxCNC error {code}: {text}")
        log(f"LinuxCNC message {code}: {text}")


def wait_for_startup(status: linuxcnc.stat, error_channel: linuxcnc.error_channel) -> None:
    start = time.time()
    while time.time() - start < TIMEOUT:
        status.poll()
        check_errors(error_channel)
        if (
            status.axis_mask != 0
            and status.exec_state == linuxcnc.EXEC_DONE
            and status.interp_state == linuxcnc.INTERP_IDLE
            and status.task_state in (linuxcnc.STATE_ESTOP, linuxcnc.STATE_ON)
        ):
            return
        time.sleep(0.1)
    fail("timeout waiting for LinuxCNC startup")


def wait_for_idle(status: linuxcnc.stat, error_channel: linuxcnc.error_channel) -> None:
    start = time.time()
    while time.time() - start < TIMEOUT:
        status.poll()
        check_errors(error_channel)
        if status.interp_state == linuxcnc.INTERP_IDLE and status.exec_state == linuxcnc.EXEC_DONE and status.inpos:
            return
        time.sleep(0.05)
    fail("timeout waiting for idle/in-position")


def machine_on_and_homed(command: linuxcnc.command, status: linuxcnc.stat, error_channel: linuxcnc.error_channel) -> None:
    status.poll()
    if status.task_state == linuxcnc.STATE_ESTOP:
        command.state(linuxcnc.STATE_ESTOP_RESET)
        command.wait_complete()
    command.state(linuxcnc.STATE_ON)
    command.wait_complete()
    command.mode(linuxcnc.MODE_MANUAL)
    command.wait_complete()
    command.teleop_enable(0)
    command.wait_complete()
    status.poll()
    if sum(status.homed[:5]) != 5:
        command.home(-1)
        command.wait_complete()
    start = time.time()
    while time.time() - start < TIMEOUT:
        status.poll()
        check_errors(error_channel)
        if sum(status.homed[:5]) == 5:
            break
        time.sleep(0.1)
    else:
        fail(f"timeout waiting for homing: {status.homed[:5]}")
    command.teleop_enable(1)
    command.wait_complete()


def mdi(command: linuxcnc.command, status: linuxcnc.stat, error_channel: linuxcnc.error_channel, text: str) -> None:
    command.mode(linuxcnc.MODE_MDI)
    command.wait_complete()
    command.mdi(text)
    command.wait_complete()
    wait_for_idle(status, error_channel)


def tcp_from_feedback() -> tuple[float, float, float]:
    return (
        hal.get_value("joint.0.pos-fb") + hal.get_value("headheadkins.tool-offset.x"),
        hal.get_value("joint.1.pos-fb") + hal.get_value("headheadkins.tool-offset.y"),
        hal.get_value("joint.2.pos-fb") + hal.get_value("headheadkins.tool-offset.z"),
    )


def check_tcp(label: str) -> float:
    actual = tcp_from_feedback()
    error = math.sqrt(sum((a - b) ** 2 for a, b in zip(actual, TARGET)))
    if error > TCP_TOL:
        fail(f"{label}: TCP error {error:.9f} actual={actual} target={TARGET}")
    return error


def run_pose_set(
    command: linuxcnc.command,
    status: linuxcnc.stat,
    error_channel: linuxcnc.error_channel,
    enable: bool,
) -> float:
    hal.set_p("headheadkins.sim-bharm-enable", "1" if enable else "0")
    wait_for_idle(status, error_channel)
    actual_enable = bool(hal.get_value("headheadkins.sim-bharm-enable"))
    if actual_enable != enable:
        fail(f"sim-bharm-enable did not set to {enable}")

    max_error = 0.0
    label = "enabled" if enable else "disabled"
    for b_deg, c_deg in POSES:
        mdi(
            command,
            status,
            error_channel,
            f"G0 X{TARGET[0]:.6f} Y{TARGET[1]:.6f} Z{TARGET[2]:.6f} B{b_deg:.6f} C{c_deg:.6f}",
        )
        max_error = max(max_error, check_tcp(f"{label} B{b_deg:+.0f} C{c_deg:.0f}"))
    return max_error


def main() -> int:
    command = linuxcnc.command()
    status = linuxcnc.stat()
    error_channel = linuxcnc.error_channel()
    component = hal.component("bharm-smoke")
    component.ready()

    wait_for_startup(status, error_channel)
    machine_on_and_homed(command, status, error_channel)
    mdi(command, status, error_channel, "G43.4")
    if not bool(hal.get_value("headheadkins.tcpc-enable")):
        fail("TCPC did not enable")
    if abs(hal.get_value("headheadkins.bcross.sinb-sinc.y") - EXPECTED_BCROSS_SINB_SINC_Y) > 1e-9:
        fail("refined B/C cross candidate coefficients did not load")
    if abs(hal.get_value("headheadkins.charm.cos.x")) > 1e-12:
        fail("C-harmonic pins did not default or load zero")
    if abs(hal.get_value("headheadkins.bcross.sinb-sin2c.x")) > 1e-12:
        fail("new B/C cross pins did not default or load zero")
    if abs(hal.get_value("headheadkins.bmid.base.x")) > 1e-12:
        fail("mid-B pins did not default or load zero")

    disabled_error = run_pose_set(command, status, error_channel, enable=False)
    enabled_error = run_pose_set(command, status, error_channel, enable=True)

    print("headheadkins B-harmonic LinuxCNC sim smoke test")
    print(f"disabled max fixed-tip TCP error: {disabled_error:.9f} mm")
    print(f"enabled max fixed-tip TCP error : {enabled_error:.9f} mm")
    print("sim-bharm-enable left TRUE in simulation for visual inspection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
