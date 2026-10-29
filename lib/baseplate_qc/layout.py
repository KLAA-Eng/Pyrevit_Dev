# -*- coding: utf-8 -*-
"""Lay out a base plate, its anchor rods, and its column in plan.

Plan points are (x, y) tuples in feet; schedule and column sizes are inches.
The plate's shape and rods come from its detail type (baseplate_qc.details).
A square or rectangular plate's L runs along the wall the column sits on, or
along the column's own axis when there is no wall. An L-shaped plate puts
one leg along that wall and the other along a second, crossing wall; each
leg points toward the longer run of its wall.
"""

import math
import re

from .details import plate_geometry, point_in_polygon
from .schedule import format_inches, parse_inches


WALL_REACH = 0.5  # feet beyond the wall face a column may sit and still use it.
TOLERANCE = 1.0 / 16  # inches.
CROSSING_DOT = 0.3  # |cos| below which a second wall counts as crossing the first.

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

def _wall_hits(point, walls, reach):
    """Yield each wall segment the point sits on, with its distance and run lengths."""
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
            canonical = _canonical(axis)
            ahead, behind = length - along, along
            if canonical != axis:
                ahead, behind = behind, ahead
            yield {'id': wall['id'], 'axis': canonical, 'origin': closest, 'width': wall['width'],
                   'distance': distance, 'ahead': ahead, 'behind': behind}


def nearest_wall(point, walls, reach=WALL_REACH):
    """Return the wall segment a column point sits on, or None.

    walls are dicts {'id', 'points': [(x, y), ...] along the wall's location
    line, 'width' (feet)}. A wall qualifies when the point is within its
    half-width plus reach of the location line; the closest one wins. Returns
    {'id', 'axis' (unit), 'origin' (closest point), 'width', 'distance',
    'ahead', 'behind' (wall run, feet, along +axis and -axis)}.
    """
    best = None
    for hit in _wall_hits(point, walls, reach):
        if best is None or hit['distance'] < best['distance']:
            best = hit
    return best


def leg_directions(point, wall, walls, reach=WALL_REACH):
    """Return ((u sign, v sign), crossing wall or None) for an L-shaped plate.

    The u leg points along the column's wall toward its longer run. The v
    leg follows a crossing wall at the column toward that wall's longer run;
    without one it takes +v.
    """
    if wall is None:
        return (1, 1), None
    u_sign = 1 if wall['ahead'] >= wall['behind'] else -1
    normal = _perp(wall['axis'])
    crossing = [hit for hit in _wall_hits(point, walls, reach)
                if hit['id'] != wall['id'] and
                abs(hit['axis'][0] * wall['axis'][0] + hit['axis'][1] * wall['axis'][1]) < CROSSING_DOT]
    if not crossing:
        return (u_sign, 1), None
    other = min(crossing, key=lambda hit: hit['distance'])
    run = other['axis'] if other['ahead'] >= other['behind'] else (-other['axis'][0], -other['axis'][1])
    v_sign = 1 if run[0] * normal[0] + run[1] * normal[1] >= 0 else -1
    return (u_sign, v_sign), other


# -- Plate layout ------------------------------------------------------------------

def layout_plate(entry, definition, edge, center, column=None, column_axis=None, walls=()):
    """Return the drawing and review issues for one column's base plate.

    entry is a schedule entry (inches); definition is its detail type from
    baseplate_qc.details; edge is the edge distance "C" (inches) or None;
    center is the column point (feet); column is a parse_column_size dict or
    None; column_axis is the column's width direction (its hand orientation);
    walls are the nearest_wall dicts that may support the column.

    Returns {'axis', 'axis_source', 'plate' (corners), 'rods' [(center,
    radius)], 'column' (corners, or (center, radius) when round, or None),
    'label' (point), 'text', 'issues' [str]}; points and radii in feet.
    """
    issues = []
    length, width = entry['length'], entry['width']
    wall = nearest_wall(center, walls)
    if wall is not None:
        axis, source = wall['axis'], 'wall'
    else:
        axis = _canonical(_unit(column_axis or (1.0, 0.0)) or (1.0, 0.0))
        source = 'column'
    signs, crossing = (1, 1), None
    if definition['shape'] == 'L':
        if width >= length:
            issues.append('L-shaped plate needs W less than L.')
        signs, crossing = leg_directions(center, wall, walls)
        if crossing is None:
            issues.append('No crossing wall at the column; the L-shaped plate\'s second leg '
                          'direction is assumed.')

    geometry = plate_geometry(definition, length, width, edge or 0.0)
    column_u, column_v = geometry['column']

    def place(u, v):
        """Plate frame inches to plan feet, with the column at center."""
        return _point(center, axis, signs[0] * (u - column_u) / 12.0, signs[1] * (v - column_v) / 12.0)

    plate = [place(u, v) for u, v in geometry['plate']]
    rods = []
    if edge is None:
        issues.append('No edge distance for a {} rod; rods not drawn.'.format(
            format_inches(entry.get('rod_diameter'))))
    else:
        radius = (entry.get('rod_diameter') or 0.75) / 24.0
        rods = [(place(u, v), radius) for u, v in geometry['rods']]
        if any(not point_in_polygon(rod, plate) for rod, _ in rods):
            issues.append('Plate is too small for the {} rod edge distance.'.format(format_inches(edge)))
    count = len(definition['rods'])
    if entry.get('rod_count') not in (None, count):
        issues.append('Schedule lists {} rods; the TYPE {} detail shows {}.'.format(
            entry['rod_count'], definition['key'], count))

    column_shape = None
    if column is not None:
        col_axis = _canonical(_unit(column_axis or axis) or axis)
        if column['shape'] == 'round':
            column_shape = (center, column['width'] / 24.0)
        else:
            column_shape = _rect(center, col_axis, column['width'], column['depth'])
        issues.extend(_column_issues(column, col_axis, center, plate, rods))
    if wall is not None:
        issues.extend(_wall_issues(plate, [hit for hit in (wall, crossing) if hit is not None]))

    corner = max(geometry['plate'], key=lambda p: signs[0] * (p[0] - column_u) + signs[1] * (p[1] - column_v))
    label = place(corner[0] + signs[0] * 3.0, corner[1] + signs[1] * 3.0)
    text = '{} ({}) {}x{}'.format(entry['mark'], entry.get('type') or '?',
                                  format_inches(length).rstrip('"'), format_inches(width).rstrip('"'))
    return {'axis': axis, 'axis_source': source, 'plate': plate, 'rods': rods,
            'column': column_shape, 'label': label, 'text': text, 'issues': issues}


def _column_issues(column, col_axis, center, plate, rods):
    issues = []
    half_w, half_d = column['width'] / 2.0, column['depth'] / 2.0
    corners = [(su * half_w, sv * half_d) for su in (-1, 1) for sv in (-1, 1)]
    if column['shape'] == 'round':
        corners = [(half_w * math.cos(a), half_w * math.sin(a))
                   for a in (i * math.pi / 8 for i in range(16))]
    for cu, cv in corners:
        # Pull each corner in by the tolerance so a flush column passes.
        scale = max(0.0, 1.0 - TOLERANCE / max(math.hypot(cu, cv), 1e-9))
        if not point_in_polygon(_point(center, col_axis, cu * scale / 12.0, cv * scale / 12.0), plate):
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


def _wall_issues(plate, walls):
    """Flag a plate corner that hangs past the faces of every supporting wall."""
    def overhang(point, wall):
        normal = _perp(wall['axis'])
        offset = (point[0] - wall['origin'][0]) * normal[0] + (point[1] - wall['origin'][1]) * normal[1]
        return abs(offset) - wall['width'] / 2.0

    worst = max(min(overhang(point, wall) for wall in walls) for point in plate)
    if worst * 12 > TOLERANCE:
        return ['Plate hangs {} past the wall face.'.format(format_inches(worst * 12))]
    return []
