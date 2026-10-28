# -*- coding: utf-8 -*-
"""Host-independent placement math for PDF overlays.

A pose places the source page raster in a view's 2D plane. Page pixels use the
raster convention (origin top-left, v down); view coordinates use the view's
right/up basis in feet. The pose maps a page pixel to the view as

    view = center + feet_per_pixel * R(rotation) * offset(pixel)

where offset is measured from the page center with y up.
"""

import cmath
import math


SNAP_DEGREES = 0.5
MIN_PICK_PIXELS = 10.0
MIN_PICK_FEET = 0.1
INCHES_PER_FOOT = 12.0


def make_pose(center, feet_per_pixel, rotation=0.0):
    return {
        'center': [float(center[0]), float(center[1])],
        'feet_per_pixel': float(feet_per_pixel),
        'rotation': float(rotation),
    }


def initial_feet_per_pixel(view_scale, dpi):
    """Return feet per pixel for a page printed at the active view's scale."""
    if view_scale <= 0 or dpi <= 0:
        raise ValueError('view scale and DPI must be positive')
    return float(view_scale) / (INCHES_PER_FOOT * float(dpi))


def page_offset(pixel, page_size):
    """Return a page pixel as a complex offset from the page center, y up."""
    return complex(pixel[0] - page_size[0] / 2.0, page_size[1] / 2.0 - pixel[1])


def _pose_factor(pose):
    return cmath.rect(pose['feet_per_pixel'], pose['rotation'])


def pixel_to_view(pose, page_size, pixel):
    point = complex(*pose['center']) + _pose_factor(pose) * page_offset(pixel, page_size)
    return (point.real, point.imag)


def view_to_pixel(pose, page_size, point):
    offset = (complex(*point) - complex(*pose['center'])) / _pose_factor(pose)
    return (offset.real + page_size[0] / 2.0, page_size[1] / 2.0 - offset.imag)


def normalize_angle(radians):
    """Return an equivalent angle in (-pi, pi]."""
    value = math.fmod(radians, 2.0 * math.pi)
    if value <= -math.pi:
        value += 2.0 * math.pi
    elif value > math.pi:
        value -= 2.0 * math.pi
    return value


def snap_rotation(radians, snap_degrees=SNAP_DEGREES):
    """Return the nearest quarter turn within snap_degrees, else None."""
    quarter = math.pi / 2.0
    nearest = round(radians / quarter) * quarter
    if abs(radians - nearest) <= math.radians(snap_degrees):
        return normalize_angle(nearest)
    return None


def fit_pose(page_size, pixels, targets, snap_degrees=SNAP_DEGREES):
    """Fit a pose so two page pixels land on two view targets.

    Rotations within snap_degrees of a quarter turn are snapped, which keeps an
    orthogonal drawing crisp despite small pick error; scale and position are
    then fit symmetrically about the two picks.
    """
    a1, a2 = [page_offset(pixel, page_size) for pixel in pixels]
    t1, t2 = [complex(*target) for target in targets]
    if abs(a2 - a1) < MIN_PICK_PIXELS:
        raise ValueError('The two PDF points are too close together.')
    if abs(t2 - t1) < MIN_PICK_FEET:
        raise ValueError('The two Revit points are too close together.')
    factor = (t2 - t1) / (a2 - a1)
    rotation = cmath.phase(factor)
    snapped = snap_rotation(rotation, snap_degrees)
    if snapped is not None:
        unit = cmath.rect(1.0, snapped)
        scale = ((t2 - t1) * (unit * (a2 - a1)).conjugate()).real / abs(a2 - a1) ** 2
        if scale > 0:
            factor, rotation = unit * scale, snapped
    center = (t1 + t2) / 2.0 - factor * (a1 + a2) / 2.0
    return make_pose((center.real, center.imag), abs(factor), normalize_angle(rotation))


def rotated_canvas_size(width, height, radians):
    """Return the pixel size that holds a page rotated about its center."""
    cos_a = abs(math.cos(radians))
    sin_a = abs(math.sin(radians))
    # Round away float noise first so an exact quarter turn keeps its size.
    canvas_width = int(math.ceil(round(width * cos_a + height * sin_a, 6)))
    canvas_height = int(math.ceil(round(width * sin_a + height * cos_a, 6)))
    return (max(canvas_width, 1), max(canvas_height, 1))


def image_size_feet(pose, page_size):
    """Return the Revit image width and height for the rendered, rotated canvas."""
    canvas = rotated_canvas_size(page_size[0], page_size[1], pose['rotation'])
    return (canvas[0] * pose['feet_per_pixel'], canvas[1] * pose['feet_per_pixel'])
