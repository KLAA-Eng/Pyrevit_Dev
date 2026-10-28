"""Find the hexagon outline in a hanger's plan linework.

Segments are plan line pieces ((x1, y1), (x2, y2)) in feet. A hexagon is a
closed loop of HEXAGON_SIDES segments whose side lengths agree within
SIDE_TOLERANCE of their mean. Tracing it lets the check highlight the hexagon
with heavy colored lines while the hanger text keeps its own color.
"""

from __future__ import division

import math


HEXAGON_SIDES = 6
POINT_TOL_FT = 1.0 / 384.0          # 1/32"
SIDE_TOLERANCE = 0.25
FLAT_SIDE_DEG = 10.0


def _length(segment):
    (x1, y1), (x2, y2) = segment
    return math.hypot(x2 - x1, y2 - y1)


def _node(nodes, point, tol):
    for index, other in enumerate(nodes):
        if math.hypot(point[0] - other[0], point[1] - other[1]) <= tol:
            return index
    nodes.append(point)
    return len(nodes) - 1


def find_loops(segments, sides=HEXAGON_SIDES, tol=POINT_TOL_FT):
    """Closed loops of exactly `sides` segments, each as a list of plan points."""
    nodes, edges = [], {}
    for segment in segments:
        if _length(segment) <= tol:
            continue
        a, b = _node(nodes, segment[0], tol), _node(nodes, segment[1], tol)
        if a != b:
            edges.setdefault(a, set()).add(b)
            edges.setdefault(b, set()).add(a)
    loops, seen = [], set()

    def walk(path):
        if len(path) == sides:
            if path[0] in edges[path[-1]]:
                key = frozenset(path)
                if key not in seen:
                    seen.add(key)
                    loops.append([nodes[i] for i in path])
            return
        for nxt in edges[path[-1]]:
            if nxt not in path and nxt > path[0]:
                walk(path + [nxt])

    for start in sorted(edges):
        walk([start])
    return loops


def _regular(loop):
    sides = [_length((loop[i], loop[(i + 1) % len(loop)])) for i in range(len(loop))]
    mean = sum(sides) / len(sides)
    return mean > 0 and all(abs(side - mean) <= SIDE_TOLERANCE * mean for side in sides)


def find_hexagons(segments, tol=POINT_TOL_FT):
    """Regular-ish hexagon loops (lists of 6 plan points) in the segments."""
    return [loop for loop in find_loops(segments, HEXAGON_SIDES, tol) if _regular(loop)]


def loop_segments(loop):
    """Closed loop points -> list of plan segments."""
    return [(loop[i], loop[(i + 1) % len(loop)]) for i in range(len(loop))]


def flat_side_offsets(loop, text_dir, origin):
    """[bottom, top]: across-text offsets (feet, from origin) of the two hexagon
    sides that run along the hanger text, or None when the hexagon has no such
    pair (for example a point-up hexagon)."""
    length = math.hypot(text_dir[0], text_dir[1])
    if length < 1e-9:
        return None
    tx, ty = text_dir[0] / length, text_dir[1] / length
    min_dot = math.cos(math.radians(FLAT_SIDE_DEG))
    offsets = []
    for a, b in loop_segments(loop):
        side = _length((a, b))
        if side <= 0 or abs((b[0] - a[0]) * tx + (b[1] - a[1]) * ty) / side < min_dot:
            continue
        mid_x, mid_y = (a[0] + b[0]) / 2 - origin[0], (a[1] + b[1]) / 2 - origin[1]
        offsets.append(-mid_x * ty + mid_y * tx)
    return sorted(offsets) if len(offsets) == 2 else None
