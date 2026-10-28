# -*- coding: utf-8 -*-
"""Host-independent member size checking against PDF size labels.

PDF labels (for example ``W12x26`` beside a beam on a RAM member map) are
placed in the view through the overlay pose, then each label is assigned to
the nearest roughly parallel member line. A member whose Revit size differs
from its label is a mismatch for review.
"""

import math
import re

from .geometry import pixel_to_view


# Steel shapes as drawn on plans and RAM maps: W12x26, HSS6x4x1/4, L4x4x3/8,
# C10x15.3, HSS6.625x0.280. A leading mark such as * is ignored.
SIZE_PATTERN = re.compile(
    r'(?<![A-Za-z])(HSS|HP|MC|WT|MT|ST|2L|W|M|S|C|L)\s?'
    r'(\d+(?:\.\d+)?(?:-\d+/\d+|/\d+)?(?:\s?[xX]\s?\d*\.?\d+(?:-\d+/\d+|/\d+)?)+)',
    re.IGNORECASE)
_DIMENSION = re.compile(r'(\d*\.?\d+)(?:-(\d+)/(\d+)|/(\d+))?')

# A label within this distance of a member line and this angle of its
# direction can belong to it. Users can change both per overlay.
DEFAULT_TOLERANCE_FEET = 2.5
DEFAULT_TOLERANCE_DEGREES = 15.0

MATCH = 'match'
MISMATCH = 'mismatch'
CONFLICT = 'conflict'
UNREADABLE = 'unreadable'


def _dimension_value(text):
    match = _DIMENSION.match(text)
    if not match:
        return None
    whole, num, den, over = match.groups()
    value = float(whole)
    if num and den:
        value += float(num) / float(den)
    elif over:
        value /= float(over)
    return value


def parse_size(text):
    """Return (key, display) for the first steel size in text, or None.

    The key compares numerically, so HSS5x5x3/8 equals HSS5X5X.375 and
    W12x26 equals w12X26.
    """
    if not text:
        return None
    match = SIZE_PATTERN.search(text)
    if not match:
        return None
    return _size_from_match(match)


def _size_from_match(match):
    prefix = match.group(1).upper()
    parts = re.split(r'\s?[xX]\s?', match.group(2))
    values = [_dimension_value(part) for part in parts]
    if None in values:
        return None
    key = (prefix,) + tuple(round(value, 3) for value in values)
    display = prefix + 'X'.join(part.strip() for part in parts)
    return key, display


def find_size_spans(text):
    """Yield (start, end, key, display) for every steel size in text."""
    for match in SIZE_PATTERN.finditer(text or ''):
        size = _size_from_match(match)
        if size:
            yield match.start(), match.end(), size[0], size[1]


# -- Placing PDF labels in the view ------------------------------------------------

def label_in_view(word, page_text, pose, page_size):
    """Return (center, direction, height) of a PDF word in view feet.

    The page point goes to the displayed page (0-1), then to raster pixels,
    then through the overlay pose, so /Rotate, crop, DPI, scale, and the
    alignment rotation are all applied.
    """
    def to_view(x, y):
        u, v = page_text.page_to_unit(x, y)
        return pixel_to_view(pose, page_size, (u * page_size[0], v * page_size[1]))

    cx, cy = word.center()
    center = to_view(cx, cy)
    ahead = to_view(cx + word.ux * word.size, cy + word.uy * word.size)
    up = to_view(cx - word.uy * word.size, cy + word.ux * word.size)
    dx, dy = ahead[0] - center[0], ahead[1] - center[1]
    length = math.hypot(dx, dy) or 1.0
    height = math.hypot(up[0] - center[0], up[1] - center[1])
    return center, (dx / length, dy / length), height


def size_labels(page_text, pose, page_size):
    """Return every steel size label on the page, placed in view feet."""
    labels = []
    for word in page_text.words:
        for start, end, key, display in find_size_spans(word.text):
            piece = word.span(start, end)
            center, direction, height = label_in_view(piece, page_text, pose, page_size)
            labels.append({
                'text': display,
                'key': key,
                'center': center,
                'direction': direction,
                'height': height,
            })
    return labels


# -- Matching labels to members ----------------------------------------------------

def _segment_distance(point, start, end):
    sx, sy = start
    dx, dy = end[0] - sx, end[1] - sy
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(point[0] - sx, point[1] - sy)
    t = max(0.0, min(1.0, ((point[0] - sx) * dx + (point[1] - sy) * dy) / length_sq))
    return math.hypot(point[0] - (sx + t * dx), point[1] - (sy + t * dy))


def _line_angle(direction_a, direction_b):
    """Return the acute angle in degrees between two undirected lines."""
    dot = abs(direction_a[0] * direction_b[0] + direction_a[1] * direction_b[1])
    return math.degrees(math.acos(max(-1.0, min(1.0, dot))))


def _direction(start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy) or 1.0
    return (dx / length, dy / length)


def match_members(labels, members, tolerance_feet=DEFAULT_TOLERANCE_FEET,
                  max_angle=DEFAULT_TOLERANCE_DEGREES):
    """Assign labels to members and classify each labelled member.

    labels: dicts from size_labels. members: dicts with id, size (Revit text),
    key (parse_size key or None), start, end (view feet). A label goes to the
    nearest member within tolerance_feet whose line is within max_angle
    degrees of the label. Returns a dict with:

    - rows: one per labelled member with status match, mismatch, conflict
      (its labels disagree), or unreadable (Revit size not recognized)
    - unmatched_labels: labels with no member nearby
    - unlabelled: members with no label
    """
    directions = [_direction(member['start'], member['end']) for member in members]
    assigned = {}
    unmatched = []
    for label in labels:
        best, best_distance = None, None
        for index, member in enumerate(members):
            if _line_angle(label['direction'], directions[index]) > max_angle:
                continue
            distance = _segment_distance(label['center'], member['start'], member['end'])
            if distance <= tolerance_feet and (best_distance is None or distance < best_distance):
                best, best_distance = index, distance
        if best is None:
            unmatched.append(label)
        else:
            assigned.setdefault(best, []).append((label, best_distance))

    rows = []
    for index in sorted(assigned, key=lambda item: str(members[item]['id'])):
        member = members[index]
        found = assigned[index]
        keys = sorted(set(label['key'] for label, _ in found))
        pdf_text = ', '.join(sorted(set(label['text'] for label, _ in found)))
        if len(keys) > 1:
            status = CONFLICT
        elif member['key'] is None:
            status = UNREADABLE
        elif member['key'] == keys[0]:
            status = MATCH
        else:
            status = MISMATCH
        rows.append({
            'id': member['id'],
            'revit': member['size'],
            'pdf': pdf_text,
            'status': status,
            'distance': min(distance for _, distance in found),
        })
    unlabelled = [member for index, member in enumerate(members) if index not in assigned]
    return {'rows': rows, 'unmatched_labels': unmatched, 'unlabelled': unlabelled}
