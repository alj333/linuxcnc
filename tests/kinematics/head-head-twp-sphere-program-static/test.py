#!/usr/bin/env python3

import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs/5th_axis_xyzbc_ssi_tcpc_probe_basic"
PROGRAM = ROOT / "nc_files/calibration/twp_sphere_probe_stage1_t4.ngc"
FULL_CYCLE_PROGRAM = ROOT / "nc_files/calibration/twp_sphere_full_cycle_bplus5_t4.ngc"
FULL_CYCLE_BMINUS5_PROGRAM = ROOT / "nc_files/calibration/twp_sphere_full_cycle_bminus5_t4.ngc"
MACHINE_HAL = CONFIG / "5th_axis_xyzbc_ssi_tcpc_probe_basic.hal"
REMAP = CONFIG / "python/remap.py"
INI = CONFIG / "5th_axis_xyzbc_ssi_tcpc_probe_basic_twp_probe_validation_2026083101.ini"
LAUNCHER = CONFIG / "launch_xyzbc_ssi_twp_probe_validation.sh"
DEFAULT_LAUNCHER = CONFIG / "launch_xyzbc_ssi_tcpc_probe_basic.sh"
PASSES = CONFIG / "twp-sphere-stage1-t4-passes.csv"
RESULTS = CONFIG / "twp-sphere-stage1-t4-results.csv"
FULL_CYCLE_PASSES = CONFIG / "twp-sphere-full-cycle-bplus5-t4-passes.csv"
FULL_CYCLE_RESULTS = CONFIG / "twp-sphere-full-cycle-bplus5-t4-results.csv"
FULL_CYCLE_BMINUS5_PASSES = CONFIG / "twp-sphere-full-cycle-bminus5-t4-passes.csv"
FULL_CYCLE_BMINUS5_RESULTS = CONFIG / "twp-sphere-full-cycle-bminus5-t4-results.csv"

TOOL_LENGTH = 229.407
TOOL_OFFSET = (-36.280125, -26.685194, -677.346675)
ENVELOPE = 17.845258
TOP_RADIUS = 22.845258
SIDE_RADIUS = 21.845258
VECTOR_TOL = 1e-9


def fail(message):
    raise SystemExit("FAIL: " + message)


def require(condition, message):
    if not condition:
        fail(message)


def add(a, b):
    return tuple(a[index] + b[index] for index in range(3))


def sub(a, b):
    return tuple(a[index] - b[index] for index in range(3))


def scale(vector, factor):
    return tuple(value * factor for value in vector)


def dot(a, b):
    return sum(a[index] * b[index] for index in range(3))


def norm(vector):
    return math.sqrt(dot(vector, vector))


def assert_vector(label, actual, expected, tolerance=VECTOR_TOL):
    error = norm(sub(actual, expected))
    require(error <= tolerance, "%s error %.12g exceeds %.12g" % (label, error, tolerance))


def rotate_y(angle_deg, vector):
    angle = math.radians(angle_deg)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    x, y, z = vector
    return (cosine * x + sine * z, y, -sine * x + cosine * z)


def rotate_x(angle_deg, vector):
    angle = math.radians(angle_deg)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    x, y, z = vector
    return (x, cosine * y - sine * z, sine * y + cosine * z)


def rotate_z(angle_deg, vector):
    angle = math.radians(angle_deg)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    x, y, z = vector
    return (cosine * x - sine * y, sine * x + cosine * y, z)


def plane_axes(b_deg, c_deg):
    # Current commissioned axis-tilt terms are zero; the nonzero C zero is live.
    c_effective = c_deg - 0.0245
    return tuple(
        rotate_z(c_effective, rotate_y(b_deg, basis))
        for basis in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    )


def fusion_zxz_axes(i_deg, j_deg, k_deg):
    return tuple(
        rotate_z(i_deg, rotate_x(j_deg, rotate_z(k_deg, basis)))
        for basis in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    )


def normalize_angle(angle_deg):
    normalized = (angle_deg + 180.0) % 360.0 - 180.0
    return 180.0 if abs(normalized + 180.0) <= VECTOR_TOL else normalized


def validate_fusion_zxz_pose_grid():
    for b_deg in (5.0, -5.0):
        for c_deg in (0.0, 45.0, 90.0, 180.0, 225.0, 270.0):
            if b_deg > 0.0:
                euler = (normalize_angle(c_deg + 90.0), b_deg, -90.0)
            else:
                euler = (normalize_angle(c_deg - 90.0), abs(b_deg), 90.0)
            actual = fusion_zxz_axes(*euler)
            expected = tuple(
                rotate_z(c_deg, rotate_y(b_deg, basis))
                for basis in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
            )
            for axis, actual_axis, expected_axis in zip("XYZ", actual, expected):
                assert_vector(
                    "B%g C%g Fusion ZXZ %s" % (b_deg, c_deg, axis),
                    actual_axis,
                    expected_axis,
                )


def sphere_contacts(center, w_axis, u_axis, v_axis, u_sign):
    return (
        sub(center, scale(w_axis, ENVELOPE)),
        add(center, scale(u_axis, u_sign * ENVELOPE)),
        sub(center, scale(v_axis, ENVELOPE)),
        add(center, scale(v_axis, ENVELOPE)),
    )


def reconstructed_center(points, w_axis, u_axis, v_axis, u_sign):
    q_w, q_u, q_vm, q_vp = points
    center_w = dot(q_w, w_axis) + ENVELOPE
    center_u = dot(q_u, u_axis) - u_sign * ENVELOPE
    center_v = (dot(q_vm, v_axis) + dot(q_vp, v_axis)) / 2.0
    return tuple(
        w_axis[index] * center_w
        + u_axis[index] * center_u
        + v_axis[index] * center_v
        for index in range(3)
    )


def coordinate_layer_at_entry(wcs, captured_origin, axes):
    delta = sub(captured_origin, wcs)
    return tuple(wcs[index] + dot(delta, axes[index]) for index in range(3))


def local_program_point(physical_point, wcs, axes):
    joint_point = sub(physical_point, TOOL_OFFSET)
    delta = sub(joint_point, wcs)
    return (dot(delta, axes[0]), dot(delta, axes[1]), dot(delta, axes[2]) - TOOL_LENGTH)


def world_program_point(physical_point, wcs):
    joint_point = sub(physical_point, TOOL_OFFSET)
    return sub(sub(joint_point, wcs), (0.0, 0.0, TOOL_LENGTH))


def validate_coordinate_math():
    sphere_center = (1210.125, 617.875, -521.625)
    wcs = (87.25, -42.5, -13.75)

    for b_deg in (0.0, 5.0, -5.0):
        axes = plane_axes(b_deg, 0.0)
        plane_x, plane_y, plane_z = axes
        w_axis = scale(plane_z, -1.0)
        u_axis = plane_x
        v_axis = plane_y
        u_sign = 1.0 if b_deg < -0.001 else -1.0

        for name, axis in zip(("X", "Y", "Z"), axes):
            require(abs(norm(axis) - 1.0) <= VECTOR_TOL, "B%g plane %s is not unit" % (b_deg, name))
        require(abs(dot(plane_x, plane_y)) <= VECTOR_TOL, "B%g plane X/Y not orthogonal" % b_deg)
        require(abs(dot(plane_x, plane_z)) <= VECTOR_TOL, "B%g plane X/Z not orthogonal" % b_deg)
        require(abs(dot(plane_y, plane_z)) <= VECTOR_TOL, "B%g plane Y/Z not orthogonal" % b_deg)

        contacts = sphere_contacts(sphere_center, w_axis, u_axis, v_axis, u_sign)
        world_points = tuple(world_program_point(point, wcs) for point in contacts)
        world_raw_center = reconstructed_center(world_points, w_axis, u_axis, v_axis, u_sign)
        world_physical_center = add(
            add(add(world_raw_center, wcs), (0.0, 0.0, TOOL_LENGTH)),
            TOOL_OFFSET,
        )
        assert_vector("B%g world physical center" % b_deg, world_physical_center, sphere_center)

        captured_origin = sub(
            sub(sphere_center, scale(w_axis, TOP_RADIUS)),
            TOOL_OFFSET,
        )
        coordinate_layer = coordinate_layer_at_entry(wcs, captured_origin, axes)
        local_points = tuple(local_program_point(point, wcs, axes) for point in contacts)
        local_center = reconstructed_center(
            local_points,
            (0.0, 0.0, -1.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            u_sign,
        )
        restored_local = (
            local_center[0] + wcs[0] - coordinate_layer[0],
            local_center[1] + wcs[1] - coordinate_layer[1],
            local_center[2] + wcs[2] + TOOL_LENGTH - coordinate_layer[2],
        )
        twp_joint_center = add(
            captured_origin,
            add(
                add(scale(plane_x, restored_local[0]), scale(plane_y, restored_local[1])),
                scale(plane_z, restored_local[2]),
            ),
        )
        twp_physical_center = add(twp_joint_center, TOOL_OFFSET)
        assert_vector("B%g transformed TWP center" % b_deg, twp_physical_center, sphere_center)
        assert_vector("B%g WORLD/TWP agreement" % b_deg, twp_physical_center, world_physical_center)

        uncorrected = add(
            captured_origin,
            add(
                add(scale(plane_x, local_center[0]), scale(plane_y, local_center[1])),
                scale(plane_z, local_center[2]),
            ),
        )
        require(norm(sub(uncorrected, sphere_center)) > 10.0, "B%g incomplete TWP coordinate reconstruction was not detectably wrong" % b_deg)


def executable_lines(text):
    result = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or (stripped.startswith("(") and not stripped.startswith("(LOG")):
            continue
        result.append(re.sub(r"\([^)]*\)", "", stripped))
    return result


def validate_control_pairs(lines):
    text = "\n".join(lines)
    for opener, closer in (("if", "endif"), ("while", "endwhile")):
        open_names = re.findall(r"^o<([^>]+)>\s+%s\b" % opener, text, re.MULTILINE)
        close_names = re.findall(r"^o<([^>]+)>\s+%s\b" % closer, text, re.MULTILINE)
        require(sorted(open_names) == sorted(close_names), "unmatched O-code %s/%s labels" % (opener, closer))


def validate_program_static():
    text = PROGRAM.read_text(encoding="ascii")
    raw_lines = text.splitlines()
    lines = executable_lines(text)
    code = "\n".join(lines)

    long_lines = [(index, len(line)) for index, line in enumerate(raw_lines, 1) if len(line) > 240]
    require(not long_lines, "program lines exceed 240 characters: %r" % (long_lines,))
    require(set(re.findall(r"\bG38\.\d\b", code)) == {"G38.3"}, "active probe envelope is not G38.3-only")
    require(len(re.findall(r"\bG38\.3\b", code)) == 1, "probe subroutine must contain one G38.3 block")
    require(len(re.findall(r"\bG68\.2\b", code)) == 1, "main path must enter TWP exactly once")
    require(len(re.findall(r"\bG53\.1\b", code)) == 1, "main path must activate TWP exactly once")
    require(len(re.findall(r"\bG69\b", code)) == 2, "program must have main and abort-cleanup G69 paths")
    require(not re.search(r"\bG43\.4\b", code), "TWP program must not enable the separate TCPC mode")
    require(len(re.findall(r"\bM0\b", code)) == 1, "program must have exactly one initial operator hold")
    require("#<_abs_z> - #<_z> - #<_hal[motion.tooloffset.z]>" in text, "G5X recovery does not remove NP_ABS tool Z")
    require("#<local_dz> + #<_twp_s1_tool_length> - #<_twp_s1_offset_z>" in text, "TWP transform does not restore local T4 length and coordinate layer")
    require(text.count("+ #<_twp_s1_tool_length> + #<_twp_s1_eval_z>]\n") >= 2, "WORLD center reconstruction is missing T4 length/geometry restoration")
    require(text.count("+ #<_twp_s1_eval_x>]\n") >= 3, "physical center reconstruction is missing evaluated X tool geometry")
    require("#5220 - FIX[#5220]" in text, "live guard does not validate the active WCS index")
    require(all("ABS[#%d]" % index in text for index in range(5210, 5220)), "live guard does not reject every G52/G92 layer")
    require("#[5204 + [20 * #5220]]" in text, "live guard does not reject active WCS rotary offsets")
    require("#[5209 + [20 * #5220]]" in text, "live guard does not reject active WCS auxiliary offsets")
    require("#[5210 + [20 * #5220]]" in text, "live guard does not reject active WCS XY rotation")

    ready_index = text.index("o<twp_s1_probe_ready> call", text.index("o<twp_s1_probe_vector> sub"))
    guard_index = text.index("o<twp_s1_live_guard> call [#<_twp_s1_measure_twp_mode>]", ready_index)
    probe_index = text.index("G38.3", guard_index)
    require(ready_index < guard_index < probe_index, "live guard is not immediately downstream of probe-ready")

    sub_names = re.findall(r"^o<([^>]+)>\s+sub\b", code, re.MULTILINE)
    require(len(sub_names) == len(set(sub_names)), "duplicate O-code subroutine definition")
    call_names = set(re.findall(r"^\s*o<([^>]+)>\s+call\b", code, re.MULTILINE))
    require(call_names <= set(sub_names), "undefined O-code calls: %r" % sorted(call_names - set(sub_names)))
    validate_control_pairs(lines)


def validate_full_cycle_program_static():
    text = FULL_CYCLE_PROGRAM.read_text(encoding="ascii")
    raw_lines = text.splitlines()
    lines = executable_lines(text)
    code = "\n".join(lines)

    long_lines = [(index, len(line)) for index, line in enumerate(raw_lines, 1) if len(line) > 240]
    require(not long_lines, "full-cycle program lines exceed 240 characters: %r" % (long_lines,))
    require(set(re.findall(r"\bG38\.\d\b", code)) == {"G38.3"}, "full-cycle probe envelope is not G38.3-only")
    require(len(re.findall(r"\bG38\.3\b", code)) == 1, "full-cycle probe subroutine must contain one G38.3 block")
    require(len(re.findall(r"\bG68\.2\b", code)) == 1, "full-cycle path must define TWP exactly once")
    require(len(re.findall(r"\bG53\.1\b", code)) == 1, "full-cycle path must activate TWP exactly once")
    require(len(re.findall(r"\bG69\b", code)) == 2, "full-cycle path must have main and abort-cleanup G69 paths")
    require(not re.search(r"\bG43\.4\b", code), "full-cycle TWP path must keep public TCPC off")
    require(len(re.findall(r"\bM0\b", code)) == 1, "full-cycle path must have one initial operator hold")
    require(
        "G68.2 X0 Y0 Z0 I90 J5 K-90" in code,
        "full-cycle path does not use the literal Fusion rotating-ZXZ B+5 frame",
    )
    require("G68.2 R0" not in code, "full-cycle path still uses the commissioning-only R0 form")

    index_out = code.index("G0 B#<_twp_fc5_target_b> C#<_twp_fc5_target_c>")
    twp_define = code.index("G68.2 X0 Y0 Z0 I90 J5 K-90")
    twp_activate = code.index("G53.1", twp_define)
    twp_cancel = code.index("G69", twp_activate)
    index_home = code.index("G0 B0 C0", twp_cancel)
    require(
        index_out < twp_define < twp_activate < twp_cancel < index_home,
        "full-cycle rotary/TWP lifecycle order changed",
    )
    require(
        text.count("o<twp_fc5_move_world_tool> call") == 7,
        "full-cycle path must use seven guarded physical-tool positioning moves",
    )
    require(
        "#<_hal[headheadtwp.current_tool_x]>" in text
        and "#<_hal[headheadtwp.current_tool_y]>" in text
        and "#<_hal[headheadtwp.current_tool_z]>" in text,
        "full-cycle positioning does not close against the physical probe-ball center",
    )
    require(
        "#<_twp_fc5_transition_radius> = 80.0" in text,
        "full-cycle transition clearance is not pinned at 80 mm",
    )
    require(
        "#<_hal[headheadtwp.plane_x_x]>" in text
        and "#<_hal[headheadtwp.plane_z_z]>" in text,
        "full-cycle reconstruction does not use synchronized CAM plane axes",
    )
    require(
        text.count("o<twp_fc5_measure_pair> call") == 3,
        "full-cycle path must measure B0 WORLD / B+5 TWP / B0 WORLD",
    )
    require(
        "#<_twp_fc5_expected_b> = #<_twp_fc5_target_b>" in text
        and "#<_twp_fc5_expected_b> = 0.0" in text,
        "full-cycle B hold guard does not follow the planned index and return",
    )
    require(
        str(FULL_CYCLE_PASSES) in text and str(FULL_CYCLE_RESULTS) in text,
        "full-cycle program does not use its separate evidence tables",
    )
    require("#<counter_delta> - 24.0" in text, "full-cycle path does not require 24 gated contacts")
    require("#<_twp_fc5_full_cycle_error>" in text, "full-cycle center error is not calculated")

    sub_names = re.findall(r"^o<([^>]+)>\s+sub\b", code, re.MULTILINE)
    require(len(sub_names) == len(set(sub_names)), "duplicate full-cycle O-code subroutine definition")
    call_names = set(re.findall(r"^\s*o<([^>]+)>\s+call\b", code, re.MULTILINE))
    require(call_names <= set(sub_names), "undefined full-cycle O-code calls: %r" % sorted(call_names - set(sub_names)))
    validate_control_pairs(lines)


def validate_bminus5_full_cycle_program_static():
    positive = FULL_CYCLE_PROGRAM.read_text(encoding="ascii")
    negative = FULL_CYCLE_BMINUS5_PROGRAM.read_text(encoding="ascii")
    lines = executable_lines(negative)
    code = "\n".join(lines)

    require("#<_twp_fcm5_target_b> = -5.0" in negative, "B-5 target is not pinned")
    require("#<_twp_fcm5_target_c> = 0.0" in negative, "B-5 C target is not pinned")
    require(
        "G68.2 X0 Y0 Z0 I-90 J5 K90" in code,
        "B-5 path does not use Fusion's alternate rotating-ZXZ branch",
    )
    require("G68.2 R0" not in code, "B-5 path uses the commissioning-only R0 form")
    require(not re.search(r"\bG43\.4\b", code), "B-5 TWP path enables separate TCPC mode")
    require("length-model.id]> - 2026082601" in negative, "B-5 path changed model identity")
    require("#3032 = #<_twp_fcm5_probe_offset>" in negative, "B-5 path changed probe compensation")
    require(str(FULL_CYCLE_BMINUS5_PASSES) in negative, "B-5 pass evidence path is not separate")
    require(str(FULL_CYCLE_BMINUS5_RESULTS) in negative, "B-5 result evidence path is not separate")

    normalized = negative
    for old, new in (
        ("twp_fcm5", "twp_fc5"),
        ("BMINUS5", "BPLUS5"),
        ("bminus5", "bplus5"),
        ("2026090102", "2026090101"),
        ("#<_twp_fc5_target_b> = -5.0", "#<_twp_fc5_target_b> = 5.0"),
        ("B-5", "B+5"),
        ("G68.2 X0 Y0 Z0 I-90 J5 K90", "G68.2 X0 Y0 Z0 I90 J5 K-90"),
    ):
        normalized = normalized.replace(old, new)
    require(
        normalized == positive,
        "B-5 program differs from the accepted B+5 cycle outside its reviewed pose identity",
    )

    raw_lines = negative.splitlines()
    long_lines = [(index, len(line)) for index, line in enumerate(raw_lines, 1) if len(line) > 240]
    require(not long_lines, "B-5 program lines exceed 240 characters: %r" % (long_lines,))
    validate_control_pairs(lines)


def validate_csv_headers():
    expected_passes = (
        "schema_version,campaign_id,phase_id,pass_id,twp_mode,b_deg,c_deg,"
        "center_x,center_y,center_z,v_diameter_mm,max_radial_residual_mm,"
        "cumulative_gated_edges"
    )
    expected_results = (
        "schema_version,campaign_id,b_deg,c_deg,tool_length_mm,probe_offset_mm,"
        "world_open_x,world_open_y,world_open_z,twp_world_x,twp_world_y,"
        "twp_world_z,world_close_x,world_close_y,world_close_z,world_closure_mm,"
        "twp_center_error_mm,world_open_pair_mm,twp_pair_mm,world_close_pair_mm,"
        "world_open_v_diameter_mm,twp_v_diameter_mm,world_close_v_diameter_mm,"
        "world_open_max_residual_mm,twp_max_residual_mm,"
        "world_close_max_residual_mm,gated_edge_count"
    )
    pass_rows = list(csv.reader(PASSES.read_text(encoding="ascii").splitlines()))
    result_rows = list(csv.reader(RESULTS.read_text(encoding="ascii").splitlines()))
    require(pass_rows and ",".join(pass_rows[0]) == expected_passes, "pass CSV schema changed")
    require(result_rows and ",".join(result_rows[0]) == expected_results, "result CSV schema changed")
    require(len(pass_rows[0]) == 13, "pass CSV column count is not 13")
    require(len(result_rows[0]) == 27, "result CSV column count is not 27")
    require(
        all(len(row) == 13 for row in pass_rows[1:]),
        "an appended physical pass row does not contain 13 columns",
    )
    require(
        all(len(row) == 27 for row in result_rows[1:]),
        "an appended accepted-result row does not contain 27 columns",
    )

    expected_full_cycle_results = (
        "schema_version,campaign_id,reached_b_deg,reached_c_deg,return_b_deg,"
        "return_c_deg,tool_length_mm,probe_offset_mm,world_open_x,world_open_y,"
        "world_open_z,twp_bplus5_world_x,twp_bplus5_world_y,twp_bplus5_world_z,"
        "world_close_x,world_close_y,world_close_z,world_return_closure_mm,"
        "full_cycle_center_error_mm,world_open_pair_mm,twp_bplus5_pair_mm,"
        "world_close_pair_mm,world_open_v_diameter_mm,twp_bplus5_v_diameter_mm,"
        "world_close_v_diameter_mm,world_open_max_residual_mm,"
        "twp_bplus5_max_residual_mm,world_close_max_residual_mm,gated_edge_count"
    )
    full_pass_rows = list(csv.reader(FULL_CYCLE_PASSES.read_text(encoding="ascii").splitlines()))
    full_result_rows = list(csv.reader(FULL_CYCLE_RESULTS.read_text(encoding="ascii").splitlines()))
    require(full_pass_rows and ",".join(full_pass_rows[0]) == expected_passes, "full-cycle pass CSV schema changed")
    require(
        full_result_rows and ",".join(full_result_rows[0]) == expected_full_cycle_results,
        "full-cycle result CSV schema changed",
    )
    require(len(full_pass_rows[0]) == 13, "full-cycle pass CSV column count is not 13")
    require(len(full_result_rows[0]) == 29, "full-cycle result CSV column count is not 29")
    require(all(len(row) == 13 for row in full_pass_rows[1:]), "a full-cycle pass row does not contain 13 columns")
    require(all(len(row) == 29 for row in full_result_rows[1:]), "a full-cycle result row does not contain 29 columns")

    expected_bminus5_results = expected_full_cycle_results.replace("bplus5", "bminus5")
    bminus5_pass_rows = list(csv.reader(FULL_CYCLE_BMINUS5_PASSES.read_text(encoding="ascii").splitlines()))
    bminus5_result_rows = list(csv.reader(FULL_CYCLE_BMINUS5_RESULTS.read_text(encoding="ascii").splitlines()))
    require(
        bminus5_pass_rows and ",".join(bminus5_pass_rows[0]) == expected_passes,
        "B-5 pass CSV schema changed",
    )
    require(
        bminus5_result_rows and ",".join(bminus5_result_rows[0]) == expected_bminus5_results,
        "B-5 result CSV schema changed",
    )
    require(all(len(row) == 13 for row in bminus5_pass_rows), "B-5 pass CSV column count is not 13")
    require(all(len(row) == 29 for row in bminus5_result_rows), "B-5 result CSV column count is not 29")


def validate_launch_boundary():
    ini = INI.read_text(encoding="ascii")
    launcher = LAUNCHER.read_text(encoding="ascii")
    default_launcher = DEFAULT_LAUNCHER.read_text(encoding="ascii")
    require(re.search(r"(?ms)^\[TWP\]\s*^ENABLE\s*=\s*1\s*$", ini), "dedicated INI does not opt in to TWP")
    require(re.search(r"(?m)^EULER_CONVENTION\s*=\s*ZXZ_R\s*$", ini), "dedicated INI does not pin Fusion's rotating ZXZ convention")
    require(re.search(r"(?m)^REMAP\s*=\s*G68\.2\s+modalgroup=1\s+argspec=xyzijkbcr\s+py=enable_twp_mode\s*$", ini), "dedicated INI does not accept the Fusion G68.2 word set")
    require(re.search(r"(?m)^REMAP\s*=\s*G53\.1\s+modalgroup=1\s+py=activate_twp_mode\s*$", ini), "dedicated INI does not map G53.1 activation")
    require("lengthmodel=1 lengthmodelid=2026082601" in ini, "dedicated INI does not pin the length model")
    require(str(PROGRAM) in ini, "dedicated INI does not open the reviewed sphere program")
    require(INI.name in launcher, "dedicated launcher does not select the dedicated INI")
    require(INI.name not in default_launcher, "default launcher unexpectedly selects TWP validation")


def validate_machine_coordinate_sources():
    remap = REMAP.read_text(encoding="ascii")
    machine_hal = MACHINE_HAL.read_text(encoding="ascii")
    require(
        'float(_hal("joint.%d.pos-cmd" % joint))' in remap,
        "TWP remap does not capture machine joint coordinates",
    )
    require(
        'float(_hal("joint.%d.motor-pos-cmd" % joint))' not in remap,
        "TWP remap still constructs frames from motor-layer coordinates",
    )
    for joint, axis in enumerate("xyzbc"):
        expected = "joint.%d.pos-cmd => headheadtwp.current_joint_%s" % (joint, axis)
        require(expected in machine_hal, "TWP state source is not machine joint %s" % axis.upper())


def main():
    validate_program_static()
    validate_full_cycle_program_static()
    validate_bminus5_full_cycle_program_static()
    validate_coordinate_math()
    validate_fusion_zxz_pose_grid()
    validate_csv_headers()
    validate_launch_boundary()
    validate_machine_coordinate_sources()
    print("TWP sphere stage-1/full-cycle static and coordinate-math validation passed")


if __name__ == "__main__":
    main()
