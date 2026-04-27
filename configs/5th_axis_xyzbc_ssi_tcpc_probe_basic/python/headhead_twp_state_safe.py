#!/usr/bin/env python3

"""Run the shared head-head TWP state component with TCPC enabled at startup.

Live TCPC on/off switching currently causes a kinematics position discontinuity.
This test config starts with TCPC enabled and blocks G49.1 until a safe
transition strategy is implemented.
"""

import os
import runpy


os.environ.setdefault("HEADHEAD_TWP_DEFAULT_TCPC", "1")
runpy.run_path(
    "/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/head_head_twp_state.py",
    run_name="__main__",
)
