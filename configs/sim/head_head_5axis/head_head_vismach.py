#!/usr/bin/env python3

"""Improved articulated vismach model for the head-head XYZBC simulation."""

import os
from vismach import *
import hal


TRAVEL_X = 3310.0
TRAVEL_Y = 1700.0
TRAVEL_Z = 900.0


def optional_stl_overlay():
    path = os.environ.get("HEAD_HEAD_FULL_STL", "")
    if not path or not os.path.isfile(path):
        return None
    try:
        return Color([0.55, 0.55, 0.60, 0.18], [AsciiSTL(filename=path)])
    except Exception as exc:
        print(f"head_head_vismach: unable to load STL overlay {path}: {exc}")
        return None


c = hal.component("headheadvismach")
c.newpin("joint_x", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("joint_y", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("joint_z", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("joint_b", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("joint_c", hal.HAL_FLOAT, hal.HAL_IN)

c.newpin("tool_length", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("tool_diameter", hal.HAL_FLOAT, hal.HAL_IN)

c.newpin("c_to_b_x", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("c_to_b_y", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("c_to_b_z", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("b_to_tool_x", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("b_to_tool_y", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("b_to_tool_z", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("b_zero_offset", hal.HAL_FLOAT, hal.HAL_IN)
c.newpin("c_zero_offset", hal.HAL_FLOAT, hal.HAL_IN)

c["tool_diameter"] = 20.0
c.ready()


class HalToolCylinder(CylinderZ):
    def coords(self):
        radius = max(1.0, c["tool_diameter"] / 2.0)
        length = max(25.0, c["tool_length"])
        return (-length, radius, 0.0, radius)


# Dimensions from the newer 5thAxis vismach model.
GANTRY_SPAN = TRAVEL_X + 600.0
GANTRY_HEIGHT = TRAVEL_Z + 1400.0
BEAM_HEIGHT = 300.0
BEAM_DEPTH = 300.0

LEG_WIDTH = 350.0
LEG_DEPTH = 350.0

TABLE_LENGTH = TRAVEL_X - 200.0
TABLE_WIDTH = TRAVEL_Y - 400.0
TABLE_THICK = 100.0
TABLE_Z = 500.0

XCAR_WIDTH = 500.0
XCAR_HEIGHT = 350.0
XCAR_DEPTH = BEAM_DEPTH + 80.0

ZCOL_WIDTH = 250.0
ZCOL_DEPTH = 250.0
ZCOL_LENGTH = TRAVEL_Z + 300.0

C_RADIUS = 140.0
C_HEIGHT = 100.0
B_WIDTH = 200.0
B_HEIGHT = 200.0
B_DEPTH = 250.0

SPINDLE_RADIUS = 50.0
SPINDLE_LENGTH = 200.0
NOSE_LENGTH = 60.0
TOOLTIP_FROM_SPINDLE_ORIGIN_Z = -SPINDLE_LENGTH * 0.4 - NOSE_LENGTH

DARK_BLUE = [0.12, 0.12, 0.30, 1.0]
MED_BLUE = [0.18, 0.18, 0.40, 1.0]
LIGHT_GRAY = [0.70, 0.70, 0.70, 1.0]
DARK_GRAY = [0.15, 0.15, 0.15, 1.0]
RED_BROWN = [0.55, 0.12, 0.10, 1.0]
ORANGE = [0.85, 0.40, 0.10, 1.0]
YELLOW = [0.90, 0.90, 0.20, 1.0]
GUIDE_GREEN = [0.15, 0.80, 0.25, 1.0]
GUIDE_CYAN = [0.10, 0.85, 0.90, 1.0]

BEAM_TOP = GANTRY_HEIGHT
BEAM_BOTTOM = GANTRY_HEIGHT - BEAM_HEIGHT
XCAR_TOP = BEAM_BOTTOM
XCAR_BOTTOM = BEAM_BOTTOM - XCAR_HEIGHT
C_BOTTOM = -30.0 - C_HEIGHT - 20.0
Z_HOME = XCAR_BOTTOM - ZCOL_LENGTH + TRAVEL_Z / 2.0

tooltip = Capture()
work = Capture()


# Static frame
left_leg = Color(DARK_BLUE, [
    Box(-GANTRY_SPAN / 2 - LEG_WIDTH / 2, -LEG_DEPTH / 2, 0,
        -GANTRY_SPAN / 2 + LEG_WIDTH / 2, LEG_DEPTH / 2, GANTRY_HEIGHT)
])
right_leg = Color(DARK_BLUE, [
    Box(GANTRY_SPAN / 2 - LEG_WIDTH / 2, -LEG_DEPTH / 2, 0,
        GANTRY_SPAN / 2 + LEG_WIDTH / 2, LEG_DEPTH / 2, GANTRY_HEIGHT)
])
beam = Color(DARK_BLUE, [
    Box(-GANTRY_SPAN / 2, -BEAM_DEPTH / 2, BEAM_BOTTOM,
         GANTRY_SPAN / 2, BEAM_DEPTH / 2, BEAM_TOP)
])
rail_front = Color(LIGHT_GRAY, [
    Box(-GANTRY_SPAN / 2, -BEAM_DEPTH / 2 - 15, BEAM_TOP - 40,
         GANTRY_SPAN / 2, -BEAM_DEPTH / 2, BEAM_TOP - 20),
    Box(-GANTRY_SPAN / 2, -BEAM_DEPTH / 2 - 15, BEAM_BOTTOM + 20,
         GANTRY_SPAN / 2, -BEAM_DEPTH / 2, BEAM_BOTTOM + 40),
])
bottom_cross_front = Color(DARK_BLUE, [
    Box(-GANTRY_SPAN / 2, -LEG_DEPTH / 2, 50,
         GANTRY_SPAN / 2, -LEG_DEPTH / 2 + 60, 120)
])
bottom_cross_back = Color(DARK_BLUE, [
    Box(-GANTRY_SPAN / 2, LEG_DEPTH / 2 - 60, 50,
         GANTRY_SPAN / 2, LEG_DEPTH / 2, 120)
])
y_rail_left = Color(MED_BLUE, [
    Box(-TABLE_LENGTH / 2 - 50, -TRAVEL_Y / 2 - 300, TABLE_Z - 150,
        -TABLE_LENGTH / 2 + 50, TRAVEL_Y / 2 + 300, TABLE_Z - 120)
])
y_rail_right = Color(MED_BLUE, [
    Box(TABLE_LENGTH / 2 - 50, -TRAVEL_Y / 2 - 300, TABLE_Z - 150,
        TABLE_LENGTH / 2 + 50, TRAVEL_Y / 2 + 300, TABLE_Z - 120)
])
foot_pads = Color(ORANGE, [
    Box(-GANTRY_SPAN / 2 - LEG_WIDTH / 2 - 10, -LEG_DEPTH / 2 - 10, 0,
        -GANTRY_SPAN / 2 + LEG_WIDTH / 2 + 10, LEG_DEPTH / 2 + 10, 30),
    Box(GANTRY_SPAN / 2 - LEG_WIDTH / 2 - 10, -LEG_DEPTH / 2 - 10, 0,
        GANTRY_SPAN / 2 + LEG_WIDTH / 2 + 10, LEG_DEPTH / 2 + 10, 30),
])
frame = Collection([
    left_leg,
    right_leg,
    beam,
    rail_front,
    bottom_cross_front,
    bottom_cross_back,
    y_rail_left,
    y_rail_right,
    foot_pads,
])


# Table / work
table_top = Color(DARK_GRAY, [
    Box(-TABLE_LENGTH / 2, -TABLE_WIDTH / 2, TABLE_Z,
         TABLE_LENGTH / 2, TABLE_WIDTH / 2, TABLE_Z + TABLE_THICK)
])
table_frame = Color(MED_BLUE, [
    Box(-TABLE_LENGTH / 2 + 50, -TABLE_WIDTH / 2 + 30, TABLE_Z - 100,
         TABLE_LENGTH / 2 - 50, TABLE_WIDTH / 2 - 30, TABLE_Z)
])
table_saddle_l = Color(DARK_BLUE, [
    Box(-TABLE_LENGTH / 2 - 30, -TABLE_WIDTH / 2 - 20, TABLE_Z - 160,
        -TABLE_LENGTH / 2 + 80, TABLE_WIDTH / 2 + 20, TABLE_Z - 100)
])
table_saddle_r = Color(DARK_BLUE, [
    Box(TABLE_LENGTH / 2 - 80, -TABLE_WIDTH / 2 - 20, TABLE_Z - 160,
        TABLE_LENGTH / 2 + 30, TABLE_WIDTH / 2 + 20, TABLE_Z - 100)
])
table_blocks = Color(ORANGE, [
    Box(-TABLE_LENGTH / 2, -TABLE_WIDTH / 2 - 10, TABLE_Z - 140,
        -TABLE_LENGTH / 2 + 40, -TABLE_WIDTH / 2 + 20, TABLE_Z - 110),
    Box(-TABLE_LENGTH / 2, TABLE_WIDTH / 2 - 20, TABLE_Z - 140,
        -TABLE_LENGTH / 2 + 40, TABLE_WIDTH / 2 + 10, TABLE_Z - 110),
    Box(TABLE_LENGTH / 2 - 40, -TABLE_WIDTH / 2 - 10, TABLE_Z - 140,
        TABLE_LENGTH / 2, -TABLE_WIDTH / 2 + 20, TABLE_Z - 110),
    Box(TABLE_LENGTH / 2 - 40, TABLE_WIDTH / 2 - 20, TABLE_Z - 140,
        TABLE_LENGTH / 2, TABLE_WIDTH / 2 + 10, TABLE_Z - 110),
])
table_x_centerline = Color(GUIDE_GREEN, [
    Box(-TABLE_LENGTH / 2 + 60, -8, TABLE_Z + TABLE_THICK + 1,
        TABLE_LENGTH / 2 - 60, 8, TABLE_Z + TABLE_THICK + 3),
])
table_y_centerline = Color(GUIDE_GREEN, [
    Box(-8, -TABLE_WIDTH / 2 + 60, TABLE_Z + TABLE_THICK + 1,
        8, TABLE_WIDTH / 2 - 60, TABLE_Z + TABLE_THICK + 3),
])
alignment_post = Color(GUIDE_CYAN, [
    CylinderZ(TABLE_Z + TABLE_THICK, 10, TABLE_Z + TABLE_THICK + 220, 10),
])
alignment_cross = Color(GUIDE_CYAN, [
    Box(-80, -5, TABLE_Z + TABLE_THICK + 220, 80, 5, TABLE_Z + TABLE_THICK + 230),
    Box(-5, -80, TABLE_Z + TABLE_THICK + 220, 5, 80, TABLE_Z + TABLE_THICK + 230),
])
corner_markers = Color(GUIDE_CYAN, [
    Box(-TABLE_LENGTH / 2 + 30, -TABLE_WIDTH / 2 + 30, TABLE_Z + TABLE_THICK + 1,
        -TABLE_LENGTH / 2 + 80, -TABLE_WIDTH / 2 + 80, TABLE_Z + TABLE_THICK + 6),
    Box(-TABLE_LENGTH / 2 + 30, TABLE_WIDTH / 2 - 80, TABLE_Z + TABLE_THICK + 1,
        -TABLE_LENGTH / 2 + 80, TABLE_WIDTH / 2 - 30, TABLE_Z + TABLE_THICK + 6),
    Box(TABLE_LENGTH / 2 - 80, -TABLE_WIDTH / 2 + 30, TABLE_Z + TABLE_THICK + 1,
        TABLE_LENGTH / 2 - 30, -TABLE_WIDTH / 2 + 80, TABLE_Z + TABLE_THICK + 6),
    Box(TABLE_LENGTH / 2 - 80, TABLE_WIDTH / 2 - 80, TABLE_Z + TABLE_THICK + 1,
        TABLE_LENGTH / 2 - 30, TABLE_WIDTH / 2 - 30, TABLE_Z + TABLE_THICK + 6),
])
table_assembly = Collection([
    table_top,
    table_frame,
    table_saddle_l,
    table_saddle_r,
    table_blocks,
    table_x_centerline,
    table_y_centerline,
    alignment_post,
    alignment_cross,
    corner_markers,
    Translate([work], 0, 0, TABLE_Z + TABLE_THICK),
])
table_y = HalTranslate([table_assembly], c, "joint_y", 0, -1, 0)


# X carriage
xcar_body = Color(MED_BLUE, [
    Box(-XCAR_WIDTH / 2, -XCAR_DEPTH / 2, XCAR_BOTTOM,
         XCAR_WIDTH / 2, XCAR_DEPTH / 2, XCAR_TOP)
])
xcar_blocks = Color(ORANGE, [
    Box(-XCAR_WIDTH / 2 + 20, -BEAM_DEPTH / 2 - 25, BEAM_TOP - 50,
        -XCAR_WIDTH / 2 + 80, -BEAM_DEPTH / 2, BEAM_TOP - 15),
    Box(XCAR_WIDTH / 2 - 80, -BEAM_DEPTH / 2 - 25, BEAM_TOP - 50,
        XCAR_WIDTH / 2 - 20, -BEAM_DEPTH / 2, BEAM_TOP - 15),
    Box(-XCAR_WIDTH / 2 + 20, -BEAM_DEPTH / 2 - 25, BEAM_BOTTOM + 15,
        -XCAR_WIDTH / 2 + 80, -BEAM_DEPTH / 2, BEAM_BOTTOM + 50),
    Box(XCAR_WIDTH / 2 - 80, -BEAM_DEPTH / 2 - 25, BEAM_BOTTOM + 15,
        XCAR_WIDTH / 2 - 20, -BEAM_DEPTH / 2, BEAM_BOTTOM + 50),
])
z_housing = Color(DARK_BLUE, [
    Box(-ZCOL_WIDTH / 2 - 80, -ZCOL_DEPTH / 2 - 80, XCAR_BOTTOM - 200,
         ZCOL_WIDTH / 2 + 80, ZCOL_DEPTH / 2 + 80, XCAR_BOTTOM)
])
z_motor_housing = Color(DARK_BLUE, [
    Box(-80, -80, BEAM_TOP, 80, 80, BEAM_TOP + 200)
])
x_carriage = Collection([xcar_body, xcar_blocks, z_housing, z_motor_housing])


# Z column
z_column = Color(MED_BLUE, [
    Box(-ZCOL_WIDTH / 2, -ZCOL_DEPTH / 2, 0,
         ZCOL_WIDTH / 2, ZCOL_DEPTH / 2, ZCOL_LENGTH)
])
z_rails = Color(LIGHT_GRAY, [
    Box(-ZCOL_WIDTH / 2 - 10, -ZCOL_DEPTH / 2 - 10, 50,
        -ZCOL_WIDTH / 2, -ZCOL_DEPTH / 2, ZCOL_LENGTH - 50),
    Box(ZCOL_WIDTH / 2, -ZCOL_DEPTH / 2 - 10, 50,
        ZCOL_WIDTH / 2 + 10, -ZCOL_DEPTH / 2, ZCOL_LENGTH - 50),
])


# C axis housing
c_housing = Collection([
    Color(DARK_BLUE, [CylinderZ(0, C_RADIUS + 30, -30, C_RADIUS + 30)]),
    Color(MED_BLUE, [CylinderZ(-30, C_RADIUS, -30 - C_HEIGHT, C_RADIUS)]),
    Color(DARK_BLUE, [CylinderZ(-30 - C_HEIGHT, C_RADIUS + 20, -30 - C_HEIGHT - 20, C_RADIUS + 20)]),
])


# B axis housing
b_housing = Collection([
    Color(RED_BROWN, [Box(-B_WIDTH / 2, -B_DEPTH / 2, -B_HEIGHT / 2,
                          -B_WIDTH / 2 + 50, B_DEPTH / 2, B_HEIGHT / 2)]),
    Color(RED_BROWN, [Box(B_WIDTH / 2 - 50, -B_DEPTH / 2, -B_HEIGHT / 2,
                          B_WIDTH / 2, B_DEPTH / 2, B_HEIGHT / 2)]),
    Color(RED_BROWN, [Box(-B_WIDTH / 2, -B_DEPTH / 2 + 30, B_HEIGHT / 2 - 50,
                          B_WIDTH / 2, B_DEPTH / 2 - 30, B_HEIGHT / 2)]),
    Color(LIGHT_GRAY, [CylinderY(-B_DEPTH / 2 - 10, 40, -B_DEPTH / 2 + 10, 40)]),
    Color(LIGHT_GRAY, [CylinderY(B_DEPTH / 2 - 10, 40, B_DEPTH / 2 + 10, 40)]),
])


# Spindle and tool
spindle_motor = Color(LIGHT_GRAY, [
    CylinderZ(0, SPINDLE_RADIUS + 20, SPINDLE_LENGTH * 0.6, SPINDLE_RADIUS + 20)
])
spindle_shaft = Color(LIGHT_GRAY, [
    CylinderZ(0, SPINDLE_RADIUS, -SPINDLE_LENGTH * 0.4, SPINDLE_RADIUS * 0.7)
])
spindle_nose = Color(LIGHT_GRAY, [
    CylinderZ(-SPINDLE_LENGTH * 0.4, SPINDLE_RADIUS * 0.7,
              -SPINDLE_LENGTH * 0.4 - NOSE_LENGTH, SPINDLE_RADIUS * 0.3)
])
tool = Color(YELLOW, [HalToolCylinder()])

spindle_assembly = Collection([
    spindle_motor,
    spindle_shaft,
    spindle_nose,
    Translate([tooltip], 0, 0, TOOLTIP_FROM_SPINDLE_ORIGIN_Z),
    Translate([tool], 0, 0, TOOLTIP_FROM_SPINDLE_ORIGIN_Z),
])

# Make the visual tooltip coincide with the kinematic B->tool reference pin.
spindle_at_tool_ref = Translate([spindle_assembly], 0, 0, -TOOLTIP_FROM_SPINDLE_ORIGIN_Z)
spindle_with_offset = HalTranslate([spindle_at_tool_ref], c, "b_to_tool_x", 1, 0, 0)
spindle_with_offset = HalTranslate([spindle_with_offset], c, "b_to_tool_y", 0, 1, 0)
spindle_with_offset = HalTranslate([spindle_with_offset], c, "b_to_tool_z", 0, 0, 1)

b_with_spindle = Collection([b_housing, spindle_with_offset])
b_rotate = HalRotate([b_with_spindle], c, "b_zero_offset", 1, 0, 1, 0)
b_rotate = HalRotate([b_rotate], c, "joint_b", 1, 0, 1, 0)

# B pivot placement relative to C pivot is fully driven by the shared geometry pins.
b_at_c = HalTranslate([b_rotate], c, "c_to_b_x", 1, 0, 0)
b_at_c = HalTranslate([b_at_c], c, "c_to_b_y", 0, 1, 0)
b_at_c = HalTranslate([b_at_c], c, "c_to_b_z", 0, 0, 1)

c_with_b = Collection([c_housing, b_at_c])
c_rotate = HalRotate([c_with_b], c, "c_zero_offset", 1, 0, 0, 1)
c_rotate = HalRotate([c_rotate], c, "joint_c", 1, 0, 0, 1)

z_assembly = Collection([z_column, z_rails, c_rotate])
z_positioned = Translate([z_assembly], 0, 0, Z_HOME)
z_translate = HalTranslate([z_positioned], c, "joint_z", 0, 0, 1)

x_assembly = Collection([x_carriage, z_translate])
x_start = -TRAVEL_X / 2.0
x_positioned = Translate([x_assembly], x_start, 0, 0)
x_translate = HalTranslate([x_positioned], c, "joint_x", 1, 0, 0)

overlay = optional_stl_overlay()
parts = [frame, table_y, x_translate]
if overlay is not None:
    parts.insert(0, overlay)

model = Collection(parts)

hud = Hud()
hud.show("Head-Head XYZBC Visual Sim")
hud.show("Imported gantry/head model from alj333/5thAxis")
hud.show("Table Y is visually inverted to match a moving-table axis")
hud.show("Cyan post/cross and green centerlines move with the table")
if os.environ.get("HEAD_HEAD_FULL_STL"):
    hud.show("STL overlay requested via HEAD_HEAD_FULL_STL")

if __name__ == "__main__":
    main(model, tooltip, work, size=GANTRY_SPAN, hud=hud, lat=-75, lon=30)
