#!/usr/bin/env python3

"""Run the shared head-head TWP state component fail-safe for production TCPC.

The real-machine config starts with TCPC disabled. G43.4 sets a live TCPC
entry origin only from explicit B0/C0, and G49.1 is allowed only when the
production remap checks prove the current B/C orientation is safe to leave
TCPC. It also enables the
interpreter guard that rejects ordinary G43/G49 tool-length changes while TCPC
is active.
"""

import os
import runpy


os.environ.setdefault("HEADHEAD_TWP_DEFAULT_TCPC", "0")
os.environ.setdefault("HEADHEAD_TWP_TOOL_LENGTH_GUARD", "1")
runpy.run_path(
    "/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/head_head_twp_state.py",
    run_name="__main__",
)
