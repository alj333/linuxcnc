"""Real-machine TCPC/TWP production remap entry points.

The implementation is shared with the validated head-head simulation remaps.
This wrapper adds real-machine entry/exit checks around the shared TCPC/TWP
motion implementation.
"""

import importlib.util
from pathlib import Path

import hal
from interpreter import INTERP_ERROR, INTERP_EXECUTE_FINISH, INTERP_OK


ROTARY_ENTRY_TOL_DEG = 0.01
TCPC_ENTRY_ZERO_TOL_DEG = 0.005

_SIM_REMAP = (
    Path("/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/python/remap.py")
)
_SPEC = importlib.util.spec_from_file_location("_head_head_sim_remap", _SIM_REMAP)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def _set_error(self, message):
    self.set_errormsg(message)
    return INTERP_ERROR


def _hal(name):
    return hal.get_value(name)


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


enable_twp_mode = _MODULE.enable_twp_mode
disable_twp_mode = _MODULE.disable_twp_mode
