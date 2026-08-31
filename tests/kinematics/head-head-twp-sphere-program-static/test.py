#!/usr/bin/env python3

import csv
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs/5th_axis_xyzbc_ssi_tcpc_probe_basic"
PROGRAM = ROOT / "nc_files/calibration/twp_sphere_probe_stage1_t4.ngc"
INI = CONFIG / "5th_axis_xyzbc_ssi_tcpc_probe_basic_twp_probe_validation_2026083101.ini"
LAUNCHER = CONFIG / "launch_xyzbc_ssi_twp_probe_validation.sh"
DEFAULT_LAUNCHER = CONFIG / "launch_xyzbc_ssi_tcpc_probe_basic.sh"
PASSES = CONFIG / "twp-sphere-stage1-t4-passes.csv"
RESULTS = CONFIG / "twp-sphere-stage1-t4-results.csv"

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
    require(PASSES.read_text(encoding="ascii").strip() == expected_passes, "pass CSV schema changed")
    require(RESULTS.read_text(encoding="ascii").strip() == expected_results, "result CSV schema changed")
    require(len(next(csv.reader([expected_passes]))) == 13, "pass CSV column count is not 13")
    require(len(next(csv.reader([expected_results]))) == 27, "result CSV column count is not 27")


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


def main():
    validate_program_static()
    validate_coordinate_math()
    validate_csv_headers()
    validate_launch_boundary()
    print("TWP sphere stage-1 static and coordinate-math validation passed")


if __name__ == "__main__":
    main()
