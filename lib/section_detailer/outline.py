"""Outline of a linked model's cut faces on a section.

Each cut element is a region: a list of closed loops of ``(u, v)`` points in
view-plane feet. The outline is the boundary of their union, so edges where
two elements meet, and edges inside another element, are left out.
"""


OUTLINE_STYLE = 'S-OBJ4'
OUTLINE_TOLERANCE = 1.0 / 256


def _box(points):
    us = [point[0] for point in points]
    vs = [point[1] for point in points]
    return min(us), min(vs), max(us), max(vs)


def _boxes_touch(first, second, tolerance):
    return (first[0] <= second[2] + tolerance and second[0] <= first[2] + tolerance and
            first[1] <= second[3] + tolerance and second[1] <= first[3] + tolerance)


def point_in_region(point, loops):
    """Return True when ``point`` is inside a region (even-odd over its loops)."""
    inside = False
    u, v = point
    for loop in loops:
        count = len(loop)
        for index in range(count):
            (u1, v1), (u2, v2) = loop[index], loop[(index + 1) % count]
            if (v1 > v) != (v2 > v):
                if u < u1 + (v - v1) * (u2 - u1) / (v2 - v1):
                    inside = not inside
    return inside


def _edges(regions):
    edges = []
    for owner, loops in enumerate(regions):
        for loop in loops:
            count = len(loop)
            for index in range(count):
                start, end = loop[index], loop[(index + 1) % count]
                if start != end:
                    edges.append((owner, start, end, _box((start, end))))
    return edges


def _covered(edge, others, tolerance):
    """Return parameter intervals of ``edge`` lying on collinear ``others``."""
    _, start, end, box = edge
    du, dv = end[0] - start[0], end[1] - start[1]
    length_sq = du * du + dv * dv
    length = length_sq ** 0.5
    intervals = []
    for _, other_start, other_end, other_box in others:
        if not _boxes_touch(box, other_box, tolerance):
            continue
        offsets = []
        for point in (other_start, other_end):
            pu, pv = point[0] - start[0], point[1] - start[1]
            if abs(du * pv - dv * pu) / length > tolerance:
                break
            offsets.append((du * pu + dv * pv) / length_sq)
        else:
            low, high = max(min(offsets), 0.0), min(max(offsets), 1.0)
            if high > low:
                intervals.append((low, high))
    return intervals


def _remaining(intervals, minimum):
    pieces = []
    position = 0.0
    for low, high in sorted(intervals):
        if low - position > minimum:
            pieces.append((position, low))
        position = max(position, high)
    if 1.0 - position > minimum:
        pieces.append((position, 1.0))
    return pieces


def boundary_segments(regions, tolerance=OUTLINE_TOLERANCE):
    """Return ``(start, end)`` segments on the outer boundary of the regions.

    An edge loses the stretches it shares with another region's edge (two
    elements meeting) and the stretches inside another region (overlaps).
    """
    edges = _edges(regions)
    region_boxes = [_box([point for loop in loops for point in loop]) if loops else None
                    for loops in regions]
    segments = []
    for edge in edges:
        owner, start, end, box = edge
        others = [other for other in edges if other[0] != owner]
        length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
        pieces = _remaining(_covered(edge, others, tolerance), tolerance / length)
        for low, high in pieces:
            a = (start[0] + (end[0] - start[0]) * low, start[1] + (end[1] - start[1]) * low)
            b = (start[0] + (end[0] - start[0]) * high, start[1] + (end[1] - start[1]) * high)
            middle = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
            hidden = any(
                index != owner and region_boxes[index] and
                _boxes_touch(region_boxes[index], (middle[0], middle[1]) * 2, 0.0) and
                point_in_region(middle, regions[index])
                for index in range(len(regions)))
            if not hidden:
                segments.append((a, b))
    return segments


def join_collinear(segments, tolerance=OUTLINE_TOLERANCE, angle=1e-4):
    """Join segments that continue one another in a straight line.

    Two segments join at a point only when no other segment ends there, so
    corners and T-junctions stay separate. ``angle`` is the largest sine
    between joined directions; tessellated arcs keep their facets.
    """
    def key(point):
        return int(round(point[0] / tolerance)), int(round(point[1] / tolerance))

    remaining = list(segments)
    changed = True
    while changed:
        changed = False
        ends = {}
        for index, (start, end) in enumerate(remaining):
            ends.setdefault(key(start), []).append(index)
            ends.setdefault(key(end), []).append(index)
        used = set()
        merged = []
        for point, indexes in ends.items():
            if len(indexes) != 2 or indexes[0] == indexes[1] or used.intersection(indexes):
                continue
            first, second = remaining[indexes[0]], remaining[indexes[1]]
            if key(first[0]) == point:
                first = (first[1], first[0])
            if key(second[1]) == point:
                second = (second[1], second[0])
            du1, dv1 = first[1][0] - first[0][0], first[1][1] - first[0][1]
            du2, dv2 = second[1][0] - second[0][0], second[1][1] - second[0][1]
            lengths = ((du1 * du1 + dv1 * dv1) * (du2 * du2 + dv2 * dv2)) ** 0.5
            if not lengths or du1 * du2 + dv1 * dv2 <= 0 or \
                    abs(du1 * dv2 - dv1 * du2) / lengths > angle:
                continue
            used.update(indexes)
            merged.append((first[0], second[1]))
            changed = True
        remaining = [segment for index, segment in enumerate(remaining)
                     if index not in used] + merged
    return remaining
