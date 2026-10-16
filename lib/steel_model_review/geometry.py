"""Finite geometry operations on plain tuples, measured in inches."""

import math


def distance(a, b):
    """Return the Euclidean distance between equally sized coordinate tuples."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def projection(point, start, end):
    """Return nearest finite plan point and unclamped span fraction.

    Args:
        point: Query coordinate tuple.
        start: Segment start coordinate tuple.
        end: Segment end coordinate tuple.

    Returns:
        A pair containing the nearest XY point and unbounded span fraction.
    """
    dx, dy = end[0] - start[0], end[1] - start[1]
    length2 = dx * dx + dy * dy
    fraction = (sum((point[i] - start[i]) * (end[i] - start[i])
                    for i in (0, 1)) / length2) if length2 else 0.0
    bounded = max(0.0, min(1.0, fraction))
    return ((start[0] + bounded * dx, start[1] + bounded * dy), fraction)


def inside(point, polygon, epsilon):
    """Return whether an XY point lies in or on a finite polygon."""
    odd = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        nearest, _fraction = projection(point, a, b)
        if distance(point[:2], nearest) <= epsilon:
            return True
        if (a[1] > point[1]) != (b[1] > point[1]):
            cross_x = a[0] + ((point[1] - a[1]) * (b[0] - a[0]) /
                              (b[1] - a[1]))
            if point[0] < cross_x:
                odd = not odd
    return odd


def section_interval(member, point, epsilon):
    """Return reliable original-solid bottom and top at a plan station.

    Args:
        member: Normalized record containing planar face equations and loops.
        point: Plan station in the record's world coordinate system.
        epsilon: Plan containment tolerance in inches.

    Returns:
        Bottom/top tuple, or None when both solid boundaries are not resolved.
    """
    tops, bottoms = [], []
    for face in member.get('faces', []):
        normal, origin, loops = face
        if abs(normal[2]) < 1e-9:
            continue
        # Count loops by parity so holes do not masquerade as steel surfaces.
        if sum(1 for loop in loops if inside(point, loop, epsilon)) % 2 != 1:
            continue
        z = origin[2] - sum(normal[i] * (point[i] - origin[i])
                            for i in (0, 1)) / normal[2]
        (tops if normal[2] > 0 else bottoms).append(z)
    if not tops or not bottoms:
        return None
    return min(bottoms), max(tops)


def intersection(a, b):
    """Return the intersection of nonparallel infinite grid lines, or None."""
    p, q = a['start'], b['start']
    r = tuple(a['end'][i] - p[i] for i in (0, 1))
    s = tuple(b['end'][i] - q[i] for i in (0, 1))
    det = r[0] * s[1] - r[1] * s[0]
    lengths = distance(r, (0, 0)) * distance(s, (0, 0))
    if not lengths or abs(det) / lengths < 1e-4:
        return None
    t = ((q[0] - p[0]) * s[1] - (q[1] - p[1]) * s[0]) / det
    return p[0] + t * r[0], p[1] + t * r[1]


def line_distance(point, line):
    """Return perpendicular plan distance to an infinite grid datum line."""
    start, end = line['start'], line['end']
    length = distance(start[:2], end[:2])
    if not length:
        return float('inf')
    return abs((end[0] - start[0]) * (start[1] - point[1]) -
               (start[0] - point[0]) * (end[1] - start[1])) / length


class SpatialIndex(object):
    """Index finite plan envelopes without exploding large diagonal envelopes.

    Args:
        records: Normalized records with unique IDs and finite bounds.
        cell: Spatial hash cell width in inches.
    """

    def __init__(self, records, cell=120.0):
        self.cell = cell
        self.cells = {}
        self.large = []
        self.records = dict((r['uid'], r) for r in records)
        for record in records:
            bounds = record['bounds']
            low, high = self._cell(bounds[0]), self._cell(bounds[1])
            count = (high[0] - low[0] + 1) * (high[1] - low[1] + 1)
            if count > 4096:
                self.large.append(record['uid'])
                continue
            for x in range(low[0], high[0] + 1):
                for y in range(low[1], high[1] + 1):
                    self.cells.setdefault((x, y), []).append(record['uid'])

    def _cell(self, point):
        return tuple(int(math.floor(point[i] / self.cell)) for i in (0, 1))

    def query(self, point, radius):
        """Yield each nearby plan-envelope record once, in stable order."""
        low = self._cell((point[0] - radius, point[1] - radius))
        high = self._cell((point[0] + radius, point[1] + radius))
        keys = set(self.large)
        # An extreme user search range must not enumerate millions of cells.
        if (high[0] - low[0] + 1) * (high[1] - low[1] + 1) > 4096:
            keys.update(self.records)
        else:
            for x in range(low[0], high[0] + 1):
                for y in range(low[1], high[1] + 1):
                    keys.update(self.cells.get((x, y), []))
        for key in sorted(keys):
            record = self.records[key]
            lo, hi = record['bounds']
            if all(lo[i] - radius <= point[i] <= hi[i] + radius
                   for i in (0, 1)):
                yield record
