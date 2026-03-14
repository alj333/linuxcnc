from interpreter import INTERP_ERROR, INTERP_OK, InterpreterException
from emccanon import MESSAGE
import hal


def _hal(name):
    return hal.get_value(name)


def _axis_word(words, key):
    return words[key] if key in words else 0.0


def twp_move(self, **words):
    """Prototype fixed-plane TWP linear move using stored headheadtwp state."""

    if not _hal("headheadtwp.valid"):
        self.set_errormsg("TWP move requested with no valid TWP definition")
        return INTERP_ERROR

    if not _hal("headheadtwp.active"):
        self.set_errormsg("TWP move requested while TWP state is not active")
        return INTERP_ERROR

    if not any(word in words for word in ("p", "q", "r")):
        self.set_errormsg("G88.5 requires at least one of P, Q, or R")
        return INTERP_ERROR

    u = _axis_word(words, "p")
    v = _axis_word(words, "q")
    w = _axis_word(words, "r")

    origin_x = _hal("headheadtwp.twp_origin_x")
    origin_y = _hal("headheadtwp.twp_origin_y")
    origin_z = _hal("headheadtwp.twp_origin_z")

    plane_x = (
        _hal("headheadtwp.plane_x_x"),
        _hal("headheadtwp.plane_x_y"),
        _hal("headheadtwp.plane_x_z"),
    )
    plane_y = (
        _hal("headheadtwp.plane_y_x"),
        _hal("headheadtwp.plane_y_y"),
        _hal("headheadtwp.plane_y_z"),
    )
    plane_z = (
        _hal("headheadtwp.plane_z_x"),
        _hal("headheadtwp.plane_z_y"),
        _hal("headheadtwp.plane_z_z"),
    )

    x = origin_x + (u * plane_x[0]) + (v * plane_y[0]) + (w * plane_z[0])
    y = origin_y + (u * plane_x[1]) + (v * plane_y[1]) + (w * plane_z[1])
    z = origin_z + (u * plane_x[2]) + (v * plane_y[2]) + (w * plane_z[2])
    b = _hal("headheadtwp.twp_b_angle")
    c = _hal("headheadtwp.twp_c_angle")

    feed = words["l"] if "l" in words else self.feed_rate
    if not feed or feed <= 0.0:
        self.set_errormsg("G88.5 requires a positive feed rate or active F value")
        return INTERP_ERROR

    cmd = "G1 X%.6f Y%.6f Z%.6f B%.6f C%.6f F%.6f" % (x, y, z, b, c, feed)

    try:
        self.execute(cmd)
    except InterpreterException as exc:
        self.set_errormsg("%d: '%s' - %s" % (
            exc.line_number,
            exc.line_text,
            exc.error_message,
        ))
        return INTERP_ERROR

    MESSAGE("TWP move UVW=(%.3f, %.3f, %.3f) -> XYZ=(%.3f, %.3f, %.3f)" % (
        u, v, w, x, y, z
    ))
    return INTERP_OK
