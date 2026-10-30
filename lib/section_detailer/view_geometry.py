"""View-plane geometry for placing detail components on a section.

Vectors are plain ``(x, y, z)`` tuples in model coordinates; the command
converts Revit ``XYZ`` values before calling these rules.
"""

import math


END_ON_TOLERANCE = 0.9
IN_PLANE_TOLERANCE = 0.1
ANGLE_SNAP = 1e-6

END_ON = 'end_on'
IN_PLANE = 'in_plane'
OBLIQUE = 'oblique'


def dot(first, second):
    return sum(a * b for a, b in zip(first, second))


def _unit(vector):
    length = math.sqrt(dot(vector, vector))
    if length == 0:
        return None
    return tuple(value / length for value in vector)


def classify_member(axis, view_direction):
    """Return how a straight member is seen in the section.

    ``end_on`` runs into the view (cut or beyond, shown by its profile),
    ``in_plane`` runs along the view (shown from the side), and ``oblique``
    is anything between; oblique members are reported, not placed.
    """
    axis = _unit(axis)
    if axis is None:
        return OBLIQUE
    alignment = abs(dot(axis, _unit(view_direction)))
    if alignment >= END_ON_TOLERANCE:
        return END_ON
    if alignment <= IN_PLANE_TOLERANCE:
        return IN_PLANE
    return OBLIQUE


def crosses_plane(start, end, origin, normal):
    """Return True when the segment start-end touches or crosses the plane."""
    first = dot([s - o for s, o in zip(start, origin)], normal)
    second = dot([e - o for e, o in zip(end, origin)], normal)
    return first * second <= 0


def to_view(point, origin, right, up):
    """Return ``(u, v)`` view-plane coordinates of a model point."""
    offset = [p - o for p, o in zip(point, origin)]
    return dot(offset, right), dot(offset, up)


def bounds_center(points):
    """Return the center of the 2D bounding box of ``(u, v)`` points."""
    if not points:
        return None
    us = [point[0] for point in points]
    vs = [point[1] for point in points]
    return (min(us) + max(us)) / 2.0, (min(vs) + max(vs)) / 2.0


def unit_2d(vector):
    """Return a 2D unit vector, or None for a zero-length vector."""
    length = math.hypot(vector[0], vector[1])
    if length == 0:
        return None
    return vector[0] / length, vector[1] / length


def width_direction(depth_2d):
    """Return the in-view direction across a member's width.

    It is the depth direction turned clockwise, so a member whose depth
    points up has its width running to the right.
    """
    return depth_2d[1], -depth_2d[0]


def extent_along(points, direction):
    """Return ``(min, max)`` of 2D points measured along a unit direction."""
    values = [point[0] * direction[0] + point[1] * direction[1] for point in points]
    return min(values), max(values)


def ply_offsets(plies, ply_width):
    """Return center offsets for ``plies`` side-by-side plies."""
    return [(index - (plies - 1) / 2.0) * ply_width for index in range(plies)]


def side_segment(points, axis_2d, depth_2d):
    """Return the 2D centerline ``(start, end)`` of a member seen from the side.

    ``points`` are the member's projected outline. The line runs the full
    projected length at the middle of the depth, and is oriented so the
    member's depth lies counterclockwise of the line direction.
    """
    axis = unit_2d(axis_2d)
    if axis is None or not points:
        return None
    if depth_2d is not None and axis[0] * depth_2d[1] - axis[1] * depth_2d[0] < 0:
        axis = (-axis[0], -axis[1])
    across = (-axis[1], axis[0])
    start, end = extent_along(points, axis)
    low, high = extent_along(points, across)
    middle = (low + high) / 2.0
    if end - start <= 0:
        return None
    return ((axis[0] * start + across[0] * middle, axis[1] * start + across[1] * middle),
            (axis[0] * end + across[0] * middle, axis[1] * end + across[1] * middle))


def clip_segment(start, end, rect):
    """Clip a 2D segment to ``(min_u, min_v, max_u, max_v)``; None if outside.

    Liang-Barsky clipping; a None rect means no crop and leaves it unchanged.
    """
    if rect is None:
        return start, end
    du, dv = end[0] - start[0], end[1] - start[1]
    low, high = 0.0, 1.0
    for p, q in ((-du, start[0] - rect[0]), (du, rect[2] - start[0]),
                 (-dv, start[1] - rect[1]), (dv, rect[3] - start[1])):
        if p == 0:
            if q < 0:
                return None
            continue
        t = q / float(p)
        if p < 0:
            low = max(low, t)
        else:
            high = min(high, t)
        if low > high:
            return None
    return ((start[0] + low * du, start[1] + low * dv),
            (start[0] + high * du, start[1] + high * dv))


def rotation_in_view(depth, right, up):
    """Return the counterclockwise angle that turns view-up onto ``depth``.

    ``depth`` is the member's section-depth direction (web direction for a
    wide flange). Revit rotates about the view direction, and right x up is
    the view direction, so a positive angle is counterclockwise on screen.
    """
    x = dot(depth, right)
    y = dot(depth, up)
    if abs(x) < ANGLE_SNAP and abs(y) < ANGLE_SNAP:
        return 0.0
    angle = math.atan2(-x, y)
    if abs(angle) < ANGLE_SNAP:
        return 0.0
    return angle
