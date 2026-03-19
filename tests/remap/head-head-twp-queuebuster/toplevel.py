import sys
from pathlib import Path


SIM_PYTHON = (
    Path.cwd().resolve().parents[2]
    / "configs"
    / "sim"
    / "head_head_5axis"
    / "python"
)

sys.path.insert(0, str(SIM_PYTHON))

import remap
