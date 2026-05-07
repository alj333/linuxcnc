import emccanon
import hal
import time
from interpreter import INTERP_ERROR, INTERP_EXECUTE_FINISH, INTERP_OK


def _hal(name):
    return hal.get_value(name)


def _axis_word(words, key):
    return words[key] if key in words else 0.0


def _plane_basis():
    return (
        (
            _hal("headheadtwp.plane_x_x"),
            _hal("headheadtwp.plane_x_y"),
            _hal("headheadtwp.plane_x_z"),
        ),
        (
            _hal("headheadtwp.plane_y_x"),
            _hal("headheadtwp.plane_y_y"),
            _hal("headheadtwp.plane_y_z"),
        ),
        (
            _hal("headheadtwp.plane_z_x"),
            _hal("headheadtwp.plane_z_y"),
            _hal("headheadtwp.plane_z_z"),
        ),
    )


def _twp_origin():
    return (
        _hal("headheadtwp.twp_origin_x"),
        _hal("headheadtwp.twp_origin_y"),
        _hal("headheadtwp.twp_origin_z"),
    )


def _current_tool_xyz():
    return (
        _hal("headheadtwp.current_tool_x"),
        _hal("headheadtwp.current_tool_y"),
        _hal("headheadtwp.current_tool_z"),
    )


def _tcpc_origin_applied_by_kins():
    try:
        state_origin = (
            _hal("headheadtwp.tcpc_origin_x"),
            _hal("headheadtwp.tcpc_origin_y"),
            _hal("headheadtwp.tcpc_origin_z"),
        )
        kins_origin = (
            _hal("headheadkins.tcpc-origin.x"),
            _hal("headheadkins.tcpc-origin.y"),
            _hal("headheadkins.tcpc-origin.z"),
        )
    except Exception:
        return False
    return all(abs(state - kins) <= 1e-6 for state, kins in zip(state_origin, kins_origin))


def _current_twp_world_xyz():
    if _hal("headheadtwp.tcpc_enabled") and _tcpc_origin_applied_by_kins():
        return _current_tcp_xyz()
    return _current_tool_xyz()


def _current_tcp_xyz():
    return (
        _hal("headheadtwp.current_tcp_x"),
        _hal("headheadtwp.current_tcp_y"),
        _hal("headheadtwp.current_tcp_z"),
    )


def _local_to_world(local_xyz):
    plane_x, plane_y, plane_z = _plane_basis()
    return _local_to_world_from_origin(_twp_origin(), local_xyz, plane_x, plane_y, plane_z)


def _local_to_world_from_origin(origin, local_xyz, plane_x=None, plane_y=None, plane_z=None):
    if plane_x is None or plane_y is None or plane_z is None:
        plane_x, plane_y, plane_z = _plane_basis()
    return (
        origin[0]
        + (local_xyz[0] * plane_x[0])
        + (local_xyz[1] * plane_y[0])
        + (local_xyz[2] * plane_z[0]),
        origin[1]
        + (local_xyz[0] * plane_x[1])
        + (local_xyz[1] * plane_y[1])
        + (local_xyz[2] * plane_z[1]),
        origin[2]
        + (local_xyz[0] * plane_x[2])
        + (local_xyz[1] * plane_y[2])
        + (local_xyz[2] * plane_z[2]),
    )


def _motion_origin_for_target(local_xyz, world_xyz, plane_x=None, plane_y=None, plane_z=None):
    mapped_xyz = _local_to_world_from_origin((0.0, 0.0, 0.0), local_xyz, plane_x, plane_y, plane_z)
    return (
        world_xyz[0] - mapped_xyz[0],
        world_xyz[1] - mapped_xyz[1],
        world_xyz[2] - mapped_xyz[2],
    )


def _line_number(self):
    return self.blocks[self.remap_level].line_number


def _set_error(self, message):
    self.set_errormsg(message)
    return INTERP_ERROR


def _pulse_bit(name):
    hal.set_p(name, "1")
    time.sleep(0.1)
    hal.set_p(name, "0")


def _require_valid_active(self, action_text):
    if not _hal("headheadtwp.valid"):
        return _set_error(self, "%s requested with no valid TWP definition" % action_text)
    if not _hal("headheadtwp.active"):
        return _set_error(self, "%s requested while TWP state is not active" % action_text)
    return None


def _require_tcpc(self, action_text):
    if not _hal("headheadtwp.tcpc_enabled"):
        return _set_error(self, "%s requested while TCPC mode is not enabled" % action_text)
    return None


def _current_bc():
    return (
        _hal("headheadtwp.current_joint_b"),
        _hal("headheadtwp.current_joint_c"),
    )


def enable_tcpc_mode(self, **words):
    del words
    yield INTERP_EXECUTE_FINISH
    _pulse_bit("headheadtwp.cmd_enable_tcpc")
    yield INTERP_EXECUTE_FINISH
    yield INTERP_OK


def disable_tcpc_mode(self, **words):
    del words
    yield INTERP_EXECUTE_FINISH
    _pulse_bit("headheadtwp.cmd_disable_tcpc")
    yield INTERP_EXECUTE_FINISH
    yield INTERP_OK


def twp_move(self, **words):
    """Prototype fixed-plane TWP linear move using stored headheadtwp state."""

    yield INTERP_EXECUTE_FINISH

    status = _require_valid_active(self, "TWP move")
    if status is not None:
        yield status
        return

    if not any(word in words for word in ("p", "q", "r")):
        yield _set_error(self, "G88.5 requires at least one of P, Q, or R")
        return

    local_xyz = (
        _axis_word(words, "p"),
        _axis_word(words, "q"),
        _axis_word(words, "r"),
    )
    world_xyz = _local_to_world(local_xyz)
    b_angle = _hal("headheadtwp.twp_b_angle")
    c_angle = _hal("headheadtwp.twp_c_angle")
    feed = words["l"] if "l" in words else self.feed_rate
    if not feed or feed <= 0.0:
        yield _set_error(self, "G88.5 requires a positive feed rate or active F value")
        return

    emccanon.SET_FEED_RATE(feed)
    emccanon.STRAIGHT_FEED(
        _line_number(self),
        world_xyz[0],
        world_xyz[1],
        world_xyz[2],
        0.0,
        b_angle,
        c_angle,
        0.0,
        0.0,
        0.0,
    )

    print(
        "TWP move UVW=(%.3f, %.3f, %.3f) -> XYZ=(%.3f, %.3f, %.3f)"
        % (local_xyz[0], local_xyz[1], local_xyz[2], world_xyz[0], world_xyz[1], world_xyz[2])
    )
    yield INTERP_OK


def enable_twp_mode(self, **words):
    yield INTERP_EXECUTE_FINISH

    status = _require_tcpc(self, "TWP mode enable")
    if status is not None:
        yield status
        return
    if _hal("headheadtwp.motion_enabled"):
        yield _set_error(self, "G68.2 redefine while TWP motion is active is not supported")
        return

    has_b = "b" in words
    has_c = "c" in words
    if has_b != has_c:
        yield _set_error(self, "G68.2 requires both B and C words, or neither")
        return

    if has_b:
        b_angle = words["b"]
        c_angle = words["c"]
    else:
        b_angle, c_angle = _current_bc()

    normal_rotation = words["r"] if "r" in words else 0.0

    axis_cmd_xyz = (
        _hal("axis.x.pos-cmd"),
        _hal("axis.y.pos-cmd"),
        _hal("axis.z.pos-cmd"),
    )
    world_xyz = _current_twp_world_xyz()
    hal.set_p("headheadtwp.requested_b_angle", "%.6f" % b_angle)
    hal.set_p("headheadtwp.requested_c_angle", "%.6f" % c_angle)
    hal.set_p("headheadtwp.requested_normal_rotation", "%.6f" % normal_rotation)
    _pulse_bit("headheadtwp.cmd_set_from_current_and_requested")
    yield INTERP_EXECUTE_FINISH
    _pulse_bit("headheadtwp.cmd_activate")
    yield INTERP_EXECUTE_FINISH

    plane_x, plane_y, plane_z = _plane_basis()
    # When the mode flips on, LinuxCNC is still holding the pre-TWP commanded
    # position in `axis.*.pos-cmd`. Choose the motion origin so that this
    # currently commanded local point maps back to the current world tool tip.
    motion_origin = _motion_origin_for_target(axis_cmd_xyz, world_xyz, plane_x, plane_y, plane_z)
    hal.set_p("headheadkins.twp-motion-origin.x", "%.6f" % motion_origin[0])
    hal.set_p("headheadkins.twp-motion-origin.y", "%.6f" % motion_origin[1])
    hal.set_p("headheadkins.twp-motion-origin.z", "%.6f" % motion_origin[2])

    _pulse_bit("headheadtwp.cmd_enable_twp_motion")
    yield INTERP_EXECUTE_FINISH
    self.execute("G92 X0 Y0 Z0")
    yield INTERP_EXECUTE_FINISH
    yield INTERP_OK


def disable_twp_mode(self, **words):
    del words
    yield INTERP_EXECUTE_FINISH

    if not _hal("headheadtwp.motion_enabled") and not _hal("headheadtwp.valid") and not _hal("headheadtwp.active"):
        yield INTERP_OK
        return

    world_xyz = _current_twp_world_xyz()

    if _hal("headheadtwp.motion_enabled"):
        self.execute("G92.1")
        yield INTERP_EXECUTE_FINISH

        plane_x, plane_y, plane_z = _plane_basis()
        # After `G92.1`, the intended post-cancel world coordinates are the same
        # literal XYZ words we need to issue while TWP mode is still active. Pick a
        # temporary motion origin that makes that command a no-op in world space,
        # then disable TWP motion without moving the tool tip.
        motion_origin = _motion_origin_for_target(world_xyz, world_xyz, plane_x, plane_y, plane_z)
        hal.set_p("headheadkins.twp-motion-origin.x", "%.6f" % motion_origin[0])
        hal.set_p("headheadkins.twp-motion-origin.y", "%.6f" % motion_origin[1])
        hal.set_p("headheadkins.twp-motion-origin.z", "%.6f" % motion_origin[2])
        self.execute("G0 X%.6f Y%.6f Z%.6f" % (world_xyz[0], world_xyz[1], world_xyz[2]))
        yield INTERP_EXECUTE_FINISH

        _pulse_bit("headheadtwp.cmd_disable_twp_motion")
        yield INTERP_EXECUTE_FINISH

    _pulse_bit("headheadtwp.cmd_cancel")
    yield INTERP_EXECUTE_FINISH
    _pulse_bit("headheadtwp.cmd_reset")
    yield INTERP_EXECUTE_FINISH
    yield INTERP_OK
