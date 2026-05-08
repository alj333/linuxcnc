#!/usr/bin/env python3

import os
from pathlib import Path
import runpy


os.environ["HEADHEAD_TWP_DEFAULT_TCPC"] = "0"
runpy.run_path(
    str(
        Path(__file__).resolve().parents[3]
        / "configs"
        / "sim"
        / "head_head_5axis"
        / "head_head_twp_state.py"
    ),
    run_name="__main__",
)
