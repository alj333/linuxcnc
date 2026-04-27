import sys
from pathlib import Path

CONFIG_PYTHON = Path(__file__).resolve().parents[2] / "python"
if str(CONFIG_PYTHON) not in sys.path:
    sys.path.insert(0, str(CONFIG_PYTHON))

from tcpc_status_widgets import TcpcStatusTab


class UserTab(TcpcStatusTab):
    pass
