#   This is a component of LinuxCNC
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
import linuxcnc
import emccanon
from interpreter import *
import hal

def m431(self):
    yield INTERP_EXECUTE_FINISH
    if self.task == 0:
        print("TASK = 0 -> ignoring M431")
        yield INTERP_OK
    else:
        # YK - switch to tilted work plane mode
        print("M431: Activating TWP")
        x = hal.get_value("axis.x.pos-cmd") # YK - get the current X of the tool (w.r.t. G53)
        y = hal.get_value("axis.y.pos-cmd") # YK - get the current Y of the tool (w.r.t. G53)
        z = hal.get_value("axis.z.pos-cmd") # YK - get the current Z of the tool (w.r.t. G53)
        b = hal.get_value("axis.b.pos-cmd") # YK - get the current B of the tool (w.r.t. G53)
        c = hal.get_value("axis.c.pos-cmd") # YK - get the current C of the tool (w.r.t. G53)
        # YK - set X coordinate of the TWP origin to be the same as the current X of the tool (w.r.t. G53)
        hal.set_p("5axiskins.twp-origin-x", str(x))
        # YK - set Y coordinate of the TWP origin to be the same as the current Y of the tool (w.r.t. G53)
        hal.set_p("5axiskins.twp-origin-y", str(y))
        # YK - set Z coordinate of the TWP origin to be the same as the current Z of the tool (w.r.t. G53)
        hal.set_p("5axiskins.twp-origin-z", str(z))
        # YK - set B angle of the TWP to be the current B angle of the tool (w.r.t. G53)
        hal.set_p("5axiskins.twp-angle-b", str(b)) 
        # YK - set C angle of the TWP to be the current C angle of the tool (w.r.t. G53)
        hal.set_p("5axiskins.twp-angle-c", str(c))
        hal.set_p("5axiskins.twp-set", str(1)) # YK - set TWP mode to on
        yield INTERP_EXECUTE_FINISH

    return INTERP_OK

# def m432(self):
#     yield INTERP_EXECUTE_FINISH
#     if self.task == 0:
#         print("TASK = 0 -> ignoring M432")
#         yield INTERP_OK
#     else:
#         print("M432: Deactivating TWP")
#         twp_x = hal.get_value("5axiskins.twp-origin-x")
#         twp_y = hal.get_value("5axiskins.twp-origin-y")
#         twp_z = hal.get_value("5axiskins.twp-origin-z")
#         twp_b = hal.get_value("5axiskins.twp-angle-b")
#         twp_c = hal.get_value("5axiskins.twp-angle-c")
#         # mov_back_command = "G53 G0 X{} Y{} Z{} B{} C{}".format(
#         #     twp_x, twp_y, twp_z, twp_b, twp_c
#         # )
#         # self.execute(mov_back_command)
#         # yield INTERP_EXECUTE_FINISH
#         mov_back_command = "G53 G0 B{} C{}".format(twp_b, twp_c)
#         self.execute(mov_back_command)
#         yield INTERP_EXECUTE_FINISH
#         mov_back_command = "G53 G0 X{} Y{}".format(twp_x, twp_y)
#         self.execute(mov_back_command)
#         yield INTERP_EXECUTE_FINISH
#         mov_back_command = "G53 G0 Z{}".format(twp_z)
#         self.execute(mov_back_command)
#         yield INTERP_EXECUTE_FINISH

#         hal.set_p("5axiskins.twp-origin-x", str(0))
#         hal.set_p("5axiskins.twp-origin-y", str(0))
#         hal.set_p("5axiskins.twp-origin-z", str(0))
#         hal.set_p("5axiskins.twp-angle-b", str(0))
#         hal.set_p("5axiskins.twp-angle-c", str(0))
#         hal.set_p("5axiskins.twp-set", str(0))
#         yield INTERP_EXECUTE_FINISH

#     return INTERP_OK


def m432(self):
    yield INTERP_EXECUTE_FINISH
    if self.task == 0:
        print("TASK = 0 -> ignoring M432")
        yield INTERP_OK
    else:
        # YK - switch to normal TCP kinematics
        print("M432: Deactivating TWP")
        hal.set_p("5axiskins.twp-set", str(0)) # YK - set TWP mode to off
        hal.set_p("5axiskins.twp-origin-x", str(0)) # YK - reset X coordinate of the TWP origin to 0
        hal.set_p("5axiskins.twp-origin-y", str(0)) # YK - reset Y coordinate of the TWP origin to 0
        hal.set_p("5axiskins.twp-origin-z", str(0)) # YK - reset Z coordinate of the TWP origin to 0
        hal.set_p("5axiskins.twp-angle-b", str(0)) # YK - reset B angle of the TWP to 0
        hal.set_p("5axiskins.twp-angle-c", str(0)) # YK - reset C angle of the TWP to 0
        yield INTERP_EXECUTE_FINISH

    return INTERP_OK
