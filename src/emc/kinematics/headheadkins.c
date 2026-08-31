/********************************************************************
* Description: headheadkins.c
*   Parameterized head-head XYZBC kinematics scaffold.
*
*   This model assumes:
*   - X/Y/Z joints locate the C-axis pivot center in world space
*   - C rotates about +Z
*   - B rotates about +Y in the C-rotated frame
*   - world XYZ are the tool-reference point coordinates when the TCPC
*     origin is zero, or a continuous TCPC program frame when TCPC is
*     entered live from G-code
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
#define C_HARMONIC_TERMS 4
#define B_MID_TERMS 5
#define B_CROSS_TERMS 7
#define LENGTH_DIFF_TERMS 5
#define LENGTH_XY_TOLERANCE_MM 1e-6
#define LENGTH_HARD_MIN_MM 100.0
#define LENGTH_HARD_MAX_MM 430.0
#define LENGTH_MAX_TOLERANCE_MM 0.002
#define LENGTH_REFERENCE_MM 229.407000
#define LENGTH_SPAN_MM 100.800271
#define LENGTH_MAX_DIFF_NORM_MM 0.400
#define LENGTH_MAX_TOTAL_NORM_MM 1.350
#define LENGTH_CONFIG_TOLERANCE 1e-9

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

    hal_float_t *active_tool_offset_x;
    hal_float_t *active_tool_offset_y;
    hal_float_t *active_tool_offset_z;

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
    hal_float_t *c_harmonic_machine[C_HARMONIC_TERMS][3];
    hal_float_t *b_mid_machine[B_MID_TERMS][3];
    hal_float_t *b_cross_machine[B_CROSS_TERMS][3];

    hal_float_t *length_model_reference;
    hal_float_t *length_model_span;
    hal_float_t *length_model_minimum;
    hal_float_t *length_model_maximum;
    hal_float_t *length_model_tolerance;
    hal_float_t *length_model_max_diff_norm;
    hal_float_t *length_model_max_total_norm;
    hal_s32_t *length_model_id;
    hal_s32_t *length_model_expected_id;
    hal_float_t *length_diff[LENGTH_DIFF_TERMS][3];
    hal_bit_t *length_model_configured;
    hal_bit_t *length_model_valid;
    hal_s32_t *length_model_fault_code;
    hal_float_t *length_model_q;
    hal_float_t *length_model_diff_offset[3];
    hal_float_t *length_model_diff_norm;
    hal_float_t *empirical_offset[3];
    hal_float_t *empirical_offset_norm;
    hal_float_t *tool_offset_eval_b;
    hal_float_t *tool_offset_eval_c;
    hal_float_t *tool_offset_eval_length;

    hal_bit_t *tcpc_enable;
    hal_float_t *tcpc_origin_x;
    hal_float_t *tcpc_origin_y;
    hal_float_t *tcpc_origin_z;
    hal_bit_t *twp_mode;
    hal_float_t *twp_motion_origin_x;
    hal_float_t *twp_motion_origin_y;
    hal_float_t *twp_motion_origin_z;
    hal_float_t *twp_b_angle;
    hal_float_t *twp_c_angle;
    hal_float_t *twp_normal_rotation;
    hal_float_t *twp_coordinate_offset_x;
    hal_float_t *twp_coordinate_offset_y;
    hal_float_t *twp_coordinate_offset_z;
    hal_float_t *twp_captured_origin_x;
    hal_float_t *twp_captured_origin_y;
    hal_float_t *twp_captured_origin_z;
    hal_bit_t *kinstype_is_world;
    hal_bit_t *kinstype_is_twp;
    hal_bit_t *kinstype_frame_ready;
} *haldata;

static int comp_id;
static int headhead_max_joints;
static int switchkins_type;
static int capture_twp_origin_on_forward;

struct synchronized_twp_frame {
    double b_angle;
    double c_angle;
    double normal_rotation;
    double coordinate_offset[3];
    double captured_origin[3];
    double tcpc_origin[3];
    int valid;
};

static struct synchronized_twp_frame active_twp_frame;

static KINEMATICS_TYPE ktype = KINEMATICS_BOTH;

static char *coordinates = REQUIRED_COORDINATES;
RTAPI_MP_STRING(coordinates, "Existing axes, must include XYZBC");

static char *kinstype = "b";
RTAPI_MP_STRING(kinstype, "Kinematics type (Identity, Both)");

static int lengthmodel = 0;
RTAPI_MP_INT(lengthmodel, "Enable fail-closed active-tool-length empirical model");

static int lengthmodelid = 0;
RTAPI_MP_INT(lengthmodelid, "Expected HAL coefficient-set ID for the length model");

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
static const char *c_harmonic_term_names[C_HARMONIC_TERMS] = {
    "cos",
    "sin",
    "cos2",
    "sin2",
};
static const char *b_mid_term_names[B_MID_TERMS] = {
    "base",
    "cosc",
    "sinc",
    "cos2c",
    "sin2c",
};
static const char *b_cross_term_names[B_CROSS_TERMS] = {
    "sinb-sinc",
    "omcb-sinc",
    "omcb-sin2c",
    "sinb-cosc",
    "omcb-cosc",
    "sinb-sin2c",
    "sinb-cos2c",
};
static const char *length_diff_term_names[LENGTH_DIFF_TERMS] = {
    "c-cos",
    "c-sin",
    "b-sin",
    "sinb-sinc",
    "sinb-cosc",
};

enum length_model_fault {
    LENGTH_MODEL_OK = 0,
    LENGTH_MODEL_CONFIG_INVALID = 1,
    LENGTH_MODEL_ID_MISMATCH = 2,
    LENGTH_MODEL_TOOL_OFFSET_NONFINITE = 3,
    LENGTH_MODEL_TOOL_XY_UNSUPPORTED = 4,
    LENGTH_MODEL_LENGTH_OUT_OF_RANGE = 5,
    LENGTH_MODEL_COMMON_DISABLED = 6,
    LENGTH_MODEL_CORRECTION_NONFINITE = 7,
    LENGTH_MODEL_DIFF_NORM_EXCEEDED = 8,
    LENGTH_MODEL_TOTAL_NORM_EXCEEDED = 9,
    LENGTH_MODEL_TRANSFORM_NONFINITE = 10,
};

struct active_tool_offset {
    double x;
    double y;
    double z;
};

struct empirical_evaluation {
    double common[3];
    double differential[3];
    double total[3];
    double q;
    double length;
    int valid;
    int fault;
};

struct tool_offset_evaluation {
    double offset[3];
    struct empirical_evaluation empirical;
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

static void snapshot_active_tool_offset(struct active_tool_offset *offset)
{
    offset->x = pinv(haldata->active_tool_offset_x);
    offset->y = pinv(haldata->active_tool_offset_y);
    offset->z = pinv(haldata->active_tool_offset_z);
}

static void combined_b_to_tool(const struct active_tool_offset *active_tool,
                               double out[3])
{
    out[0] = pinv(haldata->nominal_b_to_tool_x) + pinv(haldata->cal_b_to_tool_x)
        + active_tool->x;
    out[1] = pinv(haldata->nominal_b_to_tool_y) + pinv(haldata->cal_b_to_tool_y)
        + active_tool->y;
    out[2] = pinv(haldata->nominal_b_to_tool_z) + pinv(haldata->cal_b_to_tool_z)
        - active_tool->z;
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

static void b_mid_vector(hal_float_t *coeffs[B_MID_TERMS][3],
                         double b_eff,
                         double c_eff,
                         double out[3])
{
    double b_rad = TO_RAD * b_eff;
    double c_rad = TO_RAD * c_eff;
    double mid_b = sin(2.0 * b_rad) * sin(2.0 * b_rad);
    double terms[B_MID_TERMS] = {
        mid_b,
        mid_b * cos(c_rad),
        mid_b * sin(c_rad),
        mid_b * cos(2.0 * c_rad),
        mid_b * sin(2.0 * c_rad),
    };
    int term;
    int axis;

    out[0] = 0.0;
    out[1] = 0.0;
    out[2] = 0.0;

    for (term = 0; term < B_MID_TERMS; term++) {
        for (axis = 0; axis < 3; axis++) {
            out[axis] += terms[term] * pinv(coeffs[term][axis]);
        }
    }
}

static void c_harmonic_vector(hal_float_t *coeffs[C_HARMONIC_TERMS][3],
                              double c_eff,
                              double c_ref,
                              double out[3])
{
    double c_rad = TO_RAD * c_eff;
    double c_ref_rad = TO_RAD * c_ref;
    double terms[C_HARMONIC_TERMS] = {
        cos(c_rad) - cos(c_ref_rad),
        sin(c_rad) - sin(c_ref_rad),
        cos(2.0 * c_rad) - cos(2.0 * c_ref_rad),
        sin(2.0 * c_rad) - sin(2.0 * c_ref_rad),
    };
    int term;
    int axis;

    out[0] = 0.0;
    out[1] = 0.0;
    out[2] = 0.0;

    for (term = 0; term < C_HARMONIC_TERMS; term++) {
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
    double c_machine_fixed[3];
    double b_mid_fixed[3];
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
    b_mid_vector(haldata->b_mid_machine, b_eff, c_eff, b_mid_fixed);
    c_harmonic_vector(haldata->c_harmonic_machine,
                      c_eff,
                      pinv(haldata->c_zero_offset),
                      c_machine_fixed);
    b_harmonic_vector(haldata->b_harmonic_cframe, b_eff, cframe_local);
    rotate_z(c_eff, cframe_local, c_rotated);
    c_frame_to_world(c_rotated, cframe_world);

    out[0] = machine_fixed[0] + b_mid_fixed[0] + c_machine_fixed[0] + cframe_world[0];
    out[1] = machine_fixed[1] + b_mid_fixed[1] + c_machine_fixed[1] + cframe_world[1];
    out[2] = machine_fixed[2] + b_mid_fixed[2] + c_machine_fixed[2] + cframe_world[2];

    cross_terms[0] = sin(b_rad) * sin(c_rad);
    cross_terms[1] = (1.0 - cos(b_rad)) * sin(c_rad);
    cross_terms[2] = (1.0 - cos(b_rad)) * sin(c_rad) * sin(c_rad);
    cross_terms[3] = sin(b_rad) * cos(c_rad);
    cross_terms[4] = (1.0 - cos(b_rad)) * cos(c_rad);
    cross_terms[5] = sin(b_rad) * sin(2.0 * c_rad);
    cross_terms[6] = sin(b_rad) * cos(2.0 * c_rad);

    for (term = 0; term < B_CROSS_TERMS; term++) {
        for (axis = 0; axis < 3; axis++) {
            out[axis] += cross_terms[term] * pinv(haldata->b_cross_machine[term][axis]);
        }
    }
}

static int vec_is_finite(const double vector[3])
{
    return isfinite(vector[0]) && isfinite(vector[1]) && isfinite(vector[2]);
}

static void length_differential_offset_world(double b_cmd, double c_cmd, double out[3])
{
    double b_eff;
    double c_eff;
    double b_rad;
    double c_rad;
    double c_ref_rad;
    double terms[LENGTH_DIFF_TERMS];
    int term;
    int axis;

    effective_angles(b_cmd, c_cmd, &b_eff, &c_eff);
    b_rad = TO_RAD * b_eff;
    c_rad = TO_RAD * c_eff;
    c_ref_rad = TO_RAD * pinv(haldata->c_zero_offset);
    terms[0] = cos(c_rad) - cos(c_ref_rad);
    terms[1] = sin(c_rad) - sin(c_ref_rad);
    terms[2] = sin(b_rad);
    terms[3] = sin(b_rad) * sin(c_rad);
    terms[4] = sin(b_rad) * cos(c_rad);

    out[0] = 0.0;
    out[1] = 0.0;
    out[2] = 0.0;
    for (term = 0; term < LENGTH_DIFF_TERMS; term++) {
        for (axis = 0; axis < 3; axis++) {
            out[axis] += terms[term] * pinv(haldata->length_diff[term][axis]);
        }
    }
}

static void evaluate_empirical_offset(double b_cmd,
                                      double c_cmd,
                                      const struct active_tool_offset *active_tool,
                                      struct empirical_evaluation *evaluation)
{
    double reference;
    double span;
    double minimum;
    double maximum;
    double tolerance;
    double max_diff_norm;
    double max_total_norm;
    double active_x;
    double active_y;
    double endpoint_diff[3];
    hal_s32_t model_id_begin;
    int axis;

    evaluation->common[0] = 0.0;
    evaluation->common[1] = 0.0;
    evaluation->common[2] = 0.0;
    evaluation->differential[0] = 0.0;
    evaluation->differential[1] = 0.0;
    evaluation->differential[2] = 0.0;
    evaluation->total[0] = 0.0;
    evaluation->total[1] = 0.0;
    evaluation->total[2] = 0.0;
    evaluation->q = 0.0;
    evaluation->length = active_tool->z;
    evaluation->valid = 1;
    evaluation->fault = LENGTH_MODEL_OK;

    if (!lengthmodel) {
        b_harmonic_offset_world(b_cmd, c_cmd, evaluation->common);
        evaluation->total[0] = evaluation->common[0];
        evaluation->total[1] = evaluation->common[1];
        evaluation->total[2] = evaluation->common[2];
        return;
    }

    evaluation->valid = 0;
    if (lengthmodelid <= 0 || !haldata->length_model_id) {
        evaluation->fault = LENGTH_MODEL_ID_MISMATCH;
        return;
    }
    model_id_begin = *haldata->length_model_id;
    if (model_id_begin != lengthmodelid) {
        evaluation->fault = LENGTH_MODEL_ID_MISMATCH;
        return;
    }

    reference = pinv(haldata->length_model_reference);
    span = pinv(haldata->length_model_span);
    minimum = pinv(haldata->length_model_minimum);
    maximum = pinv(haldata->length_model_maximum);
    tolerance = pinv(haldata->length_model_tolerance);
    max_diff_norm = pinv(haldata->length_model_max_diff_norm);
    max_total_norm = pinv(haldata->length_model_max_total_norm);
    active_x = active_tool->x;
    active_y = active_tool->y;

    if (!isfinite(reference) || !isfinite(span) || !isfinite(minimum)
        || !isfinite(maximum) || !isfinite(tolerance)
        || !isfinite(max_diff_norm) || !isfinite(max_total_norm)
        || fabs(reference - LENGTH_REFERENCE_MM) > LENGTH_CONFIG_TOLERANCE
        || fabs(span - LENGTH_SPAN_MM) > LENGTH_CONFIG_TOLERANCE
        || minimum < LENGTH_HARD_MIN_MM
        || maximum > LENGTH_HARD_MAX_MM || maximum < minimum
        || tolerance < 0.0 || tolerance > LENGTH_MAX_TOLERANCE_MM
        || max_diff_norm <= 0.0 || max_diff_norm > LENGTH_MAX_DIFF_NORM_MM
        || max_total_norm <= 0.0 || max_total_norm > LENGTH_MAX_TOTAL_NORM_MM) {
        evaluation->fault = LENGTH_MODEL_CONFIG_INVALID;
        return;
    }
    if (!isfinite(active_x) || !isfinite(active_y) || !isfinite(evaluation->length)) {
        evaluation->fault = LENGTH_MODEL_TOOL_OFFSET_NONFINITE;
        return;
    }
    if (fabs(active_x) > LENGTH_XY_TOLERANCE_MM
        || fabs(active_y) > LENGTH_XY_TOLERANCE_MM) {
        evaluation->fault = LENGTH_MODEL_TOOL_XY_UNSUPPORTED;
        return;
    }

    evaluation->q = (reference - evaluation->length) / span;
    if (evaluation->length <= 0.0
        || evaluation->length < minimum - tolerance
        || evaluation->length > maximum + tolerance) {
        evaluation->fault = LENGTH_MODEL_LENGTH_OUT_OF_RANGE;
        return;
    }
    if (!pinb(haldata->sim_b_harmonic_enable)) {
        evaluation->fault = LENGTH_MODEL_COMMON_DISABLED;
        return;
    }

    b_harmonic_offset_world(b_cmd, c_cmd, evaluation->common);
    evaluation->total[0] = evaluation->common[0];
    evaluation->total[1] = evaluation->common[1];
    evaluation->total[2] = evaluation->common[2];
    length_differential_offset_world(b_cmd, c_cmd, endpoint_diff);
    for (axis = 0; axis < 3; axis++) {
        evaluation->differential[axis] = evaluation->q * endpoint_diff[axis];
        evaluation->total[axis] = evaluation->common[axis] + evaluation->differential[axis];
    }
    if (!isfinite(evaluation->q) || !vec_is_finite(evaluation->common)
        || !vec_is_finite(evaluation->differential) || !vec_is_finite(evaluation->total)) {
        evaluation->fault = LENGTH_MODEL_CORRECTION_NONFINITE;
        return;
    }
    if (vec_length(evaluation->differential) > max_diff_norm) {
        evaluation->fault = LENGTH_MODEL_DIFF_NORM_EXCEEDED;
        return;
    }
    if (vec_length(evaluation->total) > max_total_norm) {
        evaluation->fault = LENGTH_MODEL_TOTAL_NORM_EXCEEDED;
        return;
    }
    if (*haldata->length_model_id != model_id_begin) {
        evaluation->fault = LENGTH_MODEL_ID_MISMATCH;
        return;
    }

    evaluation->valid = 1;
}

static void evaluate_tool_offset_world(double b_cmd,
                                       double c_cmd,
                                       const struct active_tool_offset *active_tool,
                                       struct tool_offset_evaluation *evaluation)
{
    double b_eff;
    double c_eff;
    double c_to_b[3];
    double b_to_tool[3];
    double b_rotated[3];
    double c_frame[3];
    double c_rotated[3];
    double b_axis[3];

    effective_angles(b_cmd, c_cmd, &b_eff, &c_eff);
    combined_c_to_b(c_to_b);
    combined_b_to_tool(active_tool, b_to_tool);
    local_b_axis(b_axis);

    rotate_axis(b_axis, b_eff, b_to_tool, b_rotated);

    c_frame[0] = c_to_b[0] + b_rotated[0];
    c_frame[1] = c_to_b[1] + b_rotated[1];
    c_frame[2] = c_to_b[2] + b_rotated[2];

    rotate_z(c_eff, c_frame, c_rotated);
    c_frame_to_world(c_rotated, evaluation->offset);

    evaluate_empirical_offset(b_cmd, c_cmd, active_tool, &evaluation->empirical);
    evaluation->offset[0] += evaluation->empirical.total[0];
    evaluation->offset[1] += evaluation->empirical.total[1];
    evaluation->offset[2] += evaluation->empirical.total[2];
    if (lengthmodel && evaluation->empirical.valid
        && !vec_is_finite(evaluation->offset)) {
        evaluation->empirical.valid = 0;
        evaluation->empirical.fault = LENGTH_MODEL_TRANSFORM_NONFINITE;
    }
}

static void tcpc_origin(double out[3])
{
    out[0] = pinv(haldata->tcpc_origin_x);
    out[1] = pinv(haldata->tcpc_origin_y);
    out[2] = pinv(haldata->tcpc_origin_z);
}

static int twp_parameters_are_finite(void)
{
    return isfinite(pinv(haldata->twp_motion_origin_x))
        && isfinite(pinv(haldata->twp_motion_origin_y))
        && isfinite(pinv(haldata->twp_motion_origin_z))
        && isfinite(pinv(haldata->twp_b_angle))
        && isfinite(pinv(haldata->twp_c_angle))
        && isfinite(pinv(haldata->twp_normal_rotation));
}

static int synchronized_twp_inputs_are_finite(void)
{
    return isfinite(pinv(haldata->twp_coordinate_offset_x))
        && isfinite(pinv(haldata->twp_coordinate_offset_y))
        && isfinite(pinv(haldata->twp_coordinate_offset_z))
        && isfinite(pinv(haldata->twp_b_angle))
        && isfinite(pinv(haldata->twp_c_angle))
        && isfinite(pinv(haldata->twp_normal_rotation));
}

static int synchronized_twp_frame_is_finite(void)
{
    return active_twp_frame.valid
        && isfinite(active_twp_frame.b_angle)
        && isfinite(active_twp_frame.c_angle)
        && isfinite(active_twp_frame.normal_rotation)
        && vec_is_finite(active_twp_frame.coordinate_offset)
        && vec_is_finite(active_twp_frame.captured_origin)
        && vec_is_finite(active_twp_frame.tcpc_origin);
}

static int wrapped_angle_delta(double current, double reference, double *delta)
{
    double current_mod;
    double reference_mod;

    if (!isfinite(current) || !isfinite(reference) || delta == NULL) return -1;
    current_mod = fmod(current, 360.0);
    reference_mod = fmod(reference, 360.0);
    *delta = fmod(current_mod - reference_mod, 360.0);
    if (*delta > 180.0) *delta -= 360.0;
    if (*delta < -180.0) *delta += 360.0;
    return isfinite(*delta) ? 0 : -1;
}

static void update_debug_pins(double b_cmd,
                              double c_cmd,
                              const struct tool_offset_evaluation *evaluation)
{
    double vector[3];
    double tool_u[3];
    double tool_v[3];
    double tool_w[3];
    double c_axis[3];
    double b_axis[3];
    int axis;

    tool_vector_world(b_cmd, c_cmd, vector);
    tool_frame_world(b_cmd, c_cmd, tool_u, tool_v, tool_w);
    c_axis_world(c_axis);
    b_axis_world(c_cmd, b_axis);

    setpin(haldata->tool_offset_x, evaluation->offset[0]);
    setpin(haldata->tool_offset_y, evaluation->offset[1]);
    setpin(haldata->tool_offset_z, evaluation->offset[2]);
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

    if (haldata->length_model_configured) {
        *haldata->length_model_configured = lengthmodel ? 1 : 0;
    }
    if (haldata->length_model_valid) {
        *haldata->length_model_valid = evaluation->empirical.valid ? 1 : 0;
    }
    if (haldata->length_model_fault_code) {
        *haldata->length_model_fault_code = evaluation->empirical.fault;
    }
    setpin(haldata->length_model_q, evaluation->empirical.q);
    for (axis = 0; axis < 3; axis++) {
        setpin(haldata->length_model_diff_offset[axis],
               evaluation->empirical.differential[axis]);
        setpin(haldata->empirical_offset[axis], evaluation->empirical.total[axis]);
    }
    setpin(haldata->length_model_diff_norm,
           vec_length(evaluation->empirical.differential));
    setpin(haldata->empirical_offset_norm, vec_length(evaluation->empirical.total));
    setpin(haldata->tool_offset_eval_b, b_cmd);
    setpin(haldata->tool_offset_eval_c, c_cmd);
    setpin(haldata->tool_offset_eval_length, evaluation->empirical.length);
}

static void twp_plane_axes_for(double b_angle,
                               double c_angle,
                               double normal_rotation,
                               double plane_x[3],
                               double plane_y[3],
                               double plane_z[3])
{
    double base_x[3] = {1.0, 0.0, 0.0};
    double base_y[3] = {0.0, 1.0, 0.0};
    double base_z[3] = {0.0, 0.0, 1.0};
    double stored_plane_x[3];
    double stored_plane_y[3];

    rotary_vector_world(b_angle, c_angle, base_x, stored_plane_x);
    rotary_vector_world(b_angle, c_angle, base_y, stored_plane_y);
    rotary_vector_world(b_angle, c_angle, base_z, plane_z);

    rotate_about_plane_normal(stored_plane_x,
                              stored_plane_y,
                              normal_rotation,
                              plane_x,
                              plane_y);
}

static void twp_plane_axes(double plane_x[3], double plane_y[3], double plane_z[3])
{
    twp_plane_axes_for(pinv(haldata->twp_b_angle),
                       pinv(haldata->twp_c_angle),
                       pinv(haldata->twp_normal_rotation),
                       plane_x,
                       plane_y,
                       plane_z);
}

static void synchronized_twp_plane_axes(double plane_x[3],
                                        double plane_y[3],
                                        double plane_z[3])
{
    twp_plane_axes_for(active_twp_frame.b_angle,
                       active_twp_frame.c_angle,
                       active_twp_frame.normal_rotation,
                       plane_x,
                       plane_y,
                       plane_z);
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

static void synchronized_twp_local_to_world(const double local_xyz[3],
                                            double world_xyz[3])
{
    double plane_x[3];
    double plane_y[3];
    double plane_z[3];
    double local_delta[3] = {
        local_xyz[0] - active_twp_frame.coordinate_offset[0],
        local_xyz[1] - active_twp_frame.coordinate_offset[1],
        local_xyz[2] - active_twp_frame.coordinate_offset[2],
    };

    synchronized_twp_plane_axes(plane_x, plane_y, plane_z);
    world_xyz[0] = active_twp_frame.captured_origin[0]
                 + (local_delta[0] * plane_x[0])
                 + (local_delta[1] * plane_y[0])
                 + (local_delta[2] * plane_z[0]);
    world_xyz[1] = active_twp_frame.captured_origin[1]
                 + (local_delta[0] * plane_x[1])
                 + (local_delta[1] * plane_y[1])
                 + (local_delta[2] * plane_z[1]);
    world_xyz[2] = active_twp_frame.captured_origin[2]
                 + (local_delta[0] * plane_x[2])
                 + (local_delta[1] * plane_y[2])
                 + (local_delta[2] * plane_z[2]);
}

static void synchronized_twp_world_to_local(const double world_xyz[3],
                                            double local_xyz[3])
{
    double plane_x[3];
    double plane_y[3];
    double plane_z[3];
    double origin[3] = {
        active_twp_frame.captured_origin[0],
        active_twp_frame.captured_origin[1],
        active_twp_frame.captured_origin[2],
    };
    double world_delta[3];

    synchronized_twp_plane_axes(plane_x, plane_y, plane_z);
    vec_sub(world_xyz, origin, world_delta);
    local_xyz[0] = vec_dot(world_delta, plane_x)
                 + active_twp_frame.coordinate_offset[0];
    local_xyz[1] = vec_dot(world_delta, plane_y)
                 + active_twp_frame.coordinate_offset[1];
    local_xyz[2] = vec_dot(world_delta, plane_z)
                 + active_twp_frame.coordinate_offset[2];
}

static int headheadKinematicsForward(const double *joints,
                                     EmcPose *pos,
                                     const KINEMATICS_FORWARD_FLAGS *fflags,
                                     KINEMATICS_INVERSE_FLAGS *iflags,
                                     int twp_enabled,
                                     int synchronized_twp)
{
    struct tool_offset_evaluation evaluation;
    struct active_tool_offset active_tool;
    double origin[3];
    double world_xyz[3];
    double local_xyz[3];
    int tcpc_enabled;
    int twp_parameters_valid;

    (void)fflags;
    (void)iflags;

    tcpc_enabled = pinb(haldata->tcpc_enable);
    twp_parameters_valid = !twp_enabled
        || (synchronized_twp
            ? synchronized_twp_frame_is_finite()
            : twp_parameters_are_finite());
    if (synchronized_twp) {
        origin[0] = active_twp_frame.tcpc_origin[0];
        origin[1] = active_twp_frame.tcpc_origin[1];
        origin[2] = active_twp_frame.tcpc_origin[2];
    } else {
        tcpc_origin(origin);
    }
    snapshot_active_tool_offset(&active_tool);
    evaluate_tool_offset_world(joints[JB], joints[JC], &active_tool, &evaluation);
    if (lengthmodel && (tcpc_enabled || twp_enabled)
        && (!vec_is_finite(origin)
            || !twp_parameters_valid)) {
        evaluation.empirical.valid = 0;
        evaluation.empirical.fault = LENGTH_MODEL_TRANSFORM_NONFINITE;
    }
    update_debug_pins(joints[JB], joints[JC], &evaluation);
    if (lengthmodel && (tcpc_enabled || twp_enabled)
        && !evaluation.empirical.valid) {
        return -1;
    }

    if (tcpc_enabled || twp_enabled) {
        world_xyz[0] = joints[JX] + evaluation.offset[0] - origin[0];
        world_xyz[1] = joints[JY] + evaluation.offset[1] - origin[1];
        world_xyz[2] = joints[JZ] + evaluation.offset[2] - origin[2];
    } else {
        world_xyz[0] = joints[JX];
        world_xyz[1] = joints[JY];
        world_xyz[2] = joints[JZ];
    }

    if (twp_enabled) {
        if (synchronized_twp && capture_twp_origin_on_forward) {
            active_twp_frame.captured_origin[0] = world_xyz[0];
            active_twp_frame.captured_origin[1] = world_xyz[1];
            active_twp_frame.captured_origin[2] = world_xyz[2];
            setpin(haldata->twp_captured_origin_x, world_xyz[0]);
            setpin(haldata->twp_captured_origin_y, world_xyz[1]);
            setpin(haldata->twp_captured_origin_z, world_xyz[2]);
            capture_twp_origin_on_forward = 0;
        }
        if (synchronized_twp) {
            synchronized_twp_world_to_local(world_xyz, local_xyz);
        } else {
            twp_world_to_local(world_xyz, local_xyz);
        }
        if (lengthmodel && !vec_is_finite(local_xyz)) {
            evaluation.empirical.valid = 0;
            evaluation.empirical.fault = LENGTH_MODEL_TRANSFORM_NONFINITE;
            update_debug_pins(joints[JB], joints[JC], &evaluation);
            return -1;
        }
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
                                     KINEMATICS_FORWARD_FLAGS *fflags,
                                     int twp_enabled,
                                     int synchronized_twp)
{
    struct tool_offset_evaluation evaluation;
    struct active_tool_offset active_tool;
    double origin[3];
    EmcPose mapped;
    double tool_xyz[3];
    int tcpc_enabled;
    int twp_parameters_valid;

    (void)fflags;
    (void)iflags;

    tcpc_enabled = pinb(haldata->tcpc_enable);
    twp_parameters_valid = !twp_enabled
        || (synchronized_twp
            ? synchronized_twp_frame_is_finite()
            : twp_parameters_are_finite());
    if (synchronized_twp) {
        origin[0] = active_twp_frame.tcpc_origin[0];
        origin[1] = active_twp_frame.tcpc_origin[1];
        origin[2] = active_twp_frame.tcpc_origin[2];
    } else {
        tcpc_origin(origin);
    }
    snapshot_active_tool_offset(&active_tool);

    mapped = *pos;
    if (twp_enabled && (!lengthmodel || twp_parameters_valid)) {
        double twp_b_angle = synchronized_twp
            ? active_twp_frame.b_angle
            : pinv(haldata->twp_b_angle);
        double twp_c_angle = synchronized_twp
            ? active_twp_frame.c_angle
            : pinv(haldata->twp_c_angle);
        double c_delta;
        int c_delta_invalid = wrapped_angle_delta(pos->c,
                                                  twp_c_angle,
                                                  &c_delta);
        if (!isfinite(pos->b)
            || !isfinite(twp_b_angle)
            || c_delta_invalid
            || fabs(pos->b - twp_b_angle) > TWP_ROTARY_TOLERANCE_DEG
            || fabs(c_delta)
               > TWP_ROTARY_TOLERANCE_DEG) {
            return -1;
        }
        double local_xyz[3] = {pos->tran.x, pos->tran.y, pos->tran.z};
        if (synchronized_twp) {
            synchronized_twp_local_to_world(local_xyz, tool_xyz);
        } else {
            twp_local_to_world(local_xyz, tool_xyz);
        }
        mapped.tran.x = tool_xyz[0];
        mapped.tran.y = tool_xyz[1];
        mapped.tran.z = tool_xyz[2];
        mapped.b = twp_b_angle;
        mapped.c = twp_c_angle;
        if (lengthmodel && !vec_is_finite(tool_xyz)) {
            twp_parameters_valid = 0;
        }
    }

    evaluate_tool_offset_world(mapped.b, mapped.c, &active_tool, &evaluation);
    if (lengthmodel && (tcpc_enabled || twp_enabled)
        && (!vec_is_finite(origin) || !twp_parameters_valid)) {
        evaluation.empirical.valid = 0;
        evaluation.empirical.fault = LENGTH_MODEL_TRANSFORM_NONFINITE;
    }
    update_debug_pins(mapped.b, mapped.c, &evaluation);
    if (lengthmodel && (tcpc_enabled || twp_enabled)
        && !evaluation.empirical.valid) {
        return -1;
    }

    if (tcpc_enabled || twp_enabled) {
        mapped.tran.x = mapped.tran.x - evaluation.offset[0] + origin[0];
        mapped.tran.y = mapped.tran.y - evaluation.offset[1] + origin[1];
        mapped.tran.z = mapped.tran.z - evaluation.offset[2] + origin[2];
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

static int new_hal_s32_pin(hal_s32_t **pin, int dir, const char *name)
{
    return hal_pin_s32_newf(dir, pin, comp_id, "headheadkins.%s", name);
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

    for (term = 0; term < C_HARMONIC_TERMS; term++) {
        for (axis = 0; axis < 3; axis++) {
            result = hal_pin_float_newf(HAL_IN,
                                        &haldata->c_harmonic_machine[term][axis],
                                        comp_id,
                                        "headheadkins.charm.%s.%s",
                                        c_harmonic_term_names[term],
                                        axis_names[axis]);
            if (result < 0) return result;
        }
    }

    for (term = 0; term < B_MID_TERMS; term++) {
        for (axis = 0; axis < 3; axis++) {
            result = hal_pin_float_newf(HAL_IN,
                                        &haldata->b_mid_machine[term][axis],
                                        comp_id,
                                        "headheadkins.bmid.%s.%s",
                                        b_mid_term_names[term],
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

static int init_length_model_pins(void)
{
    int result;
    int term;
    int axis;

    result = new_hal_float_pin(&haldata->length_model_reference,
                               HAL_IN, "length-model.reference");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->length_model_span,
                               HAL_IN, "length-model.span");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->length_model_minimum,
                               HAL_IN, "length-model.minimum");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->length_model_maximum,
                               HAL_IN, "length-model.maximum");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->length_model_tolerance,
                               HAL_IN, "length-model.tolerance");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->length_model_max_diff_norm,
                               HAL_IN, "length-model.max-diff-norm");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->length_model_max_total_norm,
                               HAL_IN, "length-model.max-total-norm");
    if (result < 0) return result;
    result = new_hal_s32_pin(&haldata->length_model_id,
                             HAL_IN, "length-model.id");
    if (result < 0) return result;
    result = new_hal_s32_pin(&haldata->length_model_expected_id,
                             HAL_OUT, "length-model.expected-id");
    if (result < 0) return result;

    for (term = 0; term < LENGTH_DIFF_TERMS; term++) {
        for (axis = 0; axis < 3; axis++) {
            result = hal_pin_float_newf(HAL_IN,
                                        &haldata->length_diff[term][axis],
                                        comp_id,
                                        "headheadkins.ldiff.%s.%s",
                                        length_diff_term_names[term],
                                        axis_names[axis]);
            if (result < 0) return result;
        }
    }

    result = new_hal_bit_pin(&haldata->length_model_configured,
                             HAL_OUT, "length-model.configured");
    if (result < 0) return result;
    result = new_hal_bit_pin(&haldata->length_model_valid,
                             HAL_OUT, "length-model.valid");
    if (result < 0) return result;
    result = new_hal_s32_pin(&haldata->length_model_fault_code,
                             HAL_OUT, "length-model.fault-code");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->length_model_q,
                               HAL_OUT, "length-model.q");
    if (result < 0) return result;
    for (axis = 0; axis < 3; axis++) {
        result = hal_pin_float_newf(HAL_OUT,
                                    &haldata->length_model_diff_offset[axis],
                                    comp_id,
                                    "headheadkins.length-model.diff-offset.%s",
                                    axis_names[axis]);
        if (result < 0) return result;
        result = hal_pin_float_newf(HAL_OUT,
                                    &haldata->empirical_offset[axis],
                                    comp_id,
                                    "headheadkins.empirical-offset.%s",
                                    axis_names[axis]);
        if (result < 0) return result;
    }
    result = new_hal_float_pin(&haldata->length_model_diff_norm,
                               HAL_OUT, "length-model.diff-offset-norm");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->empirical_offset_norm,
                               HAL_OUT, "empirical-offset-norm");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->tool_offset_eval_b,
                               HAL_OUT, "tool-offset-eval.b");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->tool_offset_eval_c,
                               HAL_OUT, "tool-offset-eval.c");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->tool_offset_eval_length,
                               HAL_OUT, "tool-offset-eval.length");
    if (result < 0) return result;

    return 0;
}

static int init_geometry_pins(void)
{
    int result;
    int frame;
    int term;
    int axis;
    int mid_term;
    int cross_term;
    int length_term;

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

    result = new_hal_float_pin(&haldata->active_tool_offset_x, HAL_IN, "active-tool-offset.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->active_tool_offset_y, HAL_IN, "active-tool-offset.y");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->active_tool_offset_z, HAL_IN, "active-tool-offset.z");
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
    result = init_length_model_pins();
    if (result < 0) return result;

    result = new_hal_bit_pin(&haldata->tcpc_enable, HAL_IN, "tcpc-enable");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->tcpc_origin_x, HAL_IN, "tcpc-origin.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->tcpc_origin_y, HAL_IN, "tcpc-origin.y");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->tcpc_origin_z, HAL_IN, "tcpc-origin.z");
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
    result = new_hal_float_pin(&haldata->twp_coordinate_offset_x,
                               HAL_IN, "twp-coordinate-offset.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->twp_coordinate_offset_y,
                               HAL_IN, "twp-coordinate-offset.y");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->twp_coordinate_offset_z,
                               HAL_IN, "twp-coordinate-offset.z");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->twp_captured_origin_x,
                               HAL_OUT, "twp-captured-origin.x");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->twp_captured_origin_y,
                               HAL_OUT, "twp-captured-origin.y");
    if (result < 0) return result;
    result = new_hal_float_pin(&haldata->twp_captured_origin_z,
                               HAL_OUT, "twp-captured-origin.z");
    if (result < 0) return result;
    result = new_hal_bit_pin(&haldata->kinstype_is_world,
                             HAL_OUT, "kinstype-is-world");
    if (result < 0) return result;
    result = new_hal_bit_pin(&haldata->kinstype_is_twp,
                             HAL_OUT, "kinstype-is-twp");
    if (result < 0) return result;
    result = new_hal_bit_pin(&haldata->kinstype_frame_ready,
                             HAL_OUT, "kinstype-frame-ready");
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

    *haldata->active_tool_offset_x = 0.0;
    *haldata->active_tool_offset_y = 0.0;
    *haldata->active_tool_offset_z = 0.0;

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
    for (term = 0; term < C_HARMONIC_TERMS; term++) {
        for (axis = 0; axis < 3; axis++) {
            *haldata->c_harmonic_machine[term][axis] = 0.0;
        }
    }
    for (mid_term = 0; mid_term < B_MID_TERMS; mid_term++) {
        for (axis = 0; axis < 3; axis++) {
            *haldata->b_mid_machine[mid_term][axis] = 0.0;
        }
    }
    for (cross_term = 0; cross_term < B_CROSS_TERMS; cross_term++) {
        for (axis = 0; axis < 3; axis++) {
            *haldata->b_cross_machine[cross_term][axis] = 0.0;
        }
    }

    *haldata->length_model_reference = LENGTH_REFERENCE_MM;
    *haldata->length_model_span = LENGTH_SPAN_MM;
    *haldata->length_model_minimum = LENGTH_HARD_MIN_MM;
    *haldata->length_model_maximum = LENGTH_HARD_MAX_MM;
    *haldata->length_model_tolerance = LENGTH_MAX_TOLERANCE_MM;
    *haldata->length_model_max_diff_norm = LENGTH_MAX_DIFF_NORM_MM;
    *haldata->length_model_max_total_norm = LENGTH_MAX_TOTAL_NORM_MM;
    *haldata->length_model_id = 0;
    *haldata->length_model_expected_id = lengthmodelid;
    for (length_term = 0; length_term < LENGTH_DIFF_TERMS; length_term++) {
        for (axis = 0; axis < 3; axis++) {
            *haldata->length_diff[length_term][axis] = 0.0;
        }
    }
    *haldata->length_model_configured = lengthmodel ? 1 : 0;
    *haldata->length_model_valid = lengthmodel ? 0 : 1;
    *haldata->length_model_fault_code = lengthmodel
        ? LENGTH_MODEL_LENGTH_OUT_OF_RANGE : LENGTH_MODEL_OK;
    *haldata->length_model_q = 0.0;
    for (axis = 0; axis < 3; axis++) {
        *haldata->length_model_diff_offset[axis] = 0.0;
        *haldata->empirical_offset[axis] = 0.0;
    }
    *haldata->length_model_diff_norm = 0.0;
    *haldata->empirical_offset_norm = 0.0;
    *haldata->tool_offset_eval_b = 0.0;
    *haldata->tool_offset_eval_c = 0.0;
    *haldata->tool_offset_eval_length = 0.0;

    *haldata->tcpc_enable = lengthmodel ? 0 : 1;
    *haldata->tcpc_origin_x = 0.0;
    *haldata->tcpc_origin_y = 0.0;
    *haldata->tcpc_origin_z = 0.0;
    *haldata->twp_mode = 0;
    *haldata->twp_motion_origin_x = 0.0;
    *haldata->twp_motion_origin_y = 0.0;
    *haldata->twp_motion_origin_z = 0.0;
    *haldata->twp_b_angle = 0.0;
    *haldata->twp_c_angle = 0.0;
    *haldata->twp_normal_rotation = 0.0;
    *haldata->twp_coordinate_offset_x = 0.0;
    *haldata->twp_coordinate_offset_y = 0.0;
    *haldata->twp_coordinate_offset_z = 0.0;
    *haldata->twp_captured_origin_x = 0.0;
    *haldata->twp_captured_origin_y = 0.0;
    *haldata->twp_captured_origin_z = 0.0;
    *haldata->kinstype_is_world = 1;
    *haldata->kinstype_is_twp = 0;
    *haldata->kinstype_frame_ready = 0;

    return 0;
}

int kinematicsForward(const double *joints,
                      EmcPose *pos,
                      const KINEMATICS_FORWARD_FLAGS *fflags,
                      KINEMATICS_INVERSE_FLAGS *iflags)
{
    int result;

    if (switchkins_type == 1) {
        result = headheadKinematicsForward(joints, pos, fflags, iflags, 1, 1);
    } else {
        result = headheadKinematicsForward(
            joints, pos, fflags, iflags, pinb(haldata->twp_mode), 0);
    }
    if (result == 0) {
        *haldata->kinstype_is_world = switchkins_type == 0;
        *haldata->kinstype_is_twp = switchkins_type == 1;
        *haldata->kinstype_frame_ready = 1;
    }
    return result;
}

int kinematicsInverse(const EmcPose *pos,
                      double *joints,
                      const KINEMATICS_INVERSE_FLAGS *iflags,
                      KINEMATICS_FORWARD_FLAGS *fflags)
{
    if (switchkins_type == 1) {
        return headheadKinematicsInverse(pos, joints, iflags, fflags, 1, 1);
    }
    return headheadKinematicsInverse(
        pos, joints, iflags, fflags, pinb(haldata->twp_mode), 0);
}

KINEMATICS_TYPE kinematicsType(void)
{
    return ktype;
}

int kinematicsSwitchable(void)
{
    return 1;
}

int kinematicsSwitch(int new_switchkins_type)
{
    if (new_switchkins_type != 0 && new_switchkins_type != 1) {
        return -1;
    }
    if (new_switchkins_type == 1
        && (haldata == NULL
            || !pinb(haldata->tcpc_enable)
            || !synchronized_twp_inputs_are_finite()
            || (lengthmodel && !pinb(haldata->length_model_valid)))) {
        return -1;
    }

    if (new_switchkins_type == 1) {
        active_twp_frame.b_angle = pinv(haldata->twp_b_angle);
        active_twp_frame.c_angle = pinv(haldata->twp_c_angle);
        active_twp_frame.normal_rotation = pinv(haldata->twp_normal_rotation);
        active_twp_frame.coordinate_offset[0] = pinv(haldata->twp_coordinate_offset_x);
        active_twp_frame.coordinate_offset[1] = pinv(haldata->twp_coordinate_offset_y);
        active_twp_frame.coordinate_offset[2] = pinv(haldata->twp_coordinate_offset_z);
        active_twp_frame.tcpc_origin[0] = pinv(haldata->tcpc_origin_x);
        active_twp_frame.tcpc_origin[1] = pinv(haldata->tcpc_origin_y);
        active_twp_frame.tcpc_origin[2] = pinv(haldata->tcpc_origin_z);
        active_twp_frame.valid = 1;
    }

    switchkins_type = new_switchkins_type;
    capture_twp_origin_on_forward = new_switchkins_type == 1;
    if (haldata != NULL) {
        *haldata->kinstype_frame_ready = 0;
    }
    return 0;
}

EXPORT_SYMBOL(kinematicsType);
EXPORT_SYMBOL(kinematicsForward);
EXPORT_SYMBOL(kinematicsInverse);
EXPORT_SYMBOL(kinematicsSwitchable);
EXPORT_SYMBOL(kinematicsSwitch);
MODULE_LICENSE("GPL");

int rtapi_app_main(void)
{
    int axis_idx_for_jno[EMCMOT_MAX_JOINTS];
    int i;
    kparms ksetup;

    switchkins_type = 0;
    capture_twp_origin_on_forward = 0;
    active_twp_frame.b_angle = 0.0;
    active_twp_frame.c_angle = 0.0;
    active_twp_frame.normal_rotation = 0.0;
    active_twp_frame.coordinate_offset[0] = 0.0;
    active_twp_frame.coordinate_offset[1] = 0.0;
    active_twp_frame.coordinate_offset[2] = 0.0;
    active_twp_frame.captured_origin[0] = 0.0;
    active_twp_frame.captured_origin[1] = 0.0;
    active_twp_frame.captured_origin[2] = 0.0;
    active_twp_frame.tcpc_origin[0] = 0.0;
    active_twp_frame.tcpc_origin[1] = 0.0;
    active_twp_frame.tcpc_origin[2] = 0.0;
    active_twp_frame.valid = 0;

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
    rtapi_print_msg(RTAPI_MSG_INFO,
                    "headheadkins: lengthmodel=%d expected-id=%d domain=[%.3f, %.3f] mm\n",
                    lengthmodel ? 1 : 0,
                    lengthmodelid,
                    *haldata->length_model_minimum,
                    *haldata->length_model_maximum);

    hal_ready(comp_id);
    return 0;
}

void rtapi_app_exit(void)
{
    hal_exit(comp_id);
}
