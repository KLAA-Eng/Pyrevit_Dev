# -*- coding: utf-8 -*-
"""Read base plate detail types (TYPE A, TYPE B, ...) from their linework.

Each detail sits above a text label reading TYPE <key>. Its plate is the
largest closed loop of lines there: four corners is a square or rectangular
plate, six corners an L-shaped plate whose two legs are each L long and W
wide. Anything else is too complex and the type is left out.

The details are not to scale, so each rod is placed by the rule its drawn
position matches: the edge distance "C" from a plate edge (or from the
inside of an L leg), the middle of the plate or leg, or the middle plus or
minus half a dimensioned spacing such as 2 1/2". The "C" dimension and the
"L" dimension's direction are read from dimensions whose text is
overridden to C and L.

Input geometry is in view coordinates (feet): polylines are point lists
(arcs tessellated), arcs are {'center', 'radius', 'sweep' (radians)}, and
dimension segments are {'value' (feet), 'text' (override, '' for none),
'origin', 'direction', 'equal' (shown as EQ)}.
"""

import math
import re

from .schedule import format_inches, normalize_text, parse_inches, split_lines


SQUARE_RATIO = 1.15  # Drawn L/W at or below this reads as a square plate.
DEFAULT_HALF_WIDTH = 2.0  # feet each side of a lone TYPE label.
_LABEL_RE = re.compile(r'^TYPE\s+([A-Z0-9]+)$')

SHAPE_NAMES = {'square': 'square', 'rectangular': 'rectangular', 'L': 'L-shaped'}


# -- Labels and regions ------------------------------------------------------------

def _center(cell):
    return ((cell['xmin'] + cell['xmax']) / 2.0, (cell['ymin'] + cell['ymax']) / 2.0)


def find_type_labels(cells):
    """Return [(type key, cell)] for text reading TYPE A, TYPE B, ..."""
    labels = []
    for cell in split_lines(cells):
        match = _LABEL_RE.match(normalize_text(cell['text']))
        if match:
            labels.append((match.group(1), cell))
    return labels


def detail_regions(labels, cells):
    """Return {key: (xmin, ymin, xmax, ymax)} for the area above each label.

    A region is as wide as half the gap to the neighboring labels on each
    side and runs up to the first wide text above it (a table note or
    title), or as tall as it is wide.
    """
    regions = {}
    for key, label in labels:
        cx, cy = _center(label)
        height = label['ymax'] - label['ymin']
        gaps = [abs(_center(other)[0] - cx) for _, other in labels
                if other is not label and abs(_center(other)[1] - cy) < height]
        half = min(gaps) / 2.0 if gaps else DEFAULT_HALF_WIDTH
        bottom = label['ymax']
        top = bottom + 2.0 * half
        for cell in cells:
            wide = cell['xmax'] - cell['xmin'] > half
            if wide and cell['ymin'] >= bottom and cell['xmax'] > cx - half and cell['xmin'] < cx + half:
                top = min(top, cell['ymin'])
        regions[key] = (cx - half, bottom, cx + half, top)
    return regions


def _inside_region(point, region):
    return region[0] <= point[0] <= region[2] and region[1] <= point[1] <= region[3]


# -- Polygons ----------------------------------------------------------------------

def polygon_area(points):
    total = 0.0
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def point_in_polygon(point, polygon):
    x, y = point
    inside = False
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def _bounds(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _simplify(points):
    """Drop vertices where the outline runs straight on."""
    changed = True
    while changed and len(points) > 3:
        changed = False
        for index in range(len(points)):
            prev, here, nxt = points[index - 1], points[index], points[(index + 1) % len(points)]
            ax, ay = here[0] - prev[0], here[1] - prev[1]
            bx, by = nxt[0] - here[0], nxt[1] - here[1]
            la, lb = math.hypot(ax, ay), math.hypot(bx, by)
            if la < 1e-9 or lb < 1e-9 or abs(ax * by - ay * bx) / (la * lb) < 0.02:
                points = points[:index] + points[index + 1:]
                changed = True
                break
    return points


def find_loops(polylines, tolerance):
    """Return closed outlines (vertex lists) formed by the lines.

    Endpoints within tolerance join. Lines dangling off an outline (leaders,
    loose ends) are pruned; a group of lines where any point joins three or
    more lines is not a simple outline and is skipped.
    """
    nodes = []

    def node(point):
        for index, other in enumerate(nodes):
            if abs(point[0] - other[0]) <= tolerance and abs(point[1] - other[1]) <= tolerance:
                return index
        nodes.append(point)
        return len(nodes) - 1

    links = {}
    for points in polylines:
        for a, b in zip(points, points[1:]):
            i, j = node(a), node(b)
            if i != j:
                links.setdefault(i, set()).add(j)
                links.setdefault(j, set()).add(i)
    pruned = True
    while pruned:
        pruned = False
        for index in list(links):
            if len(links[index]) <= 1:
                for other in links.pop(index):
                    links[other].discard(index)
                pruned = True
    loops = []
    seen = set()
    for start in links:
        if start in seen:
            continue
        component, stack = set(), [start]
        while stack:
            index = stack.pop()
            if index not in component:
                component.add(index)
                stack.extend(links[index])
        seen |= component
        if any(len(links[index]) != 2 for index in component):
            continue
        order, previous = [start], None
        while True:
            here = order[-1]
            following = [index for index in links[here] if index != previous][0]
            if following == start:
                break
            previous = here
            order.append(following)
        loop = _simplify([nodes[index] for index in order])
        if len(loop) >= 3:
            loops.append(loop)
    return loops


# -- Detail reading ----------------------------------------------------------------

def _orthogonal(points, tolerance):
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        if abs(x1 - x2) > tolerance and abs(y1 - y2) > tolerance:
            return False
    return True


def _circle_centers(arcs, region, tolerance):
    """Return centers of circles (arcs with matching centers adding to a full turn)."""
    groups = []
    for arc in arcs:
        if not _inside_region(arc['center'], region):
            continue
        for group in groups:
            if (abs(group['center'][0] - arc['center'][0]) <= tolerance and
                    abs(group['center'][1] - arc['center'][1]) <= tolerance and
                    abs(group['radius'] - arc['radius']) <= tolerance):
                group['sweep'] += arc['sweep']
                break
        else:
            groups.append({'center': arc['center'], 'radius': arc['radius'], 'sweep': arc['sweep']})
    circles = [group for group in groups if group['sweep'] >= math.radians(300)]
    centers = []
    for circle in circles:  # A rod and its hole or washer circle share a center.
        if not any(abs(c[0] - circle['center'][0]) <= tolerance and
                   abs(c[1] - circle['center'][1]) <= tolerance for c, _ in centers):
            centers.append((circle['center'], circle['radius']))
    return centers


def _frame(shape, plate, dims, tolerance):
    """Return (to_frame, length, width, horizontal_axis) for the drawn plate.

    to_frame maps a drawn point to (u, v) measured from the plate's start
    corner: along L and across W for a rectangle; along the two legs from
    the corner where they meet for an L. horizontal_axis is 'u' or 'v'.
    """
    xmin, ymin, xmax, ymax = _bounds(plate)
    width_x, height_y = xmax - xmin, ymax - ymin
    if shape == 'rect':
        l_dims = [dim for dim in dims if _dim_text(dim) == 'L']
        if l_dims:
            horizontal = abs(l_dims[0]['direction'][0]) >= abs(l_dims[0]['direction'][1])
        else:
            horizontal = width_x >= height_y
        if horizontal:
            return (lambda p: (p[0] - xmin, p[1] - ymin)), width_x, height_y, 'u'
        return (lambda p: (p[1] - ymin, p[0] - xmin)), height_y, width_x, 'v'
    # L shape: the bounding box corner outside the plate is the notch; the
    # legs meet at the opposite corner.
    step = tolerance * 2
    for cx, cy, sx, sy in ((xmin, ymin, 1, 1), (xmax, ymin, -1, 1), (xmin, ymax, 1, -1), (xmax, ymax, -1, -1)):
        if not point_in_polygon((cx + sx * step, cy + sy * step), plate):
            meet_x, meet_y = (xmax if sx > 0 else xmin), (ymax if sy > 0 else ymin)
            dir_x, dir_y = -sx, -sy
            break
    else:
        return None
    to_frame = lambda p: ((p[0] - meet_x) * dir_x, (p[1] - meet_y) * dir_y)
    inner = [to_frame(p) for p in plate if tolerance < (p[0] - meet_x) * dir_x < width_x - tolerance
             and tolerance < (p[1] - meet_y) * dir_y < height_y - tolerance]
    if len(inner) != 1:
        return None
    leg_u_width, leg_v_width = inner[0][1], inner[0][0]
    return to_frame, (width_x, height_y), (leg_u_width, leg_v_width), 'u'


def _dim_text(dim):
    return normalize_text(dim.get('text') or '').replace('"', '').replace("'", '').replace(' ', '')


def _anchors(shape, axis, spacings):
    """Return the rod position rules for one axis.

    Each rule is (name, (a, b, c, d), S drawn, S true): a position is
    L*a + W*b + C*c + S*d for the plate's L, W, and edge distance C, with S
    the rule's dimensioned spacing (0 when it has none) in drawn feet for
    matching and true inches for plates.
    """
    if shape == 'rect':
        size = (1, 0) if axis == 'u' else (0, 1)
        middle = (size[0] / 2.0, size[1] / 2.0)
        rules = [('C from the start', (0, 0, 1, 0), 0.0, 0.0),
                 ('C from the end', (size[0], size[1], -1, 0), 0.0, 0.0),
                 ('middle', (middle[0], middle[1], 0, 0), 0.0, 0.0)]
    else:
        middle = (0, 0.5)
        rules = [('C from the outside', (0, 0, 1, 0), 0.0, 0.0),
                 ('C from the inside of the leg', (0, 1, -1, 0), 0.0, 0.0),
                 ('middle of the leg', (0, 0.5, 0, 0), 0.0, 0.0),
                 ('C from the leg end', (1, 0, -1, 0), 0.0, 0.0)]
    for drawn, true in spacings:
        for sign in (-1, 1):
            rules.append(('middle {} half of {}'.format('-' if sign < 0 else '+', format_inches(true)),
                          (middle[0], middle[1], 0, sign * 0.5), drawn, true))
    return rules


def _evaluate(rule, length, width, edge):
    a, b, c, d = rule[1]
    return a * length + b * width + c * edge + d * rule[2]


def read_type_details(cells, polylines, arcs, dims):
    """Return ({key: definition}, {key: problem}) for every TYPE label found.

    A definition is {'key', 'shape' ('square' | 'rectangular' | 'L'), 'rods'
    [(u rule, v rule)]}; plate_geometry turns it into a plate.
    """
    labels = find_type_labels(cells)
    regions = detail_regions(labels, cells)
    keys = [key for key, _ in labels]
    definitions, problems = {}, {}
    for key in keys:
        if keys.count(key) > 1:
            problems[key] = 'TYPE {} is labeled more than once.'.format(key)
            continue
        definition, problem = _read_detail(key, regions[key], polylines, arcs, dims)
        if definition is None:
            problems[key] = problem
        else:
            definitions[key] = definition
    return definitions, problems


def _read_detail(key, region, polylines, arcs, dims):
    tolerance = (region[2] - region[0]) * 0.002
    local = [points for points in polylines if all(_inside_region(p, region) for p in points)]
    loops = find_loops(local, tolerance)
    if not loops:
        return None, 'TYPE {}: no closed plate outline was found above the label.'.format(key)
    plate = max(loops, key=polygon_area)
    if len(plate) == 4:
        shape = 'rect'
    elif len(plate) == 6:
        shape = 'L'
    else:
        return None, ('TYPE {}: the plate outline has {} corners; only square, rectangular, and '
                      'L-shaped plates are supported.'.format(key, len(plate)))
    if not _orthogonal(plate, tolerance * 5):
        return None, 'TYPE {}: the plate outline is not square to the page.'.format(key)
    region_dims = [dim for dim in dims if _inside_region(dim['origin'], region)]
    frame = _frame(shape, plate, region_dims, tolerance)
    if frame is None:
        return None, 'TYPE {}: the L-shaped outline could not be read.'.format(key)
    to_frame, length, width, horizontal = frame
    if shape == 'L':
        (len_u, len_v), (wid_u, wid_v) = length, width
        if abs(len_u - len_v) > 0.15 * max(len_u, len_v) or abs(wid_u - wid_v) > 0.15 * max(wid_u, wid_v):
            return None, ('TYPE {}: the L-shaped plate has legs of different sizes; only legs that '
                          'are both L x W are supported.'.format(key))
        length, width = (len_u + len_v) / 2.0, (wid_u + wid_v) / 2.0
        name = 'L'
    else:
        ratio = max(length, width) / min(length, width)
        name = 'square' if ratio <= SQUARE_RATIO else 'rectangular'

    rods = [to_frame(center) for center, radius in _circle_centers(arcs, region, tolerance * 5)
            if point_in_polygon(center, plate) and radius < 0.25 * min(length, width)]
    if not rods:
        return None, 'TYPE {}: no anchor rod circles were found inside the plate.'.format(key)

    edge = [dim['value'] for dim in region_dims if _dim_text(dim) == 'C' and dim.get('value')]
    if edge:
        edge = sorted(edge)[len(edge) // 2]
    else:
        edge = min(min(u, v, length - u, (width if shape == 'rect' else length) - v) for u, v in rods)
    if edge <= 0:
        return None, 'TYPE {}: the edge distance "C" could not be read.'.format(key)

    # A measured dimension shows its own length; one typed over with a size
    # such as 2 1/2" shows that size. Either way it is a true rod spacing.
    spacings = {'u': [], 'v': []}
    for dim in region_dims:
        if dim.get('equal') or not dim.get('value'):
            continue
        text = _dim_text(dim)
        true = parse_inches(dim['text']) if text else dim['value'] * 12.0
        if true is None or true <= 0:
            continue
        along_x = abs(dim['direction'][0]) >= abs(dim['direction'][1])
        axis = horizontal if along_x else ('v' if horizontal == 'u' else 'u')
        spacings[axis].append((round(dim['value'], 6), round(true, 4)))
    rules = {axis: _anchors(shape, axis, sorted(set(spacings[axis]))) for axis in ('u', 'v')}

    placed = []
    reach = max(0.4 * edge, 0.03 * length)
    for u, v in rods:
        pair = []
        for axis, value in (('u', u), ('v', v)):
            # On a near tie, a rule from a spacing dimension wins: it was drawn for this rod.
            best = min(rules[axis], key=lambda rule: abs(_evaluate(rule, length, width, edge) - value)
                       - (0.1 * reach if rule[2] else 0.0))
            if abs(_evaluate(best, length, width, edge) - value) > reach:
                return None, ('TYPE {}: an anchor rod is not at "C" from an edge or at a dimensioned '
                              'spacing.'.format(key))
            pair.append((best[0], best[1], best[3]))
        placed.append(tuple(pair))
    if len(set(placed)) != len(placed):
        return None, 'TYPE {}: two anchor rods read as the same position.'.format(key)

    column = _column_center(loops, plate, rods, to_frame)
    expected = (length / 2.0, width / 2.0) if shape == 'rect' else (width / 2.0, width / 2.0)
    if column is not None and (abs(column[0] - expected[0]) > 0.15 * length or
                               abs(column[1] - expected[1]) > 0.15 * length):
        return None, 'TYPE {}: the column is not centered {}.'.format(
            key, 'on the plate' if shape == 'rect' else 'where the legs meet')
    return {'key': key, 'shape': name, 'rods': placed}, None


def _column_center(loops, plate, rods, to_frame):
    """Return the drawn column's center in the plate frame, or None."""
    plate_area = polygon_area(plate)
    candidates = []
    for loop in loops:
        if loop is plate or polygon_area(loop) > 0.6 * plate_area:
            continue
        frame_loop = [to_frame(p) for p in loop]
        if any(point_in_polygon(rod, frame_loop) for rod in rods):
            continue  # A rod washer.
        if all(point_in_polygon(p, plate) or _on_outline(p, plate) for p in loop):
            candidates.append(loop)
    if not candidates:
        return None
    xmin, ymin, xmax, ymax = _bounds(max(candidates, key=polygon_area))
    return to_frame(((xmin + xmax) / 2.0, (ymin + ymax) / 2.0))


def _on_outline(point, polygon, tolerance=1e-6):
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        if min(x1, x2) - tolerance <= point[0] <= max(x1, x2) + tolerance and \
                min(y1, y2) - tolerance <= point[1] <= max(y1, y2) + tolerance:
            if abs((x2 - x1) * (point[1] - y1) - (y2 - y1) * (point[0] - x1)) <= tolerance:
                return True
    return False


# -- Plate geometry ----------------------------------------------------------------

def plate_geometry(definition, length, width, edge):
    """Return {'plate', 'rods', 'column'} in inches, in the definition's frame.

    A rectangle runs from (0, 0) to (L, W) with the column at its middle; an
    L has legs L long and W wide along +u and +v from (0, 0), with the column
    in the middle of the W x W square where they meet.
    """
    if definition['shape'] == 'L':
        plate = [(0, 0), (length, 0), (length, width), (width, width), (width, length), (0, length)]
        column = (width / 2.0, width / 2.0)
    else:
        plate = [(0, 0), (length, 0), (length, width), (0, width)]
        column = (length / 2.0, width / 2.0)
    rods = [(_evaluate(rule_u, length, width, edge), _evaluate(rule_v, length, width, edge))
            for rule_u, rule_v in definition['rods']]
    return {'plate': plate, 'rods': rods, 'column': column}


def describe(definition):
    """Return text such as 'square plate, 4 rods' for the palette."""
    return '{} plate, {} rods'.format(SHAPE_NAMES[definition['shape']], len(definition['rods']))
