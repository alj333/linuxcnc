"""Fail-closed TCPC/TWP remaps for the calibrated head-head machine."""

import math
import os
import time

import hal
import linuxcnc
from interpreter import INTERP_ERROR, INTERP_EXECUTE_FINISH, INTERP_OK


ROTARY_ENTRY_TOL_DEG = 0.01
TCPC_ENTRY_ZERO_TOL_DEG = 0.005
TWP_POSE_MATCH_TOL_DEG = 0.001
TWP_TRANSITION_LINEAR_TOL_MM = 0.002
TWP_TRANSITION_ROTARY_TOL_DEG = 0.001
TWP_TRANSACTION_TIMEOUT_SEC = 2.0
TWP_TRANSACTION_ENTER = 1
TWP_TRANSACTION_EXIT = 2
TWP_TRANSACTION_CLEAR = 3
TOOL_XY_TOL_MM = 1e-6
TOOL_OTHER_AXIS_TOL = 1e-9
LENGTH_REFERENCE_MM = 229.407000
LENGTH_SPAN_MM = 100.800271
LENGTH_HARD_MIN_MM = 100.0
LENGTH_HARD_MAX_MM = 430.0
LENGTH_MAX_TOLERANCE_MM = 0.002
LENGTH_MAX_DIFF_NORM_MM = 0.400
LENGTH_MAX_TOTAL_NORM_MM = 1.350
LENGTH_CONFIG_TOL = 1e-9


def _ini_flag(section, key):
    filename = os.environ.get("INI_FILE_NAME")
    if not filename:
        return False
    try:
        value = linuxcnc.ini(filename).find(section, key)
    except Exception:
        return False
    return str(value or "").strip().lower() in ("1", "true", "yes", "on")


LENGTH_MODEL_REQUIRED = _ini_flag("TCPC", "LENGTH_MODEL_REQUIRED")
TWP_ENABLED = _ini_flag("TWP", "ENABLE")


def _set_error(self, message):
    self.set_errormsg(message)
    return INTERP_ERROR


def _hal(name):
    return hal.get_value(name)


def _pulse_bit(name):
    hal.set_p(name, "1")
    time.sleep(0.1)
    hal.set_p(name, "0")


def _wait_until(predicate, timeout=TWP_TRANSACTION_TIMEOUT_SEC):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return bool(predicate())


def _twp_transaction(command):
    request = int(_hal("headheadtwp.transaction_request"))
    ack = int(_hal("headheadtwp.transaction_ack"))
    sequence = (max(request, ack) + 1) & 0xFFFFFFFF
    if sequence == 0:
        sequence = 1

    hal.set_p("headheadtwp.transaction_command", str(command))
    hal.set_p("headheadtwp.transaction_request", str(sequence))
    if not _wait_until(
        lambda: int(_hal("headheadtwp.transaction_ack")) == sequence
    ):
        return "TWP state transaction timed out"

    fault = int(_hal("headheadtwp.transaction_fault"))
    if fault != 0:
        return "TWP state transaction was rejected (fault %d)" % fault
    return None


def _joint_command_pose():
    return tuple(float(_hal("joint.%d.motor-pos-cmd" % joint)) for joint in range(5))


def _transition_continuity_error(before, after):
    linear_delta = max(abs(after[index] - before[index]) for index in range(3))
    rotary_delta = max(abs(after[index] - before[index]) for index in range(3, 5))
    if (
        linear_delta > TWP_TRANSITION_LINEAR_TOL_MM
        or rotary_delta > TWP_TRANSITION_ROTARY_TOL_DEG
    ):
        return (
            "kinematics handoff changed joint commands "
            "(linear %.6f mm, rotary %.6f deg)" % (linear_delta, rotary_delta)
        )
    return None


def _status_snapshot():
    status = linuxcnc.stat()
    status.poll()
    return status


def _twp_coordinate_state(self):
    if _g92_g52_offsets_active(self):
        return None, "clear G52/G92 offsets before entering TWP"
    if bool(self.cutter_comp_side):
        return None, "cancel cutter compensation with G40 before entering TWP"

    status = _status_snapshot()
    g5x = tuple(float(value) for value in status.g5x_offset)
    g92 = tuple(float(value) for value in status.g92_offset)
    values = g5x + g92 + (float(status.rotation_xy),)
    if not all(math.isfinite(value) for value in values):
        return None, "active coordinate offsets are nonfinite"
    if any(abs(value) > 1e-6 for value in g92):
        return None, "clear G52/G92 offsets before entering TWP"
    if abs(float(status.rotation_xy)) > 1e-6:
        return None, "G5X XY rotation is not supported in TWP"
    if any(abs(g5x[index]) > 1e-6 for index in range(3, 9)):
        return None, "rotary/AUX G5X offsets are not supported in TWP"
    return g5x[:3], None


def _length_model_configured():
    try:
        return bool(_hal("headheadkins.length-model.configured"))
    except Exception:
        return None


def _length_model_entry_error(self):
    configured = _length_model_configured()
    if LENGTH_MODEL_REQUIRED and configured is not True:
        return "required kinematics length model is not configured"
    if configured is not True:
        return None

    try:
        if int(self.active_g_codes[9]) != 430:
            return "activate a positive tool length offset before G43.4"
    except Exception:
        return "cannot verify active G43 tool length compensation"

    try:
        active_x = float(_hal("motion.tooloffset.x"))
        active_y = float(_hal("motion.tooloffset.y"))
        active_z = float(_hal("motion.tooloffset.z"))
        other_offsets = {
            axis: float(_hal("motion.tooloffset.%s" % axis))
            for axis in ("a", "b", "c", "u", "v", "w")
        }
        minimum = float(_hal("headheadkins.length-model.minimum"))
        maximum = float(_hal("headheadkins.length-model.maximum"))
        tolerance = float(_hal("headheadkins.length-model.tolerance"))
        reference = float(_hal("headheadkins.length-model.reference"))
        span = float(_hal("headheadkins.length-model.span"))
        max_diff_norm = float(_hal("headheadkins.length-model.max-diff-norm"))
        max_total_norm = float(_hal("headheadkins.length-model.max-total-norm"))
        model_id = int(_hal("headheadkins.length-model.id"))
        expected_id = int(_hal("headheadkins.length-model.expected-id"))
        evaluated_length = float(_hal("headheadkins.tool-offset-eval.length"))
    except Exception:
        return "cannot read the active tool offset or length-model domain"

    values = (
        active_x,
        active_y,
        active_z,
        minimum,
        maximum,
        tolerance,
        reference,
        span,
        max_diff_norm,
        max_total_norm,
        evaluated_length,
        *other_offsets.values(),
    )
    if not all(math.isfinite(value) for value in values):
        return "active tool offset or length-model domain is nonfinite"
    if (
        abs(reference - LENGTH_REFERENCE_MM) > LENGTH_CONFIG_TOL
        or abs(span - LENGTH_SPAN_MM) > LENGTH_CONFIG_TOL
        or minimum < LENGTH_HARD_MIN_MM
        or maximum > LENGTH_HARD_MAX_MM
        or maximum < minimum
        or tolerance < 0.0
        or tolerance > LENGTH_MAX_TOLERANCE_MM
        or max_diff_norm <= 0.0
        or max_diff_norm > LENGTH_MAX_DIFF_NORM_MM
        or max_total_norm <= 0.0
        or max_total_norm > LENGTH_MAX_TOTAL_NORM_MM
    ):
        return "length-model domain configuration is invalid"
    if expected_id <= 0 or model_id != expected_id:
        return "length-model coefficient-set ID does not match the kinematics"
    if abs(active_x) > TOOL_XY_TOL_MM or abs(active_y) > TOOL_XY_TOL_MM:
        return (
            "active tool X/Y offsets are unsupported by the calibrated length model "
            "(X%.6f Y%.6f)" % (active_x, active_y)
        )
    unsupported = {
        axis: value
        for axis, value in other_offsets.items()
        if abs(value) > TOOL_OTHER_AXIS_TOL
    }
    if unsupported:
        detail = " ".join(
            "%s%.6f" % (axis.upper(), value)
            for axis, value in sorted(unsupported.items())
        )
        return "active tool A/B/C/U/V/W offsets are unsupported (%s)" % detail
    if active_z <= 0.0 or active_z < minimum - tolerance or active_z > maximum + tolerance:
        return (
            "active G43 Z length %.6f mm is outside the calibrated %.6f..%.6f mm domain"
            % (active_z, minimum, maximum)
        )
    if abs(evaluated_length - active_z) > LENGTH_CONFIG_TOL:
        return "kinematics length-model evaluation is not synchronized to the active offset"

    try:
        valid = bool(_hal("headheadkins.length-model.valid"))
        fault = int(_hal("headheadkins.length-model.fault-code"))
    except Exception:
        return "cannot read length-model validity diagnostics"
    if not valid:
        return "kinematics length model is invalid (fault %d)" % fault
    return None


def _g92_g52_offsets_active(self):
    try:
        if abs(float(self.params[5210])) < 0.5:
            return False
        return any(abs(float(self.params[index])) > 1e-6 for index in range(5211, 5217))
    except Exception:
        return False


def _machine_ready_error():
    if not bool(_hal("headheadtwp.machine_is_enabled")):
        return "machine must be enabled before TCPC can be changed"
    for joint in range(5):
        if not bool(_hal("headheadtwp.joint_%d_homed" % joint)):
            return "all XYZBC joints must be homed before TCPC can be changed"
    return None


def _twp_defined_or_active():
    return (
        bool(_hal("headheadtwp.motion_enabled"))
        or bool(_hal("headheadtwp.active"))
        or bool(_hal("headheadtwp.valid"))
    )


def _twp_kinematics_is_world():
    return bool(_hal("headheadkins.kinstype-is-world")) and not bool(
        _hal("headheadkins.kinstype-is-twp")
    ) and bool(_hal("headheadkins.kinstype-frame-ready"))


def _twp_kinematics_is_active():
    return bool(_hal("headheadkins.kinstype-is-twp")) and not bool(
        _hal("headheadkins.kinstype-is-world")
    ) and bool(_hal("headheadkins.kinstype-frame-ready"))


def _motion_is_in_position():
    return bool(_hal("motion.in-position"))


def _clear_twp_coordinate_offset():
    for axis in ("x", "y", "z"):
        hal.set_p("headheadkins.twp-coordinate-offset.%s" % axis, "0")


def _return_to_world_and_clear(self):
    transaction_error = _twp_transaction(TWP_TRANSACTION_EXIT)
    if transaction_error is not None:
        return transaction_error
    if not _wait_until(_twp_kinematics_is_world):
        return "kinematics did not return to world mode; TWP frame was preserved"

    self.execute("M66 E0 L0")
    yield INTERP_EXECUTE_FINISH

    clear_error = _twp_transaction(TWP_TRANSACTION_CLEAR)
    if clear_error is not None:
        return clear_error
    _clear_twp_coordinate_offset()
    return None


def _angle_delta_deg(current, reference):
    if not math.isfinite(current) or not math.isfinite(reference):
        return math.nan
    delta = math.remainder(current, 360.0) - math.remainder(reference, 360.0)
    return math.remainder(delta, 360.0)


def _at_tcpc_entry_orientation():
    current_b = float(_hal("headheadtwp.current_joint_b"))
    current_c = float(_hal("headheadtwp.current_joint_c"))
    entry_b = float(_hal("headheadtwp.tcpc_entry_b_angle"))
    entry_c = float(_hal("headheadtwp.tcpc_entry_c_angle"))
    b_delta = current_b - entry_b
    c_delta = _angle_delta_deg(current_c, entry_c)
    return (
        abs(b_delta) <= ROTARY_ENTRY_TOL_DEG
        and abs(c_delta) <= ROTARY_ENTRY_TOL_DEG
    )


def _at_tcpc_zero_orientation():
    current_b = float(_hal("headheadtwp.current_joint_b"))
    current_c = float(_hal("headheadtwp.current_joint_c"))
    return (
        abs(current_b) <= TCPC_ENTRY_ZERO_TOL_DEG
        and abs(current_c) <= TCPC_ENTRY_ZERO_TOL_DEG
    )


def _zero_orientation_message():
    return (
        "G43.4 requires B0.0000 C0.0000 before entering TCPC "
        "(current B%.4f C%.4f)"
        % (
            float(_hal("headheadtwp.current_joint_b")),
            float(_hal("headheadtwp.current_joint_c")),
        )
    )


def _entry_orientation_message():
    return (
        "G49.1 requires B/C back at the TCPC entry orientation "
        "(entry B%.4f C%.4f, current B%.4f C%.4f)"
        % (
            float(_hal("headheadtwp.tcpc_entry_b_angle")),
            float(_hal("headheadtwp.tcpc_entry_c_angle")),
            float(_hal("headheadtwp.current_joint_b")),
            float(_hal("headheadtwp.current_joint_c")),
        )
    )


def enable_tcpc_mode(self, **words):
    del words
    yield INTERP_EXECUTE_FINISH

    ready_error = _machine_ready_error()
    if ready_error is not None:
        yield _set_error(self, "G43.4 rejected: %s" % ready_error)
        return
    if _twp_defined_or_active():
        yield _set_error(self, "G43.4 rejected while TWP is active or defined; run G69 first")
        return
    if not _at_tcpc_zero_orientation():
        yield _set_error(self, _zero_orientation_message())
        return
    length_error = _length_model_entry_error(self)
    if length_error is not None:
        yield _set_error(self, "G43.4 rejected: %s" % length_error)
        return
    if bool(_hal("headheadtwp.tcpc_enabled")):
        yield INTERP_OK
        return
    if _g92_g52_offsets_active(self):
        yield _set_error(self, "G43.4 rejected: clear G52/G92 offsets before entering TCPC")
        return

    _pulse_bit("headheadtwp.cmd_enable_tcpc")
    yield INTERP_EXECUTE_FINISH
    if not bool(_hal("headheadtwp.tcpc_enabled")):
        yield _set_error(self, "G43.4 failed: TCPC state component did not enable")
        return
    yield INTERP_OK


def disable_tcpc_mode(self, **words):
    del words
    yield INTERP_EXECUTE_FINISH

    if _twp_defined_or_active():
        yield _set_error(self, "G49.1 rejected while TWP is active or defined; run G69 first")
        return
    if not bool(_hal("headheadtwp.tcpc_enabled")):
        yield INTERP_OK
        return

    ready_error = _machine_ready_error()
    if ready_error is not None:
        yield _set_error(self, "G49.1 rejected: %s" % ready_error)
        return
    if not _at_tcpc_entry_orientation():
        yield _set_error(self, _entry_orientation_message())
        return

    _pulse_bit("headheadtwp.cmd_disable_tcpc")
    yield INTERP_EXECUTE_FINISH
    if bool(_hal("headheadtwp.tcpc_enabled")):
        yield _set_error(self, "G49.1 failed: TCPC state component did not disable")
        return
    yield INTERP_OK


def enable_twp_mode(self, **words):
    yield INTERP_EXECUTE_FINISH

    if not TWP_ENABLED:
        yield _set_error(
            self,
            "G68.2 rejected: real-machine TWP entry is disabled pending "
            "recovery and supervised machine validation",
        )
        return

    ready_error = _machine_ready_error()
    if ready_error is not None:
        yield _set_error(self, "G68.2 rejected: %s" % ready_error)
        return
    if not _motion_is_in_position():
        yield _set_error(self, "G68.2 rejected: machine motion is not in position")
        return
    if not bool(_hal("headheadtwp.tcpc_enabled")):
        yield _set_error(self, "G68.2 rejected: enable TCPC with G43.4 first")
        return
    if _twp_defined_or_active() or not _twp_kinematics_is_world():
        yield _set_error(self, "G68.2 rejected: TWP is already defined or active")
        return

    length_error = _length_model_entry_error(self)
    if length_error is not None:
        yield _set_error(self, "G68.2 rejected: %s" % length_error)
        return

    coordinate_offset, coordinate_error = _twp_coordinate_state(self)
    if coordinate_error is not None:
        yield _set_error(self, "G68.2 rejected: %s" % coordinate_error)
        return

    has_b = "b" in words
    has_c = "c" in words
    if has_b != has_c:
        yield _set_error(self, "G68.2 requires both B and C words, or neither")
        return

    current_b = float(_hal("headheadtwp.current_joint_b"))
    current_c = float(_hal("headheadtwp.current_joint_c"))
    requested_b = float(words["b"]) if has_b else current_b
    requested_c = float(words["c"]) if has_c else current_c
    normal_rotation = float(words["r"]) if "r" in words else 0.0
    if not all(
        math.isfinite(value)
        for value in (
            current_b,
            current_c,
            requested_b,
            requested_c,
            normal_rotation,
            *coordinate_offset,
        )
    ):
        yield _set_error(self, "G68.2 rejected: TWP parameters are nonfinite")
        return
    if (
        abs(requested_b - current_b) > TWP_POSE_MATCH_TOL_DEG
        or abs(_angle_delta_deg(requested_c, current_c)) > TWP_POSE_MATCH_TOL_DEG
    ):
        yield _set_error(
            self,
            "G68.2 rejected: requested B/C must match the reached pose "
            "(requested B%.6f C%.6f, current B%.6f C%.6f)"
            % (requested_b, requested_c, current_b, current_c),
        )
        return

    # B/C words are assertions for the already reached pose. Latch the live
    # continuous branch so equivalent C words cannot introduce a 360-degree
    # rotary command on the first TWP move.
    hal.set_p("headheadtwp.requested_b_angle", "%.17g" % current_b)
    hal.set_p("headheadtwp.requested_c_angle", "%.17g" % current_c)
    hal.set_p("headheadtwp.requested_normal_rotation", "%.17g" % normal_rotation)
    for axis, value in zip(("x", "y", "z"), coordinate_offset):
        hal.set_p("headheadkins.twp-coordinate-offset.%s" % axis, "%.17g" % value)

    before = _joint_command_pose()
    transaction_error = _twp_transaction(TWP_TRANSACTION_ENTER)
    if transaction_error is not None:
        yield _set_error(self, "G68.2 failed: %s" % transaction_error)
        return
    if not _wait_until(_twp_kinematics_is_active):
        rollback_error = yield from _return_to_world_and_clear(self)
        detail = "kinematics did not enter TWP mode"
        if rollback_error is not None:
            detail += "; rollback failed: %s" % rollback_error
        yield _set_error(self, "G68.2 failed: %s" % detail)
        return

    self.execute("M66 E0 L0")
    yield INTERP_EXECUTE_FINISH
    after = _joint_command_pose()
    continuity_error = _transition_continuity_error(before, after)
    captured_origin = tuple(
        float(_hal("headheadkins.twp-captured-origin.%s" % axis))
        for axis in ("x", "y", "z")
    )
    state_valid = (
        bool(_hal("headheadtwp.valid"))
        and bool(_hal("headheadtwp.active"))
        and bool(_hal("headheadtwp.motion_enabled"))
        and bool(_hal("headheadtwp.tcpc_enabled"))
        and _twp_kinematics_is_active()
    )
    if continuity_error is not None or not all(map(math.isfinite, captured_origin)) or not state_valid:
        rollback_error = yield from _return_to_world_and_clear(self)
        detail = continuity_error or "TWP entry postcondition failed"
        if rollback_error is not None:
            detail += "; rollback failed: %s" % rollback_error
        yield _set_error(self, "G68.2 failed: %s" % detail)
        return

    yield INTERP_OK


def disable_twp_mode(self, **words):
    del words
    yield INTERP_EXECUTE_FINISH

    has_state = _twp_defined_or_active()
    is_world = _twp_kinematics_is_world()
    if not has_state and is_world:
        _clear_twp_coordinate_offset()
        yield INTERP_OK
        return

    ready_error = _machine_ready_error()
    if ready_error is not None:
        yield _set_error(self, "G69 rejected: %s" % ready_error)
        return
    if not _motion_is_in_position():
        yield _set_error(self, "G69 rejected: machine motion is not in position")
        return

    before = _joint_command_pose()
    transaction_error = yield from _return_to_world_and_clear(self)
    if transaction_error is not None:
        yield _set_error(self, "G69 failed: %s" % transaction_error)
        return
    after = _joint_command_pose()
    continuity_error = _transition_continuity_error(before, after)

    state_clear = not _twp_defined_or_active() and _twp_kinematics_is_world()
    if continuity_error is not None:
        yield _set_error(self, "G69 failed: %s" % continuity_error)
        return
    if not state_clear:
        yield _set_error(self, "G69 failed: TWP state did not clear")
        return
    if not bool(_hal("headheadtwp.tcpc_enabled")):
        yield _set_error(self, "G69 failed: TCPC state was not preserved")
        return

    yield INTERP_OK
