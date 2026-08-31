#!/usr/bin/env python3

"""Production-local TCPC/TWP state component for the head-head XYZBC machine."""

import math
import os
import time

import hal


STATE_UNDEFINED = 0
STATE_PARTIAL = 1
STATE_DEFINED = 2
STATE_ACTIVE = 3

TRANSACTION_NONE = 0
TRANSACTION_DEFINE_TWP = 1
TRANSACTION_ENTER_TWP = 2
TRANSACTION_EXIT_TWP = 3
TRANSACTION_CLEAR_TWP = 4

TRANSACTION_OK = 0
TRANSACTION_UNKNOWN_COMMAND = 1
TRANSACTION_TCPC_MUST_BE_OFF = 2
TRANSACTION_TWP_ALREADY_DEFINED = 3
TRANSACTION_TWP_NOT_DEFINED = 4
TRANSACTION_TWP_ALREADY_ACTIVE = 5
TRANSACTION_TWP_STILL_ACTIVE = 6
TRANSACTION_POSE_MISMATCH = 7
TRANSACTION_PARAMETER_NONFINITE = 8
TRANSACTION_MACHINE_NOT_READY = 9

TWP_POSE_MATCH_TOL_DEG = 0.001

POLL_SEC = 0.05


def default_tcpc_enabled():
    value = os.environ.get("HEADHEAD_TWP_DEFAULT_TCPC", "1").strip().lower()
    return value not in ("0", "false", "no", "off")


def tcpc_tool_length_guard_enabled():
    value = os.environ.get("HEADHEAD_TWP_TOOL_LENGTH_GUARD", "0").strip().lower()
    return value not in ("0", "false", "no", "off")


def rotate_y(angle_deg, vec):
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    x, y, z = vec
    return (c * x + s * z, y, -s * x + c * z)


def rotate_z(angle_deg, vec):
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    x, y, z = vec
    return (c * x - s * y, s * x + c * y, z)


def angle_delta_deg(current, reference):
    if not math.isfinite(current) or not math.isfinite(reference):
        return math.nan
    delta = math.remainder(current, 360.0) - math.remainder(reference, 360.0)
    return math.remainder(delta, 360.0)


def vec_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_scale(scale, vec):
    return (scale * vec[0], scale * vec[1], scale * vec[2])


def rotate_about_plane_normal(x_axis, y_axis, rotation_deg):
    angle = math.radians(rotation_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    u_axis = vec_add(vec_scale(c, x_axis), vec_scale(s, y_axis))
    v_axis = vec_add(vec_scale(-s, x_axis), vec_scale(c, y_axis))
    return u_axis, v_axis


class HeadHeadTwpState:
    def __init__(self):
        self.comp = hal.component("headheadtwp")
        self.prev_bits = {}
        self._new_pins()
        self.comp.ready()

        self.origin_defined = False
        self.orientation_defined = False
        self.twp_origin = (0.0, 0.0, 0.0)
        self.twp_bc = (0.0, 0.0)
        self.normal_rotation = 0.0
        self.motion_enabled = False
        self.synchronized_frame = False
        # Sim configs keep the historical TCPC-on default. Real-machine test
        # configs can start fail-safe with HEADHEAD_TWP_DEFAULT_TCPC=0.
        self.default_tcpc_enabled = default_tcpc_enabled()
        self.tcpc_enabled = self.default_tcpc_enabled
        self.tcpc_tool_length_guard = tcpc_tool_length_guard_enabled()
        self.tcpc_origin = (0.0, 0.0, 0.0)
        self.tcpc_entry_bc = (0.0, 0.0)
        self.pending_transaction_ack = None

    def _pin_bit_in(self, name):
        self.comp.newpin(name, hal.HAL_BIT, hal.HAL_IN)
        self.prev_bits[name] = False

    def _pin_float_in(self, name):
        self.comp.newpin(name, hal.HAL_FLOAT, hal.HAL_IN)

    def _pin_float_out(self, name):
        self.comp.newpin(name, hal.HAL_FLOAT, hal.HAL_OUT)

    def _pin_bit_out(self, name):
        self.comp.newpin(name, hal.HAL_BIT, hal.HAL_OUT)

    def _pin_s32_out(self, name):
        self.comp.newpin(name, hal.HAL_S32, hal.HAL_OUT)

    def _pin_s32_in(self, name):
        self.comp.newpin(name, hal.HAL_S32, hal.HAL_IN)

    def _pin_u32_in(self, name):
        self.comp.newpin(name, hal.HAL_U32, hal.HAL_IN)

    def _pin_u32_out(self, name):
        self.comp.newpin(name, hal.HAL_U32, hal.HAL_OUT)

    def _new_pins(self):
        for axis in ("x", "y", "z", "b", "c"):
            self._pin_float_in(f"current_joint_{axis}")

        for axis in ("x", "y", "z"):
            self._pin_float_in(f"nominal_c_to_b_{axis}")
            self._pin_float_in(f"nominal_b_to_tool_{axis}")
            self._pin_float_in(f"cal_c_to_b_{axis}")
            self._pin_float_in(f"cal_b_to_tool_{axis}")

        self._pin_float_in("b_zero_offset")
        self._pin_float_in("c_zero_offset")
        self._pin_bit_in("use_external_tool_offset")
        for axis in ("x", "y", "z"):
            self._pin_float_in(f"external_tool_offset_{axis}")
        self._pin_float_in("requested_b_angle")
        self._pin_float_in("requested_c_angle")
        self._pin_float_in("requested_normal_rotation")
        self._pin_s32_in("transaction_command")
        self._pin_u32_in("transaction_request")
        self._pin_bit_in("machine_is_enabled")
        for joint in range(5):
            self._pin_bit_in(f"joint_{joint}_homed")

        for name in (
            "cmd_set_origin_from_current",
            "cmd_set_orientation_from_current",
            "cmd_set_from_current",
            "cmd_set_from_current_and_requested",
            "cmd_set_normal_rotation",
            "cmd_activate",
            "cmd_enable_twp_motion",
            "cmd_disable_twp_motion",
            "cmd_enable_tcpc",
            "cmd_disable_tcpc",
            "cmd_cancel",
            "cmd_reset",
        ):
            self._pin_bit_in(name)

        for axis in ("x", "y", "z"):
            self._pin_float_out(f"current_tool_{axis}")
            self._pin_float_out(f"current_tcp_{axis}")
            self._pin_float_out(f"twp_origin_{axis}")
            self._pin_float_out(f"tcpc_origin_{axis}")

        self._pin_float_out("twp_b_angle")
        self._pin_float_out("twp_c_angle")
        self._pin_float_out("twp_normal_rotation")
        self._pin_float_out("tcpc_entry_b_angle")
        self._pin_float_out("tcpc_entry_c_angle")

        for vec_name in ("plane_x", "plane_y", "plane_z"):
            for axis in ("x", "y", "z"):
                self._pin_float_out(f"{vec_name}_{axis}")

        self._pin_bit_out("origin_defined")
        self._pin_bit_out("orientation_defined")
        self._pin_bit_out("valid")
        self._pin_bit_out("active")
        self._pin_bit_out("motion_enabled")
        self._pin_bit_out("synchronized_frame")
        self._pin_bit_out("tcpc_enabled")
        self._pin_bit_out("tcpc_tool_length_guard")
        self._pin_float_out("kinematics_type")
        self._pin_s32_out("state_code")
        self._pin_s32_out("transaction_fault")
        self._pin_u32_out("transaction_ack")

    def _get(self, name):
        return float(self.comp[name])

    def _combined_c_to_b(self):
        return (
            self._get("nominal_c_to_b_x") + self._get("cal_c_to_b_x"),
            self._get("nominal_c_to_b_y") + self._get("cal_c_to_b_y"),
            self._get("nominal_c_to_b_z") + self._get("cal_c_to_b_z"),
        )

    def _combined_b_to_tool(self):
        return (
            self._get("nominal_b_to_tool_x") + self._get("cal_b_to_tool_x"),
            self._get("nominal_b_to_tool_y") + self._get("cal_b_to_tool_y"),
            self._get("nominal_b_to_tool_z") + self._get("cal_b_to_tool_z"),
        )

    def _effective_angles(self, b_cmd, c_cmd):
        return (
            b_cmd + self._get("b_zero_offset"),
            c_cmd + self._get("c_zero_offset"),
        )

    def _tool_offset_world(self, b_cmd, c_cmd):
        if bool(self.comp["use_external_tool_offset"]):
            external_offset = (
                self._get("external_tool_offset_x"),
                self._get("external_tool_offset_y"),
                self._get("external_tool_offset_z"),
            )
            if any(abs(value) > 1e-9 for value in external_offset):
                return external_offset

        b_eff, c_eff = self._effective_angles(b_cmd, c_cmd)
        c_to_b = self._combined_c_to_b()
        b_to_tool = self._combined_b_to_tool()
        b_rotated = rotate_y(b_eff, b_to_tool)
        c_frame = vec_add(c_to_b, b_rotated)
        return rotate_z(c_eff, c_frame)

    def _current_joint_pose(self):
        return (
            self._get("current_joint_x"),
            self._get("current_joint_y"),
            self._get("current_joint_z"),
            self._get("current_joint_b"),
            self._get("current_joint_c"),
        )

    def _current_tool_pose(self):
        x, y, z, b, c = self._current_joint_pose()
        tool_offset = self._tool_offset_world(b, c)
        return vec_add((x, y, z), tool_offset), (b, c)

    def _current_tcp_pose(self):
        current_tool_xyz, current_bc = self._current_tool_pose()
        if self.tcpc_enabled or self.motion_enabled:
            return vec_sub(current_tool_xyz, self.tcpc_origin), current_bc
        x, y, z, _, _ = self._current_joint_pose()
        return (x, y, z), current_bc

    def _plane_axes(self, b_deg, c_deg, normal_rotation):
        b_eff, c_eff = self._effective_angles(b_deg, c_deg)
        x_axis = rotate_z(c_eff, rotate_y(b_eff, (1.0, 0.0, 0.0)))
        y_axis = rotate_z(c_eff, rotate_y(b_eff, (0.0, 1.0, 0.0)))
        z_axis = rotate_z(c_eff, rotate_y(b_eff, (0.0, 0.0, 1.0)))
        x_axis, y_axis = rotate_about_plane_normal(x_axis, y_axis, normal_rotation)
        return x_axis, y_axis, z_axis

    def _rising_edge(self, pin_name):
        current = bool(self.comp[pin_name])
        previous = self.prev_bits[pin_name]
        self.prev_bits[pin_name] = current
        return current and not previous

    def _falling_edge(self, pin_name):
        current = bool(self.comp[pin_name])
        previous = self.prev_bits[pin_name]
        self.prev_bits[pin_name] = current
        return previous and not current

    def _changed_bit(self, pin_name):
        current = bool(self.comp[pin_name])
        previous = self.prev_bits[pin_name]
        self.prev_bits[pin_name] = current
        return current != previous

    def _state_code(self):
        valid = self.origin_defined and self.orientation_defined
        if self.comp["active"]:
            return STATE_ACTIVE
        if valid:
            return STATE_DEFINED
        if self.origin_defined or self.orientation_defined:
            return STATE_PARTIAL
        return STATE_UNDEFINED

    def _clear_state(self):
        self.origin_defined = False
        self.orientation_defined = False
        self.twp_origin = (0.0, 0.0, 0.0)
        self.twp_bc = (0.0, 0.0)
        self.normal_rotation = 0.0
        self.motion_enabled = False
        self.synchronized_frame = False
        self.comp["active"] = False

    def _clear_for_machine_reset(self):
        self._clear_state()
        self.tcpc_origin = (0.0, 0.0, 0.0)
        self.tcpc_entry_bc = (0.0, 0.0)
        # Reset to the configured startup mode after estop/off.
        self.tcpc_enabled = self.default_tcpc_enabled

    def _handle_transaction(self, current_tcp_xyz, current_bc):
        request = int(self.comp["transaction_request"])
        if request == int(self.comp["transaction_ack"]):
            return

        command = int(self.comp["transaction_command"])
        fault = TRANSACTION_OK
        if command == TRANSACTION_DEFINE_TWP:
            requested_b = self._get("requested_b_angle")
            requested_c = self._get("requested_c_angle")
            requested_r = self._get("requested_normal_rotation")
            machine_ready = bool(self.comp["machine_is_enabled"]) and all(
                bool(self.comp[f"joint_{joint}_homed"]) for joint in range(5)
            )
            if not machine_ready:
                fault = TRANSACTION_MACHINE_NOT_READY
            elif self.tcpc_enabled:
                fault = TRANSACTION_TCPC_MUST_BE_OFF
            elif self.origin_defined or self.orientation_defined:
                fault = TRANSACTION_TWP_ALREADY_DEFINED
            elif not all(
                math.isfinite(value)
                for value in (*current_tcp_xyz, *current_bc, requested_b, requested_c, requested_r)
            ):
                fault = TRANSACTION_PARAMETER_NONFINITE
            elif (
                abs(requested_b - current_bc[0]) > TWP_POSE_MATCH_TOL_DEG
                or abs(angle_delta_deg(requested_c, current_bc[1]))
                > TWP_POSE_MATCH_TOL_DEG
            ):
                fault = TRANSACTION_POSE_MISMATCH
            else:
                self.twp_origin = current_tcp_xyz
                self.twp_bc = current_bc
                self.normal_rotation = requested_r
                self.origin_defined = True
                self.orientation_defined = True
                self.synchronized_frame = True
                self.comp["active"] = False
                self.motion_enabled = False
        elif command == TRANSACTION_ENTER_TWP:
            machine_ready = bool(self.comp["machine_is_enabled"]) and all(
                bool(self.comp[f"joint_{joint}_homed"]) for joint in range(5)
            )
            if not machine_ready:
                fault = TRANSACTION_MACHINE_NOT_READY
            elif self.tcpc_enabled:
                fault = TRANSACTION_TCPC_MUST_BE_OFF
            elif not self.origin_defined or not self.orientation_defined:
                fault = TRANSACTION_TWP_NOT_DEFINED
            elif self.motion_enabled or bool(self.comp["active"]):
                fault = TRANSACTION_TWP_ALREADY_ACTIVE
            elif not all(math.isfinite(value) for value in (*current_tcp_xyz, *current_bc)):
                fault = TRANSACTION_PARAMETER_NONFINITE
            elif (
                abs(self.twp_bc[0] - current_bc[0]) > TWP_POSE_MATCH_TOL_DEG
                or abs(angle_delta_deg(self.twp_bc[1], current_bc[1]))
                > TWP_POSE_MATCH_TOL_DEG
            ):
                fault = TRANSACTION_POSE_MISMATCH
            else:
                # TWP is a separate public mode from G43.4 TCPC. It captures
                # the same calibrated tool-offset reference for the internal
                # kinematics calculation without setting tcpc_enabled.
                self.tcpc_origin = self._tool_offset_world(current_bc[0], current_bc[1])
                self.comp["active"] = True
                self.motion_enabled = True
        elif command == TRANSACTION_EXIT_TWP:
            # Keep the captured frame stable until motion has switched back to
            # world kinematics. A separate CLEAR transaction removes it after
            # the remap observes headheadkins.kinstype-is-world.
            self.comp["active"] = False
            self.motion_enabled = False
        elif command == TRANSACTION_CLEAR_TWP:
            if self.motion_enabled:
                fault = TRANSACTION_TWP_STILL_ACTIVE
            else:
                self._clear_state()
                if not self.tcpc_enabled:
                    self.tcpc_origin = (0.0, 0.0, 0.0)
        else:
            fault = TRANSACTION_UNKNOWN_COMMAND

        # Publish the acknowledgement only after _update_outputs() has made
        # every state change visible to the remap in the same polling cycle.
        self.pending_transaction_ack = (request, fault)

    def _update_state_machine(self):
        if self._falling_edge("machine_is_enabled"):
            self._clear_for_machine_reset()

        homed_changed = False
        for joint in range(5):
            if self._changed_bit(f"joint_{joint}_homed"):
                homed_changed = True
        if homed_changed:
            # Any re-home/unhome event invalidates the stored tilted frame.
            self._clear_state()

        if self._rising_edge("cmd_reset"):
            self._clear_state()

        if self._rising_edge("cmd_set_normal_rotation"):
            self.normal_rotation = self._get("requested_normal_rotation")

        current_tool_xyz, current_bc = self._current_tool_pose()
        current_tcp_xyz, _ = self._current_tcp_pose()

        if self._rising_edge("cmd_enable_tcpc"):
            if not self.tcpc_enabled and not (self.origin_defined or self.orientation_defined):
                self.tcpc_origin = self._tool_offset_world(current_bc[0], current_bc[1])
                self.tcpc_entry_bc = current_bc
                self.tcpc_enabled = True

        if self._rising_edge("cmd_disable_tcpc"):
            self.tcpc_enabled = False
            self.motion_enabled = False
            self.tcpc_origin = (0.0, 0.0, 0.0)
            self.tcpc_entry_bc = (0.0, 0.0)
            current_tcp_xyz, _ = self._current_tcp_pose()

        if self._rising_edge("cmd_set_origin_from_current"):
            self.twp_origin = current_tcp_xyz
            self.origin_defined = True

        if self._rising_edge("cmd_set_orientation_from_current"):
            self.twp_bc = current_bc
            self.orientation_defined = True

        if self._rising_edge("cmd_set_from_current"):
            self.twp_origin = current_tcp_xyz
            self.twp_bc = current_bc
            self.origin_defined = True
            self.orientation_defined = True

        if self._rising_edge("cmd_set_from_current_and_requested"):
            self.twp_origin = current_tcp_xyz
            self.twp_bc = (
                self._get("requested_b_angle"),
                self._get("requested_c_angle"),
            )
            self.normal_rotation = self._get("requested_normal_rotation")
            self.origin_defined = True
            self.orientation_defined = True

        if self._rising_edge("cmd_cancel"):
            self.comp["active"] = False
            self.motion_enabled = False

        if self._rising_edge("cmd_activate"):
            if self.origin_defined and self.orientation_defined:
                self.comp["active"] = True

        if self._rising_edge("cmd_enable_twp_motion"):
            if (
                self.tcpc_enabled
                and self.origin_defined
                and self.orientation_defined
                and self.comp["active"]
            ):
                self.motion_enabled = True

        if self._rising_edge("cmd_disable_twp_motion"):
            self.motion_enabled = False

        self._handle_transaction(current_tcp_xyz, current_bc)

    def _update_outputs(self):
        current_tool_xyz, _ = self._current_tool_pose()
        current_tcp_xyz, _ = self._current_tcp_pose()
        plane_x, plane_y, plane_z = self._plane_axes(
            self.twp_bc[0], self.twp_bc[1], self.normal_rotation
        )

        self.comp["current_tool_x"] = current_tool_xyz[0]
        self.comp["current_tool_y"] = current_tool_xyz[1]
        self.comp["current_tool_z"] = current_tool_xyz[2]
        self.comp["current_tcp_x"] = current_tcp_xyz[0]
        self.comp["current_tcp_y"] = current_tcp_xyz[1]
        self.comp["current_tcp_z"] = current_tcp_xyz[2]

        self.comp["twp_origin_x"] = self.twp_origin[0]
        self.comp["twp_origin_y"] = self.twp_origin[1]
        self.comp["twp_origin_z"] = self.twp_origin[2]
        self.comp["tcpc_origin_x"] = self.tcpc_origin[0]
        self.comp["tcpc_origin_y"] = self.tcpc_origin[1]
        self.comp["tcpc_origin_z"] = self.tcpc_origin[2]
        self.comp["twp_b_angle"] = self.twp_bc[0]
        self.comp["twp_c_angle"] = self.twp_bc[1]
        self.comp["twp_normal_rotation"] = self.normal_rotation
        self.comp["tcpc_entry_b_angle"] = self.tcpc_entry_bc[0]
        self.comp["tcpc_entry_c_angle"] = self.tcpc_entry_bc[1]

        self.comp["plane_x_x"] = plane_x[0]
        self.comp["plane_x_y"] = plane_x[1]
        self.comp["plane_x_z"] = plane_x[2]
        self.comp["plane_y_x"] = plane_y[0]
        self.comp["plane_y_y"] = plane_y[1]
        self.comp["plane_y_z"] = plane_y[2]
        self.comp["plane_z_x"] = plane_z[0]
        self.comp["plane_z_y"] = plane_z[1]
        self.comp["plane_z_z"] = plane_z[2]

        self.comp["origin_defined"] = self.origin_defined
        self.comp["orientation_defined"] = self.orientation_defined
        self.comp["valid"] = self.origin_defined and self.orientation_defined
        self.comp["motion_enabled"] = self.motion_enabled
        self.comp["synchronized_frame"] = self.synchronized_frame
        self.comp["tcpc_enabled"] = self.tcpc_enabled
        self.comp["tcpc_tool_length_guard"] = self.tcpc_tool_length_guard
        self.comp["kinematics_type"] = 1.0 if self.motion_enabled else 0.0
        self.comp["state_code"] = self._state_code()
        if self.pending_transaction_ack is not None:
            request, fault = self.pending_transaction_ack
            self.comp["transaction_fault"] = fault
            self.comp["transaction_ack"] = request
            self.pending_transaction_ack = None

    def run(self):
        try:
            while True:
                self._update_state_machine()
                self._update_outputs()
                time.sleep(POLL_SEC)
        except KeyboardInterrupt:
            pass


def main():
    HeadHeadTwpState().run()


if __name__ == "__main__":
    main()
