"""Reusable TCPC/TWP status widgets for the TCPC Probe Basic test config."""

try:
    import hal
except Exception:  # pragma: no cover - only used when imported outside LinuxCNC
    hal = None

from qtpy.QtCore import QTimer, Qt
from qtpy.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


POLL_MS = 250


def _read_pin(name, default=None):
    if hal is None:
        return default
    try:
        return hal.get_value(name)
    except Exception:
        return default


def _is_on(value):
    return bool(value)


def _fmt_float(value, digits=3):
    if value is None:
        return "--"
    return f"{float(value):.{digits}f}"


def _fmt_int(value):
    if value is None:
        return "--"
    return str(int(value))


def _fmt_bool(value):
    if value is None:
        return "--"
    return "TRUE" if bool(value) else "FALSE"


def _diff(lhs, rhs):
    if lhs is None or rhs is None:
        return None
    return float(lhs) - float(rhs)


class StatusPill(QLabel):
    def __init__(self, title, parent=None, compact=False):
        super().__init__(parent)
        self.title = title
        self.compact = compact
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(22 if compact else 34)
        if compact:
            self.setMaximumHeight(24)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.set_state("UNKNOWN", "unknown")

    def set_state(self, value, state):
        self.setText(f"{self.title}: {value}" if self.compact else f"{self.title}\n{value}")
        colors = {
            "on": ("#0f3b2e", "#42f2a0", "#051812"),
            "warn": ("#4b360b", "#ffd257", "#1e1300"),
            "off": ("#372024", "#ff7a8a", "#16070a"),
            "unknown": ("#2b2f35", "#c5ccd6", "#111418"),
        }
        bg, fg, border = colors.get(state, colors["unknown"])
        self.setStyleSheet(
            "QLabel {"
            f"background-color: {bg};"
            f"color: {fg};"
            f"border: {'1' if self.compact else '2'}px solid {border};"
            f"border-radius: {'4' if self.compact else '6'}px;"
            "font-weight: 700;"
            f"font-size: {'8' if self.compact else '10'}pt;"
            "font-family: 'DejaVu Sans';"
            f"padding: {'1px 3px' if self.compact else '4px'};"
            "}"
        )


class TcpcStatusReader:
    def snapshot(self):
        tcpc = _read_pin("headheadtwp.tcpc_enabled")
        active = _read_pin("headheadtwp.active")
        motion = _read_pin("headheadtwp.motion_enabled")
        valid = _read_pin("headheadtwp.valid")
        state_code = _read_pin("headheadtwp.state_code")
        b_joint_cmd = _read_pin("joint.3.motor-pos-cmd")
        b_joint_fb = _read_pin("joint.3.motor-pos-fb")
        c_joint_cmd = _read_pin("joint.4.motor-pos-cmd")
        c_joint_fb = _read_pin("joint.4.motor-pos-fb")

        available = tcpc is not None and active is not None and motion is not None
        return {
            "available": available,
            "tcpc": _is_on(tcpc),
            "valid": _is_on(valid),
            "active": _is_on(active),
            "motion": _is_on(motion),
            "state_code": int(state_code) if state_code is not None else None,
            "b_angle": _read_pin("headheadtwp.twp_b_angle"),
            "c_angle": _read_pin("headheadtwp.twp_c_angle"),
            "normal_rotation": _read_pin("headheadtwp.twp_normal_rotation"),
            "tool_vector_x": _read_pin("headheadkins.tool-vector.x"),
            "tool_vector_y": _read_pin("headheadkins.tool-vector.y"),
            "tool_vector_z": _read_pin("headheadkins.tool-vector.z"),
            "tool_offset_x": _read_pin("headheadkins.tool-offset.x"),
            "tool_offset_y": _read_pin("headheadkins.tool-offset.y"),
            "tool_offset_z": _read_pin("headheadkins.tool-offset.z"),
            "tcpc_origin_x": _read_pin("headheadtwp.tcpc_origin_x"),
            "tcpc_origin_y": _read_pin("headheadtwp.tcpc_origin_y"),
            "tcpc_origin_z": _read_pin("headheadtwp.tcpc_origin_z"),
            "tcpc_entry_b": _read_pin("headheadtwp.tcpc_entry_b_angle"),
            "tcpc_entry_c": _read_pin("headheadtwp.tcpc_entry_c_angle"),
            "refined_fit_enabled": _read_pin("headheadkins.sim-bharm-enable"),
            "b_ssi_abs_position": _read_pin("b-ssi-abs-position"),
            "b_ssi_zeroed_position": _read_pin("b-ssi-zeroed-position"),
            "b_ssi_rawcounts": _read_pin("hm2_7i95.0.ssi.00.abs.rawcounts"),
            "b_ssi_invalid": _read_pin("b-ssi-invalid"),
            "b_joint_cmd": b_joint_cmd,
            "b_joint_fb": b_joint_fb,
            "b_following_error": _diff(b_joint_fb, b_joint_cmd),
            "c_ssi_abs_position": _read_pin("c-ssi-abs-position"),
            "c_ssi_zeroed_position": _read_pin("c-ssi-zeroed-position"),
            "c_ssi_rawcounts": _read_pin("hm2_7i95.0.ssi.01.abs.rawcounts"),
            "c_ssi_invalid": _read_pin("c-ssi-invalid"),
            "c_joint_cmd": c_joint_cmd,
            "c_joint_fb": c_joint_fb,
            "c_following_error": _diff(c_joint_fb, c_joint_cmd),
        }


class TcpcStatusStrip(QWidget):
    def __init__(self, parent=None, compact=False):
        super().__init__(parent)
        self.compact = compact
        self.reader = TcpcStatusReader()
        self.tcpc = StatusPill("TCPC", compact=compact)
        self.twp = StatusPill("TWP", compact=compact)
        self.motion = StatusPill("XYZ" if compact else "TWP MOTION", compact=compact)

        if compact:
            self.setFixedHeight(28)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout = QHBoxLayout(self)
            layout.setContentsMargins(1, 1, 1, 1)
            layout.setSpacing(2)
        else:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(1, 2, 1, 2)
            layout.setSpacing(4)

        layout.addWidget(self.tcpc)
        layout.addWidget(self.twp)
        layout.addWidget(self.motion)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(POLL_MS)
        self.update_status()

    def update_status(self):
        state = self.reader.snapshot()
        if not state["available"]:
            self.tcpc.set_state("NO PINS", "unknown")
            self.twp.set_state("NO PINS", "unknown")
            self.motion.set_state("NO PINS", "unknown")
            return

        self.tcpc.set_state("ENABLED" if state["tcpc"] else "OFF", "on" if state["tcpc"] else "off")

        if state["motion"]:
            self.twp.set_state("ACTIVE", "on")
        elif state["active"]:
            self.twp.set_state("ARMED", "warn")
        elif state["valid"]:
            self.twp.set_state("DEFINED", "warn")
        else:
            self.twp.set_state("OFF", "off")

        self.motion.set_state(
            "LOCAL XYZ" if state["motion"] else "WORLD XYZ",
            "on" if state["motion"] else "unknown",
        )


class TcpcStatusLed(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.reader = TcpcStatusReader()
        self.setFixedHeight(22)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.led = QLabel()
        self.led.setFixedSize(12, 12)
        self.label = QLabel("TCPC --")
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label.setStyleSheet(
            "QLabel { color: #d7dee8; font: 700 8pt 'DejaVu Sans'; padding: 0; }"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(5)
        layout.addStretch(1)
        layout.addWidget(self.led)
        layout.addWidget(self.label)
        layout.addStretch(1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(POLL_MS)
        self.update_status()

    def _set_led(self, text, color, border="#111418"):
        self.label.setText(text)
        self.led.setStyleSheet(
            "QLabel {"
            f"background-color: {color};"
            f"border: 1px solid {border};"
            "border-radius: 6px;"
            "}"
        )

    def update_status(self):
        state = self.reader.snapshot()
        if not state["available"]:
            self._set_led("TCPC --", "#64748b", "#1f2937")
        elif state["motion"]:
            self._set_led("TCPC TWP", "#42f2a0", "#051812")
        elif state["tcpc"]:
            self._set_led("TCPC ON", "#42f2a0", "#051812")
        else:
            self._set_led("TCPC OFF", "#ff4d5e", "#16070a")


class TcpcStatusTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.reader = TcpcStatusReader()
        self.setObjectName("TCPC_STATUS")
        self.setProperty("sidebar", False)

        self.strip = TcpcStatusStrip()
        self.fields = {}
        self.rotary_fields = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel("TCPC / TWP STATUS")
        title.setStyleSheet("font: 700 18pt 'DejaVu Sans'; color: #f1f5f9;")
        layout.addWidget(title)
        layout.addWidget(self.strip)

        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background-color: #111827; border: 1px solid #2f3b4a; border-radius: 8px; }"
            "QLabel { color: #d7dee8; font: 12pt 'DejaVu Sans'; }"
        )
        grid = QGridLayout(frame)
        grid.setContentsMargins(14, 12, 14, 12)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)
        layout.addWidget(frame)

        rows = [
            ("State code", "state_code"),
            ("B angle", "b_angle"),
            ("C angle", "c_angle"),
            ("Plane R", "normal_rotation"),
            ("Tool vector X", "tool_vector_x"),
            ("Tool vector Y", "tool_vector_y"),
            ("Tool vector Z", "tool_vector_z"),
            ("Tool offset X", "tool_offset_x"),
            ("Tool offset Y", "tool_offset_y"),
            ("Tool offset Z", "tool_offset_z"),
            ("TCPC origin X", "tcpc_origin_x"),
            ("TCPC origin Y", "tcpc_origin_y"),
            ("TCPC origin Z", "tcpc_origin_z"),
            ("TCPC entry B", "tcpc_entry_b"),
            ("TCPC entry C", "tcpc_entry_c"),
            ("Refined fit", "refined_fit_enabled"),
        ]
        for row, (label, key) in enumerate(rows):
            name = QLabel(label)
            value = QLabel("--")
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(name, row, 0)
            grid.addWidget(value, row, 1)
            self.fields[key] = value

        rotary_frame = QFrame()
        rotary_frame.setStyleSheet(
            "QFrame { background-color: #111827; border: 1px solid #2f3b4a; border-radius: 8px; }"
            "QLabel { color: #d7dee8; font: 11pt 'DejaVu Sans'; }"
        )
        rotary_grid = QGridLayout(rotary_frame)
        rotary_grid.setContentsMargins(14, 12, 14, 12)
        rotary_grid.setHorizontalSpacing(18)
        rotary_grid.setVerticalSpacing(6)
        layout.addWidget(rotary_frame)

        for col, label in ((1, "B"), (2, "C")):
            heading = QLabel(label)
            heading.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            heading.setStyleSheet("font-weight: 700;")
            rotary_grid.addWidget(heading, 0, col)

        rotary_rows = [
            ("SSI abs deg", "ssi_abs_position", _fmt_float),
            ("SSI zeroed deg", "ssi_zeroed_position", _fmt_float),
            ("SSI raw counts", "ssi_rawcounts", _fmt_int),
            ("Joint cmd", "joint_cmd", _fmt_float),
            ("Joint fb", "joint_fb", _fmt_float),
            ("Fb-cmd deg", "following_error", lambda value: _fmt_float(value, 6)),
            ("SSI invalid", "ssi_invalid", _fmt_bool),
        ]
        for row, (label, key, formatter) in enumerate(rotary_rows, start=1):
            name = QLabel(label)
            rotary_grid.addWidget(name, row, 0)
            for axis, col in (("b", 1), ("c", 2)):
                value = QLabel("--")
                value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                rotary_grid.addWidget(value, row, col)
                self.rotary_fields[f"{axis}_{key}"] = (value, formatter)

        note = QLabel(
            "Production TCPC: G43.4 enters after homing, G49.1 exits only after G69 "
            "and after B/C return to the TCPC entry orientation. Apply G43 Hn before "
            "TCPC; G43/G49 are blocked while TCPC is active."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #fbbf24; font: 11pt 'DejaVu Sans';")
        layout.addWidget(note)
        layout.addStretch(1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(POLL_MS)
        self.update_status()

    def update_status(self):
        state = self.reader.snapshot()
        self.fields["state_code"].setText("--" if state["state_code"] is None else str(state["state_code"]))
        for key in (
            "b_angle",
            "c_angle",
            "normal_rotation",
            "tool_vector_x",
            "tool_vector_y",
            "tool_vector_z",
            "tool_offset_x",
            "tool_offset_y",
            "tool_offset_z",
            "tcpc_origin_x",
            "tcpc_origin_y",
            "tcpc_origin_z",
            "tcpc_entry_b",
            "tcpc_entry_c",
        ):
            self.fields[key].setText(_fmt_float(state[key]))
        self.fields["refined_fit_enabled"].setText(_fmt_bool(state["refined_fit_enabled"]))

        for key, (field, formatter) in self.rotary_fields.items():
            field.setText(formatter(state[key]))
