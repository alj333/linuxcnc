import sys
from pathlib import Path

from qtpy.QtWidgets import QSizePolicy, QWidget, QVBoxLayout

CONFIG_PYTHON = Path(__file__).resolve().parents[2] / "python"
if str(CONFIG_PYTHON) not in sys.path:
    sys.path.insert(0, str(CONFIG_PYTHON))

from tcpc_status_widgets import TcpcStatusLed


class UserButton(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TCPC_STATUS_INDICATOR")
        self.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(TcpcStatusLed())
