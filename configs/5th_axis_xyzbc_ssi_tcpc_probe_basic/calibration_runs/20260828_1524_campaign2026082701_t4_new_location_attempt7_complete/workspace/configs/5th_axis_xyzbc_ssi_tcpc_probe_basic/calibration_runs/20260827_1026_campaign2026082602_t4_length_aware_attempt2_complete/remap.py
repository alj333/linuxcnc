"""Real-machine TCPC/TWP production remap entry points.

The implementation is shared with the validated head-head simulation remaps.
This wrapper adds real-machine entry/exit checks around the shared TCPC/TWP
motion implementation.
"""

import importlib.util
import math
import os
from pathlib import Path

import hal
import linuxcnc
from interpreter import INTERP_ERROR, INTERP_EXECUTE_FINISH, INTERP_OK


ROTARY_ENTRY_TOL_DEG = 0.01
TCPC_ENTRY_ZERO_TOL_DEG = 0.005
REAL_MACHINE_TWP_ENABLED = False
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

_SIM_REMAP = (
    Path("/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/python/remap.py")
)
_SPEC = importlib.util.spec_from_file_location("_head_head_sim_remap", _SIM_REMAP)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


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


def _set_error(self, message):
    self.set_errormsg(message)
    return INTERP_ERROR


def _hal(name):
    return hal.get_value(name)


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


def _angle_delta_deg(current, reference):
    delta = current - reference
    while delta > 180.0:
        delta -= 360.0
    while delta < -180.0:
        delta += 360.0
    return delta


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

    _MODULE._pulse_bit("headheadtwp.cmd_enable_tcpc")
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

    _MODULE._pulse_bit("headheadtwp.cmd_disable_tcpc")
    yield INTERP_EXECUTE_FINISH
    if bool(_hal("headheadtwp.tcpc_enabled")):
        yield _set_error(self, "G49.1 failed: TCPC state component did not disable")
        return
    yield INTERP_OK


def enable_twp_mode(self, **words):
    yield INTERP_EXECUTE_FINISH

    if not REAL_MACHINE_TWP_ENABLED:
        yield _set_error(
            self,
            "G68.2 rejected: real-machine TWP entry is disabled pending "
            "entry-continuity validation",
        )
        return

    yield from _MODULE.enable_twp_mode(self, **words)


disable_twp_mode = _MODULE.disable_twp_mode
