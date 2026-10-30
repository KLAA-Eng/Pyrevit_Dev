# -*- coding: utf-8 -*-
"""Read base plate detail types (TYPE A, TYPE B, ...) from their linework.

Each detail sits above a text label reading TYPE <key>. The lines there are
split where they cross or touch and loose ends are trimmed, so leaders,
centerlines, and a column drawn over the plate do not break its outline.
The plate is the largest outline left: four corners (or nearly a full
rectangle) is a square or rectangular plate, six corners an L-shaped plate
whose legs are L long and W wide. Anything else is too complex and the
type is left out.

The details are not to scale, so the rods and the column are placed by the
rule their drawn positions match on each axis: the edge distance "C" or a
dimensioned distance (such as 2" or 2 3/4", alone or two chained) from a
plate edge, an L leg's inside edge, or the middle; or the middle itself.
The "C" dimension and the "L" dimension's direction are read from
dimensions whose text is overridden to C and L.

Input geometry is in view coordinates (feet): polylines are point lists
(arcs tessellated), arcs are {'center', 'radius', 'sweep' (radians)}, and
dimension segments are {'value' (feet), 'text' (override, '' for none),
'origin', 'direction', 'equal' (shown as EQ)}.
"""

import math
import re

from .schedule import format_inches, normalize_text, parse_inches, split_lines


SQUARE_RATIO = 1.15  # Drawn L/W at or below this reads as a square plate.
FULL_RECTANGLE = 0.9  # An outline filling this much of its box reads as a rectangle.
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
    title) or the next TYPE label above, or as tall as it is wide.
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
        above = [other for _, other in labels if other is not label]
        for cell in cells + above:
            wide = cell['xmax'] - cell['xmin'] > half or any(cell is other for other in above)
            if wide and cell['ymin'] >= bottom and cell['xmax'] > cx - half and cell['xmin'] < cx + half:
                top = min(top, cell['ymin'])
        regions[key] = (cx - half, bottom, cx + half, top)
    return regions


def _inside_region(point, region):
    return region[0] <= point[0] <= region[2] and region[1] <= point[1] <= region[3]


# -- Polygons ----------------------------------------------------------------------

def signed_area(points):
    total = 0.0
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        total += x1 * y2 - x2 * y1
    return total / 2.0


def polygon_area(points):
    return abs(signed_area(points))


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


# -- Planar outlines ---------------------------------------------------------------

def _segments(polylines):
    return [(a, b) for points in polylines for a, b in zip(points, points[1:])
            if abs(a[0] - b[0]) + abs(a[1] - b[1]) > 1e-12]


def _split_points(segments, tolerance):
    """Return, per segment, the parameters (0..1) where other segments cross or touch it."""
    boxes = [(min(a[0], b[0]) - tolerance, min(a[1], b[1]) - tolerance,
              max(a[0], b[0]) + tolerance, max(a[1], b[1]) + tolerance) for a, b in segments]
    splits = [[0.0, 1.0] for _ in segments]
    by_left = sorted(range(len(segments)), key=lambda index: boxes[index][0])
    for position, i in enumerate(by_left):
        a, b = segments[i]
        for j in by_left[position + 1:]:
            box_i, box_j = boxes[i], boxes[j]
            if box_j[0] > box_i[2]:
                break  # Sorted by left edge: no later segment reaches back to this one.
            if box_i[3] < box_j[1] or box_j[3] < box_i[1]:
                continue
            c, d = segments[j]
            rx, ry = b[0] - a[0], b[1] - a[1]
            sx, sy = d[0] - c[0], d[1] - c[1]
            denom = rx * sy - ry * sx
            len_r, len_s = math.hypot(rx, ry), math.hypot(sx, sy)
            if abs(denom) > 1e-12 * len_r * len_s:
                t = ((c[0] - a[0]) * sy - (c[1] - a[1]) * sx) / denom
                u = ((c[0] - a[0]) * ry - (c[1] - a[1]) * rx) / denom
                reach_t, reach_u = tolerance / len_r, tolerance / len_s
                if -reach_t <= t <= 1 + reach_t and -reach_u <= u <= 1 + reach_u:
                    splits[i].append(min(1.0, max(0.0, t)))
                    splits[j].append(min(1.0, max(0.0, u)))
            else:
                # Parallel: overlapping collinear lines split at each other's ends.
                for point, k, (p, q) in ((c, i, (a, b)), (d, i, (a, b)), (a, j, (c, d)), (b, j, (c, d))):
                    _collinear_split(point, p, q, splits[k], tolerance)
    return splits


def _collinear_split(point, start, end, splits, tolerance):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length_sq = dx * dx + dy * dy
    t = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / length_sq
    if 0.0 < t < 1.0:
        off = abs((point[0] - start[0]) * dy - (point[1] - start[1]) * dx) / math.sqrt(length_sq)
        if off <= tolerance:
            splits.append(t)


def planar_graph(polylines, tolerance):
    """Return (nodes, {node: set(neighbors)}) with lines split where they meet.

    Endpoints within tolerance join, and loose ends (leaders, centerline
    tails, dimension ticks) are trimmed away repeatedly.
    """
    segments = _segments(polylines)
    nodes, grid = [], {}

    def node(point):
        gx, gy = int(math.floor(point[0] / tolerance)), int(math.floor(point[1] / tolerance))
        for cx in (gx - 1, gx, gx + 1):
            for cy in (gy - 1, gy, gy + 1):
                for index in grid.get((cx, cy), ()):
                    other = nodes[index]
                    if abs(point[0] - other[0]) <= tolerance and abs(point[1] - other[1]) <= tolerance:
                        return index
        nodes.append(point)
        grid.setdefault((gx, gy), []).append(len(nodes) - 1)
        return len(nodes) - 1

    links = {}
    for (a, b), params in zip(segments, _split_points(segments, tolerance)):
        points = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for t in sorted(set(params))]
        ids = [node(point) for point in points]
        for i, j in zip(ids, ids[1:]):
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
    return nodes, links


def planar_faces(nodes, links):
    """Return (outer boundaries, bounded faces) of the trimmed drawing.

    Each connected group of lines has one outer boundary (its outline) and
    bounded faces (the areas its lines enclose). Polygons are vertex lists.
    """
    order = {}
    for index, neighbors in links.items():
        x, y = nodes[index]
        order[index] = sorted(neighbors, key=lambda other: math.atan2(nodes[other][1] - y,
                                                                      nodes[other][0] - x))
    used, outer, bounded = set(), [], []
    for start in links:
        for first in links[start]:
            if (start, first) in used:
                continue
            face, a, b = [], start, first
            while (a, b) not in used:
                used.add((a, b))
                face.append(a)
                around = order[b]
                # The next edge turns as far right as it can: it is just
                # clockwise from the edge we arrived on.
                c = around[(around.index(a) - 1) % len(around)]
                a, b = b, c
            polygon = [nodes[index] for index in face]
            if len(polygon) < 3:
                continue
            (outer if signed_area(polygon) < 0 else bounded).append(polygon)
    return outer, bounded


# -- Detail reading ----------------------------------------------------------------

def _orthogonal(points, tolerance):
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        if abs(x1 - x2) > tolerance and abs(y1 - y2) > tolerance:
            return False
    return True


def _circle_centers(arcs, region, tolerance):
    """Return (center, radius) of circles (arcs sharing a center adding to a full turn)."""
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


def _box_center(points):
    xmin, ymin, xmax, ymax = _bounds(points)
    return ((xmin + xmax) / 2.0, (ymin + ymax) / 2.0)


def find_loops(polylines, tolerance):
    """Return closed loops of whole lines joined end to end (no splitting).

    This finds a plate drawn as four or six lines even when a leader or
    centerline crossing it closes a small extra area onto its outline.
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
    loops, seen = [], set()
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
        loops.append([nodes[index] for index in order])
    return loops


def _classify(polygon, tolerance):
    """Return 'rect', 'L', or None for a simplified outline."""
    if len(polygon) in (4, 6) and _orthogonal(polygon, tolerance * 5):
        return 'rect' if len(polygon) == 4 else 'L'
    return None


def _nearly_rectangle(polygon, tolerance):
    """True when an outline fills its box and every slanted edge is short.

    Rounded corners or a column edge drawn over the plate pass; a chamfered
    or angled plate does not.
    """
    xmin, ymin, xmax, ymax = _bounds(polygon)
    short = 0.1 * min(xmax - xmin, ymax - ymin)
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        slanted = abs(x1 - x2) > tolerance * 5 and abs(y1 - y2) > tolerance * 5
        if slanted and math.hypot(x2 - x1, y2 - y1) > short:
            return False
    rectangle_area = polygon_area(_dominant_rectangle(polygon, tolerance))
    return rectangle_area > 0 and \
        abs(polygon_area(polygon) - rectangle_area) <= (1 - FULL_RECTANGLE) * rectangle_area


def _dominant_rectangle(polygon, tolerance):
    """Return the rectangle on the outline's longest edge runs.

    Each side is the edge line (bottom, top, left, right) with the most
    length, so a column poking past the plate edge does not widen it.
    """
    xmin, ymin, xmax, ymax = _bounds(polygon)
    runs = {'h': {}, 'v': {}}  # Edge line key -> [total length, coordinate].
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        if abs(y1 - y2) <= tolerance * 5:
            direction, coordinate, length = 'h', (y1 + y2) / 2.0, abs(x2 - x1)
        elif abs(x1 - x2) <= tolerance * 5:
            direction, coordinate, length = 'v', (x1 + x2) / 2.0, abs(y2 - y1)
        else:
            continue
        run = runs[direction].setdefault(round(coordinate / (tolerance * 5)), [0.0, coordinate])
        run[0] += length

    def side(direction, low, high, pick_low):
        middle = (low + high) / 2.0
        options = [run for run in runs[direction].values() if (run[1] < middle) == pick_low]
        return max(options)[1] if options else (low if pick_low else high)

    bottom, top = side('h', ymin, ymax, True), side('h', ymin, ymax, False)
    left, right = side('v', xmin, xmax, True), side('v', xmin, xmax, False)
    return [(left, bottom), (right, bottom), (right, top), (left, top)]


def _plate_outline(candidates, tolerance):
    """Return (corners, shape) for the plate, or (None, reason).

    The plate is the largest clean square, rectangle, or L among the
    candidate outlines, if it is at least half the size of the largest
    outline; otherwise the largest outline when it is nearly a rectangle.
    """
    candidates = [_simplify(list(polygon)) for polygon in candidates]
    candidates = [polygon for polygon in candidates if len(polygon) >= 3]
    if not candidates:
        return None, 'no closed plate outline was found above the label.'
    largest = max(candidates, key=polygon_area)
    clean = [(polygon, _classify(polygon, tolerance)) for polygon in candidates]
    clean = [(polygon, shape) for polygon, shape in clean
             if shape and polygon_area(polygon) >= 0.5 * polygon_area(largest)]
    if clean:
        return max(clean, key=lambda item: polygon_area(item[0]))
    if _nearly_rectangle(largest, tolerance):
        return _dominant_rectangle(largest, tolerance), 'rect'
    if len(largest) in (4, 6):
        return None, 'the plate outline is not square to the page.'
    return None, ('the plate outline has {} corners; only square, rectangular, and L-shaped '
                  'plates are supported.'.format(len(largest)))


def _frame(shape, plate, dims, tolerance):
    """Return (to_frame, sizes, horizontal_axis) for the drawn plate.

    to_frame maps a drawn point to (u, v) measured from the plate's start
    corner: along L and across W for a rectangle; along the two legs from
    the corner where they meet for an L. sizes gives each axis its drawn
    (L, W): for an L, the leg length on that axis and the other leg's width.
    horizontal_axis is 'u' or 'v'.
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
            sizes = {'u': (width_x, height_y), 'v': (width_x, height_y)}
            return (lambda p: (p[0] - xmin, p[1] - ymin)), sizes, 'u'
        sizes = {'u': (height_y, width_x), 'v': (height_y, width_x)}
        return (lambda p: (p[1] - ymin, p[0] - xmin)), sizes, 'v'
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
    # The u leg is inner v wide; the v leg is inner u wide.
    sizes = {'u': (width_x, inner[0][0]), 'v': (height_y, inner[0][1])}
    return to_frame, sizes, 'u'


def _dim_text(dim):
    return normalize_text(dim.get('text') or '').replace('"', '').replace("'", '').replace(' ', '')


def _rules(shape, axis, distances):
    """Return the position rules for one axis.

    Each rule is (name, (a, b, c), offsets): a position is L*a + W*b + C*c
    plus the sum of its offsets, for the plate's L and W on this axis and
    edge distance C. offsets are (sign, drawn feet, true inches) from the
    detail's dimensions, so drawn positions can be matched and true ones
    placed. For a rectangle, W is the plate width on the v axis.
    """
    if shape == 'rect':
        size = (1, 0) if axis == 'u' else (0, 1)
        bases = [('the start', (0, 0, 0), 1), ('the end', (size[0], size[1], 0), -1),
                 ('the middle', (size[0] / 2.0, size[1] / 2.0, 0), 0)]
    else:
        bases = [('the outside', (0, 0, 0), 1), ('the leg end', (1, 0, 0), -1),
                 ('the inside of the leg', (0, 1, 0), 0), ('the middle of the leg', (0, 0.5, 0), 0)]
    rules = []
    for name, coefficients, inward in bases:
        a, b, _ = coefficients
        signs = (inward,) if inward else (-1, 1)
        rules.append((name.capitalize(), coefficients, ()))
        if name != 'the middle' and name != 'the middle of the leg':
            for sign in signs:
                rules.append(('C from {}'.format(name), (a, b, sign), ()))
        for sign in signs:
            for distance in distances:
                rules.append(('{} from {}'.format(format_inches(distance[1]), name), (a, b, 0),
                              ((sign,) + distance,)))
            for first in distances:
                for second in distances:
                    if first <= second:
                        rules.append(('{} + {} from {}'.format(format_inches(first[1]),
                                                               format_inches(second[1]), name),
                                      (a, b, 0), ((sign,) + first, (sign,) + second)))
            if not inward:
                for distance in distances:  # A spacing centered here.
                    rules.append(('{} half of {} from {}'.format('+' if sign > 0 else '-',
                                                                format_inches(distance[1]), name),
                                  (a, b, 0), ((sign * 0.5,) + distance,)))
    return rules


def _drawn(rule, size, edge):
    a, b, c = rule[1]
    return a * size[0] + b * size[1] + c * edge + sum(sign * drawn for sign, drawn, _ in rule[2])


def _true(rule, length, width, edge):
    a, b, c = rule[1]
    return a * length + b * width + c * edge + sum(sign * true for sign, _, true in rule[2])


def _match(rules, size, edge, value, reach):
    """Return the rule nearest a drawn position, or None beyond reach.

    On a near tie the more specific rule wins: one using a dimension beats
    C or the middle, and a single dimension beats two chained.
    """
    def cost(rule):
        bonus = {0: 0.0, 1: 0.15, 2: 0.1}[len(rule[2])] * reach
        return abs(_drawn(rule, size, edge) - value) - bonus

    best = min(rules, key=cost)
    return best if abs(_drawn(best, size, edge) - value) <= reach else None


def read_type_details(cells, polylines, arcs, dims):
    """Return ({key: definition}, {key: problem}) for every TYPE label found.

    A definition is {'key', 'shape' ('square' | 'rectangular' | 'L'), 'rods'
    [(u rule, v rule)], 'column' (u rule, v rule)}; plate_geometry turns it
    into a plate.
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
            problems[key] = 'TYPE {}: {}'.format(key, problem)
        else:
            definitions[key] = definition
    return definitions, problems


def _read_detail(key, region, polylines, arcs, dims):
    tolerance = (region[2] - region[0]) * 0.002
    local = [points for points in polylines if all(_inside_region(p, region) for p in points)]
    nodes, links = planar_graph(local, tolerance)
    outlines, faces = planar_faces(nodes, links)
    plate, shape = _plate_outline(outlines + find_loops(local, tolerance), tolerance)
    if plate is None:
        return None, shape
    region_dims = [dim for dim in dims if _inside_region(dim['origin'], region)]
    frame = _frame(shape, plate, region_dims, tolerance)
    if frame is None:
        return None, 'the L-shaped outline could not be read.'
    to_frame, sizes, horizontal = frame
    if shape == 'L':
        name = 'L'
        smallest = min(sizes['u'][1], sizes['v'][1])
    else:
        length, width = sizes['u']
        name = 'square' if max(length, width) / min(length, width) <= SQUARE_RATIO else 'rectangular'
        smallest = min(length, width)

    rods = [center for center, radius in _circle_centers(arcs, region, tolerance * 5)
            if point_in_polygon(center, plate) and radius < 0.25 * smallest]
    if not rods:
        # Anchors drawn as small squares (washers or symbols) instead of circles.
        rods = [_box_center(face) for face in outlines + faces
                if face is not plate and _small_square(face, smallest)
                and point_in_polygon(_box_center(face), plate)]
        rods = _dedupe(rods, tolerance * 5)
    if not rods:
        return None, 'no anchor rods (circles or small squares) were found inside the plate.'
    column = _column_center(outlines, faces, plate, rods, smallest)
    rods = [to_frame(rod) for rod in rods]

    edge = [dim['value'] for dim in region_dims if _dim_text(dim) == 'C' and dim.get('value')]
    if edge:
        edge = sorted(edge)[len(edge) // 2]
    else:
        far_v = sizes['v'][0] if shape == 'L' else sizes['v'][1]
        edge = min(min(u, v, sizes['u'][0] - u, far_v - v) for u, v in rods)
    if edge <= 0:
        return None, 'the edge distance "C" could not be read.'

    # A measured dimension shows its own length; one typed over with a size
    # such as 2" shows that size. Either way it gives a true distance.
    distances = {'u': set(), 'v': set()}
    for dim in region_dims:
        if dim.get('equal') or not dim.get('value'):
            continue
        true = parse_inches(dim['text']) if _dim_text(dim) else dim['value'] * 12.0
        if true is None or true <= 0:
            continue
        along_x = abs(dim['direction'][0]) >= abs(dim['direction'][1])
        axis = horizontal if along_x else ('v' if horizontal == 'u' else 'u')
        distances[axis].add((round(dim['value'], 6), round(true, 4)))
    rules = {axis: _rules(shape, axis, sorted(distances[axis])) for axis in ('u', 'v')}
    size = {axis: sizes[axis] if shape == 'L' else sizes['u'] for axis in ('u', 'v')}
    reach = max(0.4 * edge, 0.03 * smallest)

    placed = []
    for u, v in rods:
        pair = tuple(_match(rules[axis], size[axis], edge, value, reach)
                     for axis, value in (('u', u), ('v', v)))
        if None in pair:
            return None, ('an anchor rod is not at "C", a dimensioned distance, or the middle '
                          'from an edge.')
        placed.append(pair)
    if len(set(placed)) != len(placed):
        return None, 'two anchor rods read as the same position.'

    if column is None:
        middle = [rule for rule in rules['u'] if rule[0] in ('The middle', 'The middle of the leg')][0]
        placed_column = (middle, [rule for rule in rules['v']
                                  if rule[0] in ('The middle', 'The middle of the leg')][0])
    else:
        column = to_frame(column)
        placed_column = tuple(_match(rules[axis], size[axis], edge, value, reach * 1.5)
                              for axis, value in (('u', column[0]), ('v', column[1])))
        if None in placed_column:
            return None, 'the column is not at the middle or a dimensioned distance from an edge.'
    return {'key': key, 'shape': name, 'rods': placed, 'column': placed_column}, None


def _small_square(face, smallest):
    xmin, ymin, xmax, ymax = _bounds(face)
    w, h = xmax - xmin, ymax - ymin
    return 0 < w < 0.2 * smallest and 0 < h < 0.2 * smallest and max(w, h) <= 1.5 * min(w, h)


def _dedupe(points, tolerance):
    kept = []
    for point in points:
        if not any(abs(point[0] - other[0]) <= tolerance and abs(point[1] - other[1]) <= tolerance
                   for other in kept):
            kept.append(point)
    return kept


def _column_center(outlines, faces, plate, rods, smallest):
    """Return the drawn column's center, or None.

    The column is the largest outline inside the plate that is not a rod's
    washer and is bigger than the anchor symbols. Only when the column's
    lines touch the plate's (so it has no outline of its own) are the
    enclosed faces tried, and then not ones as big as a plate quarter.
    """
    plate_area = polygon_area(plate)
    for shapes, limit in ((outlines, 0.6), (faces, 0.2)):
        candidates = [shape for shape in shapes
                      if polygon_area(shape) <= limit * plate_area and not _small_square(shape, smallest)
                      and not any(point_in_polygon(rod, shape) for rod in rods)
                      and point_in_polygon(_box_center(shape), plate)]
        if candidates:
            return _box_center(max(candidates, key=polygon_area))
    return None


# -- Plate geometry ----------------------------------------------------------------

def plate_geometry(definition, length, width, edge):
    """Return {'plate', 'rods', 'column'} in inches, in the definition's frame.

    A rectangle runs from (0, 0) to (L, W); an L has legs L long and W wide
    along +u and +v from (0, 0).
    """
    if definition['shape'] == 'L':
        plate = [(0, 0), (length, 0), (length, width), (width, width), (width, length), (0, length)]
    else:
        plate = [(0, 0), (length, 0), (length, width), (0, width)]
    rods = [(_true(rule_u, length, width, edge), _true(rule_v, length, width, edge))
            for rule_u, rule_v in definition['rods']]
    rule_u, rule_v = definition['column']
    column = (_true(rule_u, length, width, edge), _true(rule_v, length, width, edge))
    return {'plate': plate, 'rods': rods, 'column': column}


def describe(definition):
    """Return text such as 'square plate, 4 rods' for the palette."""
    text = '{} plate, {} rods'.format(SHAPE_NAMES[definition['shape']], len(definition['rods']))
    column = [rule[0] for rule in definition['column']]
    if any(not name.startswith('The middle') for name in column):
        text += ', column off center'
    return text
