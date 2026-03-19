import configparser
import json
import os
import subprocess
from pathlib import Path

import hal
import linuxcnc
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QApplication,
    QFrame,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


CONFIG_DIR = Path(__file__).resolve().parents[2]
BASELINE_FILE = CONFIG_DIR / "geometry_baseline.ini"
DRAFT_FILE = CONFIG_DIR / "five_axis_calibration_draft.json"


class UserTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("5_axis_calibration")
        self.setProperty("sidebar", False)

        self.command = linuxcnc.command()
        self.status = linuxcnc.stat()
        self.baseline = self._load_baseline()
        self.offset_fields = {}
        self.metadata_fields = {}
        self.capture_fields = {}
        self.note_fields = {}
        self.capture_preview = None
        self.generated_preview = None
        self.status_banner = None
        self.step_list = None
        self.step_stack = None

        self._build_ui()
        self._load_draft()
        self._update_summary()

    def _load_baseline(self):
        cfg = configparser.ConfigParser()
        cfg.read(BASELINE_FILE)
        return {
            "c_to_b": {
                "x": cfg.getfloat("GEOMETRY_NOMINAL", "C_TO_B_X", fallback=0.0),
                "y": cfg.getfloat("GEOMETRY_NOMINAL", "C_TO_B_Y", fallback=0.0),
                "z": cfg.getfloat("GEOMETRY_NOMINAL", "C_TO_B_Z", fallback=0.0),
            },
            "b_to_tool": {
                "x": cfg.getfloat("GEOMETRY_NOMINAL", "B_TO_SPINDLE_X", fallback=0.0),
                "y": cfg.getfloat("GEOMETRY_NOMINAL", "B_TO_SPINDLE_Y", fallback=0.0),
                "z": cfg.getfloat("GEOMETRY_NOMINAL", "B_TO_SPINDLE_Z", fallback=0.0),
            },
            "zero_offsets": {
                "b": cfg.getfloat("CALIBRATION_DEFAULTS", "B_ZERO_OFFSET", fallback=0.0),
                "c": cfg.getfloat("CALIBRATION_DEFAULTS", "C_ZERO_OFFSET", fallback=0.0),
            },
        }

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll)

        content = QWidget()
        content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        scroll.setWidget(content)

        layout_root = QVBoxLayout(content)
        layout_root.setContentsMargins(0, 0, 0, 0)
        layout_root.setSpacing(10)

        title = QLabel("Head-Head 5-Axis Calibration Wizard")
        title.setStyleSheet("font: 24px 'Bebas Kai'; color: white;")
        layout_root.addWidget(title)

        intro = QLabel(
            "Use this page to step through rotary zero checks, head offset capture, "
            "and final TCP/TWP verification. The summary panel builds the HAL values "
            "to carry into the head-head model."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("font-size: 13px;")
        layout_root.addWidget(intro)

        self.status_banner = QLabel("Wizard ready. Load live HAL values or enter measured corrections.")
        self.status_banner.setWordWrap(True)
        self.status_banner.setStyleSheet("font-size: 12px; color: #d8f0ff;")
        layout_root.addWidget(self.status_banner)

        body = QHBoxLayout()
        body.setSpacing(12)
        layout_root.addLayout(body, 1)

        self.step_list = QListWidget()
        self.step_list.setMaximumWidth(240)
        self.step_list.currentRowChanged.connect(self._set_step_index)
        body.addWidget(self.step_list)

        self.step_stack = QStackedWidget()
        self.step_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        body.addWidget(self.step_stack, 1)

        self._stack_pages = []
        for title_text, page in self._build_pages():
            item = QListWidgetItem(title_text)
            self.step_list.addItem(item)
            page.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            self.step_stack.addWidget(page)
            self._stack_pages.append(page)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        layout_root.addLayout(actions)

        prev_button = QPushButton("Previous Step")
        prev_button.clicked.connect(self._prev_step)
        actions.addWidget(prev_button)

        next_button = QPushButton("Next Step")
        next_button.clicked.connect(self._next_step)
        actions.addWidget(next_button)

        save_button = QPushButton("Save Draft")
        save_button.clicked.connect(self._save_draft)
        actions.addWidget(save_button)

        load_button = QPushButton("Reload Draft")
        load_button.clicked.connect(self._load_draft)
        actions.addWidget(load_button)

        live_button = QPushButton("Load Live HAL")
        live_button.clicked.connect(self._load_live_hal)
        actions.addWidget(live_button)

        apply_button = QPushButton("Apply To Running Sim")
        apply_button.clicked.connect(self._apply_to_running_sim)
        actions.addWidget(apply_button)

        copy_button = QPushButton("Copy HAL Summary")
        copy_button.clicked.connect(self._copy_summary)
        actions.addWidget(copy_button)

        actions.addStretch(1)

        layout_root.addStretch(1)

        self.step_list.setCurrentRow(0)

    def _build_pages(self):
        return [
            ("Setup", self._build_setup_page()),
            ("Probe Qual", self._build_probe_qualification_page()),
            ("Sphere Map", self._build_sphere_capture_page()),
            ("Rotary Zero", self._build_rotary_page()),
            ("C To B", self._build_c_to_b_page()),
            ("B To Tool", self._build_b_to_tool_page()),
            ("Verify", self._build_verify_page()),
            ("Summary", self._build_summary_page()),
        ]

    def _page_shell(self, heading, detail):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        label = QLabel(heading)
        label.setStyleSheet("font: 20px 'Bebas Kai'; color: white;")
        layout.addWidget(label)

        text = QLabel(detail)
        text.setWordWrap(True)
        text.setStyleSheet("font-size: 13px;")
        layout.addWidget(text)
        return page, layout

    def _build_setup_page(self):
        page, layout = self._page_shell(
            "Setup And Safety",
            "Start from a known state with the actual shop tooling: qualify the OMP40-style "
            "wireless probe, place the 20 mm sphere on its tall 45 degree stand, and keep the "
            "granite square ready for final plane verification.",
        )

        button_row = QHBoxLayout()
        layout.addLayout(button_row)

        reset_button = QPushButton("Clear TWP")
        reset_button.clicked.connect(lambda: self._issue_mdi("G69"))
        button_row.addWidget(reset_button)

        tcpc_off_button = QPushButton("TCPC Off")
        tcpc_off_button.clicked.connect(lambda: self._issue_mdi("G49.1"))
        button_row.addWidget(tcpc_off_button)

        tcpc_on_button = QPushButton("TCPC On")
        tcpc_on_button.clicked.connect(lambda: self._issue_mdi("G43.4"))
        button_row.addWidget(tcpc_on_button)

        safe_pose_button = QPushButton("Go To Safe Pose")
        safe_pose_button.clicked.connect(
            lambda: self._issue_mdi("G0 X1500 Y850 Z-600 B0 C0")
        )
        button_row.addWidget(safe_pose_button)

        layout.addWidget(self._instruction_box("Procedure", [
            "1. Home the machine and confirm no active TWP state.",
            "2. Fit and verify the wireless probe before any 5-axis geometry capture.",
            "3. Place the 20 mm sphere on the tall 45 degree stand in a reachable part of travel.",
            "4. Keep the granite square available for the final TWP plane sanity check.",
            "5. Use Save Draft often while building up the calibration set.",
        ]))

        layout.addWidget(self._notes_box(
            "setup_notes",
            "Record probe stylus details, sphere stand location, granite square setup, and safety notes here.",
        ))
        layout.addStretch(1)
        return page

    def _build_probe_qualification_page(self):
        page, layout = self._page_shell(
            "Probe Qualification",
            "Qualify the OMP40-style probe with the 50 mm calibration ring before using the 20 mm sphere "
            "for rotary calibration. This step captures the measurement conditions that support the geometry data.",
        )

        artifact_box = QGroupBox("Qualification setup")
        artifact_form = QFormLayout(artifact_box)
        artifact_form.addRow("Ring ID (mm)", self._metadata_entry("ring_id_mm", "50.0"))
        artifact_form.addRow("Sphere diameter (mm)", self._metadata_entry("sphere_diameter_mm", "20.0"))
        artifact_form.addRow("Sphere stand angle (deg)", self._metadata_entry("sphere_stand_angle_deg", "45.0"))
        artifact_form.addRow("Probe repeatability in ring (mm)", self._metadata_entry("probe_repeatability_mm", "0.0"))
        artifact_form.addRow("Sphere center repeatability (mm)", self._metadata_entry("sphere_repeatability_mm", "0.0"))
        layout.addWidget(artifact_box)

        pose_row = QHBoxLayout()
        layout.addLayout(pose_row)
        pose_row.addWidget(self._mdi_button("Probe Safe Pose", "G0 X1500 Y850 Z-600 B0 C0"))
        pose_row.addWidget(self._mdi_button("Sphere Pose", "G0 X1500 Y850 Z-600 B45 C90"))
        pose_row.addStretch(1)

        layout.addWidget(self._instruction_box("Qualification sequence", [
            "1. Qualify the probe stylus in the 50 mm ID ring and record repeatability.",
            "2. Touch the 20 mm sphere several times at B0/C0 to confirm stable sphere-center pickup.",
            "3. Re-check the sphere at a second rotary pose before trusting any 5-axis geometry capture.",
            "4. If repeatability is poor, stop here and resolve probe or fixture issues before continuing.",
        ]))

        layout.addWidget(self._notes_box(
            "probe_qualification_notes",
            "Record ring location, probe stylus configuration, measured repeatability, and whether the sphere center capture looked stable.",
        ))
        layout.addStretch(1)
        return page

    def _build_sphere_capture_page(self):
        page, layout = self._page_shell(
            "Sphere Center Capture Map",
            "Use the 20 mm sphere as the common artifact and record the measured sphere center at a small fixed pose set. "
            "This gives a repeatable drift map before adjusting rotary zero or geometry offsets.",
        )

        action_row = QHBoxLayout()
        layout.addLayout(action_row)
        action_row.addWidget(self._program_button("Load Capture Sequence", "calibration_sphere_capture_sequence.ngc"))
        action_row.addWidget(self._mdi_button("Safe Pose", "G0 X1500 Y850 Z-600 B0 C0"))
        action_row.addStretch(1)

        capture_box = QGroupBox("Measured sphere centers")
        capture_grid = QGridLayout(capture_box)
        headers = ["Pose", "Target", "X", "Y", "Z", "B", "C", ""]
        for col, text in enumerate(headers):
            capture_grid.addWidget(QLabel(text), 0, col)

        capture_rows = [
            ("ref", "Reference", "B0 C0", 0.0, 0.0),
            ("b_pos", "B plus", "B45 C0", 45.0, 0.0),
            ("b_neg", "B minus", "B-45 C0", -45.0, 0.0),
            ("c_pos", "C plus", "B0 C90", 0.0, 90.0),
            ("c_neg", "C minus", "B0 C-90", 0.0, -90.0),
            ("bc_mix", "Mixed", "B45 C90", 45.0, 90.0),
        ]
        for row_index, (prefix, label, target, target_b, target_c) in enumerate(capture_rows, start=1):
            capture_grid.addWidget(QLabel(label), row_index, 0)
            capture_grid.addWidget(QLabel(target), row_index, 1)
            capture_grid.addWidget(self._capture_entry(f"{prefix}_x"), row_index, 2)
            capture_grid.addWidget(self._capture_entry(f"{prefix}_y"), row_index, 3)
            capture_grid.addWidget(self._capture_entry(f"{prefix}_z"), row_index, 4)
            capture_grid.addWidget(self._capture_entry(f"{prefix}_b"), row_index, 5)
            capture_grid.addWidget(self._capture_entry(f"{prefix}_c"), row_index, 6)
            capture_button = QPushButton("Capture Current")
            capture_button.clicked.connect(
                lambda _checked=False, pose_prefix=prefix, b_target=target_b, c_target=target_c:
                self._capture_current_position(pose_prefix, b_target, c_target)
            )
            capture_grid.addWidget(capture_button, row_index, 7)
        layout.addWidget(capture_box)

        self.capture_preview = QPlainTextEdit()
        self.capture_preview.setReadOnly(True)
        self.capture_preview.setMinimumHeight(180)
        layout.addWidget(self.capture_preview)

        layout.addWidget(self._instruction_box("Capture sequence", [
            "1. Run the capture sequence program or move manually to each listed B/C pose.",
            "2. At each stop, probe the 20 mm sphere center with the same probing routine.",
            "3. When the machine is sitting at the measured sphere center, press Capture Current for that pose.",
            "4. Use the drift table below to compare every pose back to the B0/C0 reference before changing offsets.",
        ]))

        layout.addWidget(self._notes_box(
            "sphere_capture_notes",
            "Record the probing cycle used, whether the sphere was reached cleanly at every pose, and any capture that looked suspicious.",
        ))
        layout.addStretch(1)
        return page

    def _build_rotary_page(self):
        page, layout = self._page_shell(
            "Rotary Zero Offsets",
            "Use the qualified probe and the mounted 20 mm sphere to confirm the angular zero "
            "corrections needed to make B0/C0 and a second rotary pose match the expected head orientation.",
        )

        layout.addWidget(self._current_baseline_box("Current defaults", {
            "B zero offset": self.baseline["zero_offsets"]["b"],
            "C zero offset": self.baseline["zero_offsets"]["c"],
        }, "deg"))

        form_box = QGroupBox("Measured rotary corrections")
        form = QFormLayout(form_box)
        form.addRow("B zero offset (deg)", self._offset_entry("b_zero_offset"))
        form.addRow("C zero offset (deg)", self._offset_entry("c_zero_offset"))
        layout.addWidget(form_box)

        pose_row = QHBoxLayout()
        layout.addLayout(pose_row)
        pose_row.addWidget(self._mdi_button("Check B0 C0", "G0 X1500 Y850 Z-600 B0 C0"))
        pose_row.addWidget(self._mdi_button("Check B45 C90", "G0 X1500 Y850 Z-600 B45 C90"))
        pose_row.addStretch(1)

        layout.addWidget(self._instruction_box("How to measure", [
            "1. Start from the sphere capture map and look at the B plus/B minus and C plus/C minus drift symmetry.",
            "2. Use rotary zero offsets to reduce the paired directional error first, before touching geometry corrections.",
            "3. Re-check at B45/C90 or another reachable mixed pose to confirm the chosen sign convention still helps.",
            "4. Use the granite square only as a secondary visual check, not the primary source of zero-offset values.",
            "5. Enter only the extra rotary correction needed beyond the nominal zero model.",
        ]))

        layout.addWidget(self._notes_box(
            "rotary_notes",
            "Record which sphere poses were used and what confirmed the final B/C zero sign.",
        ))
        layout.addStretch(1)
        return page

    def _build_c_to_b_page(self):
        page, layout = self._page_shell(
            "C Pivot To B Pivot Offsets",
            "Measure the delta from the C rotation center to the B rotation center. "
            "Use repeated sphere-center captures across C and B motion to solve the `cal-c-to-b` corrections "
            "on top of the nominal model.",
        )

        layout.addWidget(self._current_baseline_box("Nominal C to B", {
            "X": self.baseline["c_to_b"]["x"],
            "Y": self.baseline["c_to_b"]["y"],
            "Z": self.baseline["c_to_b"]["z"],
        }, "mm"))

        form_box = QGroupBox("Measured C to B corrections")
        form = QFormLayout(form_box)
        form.addRow("cal-c-to-b.x (mm)", self._offset_entry("cal_c_to_b_x"))
        form.addRow("cal-c-to-b.y (mm)", self._offset_entry("cal_c_to_b_y"))
        form.addRow("cal-c-to-b.z (mm)", self._offset_entry("cal_c_to_b_z"))
        layout.addWidget(form_box)

        layout.addWidget(self._instruction_box("How to measure", [
            "1. Use the sphere capture map after rotary zero is reasonably close.",
            "2. Look for common drift that remains in the C-related poses after B/C zero is no longer the dominant issue.",
            "3. Keep the sphere stand fixed; only the machine should move between captures.",
            "4. Record only the small correction beyond the nominal C->B vector.",
            "5. Positive values follow the head-head model signs shown in the summary block.",
        ]))

        layout.addWidget(self._notes_box(
            "c_to_b_notes",
            "Describe the sphere stand location, the rotary poses used, and how the C/B center relationship was derived.",
        ))
        layout.addStretch(1)
        return page

    def _build_b_to_tool_page(self):
        page, layout = self._page_shell(
            "B Pivot To Tool Reference Offsets",
            "Measure the spindle/tool reference point relative to the B center at B0/C0. "
            "Use the qualified probe and sphere captures to solve the `cal-b-to-tool` corrections.",
        )

        layout.addWidget(self._current_baseline_box("Nominal B to tool", {
            "X": self.baseline["b_to_tool"]["x"],
            "Y": self.baseline["b_to_tool"]["y"],
            "Z": self.baseline["b_to_tool"]["z"],
        }, "mm"))

        form_box = QGroupBox("Measured B to tool corrections")
        form = QFormLayout(form_box)
        form.addRow("cal-b-to-tool.x (mm)", self._offset_entry("cal_b_to_tool_x"))
        form.addRow("cal-b-to-tool.y (mm)", self._offset_entry("cal_b_to_tool_y"))
        form.addRow("cal-b-to-tool.z (mm)", self._offset_entry("cal_b_to_tool_z"))
        layout.addWidget(form_box)

        layout.addWidget(self._instruction_box("How to measure", [
            "1. Use the same qualified probe and sphere reference for all captures in this section.",
            "2. After rotary zero is close, look for the remaining B-related drift that persists in fixed-tip TCPC checks.",
            "3. Use B-only and mixed B/C poses to judge whether the spindle reference point is still offset from the B center model.",
            "4. Re-check at an additional B tilt to confirm the solved offset behaves consistently.",
            "5. Enter only the correction beyond the nominal spindle offset model.",
        ]))

        layout.addWidget(self._notes_box(
            "b_to_tool_notes",
            "Record the probe configuration, tool reference definition, and any measured spindle centerline shift.",
        ))
        layout.addStretch(1)
        return page

    def _build_verify_page(self):
        page, layout = self._page_shell(
            "Verification",
            "After updating offsets, verify fixed-tip TCPC, moving TCP motion, and tilted-plane motion "
            "using the current sample programs, the 20 mm sphere, and the granite square.",
        )

        grid = QGridLayout()
        layout.addLayout(grid)

        grid.addWidget(self._program_button("Load B/C Alignment", "calibration_bc_alignment_check.ngc"), 0, 0)
        grid.addWidget(self._program_button("Load Fixed-Tip TCPC", "calibration_tcpc_fixed_tip_check.ngc"), 0, 1)
        grid.addWidget(self._program_button("Load Moving TCPC", "calibration_tcpc_motion_check.ngc"), 1, 0)
        grid.addWidget(self._program_button("Load TWP Demo", "twp_g68_2_fresh_demo.ngc"), 1, 1)
        grid.addWidget(self._program_button("Load Machine Fixed-Tip", "machine_tcp_fixed_tip_probe_check.ngc"), 2, 0)
        grid.addWidget(self._program_button("Load Machine Moving TCP", "machine_tcp_motion_probe_check.ngc"), 2, 1)
        grid.addWidget(self._program_button("Load Machine TWP Check", "machine_twp_granite_square_check.ngc"), 3, 0)
        grid.addWidget(self._mdi_button("Enable TCPC", "G43.4"), 3, 1)
        grid.addWidget(self._mdi_button("Cancel TWP", "G69"), 4, 0)
        grid.addWidget(self._mdi_button("Disable TCPC", "G49.1"), 4, 1)
        grid.addWidget(self._mdi_button("Tilt Pose", "G0 X1500 Y850 Z-600 B45 C90"), 5, 0)

        verify_log = QGroupBox("Machine verification log")
        verify_form = QFormLayout(verify_log)
        verify_form.addRow(
            "Fixed-tip TCP result",
            self._metadata_entry("verify_fixed_tip_result", "pending"),
        )
        verify_form.addRow(
            "Fixed-tip first drift pose",
            self._metadata_entry("verify_fixed_tip_first_drift_pose", ""),
        )
        verify_form.addRow(
            "Fixed-tip likely cause",
            self._metadata_entry("verify_fixed_tip_likely_cause", ""),
        )
        verify_form.addRow(
            "Moving TCP result",
            self._metadata_entry("verify_moving_tcp_result", "pending"),
        )
        verify_form.addRow(
            "Moving TCP first drift pose",
            self._metadata_entry("verify_moving_tcp_first_drift_pose", ""),
        )
        verify_form.addRow(
            "Moving TCP likely cause",
            self._metadata_entry("verify_moving_tcp_likely_cause", ""),
        )
        verify_form.addRow(
            "TWP granite-square result",
            self._metadata_entry("verify_twp_result", "pending"),
        )
        verify_form.addRow(
            "TWP first drift pose",
            self._metadata_entry("verify_twp_first_drift_pose", ""),
        )
        verify_form.addRow(
            "TWP likely cause",
            self._metadata_entry("verify_twp_likely_cause", ""),
        )
        layout.addWidget(verify_log)

        layout.addWidget(self._instruction_box("Acceptance checks", [
            "1. B/C alignment check: verify basic rotary direction and zero logic with TCPC off.",
            "2. Fixed-tip TCPC check: the measured sphere center should stay put while B/C change.",
            "3. Moving TCPC check: the TCP path should stay smooth with no visible swing or jump.",
            "4. Machine fixed-tip TCP: run on the real sphere setup and watch for any tip walk-off.",
            "5. Machine moving TCP: confirm smooth path quality before trusting 5-axis toolpaths.",
            "6. Machine TWP check: use the granite square as a final sanity check on the tilted plane.",
            "7. If anything drifts, update the offsets and use Apply To Running Sim before retesting.",
        ]))

        layout.addWidget(self._notes_box(
            "verify_notes",
            "Record sphere-center drift, granite-square observations, and which sample program passed.",
        ))
        layout.addStretch(1)
        return page

    def _build_summary_page(self):
        page, layout = self._page_shell(
            "Summary And HAL Values",
            "Review the proposed calibration block below. This is a staging summary only; "
            "it does not write machine values automatically.",
        )

        self.generated_preview = QPlainTextEdit()
        self.generated_preview.setReadOnly(True)
        self.generated_preview.setMinimumHeight(320)
        layout.addWidget(self.generated_preview)
        layout.addWidget(self._instruction_box("Apply behavior", [
            "Apply To Running Sim updates the live headheadkins, headheadtwp, and vismach pins.",
            "This is a simulation/staging action only; it does not write permanent machine config files.",
        ]))
        layout.addStretch(1)
        return page

    def _current_baseline_box(self, title, values, units):
        box = QGroupBox(title)
        form = QFormLayout(box)
        for label, value in values.items():
            value_label = QLabel(f"{value:.3f} {units}")
            form.addRow(label, value_label)
        return box

    def _offset_entry(self, key):
        entry = QLineEdit("0.0")
        entry.textChanged.connect(self._update_summary)
        self.offset_fields[key] = entry
        return entry

    def _capture_entry(self, key):
        entry = QLineEdit("")
        entry.textChanged.connect(self._update_summary)
        self.capture_fields[key] = entry
        return entry

    def _metadata_entry(self, key, default):
        entry = QLineEdit(default)
        entry.textChanged.connect(self._update_summary)
        self.metadata_fields[key] = entry
        return entry

    def _instruction_box(self, title, lines):
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        text = QLabel("\n".join(lines))
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(text)
        return box

    def _notes_box(self, key, placeholder):
        box = QGroupBox("Operator notes")
        layout = QVBoxLayout(box)
        edit = QTextEdit()
        edit.setPlaceholderText(placeholder)
        edit.textChanged.connect(self._update_summary)
        layout.addWidget(edit)
        self.note_fields[key] = edit
        return box

    def _mdi_button(self, label, command):
        button = QPushButton(label)
        button.clicked.connect(lambda: self._issue_mdi(command))
        return button

    def _program_button(self, label, filename):
        button = QPushButton(label)
        path = str(CONFIG_DIR / filename)
        button.clicked.connect(lambda: self._load_program(path))
        return button

    def _set_step_index(self, index):
        if index < 0:
            return
        self.step_stack.setCurrentIndex(index)
        self._update_summary()

    def _prev_step(self):
        row = max(0, self.step_list.currentRow() - 1)
        self.step_list.setCurrentRow(row)

    def _next_step(self):
        row = min(self.step_list.count() - 1, self.step_list.currentRow() + 1)
        self.step_list.setCurrentRow(row)

    def _issue_mdi(self, command):
        try:
            self.command.mode(linuxcnc.MODE_MDI)
            self.command.wait_complete()
            self.command.mdi(command)
            self._set_status(f"MDI sent: {command}")
        except linuxcnc.error as exc:
            self._set_status(f"MDI error: {exc}", error=True)
            QMessageBox.warning(self, "MDI error", str(exc))

    def _load_program(self, path):
        try:
            self.command.mode(linuxcnc.MODE_AUTO)
            self.command.wait_complete()
            self.command.program_open(path)
            self._set_status(f"Loaded program: {Path(path).name}")
        except linuxcnc.error as exc:
            self._set_status(f"Program load error: {exc}", error=True)
            QMessageBox.warning(self, "Program load error", str(exc))

    def _float_value(self, key):
        text = self.offset_fields[key].text().strip()
        try:
            return float(text)
        except ValueError:
            return 0.0

    def _capture_float(self, key):
        field = self.capture_fields.get(key)
        if field is None:
            return 0.0
        text = field.text().strip()
        try:
            return float(text)
        except ValueError:
            return 0.0

    def _capture_delta(self, prefix):
        return (
            self._capture_float(f"{prefix}_x") - self._capture_float("ref_x"),
            self._capture_float(f"{prefix}_y") - self._capture_float("ref_y"),
            self._capture_float(f"{prefix}_z") - self._capture_float("ref_z"),
        )

    def _format_vec(self, vec):
        return f"({vec[0]:+.3f}, {vec[1]:+.3f}, {vec[2]:+.3f})"

    def _update_capture_preview(self):
        if self.capture_preview is None:
            return
        ref = (
            self._capture_float("ref_x"),
            self._capture_float("ref_y"),
            self._capture_float("ref_z"),
        )
        lines = [
            "Reference sphere center XYZ",
            self._format_vec(ref),
            "",
            "Drift from reference",
            f"B plus   {self._format_vec(self._capture_delta('b_pos'))}",
            f"B minus  {self._format_vec(self._capture_delta('b_neg'))}",
            f"C plus   {self._format_vec(self._capture_delta('c_pos'))}",
            f"C minus  {self._format_vec(self._capture_delta('c_neg'))}",
            f"Mixed    {self._format_vec(self._capture_delta('bc_mix'))}",
            "",
            "Quick reading guide",
            "- paired B drift that flips direction usually points to B zero first",
            "- paired C drift that flips direction usually points to C zero first",
            "- common remaining drift after zero cleanup points toward geometry correction",
        ]
        self.capture_preview.setPlainText("\n".join(lines))

    def _update_summary(self):
        if self.generated_preview is None:
            return
        self._update_capture_preview()
        lines = [
            "# Head-head 5-axis calibration summary",
            "",
            "# Measurement setup",
            f"# Probe ring ID (mm): {self._metadata_value('ring_id_mm', '50.0')}",
            f"# Sphere diameter (mm): {self._metadata_value('sphere_diameter_mm', '20.0')}",
            f"# Sphere stand angle (deg): {self._metadata_value('sphere_stand_angle_deg', '45.0')}",
            f"# Probe repeatability in ring (mm): {self._metadata_value('probe_repeatability_mm', '0.0')}",
            f"# Sphere center repeatability (mm): {self._metadata_value('sphere_repeatability_mm', '0.0')}",
            f"# Fixed-tip TCP result: {self._metadata_value('verify_fixed_tip_result', 'pending')}",
            f"# Fixed-tip first drift pose: {self._metadata_value('verify_fixed_tip_first_drift_pose', '')}",
            f"# Fixed-tip likely cause: {self._metadata_value('verify_fixed_tip_likely_cause', '')}",
            f"# Moving TCP result: {self._metadata_value('verify_moving_tcp_result', 'pending')}",
            f"# Moving TCP first drift pose: {self._metadata_value('verify_moving_tcp_first_drift_pose', '')}",
            f"# Moving TCP likely cause: {self._metadata_value('verify_moving_tcp_likely_cause', '')}",
            f"# TWP result: {self._metadata_value('verify_twp_result', 'pending')}",
            f"# TWP first drift pose: {self._metadata_value('verify_twp_first_drift_pose', '')}",
            f"# TWP likely cause: {self._metadata_value('verify_twp_likely_cause', '')}",
            "",
            "# Captured sphere centers",
            f"# ref_xyz = {self._format_vec((self._capture_float('ref_x'), self._capture_float('ref_y'), self._capture_float('ref_z')))}",
            f"# b_pos_delta = {self._format_vec(self._capture_delta('b_pos'))}",
            f"# b_neg_delta = {self._format_vec(self._capture_delta('b_neg'))}",
            f"# c_pos_delta = {self._format_vec(self._capture_delta('c_pos'))}",
            f"# c_neg_delta = {self._format_vec(self._capture_delta('c_neg'))}",
            f"# bc_mix_delta = {self._format_vec(self._capture_delta('bc_mix'))}",
            "",
            "# Rotary zero offsets",
            f"setp headheadkins.b-zero-offset {self._float_value('b_zero_offset'):.6f}",
            f"setp headheadkins.c-zero-offset {self._float_value('c_zero_offset'):.6f}",
            f"setp headheadtwp.b_zero_offset {self._float_value('b_zero_offset'):.6f}",
            f"setp headheadtwp.c_zero_offset {self._float_value('c_zero_offset'):.6f}",
            "",
            "# C pivot to B pivot correction",
            f"setp headheadkins.cal-c-to-b.x {self._float_value('cal_c_to_b_x'):.6f}",
            f"setp headheadkins.cal-c-to-b.y {self._float_value('cal_c_to_b_y'):.6f}",
            f"setp headheadkins.cal-c-to-b.z {self._float_value('cal_c_to_b_z'):.6f}",
            f"setp headheadtwp.cal_c_to_b_x {self._float_value('cal_c_to_b_x'):.6f}",
            f"setp headheadtwp.cal_c_to_b_y {self._float_value('cal_c_to_b_y'):.6f}",
            f"setp headheadtwp.cal_c_to_b_z {self._float_value('cal_c_to_b_z'):.6f}",
            "",
            "# B pivot to tool correction",
            f"setp headheadkins.cal-b-to-tool.x {self._float_value('cal_b_to_tool_x'):.6f}",
            f"setp headheadkins.cal-b-to-tool.y {self._float_value('cal_b_to_tool_y'):.6f}",
            f"setp headheadkins.cal-b-to-tool.z {self._float_value('cal_b_to_tool_z'):.6f}",
            f"setp headheadtwp.cal_b_to_tool_x {self._float_value('cal_b_to_tool_x'):.6f}",
            f"setp headheadtwp.cal_b_to_tool_y {self._float_value('cal_b_to_tool_y'):.6f}",
            f"setp headheadtwp.cal_b_to_tool_z {self._float_value('cal_b_to_tool_z'):.6f}",
            "",
            "# Vismach combined geometry",
            f"setp headheadvismach.b_zero_offset {self._float_value('b_zero_offset'):.6f}",
            f"setp headheadvismach.c_zero_offset {self._float_value('c_zero_offset'):.6f}",
            f"setp headheadvismach.c_to_b_x {self.baseline['c_to_b']['x'] + self._float_value('cal_c_to_b_x'):.6f}",
            f"setp headheadvismach.c_to_b_y {self.baseline['c_to_b']['y'] + self._float_value('cal_c_to_b_y'):.6f}",
            f"setp headheadvismach.c_to_b_z {self.baseline['c_to_b']['z'] + self._float_value('cal_c_to_b_z'):.6f}",
            f"setp headheadvismach.b_to_tool_x {self.baseline['b_to_tool']['x'] + self._float_value('cal_b_to_tool_x'):.6f}",
            f"setp headheadvismach.b_to_tool_y {self.baseline['b_to_tool']['y'] + self._float_value('cal_b_to_tool_y'):.6f}",
            f"setp headheadvismach.b_to_tool_z {self.baseline['b_to_tool']['z'] + self._float_value('cal_b_to_tool_z'):.6f}",
            "",
            "# Notes",
        ]
        for key, edit in self.note_fields.items():
            text = edit.toPlainText().strip()
            if text:
                lines.append(f"[{key}]")
                lines.extend(text.splitlines())
                lines.append("")
        self.generated_preview.setPlainText("\n".join(lines).rstrip() + "\n")

    def _copy_summary(self):
        QApplication.clipboard().setText(self.generated_preview.toPlainText())
        self._set_status("Calibration summary copied to clipboard.")

    def _metadata_value(self, key, default=""):
        field = self.metadata_fields.get(key)
        if field is None:
            return default
        text = field.text().strip()
        return text if text else default

    def _save_draft(self):
        data = {
            "offsets": {key: field.text() for key, field in self.offset_fields.items()},
            "metadata": {key: field.text() for key, field in self.metadata_fields.items()},
            "captures": {key: field.text() for key, field in self.capture_fields.items()},
            "notes": {key: edit.toPlainText() for key, edit in self.note_fields.items()},
            "step": self.step_list.currentRow(),
        }
        DRAFT_FILE.write_text(json.dumps(data, indent=2))
        self._set_status(f"Draft saved: {DRAFT_FILE.name}")

    def _load_draft(self):
        if not DRAFT_FILE.exists():
            self._update_summary()
            return
        try:
            data = json.loads(DRAFT_FILE.read_text())
        except json.JSONDecodeError:
            self._update_summary()
            return

        for key, value in data.get("offsets", {}).items():
            if key in self.offset_fields:
                self.offset_fields[key].setText(str(value))

        for key, value in data.get("metadata", {}).items():
            if key in self.metadata_fields:
                self.metadata_fields[key].setText(str(value))

        for key, value in data.get("captures", {}).items():
            if key in self.capture_fields:
                self.capture_fields[key].setText(str(value))

        for key, value in data.get("notes", {}).items():
            if key in self.note_fields:
                self.note_fields[key].setPlainText(value)

        step = data.get("step", 0)
        if 0 <= step < self.step_list.count():
            self.step_list.setCurrentRow(step)
        self._update_summary()
        self._set_status(f"Draft loaded: {DRAFT_FILE.name}")

    def _live_value(self, pin_name, default=0.0):
        try:
            return float(hal.get_value(pin_name))
        except Exception:
            return default

    def _set_status(self, text, error=False):
        if self.status_banner is None:
            return
        color = "#ffb0b0" if error else "#d8f0ff"
        self.status_banner.setStyleSheet(f"font-size: 12px; color: {color};")
        self.status_banner.setText(text)

    def _capture_current_position(self, prefix, expected_b, expected_c):
        try:
            self.status.poll()
            actual = self.status.actual_position
            x, y, z = actual[0], actual[1], actual[2]
            b, c = actual[3], actual[4]
            self.capture_fields[f"{prefix}_x"].setText(f"{x:.6f}")
            self.capture_fields[f"{prefix}_y"].setText(f"{y:.6f}")
            self.capture_fields[f"{prefix}_z"].setText(f"{z:.6f}")
            self.capture_fields[f"{prefix}_b"].setText(f"{b:.6f}")
            self.capture_fields[f"{prefix}_c"].setText(f"{c:.6f}")
            self._set_status(
                f"Captured current XYZBC for {prefix}: expected B/C {expected_b:.1f}/{expected_c:.1f}, actual {b:.3f}/{c:.3f}"
            )
        except Exception as exc:
            self._set_status(f"Capture failed: {exc}", error=True)
            QMessageBox.warning(self, "Capture failed", str(exc))

    def _load_live_hal(self):
        mapping = {
            "b_zero_offset": "headheadkins.b-zero-offset",
            "c_zero_offset": "headheadkins.c-zero-offset",
            "cal_c_to_b_x": "headheadkins.cal-c-to-b.x",
            "cal_c_to_b_y": "headheadkins.cal-c-to-b.y",
            "cal_c_to_b_z": "headheadkins.cal-c-to-b.z",
            "cal_b_to_tool_x": "headheadkins.cal-b-to-tool.x",
            "cal_b_to_tool_y": "headheadkins.cal-b-to-tool.y",
            "cal_b_to_tool_z": "headheadkins.cal-b-to-tool.z",
        }
        for field_key, pin_name in mapping.items():
            self.offset_fields[field_key].setText(f"{self._live_value(pin_name):.6f}")
        self._update_summary()
        self._set_status("Loaded current live HAL calibration values into the wizard.")

    def _apply_pin(self, pin_name, value):
        subprocess.run(
            ["halcmd", "setp", pin_name, f"{value:.6f}"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

    def _apply_to_running_sim(self):
        try:
            b_zero = self._float_value("b_zero_offset")
            c_zero = self._float_value("c_zero_offset")
            cal_c_to_b = {
                "x": self._float_value("cal_c_to_b_x"),
                "y": self._float_value("cal_c_to_b_y"),
                "z": self._float_value("cal_c_to_b_z"),
            }
            cal_b_to_tool = {
                "x": self._float_value("cal_b_to_tool_x"),
                "y": self._float_value("cal_b_to_tool_y"),
                "z": self._float_value("cal_b_to_tool_z"),
            }

            apply_values = {
                "headheadkins.b-zero-offset": b_zero,
                "headheadkins.c-zero-offset": c_zero,
                "headheadtwp.b_zero_offset": b_zero,
                "headheadtwp.c_zero_offset": c_zero,
                "headheadvismach.b_zero_offset": b_zero,
                "headheadvismach.c_zero_offset": c_zero,
                "headheadkins.cal-c-to-b.x": cal_c_to_b["x"],
                "headheadkins.cal-c-to-b.y": cal_c_to_b["y"],
                "headheadkins.cal-c-to-b.z": cal_c_to_b["z"],
                "headheadtwp.cal_c_to_b_x": cal_c_to_b["x"],
                "headheadtwp.cal_c_to_b_y": cal_c_to_b["y"],
                "headheadtwp.cal_c_to_b_z": cal_c_to_b["z"],
                "headheadkins.cal-b-to-tool.x": cal_b_to_tool["x"],
                "headheadkins.cal-b-to-tool.y": cal_b_to_tool["y"],
                "headheadkins.cal-b-to-tool.z": cal_b_to_tool["z"],
                "headheadtwp.cal_b_to_tool_x": cal_b_to_tool["x"],
                "headheadtwp.cal_b_to_tool_y": cal_b_to_tool["y"],
                "headheadtwp.cal_b_to_tool_z": cal_b_to_tool["z"],
                "headheadvismach.c_to_b_x": self.baseline["c_to_b"]["x"] + cal_c_to_b["x"],
                "headheadvismach.c_to_b_y": self.baseline["c_to_b"]["y"] + cal_c_to_b["y"],
                "headheadvismach.c_to_b_z": self.baseline["c_to_b"]["z"] + cal_c_to_b["z"],
                "headheadvismach.b_to_tool_x": self.baseline["b_to_tool"]["x"] + cal_b_to_tool["x"],
                "headheadvismach.b_to_tool_y": self.baseline["b_to_tool"]["y"] + cal_b_to_tool["y"],
                "headheadvismach.b_to_tool_z": self.baseline["b_to_tool"]["z"] + cal_b_to_tool["z"],
            }

            for pin_name, value in apply_values.items():
                self._apply_pin(pin_name, value)

            self._set_status("Applied calibration values to the running sim HAL pins.")
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() or str(exc)
            self._set_status(f"Apply failed: {message}", error=True)
            QMessageBox.warning(self, "Apply failed", message)
