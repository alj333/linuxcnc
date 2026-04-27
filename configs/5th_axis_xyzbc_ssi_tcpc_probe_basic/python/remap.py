"""Real-machine TCPC test config remap entry points.

The implementation is shared with the validated head-head simulation remaps.
This wrapper avoids copying the old 5axiskins remap code into the TCPC config.
"""

import importlib.util
from pathlib import Path

import hal
from interpreter import INTERP_ERROR, INTERP_EXECUTE_FINISH, INTERP_OK


_SIM_REMAP = (
    Path("/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/python/remap.py")
)
_SPEC = importlib.util.spec_from_file_location("_head_head_sim_remap", _SIM_REMAP)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def _set_error(self, message):
    self.set_errormsg(message)
    return INTERP_ERROR


def enable_tcpc_mode(self, **words):
    del words
    yield INTERP_EXECUTE_FINISH
    if not hal.get_value("headheadtwp.tcpc_enabled"):
        yield _set_error(
            self,
            "TCPC is disabled; restart the TCPC config to enable without a kinematics jump",
        )
        return
    yield INTERP_OK


def disable_tcpc_mode(self, **words):
    del words
    yield INTERP_EXECUTE_FINISH
    yield _set_error(
        self,
        "G49.1 is blocked in this TCPC test config; live TCPC disable is not safe yet",
    )


enable_twp_mode = _MODULE.enable_twp_mode
disable_twp_mode = _MODULE.disable_twp_mode
