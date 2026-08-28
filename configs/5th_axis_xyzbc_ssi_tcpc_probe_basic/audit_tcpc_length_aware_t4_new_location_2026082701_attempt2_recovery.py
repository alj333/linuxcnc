#!/usr/bin/env python3
"""File-only preflight for the frozen T4 new-location recovery."""

from __future__ import annotations

import csv
import hashlib
import re
import sys
from pathlib import Path


DEFAULT_ROOT = Path("/home/cnc5/linuxcnc-dev")
RUNNER_REL = Path("nc_files/calibration/tcpc_length_aware_t4_new_location_2026082701_attempt2_recovery.ngc")
RUNNER_SHA256 = "c027a0bab19f403e5e625f01fb50d6d050b51188fa0a0885dbaa795035b5c758"
SEAL_REL = Path("configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/calibration_runs/20260827_1754_campaign2026082701_t4_new_location_attempt1_partial_gap_abort_seq18")
SEAL_SUMS_SHA256 = "2cef1968a26d61cf3f14c6a8807541ce3462f92a8927e6a44e643901234ac6f2"
CFG_REL = Path("configs/5th_axis_xyzbc_ssi_tcpc_probe_basic")
OLD_PREFIX = "tcpc-length-aware-t4-new-location-2026082701-attempt1"
NEW_PREFIX = "tcpc-length-aware-t4-new-location-2026082701-attempt2-recovery"

HEADERS = {
    "results": "schema_version,campaign_id,stage_mode,attempt_id,sample_seq,block_id,anchor_seq,is_closure,contact_count,u_method_code,abs_b_deg,abs_c_deg,live_tool_number,expected_tool_length_mm,probe_calibration_offset_mm,probe_diameter_mm,effective_contact_radius_mm,center_abs_x_mm,center_abs_y_mm,center_abs_z_mm,u_center_correction_mm,v_center_correction_mm,center_correction_norm_mm,v_corrected_diameter_mm,pass_center_delta_mm,w_contact_radial_residual_mm,u_contact_radial_residual_mm,v_minus_contact_radial_residual_mm,v_plus_contact_radial_residual_mm,w_travel_mm,u_travel_mm,v_minus_travel_mm,v_plus_travel_mm",
    "state": "schema_version,campaign_id,stage_mode,attempt_id,sample_seq,abs_b_deg,abs_c_deg,persistent_correction_enabled,tcpc_enabled,twp_active,twp_motion_enabled,twp_valid,b_ssi_invalid,c_ssi_invalid,motion_tooloffset_z_mm,halui_tool_length_offset_z_mm,kins_active_tool_offset_z_mm,joint_b_cmd_deg,joint_b_fb_deg,joint_c_cmd_deg,joint_c_fb_deg,b_ssi_zeroed_deg,c_ssi_zeroed_deg,accepted_endpoint_abs_x_mm,accepted_endpoint_abs_y_mm,accepted_endpoint_abs_z_mm,joint_0_motor_pos_cmd_mm,joint_0_motor_pos_fb_mm,joint_0_motor_following_error_fb_minus_cmd_mm,joint_1_motor_pos_cmd_mm,joint_1_motor_pos_fb_mm,joint_1_motor_following_error_fb_minus_cmd_mm,joint_2_motor_pos_cmd_mm,joint_2_motor_pos_fb_mm,joint_2_motor_following_error_fb_minus_cmd_mm",
    "model-state": "schema_version,campaign_id,stage_mode,attempt_id,sample_seq,model_id,expected_model_id,configured,valid,fault_code,q,evaluated_b_deg,evaluated_c_deg,evaluated_length_mm,diff_offset_x_mm,diff_offset_y_mm,diff_offset_z_mm,diff_offset_norm_mm,empirical_offset_x_mm,empirical_offset_y_mm,empirical_offset_z_mm,empirical_offset_norm_mm",
    "closures": "schema_version,campaign_id,stage_mode,attempt_id,block_id,open_sample_seq,close_sample_seq,abs_b_deg,abs_c_deg,closure_dx_mm,closure_dy_mm,closure_dz_mm,closure_norm_mm,limit_mm,pass",
    "contact-trace": "schema_version,campaign_id,stage_mode,attempt_id,global_seq,abs_b_deg,abs_c_deg,acquisition_try,pass_id,contact_id,pre_raw_count,pre_mux_count,pre_gated_count,post_raw_count,post_mux_count,post_gated_count,ready_raw_count,ready_mux_count,ready_gated_count,probe_result,travel_mm,raw_delta,mux_delta,gated_delta,repeat_raw_delta,repeat_mux_delta,repeat_gated_delta,extra_raw_minus_gated_delta,burst_flag,consistency_fault,release_fault,terminal_failure",
    "gap-trace": "schema_version,campaign_id,stage_mode,attempt_id,next_global_seq,abs_b_deg,abs_c_deg,acquisition_try,pass_id,contact_id,prior_ready_raw_count,prior_ready_mux_count,prior_ready_gated_count,current_pre_raw_count,current_pre_mux_count,current_pre_gated_count,gap_raw_delta,gap_mux_delta,gap_gated_delta,prior_contact_extra_delta,combined_extra_delta,burst_flag,consistency_fault,initial_baseline",
}


class Checks:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.passes = 0

    def require(self, condition: bool, message: str) -> None:
        if condition:
            self.passes += 1
        else:
            self.failures.append(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path, expected_header: str, checks: Checks) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="ascii", newline="") as handle:
            reader = csv.DictReader(handle)
            checks.require(reader.fieldnames == expected_header.split(","), f"wrong CSV header: {path}")
            return list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        checks.require(False, f"cannot read CSV {path}: {exc}")
        return []


def integer(row: dict[str, str], field: str) -> int:
    value = float(row[field])
    if not value.is_integer():
        raise ValueError(f"{field} is not integral: {value}")
    return int(value)


def identity_ok(rows: list[dict[str, str]], mode: int, attempt: int) -> bool:
    try:
        return all(
            integer(row, "campaign_id") == 2026082701
            and integer(row, "stage_mode") == mode
            and integer(row, "attempt_id") == attempt
            for row in rows
        )
    except (KeyError, ValueError):
        return False


def top_level_program(text: str) -> list[str]:
    # Parenthesized comments may span lines. Subroutine definitions are skipped
    # by the interpreter and are not pre-M0 execution-path motion.
    text = re.sub(r"\([^)]*\)", "", text, flags=re.S)
    result: list[str] = []
    in_sub = False
    for raw in text.splitlines():
        line = raw.strip()
        if re.match(r"^o<[^>]+>\s+sub\b", line, re.I):
            in_sub = True
            continue
        if in_sub and re.match(r"^o<[^>]+>\s+endsub\b", line, re.I):
            in_sub = False
            continue
        if line and not in_sub:
            result.append(line)
    return result


def check_runner(root: Path, checks: Checks) -> None:
    path = root / RUNNER_REL
    checks.require(path.is_file(), f"missing runner: {path}")
    if not path.is_file():
        return
    checks.require(sha256(path) == RUNNER_SHA256, "recovery runner SHA-256 changed")
    try:
        text = path.read_text(encoding="ascii")
    except (OSError, UnicodeError) as exc:
        checks.require(False, f"cannot read runner: {exc}")
        return

    top = top_level_program(text)
    holds = [line for line in top if re.fullmatch(r"M0", line, re.I)]
    optional_holds = [line for line in top if re.search(r"\bM1\b", line, re.I)]
    checks.require(len(holds) == 1, "runner must have exactly one top-level M0")
    checks.require(not optional_holds, "runner contains a top-level M1")
    if holds:
        pre_hold = top[: top.index(holds[0])]
        axis_motion = re.compile(r"\b(?:G0+|G1|G2|G3|G38(?:\.\d+)?)\b", re.I)
        checks.require(not any(axis_motion.search(line) for line in pre_hold), "axis/probe motion exists before the sole M0")

    body_match = re.search(
        r"o<run_relocated_t4_recovery>\s+if\b(?P<body>.*?)o<run_relocated_t4_recovery>\s+endif",
        text,
        flags=re.S | re.I,
    )
    checks.require(body_match is not None, "recovery body is missing")
    if not body_match:
        return
    body = body_match.group("body")

    b0 = re.findall(r"o<tcpc_primary_b0_sweep>\s+call\s+\[([-+0-9.]+)\]", body, re.I)
    low = re.findall(r"o<tcpc_primary_low_tilt_block>\s+call\s+\[([-+0-9.]+)\]", body, re.I)
    tilt = re.findall(r"o<tcpc_primary_tilt_block>\s+call\s+\[([-+0-9.]+)\]", body, re.I)
    direct = re.findall(r"o<tcpc_measure_pose>\s+call\s+\[([-+0-9.]+)\]\s+\[([-+0-9.]+)\]", body, re.I)
    checks.require([float(v) for v in b0] == [100.0, 200.0], "opening/closing B0 sweep topology changed")
    checks.require([float(v) for v in low] == [10.0, -10.0, 15.0, -15.0], "low-tilt recovery topology changed")
    checks.require([float(v) for v in tilt] == [30.0, -30.0, 45.0, -45.0, 60.0, -60.0, 90.0, -90.0], "high-tilt recovery topology changed")
    expected_direct = [(-5.0, c) for c in (0.0, 45.0, 90.0, 180.0, 225.0, 270.0, 0.0)] + [(0.0, 0.0)]
    checks.require([(float(b), float(c)) for b, c in direct] == expected_direct, "direct bridge/midpoint pose topology changed")
    checks.require(len(re.findall(r"#726\s*=\s*16\.0", body)) == 1, "canonical rows 10..16 skip marker changed")
    checks.require(9 + 7 + 4 * 7 + 4 * 5 + 1 + 4 * 5 + 9 == 94, "internal topology count error")

    required_literals = (
        "#711 = 36.0", "#715 = 2026082701.0", "#727 = 2.0", "#707 = 94.0",
        "#716 = 2.0", "#717 = 0.154742", "#516 = 229.407000", "#779 = 8.0",
        "call [2501.004768] [696.551145] [-302.567719] [3609.0] [9.0] [#726]",
        "call [2501.211649] [696.532630] [-302.571603] [3617.0] [17.0] [#726]",
        "ABS[#726 - 101.0]", "ABS[#788 - #707]", "ABS[#978 - 29.0]", "ABS[#973 - 752.0]",
    )
    for literal in required_literals:
        checks.require(literal in text, f"missing frozen runner invariant: {literal}")


def check_empty_outputs(root: Path, checks: Checks) -> None:
    for suffix, header in HEADERS.items():
        path = root / CFG_REL / f"{NEW_PREFIX}-{suffix}.csv"
        rows = read_csv(path, header, checks)
        checks.require(len(rows) == 0, f"recovery output is not header-only: {path}")


def check_seal(root: Path, checks: Checks) -> None:
    seal = root / SEAL_REL
    sums = seal / "SHA256SUMS"
    checks.require(sums.is_file(), f"missing sealed inventory: {sums}")
    if not sums.is_file():
        return
    checks.require(sha256(sums) == SEAL_SUMS_SHA256, "sealed SHA256SUMS root hash changed")
    try:
        lines = sums.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as exc:
        checks.require(False, f"cannot read sealed inventory: {exc}")
        return
    checks.require(len(lines) == 21, "sealed inventory must contain exactly 21 entries")

    inventory: dict[str, str] = {}
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  \./(.+)", line)
        checks.require(match is not None, f"malformed sealed inventory line: {line!r}")
        if not match:
            continue
        expected, rel = match.groups()
        rel_path = Path(rel)
        safe = not rel_path.is_absolute() and ".." not in rel_path.parts and rel not in inventory
        checks.require(safe, f"unsafe or duplicate sealed path: {rel}")
        if safe:
            inventory[rel] = expected

    disk_files: set[str] = set()
    for item in seal.rglob("*"):
        checks.require(not item.is_symlink(), f"symlink is forbidden in sealed archive: {item}")
        if item.is_file() and item != sums:
            disk_files.add(item.relative_to(seal).as_posix())
    checks.require(set(inventory) == disk_files, "sealed inventory and regular-file topology differ")
    for rel, expected in inventory.items():
        path = seal / rel
        checks.require(path.is_file() and sha256(path) == expected, f"sealed file hash mismatch: {rel}")

    data_dir = seal / "workspace" / CFG_REL
    tables: dict[str, list[dict[str, str]]] = {}
    for suffix, header in HEADERS.items():
        tables[suffix] = read_csv(data_dir / f"{OLD_PREFIX}-{suffix}.csv", header, checks)

    expected_counts = {
        "results": 17, "state": 17, "model-state": 17, "closures": 2,
        "contact-trace": 137, "gap-trace": 138,
    }
    for suffix, count in expected_counts.items():
        checks.require(len(tables[suffix]) == count, f"sealed {suffix} row count is not {count}")
        checks.require(identity_ok(tables[suffix], 35, 1), f"sealed {suffix} identity changed")

    canonical_poses = (
        [(0.0, c) for c in (0, 45, 90, 135, 180, 225, 270, 315, 0)]
        + [(5.0, c) for c in (0, 45, 90, 180, 225, 270, 0)]
        + [(-5.0, 0.0)]
    )
    for suffix in ("results", "state", "model-state"):
        rows = tables[suffix]
        try:
            seq = [integer(row, "sample_seq") for row in rows]
            poses = [(float(row["abs_b_deg"] if suffix != "model-state" else row["evaluated_b_deg"]),
                      float(row["abs_c_deg"] if suffix != "model-state" else row["evaluated_c_deg"])) for row in rows]
            checks.require(seq == list(range(1, 18)), f"sealed {suffix} sequence is not 1..17")
            checks.require(poses == canonical_poses, f"sealed {suffix} pose sequence changed")
        except (KeyError, ValueError):
            checks.require(False, f"sealed {suffix} contains invalid sequence/pose values")

    expected_keys = [(seq, p, c) for seq in range(1, 18) for p in (1, 2) for c in (1, 2, 3, 4)]
    contact = tables["contact-trace"]
    gap = tables["gap-trace"]
    try:
        contact_keys = [(integer(r, "global_seq"), integer(r, "pass_id"), integer(r, "contact_id")) for r in contact]
        gap_keys = [(integer(r, "next_global_seq"), integer(r, "pass_id"), integer(r, "contact_id")) for r in gap]
        checks.require(contact_keys == expected_keys + [(18, 1, 1)], "sealed contact transaction sequence changed")
        checks.require(gap_keys == expected_keys + [(18, 1, 1), (18, 1, 2)], "sealed gap transaction sequence changed")

        accepted_contacts = contact[:136]
        contact_semantics = all(
            integer(r, "probe_result") == 1
            and integer(r, "raw_delta") == integer(r, "mux_delta") == integer(r, "gated_delta") == 1
            and integer(r, "repeat_raw_delta") == integer(r, "repeat_mux_delta")
            and integer(r, "repeat_gated_delta") == 0
            and integer(r, "burst_flag") == integer(r, "consistency_fault") == integer(r, "release_fault") == integer(r, "terminal_failure") == 0
            for r in accepted_contacts
        )
        checks.require(contact_semantics, "accepted Attempt-1 pulse semantics changed")
        checks.require(all(integer(r, "gap_raw_delta") == integer(r, "gap_mux_delta") and integer(r, "gap_gated_delta") == 0 and integer(r, "burst_flag") == integer(r, "consistency_fault") == 0 for r in gap[:137]), "accepted Attempt-1 gap semantics changed")

        rejected_contact = contact[-1]
        checks.require(
            integer(rejected_contact, "raw_delta") == integer(rejected_contact, "mux_delta") == integer(rejected_contact, "gated_delta") == 1
            and integer(rejected_contact, "post_raw_count") == integer(rejected_contact, "ready_raw_count") == 709
            and integer(rejected_contact, "post_mux_count") == integer(rejected_contact, "ready_mux_count") == 709
            and integer(rejected_contact, "post_gated_count") == integer(rejected_contact, "ready_gated_count") == 225,
            "row-18 rejected-prefix W contact semantics changed",
        )
        abort = gap[-1]
        checks.require(
            integer(abort, "prior_ready_raw_count") == integer(abort, "prior_ready_mux_count") == 709
            and integer(abort, "prior_ready_gated_count") == 225
            and integer(abort, "current_pre_raw_count") == integer(abort, "current_pre_mux_count") == 713
            and integer(abort, "current_pre_gated_count") == 225
            and integer(abort, "gap_raw_delta") == integer(abort, "gap_mux_delta") == 4
            and integer(abort, "gap_gated_delta") == 0
            and integer(abort, "combined_extra_delta") == 4
            and integer(abort, "burst_flag") == 1
            and integer(abort, "consistency_fault") == 0
            and integer(abort, "initial_baseline") == 0,
            "row-18 four-raw/four-mux/zero-gated abort semantics changed",
        )
    except (KeyError, ValueError):
        checks.require(False, "sealed pulse traces contain invalid numeric fields")

    closures = tables["closures"]
    try:
        closure_shape = [
            (integer(r, "block_id"), integer(r, "open_sample_seq"), integer(r, "close_sample_seq"), integer(r, "pass"))
            for r in closures
        ]
        checks.require(closure_shape == [(100, 1, 9, 1), (5, 10, 16, 1)], "sealed closure sequence changed")
    except (KeyError, ValueError):
        checks.require(False, "sealed closure rows contain invalid values")


def main() -> int:
    if len(sys.argv) > 2:
        print(f"usage: {Path(sys.argv[0]).name} [repo-root]", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else DEFAULT_ROOT
    checks = Checks()
    checks.require(root.is_dir(), f"repository root does not exist: {root}")
    if root.is_dir():
        check_runner(root, checks)
        check_empty_outputs(root, checks)
        check_seal(root, checks)
    if checks.failures:
        print("T4 RECOVERY FILE PREFLIGHT: FAIL")
        for failure in checks.failures:
            print(f"FAIL: {failure}")
        return 1
    print(f"T4 RECOVERY FILE PREFLIGHT: PASS ({checks.passes} checks)")
    print("Composite mapping: sealed Attempt-1 rows 1..17 + recovery rows 18..101")
    print("This file-only result does not authorize Cycle Start.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
