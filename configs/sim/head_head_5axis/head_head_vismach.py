#!/usr/bin/env python3

"""Rough articulated vismach model for head-head XYZBC simulation."""

import os
from vismach import *
import hal


TRAVEL_X = 3310.0
TRAVEL_Y = 1700.0
TRAVEL_Z = 900.0


def optional_stl_overlay():
    path = os.environ.get("HEAD_HEAD_FULL_STL", "")
    if not path:
        return None
    if not os.path.isfile(path):
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


class HalToolReference(CylinderZ):
    def __init__(self, comp):
        super().__init__(0.0, 0.0, 1.0, 0.0)
        self.comp = comp

    def coords(self):
        radius = max(1.0, self.comp["tool_diameter"] / 2.0)
        return (0.0, radius, 40.0, radius)


tooltip = Capture()
work = Capture()

# A simple tool reference marker starting at the current kinematic tool point.
tool_reference = Collection([
    tooltip,
    Color([0.85, 0.20, 0.20, 1.0], [HalToolReference(c)]),
    Color([0.95, 0.55, 0.20, 1.0], [CylinderZ(40.0, 12.0, 90.0, 16.0)]),
])

# Move the spindle/tool stack from the B pivot to the kinematic tool reference.
tool_stack = HalTranslate([tool_reference], c, "b_to_tool_x", 1, 0, 0)
tool_stack = HalTranslate([tool_stack], c, "b_to_tool_y", 0, 1, 0)
tool_stack = HalTranslate([tool_stack], c, "b_to_tool_z", 0, 0, 1)

# Add a rough B head body around the B pivot.
b_head = Collection([
    tool_stack,
    Color([0.95, 0.75, 0.15, 1.0], [Box(-90, -70, -40, 90, 70, 90)]),
    Color([0.80, 0.80, 0.85, 1.0], [CylinderY(-120.0, 18.0, 120.0, 18.0)]),
])

b_head = HalRotate([b_head], c, "b_zero_offset", 1, 0, 1, 0)
b_head = HalRotate([b_head], c, "joint_b", 1, 0, 1, 0)

# Offset the B pivot from the C pivot.
c_group = HalTranslate([b_head], c, "c_to_b_x", 1, 0, 0)
c_group = HalTranslate([c_group], c, "c_to_b_y", 0, 1, 0)
c_group = HalTranslate([c_group], c, "c_to_b_z", 0, 0, 1)

# Add a simple C housing around the C pivot.
c_group = Collection([
    c_group,
    Color([0.25, 0.55, 0.85, 1.0], [CylinderZ(-70.0, 55.0, 70.0, 55.0)]),
    Color([0.35, 0.35, 0.40, 1.0], [Box(-120, -120, -40, 120, 120, 40)]),
])

c_group = HalRotate([c_group], c, "c_zero_offset", 1, 0, 0, 1)
c_group = HalRotate([c_group], c, "joint_c", 1, 0, 0, 1)

# Z carriage and ram. Z joint locates the C pivot center.
z_carriage = Collection([
    c_group,
    Color([0.75, 0.75, 0.78, 1.0], [Box(-140, -110, 0, 140, 110, 210)]),
    Color([0.55, 0.55, 0.60, 1.0], [Box(-110, -90, 210, 110, 90, 520)]),
])
z_carriage = HalTranslate([z_carriage], c, "joint_z", 0, 0, 1)

# X beam assembly.
x_assembly = Collection([
    z_carriage,
    Color([0.20, 0.70, 0.30, 1.0], [Box(-500, -120, 480, 500, 120, 620)]),
    Color([0.65, 0.65, 0.68, 1.0], [Box(-520, -80, 300, -420, 80, 760)]),
    Color([0.65, 0.65, 0.68, 1.0], [Box(420, -80, 300, 520, 80, 760)]),
])
x_assembly = HalTranslate([x_assembly], c, "joint_x", 1, 0, 0)

# Y carriage / bridge assembly.
y_assembly = Collection([
    x_assembly,
    Color([0.20, 0.40, 0.85, 1.0], [Box(-650, -120, 620, 650, 120, 760)]),
    Color([0.50, 0.50, 0.55, 1.0], [Box(-700, -100, 0, -620, 100, 800)]),
    Color([0.50, 0.50, 0.55, 1.0], [Box(620, -100, 0, 700, 100, 800)]),
])
y_assembly = HalTranslate([y_assembly], c, "joint_y", 0, 1, 0)

table = Collection([
    work,
    Color([0.40, 0.40, 0.45, 1.0], [Box(-900, -700, -90, 900, 700, -20)]),
    Color([0.55, 0.55, 0.60, 1.0], [Box(-980, -760, -140, 980, 760, -90)]),
])

frame = Collection([
    Color([0.45, 0.45, 0.48, 1.0], [Box(-900, -850, -150, 900, 850, -140)]),
    Color([0.35, 0.35, 0.40, 1.0], [Box(-820, -840, -140, -720, 840, 1200)]),
    Color([0.35, 0.35, 0.40, 1.0], [Box(720, -840, -140, 820, 840, 1200)]),
])

overlay = optional_stl_overlay()
parts = [frame, table, y_assembly]
if overlay is not None:
    parts.insert(0, overlay)

model = Collection(parts)

hud = Hud()
hud.show("Head-Head XYZBC Rough Visual Sim")
if os.environ.get("HEAD_HEAD_FULL_STL"):
    hud.show("STL overlay requested via HEAD_HEAD_FULL_STL")

if __name__ == "__main__":
    main(model, tooltip, work, size=max(TRAVEL_X, TRAVEL_Y), hud=hud, lat=-70, lon=35)
