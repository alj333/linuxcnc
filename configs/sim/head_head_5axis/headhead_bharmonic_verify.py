#!/usr/bin/env python3
"""Offline verification for headheadkins B-harmonic diagnostic math.

This mirrors the relevant headheadkins.c forward/inverse offset path closely
enough to verify zero-default behavior, tool-frame conventions, and candidate
fixed-tip consistency without launching a LinuxCNC GUI or moving the machine.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


EPS = 1e-9


@dataclass(frozen=True)
class Geometry:
    nominal_c_to_b: tuple[float, float, float]
    cal_c_to_b: tuple[float, float, float]
    nominal_b_to_tool: tuple[float, float, float]
    cal_b_to_tool: tuple[float, float, float]
    b_zero_deg: float
    c_zero_deg: float
    c_axis_tilt_x_deg: float = 0.0
    c_axis_tilt_y_deg: float = 0.0
    b_axis_tilt_x_deg: float = 0.0
    b_axis_tilt_z_deg: float = 0.0


@dataclass(frozen=True)
class BHarmonic:
    enabled: bool
    machine: dict[str, tuple[float, float, float]]
    cframe: dict[str, tuple[float, float, float]]
    bcross: dict[str, tuple[float, float, float]]


ACTIVE_GEOMETRY = Geometry(
    nominal_c_to_b=(0.010934, 0.0, -270.000000),
    cal_c_to_b=(0.035886006, 0.009526306, 0.0),
    nominal_b_to_tool=(-0.668710, -26.721365, -308.980001),
    cal_b_to_tool=(0.0, 0.0, 0.815000),
    b_zero_deg=0.0,
    c_zero_deg=-0.024500,
)

FRAME_CONVENTION_GEOMETRY = Geometry(
    nominal_c_to_b=ACTIVE_GEOMETRY.nominal_c_to_b,
    cal_c_to_b=ACTIVE_GEOMETRY.cal_c_to_b,
    nominal_b_to_tool=ACTIVE_GEOMETRY.nominal_b_to_tool,
    cal_b_to_tool=ACTIVE_GEOMETRY.cal_b_to_tool,
    b_zero_deg=0.0,
    c_zero_deg=0.0,
)

ZERO_HARMONIC = BHarmonic(
    enabled=False,
    machine={
        "sin": (0.0, 0.0, 0.0),
        "omc": (0.0, 0.0, 0.0),
        "sin2": (0.0, 0.0, 0.0),
    },
    cframe={
        "sin": (0.0, 0.0, 0.0),
        "omc": (0.0, 0.0, 0.0),
        "sin2": (0.0, 0.0, 0.0),
    },
    bcross={
        "sinb-sinc": (0.0, 0.0, 0.0),
        "omcb-sinc": (0.0, 0.0, 0.0),
        "omcb-sin2c": (0.0, 0.0, 0.0),
        "sinb-cosc": (0.0, 0.0, 0.0),
        "omcb-cosc": (0.0, 0.0, 0.0),
    },
)

MACHINE_FIXED_CANDIDATE = BHarmonic(
    enabled=True,
    machine={
        "sin": (0.003457595, 0.071987315, 0.318267363),
        "omc": (0.108123741, 0.034446993, -0.364472105),
        "sin2": (-0.032225192, 0.005230194, -0.190772593),
    },
    cframe=ZERO_HARMONIC.cframe,
    bcross=ZERO_HARMONIC.bcross,
)

MACHINE_FIXED_DISABLED = BHarmonic(
    enabled=False,
    machine=MACHINE_FIXED_CANDIDATE.machine,
    cframe=MACHINE_FIXED_CANDIDATE.cframe,
    bcross=MACHINE_FIXED_CANDIDATE.bcross,
)

BCROSS_CANDIDATE = BHarmonic(
    enabled=True,
    machine=MACHINE_FIXED_CANDIDATE.machine,
    cframe=ZERO_HARMONIC.cframe,
    bcross={
        "sinb-sinc": (0.002528625, 0.322704792, 0.129756713),
        "omcb-sinc": (-0.075154781, 0.002088037, -0.001416604),
        "omcb-sin2c": (0.015430253, -0.178186533, -0.027922013),
        "sinb-cosc": (-0.047944843, -0.063115561, -0.018569166),
        "omcb-cosc": (-0.033954526, 0.071241728, -0.000964915),
    },
)

POSES = [
    (b, c)
    for b in (-90.0, -60.0, -30.0, 0.0, 30.0, 60.0, 90.0)
    for c in (0.0, 90.0, 180.0, 270.0)
]


def vec_add(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vec_sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_scale(scale: float, vec: tuple[float, float, float]) -> tuple[float, float, float]:
    return (scale * vec[0], scale * vec[1], scale * vec[2])


def vec_dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return (a[0] * b[0]) + (a[1] * b[1]) + (a[2] * b[2])


def vec_cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        (a[1] * b[2]) - (a[2] * b[1]),
        (a[2] * b[0]) - (a[0] * b[2]),
        (a[0] * b[1]) - (a[1] * b[0]),
    )


def vec_length(vec: tuple[float, float, float]) -> float:
    return math.sqrt(vec_dot(vec, vec))


def vec_normalize(vec: tuple[float, float, float]) -> tuple[float, float, float]:
    length = vec_length(vec)
    if length <= 1e-12:
        return (0.0, 1.0, 0.0)
    return (vec[0] / length, vec[1] / length, vec[2] / length)


def rotate_x(angle_deg: float, vec: tuple[float, float, float]) -> tuple[float, float, float]:
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    x, y, z = vec
    return (x, (c * y) - (s * z), (s * y) + (c * z))


def rotate_y(angle_deg: float, vec: tuple[float, float, float]) -> tuple[float, float, float]:
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    x, y, z = vec
    return ((c * x) + (s * z), y, (-s * x) + (c * z))


def rotate_z(angle_deg: float, vec: tuple[float, float, float]) -> tuple[float, float, float]:
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    x, y, z = vec
    return ((c * x) - (s * y), (s * x) + (c * y), z)


def rotate_axis(
    axis: tuple[float, float, float],
    angle_deg: float,
    vec: tuple[float, float, float],
) -> tuple[float, float, float]:
    normalized = vec_normalize(axis)
    angle = math.radians(angle_deg)
    c = math.cos(angle)
    s = math.sin(angle)
    dot = vec_dot(normalized, vec)
    cross = vec_cross(normalized, vec)
    return vec_add(
        vec_add(vec_scale(c, vec), vec_scale(s, cross)),
        vec_scale(dot * (1.0 - c), normalized),
    )


def c_frame_to_world(geometry: Geometry, vec: tuple[float, float, float]) -> tuple[float, float, float]:
    return rotate_y(geometry.c_axis_tilt_y_deg, rotate_x(geometry.c_axis_tilt_x_deg, vec))


def local_b_axis(geometry: Geometry) -> tuple[float, float, float]:
    return vec_normalize(
        (
            math.tan(math.radians(geometry.b_axis_tilt_x_deg)),
            1.0,
            math.tan(math.radians(geometry.b_axis_tilt_z_deg)),
        )
    )


def rotary_vector_world(
    geometry: Geometry,
    b_deg: float,
    c_deg: float,
    vec: tuple[float, float, float],
) -> tuple[float, float, float]:
    b_eff = b_deg + geometry.b_zero_deg
    c_eff = c_deg + geometry.c_zero_deg
    b_rotated = rotate_axis(local_b_axis(geometry), b_eff, vec)
    return c_frame_to_world(geometry, rotate_z(c_eff, b_rotated))


def tool_frame_world(
    geometry: Geometry,
    b_deg: float,
    c_deg: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    return (
        rotary_vector_world(geometry, b_deg, c_deg, (1.0, 0.0, 0.0)),
        rotary_vector_world(geometry, b_deg, c_deg, (0.0, 1.0, 0.0)),
        rotary_vector_world(geometry, b_deg, c_deg, (0.0, 0.0, -1.0)),
    )


def b_harmonic_vector(
    coeffs: dict[str, tuple[float, float, float]],
    b_eff: float,
) -> tuple[float, float, float]:
    b_rad = math.radians(b_eff)
    terms = {
        "sin": math.sin(b_rad),
        "omc": 1.0 - math.cos(b_rad),
        "sin2": math.sin(2.0 * b_rad),
    }
    out = (0.0, 0.0, 0.0)
    for term_name, term_value in terms.items():
        out = vec_add(out, vec_scale(term_value, coeffs[term_name]))
    return out


def b_cross_vector(
    coeffs: dict[str, tuple[float, float, float]],
    b_eff: float,
    c_eff: float,
) -> tuple[float, float, float]:
    b_rad = math.radians(b_eff)
    c_rad = math.radians(c_eff)
    terms = {
        "sinb-sinc": math.sin(b_rad) * math.sin(c_rad),
        "omcb-sinc": (1.0 - math.cos(b_rad)) * math.sin(c_rad),
        "omcb-sin2c": (1.0 - math.cos(b_rad)) * math.sin(c_rad) * math.sin(c_rad),
        "sinb-cosc": math.sin(b_rad) * math.cos(c_rad),
        "omcb-cosc": (1.0 - math.cos(b_rad)) * math.cos(c_rad),
    }
    out = (0.0, 0.0, 0.0)
    for term_name, term_value in terms.items():
        out = vec_add(out, vec_scale(term_value, coeffs[term_name]))
    return out


def b_harmonic_offset_world(
    geometry: Geometry,
    harmonic: BHarmonic,
    b_deg: float,
    c_deg: float,
) -> tuple[float, float, float]:
    if not harmonic.enabled:
        return (0.0, 0.0, 0.0)

    b_eff = b_deg + geometry.b_zero_deg
    c_eff = c_deg + geometry.c_zero_deg
    machine_fixed = b_harmonic_vector(harmonic.machine, b_eff)
    cframe_local = b_harmonic_vector(harmonic.cframe, b_eff)
    cframe_world = c_frame_to_world(geometry, rotate_z(c_eff, cframe_local))
    return vec_add(vec_add(machine_fixed, cframe_world), b_cross_vector(harmonic.bcross, b_eff, c_eff))


def tool_offset_world(
    geometry: Geometry,
    harmonic: BHarmonic,
    b_deg: float,
    c_deg: float,
) -> tuple[float, float, float]:
    b_eff = b_deg + geometry.b_zero_deg
    c_eff = c_deg + geometry.c_zero_deg
    c_to_b = vec_add(geometry.nominal_c_to_b, geometry.cal_c_to_b)
    b_to_tool = vec_add(geometry.nominal_b_to_tool, geometry.cal_b_to_tool)
    b_rotated = rotate_axis(local_b_axis(geometry), b_eff, b_to_tool)
    c_rotated = rotate_z(c_eff, vec_add(c_to_b, b_rotated))
    return vec_add(
        c_frame_to_world(geometry, c_rotated),
        b_harmonic_offset_world(geometry, harmonic, b_deg, c_deg),
    )


def inverse_tcp(
    geometry: Geometry,
    harmonic: BHarmonic,
    tcp_xyz: tuple[float, float, float],
    b_deg: float,
    c_deg: float,
) -> tuple[float, float, float]:
    return vec_sub(tcp_xyz, tool_offset_world(geometry, harmonic, b_deg, c_deg))


def forward_tcp(
    geometry: Geometry,
    harmonic: BHarmonic,
    joint_xyz: tuple[float, float, float],
    b_deg: float,
    c_deg: float,
) -> tuple[float, float, float]:
    return vec_add(joint_xyz, tool_offset_world(geometry, harmonic, b_deg, c_deg))


def norm(vec: tuple[float, float, float]) -> float:
    return vec_length(vec)


def probe_formula_frame(
    b_deg: float,
    c_deg: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    b_rad = math.radians(b_deg)
    c_rad = math.radians(c_deg)
    return (
        (math.cos(b_rad) * math.cos(c_rad), math.cos(b_rad) * math.sin(c_rad), -math.sin(b_rad)),
        (-math.sin(c_rad), math.cos(c_rad), 0.0),
        (-math.sin(b_rad) * math.cos(c_rad), -math.sin(b_rad) * math.sin(c_rad), -math.cos(b_rad)),
    )


def assert_close(label: str, value: float, tolerance: float) -> None:
    if value > tolerance:
        raise AssertionError(f"{label}: {value:.12g} > {tolerance:.12g}")


def verify_zero_default() -> float:
    max_delta = 0.0
    zero_enabled = BHarmonic(
        enabled=True,
        machine=ZERO_HARMONIC.machine,
        cframe=ZERO_HARMONIC.cframe,
        bcross=ZERO_HARMONIC.bcross,
    )
    for b_deg, c_deg in POSES:
        baseline = tool_offset_world(ACTIVE_GEOMETRY, ZERO_HARMONIC, b_deg, c_deg)
        enabled_zero = tool_offset_world(ACTIVE_GEOMETRY, zero_enabled, b_deg, c_deg)
        disabled_candidate = tool_offset_world(ACTIVE_GEOMETRY, MACHINE_FIXED_DISABLED, b_deg, c_deg)
        max_delta = max(max_delta, norm(vec_sub(enabled_zero, baseline)))
        max_delta = max(max_delta, norm(vec_sub(disabled_candidate, baseline)))
    assert_close("zero/default harmonic offset delta", max_delta, EPS)
    return max_delta


def verify_tool_frame() -> tuple[float, float]:
    max_formula_delta = 0.0
    max_orthogonality_error = 0.0
    for b_deg, c_deg in POSES:
        frame = tool_frame_world(FRAME_CONVENTION_GEOMETRY, b_deg, c_deg)
        expected = probe_formula_frame(b_deg, c_deg)
        for actual_axis, expected_axis in zip(frame, expected):
            max_formula_delta = max(max_formula_delta, norm(vec_sub(actual_axis, expected_axis)))
        u_axis, v_axis, w_axis = tool_frame_world(ACTIVE_GEOMETRY, b_deg, c_deg)
        max_orthogonality_error = max(
            max_orthogonality_error,
            abs(vec_dot(u_axis, v_axis)),
            abs(vec_dot(u_axis, w_axis)),
            abs(vec_dot(v_axis, w_axis)),
            abs(vec_length(u_axis) - 1.0),
            abs(vec_length(v_axis) - 1.0),
            abs(vec_length(w_axis) - 1.0),
        )
    assert_close("tool frame probe-formula delta", max_formula_delta, EPS)
    assert_close("active tool frame orthogonality error", max_orthogonality_error, EPS)
    return max_formula_delta, max_orthogonality_error


def verify_forward_inverse() -> float:
    max_roundtrip = 0.0
    targets = (
        (468.86, 323.66, -858.97),
        (500.0, 320.0, -850.0),
        (450.0, 360.0, -820.0),
    )
    for target in targets:
        for b_deg, c_deg in POSES:
            for harmonic in (MACHINE_FIXED_CANDIDATE, BCROSS_CANDIDATE):
                joints = inverse_tcp(ACTIVE_GEOMETRY, harmonic, target, b_deg, c_deg)
                returned = forward_tcp(ACTIVE_GEOMETRY, harmonic, joints, b_deg, c_deg)
                max_roundtrip = max(max_roundtrip, norm(vec_sub(returned, target)))
    assert_close("candidate forward/inverse round-trip", max_roundtrip, EPS)
    return max_roundtrip


def harmonic_offsets_for_c0() -> list[tuple[float, tuple[float, float, float]]]:
    rows = []
    for b_deg in (-90.0, -60.0, -30.0, 0.0, 30.0, 60.0, 90.0):
        rows.append((b_deg, b_harmonic_offset_world(ACTIVE_GEOMETRY, BCROSS_CANDIDATE, b_deg, 0.0)))
    return rows


def fmt_vec(vec: tuple[float, float, float]) -> str:
    return f"{vec[0]:+0.9f}, {vec[1]:+0.9f}, {vec[2]:+0.9f}"


def main() -> int:
    zero_delta = verify_zero_default()
    frame_delta, frame_orthogonality = verify_tool_frame()
    roundtrip = verify_forward_inverse()

    print("headheadkins B-harmonic offline verification")
    print(f"zero/default max offset delta      : {zero_delta:.12g} mm")
    print(f"tool-frame formula max delta       : {frame_delta:.12g}")
    print(f"tool-frame orthogonality max error : {frame_orthogonality:.12g}")
    print(f"candidate forward/inverse max error: {roundtrip:.12g} mm")
    print("")
    print("B/C cross candidate harmonic offsets at C0:")
    print("| B deg | dX | dY | dZ |")
    print("| ---: | ---: | ---: | ---: |")
    for b_deg, offset in harmonic_offsets_for_c0():
        print(f"| {b_deg:+.0f} | {fmt_vec(offset).replace(', ', ' | ')} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
