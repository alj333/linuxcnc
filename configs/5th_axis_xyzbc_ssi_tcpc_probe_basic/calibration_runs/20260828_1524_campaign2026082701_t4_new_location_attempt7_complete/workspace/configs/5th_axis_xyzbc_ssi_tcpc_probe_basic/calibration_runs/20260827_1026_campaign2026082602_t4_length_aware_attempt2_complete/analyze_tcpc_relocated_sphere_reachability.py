#!/usr/bin/env python3
"""Replay the planned balanced T4 sphere grid against exact current kinematics."""

from __future__ import annotations

import argparse
import configparser
import csv
import hashlib
import math
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

import analyze_tcpc_relocated_sphere_anchor as anchor
import fit_tcpc_dual_probe as fit


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
HAL_PATH = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic.hal"
INI_PATH = HERE / "5th_axis_xyzbc_ssi_tcpc_probe_basic.ini"
PRIMARY_PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t4_primary.ngc"
VERIFICATION_PROGRAM = REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t3_verification.ngc"
EXPECTED_PRIMARY_SHA256 = "bd68d6d5a690f50fae525d1a6d967fae571ffd7fe60cf83bed7bb889ee5f11c2"
EXPECTED_VERIFICATION_SHA256 = "ceaf8895626a2b3030fb1d36f5575f7ff5c3850630178303795279e9be483c18"
DEFAULT_REPORT = HERE / "TCPC_RELOCATED_SPHERE_REACHABILITY_REPORT.md"
DEFAULT_DETAILS = HERE / "tcpc-relocated-sphere-reachability.csv"
CAMPAIGN = 2026082404

T4_TOOL_LENGTH = 229.407000
T3_TOOL_LENGTH = 128.606729
T4_EFFECTIVE_RADIUS = 15.0 + 3.0 - 0.154742
T3_EFFECTIVE_RADIUS = 15.0 + 3.0 - 0.117658
TOP_CLEAR_RADIUS = T4_EFFECTIVE_RADIUS + 5.0
SIDE_START_RADIUS = T4_EFFECTIVE_RADIUS + 4.0
TOP_PROBE_TRAVEL = 7.0
SIDE_PROBE_TRAVEL = 6.0
HIGH_Z_LIFT = 25.0
CENTER_ERROR_ALLOWANCE = 2.0
PATH_MODEL_ALLOWANCE = 3.0
LOW_TILT_C = (0, 45, 90, 180, 225, 270, 0)
QUADRANT_C = (0, 90, 180, 270, 0)
REQUIRED_REMAINING_LINEAR_MARGIN = 10.0
REQUIRED_NOMINAL_LINEAR_MARGIN = (
    CENTER_ERROR_ALLOWANCE + PATH_MODEL_ALLOWANCE + REQUIRED_REMAINING_LINEAR_MARGIN
)
ROTARY_SAMPLE_DEG = 1.0

SET_RE = re.compile(r"^\s*setp\s+(headheadkins\.[^\s]+)\s+([^\s#]+)")


@dataclass(frozen=True)
class Pose:
    slot: int
    b_deg: float
    c_deg: float
    role: str


@dataclass(frozen=True)
class Sample:
    tool: int
    slot: int
    b_deg: float
    c_deg: float
    kind: str
    tcp: np.ndarray
    joints: np.ndarray
    joint_margins: np.ndarray
    axis_margins: np.ndarray


@dataclass(frozen=True)
class Limits:
    joint_minimum: np.ndarray
    joint_maximum: np.ndarray
    axis_minimum: np.ndarray
    axis_maximum: np.ndarray
    b_limits: tuple[float, float]
    c_limits: tuple[float, float]


def grid() -> list[Pose]:
    poses: list[Pose] = []
    slot = 0
    for phase in ("opening",):
        for c_deg in (0, 45, 90, 135, 180, 225, 270, 315, 0):
            slot += 1
            poses.append(Pose(slot, 0.0, float(c_deg), f"b0_{phase}"))
    for b_deg in (5, -5, 10, -10, 15, -15):
        for c_deg in LOW_TILT_C:
            slot += 1
            poses.append(Pose(slot, float(b_deg), float(c_deg), f"b{b_deg:+g}"))
    for b_deg in (30, -30, 45, -45):
        for c_deg in QUADRANT_C:
            slot += 1
            poses.append(Pose(slot, float(b_deg), float(c_deg), f"b{b_deg:+g}"))
    slot += 1
    poses.append(Pose(slot, 0.0, 0.0, "b0_midpoint"))
    for b_deg in (60, -60, 90, -90):
        for c_deg in QUADRANT_C:
            slot += 1
            poses.append(Pose(slot, float(b_deg), float(c_deg), f"b{b_deg:+g}"))
    for c_deg in (0, 45, 90, 135, 180, 225, 270, 315, 0):
        slot += 1
        poses.append(Pose(slot, 0.0, float(c_deg), "b0_closing"))
    assert len(poses) == 101
    return poses


def verification_grid() -> list[Pose]:
    poses: list[Pose] = []
    slot = 0
    for c_deg in (0, 90, 180, 270, 0):
        slot += 1
        poses.append(Pose(slot, 0.0, float(c_deg), "b0_opening"))
    for b_deg in (45, -45):
        for c_deg in (0, 90, 180, 270, 0):
            slot += 1
            poses.append(Pose(slot, float(b_deg), float(c_deg), f"b{b_deg:+g}"))
    slot += 1
    poses.append(Pose(slot, 0.0, 0.0, "b0_midpoint"))
    for b_deg in (90, -90):
        for c_deg in (0, 90, 180, 270, 0):
            slot += 1
            poses.append(Pose(slot, float(b_deg), float(c_deg), f"b{b_deg:+g}"))
    for c_deg in (0, 90, 180, 270, 0):
        slot += 1
        poses.append(Pose(slot, 0.0, float(c_deg), "b0_closing"))
    assert len(poses) == 31
    return poses


def parse_hal(path: Path) -> dict[str, float]:
    pins: dict[str, float] = {}
    for line in path.read_text().splitlines():
        match = SET_RE.match(line)
        if not match:
            continue
        try:
            value = float(match.group(2))
        except ValueError:
            continue
        if not math.isfinite(value):
            raise ValueError(f"HAL geometry is non-finite: {match.group(1)}={value}")
        pins[match.group(1)] = value
    required = {
        "headheadkins.nominal-c-to-b.x": 0.010934,
        "headheadkins.nominal-c-to-b.y": 0.0,
        "headheadkins.nominal-c-to-b.z": -270.0,
        "headheadkins.nominal-b-to-tool.x": -0.668710,
        "headheadkins.nominal-b-to-tool.y": -26.721365,
        "headheadkins.nominal-b-to-tool.z": -180.373272,
        "headheadkins.cal-c-to-b.x": 0.035886006,
        "headheadkins.cal-c-to-b.y": 0.009526306,
        "headheadkins.cal-c-to-b.z": 0.0,
        "headheadkins.cal-b-to-tool.x": 0.0,
        "headheadkins.cal-b-to-tool.y": 0.0,
        "headheadkins.cal-b-to-tool.z": 0.815,
        "headheadkins.b-zero-offset": fit.CURRENT_B_ZERO,
        "headheadkins.c-zero-offset": fit.CURRENT_C_ZERO,
        "headheadkins.sim-bharm-enable": 1.0,
    }
    for name, expected in required.items():
        value = pins.get(name)
        if value is None or abs(value - expected) > 1e-9:
            raise ValueError(f"HAL geometry mismatch: {name}={value!r}, expected {expected}")
    for name in (
        "headheadkins.c-axis-tilt.x",
        "headheadkins.c-axis-tilt.y",
        "headheadkins.b-axis-tilt.x",
        "headheadkins.b-axis-tilt.z",
    ):
        value = pins.get(name, 0.0)
        if abs(value) > 1e-12:
            raise ValueError(
                f"reachability replay requires the current zero rigid-axis tilt: {name}={value}"
            )
    return pins


def validate_model_constants() -> None:
    expected = {
        "fit.T4_LENGTH": (fit.T4_LENGTH, T4_TOOL_LENGTH),
        "fit.T3_LENGTH": (fit.T3_LENGTH, T3_TOOL_LENGTH),
        "anchor.EFFECTIVE_RADIUS": (anchor.EFFECTIVE_RADIUS, T4_EFFECTIVE_RADIUS),
    }
    for name, (actual, required) in expected.items():
        if abs(actual - required) > 1e-9:
            raise ValueError(f"model constant mismatch: {name}={actual}, expected {required}")


def parse_limits(path: Path) -> Limits:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    if not parser.read(path):
        raise ValueError(f"cannot read INI limits from {path}")
    joint_minimum = np.array([float(parser[f"JOINT_{joint}"]["MIN_LIMIT"]) for joint in range(3)])
    joint_maximum = np.array([float(parser[f"JOINT_{joint}"]["MAX_LIMIT"]) for joint in range(3)])
    axis_minimum = np.array([float(parser[f"AXIS_{axis}"]["MIN_LIMIT"]) for axis in "XYZ"])
    axis_maximum = np.array([float(parser[f"AXIS_{axis}"]["MAX_LIMIT"]) for axis in "XYZ"])
    b_limits = (
        max(float(parser["JOINT_3"]["MIN_LIMIT"]), float(parser["AXIS_B"]["MIN_LIMIT"])),
        min(float(parser["JOINT_3"]["MAX_LIMIT"]), float(parser["AXIS_B"]["MAX_LIMIT"])),
    )
    c_limits = (
        max(float(parser["JOINT_4"]["MIN_LIMIT"]), float(parser["AXIS_C"]["MIN_LIMIT"])),
        min(float(parser["JOINT_4"]["MAX_LIMIT"]), float(parser["AXIS_C"]["MAX_LIMIT"])),
    )
    numeric_limits = np.concatenate(
        (
            joint_minimum,
            joint_maximum,
            axis_minimum,
            axis_maximum,
            np.array(b_limits),
            np.array(c_limits),
        )
    )
    if not np.all(np.isfinite(numeric_limits)):
        raise ValueError("INI contains a non-finite axis or joint limit")
    if np.any(joint_minimum >= joint_maximum) or np.any(axis_minimum >= axis_maximum):
        raise ValueError("INI contains a reversed or empty linear limit interval")
    if b_limits[0] >= b_limits[1] or c_limits[0] >= c_limits[1]:
        raise ValueError("INI contains a reversed or empty rotary limit interval")
    return Limits(
        joint_minimum,
        joint_maximum,
        axis_minimum,
        axis_maximum,
        b_limits,
        c_limits,
    )


def subroutine_text(text: str, name: str) -> str:
    match = re.search(
        rf"^o<{re.escape(name)}> sub\s*$([\s\S]*?)^o<{re.escape(name)}> endsub\s*$",
        text,
        flags=re.MULTILINE,
    )
    if not match:
        raise ValueError(f"primary program is missing subroutine {name}")
    return match.group(1)


def validate_program_contract(path: Path) -> tuple[list[Pose], str]:
    text = path.read_text()
    digest = hashlib.sha256(text.encode()).hexdigest()
    if digest != EXPECTED_PRIMARY_SHA256:
        raise ValueError(
            f"primary program SHA-256 {digest} does not match frozen {EXPECTED_PRIMARY_SHA256}"
        )
    required_snippets = (
        "#707 = 101.0",
        "#711 = 23.0",
        "#715 = 2026082404.0",
        "#717 = 0.154742",
        "#539 = -1.0",
        "G1 Z#<safe_z>",
        "o<negative_b_upper_u> if [#520 LT -0.001]",
        "#122 = [-#539 * #533 * #511]",
        "- [#539 * #505]",
        "tcpc-relocated-sphere-t4-primary-results.csv",
        "tcpc-relocated-sphere-t4-primary-state.csv",
        "tcpc-relocated-sphere-t4-primary-closures.csv",
    )
    for snippet in required_snippets:
        if snippet not in text:
            raise ValueError(f"primary program contract is missing {snippet!r}")
    if "tcpc-relocated-sphere-t4-anchor-results.csv" in text or "G4 P20" in text:
        raise ValueError("primary program contains an anchor output path or 20-second dwell")
    if len(re.findall(r"^M0\s*$", text, flags=re.MULTILINE)) != 1:
        raise ValueError("primary program must contain exactly one operator M0")

    constants = {int(key): float(value) for key, value in re.findall(r"^#(50[789]|51[0125])\s*=\s*([-+0-9.]+)", text, re.MULTILINE)}
    expected_constants = {507: 1200.0, 508: TOP_PROBE_TRAVEL, 509: 5.0, 510: 4.0, 511: SIDE_PROBE_TRAVEL, 512: 3.0, 515: HIGH_Z_LIFT}
    if constants != expected_constants:
        raise ValueError(f"primary program motion constants differ: {constants!r}")

    b0_sub = subroutine_text(text, "tcpc_primary_b0_sweep")
    b0_c = [float(value) for value in re.findall(r"^\s*o<tcpc_measure_pose> call \[0\.0\] \[([-+0-9.]+)\]", b0_sub, re.MULTILINE)]
    if b0_c != [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0, 0.0]:
        raise ValueError(f"primary B0 sweep differs: {b0_c!r}")
    tilt_sub = subroutine_text(text, "tcpc_primary_tilt_block")
    tilt_c = [float(value) for value in re.findall(r"^\s*o<tcpc_measure_pose> call \[#<block_b>\] \[([-+0-9.]+)\]", tilt_sub, re.MULTILINE)]
    if tilt_c != [0.0, 90.0, 180.0, 270.0, 0.0]:
        raise ValueError(f"primary tilted sweep differs: {tilt_c!r}")
    low_tilt_sub = subroutine_text(text, "tcpc_primary_low_tilt_block")
    low_tilt_c = [float(value) for value in re.findall(r"^\s*o<tcpc_measure_pose> call \[#<block_b>\] \[([-+0-9.]+)\]", low_tilt_sub, re.MULTILINE)]
    if low_tilt_c != [float(value) for value in LOW_TILT_C]:
        raise ValueError(f"primary low tilted sweep differs: {low_tilt_c!r}")

    body = re.search(
        r"^o<run_relocated_t4_primary> if \[ABS\[#711 - 23\.0\] LT 0\.1\]\s*$([\s\S]*?)^o<run_relocated_t4_primary> endif\s*$",
        text,
        flags=re.MULTILINE,
    )
    if not body:
        raise ValueError("primary mode-23 body is missing")
    tokens = re.findall(
        r"^\s*o<tcpc_primary_b0_sweep> call \[([-+0-9.]+)\]|"
        r"^\s*o<tcpc_primary_low_tilt_block> call \[([-+0-9.]+)\] \[([-+0-9.]+)\]|"
        r"^\s*o<tcpc_primary_tilt_block> call \[([-+0-9.]+)\] \[([-+0-9.]+)\]|"
        r"^\s*o<tcpc_measure_pose> call \[0\.0\] \[0\.0\]",
        body.group(1),
        flags=re.MULTILINE,
    )
    expanded: list[Pose] = []
    slot = 0
    for b0_block, low_tilt_b, low_tilt_block, tilt_b, tilt_block in tokens:
        if b0_block:
            for c_deg in b0_c:
                slot += 1
                expanded.append(Pose(slot, 0.0, c_deg, f"program_b0_{b0_block}"))
        elif low_tilt_b:
            if abs(float(low_tilt_b) - float(low_tilt_block)) > 1e-9:
                raise ValueError("primary low tilted B and block ID differ")
            for c_deg in low_tilt_c:
                slot += 1
                expanded.append(Pose(slot, float(low_tilt_b), c_deg, f"program_b{low_tilt_b}"))
        elif tilt_b:
            if abs(float(tilt_b) - float(tilt_block)) > 1e-9:
                raise ValueError("primary tilted B and block ID differ")
            for c_deg in tilt_c:
                slot += 1
                expanded.append(Pose(slot, float(tilt_b), c_deg, f"program_b{tilt_b}"))
        else:
            slot += 1
            expanded.append(Pose(slot, 0.0, 0.0, "program_midpoint"))
    if [(pose.b_deg, pose.c_deg) for pose in expanded] != [(pose.b_deg, pose.c_deg) for pose in grid()]:
        raise ValueError("primary program pose order differs from reachability grid")
    return expanded, digest


def validate_verification_program_contract(path: Path) -> tuple[list[Pose], str]:
    text = path.read_text()
    digest = hashlib.sha256(text.encode()).hexdigest()
    if digest != EXPECTED_VERIFICATION_SHA256:
        raise ValueError(
            f"verification program SHA-256 {digest} does not match frozen {EXPECTED_VERIFICATION_SHA256}"
        )
    required_snippets = (
        "#707 = 31.0",
        "#711 = 24.0",
        "#715 = 2026082404.0",
        "#716 = 1.0",
        "#717 = 0.117658",
        "#539 = -1.0",
        "G1 Z#<safe_z>",
        "o<negative_b_upper_u> if [#520 LT -0.001]",
        "#122 = [-#539 * #533 * #511]",
        "- [#539 * #505]",
        "tcpc-relocated-sphere-t3-verification-results.csv",
        "tcpc-relocated-sphere-t3-verification-state.csv",
        "tcpc-relocated-sphere-t3-verification-closures.csv",
    )
    for snippet in required_snippets:
        if snippet not in text:
            raise ValueError(f"verification program contract is missing {snippet!r}")
    if "tcpc-relocated-sphere-t4-primary-results.csv" in text or "G4 P20" in text:
        raise ValueError("verification program contains a primary output path or 20-second dwell")
    if len(re.findall(r"^M0\s*$", text, flags=re.MULTILINE)) != 1:
        raise ValueError("verification program must contain exactly one operator M0")

    constants = {int(key): float(value) for key, value in re.findall(r"^#(50[789]|51[0125])\s*=\s*([-+0-9.]+)", text, re.MULTILINE)}
    expected_constants = {507: 1200.0, 508: TOP_PROBE_TRAVEL, 509: 5.0, 510: 4.0, 511: SIDE_PROBE_TRAVEL, 512: 3.0, 515: HIGH_Z_LIFT}
    if constants != expected_constants:
        raise ValueError(f"verification program motion constants differ: {constants!r}")

    b0_sub = subroutine_text(text, "tcpc_primary_b0_sweep")
    b0_c = [float(value) for value in re.findall(r"^\s*o<tcpc_measure_pose> call \[0\.0\] \[([-+0-9.]+)\]", b0_sub, re.MULTILINE)]
    if b0_c != [0.0, 90.0, 180.0, 270.0, 0.0]:
        raise ValueError(f"verification B0 sweep differs: {b0_c!r}")
    tilt_sub = subroutine_text(text, "tcpc_primary_tilt_block")
    tilt_c = [float(value) for value in re.findall(r"^\s*o<tcpc_measure_pose> call \[#<block_b>\] \[([-+0-9.]+)\]", tilt_sub, re.MULTILINE)]
    if tilt_c != [0.0, 90.0, 180.0, 270.0, 0.0]:
        raise ValueError(f"verification tilted sweep differs: {tilt_c!r}")

    body = re.search(
        r"^o<run_relocated_t3_verification> if \[ABS\[#711 - 24\.0\] LT 0\.1\]\s*$([\s\S]*?)^o<run_relocated_t3_verification> endif\s*$",
        text,
        flags=re.MULTILINE,
    )
    if not body:
        raise ValueError("verification mode-24 body is missing")
    tokens = re.findall(
        r"^\s*o<tcpc_primary_b0_sweep> call \[([-+0-9.]+)\]|"
        r"^\s*o<tcpc_primary_tilt_block> call \[([-+0-9.]+)\] \[([-+0-9.]+)\]|"
        r"^\s*o<tcpc_measure_pose> call \[0\.0\] \[0\.0\]",
        body.group(1),
        flags=re.MULTILINE,
    )
    expanded: list[Pose] = []
    slot = 0
    for b0_block, tilt_b, tilt_block in tokens:
        if b0_block:
            for c_deg in b0_c:
                slot += 1
                expanded.append(Pose(slot, 0.0, c_deg, f"program_b0_{b0_block}"))
        elif tilt_b:
            if abs(float(tilt_b) - float(tilt_block)) > 1e-9:
                raise ValueError("verification tilted B and block ID differ")
            for c_deg in tilt_c:
                slot += 1
                expanded.append(Pose(slot, float(tilt_b), c_deg, f"program_b{tilt_b}"))
        else:
            slot += 1
            expanded.append(Pose(slot, 0.0, 0.0, "program_midpoint"))
    if [(pose.b_deg, pose.c_deg) for pose in expanded] != [
        (pose.b_deg, pose.c_deg) for pose in verification_grid()
    ]:
        raise ValueError("verification program pose order differs from reachability grid")
    return expanded, digest


def pin_vector(pins: dict[str, float], prefix: str) -> np.ndarray:
    return np.array([pins.get(f"{prefix}.{axis}", 0.0) for axis in fit.AXES])


def harmonic_offset(b_deg: float, c_deg: float, pins: dict[str, float]) -> np.ndarray:
    if pins.get("headheadkins.sim-bharm-enable", 0.0) < 0.5:
        return np.zeros(3)
    b_eff = b_deg + pins.get("headheadkins.b-zero-offset", 0.0)
    c_eff = c_deg + pins.get("headheadkins.c-zero-offset", 0.0)
    b_rad = math.radians(b_eff)
    c_rad = math.radians(c_eff)
    c_ref = math.radians(pins.get("headheadkins.c-zero-offset", 0.0))
    sin_b = math.sin(b_rad)
    omc_b = 1.0 - math.cos(b_rad)
    sin_2b = math.sin(2.0 * b_rad)
    sin_c = math.sin(c_rad)
    cos_c = math.cos(c_rad)

    result = np.zeros(3)
    for term, value in (("sin", sin_b), ("omc", omc_b), ("sin2", sin_2b)):
        result += value * pin_vector(pins, f"headheadkins.bharm-m.{term}")

    c_local = np.zeros(3)
    for term, value in (("sin", sin_b), ("omc", omc_b), ("sin2", sin_2b)):
        c_local += value * pin_vector(pins, f"headheadkins.bharm-c.{term}")
    c_frame = fit.rotation_y(pins.get("headheadkins.c-axis-tilt.y", 0.0)) @ fit.rotation_x(
        pins.get("headheadkins.c-axis-tilt.x", 0.0)
    )
    result += c_frame @ (fit.rotation_z(c_eff) @ c_local)

    for term, value in (
        ("cos", cos_c - math.cos(c_ref)),
        ("sin", sin_c - math.sin(c_ref)),
        ("cos2", math.cos(2.0 * c_rad) - math.cos(2.0 * c_ref)),
        ("sin2", math.sin(2.0 * c_rad) - math.sin(2.0 * c_ref)),
    ):
        result += value * pin_vector(pins, f"headheadkins.charm.{term}")

    mid = sin_2b * sin_2b
    for term, value in (
        ("base", mid),
        ("cosc", mid * cos_c),
        ("sinc", mid * sin_c),
        ("cos2c", mid * math.cos(2.0 * c_rad)),
        ("sin2c", mid * math.sin(2.0 * c_rad)),
    ):
        result += value * pin_vector(pins, f"headheadkins.bmid.{term}")

    for term, value in (
        ("sinb-sinc", sin_b * sin_c),
        ("omcb-sinc", omc_b * sin_c),
        ("omcb-sin2c", omc_b * sin_c * sin_c),
        ("sinb-cosc", sin_b * cos_c),
        ("omcb-cosc", omc_b * cos_c),
        ("sinb-sin2c", sin_b * math.sin(2.0 * c_rad)),
        ("sinb-cos2c", sin_b * math.cos(2.0 * c_rad)),
    ):
        result += value * pin_vector(pins, f"headheadkins.bcross.{term}")
    return result


def tool_offset(b_deg: float, c_deg: float, pins: dict[str, float], length: float = T4_TOOL_LENGTH) -> np.ndarray:
    return fit.rigid_offset(b_deg, c_deg, length, {}) + harmonic_offset(b_deg, c_deg, pins)


def inverse_joints(
    tcp: np.ndarray,
    b_deg: float,
    c_deg: float,
    pins: dict[str, float],
    length: float = T4_TOOL_LENGTH,
) -> np.ndarray:
    origin = tool_offset(0.0, 0.0, pins, length)
    return tcp - tool_offset(b_deg, c_deg, pins, length) + origin


def frame(b_deg: float, c_deg: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    b = math.radians(b_deg)
    c = math.radians(c_deg)
    w = np.array([-math.sin(b) * math.cos(c), -math.sin(b) * math.sin(c), -math.cos(b)])
    u = np.array([math.cos(b) * math.cos(c), math.cos(b) * math.sin(c), -math.sin(b)])
    v = np.array([-math.sin(c), math.cos(c), 0.0])
    return w, u, v


def linear_points(start: np.ndarray, end: np.ndarray, maximum_step: float = 1.0) -> Iterable[np.ndarray]:
    count = max(1, int(math.ceil(np.linalg.norm(end - start) / maximum_step)))
    for index in range(count + 1):
        yield start + (end - start) * (index / count)


def append_sample(
    samples: list[Sample],
    tool: int,
    length: float,
    pose: Pose,
    kind: str,
    tcp: np.ndarray,
    pins: dict[str, float],
    limits: Limits,
    b_deg: float | None = None,
    c_deg: float | None = None,
) -> None:
    b = pose.b_deg if b_deg is None else b_deg
    c = pose.c_deg if c_deg is None else c_deg
    joints = inverse_joints(tcp, b, c, pins, length)
    joint_margins = np.minimum(joints - limits.joint_minimum, limits.joint_maximum - joints)
    axis_margins = np.minimum(tcp - limits.axis_minimum, limits.axis_maximum - tcp)
    samples.append(Sample(tool, pose.slot, b, c, kind, tcp.copy(), joints, joint_margins, axis_margins))


def replay(
    center: np.ndarray,
    pins: dict[str, float],
    limits: Limits,
    tool: int = 4,
    length: float = T4_TOOL_LENGTH,
    effective_radius: float = T4_EFFECTIVE_RADIUS,
    poses: Sequence[Pose] | None = None,
) -> list[Sample]:
    samples: list[Sample] = []
    selected_poses = list(grid() if poses is None else poses)
    top_clear_radius = effective_radius + 5.0
    side_start_radius = effective_radius + 4.0
    previous_pose: Pose | None = None
    previous_top: np.ndarray | None = None
    for pose in selected_poses:
        w, u, v = frame(pose.b_deg, pose.c_deg)
        top = center - w * top_clear_radius

        if previous_pose is not None and previous_top is not None:
            high = previous_top + np.array([0.0, 0.0, HIGH_Z_LIFT])
            append_sample(samples, tool, length, pose, "transit_lift", high, pins, limits, previous_pose.b_deg, previous_pose.c_deg)
            angle_span = max(abs(pose.b_deg - previous_pose.b_deg), abs(pose.c_deg - previous_pose.c_deg))
            count = max(1, int(math.ceil(angle_span / ROTARY_SAMPLE_DEG)))
            for index in range(count + 1):
                fraction = index / count
                b = previous_pose.b_deg + (pose.b_deg - previous_pose.b_deg) * fraction
                c = previous_pose.c_deg + (pose.c_deg - previous_pose.c_deg) * fraction
                append_sample(samples, tool, length, pose, "transit_rotary", high, pins, limits, b, c)
            high_target_xy = np.array([top[0], top[1], high[2]])
            for point in linear_points(high, high_target_xy):
                append_sample(samples, tool, length, pose, "transit_xy", point, pins, limits)
            for point in linear_points(high_target_xy, top):
                append_sample(samples, tool, length, pose, "transit_descend", point, pins, limits)

        append_sample(samples, tool, length, pose, "top_clear", top, pins, limits)
        append_sample(samples, tool, length, pose, "w_probe_endpoint", top + w * TOP_PROBE_TRAVEL, pins, limits)

        upper_sign = -1.0 if pose.b_deg >= 0.0 else 1.0
        u_start = center + upper_sign * u * side_start_radius
        u_clear = u_start - w * top_clear_radius
        u_direction = -upper_sign * u
        for point in linear_points(top, u_clear):
            append_sample(samples, tool, length, pose, "u_clear_path", point, pins, limits)
        for point in linear_points(u_clear, u_start):
            append_sample(samples, tool, length, pose, "u_descend_path", point, pins, limits)
        u_endpoint = u_start + u_direction * SIDE_PROBE_TRAVEL
        for point in linear_points(u_start, u_endpoint):
            append_sample(samples, tool, length, pose, "u_probe_path", point, pins, limits)

        for sign, name in ((-1.0, "v_minus"), (1.0, "v_plus")):
            v_start = center + sign * v * side_start_radius
            v_clear = v_start - w * top_clear_radius
            for point in linear_points(top, v_clear):
                append_sample(samples, tool, length, pose, f"{name}_clear_path", point, pins, limits)
            for point in linear_points(v_clear, v_start):
                append_sample(samples, tool, length, pose, f"{name}_descend_path", point, pins, limits)
            v_endpoint = v_start - sign * v * SIDE_PROBE_TRAVEL
            for point in linear_points(v_start, v_endpoint):
                append_sample(samples, tool, length, pose, f"{name}_probe_path", point, pins, limits)

        previous_pose = pose
        previous_top = top
    return samples


def write_details(path: Path, samples: Sequence[Sample]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "tool_number",
                "slot_id",
                "abs_b_deg",
                "abs_c_deg",
                "sample_kind",
                "tcp_abs_x_mm",
                "tcp_abs_y_mm",
                "tcp_abs_z_mm",
                "joint_0_mm",
                "joint_1_mm",
                "joint_2_mm",
                "joint_0_margin_mm",
                "joint_1_margin_mm",
                "joint_2_margin_mm",
                "axis_x_margin_mm",
                "axis_y_margin_mm",
                "axis_z_margin_mm",
            ]
        )
        for sample in samples:
            writer.writerow(
                [
                    sample.tool,
                    sample.slot,
                    f"{sample.b_deg:.6f}",
                    f"{sample.c_deg:.6f}",
                    sample.kind,
                    *(f"{value:.9f}" for value in sample.tcp),
                    *(f"{value:.9f}" for value in sample.joints),
                    *(f"{value:.9f}" for value in sample.joint_margins),
                    *(f"{value:.9f}" for value in sample.axis_margins),
                ]
            )


def write_report(
    path: Path,
    center: np.ndarray,
    attempt: int,
    samples: Sequence[Sample],
    b_limits: tuple[float, float],
    c_limits: tuple[float, float],
    details: Path,
    primary_program_digest: str,
    verification_program_digest: str,
) -> bool:
    worst_joint = min(samples, key=lambda sample: float(np.min(sample.joint_margins)))
    worst_axis = min(samples, key=lambda sample: float(np.min(sample.axis_margins)))
    per_joint = [min(samples, key=lambda sample, joint=joint: sample.joint_margins[joint]) for joint in range(3)]
    per_axis = [min(samples, key=lambda sample, axis=axis: sample.axis_margins[axis]) for axis in range(3)]
    all_poses = grid() + verification_grid()
    b_margin = min(min(pose.b_deg - b_limits[0], b_limits[1] - pose.b_deg) for pose in all_poses)
    c_margin = min(min(pose.c_deg - c_limits[0], c_limits[1] - pose.c_deg) for pose in all_poses)
    worst_linear_margin = min(float(np.min(worst_joint.joint_margins)), float(np.min(worst_axis.axis_margins)))
    remaining_margin = worst_linear_margin - CENTER_ERROR_ALLOWANCE - PATH_MODEL_ALLOWANCE
    passed = (
        remaining_margin >= REQUIRED_REMAINING_LINEAR_MARGIN
        and b_margin >= 5.0
        and c_margin >= 5.0
    )
    lines = [
        "# Relocated-Sphere T4 Reachability Report",
        "",
        f"- measurement campaign: `{CAMPAIGN}`",
        f"- inherited anchor campaign: `{anchor.CAMPAIGN}`",
        f"- anchor attempt: `{attempt}`",
        f"- anchor center: `X{center[0]:.6f} Y{center[1]:.6f} Z{center[2]:.6f}` mm",
        f"- planned T4 primary poses: `{len(grid())}`",
        f"- planned T3 verification poses: `{len(verification_grid())}`",
        f"- sampled kinematic points: `{len(samples)}`",
        f"- frozen T4 primary SHA-256: `{primary_program_digest}`",
        f"- frozen T3 verification SHA-256: `{verification_program_digest}`",
        f"- required nominal AXIS/JOINT margin: `{REQUIRED_NOMINAL_LINEAR_MARGIN:.3f} mm`",
        f"- reserved empirical measured-center allowance: `{CENTER_ERROR_ALLOWANCE:.3f} mm`",
        f"- reserved path/model allowance: `{PATH_MODEL_ALLOWANCE:.3f} mm`",
        f"- required margin after allowances: `{REQUIRED_REMAINING_LINEAR_MARGIN:.3f} mm`",
        f"- status: `{'PASS' if passed else 'FAIL'}`",
        "",
        "| constraint | minimum margin | remaining after allowances | pose/sample | position |",
        "| --- | ---: | ---: | --- | ---: |",
    ]
    for joint, sample in enumerate(per_joint):
        lines.append(
            f"| J{joint} | {sample.joint_margins[joint]:.6f} mm | "
            f"{sample.joint_margins[joint] - CENTER_ERROR_ALLOWANCE - PATH_MODEL_ALLOWANCE:.6f} mm | "
            f"T{sample.tool} B{sample.b_deg:+g} C{sample.c_deg:g} `{sample.kind}` | {sample.joints[joint]:.6f} mm |"
        )
    for axis, name in enumerate("XYZ"):
        sample = per_axis[axis]
        lines.append(
            f"| {name} axis | {sample.axis_margins[axis]:.6f} mm | "
            f"{sample.axis_margins[axis] - CENTER_ERROR_ALLOWANCE - PATH_MODEL_ALLOWANCE:.6f} mm | "
            f"T{sample.tool} B{sample.b_deg:+g} C{sample.c_deg:g} `{sample.kind}` | {sample.tcp[axis]:.6f} mm |"
        )
    lines.extend(
        [
            "",
            f"Rotary configured-limit margins: B `{b_margin:.3f} deg`, C `{c_margin:.3f} deg`.",
            "",
            "The 2 mm center allowance is a conservative campaign assumption, not a bound enforced by the probing runners. Each accepted pass is internally checked, but successive accepted centers can update the next pose origin. The observed baseline center errors are below 0.4 mm; any campaign result outside the 2 mm anchor envelope invalidates this reachability release.",
            "",
            "The 3 mm path/model allowance covers omitted post-contact retract segments and the small TCPC entry-angle origin difference. The current zero C-frame and B-axis tilt settings are asserted before replay.",
            "",
            "This report checks controller geometry and configured limits. It does not release probe-body, holder, sphere-post, cable, or fixture clearance. Every positive-B pose has a corresponding negative-B pose. At 2026-08-24T23:42:38+07:00, the operator explicitly accepted T4 physical clearance for B-5/-10/-15 at C45/C225; that is operator evidence, not a result of this replay model.",
            "",
            f"Detailed samples: `{details.name}`",
            "",
        ]
    )
    path.write_text("\n".join(lines))
    return passed


def self_test() -> None:
    anchor.validate_program_hash()
    validate_model_constants()
    pins = parse_hal(HAL_PATH)
    limits = parse_limits(INI_PATH)
    assert np.allclose(limits.joint_minimum, [-10.0, -10.0, -900.01])
    assert np.allclose(limits.joint_maximum, [3350.01, 1730.01, 10.0])
    assert np.allclose(limits.axis_minimum, [-10.0, -10.0, -900.01])
    assert np.allclose(limits.axis_maximum, [3350.01, 1730.01, 0.0])
    assert limits.b_limits == (-100.0, 100.0)
    assert limits.c_limits == (-359.0, 359.0)
    expected_offset = np.array([-26.316704, 408.507824, -269.540992])
    assert np.allclose(tool_offset(90.0, 270.0, pins), expected_offset, atol=2e-6)
    negative_b_delta = tool_offset(-45.0, 90.0, pins, T4_TOOL_LENGTH) - tool_offset(
        -45.0, 90.0, pins, T3_TOOL_LENGTH
    )
    assert np.allclose(
        negative_b_delta,
        [0.030478258, 71.2765487, -71.2765552],
        atol=2e-7,
    )
    oracle_tcp = np.array([1000.0, 800.0, -300.0])
    negative_b_inverse_delta = inverse_joints(
        oracle_tcp, -45.0, 90.0, pins, T4_TOOL_LENGTH
    ) - inverse_joints(oracle_tcp, -45.0, 90.0, pins, T3_TOOL_LENGTH)
    assert np.allclose(
        negative_b_inverse_delta,
        [-0.030478258, -71.2765487, -29.5237158],
        atol=2e-7,
    )
    old_center = np.array([1024.211254, 443.417496, -302.422242])
    w, _, _ = frame(90.0, 270.0)
    top = old_center - w * TOP_CLEAR_RADIUS
    joints = inverse_joints(top, 90.0, 270.0, pins)
    assert abs(joints[1] - (-14.647156)) < 3e-6
    assert len(grid()) == 101
    tilted_c = {pose.c_deg for pose in grid() if pose.b_deg != 0.0}
    assert tilted_c == {0.0, 45.0, 90.0, 180.0, 225.0, 270.0}
    assert {pose.b_deg for pose in grid()} == {-90.0, -60.0, -45.0, -30.0, -15.0, -10.0, -5.0, 0.0, 5.0, 10.0, 15.0, 30.0, 45.0, 60.0, 90.0}
    for pose in grid():
        if abs(pose.b_deg) <= 15.0 and abs(pose.b_deg) > 0.001:
            assert pose.c_deg in {float(value) for value in LOW_TILT_C}
        elif abs(pose.b_deg) > 15.0:
            assert pose.c_deg in {float(value) for value in QUADRANT_C}
        if abs(pose.b_deg) > 0.001:
            assert pose.c_deg not in {135.0, 315.0}
    program_grid, digest = validate_program_contract(PRIMARY_PROGRAM)
    assert len(program_grid) == 101 and len(digest) == 64
    verification_poses, verification_digest = validate_verification_program_contract(VERIFICATION_PROGRAM)
    assert len(verification_poses) == 31 and len(verification_digest) == 64
    with tempfile.TemporaryDirectory() as directory:
        scratch = Path(directory)
        hal_text = HAL_PATH.read_text()
        for name, mutated in (
            (
                "required-nan.hal",
                hal_text.replace(
                    "setp headheadkins.nominal-c-to-b.x 0.010934",
                    "setp headheadkins.nominal-c-to-b.x nan",
                    1,
                ),
            ),
            (
                "tilt-nan.hal",
                hal_text + "\nsetp headheadkins.b-axis-tilt.x nan\n",
            ),
        ):
            path = scratch / name
            path.write_text(mutated)
            try:
                parse_hal(path)
            except ValueError:
                pass
            else:
                raise AssertionError(f"non-finite HAL mutation {name} was accepted")
        bad_ini = scratch / "nonfinite-limit.ini"
        bad_ini.write_text(INI_PATH.read_text().replace("MIN_LIMIT = -10", "MIN_LIMIT = nan", 1))
        try:
            parse_limits(bad_ini)
        except ValueError:
            pass
        else:
            raise AssertionError("non-finite INI limit was accepted")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor-results", type=Path, default=anchor.DEFAULT_RESULTS)
    parser.add_argument("--anchor-state", type=Path, default=anchor.DEFAULT_STATE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--details", type=Path, default=DEFAULT_DETAILS)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        print("self-test: PASS")
        return 0
    try:
        anchor.validate_program_hash()
        validate_model_constants()
        result_rows = anchor.read_rows(args.anchor_results, anchor.RESULT_FIELDS)
        state_rows = anchor.read_rows(args.anchor_state, anchor.STATE_FIELDS)
        attempt, center_tuple = anchor.validate(result_rows, state_rows)
        pins = parse_hal(HAL_PATH)
        limits = parse_limits(INI_PATH)
        _, primary_program_digest = validate_program_contract(PRIMARY_PROGRAM)
        _, verification_program_digest = validate_verification_program_contract(VERIFICATION_PROGRAM)
        center = np.array(center_tuple)
        samples = replay(center, pins, limits)
        samples.extend(
            replay(
                center,
                pins,
                limits,
                tool=3,
                length=T3_TOOL_LENGTH,
                effective_radius=T3_EFFECTIVE_RADIUS,
                poses=verification_grid(),
            )
        )
        write_details(args.details, samples)
        passed = write_report(
            args.report,
            center,
            attempt,
            samples,
            limits.b_limits,
            limits.c_limits,
            args.details,
            primary_program_digest,
            verification_program_digest,
        )
    except (OSError, ValueError, KeyError) as exc:
        print(f"reachability analysis: FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"reachability analysis: {'PASS' if passed else 'FAIL'}")
    print(f"report: {args.report}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
