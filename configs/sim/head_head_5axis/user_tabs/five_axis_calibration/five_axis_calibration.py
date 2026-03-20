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
        self.recommendation_preview = None
        self.verify_guidance_preview = None
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

        program_row = QHBoxLayout()
        layout.addLayout(program_row)
        program_row.addWidget(self._program_button("Load B/C Align", "calibration_bc_alignment_check.ngc"))
        program_row.addWidget(self._program_button("Load B Zero", "machine_b_zero_alignment_check.ngc"))
        program_row.addWidget(self._program_button("Load C Zero", "machine_c_zero_alignment_check.ngc"))
        program_row.addWidget(self._program_button("Load Fixed-Tip TCP", "machine_tcp_fixed_tip_probe_check.ngc"))
        program_row.addWidget(self._program_button("Load TWP Check", "machine_twp_granite_square_check.ngc"))
        program_row.addStretch(1)

        checklist_box = QGroupBox("Machine bring-up checklist")
        checklist_form = QFormLayout(checklist_box)
        checklist_form.addRow("Power-up / reset", self._metadata_entry("bringup_power_reset", "pending"))
        checklist_form.addRow("Home / reference state", self._metadata_entry("bringup_home_state", "pending"))
        checklist_form.addRow("Probe qualification", self._metadata_entry("bringup_probe_state", "pending"))
        checklist_form.addRow("Sphere stand setup", self._metadata_entry("bringup_sphere_state", "pending"))
        checklist_form.addRow("B/C zeroing", self._metadata_entry("bringup_rotary_zero_state", "pending"))
        checklist_form.addRow("Sphere map captured", self._metadata_entry("bringup_sphere_map_state", "pending"))
        checklist_form.addRow("Fixed-tip TCP", self._metadata_entry("bringup_fixed_tip_state", "pending"))
        checklist_form.addRow("Moving TCP", self._metadata_entry("bringup_moving_tcp_state", "pending"))
        checklist_form.addRow("TWP granite-square check", self._metadata_entry("bringup_twp_state", "pending"))
        checklist_form.addRow("Overall machine bring-up", self._metadata_entry("bringup_overall_state", "pending"))
        layout.addWidget(checklist_box)

        layout.addWidget(self._instruction_box("Procedure", [
            "1. Power up, clear faults, and confirm the machine starts from a sane reference state.",
            "2. Clear any leftover TWP state with G69 and confirm TCPC is off unless a step explicitly enables it.",
            "3. Qualify the wireless probe before any 5-axis geometry capture.",
            "4. Place the 20 mm sphere on the tall 45 degree stand in a reachable part of travel.",
            "5. Run the B and C zero checks before trying to solve TCP drift.",
            "6. Capture the sphere map, then move into fixed-tip TCP, moving TCP, and finally the granite-square TWP check.",
            "7. Use Save Draft often while building up the calibration set.",
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

        self.recommendation_preview = QPlainTextEdit()
        self.recommendation_preview.setReadOnly(True)
        self.recommendation_preview.setMinimumHeight(170)
        layout.addWidget(self.recommendation_preview)

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
            "Use the direct-output rotary encoders, the granite square, and the mounted sphere setup to establish "
            "believable B0/C0 first, then refine the angular zero corrections from repeatable checks.",
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
        pose_row.addWidget(self._program_button("Load B Zero Check", "machine_b_zero_alignment_check.ngc"))
        pose_row.addWidget(self._program_button("Load C Zero Check", "machine_c_zero_alignment_check.ngc"))
        pose_row.addStretch(1)

        zero_box = QGroupBox("Rotary zeroing log")
        zero_form = QFormLayout(zero_box)
        zero_form.addRow("B zero reference", self._metadata_entry("b_zero_reference", "granite square"))
        zero_form.addRow("B zero observed error", self._metadata_entry("b_zero_observed_error", ""))
        zero_form.addRow("C zero reference", self._metadata_entry("c_zero_reference", "machine-forward reference"))
        zero_form.addRow("C zero observed error", self._metadata_entry("c_zero_observed_error", ""))
        zero_form.addRow("Zeroing pass result", self._metadata_entry("rotary_zero_pass_result", "pending"))
        layout.addWidget(zero_box)

        layout.addWidget(self._instruction_box("How to measure", [
            "1. Run the dedicated B zero and C zero alignment programs before trying to solve TCP drift.",
            "2. Because the encoders are mounted directly on the gearbox output, zero the rotary reference first and trust the feedback after that.",
            "3. Use the granite square as the primary B0 reference and a clear spindle-facing machine reference for C0.",
            "4. After B0/C0 are believable, use the sphere capture map to trim the remaining paired B and C drift symmetry.",
            "5. Re-check at B45/C90 or another reachable mixed pose to confirm the chosen sign convention still helps.",
            "6. Enter only the extra rotary correction needed beyond the nominal zero model.",
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
            "Run the real-machine verification path first: fixed-tip TCP, moving TCP, then the granite-square "
            "TWP check. The older sim/reference programs stay available here as secondary debug tools only.",
        )

        machine_box = QGroupBox("Machine verification workflow")
        machine_grid = QGridLayout(machine_box)
        machine_grid.addWidget(self._program_button("1. Load Machine Fixed-Tip", "machine_tcp_fixed_tip_probe_check.ngc"), 0, 0)
        machine_grid.addWidget(self._program_button("2. Load Machine Moving TCP", "machine_tcp_motion_probe_check.ngc"), 0, 1)
        machine_grid.addWidget(self._program_button("3. Load Machine TWP Check", "machine_twp_granite_square_check.ngc"), 1, 0)
        machine_grid.addWidget(self._mdi_button("Enable TCPC", "G43.4"), 1, 1)
        machine_grid.addWidget(self._mdi_button("Cancel TWP", "G69"), 2, 0)
        machine_grid.addWidget(self._mdi_button("Disable TCPC", "G49.1"), 2, 1)
        machine_grid.addWidget(self._mdi_button("Tilt Pose", "G0 X1500 Y850 Z-600 B45 C90"), 3, 0)
        layout.addWidget(machine_box)

        reference_box = QGroupBox("Reference and sim tools")
        reference_grid = QGridLayout(reference_box)
        reference_grid.addWidget(self._program_button("Load B/C Alignment", "calibration_bc_alignment_check.ngc"), 0, 0)
        reference_grid.addWidget(self._program_button("Load Fixed-Tip TCPC", "calibration_tcpc_fixed_tip_check.ngc"), 0, 1)
        reference_grid.addWidget(self._program_button("Load Moving TCPC", "calibration_tcpc_motion_check.ngc"), 1, 0)
        reference_grid.addWidget(self._program_button("Load TWP Demo", "twp_g68_2_fresh_demo.ngc"), 1, 1)
        layout.addWidget(reference_box)

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

        fixed_tip_box = QGroupBox("Fixed-tip TCP pose log")
        fixed_tip_form = QFormLayout(fixed_tip_box)
        fixed_tip_form.addRow("B0 C0 entry", self._metadata_entry("verify_fixed_tip_pose_b0_c0_entry", "pending"))
        fixed_tip_form.addRow("B20 C0", self._metadata_entry("verify_fixed_tip_pose_b20_c0", "pending"))
        fixed_tip_form.addRow("B45 C0", self._metadata_entry("verify_fixed_tip_pose_b45_c0", "pending"))
        fixed_tip_form.addRow("B45 C90", self._metadata_entry("verify_fixed_tip_pose_b45_c90", "pending"))
        fixed_tip_form.addRow("B0 C180", self._metadata_entry("verify_fixed_tip_pose_b0_c180", "pending"))
        fixed_tip_form.addRow("B-30 C-90", self._metadata_entry("verify_fixed_tip_pose_bneg30_cneg90", "pending"))
        fixed_tip_form.addRow("Return B0 C0", self._metadata_entry("verify_fixed_tip_pose_return_b0_c0", "pending"))
        fixed_tip_form.addRow(self._pose_group_button_row("fixed_tip"))
        layout.addWidget(fixed_tip_box)

        moving_box = QGroupBox("Moving TCP pose log")
        moving_form = QFormLayout(moving_box)
        moving_form.addRow("Start clear pose", self._metadata_entry("verify_moving_pose_start", "pending"))
        moving_form.addRow("X1550 Y850 Z-600 B20 C0", self._metadata_entry("verify_moving_pose_x1550_y850_z600_b20_c0", "pending"))
        moving_form.addRow("X1600 Y950 Z-600 B20 C90", self._metadata_entry("verify_moving_pose_x1600_y950_z600_b20_c90", "pending"))
        moving_form.addRow("X1500 Y1000 Z-560 B0 C90", self._metadata_entry("verify_moving_pose_x1500_y1000_z560_b0_c90", "pending"))
        moving_form.addRow("X1450 Y900 Z-580 B-30 C180", self._metadata_entry("verify_moving_pose_x1450_y900_z580_bneg30_c180", "pending"))
        moving_form.addRow("Return start pose", self._metadata_entry("verify_moving_pose_return_start", "pending"))
        moving_form.addRow(self._pose_group_button_row("moving_tcp"))
        layout.addWidget(moving_box)

        twp_box = QGroupBox("TWP pose log")
        twp_form = QFormLayout(twp_box)
        twp_form.addRow("Tilted start pose", self._metadata_entry("verify_twp_pose_start", "pending"))
        twp_form.addRow("Local +U", self._metadata_entry("verify_twp_pose_u_plus", "pending"))
        twp_form.addRow("Local +V", self._metadata_entry("verify_twp_pose_v_plus", "pending"))
        twp_form.addRow("Local +W", self._metadata_entry("verify_twp_pose_w_plus", "pending"))
        twp_form.addRow("Return local origin", self._metadata_entry("verify_twp_pose_return_origin", "pending"))
        twp_form.addRow(self._pose_group_button_row("twp"))
        layout.addWidget(twp_box)

        self.verify_guidance_preview = QPlainTextEdit()
        self.verify_guidance_preview.setReadOnly(True)
        self.verify_guidance_preview.setMinimumHeight(190)
        layout.addWidget(self.verify_guidance_preview)

        recheck_row = QHBoxLayout()
        layout.addLayout(recheck_row)
        load_recheck_button = QPushButton("Load Suggested Re-check")
        load_recheck_button.clicked.connect(self._load_suggested_recheck)
        recheck_row.addWidget(load_recheck_button)
        go_recheck_button = QPushButton("Go To Suggested Pose")
        go_recheck_button.clicked.connect(self._go_to_suggested_recheck_pose)
        recheck_row.addWidget(go_recheck_button)
        recheck_row.addStretch(1)

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

    def _pose_group_button_row(self, group_name):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        for label, value in (
            ("Mark Pending", "pending"),
            ("Mark Pass", "pass"),
            ("Mark Hold", "hold"),
            ("Mark Fail", "fail"),
        ):
            button = QPushButton(label)
            button.clicked.connect(
                lambda _checked=False, group=group_name, status=value: self._set_pose_group_status(group, status)
            )
            layout.addWidget(button)
        layout.addStretch(1)
        return row

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

    def _issue_mdi_sequence(self, commands):
        try:
            self.command.mode(linuxcnc.MODE_MDI)
            self.command.wait_complete()
            for command in commands:
                self.command.mdi(command)
                self.command.wait_complete()
            if commands:
                self._set_status(f"MDI sequence sent: {commands[-1]}")
        except linuxcnc.error as exc:
            self._set_status(f"MDI sequence error: {exc}", error=True)
            QMessageBox.warning(self, "MDI sequence error", str(exc))

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

    def _vec_mag(self, vec):
        return (vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2) ** 0.5

    def _vec_sub(self, a, b):
        return (
            a[0] - b[0],
            a[1] - b[1],
            a[2] - b[2],
        )

    def _vec_avg(self, a, b):
        return (
            (a[0] + b[0]) / 2.0,
            (a[1] + b[1]) / 2.0,
            (a[2] + b[2]) / 2.0,
        )

    def _vec_half_diff(self, a, b):
        return (
            (a[0] - b[0]) / 2.0,
            (a[1] - b[1]) / 2.0,
            (a[2] - b[2]) / 2.0,
        )

    def _capture_ready(self):
        required = ("ref_x", "ref_y", "ref_z", "b_pos_x", "b_neg_x", "c_pos_x", "c_neg_x")
        return all(self.capture_fields[key].text().strip() for key in required)

    def _rotate_y(self, angle_deg, vec):
        angle = math.radians(angle_deg)
        c = math.cos(angle)
        s = math.sin(angle)
        x, y, z = vec
        return (
            c * x + s * z,
            y,
            -s * x + c * z,
        )

    def _rotate_z(self, angle_deg, vec):
        angle = math.radians(angle_deg)
        c = math.cos(angle)
        s = math.sin(angle)
        x, y, z = vec
        return (
            c * x - s * y,
            s * x + c * y,
            z,
        )

    def _capture_pose_targets(self):
        return {
            "b_pos": (45.0, 0.0),
            "b_neg": (-45.0, 0.0),
            "c_pos": (0.0, 90.0),
            "c_neg": (0.0, -90.0),
            "bc_mix": (45.0, 90.0),
        }

    def _current_model_params(self):
        return {
            "c_to_b": (
                self.baseline["c_to_b"]["x"] + self._float_value("cal_c_to_b_x"),
                self.baseline["c_to_b"]["y"] + self._float_value("cal_c_to_b_y"),
                self.baseline["c_to_b"]["z"] + self._float_value("cal_c_to_b_z"),
            ),
            "b_to_tool": (
                self.baseline["b_to_tool"]["x"] + self._float_value("cal_b_to_tool_x"),
                self.baseline["b_to_tool"]["y"] + self._float_value("cal_b_to_tool_y"),
                self.baseline["b_to_tool"]["z"] + self._float_value("cal_b_to_tool_z"),
            ),
            "b_zero": self._float_value("b_zero_offset"),
            "c_zero": self._float_value("c_zero_offset"),
        }

    def _tool_offset_world(self, params, b_cmd, c_cmd):
        b_eff = b_cmd + params["b_zero"]
        c_eff = c_cmd + params["c_zero"]
        b_rotated = self._rotate_y(b_eff, params["b_to_tool"])
        c_frame = (
            params["c_to_b"][0] + b_rotated[0],
            params["c_to_b"][1] + b_rotated[1],
            params["c_to_b"][2] + b_rotated[2],
        )
        return self._rotate_z(c_eff, c_frame)

    def _predicted_capture_deltas(self, params):
        ref_offset = self._tool_offset_world(params, 0.0, 0.0)
        predicted = {}
        for prefix, (b_deg, c_deg) in self._capture_pose_targets().items():
            pose_offset = self._tool_offset_world(params, b_deg, c_deg)
            predicted[prefix] = self._vec_sub(ref_offset, pose_offset)
        return predicted

    def _measured_capture_deltas(self):
        return {
            "b_pos": self._capture_delta("b_pos"),
            "b_neg": self._capture_delta("b_neg"),
            "c_pos": self._capture_delta("c_pos"),
            "c_neg": self._capture_delta("c_neg"),
            "bc_mix": self._capture_delta("bc_mix"),
        }

    def _residual_score(self, params):
        measured = self._measured_capture_deltas()
        predicted = self._predicted_capture_deltas(params)
        total = 0.0
        for key, measured_vec in measured.items():
            residual = self._vec_sub(measured_vec, predicted[key])
            total += self._vec_mag(residual) ** 2
        return total ** 0.5

    def _trial_hint(self, ranked_name):
        params = self._current_model_params()
        base_score = self._residual_score(params)

        if ranked_name == "B_ZERO_OFFSET":
            trials = [(-0.1, "negative"), (0.1, "positive")]
            best = None
            for delta, label in trials:
                trial = dict(params)
                trial["b_zero"] = params["b_zero"] + delta
                score = self._residual_score(trial)
                if best is None or score < best[0]:
                    best = (score, delta, label)
            if best and best[0] < base_score:
                return f"Suggested first trial: {best[2]} B zero change (~{best[1]:+.3f} deg), then re-check B+/B-."
            return "Suggested first trial: B zero bucket is dominant, but the sign is still ambiguous. Try a very small change and re-capture B+/B-."

        if ranked_name == "C_ZERO_OFFSET":
            trials = [(-0.1, "negative"), (0.1, "positive")]
            best = None
            for delta, label in trials:
                trial = dict(params)
                trial["c_zero"] = params["c_zero"] + delta
                score = self._residual_score(trial)
                if best is None or score < best[0]:
                    best = (score, delta, label)
            if best and best[0] < base_score:
                return f"Suggested first trial: {best[2]} C zero change (~{best[1]:+.3f} deg), then re-check C+/C-."
            return "Suggested first trial: C zero bucket is dominant, but the sign is still ambiguous. Try a very small change and re-capture C+/C-."

        if ranked_name in ("cal-c-to-b", "cal-b-to-tool"):
            field = "c_to_b" if ranked_name == "cal-c-to-b" else "b_to_tool"
            best = None
            for axis_index, axis_name in enumerate(("x", "y", "z")):
                for delta, label in ((-0.1, "negative"), (0.1, "positive")):
                    trial = {
                        "c_to_b": list(params["c_to_b"]),
                        "b_to_tool": list(params["b_to_tool"]),
                        "b_zero": params["b_zero"],
                        "c_zero": params["c_zero"],
                    }
                    trial[field][axis_index] += delta
                    trial["c_to_b"] = tuple(trial["c_to_b"])
                    trial["b_to_tool"] = tuple(trial["b_to_tool"])
                    score = self._residual_score(trial)
                    if best is None or score < best[0]:
                        best = (score, axis_name, delta, label)
            if best and best[0] < base_score:
                return (
                    f"Suggested first trial: {best[3]} {ranked_name}.{best[1]} change "
                    f"(~{best[2]:+.3f} mm), then re-capture the sphere map."
                )
            return f"Suggested first trial: {ranked_name} looks dominant, but no clean sign stands out yet. Try a very small single-axis change and re-capture."

        return ""

    def _recommendation_lines(self):
        if not self._capture_ready():
            return [
                "Recommended next adjustment",
                "",
                "Capture at least the reference, B plus/B minus, and C plus/C minus sphere centers",
                "before using the solve assistant.",
            ]

        b_pos = self._capture_delta("b_pos")
        b_neg = self._capture_delta("b_neg")
        c_pos = self._capture_delta("c_pos")
        c_neg = self._capture_delta("c_neg")
        bc_mix = self._capture_delta("bc_mix")

        b_common = self._vec_avg(b_pos, b_neg)
        b_antisym = self._vec_half_diff(b_pos, b_neg)
        c_common = self._vec_avg(c_pos, c_neg)
        c_antisym = self._vec_half_diff(c_pos, c_neg)
        global_common = self._vec_avg(b_common, c_common)

        b_zero_score = self._vec_mag(b_antisym)
        c_zero_score = self._vec_mag(c_antisym)
        c_to_b_score = self._vec_mag(c_common)
        b_to_tool_score = max(self._vec_mag(b_common), self._vec_mag(bc_mix))

        ranked = [
            ("B_ZERO_OFFSET", b_zero_score, "B plus/B minus drift flips around zero and is larger than the C pair."),
            ("C_ZERO_OFFSET", c_zero_score, "C plus/C minus drift flips around zero and is larger than the B pair."),
            ("cal-c-to-b", c_to_b_score, "C-related poses share a common residual after the paired zero error is separated."),
            ("cal-b-to-tool", b_to_tool_score, "B-related and mixed poses keep a common residual after zero is separated."),
        ]
        ranked.sort(key=lambda item: item[1], reverse=True)

        lines = [
            "Recommended next adjustment",
            "",
            f"1. {ranked[0][0]}",
            f"   Reason: {ranked[0][2]}",
            f"   Score: {ranked[0][1]:.3f} mm",
            f"   {self._trial_hint(ranked[0][0])}",
            "",
            "Supporting drift summary",
            f"- B paired antisymmetric drift: {self._format_vec(b_antisym)} |mag|={b_zero_score:.3f}",
            f"- C paired antisymmetric drift: {self._format_vec(c_antisym)} |mag|={c_zero_score:.3f}",
            f"- B common residual: {self._format_vec(b_common)} |mag|={self._vec_mag(b_common):.3f}",
            f"- C common residual: {self._format_vec(c_common)} |mag|={self._vec_mag(c_common):.3f}",
            f"- Mixed BC residual: {self._format_vec(bc_mix)} |mag|={self._vec_mag(bc_mix):.3f}",
            f"- Overall common residual: {self._format_vec(global_common)} |mag|={self._vec_mag(global_common):.3f}",
        ]

        if ranked[0][1] < 0.01:
            lines.extend([
                "",
                "No dominant error is visible yet. Re-check repeatability before changing offsets.",
            ])
        else:
            runner_up = ranked[1]
            lines.extend([
                "",
                f"Second look if the first change does not help: {runner_up[0]}",
                f"Reason: {runner_up[2]}",
            ])
        return lines

    def _dominant_adjustment_name(self):
        for line in self._recommendation_lines():
            if line.startswith("1. "):
                return line[3:].strip()
        return ""

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
        if self.recommendation_preview is not None:
            self.recommendation_preview.setPlainText("\n".join(self._recommendation_lines()))
        if self.verify_guidance_preview is not None:
            self.verify_guidance_preview.setPlainText("\n".join(self._verify_guidance_lines()))

    def _status_bucket(self, key):
        return self._metadata_value(key, "pending").strip().lower()

    def _first_flagged_pose(self, pose_keys):
        for label, key in pose_keys:
            if self._status_bucket(key) in ("fail", "hold"):
                return label
        return ""

    def _pose_status_line(self, pose_keys):
        parts = []
        for label, key in pose_keys:
            parts.append(f"{label}={self._metadata_value(key, 'pending')}")
        return ", ".join(parts)

    def _set_pose_group_status(self, group_name, status):
        pose_group = self._verify_pose_groups().get(group_name, [])
        for _label, key in pose_group:
            field = self.metadata_fields.get(key)
            if field is not None:
                field.setText(status)
        self._set_status(f"Set {group_name} pose states to {status}.")

    def _verify_pose_groups(self):
        return {
            "fixed_tip": [
                ("B0/C0 entry", "verify_fixed_tip_pose_b0_c0_entry"),
                ("B20/C0", "verify_fixed_tip_pose_b20_c0"),
                ("B45/C0", "verify_fixed_tip_pose_b45_c0"),
                ("B45/C90", "verify_fixed_tip_pose_b45_c90"),
                ("B0/C180", "verify_fixed_tip_pose_b0_c180"),
                ("B-30/C-90", "verify_fixed_tip_pose_bneg30_cneg90"),
                ("Return B0/C0", "verify_fixed_tip_pose_return_b0_c0"),
            ],
            "moving_tcp": [
                ("Start", "verify_moving_pose_start"),
                ("X1550 Y850 Z-600 B20 C0", "verify_moving_pose_x1550_y850_z600_b20_c0"),
                ("X1600 Y950 Z-600 B20 C90", "verify_moving_pose_x1600_y950_z600_b20_c90"),
                ("X1500 Y1000 Z-560 B0 C90", "verify_moving_pose_x1500_y1000_z560_b0_c90"),
                ("X1450 Y900 Z-580 B-30 C180", "verify_moving_pose_x1450_y900_z580_bneg30_c180"),
                ("Return start", "verify_moving_pose_return_start"),
            ],
            "twp": [
                ("Tilted start", "verify_twp_pose_start"),
                ("Local +U", "verify_twp_pose_u_plus"),
                ("Local +V", "verify_twp_pose_v_plus"),
                ("Local +W", "verify_twp_pose_w_plus"),
                ("Return origin", "verify_twp_pose_return_origin"),
            ],
        }

    def _pose_focus_lines(self):
        pose_groups = self._verify_pose_groups()
        fixed_tip_pose = self._first_flagged_pose(pose_groups["fixed_tip"])
        moving_pose = self._first_flagged_pose(pose_groups["moving_tcp"])
        twp_pose = self._first_flagged_pose(pose_groups["twp"])

        if fixed_tip_pose in ("B20/C0", "B45/C0"):
            return [
                "Pose-based follow-up",
                "",
                f"First fixed-tip issue appears at {fixed_tip_pose}.",
                "This is still a B-dominant pose. Check B zero first, then re-check B-related sphere-map drift before changing mixed geometry.",
            ]

        if fixed_tip_pose in ("B45/C90", "B0/C180", "B-30/C-90"):
            return [
                "Pose-based follow-up",
                "",
                f"First fixed-tip issue appears at {fixed_tip_pose}.",
                "This is already a C or mixed rotary pose. Check C zero and the C-related common residual before moving on to B-to-tool changes.",
            ]

        if fixed_tip_pose == "Return B0/C0":
            return [
                "Pose-based follow-up",
                "",
                "The first fixed-tip issue is the return to B0/C0.",
                "Check repeatability first: probe qualification, rotary return consistency, and whether the sphere setup moved during the test.",
            ]

        if moving_pose == "X1550 Y850 Z-600 B20 C0":
            return [
                "Pose-based follow-up",
                "",
                "The first moving-TCP issue appears on the first B-dominant move.",
                "Check B-to-tool and B-related zero/geometry before chasing the later C-heavy poses.",
            ]

        if moving_pose in ("X1600 Y950 Z-600 B20 C90", "X1500 Y1000 Z-560 B0 C90"):
            return [
                "Pose-based follow-up",
                "",
                f"The first moving-TCP issue appears at {moving_pose}.",
                "That is a C-heavy move. Check C zero and C-to-B geometry before changing the B-to-tool offset again.",
            ]

        if moving_pose == "X1450 Y900 Z-580 B-30 C180":
            return [
                "Pose-based follow-up",
                "",
                "The first moving-TCP issue appears on the mixed negative pose.",
                "Check the common geometry terms next, especially C-to-B first, then confirm the B-to-tool correction still helps across mixed poses.",
            ]

        if moving_pose == "Return start":
            return [
                "Pose-based follow-up",
                "",
                "The path looked acceptable until the return-to-start check.",
                "Check repeatability and whether the zero/reference state is drifting between passes before making a larger geometry change.",
            ]

        if twp_pose == "Local +U":
            return [
                "Pose-based follow-up",
                "",
                "The first TWP issue appears on local +U.",
                "Check the entry B/C pose and confirm the active TWP definition matches the intended stored plane before changing plane-normal assumptions.",
            ]

        if twp_pose == "Local +V":
            return [
                "Pose-based follow-up",
                "",
                "The first TWP issue appears on local +V.",
                "That usually points to plane-orientation trouble rather than pure TCP length. Re-check the chosen B/C pose and C-related alignment first.",
            ]

        if twp_pose == "Local +W":
            return [
                "Pose-based follow-up",
                "",
                "The first TWP issue appears on local +W.",
                "That is the plane-normal move. Re-check TCP credibility first, then confirm the tilted-plane normal is being established from the intended pose.",
            ]

        if twp_pose == "Return origin":
            return [
                "Pose-based follow-up",
                "",
                "The TWP path looks acceptable until the return-to-origin check.",
                "Check local-origin setup and whether the stored plane is being canceled and re-entered consistently.",
            ]

        return [
            "Pose-based follow-up",
            "",
            "No pose-specific issue is marked yet.",
            "Use the first failed pose fields if you want the wizard to narrow the next adjustment further.",
        ]

    def _preferred_recheck_pose(self, adjustment_name):
        pose_groups = self._verify_pose_groups()
        fixed_tip_pose = self._first_flagged_pose(pose_groups["fixed_tip"])
        moving_pose = self._first_flagged_pose(pose_groups["moving_tcp"])
        twp_pose = self._first_flagged_pose(pose_groups["twp"])

        if fixed_tip_pose:
            return fixed_tip_pose
        if moving_pose:
            return moving_pose
        if twp_pose:
            return twp_pose

        defaults = {
            "B_ZERO_OFFSET": "B45/C0",
            "C_ZERO_OFFSET": "B45/C90",
            "cal-c-to-b": "X1600 Y950 Z-600 B20 C90",
            "cal-b-to-tool": "X1550 Y850 Z-600 B20 C0",
        }
        return defaults.get(adjustment_name, "")

    def _suggested_recheck_program_filename(self):
        pose_groups = self._verify_pose_groups()
        fixed_tip_pose = self._first_flagged_pose(pose_groups["fixed_tip"])
        moving_pose = self._first_flagged_pose(pose_groups["moving_tcp"])
        twp_pose = self._first_flagged_pose(pose_groups["twp"])
        dominant = self._dominant_adjustment_name()

        if twp_pose:
            return "machine_twp_granite_square_check.ngc"
        if moving_pose:
            return "machine_tcp_motion_probe_check.ngc"
        if fixed_tip_pose:
            return "machine_tcp_fixed_tip_probe_check.ngc"

        defaults = {
            "B_ZERO_OFFSET": "machine_tcp_fixed_tip_probe_check.ngc",
            "C_ZERO_OFFSET": "machine_tcp_fixed_tip_probe_check.ngc",
            "cal-c-to-b": "machine_tcp_motion_probe_check.ngc",
            "cal-b-to-tool": "machine_tcp_motion_probe_check.ngc",
        }
        return defaults.get(dominant, "")

    def _suggested_recheck_sequence(self):
        pose = self._preferred_recheck_pose(self._dominant_adjustment_name())
        fixed_tip_targets = {
            "B0/C0 entry": "G1 X1500.000 Y850.000 Z-600.000 B0.000 C0.000",
            "B20/C0": "G1 X1500.000 Y850.000 Z-600.000 B20.000 C0.000",
            "B45/C0": "G1 X1500.000 Y850.000 Z-600.000 B45.000 C0.000",
            "B45/C90": "G1 X1500.000 Y850.000 Z-600.000 B45.000 C90.000",
            "B0/C180": "G1 X1500.000 Y850.000 Z-600.000 B0.000 C180.000",
            "B-30/C-90": "G1 X1500.000 Y850.000 Z-600.000 B-30.000 C-90.000",
            "Return B0/C0": "G1 X1500.000 Y850.000 Z-600.000 B0.000 C0.000",
        }
        moving_targets = {
            "Start": "G1 X1500.000 Y850.000 Z-600.000 B0.000 C0.000",
            "X1550 Y850 Z-600 B20 C0": "G1 X1550.000 Y850.000 Z-600.000 B20.000 C0.000",
            "X1600 Y950 Z-600 B20 C90": "G1 X1600.000 Y950.000 Z-600.000 B20.000 C90.000",
            "X1500 Y1000 Z-560 B0 C90": "G1 X1500.000 Y1000.000 Z-560.000 B0.000 C90.000",
            "X1450 Y900 Z-580 B-30 C180": "G1 X1450.000 Y900.000 Z-580.000 B-30.000 C180.000",
            "Return start": "G1 X1500.000 Y850.000 Z-600.000 B0.000 C0.000",
        }
        twp_targets = {
            "Tilted start": ["G0 X1500.000 Y850.000 Z-600.000 B45.000 C90.000"],
            "Local +U": ["G0 X1500.000 Y850.000 Z-600.000 B45.000 C90.000", "G68.2 B45.0 C90.0", "G0 X100.0 Y0.0 Z0.0"],
            "Local +V": ["G0 X1500.000 Y850.000 Z-600.000 B45.000 C90.000", "G68.2 B45.0 C90.0", "G1 X100.0 Y120.0 Z0.0"],
            "Local +W": ["G0 X1500.000 Y850.000 Z-600.000 B45.000 C90.000", "G68.2 B45.0 C90.0", "G1 X100.0 Y120.0 Z40.0"],
            "Return origin": ["G0 X1500.000 Y850.000 Z-600.000 B45.000 C90.000", "G68.2 B45.0 C90.0", "G1 X0.0 Y0.0 Z0.0"],
        }

        if pose in fixed_tip_targets:
            return ["G69", "G43.4", "G94 F1200", fixed_tip_targets[pose]]
        if pose in moving_targets:
            return ["G69", "G43.4", "G94 F1200", moving_targets[pose]]
        if pose in twp_targets:
            return ["G69", "G43.4", "G94 F1200", *twp_targets[pose]]
        return []

    def _load_suggested_recheck(self):
        filename = self._suggested_recheck_program_filename()
        if not filename:
            self._set_status("No suggested re-check program is available yet.", error=True)
            return
        self._load_program(str(CONFIG_DIR / filename))

    def _go_to_suggested_recheck_pose(self):
        commands = self._suggested_recheck_sequence()
        if not commands:
            self._set_status("No suggested re-check pose is available yet.", error=True)
            return
        self._issue_mdi_sequence(commands)

    def _trial_change_plan_lines(self):
        dominant = self._dominant_adjustment_name()
        if not dominant:
            return [
                "Trial change plan",
                "",
                "Capture the sphere map first so the wizard can propose a controlled first trial.",
            ]

        recheck_pose = self._preferred_recheck_pose(dominant)
        lines = [
            "Trial change plan",
            "",
            self._trial_hint(dominant),
        ]

        if recheck_pose:
            lines.append(f"Re-run first: {recheck_pose}")
        else:
            lines.append("Re-run first: the earliest pose that showed drift in the current test.")

        if dominant in ("B_ZERO_OFFSET", "C_ZERO_OFFSET"):
            lines.append("If that pose improves, re-run the paired fixed-tip checks before touching geometry corrections.")
        elif dominant == "cal-c-to-b":
            lines.append("If that pose improves, re-run the C-heavy moving-TCP or mixed fixed-tip poses before changing B-to-tool.")
        elif dominant == "cal-b-to-tool":
            lines.append("If that pose improves, re-run the early B-dominant moving-TCP pose and then the fixed-tip B checks.")

        lines.append("If it gets worse, revert the trial change and move to the runner-up adjustment from the sphere-map recommendation.")
        return lines

    def _verify_guidance_lines(self):
        fixed_tip = self._status_bucket("verify_fixed_tip_result")
        moving_tcp = self._status_bucket("verify_moving_tcp_result")
        twp = self._status_bucket("verify_twp_result")
        rotary = self._status_bucket("bringup_rotary_zero_state")
        sphere_map = self._status_bucket("bringup_sphere_map_state")
        overall = self._status_bucket("bringup_overall_state")

        lines = [
            "Bring-up recovery guidance",
            "",
        ]

        if fixed_tip in ("fail", "hold"):
            lines.extend([
                "Fixed-tip TCP is not yet believable.",
                "Return first to: Rotary Zero and Sphere Map.",
                "Check order: B/C zero reference -> paired B/C drift -> small zero change -> re-run fixed-tip TCP.",
            ])
            lines.extend(["", *self._pose_focus_lines()[2:]])
            lines.extend(["", *self._trial_change_plan_lines()[2:]])
            return lines

        if moving_tcp in ("fail", "hold"):
            lines.extend([
                "Fixed-tip TCP passed, but moving TCP is not stable yet.",
                "Return first to: B To Tool and C To B.",
                "Check order: look for common residual in the sphere map -> apply a small geometry correction -> re-run moving TCP.",
            ])
            lines.extend(["", *self._pose_focus_lines()[2:]])
            lines.extend(["", *self._trial_change_plan_lines()[2:]])
            return lines

        if twp in ("fail", "hold"):
            lines.extend([
                "TCP looks usable, but the TWP plane check is not yet believable.",
                "Return first to: verify the granite-square setup, then re-check fixed-tip TCP before changing TWP assumptions.",
                "If TCP is clean and TWP still looks wrong, review the active B/C pose and local plane definition path.",
            ])
            lines.extend(["", *self._pose_focus_lines()[2:]])
            lines.extend(["", *self._trial_change_plan_lines()[2:]])
            return lines

        if rotary in ("fail", "hold"):
            lines.extend([
                "The first blocker is still rotary zero alignment.",
                "Return first to: the B and C zero check programs and the Rotary Zero page.",
            ])
            return lines

        if sphere_map in ("fail", "hold"):
            lines.extend([
                "Capture quality is still the next blocker.",
                "Return first to: Probe Qual and Sphere Map.",
                "Do not adjust offsets until the sphere map repeats cleanly.",
            ])
            return lines

        if overall == "pass" or (fixed_tip == "pass" and moving_tcp == "pass" and twp == "pass"):
            lines.extend([
                "Current bring-up state looks good.",
                "Next step: keep the summary as the machine record and repeat the same sequence after any mechanical change.",
            ])
            return lines

        lines.extend([
            "No failed stage is marked yet.",
            "Recommended path: Rotary Zero -> Sphere Map -> Fixed-tip TCP -> Moving TCP -> TWP check.",
        ])
        lines.extend(["", *self._pose_focus_lines()[2:]])
        lines.extend(["", *self._trial_change_plan_lines()[2:]])
        return lines

    def _update_summary(self):
        if self.generated_preview is None:
            return
        self._update_capture_preview()
        pose_groups = self._verify_pose_groups()
        fixed_tip_first = self._metadata_value(
            "verify_fixed_tip_first_drift_pose",
            self._first_flagged_pose(pose_groups["fixed_tip"]),
        )
        moving_first = self._metadata_value(
            "verify_moving_tcp_first_drift_pose",
            self._first_flagged_pose(pose_groups["moving_tcp"]),
        )
        twp_first = self._metadata_value(
            "verify_twp_first_drift_pose",
            self._first_flagged_pose(pose_groups["twp"]),
        )
        lines = [
            "# Head-head 5-axis calibration summary",
            "",
            "# Measurement setup",
            f"# Bring-up power/reset: {self._metadata_value('bringup_power_reset', 'pending')}",
            f"# Bring-up home/reference: {self._metadata_value('bringup_home_state', 'pending')}",
            f"# Bring-up probe qualification: {self._metadata_value('bringup_probe_state', 'pending')}",
            f"# Bring-up sphere setup: {self._metadata_value('bringup_sphere_state', 'pending')}",
            f"# Bring-up B/C zeroing: {self._metadata_value('bringup_rotary_zero_state', 'pending')}",
            f"# Bring-up sphere map: {self._metadata_value('bringup_sphere_map_state', 'pending')}",
            f"# Bring-up fixed-tip TCP: {self._metadata_value('bringup_fixed_tip_state', 'pending')}",
            f"# Bring-up moving TCP: {self._metadata_value('bringup_moving_tcp_state', 'pending')}",
            f"# Bring-up TWP check: {self._metadata_value('bringup_twp_state', 'pending')}",
            f"# Bring-up overall: {self._metadata_value('bringup_overall_state', 'pending')}",
            f"# Probe ring ID (mm): {self._metadata_value('ring_id_mm', '50.0')}",
            f"# Sphere diameter (mm): {self._metadata_value('sphere_diameter_mm', '20.0')}",
            f"# Sphere stand angle (deg): {self._metadata_value('sphere_stand_angle_deg', '45.0')}",
            f"# Probe repeatability in ring (mm): {self._metadata_value('probe_repeatability_mm', '0.0')}",
            f"# Sphere center repeatability (mm): {self._metadata_value('sphere_repeatability_mm', '0.0')}",
            f"# Fixed-tip TCP result: {self._metadata_value('verify_fixed_tip_result', 'pending')}",
            f"# Fixed-tip first drift pose: {fixed_tip_first}",
            f"# Fixed-tip likely cause: {self._metadata_value('verify_fixed_tip_likely_cause', '')}",
            f"# Fixed-tip pose states: {self._pose_status_line(pose_groups['fixed_tip'])}",
            f"# Moving TCP result: {self._metadata_value('verify_moving_tcp_result', 'pending')}",
            f"# Moving TCP first drift pose: {moving_first}",
            f"# Moving TCP likely cause: {self._metadata_value('verify_moving_tcp_likely_cause', '')}",
            f"# Moving TCP pose states: {self._pose_status_line(pose_groups['moving_tcp'])}",
            f"# TWP result: {self._metadata_value('verify_twp_result', 'pending')}",
            f"# TWP first drift pose: {twp_first}",
            f"# TWP likely cause: {self._metadata_value('verify_twp_likely_cause', '')}",
            f"# TWP pose states: {self._pose_status_line(pose_groups['twp'])}",
            "",
            "# Captured sphere centers",
            f"# ref_xyz = {self._format_vec((self._capture_float('ref_x'), self._capture_float('ref_y'), self._capture_float('ref_z')))}",
            f"# b_pos_delta = {self._format_vec(self._capture_delta('b_pos'))}",
            f"# b_neg_delta = {self._format_vec(self._capture_delta('b_neg'))}",
            f"# c_pos_delta = {self._format_vec(self._capture_delta('c_pos'))}",
            f"# c_neg_delta = {self._format_vec(self._capture_delta('c_neg'))}",
            f"# bc_mix_delta = {self._format_vec(self._capture_delta('bc_mix'))}",
            "",
            "# Recommended next adjustment",
        ]
        for line in self._recommendation_lines()[2:]:
            lines.append(f"# {line}" if line else "#")
        lines.extend([
            "",
            "# Bring-up recovery guidance",
        ])
        for line in self._verify_guidance_lines()[2:]:
            lines.append(f"# {line}" if line else "#")
        lines.extend([
            "",
            "# Pose-based follow-up",
        ])
        for line in self._pose_focus_lines()[2:]:
            lines.append(f"# {line}" if line else "#")
        lines.extend([
            "",
            "# Trial change plan",
        ])
        for line in self._trial_change_plan_lines()[2:]:
            lines.append(f"# {line}" if line else "#")
        lines.extend([
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
        ])
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
