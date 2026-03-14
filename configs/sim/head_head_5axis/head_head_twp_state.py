#!/usr/bin/env python3

"""Prototype TWP state component for the head-head XYZBC simulation."""

import math
import time

import hal


STATE_UNDEFINED = 0
STATE_PARTIAL = 1
STATE_DEFINED = 2
STATE_ACTIVE = 3

POLL_SEC = 0.05


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


def vec_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


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
        self._pin_float_in("requested_normal_rotation")

        for name in (
            "cmd_set_origin_from_current",
            "cmd_set_orientation_from_current",
            "cmd_set_from_current",
            "cmd_set_normal_rotation",
            "cmd_activate",
            "cmd_cancel",
            "cmd_reset",
        ):
            self._pin_bit_in(name)

        for axis in ("x", "y", "z"):
            self._pin_float_out(f"current_tool_{axis}")
            self._pin_float_out(f"twp_origin_{axis}")

        self._pin_float_out("twp_b_angle")
        self._pin_float_out("twp_c_angle")
        self._pin_float_out("twp_normal_rotation")

        for vec_name in ("plane_x", "plane_y", "plane_z"):
            for axis in ("x", "y", "z"):
                self._pin_float_out(f"{vec_name}_{axis}")

        self._pin_bit_out("origin_defined")
        self._pin_bit_out("orientation_defined")
        self._pin_bit_out("valid")
        self._pin_bit_out("active")
        self._pin_s32_out("state_code")

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
        self.comp["active"] = False

    def _update_state_machine(self):
        if self._rising_edge("cmd_reset"):
            self._clear_state()

        if self._rising_edge("cmd_set_normal_rotation"):
            self.normal_rotation = self._get("requested_normal_rotation")

        current_tool_xyz, current_bc = self._current_tool_pose()

        if self._rising_edge("cmd_set_origin_from_current"):
            self.twp_origin = current_tool_xyz
            self.origin_defined = True

        if self._rising_edge("cmd_set_orientation_from_current"):
            self.twp_bc = current_bc
            self.orientation_defined = True

        if self._rising_edge("cmd_set_from_current"):
            self.twp_origin = current_tool_xyz
            self.twp_bc = current_bc
            self.origin_defined = True
            self.orientation_defined = True

        if self._rising_edge("cmd_cancel"):
            self.comp["active"] = False

        if self._rising_edge("cmd_activate"):
            if self.origin_defined and self.orientation_defined:
                self.comp["active"] = True

    def _update_outputs(self):
        current_tool_xyz, _ = self._current_tool_pose()
        plane_x, plane_y, plane_z = self._plane_axes(
            self.twp_bc[0], self.twp_bc[1], self.normal_rotation
        )

        self.comp["current_tool_x"] = current_tool_xyz[0]
        self.comp["current_tool_y"] = current_tool_xyz[1]
        self.comp["current_tool_z"] = current_tool_xyz[2]

        self.comp["twp_origin_x"] = self.twp_origin[0]
        self.comp["twp_origin_y"] = self.twp_origin[1]
        self.comp["twp_origin_z"] = self.twp_origin[2]
        self.comp["twp_b_angle"] = self.twp_bc[0]
        self.comp["twp_c_angle"] = self.twp_bc[1]
        self.comp["twp_normal_rotation"] = self.normal_rotation

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
        self.comp["state_code"] = self._state_code()

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
