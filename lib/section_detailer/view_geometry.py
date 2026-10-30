"""View-plane geometry for placing detail components on a section.

Vectors are plain ``(x, y, z)`` tuples in model coordinates; the command
converts Revit ``XYZ`` values before calling these rules.
"""

import math


CUT_TOLERANCE = 0.9
IN_PLANE_TOLERANCE = 0.1
ANGLE_SNAP = 1e-6

CUT = 'cut'
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
    """Return how a straight member meets the section plane.

    ``cut`` runs into the view, ``in_plane`` runs along it, and ``oblique``
    is anything between; oblique members are reported, not placed.
    """
    axis = _unit(axis)
    if axis is None:
        return OBLIQUE
    alignment = abs(dot(axis, _unit(view_direction)))
    if alignment >= CUT_TOLERANCE:
        return CUT
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
