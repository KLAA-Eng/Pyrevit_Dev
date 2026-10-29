# -*- coding: utf-8 -*-
"""Lay out a base plate, its anchor rods, and its column in plan.

Plan points are (x, y) tuples in feet; schedule and column sizes are inches.
The plate's L dimension runs along the wall the column sits on (or along the
column's own axis when no wall is found) and the column is centered on the
plate, per the base plate detail types:

- Type A and B: four rods, one at each plate corner, the edge distance "C"
  in from both edges.
- Type C: two pairs of rods, the edge distance "C" in from each L end, the
  rods of a pair TYPE_C_ROD_SPACING apart across W.
"""

import math
import re

from .schedule import format_inches, parse_inches


TYPE_C_ROD_SPACING = 2.5  # inches, from the Type C detail.
KNOWN_TYPES = ('A', 'B', 'C')
WALL_REACH = 0.5  # feet beyond the wall face a column may sit and still use it.
TOLERANCE = 1.0 / 16  # inches.

_HSS_RE = re.compile(r'HSS\s*([0-9./\s-]+(?:X[0-9./\s-]+)+)')


def parse_column_size(name):
    """Return {'shape', 'depth', 'width'} in inches from an HSS size, or None.

    HSS8x4x1/2 is 8 deep (along the column's facing) by 4 wide; HSS6.625x0.280
    is round with a 6.625 diameter. Other shapes need the family's parameters.
    """
    match = _HSS_RE.search((name or '').upper())
    if not match:
        return None
    parts = [part.strip() for part in match.group(1).split('X')]
    sizes = [parse_inches(re.sub(r'(\d)-(\d)', r'\1 \2', part)) for part in parts]
    if any(size is None for size in sizes):
        return None
    if len(sizes) == 2:
        return {'shape': 'round', 'depth': sizes[0], 'width': sizes[0]}
    return {'shape': 'rect', 'depth': sizes[0], 'width': sizes[1]}


# -- Vectors -----------------------------------------------------------------------

def _unit(vector):
    length = math.hypot(vector[0], vector[1])
    if length < 1e-9:
        return None
    return (vector[0] / length, vector[1] / length)


def _canonical(axis):
    """Point an axis into +x (or +y when vertical) so labels land consistently."""
    if axis[0] < -1e-9 or (abs(axis[0]) <= 1e-9 and axis[1] < 0):
        return (-axis[0], -axis[1])
    return axis


def _perp(axis):
    return (-axis[1], axis[0])


def _point(center, axis, u_feet, v_feet):
    normal = _perp(axis)
    return (center[0] + axis[0] * u_feet + normal[0] * v_feet,
            center[1] + axis[1] * u_feet + normal[1] * v_feet)


def _local(point, center, axis):
    dx, dy = point[0] - center[0], point[1] - center[1]
    normal = _perp(axis)
    return (dx * axis[0] + dy * axis[1], dx * normal[0] + dy * normal[1])


def _rect(center, axis, length, width):
    """Corners (feet) of a length x width (inches) rectangle centered on center."""
    half_u, half_v = length / 24.0, width / 24.0
    return [_point(center, axis, u, v)
            for u, v in ((-half_u, -half_v), (half_u, -half_v), (half_u, half_v), (-half_u, half_v))]


# -- Walls -------------------------------------------------------------------------

def nearest_wall(point, walls, reach=WALL_REACH):
    """Return the wall segment a column point sits on, or None.

    walls are dicts {'id', 'points': [(x, y), ...] along the wall's location
    line, 'width' (feet)}. A wall qualifies when the point is within its
    half-width plus reach of the location line; the closest one wins. Returns
    {'id', 'axis' (unit), 'origin' (closest point), 'width', 'distance'}.
    """
    best = None
    for wall in walls:
        points = wall['points']
        for start, end in zip(points, points[1:]):
            axis = _unit((end[0] - start[0], end[1] - start[1]))
            if axis is None:
                continue
            length = math.hypot(end[0] - start[0], end[1] - start[1])
            along = (point[0] - start[0]) * axis[0] + (point[1] - start[1]) * axis[1]
            along = max(0.0, min(length, along))
            closest = (start[0] + axis[0] * along, start[1] + axis[1] * along)
            distance = math.hypot(point[0] - closest[0], point[1] - closest[1])
            if distance > wall['width'] / 2.0 + reach:
                continue
            if best is None or distance < best['distance']:
                best = {'id': wall['id'], 'axis': _canonical(axis), 'origin': closest,
                        'width': wall['width'], 'distance': distance}
    return best


# -- Plate layout ------------------------------------------------------------------

def rod_offsets(plate_type, length, width, edge):
    """Return rod (u, v) offsets in inches from the plate center for a detail type."""
    half_u = length / 2.0 - edge
    if plate_type == 'C':
        half_v = TYPE_C_ROD_SPACING / 2.0
    else:
        half_v = width / 2.0 - edge
    return [(su * half_u, sv * half_v) for su in (-1, 1) for sv in (-1, 1)]


def layout_plate(entry, edge, center, column=None, column_axis=None, wall=None):
    """Return the drawing and review issues for one column's base plate.

    entry is a schedule entry (inches); edge is the edge distance "C" (inches);
    center is the column point (feet); column is a parse_column_size dict or
    None; column_axis is the column's width direction (its hand orientation);
    wall is a nearest_wall result or None.

    Returns {'axis', 'axis_source', 'plate' (corners), 'rods' [(center,
    radius)], 'column' (corners, or (center, radius) when round, or None),
    'label' (point), 'text', 'issues' [str]}; points and radii in feet.
    """
    issues = []
    plate_type = entry.get('type')
    if plate_type not in KNOWN_TYPES:
        issues.append('Type {} is not in the base plate detail; drawn as Type A.'.format(plate_type or '?'))
        plate_type = 'A'
    length, width = entry['length'], entry['width']
    if wall is not None:
        axis, source = wall['axis'], 'wall'
    else:
        axis = _canonical(_unit(column_axis or (1.0, 0.0)) or (1.0, 0.0))
        source = 'column'

    rods = []
    if edge is None:
        issues.append('No edge distance for a {} rod; rods not drawn.'.format(
            format_inches(entry.get('rod_diameter'))))
    else:
        if length / 2.0 - edge <= 0 or (plate_type != 'C' and width / 2.0 - edge <= 0):
            issues.append('Plate is too small for the {} rod edge distance.'.format(format_inches(edge)))
        radius = (entry.get('rod_diameter') or 0.75) / 24.0
        for u, v in rod_offsets(plate_type, length, width, edge):
            rods.append((_point(center, axis, u / 12.0, v / 12.0), radius))
    if entry.get('rod_count') not in (None, 4):
        issues.append('Schedule lists {} rods; the detail shows 4.'.format(entry['rod_count']))

    column_shape = None
    if column is not None:
        col_axis = _canonical(_unit(column_axis or axis) or axis)
        if column['shape'] == 'round':
            column_shape = (center, column['width'] / 24.0)
        else:
            column_shape = _rect(center, col_axis, column['width'], column['depth'])
        issues.extend(_column_issues(column, col_axis, center, axis, length, width, rods))

    plate = _rect(center, axis, length, width)
    if wall is not None:
        issues.extend(_wall_issues(plate, wall))

    label = _point(center, axis, length / 24.0 + 0.25, width / 24.0 + 0.25)
    text = '{} ({}) {}x{}'.format(entry['mark'], entry.get('type') or '?',
                                  format_inches(length).rstrip('"'), format_inches(width).rstrip('"'))
    return {'axis': axis, 'axis_source': source, 'plate': plate, 'rods': rods,
            'column': column_shape, 'label': label, 'text': text, 'issues': issues}


def _column_issues(column, col_axis, center, axis, length, width, rods):
    issues = []
    half_w, half_d = column['width'] / 2.0, column['depth'] / 2.0
    corners = [(su * half_w, sv * half_d) for su in (-1, 1) for sv in (-1, 1)]
    if column['shape'] == 'round':
        corners = [(half_w * math.cos(a), half_w * math.sin(a))
                   for a in (i * math.pi / 8 for i in range(16))]
    for cu, cv in corners:
        world = _point(center, col_axis, cu / 12.0, cv / 12.0)
        u, v = _local(world, center, axis)
        if abs(u) * 12 > length / 2.0 + TOLERANCE or abs(v) * 12 > width / 2.0 + TOLERANCE:
            issues.append('Column is larger than the plate.')
            break
    for rod_center, radius in rods:
        u, v = _local(rod_center, center, col_axis)
        u, v, r = u * 12, v * 12, radius * 12
        if column['shape'] == 'round':
            gap = math.hypot(u, v) - half_w - r
        else:
            du, dv = max(abs(u) - half_w, 0.0), max(abs(v) - half_d, 0.0)
            inside = abs(u) < half_w and abs(v) < half_d
            gap = -1.0 if inside else math.hypot(du, dv) - r
        if gap < -TOLERANCE:
            issues.append('An anchor rod falls on the column.')
            break
    return issues


def _wall_issues(plate, wall):
    """Flag a plate that hangs past either wall face."""
    normal = _perp(wall['axis'])
    origin = wall['origin']
    half = wall['width'] / 2.0
    worst = max(abs((x - origin[0]) * normal[0] + (y - origin[1]) * normal[1]) for x, y in plate) - half
    if worst * 12 > TOLERANCE:
        return ['Plate hangs {} past the wall face.'.format(format_inches(worst * 12))]
    return []
