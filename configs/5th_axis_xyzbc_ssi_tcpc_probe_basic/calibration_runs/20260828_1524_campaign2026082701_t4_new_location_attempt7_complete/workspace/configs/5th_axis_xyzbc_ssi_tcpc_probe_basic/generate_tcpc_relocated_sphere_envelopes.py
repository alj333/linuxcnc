#!/usr/bin/env python3
"""Generate gated no-contact envelopes for the relocated-sphere campaign."""

from __future__ import annotations

import argparse
from collections import Counter
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np

import analyze_tcpc_relocated_sphere_anchor as anchor
import analyze_tcpc_relocated_sphere_reachability as reach


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_T4_OUTPUT = (
    REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t4_no_contact_envelope.ngc"
)
DEFAULT_T3_OUTPUT = (
    REPO_ROOT / "nc_files/calibration/tcpc_relocated_sphere_t3_no_contact_envelope.ngc"
)
CAMPAIGN = 2026082404


@dataclass(frozen=True)
class ToolSpec:
    tool: int
    length: float
    calibration_offset: float
    effective_radius: float
    pose_count: int
    title: str


@dataclass(frozen=True)
class ReachabilityAcceptance:
    center: tuple[float, float, float]
    attempt: int
    primary_digest: str
    verification_digest: str
    worst_nominal_linear_margin: float
    remaining_linear_margin: float
    b_margin: float
    c_margin: float


T4_SPEC = ToolSpec(
    tool=4,
    length=anchor.TOOL_LENGTH,
    calibration_offset=anchor.CAL_OFFSET,
    effective_radius=anchor.EFFECTIVE_RADIUS,
    pose_count=101,
    title="T4 long probe",
)
T3_SPEC = ToolSpec(
    tool=3,
    length=reach.T3_TOOL_LENGTH,
    calibration_offset=0.117658,
    effective_radius=reach.T3_EFFECTIVE_RADIUS,
    pose_count=31,
    title="T3 short probe",
)


class GenerationError(ValueError):
    pass


def validate_signed_b_pairing(poses: Sequence[reach.Pose]) -> None:
    """Require each positive-B pose to have the same negative-B counterpart."""
    positive: Counter[tuple[float, float]] = Counter()
    negative: Counter[tuple[float, float]] = Counter()
    for pose in poses:
        key = (round(abs(pose.b_deg), 9), round(pose.c_deg % 360.0, 9))
        if pose.b_deg > 0.001:
            positive[key] += 1
        elif pose.b_deg < -0.001:
            negative[key] += 1
    if positive != negative:
        raise GenerationError(
            "every positive-B/C pose must have a matching negative-B/C pose "
            f"with the same multiplicity: positive={positive}, negative={negative}"
        )


def validate_combined_reachability(
    anchor_results: Path,
    anchor_state: Path,
) -> tuple[ReachabilityAcceptance, list[reach.Pose], list[reach.Pose]]:
    """Validate frozen inputs and replay both complete tool paths without output."""
    anchor.validate_program_hash()
    reach.validate_model_constants()
    result_rows = anchor.read_rows(anchor_results, anchor.RESULT_FIELDS)
    state_rows = anchor.read_rows(anchor_state, anchor.STATE_FIELDS)
    attempt, center_tuple = anchor.validate(result_rows, state_rows)

    primary_poses, primary_digest = reach.validate_program_contract(reach.PRIMARY_PROGRAM)
    verification_poses, verification_digest = reach.validate_verification_program_contract(
        reach.VERIFICATION_PROGRAM
    )
    if len(primary_poses) != T4_SPEC.pose_count or len(verification_poses) != T3_SPEC.pose_count:
        raise GenerationError("frozen program pose counts do not match the 101/31 envelope contract")

    pins = reach.parse_hal(reach.HAL_PATH)
    limits = reach.parse_limits(reach.INI_PATH)
    center = np.asarray(center_tuple, dtype=float)
    samples = reach.replay(
        center,
        pins,
        limits,
        tool=T4_SPEC.tool,
        length=T4_SPEC.length,
        effective_radius=T4_SPEC.effective_radius,
        poses=primary_poses,
    )
    samples.extend(
        reach.replay(
            center,
            pins,
            limits,
            tool=T3_SPEC.tool,
            length=T3_SPEC.length,
            effective_radius=T3_SPEC.effective_radius,
            poses=verification_poses,
        )
    )
    if not samples:
        raise GenerationError("combined reachability replay produced no samples")

    joint_margin = min(float(np.min(sample.joint_margins)) for sample in samples)
    axis_margin = min(float(np.min(sample.axis_margins)) for sample in samples)
    worst_linear_margin = min(joint_margin, axis_margin)
    remaining_margin = (
        worst_linear_margin - reach.CENTER_ERROR_ALLOWANCE - reach.PATH_MODEL_ALLOWANCE
    )
    all_poses = primary_poses + verification_poses
    b_margin = min(
        min(pose.b_deg - limits.b_limits[0], limits.b_limits[1] - pose.b_deg)
        for pose in all_poses
    )
    c_margin = min(
        min(pose.c_deg - limits.c_limits[0], limits.c_limits[1] - pose.c_deg)
        for pose in all_poses
    )
    passed = (
        remaining_margin >= reach.REQUIRED_REMAINING_LINEAR_MARGIN
        and b_margin >= 5.0
        and c_margin >= 5.0
    )
    if not passed:
        raise GenerationError(
            "combined T4/T3 reachability failed: "
            f"nominal linear margin {worst_linear_margin:.6f} mm, "
            f"remaining {remaining_margin:.6f} mm, "
            f"B margin {b_margin:.6f} deg, C margin {c_margin:.6f} deg"
        )

    acceptance = ReachabilityAcceptance(
        center=tuple(float(value) for value in center),
        attempt=attempt,
        primary_digest=primary_digest,
        verification_digest=verification_digest,
        worst_nominal_linear_margin=worst_linear_margin,
        remaining_linear_margin=remaining_margin,
        b_margin=b_margin,
        c_margin=c_margin,
    )
    return acceptance, primary_poses, verification_poses


def pose_calls(poses: Sequence[reach.Pose]) -> str:
    lines: list[str] = []
    for pose in poses:
        lines.append(
            f"(Pose {pose.slot}: {pose.role})\n"
            f"o<tcpc_envelope_pose> call [{pose.slot:.1f}] "
            f"[{pose.b_deg:.1f}] [{pose.c_deg:.1f}]"
        )
    return "\n".join(lines)


def render_program(
    spec: ToolSpec,
    poses: Sequence[reach.Pose],
    center: tuple[float, float, float],
    attempt: int,
    primary_digest: str,
    verification_digest: str,
) -> str:
    """Render one operator-started envelope from an already accepted center."""
    if len(poses) != spec.pose_count:
        raise GenerationError(
            f"T{spec.tool} render received {len(poses)} poses, expected {spec.pose_count}"
        )
    if not all(np.isfinite(center)):
        raise GenerationError("accepted center contains a non-finite coordinate")
    validate_signed_b_pairing(poses)

    calls = pose_calls(poses)
    program = f"""(TCPC relocated-sphere no-contact envelope - {spec.title}.)
(Campaign {CAMPAIGN}; accepted anchor campaign {anchor.CAMPAIGN} attempt {attempt}.)
(No probing commands. No file output. No tool, TLO, TCPC, WCS, or gate changes.)
(Operator owns Cycle Start, Feed Hold, Abort, recovery, and every clearance decision.)
(Start homed and enabled at B0 C0 with T{spec.tool}/H{spec.tool}, TCPC on, TWP clear,)
(spindle stopped, and the probe ball within 3 mm of the accepted top-clear point.)
(The path visits the fixed top point, sign-aware upper-U side, -V side, and +V side.)
(Every side approach uses a W-offset overhead waypoint before its 4 mm start clearance.)
(Positive and negative B use paired pose grids and the same uninterrupted clearance profile.)
(Frozen primary SHA-256: {primary_digest})
(Frozen verification SHA-256: {verification_digest})

G21 G17 G40 G64 P0.001 G80 G90 G94

o<preview_guard> if [#<_task> EQ 0]
  M2
o<preview_guard> endif

#500 = {spec.tool:.1f}       (exact live tool)
#501 = {spec.length:.6f}  (exact Z tool length)
#502 = {spec.calibration_offset:.6f}    (ring-qualified probe offset)
#503 = {spec.effective_radius:.6f}   (sphere plus effective probe radius)
#504 = {spec.effective_radius + 5.0:.6f}   (top-clear radius)
#505 = {spec.effective_radius + 4.0:.6f}   (side-start radius)
#506 = 1200.0    (linear positioning feed, mm/min)
#507 = 200.0     (rotary index feed, deg/min)
#508 = 25.0      (machine-Z transit lift, mm)
#509 = {spec.pose_count:.1f}      (exact pose count)
#510 = 0.0       (completed pose sequence)
#511 = 0.0       (previous B)
#512 = 0.0       (previous C)
#700 = {center[0]:.6f}   (accepted absolute sphere center X)
#701 = {center[1]:.6f}   (accepted absolute sphere center Y)
#702 = {center[2]:.6f}   (accepted absolute sphere center Z)
#703 = {attempt:.1f}       (accepted anchor attempt)
#704 = {CAMPAIGN:.1f} (frozen measurement campaign)

o<tcpc_envelope_coordinate_guard> sub
  o<envelope_wcs_index_range> if [[#5220 LT 0.5] OR [#5220 GT 9.5] OR [ABS[#5220 - FIX[#5220]] GT 0.000001]]
    (abort, Envelope requires a valid integral active WCS index)
  o<envelope_wcs_index_range> endif
  o<envelope_wcs_index_unchanged> if [ABS[#5220 - #760] GT 0.000001]
    (abort, Active WCS changed during the envelope; reload the program)
  o<envelope_wcs_index_unchanged> endif
  o<envelope_g52_g92_enable_clear> if [ABS[#5210] GT 0.0001]
    (abort, Envelope requires G52 and G92 disabled)
  o<envelope_g52_g92_enable_clear> endif
  o<envelope_g52_g92_xyz_clear> if [[ABS[#5211] GT 0.0001] OR [ABS[#5212] GT 0.0001] OR [ABS[#5213] GT 0.0001]]
    (abort, Envelope requires XYZ G52 and G92 offsets zero)
  o<envelope_g52_g92_xyz_clear> endif
  o<envelope_g52_g92_abc_clear> if [[ABS[#5214] GT 0.0001] OR [ABS[#5215] GT 0.0001] OR [ABS[#5216] GT 0.0001]]
    (abort, Envelope requires ABC G52 and G92 offsets zero)
  o<envelope_g52_g92_abc_clear> endif
  o<envelope_g52_g92_uvw_clear> if [[ABS[#5217] GT 0.0001] OR [ABS[#5218] GT 0.0001] OR [ABS[#5219] GT 0.0001]]
    (abort, Envelope requires UVW G52 and G92 offsets zero)
  o<envelope_g52_g92_uvw_clear> endif
  o<envelope_wcs_rotary_clear> if [[ABS[#[5205 + [20 * #5220]]] GT 0.0001] OR [ABS[#[5206 + [20 * #5220]]] GT 0.0001]]
    (abort, Envelope requires active WCS B and C offsets zero)
  o<envelope_wcs_rotary_clear> endif
  o<envelope_wcs_rotation_clear> if [ABS[#[5210 + [20 * #5220]]] GT 0.0001]
    (abort, Envelope requires zero active WCS XY rotation)
  o<envelope_wcs_rotation_clear> endif
  o<envelope_wcs_offsets_a> if [[ABS[#[5201 + [20 * #5220]] - #761] GT 0.0001] OR [ABS[#[5202 + [20 * #5220]] - #762] GT 0.0001] OR [ABS[#[5203 + [20 * #5220]] - #763] GT 0.0001] OR [ABS[#[5204 + [20 * #5220]] - #764] GT 0.0001]]
    (abort, Active WCS XYZ or A offset changed during the envelope)
  o<envelope_wcs_offsets_a> endif
  o<envelope_wcs_offsets_b> if [[ABS[#[5205 + [20 * #5220]] - #765] GT 0.0001] OR [ABS[#[5206 + [20 * #5220]] - #766] GT 0.0001] OR [ABS[#[5207 + [20 * #5220]] - #767] GT 0.0001]]
    (abort, Active WCS B C or U offset changed during the envelope)
  o<envelope_wcs_offsets_b> endif
  o<envelope_wcs_offsets_c> if [[ABS[#[5208 + [20 * #5220]] - #768] GT 0.0001] OR [ABS[#[5209 + [20 * #5220]] - #769] GT 0.0001] OR [ABS[#[5210 + [20 * #5220]] - #770] GT 0.0001]]
    (abort, Active WCS V W or rotation changed during the envelope)
  o<envelope_wcs_offsets_c> endif
o<tcpc_envelope_coordinate_guard> endsub

o<tcpc_envelope_hold_position_guard> sub
  o<envelope_hold_xyz_unchanged> if [[ABS[#<_abs_x> - #771] GT 0.001] OR [ABS[#<_abs_y> - #772] GT 0.001] OR [ABS[#<_abs_z> - #773] GT 0.001]]
    (abort, XYZ changed during an envelope hold; reload and re-establish the reviewed start)
  o<envelope_hold_xyz_unchanged> endif
o<tcpc_envelope_hold_position_guard> endsub

o<tcpc_envelope_live_guard> sub
  #<guard_target_b> = #1
  #<guard_target_c> = #2
  M66 E0 L0
  o<tcpc_envelope_coordinate_guard> call
  o<envelope_tool_contract> if [[ABS[#500 - {spec.tool:.1f}] GT 0.000001] OR [ABS[#501 - {spec.length:.6f}] GT 0.000001] OR [ABS[#502 - {spec.calibration_offset:.6f}] GT 0.000001]]
    (abort, Embedded tool or calibration contract changed during the envelope)
  o<envelope_tool_contract> endif
  o<envelope_geometry_contract> if [[ABS[#503 - {spec.effective_radius:.6f}] GT 0.000001] OR [ABS[#504 - {spec.effective_radius + 5.0:.6f}] GT 0.000001] OR [ABS[#505 - {spec.effective_radius + 4.0:.6f}] GT 0.000001]]
    (abort, Embedded sphere clearance geometry changed during the envelope)
  o<envelope_geometry_contract> endif
  o<envelope_motion_contract> if [[ABS[#506 - 1200.0] GT 0.000001] OR [ABS[#507 - 200.0] GT 0.000001] OR [ABS[#508 - 25.0] GT 0.000001] OR [ABS[#509 - {spec.pose_count:.1f}] GT 0.000001]]
    (abort, Embedded feed lift or pose-count contract changed during the envelope)
  o<envelope_motion_contract> endif
  o<envelope_center_contract_a> if [[ABS[#700 - {center[0]:.6f}] GT 0.000001] OR [ABS[#701 - {center[1]:.6f}] GT 0.000001] OR [ABS[#702 - {center[2]:.6f}] GT 0.000001]]
    (abort, Accepted absolute sphere center changed during the envelope)
  o<envelope_center_contract_a> endif
  o<envelope_center_contract_b> if [[ABS[#703 - {attempt:.1f}] GT 0.000001] OR [ABS[#704 - {CAMPAIGN:.1f}] GT 0.000001]]
    (abort, Accepted anchor identity changed during the envelope)
  o<envelope_center_contract_b> endif
  o<envelope_machine_on> if [#<_hal[halui.machine.is-on]> LT 0.5]
    (abort, Envelope requires the machine enabled)
  o<envelope_machine_on> endif
  o<envelope_all_homed> if [[#<_hal[joint.0.homed]> + #<_hal[joint.1.homed]> + #<_hal[joint.2.homed]> + #<_hal[joint.3.homed]> + #<_hal[joint.4.homed]>] LT 4.5]
    (abort, Envelope requires all five joints homed)
  o<envelope_all_homed> endif
  o<envelope_spindle_off> if [#<_hal[spindle.0.on]> GT 0.5]
    (abort, Envelope requires the spindle stopped)
  o<envelope_spindle_off> endif
  o<envelope_tool_live> if [ABS[#<_hal[iocontrol.0.tool-number]> - #500] GT 0.1]
    (abort, Live tool number does not match this envelope)
  o<envelope_tool_live> endif
  o<envelope_motion_tlo_live> if [ABS[#<_hal[motion.tooloffset.z]> - #501] GT 0.002]
    (abort, Live motion Z tool offset does not match this envelope)
  o<envelope_motion_tlo_live> endif
  o<envelope_halui_tlo_live> if [ABS[#<_hal[halui.tool.length_offset.z]> - #501] GT 0.002]
    (abort, Live HALUI Z tool offset does not match this envelope)
  o<envelope_halui_tlo_live> endif
  o<envelope_kins_tlo_live> if [ABS[#<_hal[headheadkins.active-tool-offset.z]> - #501] GT 0.002]
    (abort, Live kinematics Z tool offset does not match this envelope)
  o<envelope_kins_tlo_live> endif
  o<envelope_tlo_xy_live> if [[ABS[#<_hal[motion.tooloffset.x]>] GT 0.002] OR [ABS[#<_hal[motion.tooloffset.y]>] GT 0.002]]
    (abort, Envelope requires zero active X and Y tool offsets)
  o<envelope_tlo_xy_live> endif
  o<envelope_tlo_abc_live> if [[ABS[#<_hal[motion.tooloffset.a]>] GT 0.002] OR [ABS[#<_hal[motion.tooloffset.b]>] GT 0.002] OR [ABS[#<_hal[motion.tooloffset.c]>] GT 0.002]]
    (abort, Envelope requires zero active A B and C tool offsets)
  o<envelope_tlo_abc_live> endif
  o<envelope_tlo_uvw_live> if [[ABS[#<_hal[motion.tooloffset.u]>] GT 0.002] OR [ABS[#<_hal[motion.tooloffset.v]>] GT 0.002] OR [ABS[#<_hal[motion.tooloffset.w]>] GT 0.002]]
    (abort, Envelope requires zero active U V and W tool offsets)
  o<envelope_tlo_uvw_live> endif
  o<envelope_tcpc_live> if [#<_hal[headheadtwp.tcpc_enabled]> LT 0.5]
    (abort, Envelope requires TCPC active)
  o<envelope_tcpc_live> endif
  o<envelope_twp_clear_live> if [[#<_hal[headheadtwp.active]> + #<_hal[headheadtwp.motion_enabled]> + #<_hal[headheadtwp.valid]>] GT 0.5]
    (abort, Envelope requires TWP active motion and valid states clear)
  o<envelope_twp_clear_live> endif
  o<envelope_ssi_valid_live> if [[#<_hal[b-ssi-invalid]> + #<_hal[c-ssi-invalid]>] GT 0.5]
    (abort, Envelope requires valid B and C SSI feedback)
  o<envelope_ssi_valid_live> endif
  o<envelope_correction_live> if [#<_hal[headheadkins.sim-bharm-enable]> LT 0.5]
    (abort, Envelope requires the fitted persistent correction enabled)
  o<envelope_correction_live> endif
  o<envelope_probe_gates_clear> if [[#<_hal[motion.digital-out-00]> GT 0.5] OR [#<_hal[motion.digital-out-01]> GT 0.5]]
    (abort, Envelope requires both probe gate requests clear)
  o<envelope_probe_gates_clear> endif

  #<b_cmd_error> = ABS[[[#<_hal[headheadtwp.current_joint_b]> - #<guard_target_b> + 540.0] MOD 360.0] - 180.0]
  #<b_fb_error> = ABS[[[#<_hal[joint.3.pos-fb]> - #<guard_target_b> + 540.0] MOD 360.0] - 180.0]
  #<b_ssi_error> = ABS[[[#<_hal[b-ssi-zeroed-position]> - #<guard_target_b> + 540.0] MOD 360.0] - 180.0]
  #<c_cmd_error> = ABS[[[#<_hal[headheadtwp.current_joint_c]> - #<guard_target_c> + 540.0] MOD 360.0] - 180.0]
  #<c_fb_error> = ABS[[[#<_hal[joint.4.pos-fb]> - #<guard_target_c> + 540.0] MOD 360.0] - 180.0]
  (The physical C SSI zeroed signal has the opposite polarity to joint C.)
  #<c_ssi_error> = ABS[[[#<_hal[c-ssi-zeroed-position]> + #<guard_target_c> + 540.0] MOD 360.0] - 180.0]
  o<envelope_b_pose_live> if [[#<b_cmd_error> GT 0.01] OR [#<b_fb_error> GT 0.01] OR [#<b_ssi_error> GT 0.01]]
    (abort, B command feedback or SSI is outside envelope pose tolerance)
  o<envelope_b_pose_live> endif
  o<envelope_c_pose_live> if [[#<c_cmd_error> GT 0.01] OR [#<c_fb_error> GT 0.01] OR [#<c_ssi_error> GT 0.01]]
    (abort, C command feedback or SSI is outside envelope pose tolerance)
  o<envelope_c_pose_live> endif
o<tcpc_envelope_live_guard> endsub

o<tcpc_envelope_pose> sub
  #<slot> = #1
  #<target_b> = #2
  #<target_c> = #3

  o<envelope_pose_order> if [ABS[#<slot> - [#510 + 1.0]] GT 0.000001]
    (abort, Envelope pose sequence is not contiguous)
  o<envelope_pose_order> endif

  o<envelope_later_pose> if [#510 GT 0.5]
    o<tcpc_envelope_live_guard> call [#511] [#512]
    #<current_w_x> = [-SIN[#511] * COS[#512]]
    #<current_w_y> = [-SIN[#511] * SIN[#512]]
    #<current_w_z> = [-COS[#511]]
    #<expected_top_abs_x> = [#700 - [#<current_w_x> * #504]]
    #<expected_top_abs_y> = [#701 - [#<current_w_y> * #504]]
    #<expected_top_abs_z> = [#702 - [#<current_w_z> * #504]]
    o<envelope_previous_top_required> if [[ABS[#<_abs_x> - #<expected_top_abs_x>] GT 0.010] OR [ABS[#<_abs_y> - #<expected_top_abs_y>] GT 0.010] OR [ABS[#<_abs_z> - #<expected_top_abs_z>] GT 0.010]]
      (abort, Envelope is not at the previous pose top-clear point)
    o<envelope_previous_top_required> endif

    G90
    F#506
    #<safe_z> = [#<_z> + #508]
    G1 Z#<safe_z>
    o<tcpc_envelope_live_guard> call [#511] [#512]

    F#507
    o<envelope_sign_change_zero_transit> if [[[#511 * #<target_b>] LT -0.01] AND [ABS[#512] LT 0.05] AND [ABS[#<target_c>] LT 0.05]]
      G1 B0 C0
      o<tcpc_envelope_live_guard> call [0.0] [0.0]
    o<envelope_sign_change_zero_transit> endif
    G1 B#<target_b> C#<target_c>
    o<tcpc_envelope_live_guard> call [#<target_b>] [#<target_c>]

    #540 = [#<_abs_x> - #<_x>]
    #541 = [#<_abs_y> - #<_y>]
    #542 = [#<_abs_z> - #<_z>]
    #<transit_w_x> = [-SIN[#<target_b>] * COS[#<target_c>]]
    #<transit_w_y> = [-SIN[#<target_b>] * SIN[#<target_c>]]
    #<transit_w_z> = [-COS[#<target_b>]]
    #<transit_top_x> = [#700 - #540 - [#<transit_w_x> * #504]]
    #<transit_top_y> = [#701 - #541 - [#<transit_w_y> * #504]]
    #<transit_top_z> = [#702 - #542 - [#<transit_w_z> * #504]]
    F#506
    G1 X#<transit_top_x> Y#<transit_top_y>
    o<tcpc_envelope_live_guard> call [#<target_b>] [#<target_c>]

    F200.0
    G1 Z#<transit_top_z>
    F#506
  o<envelope_later_pose> else
    o<envelope_first_pose_zero> if [[ABS[#<target_b>] GT 0.000001] OR [ABS[#<target_c>] GT 0.000001]]
      (abort, First envelope pose must be B0 C0)
    o<envelope_first_pose_zero> endif
    o<tcpc_envelope_live_guard> call [0.0] [0.0]
    #540 = [#<_abs_x> - #<_x>]
    #541 = [#<_abs_y> - #<_y>]
    #542 = [#<_abs_z> - #<_z>]
  o<envelope_later_pose> endif

  #<w_x> = [-SIN[#<target_b>] * COS[#<target_c>]]
  #<w_y> = [-SIN[#<target_b>] * SIN[#<target_c>]]
  #<w_z> = [-COS[#<target_b>]]
  #<u_x> = [COS[#<target_b>] * COS[#<target_c>]]
  #<u_y> = [COS[#<target_b>] * SIN[#<target_c>]]
  #<u_z> = [-SIN[#<target_b>]]
  #<v_x> = [-SIN[#<target_c>]]
  #<v_y> = [COS[#<target_c>]]
  #<v_z> = 0.0

  #<upper_sign> = -1.0
  o<negative_b_upper_u> if [#<target_b> LT -0.001]
    #<upper_sign> = 1.0
  o<negative_b_upper_u> endif

  #<top_x> = [#700 - #540 - [#<w_x> * #504]]
  #<top_y> = [#701 - #541 - [#<w_y> * #504]]
  #<top_z> = [#702 - #542 - [#<w_z> * #504]]
  #<u_start_x> = [#700 - #540 + [#<upper_sign> * #<u_x> * #505]]
  #<u_start_y> = [#701 - #541 + [#<upper_sign> * #<u_y> * #505]]
  #<u_start_z> = [#702 - #542 + [#<upper_sign> * #<u_z> * #505]]
  #<u_clear_x> = [#<u_start_x> - [#<w_x> * #504]]
  #<u_clear_y> = [#<u_start_y> - [#<w_y> * #504]]
  #<u_clear_z> = [#<u_start_z> - [#<w_z> * #504]]
  #<vm_start_x> = [#700 - #540 - [#<v_x> * #505]]
  #<vm_start_y> = [#701 - #541 - [#<v_y> * #505]]
  #<vm_start_z> = [#702 - #542 - [#<v_z> * #505]]
  #<vm_clear_x> = [#<vm_start_x> - [#<w_x> * #504]]
  #<vm_clear_y> = [#<vm_start_y> - [#<w_y> * #504]]
  #<vm_clear_z> = [#<vm_start_z> - [#<w_z> * #504]]
  #<vp_start_x> = [#700 - #540 + [#<v_x> * #505]]
  #<vp_start_y> = [#701 - #541 + [#<v_y> * #505]]
  #<vp_start_z> = [#702 - #542 + [#<v_z> * #505]]
  #<vp_clear_x> = [#<vp_start_x> - [#<w_x> * #504]]
  #<vp_clear_y> = [#<vp_start_y> - [#<w_y> * #504]]
  #<vp_clear_z> = [#<vp_start_z> - [#<w_z> * #504]]

  G90
  F#506
  G1 X#<top_x> Y#<top_y> Z#<top_z>
  o<tcpc_envelope_live_guard> call [#<target_b>] [#<target_c>]
  G1 X#<u_clear_x> Y#<u_clear_y> Z#<u_clear_z>
  G1 X#<u_start_x> Y#<u_start_y> Z#<u_start_z>
  o<tcpc_envelope_live_guard> call [#<target_b>] [#<target_c>]
  G1 X#<u_clear_x> Y#<u_clear_y> Z#<u_clear_z>
  G1 X#<top_x> Y#<top_y> Z#<top_z>
  G1 X#<vm_clear_x> Y#<vm_clear_y> Z#<vm_clear_z>
  G1 X#<vm_start_x> Y#<vm_start_y> Z#<vm_start_z>
  o<tcpc_envelope_live_guard> call [#<target_b>] [#<target_c>]
  G1 X#<vm_clear_x> Y#<vm_clear_y> Z#<vm_clear_z>
  G1 X#<top_x> Y#<top_y> Z#<top_z>
  G1 X#<vp_clear_x> Y#<vp_clear_y> Z#<vp_clear_z>
  G1 X#<vp_start_x> Y#<vp_start_y> Z#<vp_start_z>
  o<tcpc_envelope_live_guard> call [#<target_b>] [#<target_c>]
  G1 X#<vp_clear_x> Y#<vp_clear_y> Z#<vp_clear_z>
  G1 X#<top_x> Y#<top_y> Z#<top_z>
  o<tcpc_envelope_live_guard> call [#<target_b>] [#<target_c>]

  #510 = #<slot>
  #511 = #<target_b>
  #512 = #<target_c>
o<tcpc_envelope_pose> endsub

(MAIN EXECUTION)
o<envelope_initial_wcs_index> if [[#5220 LT 0.5] OR [#5220 GT 9.5] OR [ABS[#5220 - FIX[#5220]] GT 0.000001]]
  (abort, Envelope requires a valid integral active WCS index)
o<envelope_initial_wcs_index> endif
#760 = #5220
#761 = #[5201 + [20 * #760]]
#762 = #[5202 + [20 * #760]]
#763 = #[5203 + [20 * #760]]
#764 = #[5204 + [20 * #760]]
#765 = #[5205 + [20 * #760]]
#766 = #[5206 + [20 * #760]]
#767 = #[5207 + [20 * #760]]
#768 = #[5208 + [20 * #760]]
#769 = #[5209 + [20 * #760]]
#770 = #[5210 + [20 * #760]]
#771 = #<_abs_x>
#772 = #<_abs_y>
#773 = #<_abs_z>
(MSG, Confirm T{spec.tool}/H{spec.tool} TCPC B0 C0 spindle off accepted sphere center and all clearances. No motion has occurred.)
M0

o<tcpc_envelope_hold_position_guard> call
o<tcpc_envelope_live_guard> call [0.0] [0.0]
#<accepted_top_x> = #700
#<accepted_top_y> = #701
#<accepted_top_z> = [#702 + #504]
#<initial_distance> = SQRT[[[#<_abs_x> - #<accepted_top_x>] * [#<_abs_x> - #<accepted_top_x>]] + [[#<_abs_y> - #<accepted_top_y>] * [#<_abs_y> - #<accepted_top_y>]] + [[#<_abs_z> - #<accepted_top_z>] * [#<_abs_z> - #<accepted_top_z>]]]
o<envelope_initial_position_near> if [#<initial_distance> GT 3.0]
  (abort, Start is more than 3 mm from the accepted B0 C0 top-clear point)
o<envelope_initial_position_near> endif

{calls}

o<envelope_exact_count> if [ABS[#510 - #509] GT 0.000001]
  (abort, Envelope did not execute the exact frozen pose count)
o<envelope_exact_count> endif
o<tcpc_envelope_live_guard> call [0.0] [0.0]
(MSG, Relocated-sphere T{spec.tool} no-contact envelope complete at B0 C0 top clearance.)
M2
"""
    return program


def validate_rendered_program(
    text: str,
    spec: ToolSpec,
    poses: Sequence[reach.Pose],
) -> None:
    validate_signed_b_pairing(poses)
    upper = text.upper()
    if "G38" in upper:
        raise GenerationError(f"T{spec.tool} envelope contains a probe command")
    if re.search(r"\(LOG(?:APPEND|CLOSE|OPEN)?\b", upper):
        raise GenerationError(f"T{spec.tool} envelope contains a file-output directive")
    if re.search(r"^\s*G4\b", upper, flags=re.MULTILINE):
        raise GenerationError(f"T{spec.tool} envelope contains a dwell")
    if re.search(r"^\s*M6[45]\b", upper, flags=re.MULTILINE):
        raise GenerationError(f"T{spec.tool} envelope changes a probe gate output")

    call_pattern = re.compile(
        r"^o<tcpc_envelope_pose> call \[([-+0-9.]+)\] \[([-+0-9.]+)\] "
        r"\[([-+0-9.]+)\]$",
        flags=re.MULTILINE,
    )
    calls = [tuple(float(value) for value in match) for match in call_pattern.findall(text)]
    expected_calls = [
        (
            float(pose.slot),
            pose.b_deg,
            pose.c_deg,
        )
        for pose in poses
    ]
    if calls != expected_calls or len(calls) != spec.pose_count:
        raise GenerationError(f"T{spec.tool} envelope call order/count differs from its exact grid")

    if len(re.findall(r"^\s*M0\s*$", text, flags=re.MULTILINE)) != 1:
        raise GenerationError(f"T{spec.tool} source must have exactly one initial M0")
    if "hold_flag" in text or "envelope_negative_block_hold" in text:
        raise GenerationError(f"T{spec.tool} source contains a per-pose clearance hold")
    main = text.split("(MAIN EXECUTION)", 1)[1]
    before_initial_hold = main.split("\nM0\n", 1)[0]
    if re.search(r"^\s*G(?:0|1)\b", before_initial_hold, flags=re.MULTILINE):
        raise GenerationError(f"T{spec.tool} envelope can move before its initial M0")

    required = (
        "#508 = 25.0",
        f"#509 = {spec.pose_count:.1f}",
        f"#500 = {spec.tool:.1f}",
        f"#501 = {spec.length:.6f}",
        f"#503 = {spec.effective_radius:.6f}",
        "o<envelope_tool_contract> if",
        "o<envelope_geometry_contract> if",
        "o<envelope_motion_contract> if",
        "o<envelope_center_contract_a> if",
        "o<negative_b_upper_u> if [#<target_b> LT -0.001]",
        "G1 Z#<safe_z>",
        "G1 B0 C0",
        "G1 B#<target_b> C#<target_c>",
        "#<u_clear_x>",
        "#<u_start_x>",
        "#<vm_clear_x>",
        "#<vm_start_x>",
        "#<vp_clear_x>",
        "#<vp_start_x>",
        "#<_hal[halui.machine.is-on]>",
        "#<_hal[joint.4.homed]>",
        "#<_hal[spindle.0.on]>",
        "#<_hal[iocontrol.0.tool-number]>",
        "#<_hal[motion.tooloffset.z]>",
        "#<_hal[headheadkins.active-tool-offset.z]>",
        "#<_hal[headheadtwp.tcpc_enabled]>",
        "#<_hal[b-ssi-invalid]>",
        "#<_hal[c-ssi-invalid]>",
        "#<_hal[c-ssi-zeroed-position]> + #<guard_target_c>",
    )
    missing = [snippet for snippet in required if snippet not in text]
    if missing:
        raise GenerationError(f"T{spec.tool} envelope is missing contracts: {missing!r}")

    low_b = {5.0, 10.0, 15.0}
    low_c = {0.0, 45.0, 90.0, 180.0, 225.0, 270.0}
    high_b = {30.0, 45.0, 60.0, 90.0}
    quadrant_c = {0.0, 90.0, 180.0, 270.0}
    for pose in poses:
        b_abs = round(abs(pose.b_deg), 9)
        c_norm = round(pose.c_deg % 360.0, 9)
        if b_abs <= 0.001:
            continue
        if c_norm in {135.0, 315.0}:
            raise GenerationError(f"T{spec.tool} tilted pose enters a known post-collision sector")
        if b_abs in low_b and c_norm not in low_c:
            raise GenerationError(f"T{spec.tool} low-B pose is outside the reviewed C45 subset")
        if b_abs in high_b and c_norm not in quadrant_c:
            raise GenerationError(f"T{spec.tool} B30-or-higher pose must use C90 steps")
        if b_abs not in low_b | high_b:
            raise GenerationError(f"T{spec.tool} pose uses unsupported signed B magnitude {b_abs:g}")


def self_test() -> None:
    reach.validate_model_constants()
    synthetic_center = (1024.250000, 844.750000, -302.500000)
    primary_poses = reach.grid()
    verification_poses = reach.verification_grid()
    rendered = (
        (
            T4_SPEC,
            primary_poses,
            render_program(
                T4_SPEC,
                primary_poses,
                synthetic_center,
                7,
                "a" * 64,
                "b" * 64,
            ),
        ),
        (
            T3_SPEC,
            verification_poses,
            render_program(
                T3_SPEC,
                verification_poses,
                synthetic_center,
                7,
                "a" * 64,
                "b" * 64,
            ),
        ),
    )
    for spec, poses, text in rendered:
        validate_rendered_program(text, spec, poses)
        assert f"#700 = {synthetic_center[0]:.6f}" in text
        assert f"#701 = {synthetic_center[1]:.6f}" in text
        assert f"#702 = {synthetic_center[2]:.6f}" in text

    validate_signed_b_pairing(primary_poses)
    validate_signed_b_pairing(verification_poses)


def write_atomically(outputs: Sequence[tuple[Path, str]]) -> None:
    resolved = [path.resolve() for path, _ in outputs]
    if len(set(resolved)) != len(resolved):
        raise GenerationError("T4 and T3 output paths must be different")
    staged: list[tuple[Path, Path]] = []
    try:
        for path, text in outputs:
            if not path.parent.is_dir():
                raise GenerationError(f"output directory does not exist: {path.parent}")
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="ascii",
                newline="\n",
                prefix=f".{path.name}.",
                suffix=".tmp",
                dir=path.parent,
                delete=False,
            ) as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
                staged.append((Path(handle.name), path))
        for temporary, destination in staged:
            os.replace(temporary, destination)
    finally:
        for temporary, _ in staged:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor-results", type=Path, default=anchor.DEFAULT_RESULTS)
    parser.add_argument("--anchor-state", type=Path, default=anchor.DEFAULT_STATE)
    parser.add_argument("--t4-output", type=Path, default=DEFAULT_T4_OUTPUT)
    parser.add_argument("--t3-output", type=Path, default=DEFAULT_T3_OUTPUT)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        print("self-test: PASS")
        return 0

    try:
        acceptance, primary_poses, verification_poses = validate_combined_reachability(
            args.anchor_results,
            args.anchor_state,
        )
        t4_text = render_program(
            T4_SPEC,
            primary_poses,
            acceptance.center,
            acceptance.attempt,
            acceptance.primary_digest,
            acceptance.verification_digest,
        )
        t3_text = render_program(
            T3_SPEC,
            verification_poses,
            acceptance.center,
            acceptance.attempt,
            acceptance.primary_digest,
            acceptance.verification_digest,
        )
        validate_rendered_program(t4_text, T4_SPEC, primary_poses)
        validate_rendered_program(t3_text, T3_SPEC, verification_poses)
        write_atomically(((args.t4_output, t4_text), (args.t3_output, t3_text)))
    except (OSError, ValueError, KeyError, AssertionError) as exc:
        print(f"envelope generation refused: {exc}", file=sys.stderr)
        return 1

    print("relocated-sphere envelope generation: PASS")
    print(
        "accepted center: "
        f"X{acceptance.center[0]:.6f} Y{acceptance.center[1]:.6f} "
        f"Z{acceptance.center[2]:.6f}; anchor attempt {acceptance.attempt}"
    )
    print(
        f"combined remaining linear margin: {acceptance.remaining_linear_margin:.6f} mm; "
        f"B/C margins: {acceptance.b_margin:.6f}/{acceptance.c_margin:.6f} deg"
    )
    print(f"T4 envelope: {args.t4_output}")
    print(f"T3 envelope: {args.t3_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
