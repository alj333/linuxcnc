#!/usr/bin/env python3

import os
from pathlib import Path
import sys


INI_PATH = Path(os.environ["INI_FILE_NAME"]).resolve()
CONFIG_PYTHON = (
    INI_PATH.parents[3]
    / "configs"
    / "5th_axis_xyzbc_ssi_tcpc_probe_basic"
    / "python"
)
sys.path.insert(0, str(CONFIG_PYTHON))

import remap  # noqa: F401
