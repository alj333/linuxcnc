/********************************************************************
* Description: headheadkins.c
*   Parameterized head-head XYZBC kinematics scaffold.
*
*   This model assumes:
*   - X/Y/Z joints locate the C-axis pivot center in world space
*   - C rotates about +Z
*   - B rotates about +Y in the C-rotated frame
*   - world XYZ are the tool-reference point coordinates
*
*   The geometry is intentionally exposed as HAL pins so nominal CAD
*   values and later calibration values can be applied without rebuilding.
*
* License: GPL Version 2
********************************************************************/

#include "motion.h"
#include "hal.h"
#include "rtapi.h"
#include "rtapi_app.h"
#include "rtapi_math.h"
#include "rtapi_string.h"
#include "rtapi_ctype.h"
#include "kinematics.h"

#define REQUIRED_COORDINATES "XYZBC"
#define TWP_ROTARY_TOLERANCE_DEG 1e-3
#define TOOL_FRAME_AXES 3
#define B_HARMONIC_TERMS 3
#define B_CROSS_TERMS 5

struct haldata {
    hal_float_t *nominal_c_to_b_x;
    hal_float_t *nominal_c_to_b_y;
    hal_float_t *nominal_c_to_b_z;

    hal_float_t *nominal_b_to_tool_x;
    hal_float_t *nominal_b_to_tool_y;
    hal_float_t *nominal_b_to_tool_z;

    hal_float_t *cal_c_to_b_x;
    hal_float_t *cal_c_to_b_y;
    hal_float_t *cal_c_to_b_z;

    hal_float_t *cal_b_to_tool_x;
    hal_float_t *cal_b_to_tool_y;
    hal_float_t *cal_b_to_tool_z;

    hal_float_t *b_zero_offset;
    hal_float_t *c_zero_offset;

    hal_float_t *c_axis_tilt_x;
    hal_float_t *c_axis_tilt_y;
    hal_float_t *b_axis_tilt_x;
    hal_float_t *b_axis_tilt_z;

    hal_float_t *tool_offset_x;
    hal_float_t *tool_offset_y;
    hal_float_t *tool_offset_z;
    hal_float_t *tool_vector_x;
    hal_float_t *tool_vector_y;
    hal_float_t *tool_vector_z;
    hal_float_t *tool_frame[TOOL_FRAME_AXES][3];
    hal_float_t *c_axis_vector_x;
    hal_float_t *c_axis_vector_y;
    hal_float_t *c_axis_vector_z;
    hal_float_t *b_axis_vector_x;
    hal_float_t *b_axis_vector_y;
    hal_float_t *b_axis_vector_z;

    hal_bit_t *sim_b_harmonic_enable;
    hal_float_t *b_harmonic_machine[B_HARMONIC_TERMS][3];
    hal_float_t *b_harmonic_cframe[B_HARMONIC_TERMS][3];
    hal_float_t *b_cross_machine[B_CROSS_TERMS][3];

    hal_bit_t *tcpc_enable;
    hal_bit_t *twp_mode;
    hal_float_t *twp_motion_origin_x;
    hal_float_t *twp_motion_origin_y;
    hal_float_t *twp_motion_origin_z;
    hal_float_t *twp_b_angle;
    hal_float_t *twp_c_angle;
    hal_float_t *twp_normal_rotation;
} *haldata;

static int comp_id;
static int headhead_max_joints;

static KINEMATICS_TYPE ktype = KINEMATICS_BOTH;

static char *coordinates = REQUIRED_COORDINATES;
RTAPI_MP_STRING(coordinates, "Existing axes, must include XYZBC");

static char *kinstype = "b";
RTAPI_MP_STRING(kinstype, "Kinematics type (Identity, Both)");

static int JX = -1;
static int JY = -1;
static int JZ = -1;
static int JB = -1;
static int JC = -1;

static const char *tool_frame_names[TOOL_FRAME_AXES] = {"u", "v", "w"};
static const char *axis_names[3] = {"x", "y", "z"};
static const char *b_harmonic_term_names[B_HARMONIC_TERMS] = {
    "sin",
    "omc",
    "sin2",
};
static const char *b_cross_term_names[B_CROSS_TERMS] = {
    "sinb-sinc",
    "omcb-sinc",
    "omcb-sin2c",
    "sinb-cosc",
    "omcb-cosc",
};

static double pinv(hal_float_t *pin)
{
    return pin ? *pin : 0.0;
}

static int pinb(hal_bit_t *pin)
{
    return pin ? *pin : 0;
}

static void setpin(hal_float_t *pin, double value)
{
    if (pin) {
        *pin = value;
    }
}

static void rotate_x(double angle_deg, const double in[3], double out[3])
{
    double angle = TO_RAD * angle_deg;
    double c = cos(angle);
    double s = sin(angle);

    out[0] = in[0];
    out[1] = (c * in[1]) - (s * in[2]);
    out[2] = (s * in[1]) + (c * in[2]);
}

static void rotate_y(double angle_deg, const double in[3], double out[3])
{
    double angle = TO_RAD * angle_deg;
    double c = cos(angle);
    double s = sin(angle);

    out[0] = c * in[0] + s * in[2];
    out[1] = in[1];
    out[2] = -s * in[0] + c * in[2];
}

static void rotate_z(double angle_deg, const double in[3], double out[3])
{
    double angle = TO_RAD * angle_deg;
    double c = cos(angle);
    double s = sin(angle);

    out[0] = c * in[0] - s * in[1];
    out[1] = s * in[0] + c * in[1];
    out[2] = in[2];
}

static void vec_add(const double a[3], const double b[3], double out[3])
{
    out[0] = a[0] + b[0];
    out[1] = a[1] + b[1];
    out[2] = a[2] + b[2];
}

static void vec_sub(const double a[3], const double b[3], double out[3])
{
    out[0] = a[0] - b[0];
    out[1] = a[1] - b[1];
    out[2] = a[2] - b[2];
}

static double vec_dot(const double a[3], const double b[3])
{
    return (a[0] * b[0]) + (a[1] * b[1]) + (a[2] * b[2]);
}

static void vec_scale(double scale, const double in[3], double out[3])
{
    out[0] = scale * in[0];
    out[1] = scale * in[1];
    out[2] = scale * in[2];
}

static double vec_length(const double in[3])
{
    return sqrt(vec_dot(in, in));
}

static void vec_normalize(const double in[3], double out[3])
{
    double length = vec_length(in);

    if (length <= 1e-12) {
        out[0] = 0.0;
        out[1] = 1.0;
        out[2] = 0.0;
        return;
    }

    out[0] = in[0] / length;
    out[1] = in[1] / length;
    out[2] = in[2] / length;
}

static void rotate_axis(const double axis[3], double angle_deg, const double in[3], double out[3])
{
    double normalized_axis[3];
    double angle = TO_RAD * angle_deg;
    double c = cos(angle);
    double s = sin(angle);
    double dot;
    double cross[3];

    vec_normalize(axis, normalized_axis);
    dot = vec_dot(normalized_axis, in);

    cross[0] = (normalized_axis[1] * in[2]) - (normalized_axis[2] * in[1]);
    cross[1] = (normalized_axis[2] * in[0]) - (normalized_axis[0] * in[2]);
    cross[2] = (normalized_axis[0] * in[1]) - (normalized_axis[1] * in[0]);

    out[0] = (in[0] * c) + (cross[0] * s) + (normalized_axis[0] * dot * (1.0 - c));
    out[1] = (in[1] * c) + (cross[1] * s) + (normalized_axis[1] * dot * (1.0 - c));
    out[2] = (in[2] * c) + (cross[2] * s) + (normalized_axis[2] * dot * (1.0 - c));
}

static void rotate_about_plane_normal(const double x_axis[3],
                                      const double y_axis[3],
                                      double rotation_deg,
                                      double u_axis[3],
                                      double v_axis[3])
{
    double angle = TO_RAD * rotation_deg;
    double c = cos(angle);
    double s = sin(angle);
    double x_term[3];
    double y_term[3];

    vec_scale(c, x_axis, x_term);
    vec_scale(s, y_axis, y_term);
    vec_add(x_term, y_term, u_axis);

    vec_scale(-s, x_axis, x_term);
    vec_scale(c, y_axis, y_term);
    vec_add(x_term, y_term, v_axis);
}

static void effective_angles(double b_cmd, double c_cmd, double *b_eff, double *c_eff)
{
    *b_eff = b_cmd + pinv(haldata->b_zero_offset);
    *c_eff = c_cmd + pinv(haldata->c_zero_offset);
}

static void combined_c_to_b(double out[3])
{
    out[0] = pinv(haldata->nominal_c_to_b_x) + pinv(haldata->cal_c_to_b_x);
    out[1] = pinv(haldata->nominal_c_to_b_y) + pinv(haldata->cal_c_to_b_y);
    out[2] = pinv(haldata->nominal_c_to_b_z) + pinv(haldata->cal_c_to_b_z);
}

static void combined_b_to_tool(double out[3])
{
    out[0] = pinv(haldata->nominal_b_to_tool_x) + pinv(haldata->cal_b_to_tool_x);
    out[1] = pinv(haldata->nominal_b_to_tool_y) + pinv(haldata->cal_b_to_tool_y);
    out[2] = pinv(haldata->nominal_b_to_tool_z) + pinv(haldata->cal_b_to_tool_z);
}

static void c_frame_to_world(const double in[3], double out[3])
{
    double x_tilted[3];

    rotate_x(pinv(haldata->c_axis_tilt_x), in, x_tilted);
    rotate_y(pinv(haldata->c_axis_tilt_y), x_tilted, out);
}

static void local_b_axis(double out[3])
{
    double skewed[3];

    skewed[0] = tan(TO_RAD * pinv(haldata->b_axis_tilt_x));
    skewed[1] = 1.0;
    skewed[2] = tan(TO_RAD * pinv(haldata->b_axis_tilt_z));
    vec_normalize(skewed, out);
}

static void rotary_vector_world(double b_cmd, double c_cmd, const double in[3], double out[3])
{
    double b_eff;
    double c_eff;
    double b_axis[3];
    double b_rotated[3];
    double c_rotated[3];

    effective_angles(b_cmd, c_cmd, &b_eff, &c_eff);
    local_b_axis(b_axis);
    rotate_axis(b_axis, b_eff, in, b_rotated);
    rotate_z(c_eff, b_rotated, c_rotated);
    c_frame_to_world(c_rotated, out);
}

static void c_axis_world(double out[3])
{
    double base_axis[3] = {0.0, 0.0, 1.0};

    c_frame_to_world(base_axis, out);
}

static void b_axis_world(double c_cmd, double out[3])
{
    double b_axis[3];
    double c_rotated[3];
    double b_eff;
    double c_eff;

    effective_angles(0.0, c_cmd, &b_eff, &c_eff);
    (void)b_eff;

    local_b_axis(b_axis);
    rotate_z(c_eff, b_axis, c_rotated);
    c_frame_to_world(c_rotated, out);
}

static void tool_vector_world(double b_cmd, double c_cmd, double out[3])
{
    double base_tool_axis[3] = {0.0, 0.0, -1.0};

    rotary_vector_world(b_cmd, c_cmd, base_tool_axis, out);
}

static void tool_frame_world(double b_cmd, double c_cmd, double u_axis[3], double v_axis[3], double w_axis[3])
{
    double base_u[3] = {1.0, 0.0, 0.0};
    double base_v[3] = {0.0, 1.0, 0.0};
    double base_w[3] = {0.0, 0.0, -1.0};

    rotary_vector_world(b_cmd, c_cmd, base_u, u_axis);
    rotary_vector_world(b_cmd, c_cmd, base_v, v_axis);
    rotary_vector_world(b_cmd, c_cmd, base_w, w_axis);
}

static void b_harmonic_vector(hal_float_t *coeffs[B_HARMONIC_TERMS][3], double b_eff, double out[3])
{
    double b_rad = TO_RAD * b_eff;
    double terms[B_HARMONIC_TERMS] = {
        sin(b_rad),
        1.0 - cos(b_rad),
        sin(2.0 * b_rad),
    };
    int term;
    int axis;

    out[0] = 0.0;
    out[1] = 0.0;
    out[2] = 0.0;

    for (term = 0; term < B_HARMONIC_TERMS; term++) {
        for (axis = 0; axis < 3; axis++) {
            out[axis] += terms[term] * pinv(coeffs[term][axis]);
        }
    }
}

static void b_harmonic_offset_world(double b_cmd, double c_cmd, double out[3])
{
    double b_eff;
    double c_eff;
    double b_rad;
    double c_rad;
    double machine_fixed[3];
    double cframe_local[3];
    double c_rotated[3];
    double cframe_world[3];
    double cross_terms[B_CROSS_TERMS];
    int term;
    int axis;

    out[0] = 0.0;
    out[1] = 0.0;
    out[2] = 0.0;

    if (!pinb(haldata->sim_b_harmonic_enable)) {
        return;
    }

    effective_angles(b_cmd, c_cmd, &b_eff, &c_eff);
    b_rad = TO_RAD * b_eff;
    c_rad = TO_RAD * c_eff;

    b_harmonic_vector(haldata->b_harmonic_machine, b_eff, machine_fixed);
    b_harmonic_vector(haldata->b_harmonic_cframe, b_eff, cframe_local);
    rotate_z(c_eff, cframe_local, c_rotated);
    c_frame_to_world(c_rotated, cframe_world);

    out[0] = machine_fixed[0] + cframe_world[0];
    out[1] = machine_fixed[1] + cframe_world[1];
    out[2] = machine_fixed[2] + cframe_world[2];

    cross_terms[0] = sin(b_rad) * sin(c_rad);
    cross_terms[1] = (1.0 - cos(b_rad)) * sin(c_rad);
    cross_terms[2] = (1.0 - cos(b_rad)) * sin(c_rad) * sin(c_rad);
    cross_terms[3] = sin(b_rad) * cos(c_rad);
    cross_terms[4] = (1.0 - cos(b_rad)) * cos(c_rad);

    for (term = 0; term < B_CROSS_TERMS; term++) {
        for (axis = 0; axis < 3; axis++) {
            out[axis] += cross_terms[term] * pinv(haldata->b_cross_machine[term][axis]);
        }
    }
}

static void tool_offset_world(double b_cmd, double c_cmd, double out[3])
{
    double b_eff;
    double c_eff;
    double c_to_b[3];
    double b_to_tool[3];
    double b_rotated[3];
    double c_frame[3];
    double c_rotated[3];
    double b_axis[3];
    double harmonic[3];

    effective_angles(b_cmd, c_cmd, &b_eff, &c_eff);
    combined_c_to_b(c_to_b);
    combined_b_to_tool(b_to_tool);
    local_b_axis(b_axis);

    rotate_axis(b_axis, b_eff, b_to_tool, b_rotated);

    c_frame[0] = c_to_b[0] + b_rotated[0];
    c_frame[1] = c_to_b[1] + b_rotated[1];
    c_frame[2] = c_to_b[2] + b_rotated[2];

    rotate_z(c_eff, c_frame, c_rotated);
    c_frame_to_world(c_rotated, out);

    b_harmonic_offset_world(b_cmd, c_cmd, harmonic);
    out[0] += harmonic[0];
    out[1] += harmonic[1];
    out[2] += harmonic[2];
}

static void update_debug_pins(double b_cmd, double c_cmd)
{
    double offset[3];
    double vector[3];
    double tool_u[3];
    double tool_v[3];
    double tool_w[3];
    double c_axis[3];
    double b_axis[3];
    int axis;

    tool_offset_world(b_cmd, c_cmd, offset);
    tool_vector_world(b_cmd, c_cmd, vector);
    tool_frame_world(b_cmd, c_cmd, tool_u, tool_v, tool_w);
    c_axis_world(c_axis);
    b_axis_world(c_cmd, b_axis);

    setpin(haldata->tool_offset_x, offset[0]);
    setpin(haldata->tool_offset_y, offset[1]);
    setpin(haldata->tool_offset_z, offset[2]);
    setpin(haldata->tool_vector_x, vector[0]);
    setpin(haldata->tool_vector_y, vector[1]);
    setpin(haldata->tool_vector_z, vector[2]);
    for (axis = 0; axis < 3; axis++) {
        setpin(haldata->tool_frame[0][axis], tool_u[axis]);
        setpin(haldata->tool_frame[1][axis], tool_v[axis]);
        setpin(haldata->tool_frame[2][axis], tool_w[axis]);
    }
    setpin(haldata->c_axis_vector_x, c_axis[0]);
    setpin(haldata->c_axis_vector_y, c_axis[1]);
    setpin(haldata->c_axis_vector_z, c_axis[2]);
    setpin(haldata->b_axis_vector_x, b_axis[0]);
    setpin(haldata->b_axis_vector_y, b_axis[1]);
    setpin(haldata->b_axis_vector_z, b_axis[2]);
}

static void twp_plane_axes(double plane_x[3], double plane_y[3], double plane_z[3])
{
    double base_x[3] = {1.0, 0.0, 0.0};
    double base_y[3] = {0.0, 1.0, 0.0};
    double base_z[3] = {0.0, 0.0, 1.0};
    double stored_plane_x[3];
    double stored_plane_y[3];

    rotary_vector_world(pinv(haldata->twp_b_angle),
                        pinv(haldata->twp_c_angle),
                        base_x,
                        stored_plane_x);
    rotary_vector_world(pinv(haldata->twp_b_angle),
                        pinv(haldata->twp_c_angle),
                        base_y,
                        stored_plane_y);
    rotary_vector_world(pinv(haldata->twp_b_angle),
                        pinv(haldata->twp_c_angle),
                        base_z,
                        plane_z);

    rotate_about_plane_normal(stored_plane_x,
                              stored_plane_y,
                              pinv(haldata->twp_normal_rotation),
                              plane_x,
                              plane_y);
}

static void twp_local_to_world(const double local_xyz[3], double world_xyz[3])
{
    double plane_x[3];
    double plane_y[3];
    double plane_z[3];

    twp_plane_axes(plane_x, plane_y, plane_z);

    world_xyz[0] = pinv(haldata->twp_motion_origin_x)
                 + (local_xyz[0] * plane_x[0])
                 + (local_xyz[1] * plane_y[0])
                 + (local_xyz[2] * plane_z[0]);
    world_xyz[1] = pinv(haldata->twp_motion_origin_y)
                 + (local_xyz[0] * plane_x[1])
                 + (local_xyz[1] * plane_y[1])
                 + (local_xyz[2] * plane_z[1]);
    world_xyz[2] = pinv(haldata->twp_motion_origin_z)
                 + (local_xyz[0] * plane_x[2])
                 + (local_xyz[1] * plane_y[2])
                 + (local_xyz[2] * plane_z[2]);
}

static void twp_world_to_local(const double world_xyz[3], double local_xyz[3])
{
    double plane_x[3];
    double plane_y[3];
    double plane_z[3];
    double origin[3] = {
        pinv(haldata->twp_motion_origin_x),
        pinv(haldata->twp_motion_origin_y),
        pinv(haldata->twp_motion_origin_z),
    };
    double offset[3];

    twp_plane_axes(plane_x, plane_y, plane_z);
    vec_sub(world_xyz, origin, offset);

    local_xyz[0] = vec_dot(offset, plane_x);
    local_xyz[1] = vec_dot(offset, plane_y);
    local_xyz[2] = vec_dot(offset, plane_z);
}

static int headheadKinematicsForward(const double *joints,
                                     EmcPose *pos,
                                     const KINEMATICS_FORWARD_FLAGS *fflags,
                                     KINEMATICS_INVERSE_FLAGS *iflags)
{
    double offset[3];
    double world_xyz[3];
    double local_xyz[3];

    (void)fflags;
    (void)iflags;

    tool_offset_world(joints[JB], joints[JC], offset);
    update_debug_pins(joints[JB], joints[JC]);

    if (pinb(haldata->tcpc_enable) || pinb(haldata->twp_mode)) {
        world_xyz[0] = joints[JX] + offset[0];
        world_xyz[1] = joints[JY] + offset[1];
        world_xyz[2] = joints[JZ] + offset[2];
    } else {
        world_xyz[0] = joints[JX];
        world_xyz[1] = joints[JY];
        world_xyz[2] = joints[JZ];
    }

    if (pinb(haldata->twp_mode)) {
        twp_world_to_local(world_xyz, local_xyz);
        pos->tran.x = local_xyz[0];
        pos->tran.y = local_xyz[1];
        pos->tran.z = local_xyz[2];
    } else {
        pos->tran.x = world_xyz[0];
        pos->tran.y = world_xyz[1];
        pos->tran.z = world_xyz[2];
    }
    pos->b = joints[JB];
    pos->c = joints[JC];
    pos->a = 0.0;
    pos->u = 0.0;
    pos->v = 0.0;
    pos->w = 0.0;

    return 0;
}

static int headheadKinematicsInverse(const EmcPose *pos,
                                     double *joints,
                                     const KINEMATICS_INVERSE_FLAGS *iflags,
                                     KINEMATICS_FORWARD_FLAGS *fflags)
{
    double offset[3];
    EmcPose mapped;
    double tool_xyz[3];

    (void)fflags;
    (void)iflags;

    mapped = *pos;
    if (pinb(haldata->twp_mode)) {
        if (fabs(pos->b - pinv(haldata->twp_b_angle)) > TWP_ROTARY_TOLERANCE_DEG
            || fabs(pos->c - pinv(haldata->twp_c_angle)) > TWP_ROTARY_TOLERANCE_DEG) {
            return -1;
        }
        double local_xyz[3] = {pos->tran.x, pos->tran.y, pos->tran.z};
        twp_local_to_world(local_xyz, tool_xyz);
        mapped.tran.x = tool_xyz[0];
        mapped.tran.y = tool_xyz[1];
        mapped.tran.z = tool_xyz[2];
        mapped.b = pinv(haldata->twp_b_angle);
        mapped.c = pinv(haldata->twp_c_angle);
    }

    update_debug_pins(mapped.b, mapped.c);

    if (pinb(haldata->tcpc_enable) || pinb(haldata->twp_mode)) {
        tool_offset_world(mapped.b, mapped.c, offset);
        mapped.tran.x = mapped.tran.x - offset[0];
        mapped.tran.y = mapped.tran.y - offset[1];
        mapped.tran.z = mapped.tran.z - offset[2];
    }

    position_to_mapped_joints(headhead_max_joints, &mapped, joints);
    return 0;
}

static int new_hal_float_pin(hal_float_t **pin, int dir, const char *name)
{
    return hal_pin_float_newf(dir, pin, comp_id, "headheadkins.%s", name);
}

static int new_hal_bit_pin(hal_bit_t **pin, int dir, const char *name)
{
    return hal_pin_bit_newf(dir, pin, comp_id, "headheadkins.%s", name);
}

static int init_tool_frame_pins(void)
{
    int frame;
    int axis;
    int result;

    for (frame = 0; frame < TOOL_FRAME_AXES; frame++) {
        for (axis = 0; axis < 3; axis++) {
            result = hal_pin_float_newf(HAL_OUT,
                                        &haldata->tool_frame[frame][axis],
                                        comp_id,
                                        "headheadkins.tool-frame-%s.%s",
                                        tool_frame_names[frame],
                                        axis_names[axis]);
            if (result < 0) return result;
        }
    }

    return 0;
}

static int init_b_harmonic_pins(void)
{
    int term;
    int axis;
    int result;

    result = new_hal_bit_pin(&haldata->sim_b_harmonic_enable, HAL_IN, "sim-bharm-enable");
    if (result < 0) return result;

    for (term = 0; term < B_HARMONIC_TERMS; term++) {
        for (axis = 0; axis < 3; axis++) {
            result = hal_pin_float_newf(HAL_IN,
                                        &haldata->b_harmonic_machine[term][axis],
                                        comp_id,
                                        "headheadkins.bharm-m.%s.%s",
                                        b_harmonic_term_names[term],
                                        axis_names[axis]);
            if (result < 0) return result;
            result = hal_pin_float_newf(HAL_IN,
                                        &haldata->b_harmonic_cframe[term][axis],
                                        comp_id,
                                        "headheadkins.bharm-c.%s.%s",
                                        b_harmonic_term_names[term],
                                        axis_names[axis]);
            if (result < 0) return result;
        }
    }

    for (term = 0; term < B_CROSS_TERMS; term++) {
        for (axis = 0; axis < 3; axis++) {
            result = hal_pin_float_newf(HAL_IN,
                                        &haldata->b_cross_machine[term][axis],
                                        comp_id,
                                        "headheadkins.bcross.%s.%s",
                                        b_cross_term_names[term],
                                        axis_names[axis]);
            if (result < 0) return result;
        }
    }

    return 0;
}

static int init_geometry_pins(void)
{
    int result;
    int frame;
    int term;
    int axis;
    int cross_term;

    result = new_hal_float_pin(&haldata->nominal_c_to_b_x, HAL_IN, "nominal-c-to-b.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->nominal_c_to_b_y, HAL_IN, "nominal-c-to-b.y");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->nominal_c_to_b_z, HAL_IN, "nominal-c-to-b.z");
    if (result < 0) return result;

    result = new_hal_float_pin(&haldata->nominal_b_to_tool_x, HAL_IN, "nominal-b-to-tool.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->nominal_b_to_tool_y, HAL_IN, "nominal-b-to-tool.y");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->nominal_b_to_tool_z, HAL_IN, "nominal-b-to-tool.z");
    if (result < 0) return result;

    result = new_hal_float_pin(&haldata->cal_c_to_b_x, HAL_IN, "cal-c-to-b.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->cal_c_to_b_y, HAL_IN, "cal-c-to-b.y");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->cal_c_to_b_z, HAL_IN, "cal-c-to-b.z");
    if (result < 0) return result;

    result = new_hal_float_pin(&haldata->cal_b_to_tool_x, HAL_IN, "cal-b-to-tool.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->cal_b_to_tool_y, HAL_IN, "cal-b-to-tool.y");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->cal_b_to_tool_z, HAL_IN, "cal-b-to-tool.z");
    if (result < 0) return result;

    result = new_hal_float_pin(&haldata->b_zero_offset, HAL_IN, "b-zero-offset");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->c_zero_offset, HAL_IN, "c-zero-offset");
    if (result < 0) return result;

    result = new_hal_float_pin(&haldata->c_axis_tilt_x, HAL_IN, "c-axis-tilt.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->c_axis_tilt_y, HAL_IN, "c-axis-tilt.y");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->b_axis_tilt_x, HAL_IN, "b-axis-tilt.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->b_axis_tilt_z, HAL_IN, "b-axis-tilt.z");
    if (result < 0) return result;

    result = new_hal_float_pin(&haldata->tool_offset_x, HAL_OUT, "tool-offset.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->tool_offset_y, HAL_OUT, "tool-offset.y");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->tool_offset_z, HAL_OUT, "tool-offset.z");
    if (result < 0) return result;

    result = new_hal_float_pin(&haldata->tool_vector_x, HAL_OUT, "tool-vector.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->tool_vector_y, HAL_OUT, "tool-vector.y");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->tool_vector_z, HAL_OUT, "tool-vector.z");
    if (result < 0) return result;
    result = init_tool_frame_pins();
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->c_axis_vector_x, HAL_OUT, "c-axis-vector.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->c_axis_vector_y, HAL_OUT, "c-axis-vector.y");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->c_axis_vector_z, HAL_OUT, "c-axis-vector.z");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->b_axis_vector_x, HAL_OUT, "b-axis-vector.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->b_axis_vector_y, HAL_OUT, "b-axis-vector.y");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->b_axis_vector_z, HAL_OUT, "b-axis-vector.z");
    if (result < 0) return result;
    result = init_b_harmonic_pins();
    if (result < 0) return result;

    result = new_hal_bit_pin(&haldata->tcpc_enable, HAL_IN, "tcpc-enable");
    if (result < 0) return result;
    result = new_hal_bit_pin(&haldata->twp_mode, HAL_IN, "twp-mode");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->twp_motion_origin_x, HAL_IN, "twp-motion-origin.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->twp_motion_origin_y, HAL_IN, "twp-motion-origin.y");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->twp_motion_origin_z, HAL_IN, "twp-motion-origin.z");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->twp_b_angle, HAL_IN, "twp-angle.b");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->twp_c_angle, HAL_IN, "twp-angle.c");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->twp_normal_rotation, HAL_IN, "twp-normal-rotation");
    if (result < 0) return result;

    *haldata->nominal_c_to_b_x = 0.0;
    *haldata->nominal_c_to_b_y = 0.0;
    *haldata->nominal_c_to_b_z = 0.0;

    *haldata->nominal_b_to_tool_x = 0.0;
    *haldata->nominal_b_to_tool_y = 25.0;
    *haldata->nominal_b_to_tool_z = -180.0;

    *haldata->cal_c_to_b_x = 0.0;
    *haldata->cal_c_to_b_y = 0.0;
    *haldata->cal_c_to_b_z = 0.0;

    *haldata->cal_b_to_tool_x = 0.0;
    *haldata->cal_b_to_tool_y = 0.0;
    *haldata->cal_b_to_tool_z = 0.0;

    *haldata->b_zero_offset = 0.0;
    *haldata->c_zero_offset = 0.0;

    *haldata->c_axis_tilt_x = 0.0;
    *haldata->c_axis_tilt_y = 0.0;
    *haldata->b_axis_tilt_x = 0.0;
    *haldata->b_axis_tilt_z = 0.0;

    *haldata->tool_offset_x = 0.0;
    *haldata->tool_offset_y = 25.0;
    *haldata->tool_offset_z = -180.0;
    *haldata->tool_vector_x = 0.0;
    *haldata->tool_vector_y = 0.0;
    *haldata->tool_vector_z = -1.0;
    for (frame = 0; frame < TOOL_FRAME_AXES; frame++) {
        for (axis = 0; axis < 3; axis++) {
            *haldata->tool_frame[frame][axis] = 0.0;
        }
    }
    *haldata->tool_frame[0][0] = 1.0;
    *haldata->tool_frame[1][1] = 1.0;
    *haldata->tool_frame[2][2] = -1.0;
    *haldata->c_axis_vector_x = 0.0;
    *haldata->c_axis_vector_y = 0.0;
    *haldata->c_axis_vector_z = 1.0;
    *haldata->b_axis_vector_x = 0.0;
    *haldata->b_axis_vector_y = 1.0;
    *haldata->b_axis_vector_z = 0.0;

    *haldata->sim_b_harmonic_enable = 0;
    for (term = 0; term < B_HARMONIC_TERMS; term++) {
        for (axis = 0; axis < 3; axis++) {
            *haldata->b_harmonic_machine[term][axis] = 0.0;
            *haldata->b_harmonic_cframe[term][axis] = 0.0;
        }
    }
    for (cross_term = 0; cross_term < B_CROSS_TERMS; cross_term++) {
        for (axis = 0; axis < 3; axis++) {
            *haldata->b_cross_machine[cross_term][axis] = 0.0;
        }
    }

    *haldata->tcpc_enable = 1;
    *haldata->twp_mode = 0;
    *haldata->twp_motion_origin_x = 0.0;
    *haldata->twp_motion_origin_y = 0.0;
    *haldata->twp_motion_origin_z = 0.0;
    *haldata->twp_b_angle = 0.0;
    *haldata->twp_c_angle = 0.0;
    *haldata->twp_normal_rotation = 0.0;

    return 0;
}

int kinematicsForward(const double *joints,
                      EmcPose *pos,
                      const KINEMATICS_FORWARD_FLAGS *fflags,
                      KINEMATICS_INVERSE_FLAGS *iflags)
{
    return headheadKinematicsForward(joints, pos, fflags, iflags);
}

int kinematicsInverse(const EmcPose *pos,
                      double *joints,
                      const KINEMATICS_INVERSE_FLAGS *iflags,
                      KINEMATICS_FORWARD_FLAGS *fflags)
{
    return headheadKinematicsInverse(pos, joints, iflags, fflags);
}

KINEMATICS_TYPE kinematicsType(void)
{
    return ktype;
}

KINS_NOT_SWITCHABLE
EXPORT_SYMBOL(kinematicsType);
EXPORT_SYMBOL(kinematicsForward);
EXPORT_SYMBOL(kinematicsInverse);
MODULE_LICENSE("GPL");

int rtapi_app_main(void)
{
    int axis_idx_for_jno[EMCMOT_MAX_JOINTS];
    int i;
    kparms ksetup;

    switch (*kinstype) {
    case '1':
        ktype = KINEMATICS_IDENTITY;
        break;
    case 'b':
    case 'B':
    default:
        ktype = KINEMATICS_BOTH;
        break;
    }

    comp_id = hal_init("headheadkins");
    if (comp_id < 0) {
        return comp_id;
    }

    ksetup.max_joints = EMCMOT_MAX_JOINTS;
    ksetup.allow_duplicates = 1;
    ksetup.required_coordinates = REQUIRED_COORDINATES;

    if (map_coordinates_to_jnumbers(coordinates,
                                    ksetup.max_joints,
                                    ksetup.allow_duplicates,
                                    axis_idx_for_jno)) {
        hal_exit(comp_id);
        return -1;
    }

    for (i = 0; REQUIRED_COORDINATES[i] != '\0'; i++) {
        char reqd = REQUIRED_COORDINATES[i];
        if (!strchr(coordinates, reqd) && !strchr(coordinates, tolower(reqd))) {
            rtapi_print_msg(RTAPI_MSG_ERR,
                            "headheadkins: coordinates=%s must include %s\n",
                            coordinates,
                            REQUIRED_COORDINATES);
            hal_exit(comp_id);
            return -1;
        }
    }

    headhead_max_joints = strlen(coordinates);
    for (i = 0; i < EMCMOT_MAX_JOINTS; i++) {
        if (axis_idx_for_jno[i] == 0 && JX == -1) JX = i;
        if (axis_idx_for_jno[i] == 1 && JY == -1) JY = i;
        if (axis_idx_for_jno[i] == 2 && JZ == -1) JZ = i;
        if (axis_idx_for_jno[i] == 4 && JB == -1) JB = i;
        if (axis_idx_for_jno[i] == 5 && JC == -1) JC = i;
    }

    haldata = hal_malloc(sizeof(struct haldata));
    if (!haldata) {
        hal_exit(comp_id);
        return -1;
    }

    if (init_geometry_pins() < 0) {
        hal_exit(comp_id);
        return -1;
    }

    rtapi_print_msg(RTAPI_MSG_INFO,
                    "headheadkins: coordinates=%s JX=%d JY=%d JZ=%d JB=%d JC=%d\n",
                    coordinates, JX, JY, JZ, JB, JC);
    rtapi_print_msg(RTAPI_MSG_INFO,
                    "headheadkins: default nominal-b-to-tool=(%.3f, %.3f, %.3f)\n",
                    *haldata->nominal_b_to_tool_x,
                    *haldata->nominal_b_to_tool_y,
                    *haldata->nominal_b_to_tool_z);

    hal_ready(comp_id);
    return 0;
}

void rtapi_app_exit(void)
{
    hal_exit(comp_id);
}
