"""Plan geometry of section markers and the SIM / OH notes written beside them.

Points are (x, y) plan tuples in feet. A marker's cut line is its longest
drawn line plus the lines collinear with it; the head and tail symbols drawn
off the line show which way the section looks.
"""

from __future__ import division

import math
import re


LINE_TOLERANCE_FT = 0.05
SIM_PATTERN = re.compile(r'(?<![A-Z0-9])SIM(?:ILAR)?(?![A-Z0-9])')
OH_PATTERN = re.compile(r'(?<![A-Z0-9])(?:O\.?\s?H\.?|OPP(?:OSITE)?\.?(?:\s+HAND)?)(?![A-Z0-9])')


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _length(a):
    return math.hypot(a[0], a[1])


def unit(vector):
    length = _length(vector)
    return (vector[0] / length, vector[1] / length) if length > 1e-9 else None


def right_of(look):
    """Plan direction to the viewer's right when looking along look."""
    return (look[1], -look[0])


def note_flags(text):
    """{'sim': bool, 'oh': bool} for one note's text."""
    upper = (text or '').upper()
    return {'sim': bool(SIM_PATTERN.search(upper)), 'oh': bool(OH_PATTERN.search(upper))}


def cut_line(segments, points=()):
    """{'start', 'end', 'look'} from a marker's drawn segments [(a, b), ...] and
    other symbol points, else None. look is the unit plan direction the section
    looks toward (the side its head and tail symbols are drawn on), or None
    when the symbols are balanced on both sides of the line."""
    segments = [s for s in segments if _length(_sub(s[1], s[0])) > LINE_TOLERANCE_FT]
    if not segments:
        return None
    longest = max(segments, key=lambda s: _length(_sub(s[1], s[0])))
    origin, direction = longest[0], unit(_sub(longest[1], longest[0]))
    along, off = [], list(points)
    for a, b in segments:
        offsets = [_cross(direction, _sub(p, origin)) for p in (a, b)]
        if all(abs(o) <= LINE_TOLERANCE_FT for o in offsets):
            along.extend(_dot(direction, _sub(p, origin)) for p in (a, b))
        else:
            off.extend((a, b))
    sides = [_cross(direction, _sub(p, origin)) for p in off]
    sides = [o for o in sides if abs(o) > LINE_TOLERANCE_FT]
    lean = sum(sides) / len(sides) if sides else 0.0
    normal = (-direction[1], direction[0])
    look = None
    if abs(lean) > LINE_TOLERANCE_FT:
        look = normal if lean > 0 else (-normal[0], -normal[1])
    point = lambda t: (origin[0] + direction[0] * t, origin[1] + direction[1] * t)
    return {'start': point(min(along)), 'end': point(max(along)), 'look': look}


def closest_on_segment(point, a, b):
    ab = _sub(b, a)
    length2 = _dot(ab, ab)
    t = 0.0 if length2 < 1e-12 else max(0.0, min(1.0, _dot(_sub(point, a), ab) / length2))
    return (a[0] + ab[0] * t, a[1] + ab[1] * t)


def _point_segment(point, a, b):
    return _length(_sub(point, closest_on_segment(point, a, b)))


def _point_box(point, low, high):
    dx = max(low[0] - point[0], 0.0, point[0] - high[0])
    dy = max(low[1] - point[1], 0.0, point[1] - high[1])
    return math.hypot(dx, dy)


def _segments_cross(a, b, c, d):
    d1, d2 = _cross(_sub(b, a), _sub(c, a)), _cross(_sub(b, a), _sub(d, a))
    d3, d4 = _cross(_sub(d, c), _sub(a, c)), _cross(_sub(d, c), _sub(b, c))
    if d1 == d2 == d3 == d4 == 0:
        # Collinear: they cross only where they overlap.
        return any(_point_segment(p, c, d) == 0 for p in (a, b)) or \
            any(_point_segment(p, a, b) == 0 for p in (c, d))
    return d1 * d2 <= 0 and d3 * d4 <= 0


def box_segment_distance(low, high, a, b):
    """Plan distance from a box (min/max corners) to a segment; 0 when they touch."""
    corners = [low, (high[0], low[1]), high, (low[0], high[1])]
    edges = list(zip(corners, corners[1:] + corners[:1]))
    if _point_box(a, low, high) == 0.0 or any(_segments_cross(a, b, c, d) for c, d in edges):
        return 0.0
    return min([_point_segment(c, a, b) for c in corners]
               + [_point_box(p, low, high) for p in (a, b)])


def assign_notes(markers, notes, reach):
    """{marker id: {'sim', 'oh', 'texts'}} from notes [(text, low, high), ...]
    and markers {id: (start, end)}. Each SIM / OH note belongs to its nearest
    marker within reach (feet), so one note never marks two sections."""
    result = dict((key, {'sim': False, 'oh': False, 'texts': []}) for key in markers)
    for text, low, high in notes:
        flags = note_flags(text)
        if not (flags['sim'] or flags['oh']):
            continue
        distances = [(box_segment_distance(low, high, a, b), key)
                     for key, (a, b) in markers.items()]
        distances = [d for d in distances if d[0] <= reach]
        if not distances:
            continue
        entry = result[min(distances, key=lambda d: (d[0], str(d[1])))[1]]
        entry['sim'] = entry['sim'] or flags['sim']
        entry['oh'] = entry['oh'] or flags['oh']
        entry['texts'].append(' '.join((text or '').split()))
    return result
