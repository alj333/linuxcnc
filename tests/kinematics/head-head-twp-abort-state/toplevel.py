#!/usr/bin/env python3

from pathlib import Path
import sys


CONFIG_PYTHON = Path.cwd().resolve().parents[2] / "configs" / "sim" / "head_head_5axis" / "python"
sys.path.insert(0, str(CONFIG_PYTHON))

import remap  # noqa: F401
