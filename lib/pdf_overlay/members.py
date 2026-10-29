# -*- coding: utf-8 -*-
"""Host-independent member size checking against PDF size labels.

PDF labels (for example ``W12x26`` beside a beam on a RAM member map) are
placed in the view through the overlay pose, then each label is assigned to
the nearest roughly parallel member line. A member whose Revit size differs
from its label is a mismatch for review. Stud counts and camber printed after
a size (``W16x26 (14) c=3/4"``) are read and compared too, and
``revision_plan`` lists what to change to make a member match its label.
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
STUDS_DIFFER = 'studs'
CAMBER_DIFFER = 'camber'
CONFLICT = 'conflict'
UNREADABLE = 'unreadable'
# Statuses a revision can resolve.
REVISABLE = (MISMATCH, STUDS_DIFFER, CAMBER_DIFFER)

# Studs follow a size as (14), [14], or split runs (6,8) that add up; camber
# as c=3/4", c=1", c=1 1/4", c=1-1/4", or c=.75. (HIGH) and 51K are ignored.
STUDS_PATTERN = re.compile(r'[\(\[]\s*(\d{1,3}(?:\s*[,+]\s*\d{1,3})*)\s*[\)\]]')
CAMBER_PATTERN = re.compile(
    r'(?<![A-Za-z])c\s*=\s*(\d+[\s-]+\d+/\d+|\d+/\d+|\d*\.\d+|\d+)\s*(?:"|\'\'|in\b)?',
    re.IGNORECASE)
CAMBER_TOLERANCE_INCHES = 1.0 / 32.0
# Following words on the label's baseline that can carry studs or camber.
TAIL_WORDS = 3
TAIL_GAP_RATIO = 1.5


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


def parse_inches(text):
    """Return inches from 3/4, 1, 1 1/4, 1-1/4, or .75 (quote marks ignored), else None."""
    if text is None:
        return None
    text = text.strip().strip('"').strip("'").strip()
    match = re.match(r'^(\d+)[\s-]+(\d+)/(\d+)$', text)
    if match:
        return int(match.group(1)) + float(match.group(2)) / float(match.group(3))
    match = re.match(r'^(\d+)/(\d+)$', text)
    if match:
        return float(match.group(1)) / float(match.group(2))
    try:
        return float(text)
    except ValueError:
        return None


def format_inches(inches):
    """Format inches to the nearest 1/16 as 3/4", 1", or 1 1/4"."""
    sixteenths = int(round(inches * 16))
    whole, remainder = divmod(sixteenths, 16)
    if remainder == 0:
        return '{}"'.format(whole)
    numerator, denominator = remainder, 16
    while numerator % 2 == 0:
        numerator //= 2
        denominator //= 2
    fraction = '{}/{}'.format(numerator, denominator)
    return '{} {}"'.format(whole, fraction) if whole else fraction + '"'


def parse_extras(text):
    """Return {'studs': int or None, 'camber': inches or None} from label tail text."""
    studs = None
    match = STUDS_PATTERN.search(text or '')
    if match:
        studs = sum(int(part) for part in re.split(r'\s*[,+]\s*', match.group(1)))
    camber = None
    match = CAMBER_PATTERN.search(text or '')
    if match:
        camber = parse_inches(match.group(1))
    return {'studs': studs, 'camber': camber}


def describe_member(size, studs=None, camber=None):
    """Return size text with studs and camber, as a plan would print it."""
    text = size
    if studs:
        text += ' ({})'.format(studs)
    if camber:
        text += ' c=' + format_inches(camber)
    return text


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


def _following_text(word, words):
    """Return the text of up to TAIL_WORDS words that continue word's baseline."""
    ux, uy, size = word.ux, word.uy, word.size

    def along(other):
        return other.x * ux + other.y * uy

    def across(other):
        return -other.x * uy + other.y * ux

    base = across(word)
    nearby = sorted((other for other in words
                     if other is not word and other.ux * ux + other.uy * uy > 0.999
                     and abs(across(other) - base) < 0.5 * size),
                    key=along)
    cursor = along(word) + word.length
    parts = []
    for other in nearby:
        start = along(other)
        if start < cursor - 0.5 * size:
            continue
        if start - cursor > TAIL_GAP_RATIO * size or SIZE_PATTERN.search(other.text):
            break
        parts.append(other.text)
        cursor = start + other.length
        if len(parts) >= TAIL_WORDS:
            break
    return ' '.join(parts)


def size_labels(page_text, pose, page_size):
    """Return every steel size label on the page, placed in view feet.

    Each label carries the studs and camber printed after it, up to the next
    size, within its own word or the next few words on its baseline.
    """
    labels = []
    for word in page_text.words:
        spans = list(find_size_spans(word.text))
        for index, (start, end, key, display) in enumerate(spans):
            if index + 1 < len(spans):
                tail = word.text[end:spans[index + 1][0]]
            else:
                tail = word.text[end:] + ' ' + _following_text(word, page_text.words)
            extras = parse_extras(tail)
            piece = word.span(start, end)
            center, direction, height = label_in_view(piece, page_text, pose, page_size)
            labels.append({
                'text': display,
                'key': key,
                'studs': extras['studs'],
                'camber': extras['camber'],
                'display': describe_member(display, extras['studs'], extras['camber']),
                'center': center,
                'direction': direction,
                'height': height,
            })
    return labels


# -- Matching labels to members ----------------------------------------------------

def label_mark(label, radius):
    """Return the review mark for a label: a circle of radius (the match
    window) at the label and a diameter along the label's direction."""
    cx, cy = label['center']
    dx, dy = label['direction']
    return {
        'center': (cx, cy),
        'radius': radius,
        'line': ((cx - dx * radius, cy - dy * radius), (cx + dx * radius, cy + dy * radius)),
    }


def sort_labels(labels):
    """Order labels by size text, then left to right and top to bottom."""
    return sorted(labels, key=lambda label: (label['text'], round(label['center'][0], 1),
                                             -round(label['center'][1], 1)))


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
    key (parse_size key or None), start, end (view feet), and optional studs
    and camber (inches). A label goes to the nearest member within
    tolerance_feet whose line is within max_angle degrees of the label.
    Returns a dict with:

    - rows: one per labelled member with status match, mismatch, studs or
      camber (size matches but the PDF's studs or camber differ), conflict
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
        found = [label for label, _ in assigned[index]]
        variants = set((label['key'], label.get('studs'), label.get('camber')) for label in found)
        label = found[0]
        if len(variants) > 1:
            status = CONFLICT
        elif member['key'] is None:
            status = UNREADABLE
        elif member['key'] != label['key']:
            status = MISMATCH
        elif label.get('studs') is not None and member.get('studs') != label['studs']:
            status = STUDS_DIFFER
        elif label.get('camber') is not None and not same_camber(member.get('camber'), label['camber']):
            status = CAMBER_DIFFER
        else:
            status = MATCH
        rows.append({
            'id': member['id'],
            'revit': describe_member(member['size'], member.get('studs'), member.get('camber')),
            'pdf': ', '.join(sorted(set(item.get('display', item['text']) for item in found))),
            'label': label if status != CONFLICT else None,
            'status': status,
            'distance': min(distance for _, distance in assigned[index]),
        })
    unlabelled = [member for index, member in enumerate(members) if index not in assigned]
    return {'rows': rows, 'unmatched_labels': unmatched, 'unlabelled': unlabelled}


def same_camber(revit_inches, pdf_inches):
    """Compare cambers to 1/32 inch; no camber in Revit counts as zero."""
    return abs((revit_inches or 0.0) - (pdf_inches or 0.0)) <= CAMBER_TOLERANCE_INCHES


# -- Revising members to the PDF ------------------------------------------------------

def revision_plan(row, member):
    """Return the changes that make member match its PDF label.

    Returns {'size': (key, display) or None, 'studs': int or None,
    'camber': inches or None, 'skip': reason or None}. Studs and camber are
    set only where the PDF prints them; a size alone leaves them unchanged.
    """
    plan = {'size': None, 'studs': None, 'camber': None, 'skip': None}
    if row is None:
        plan['skip'] = 'No PDF label is matched to this member.'
        return plan
    label = row.get('label')
    if row['status'] == CONFLICT or label is None:
        plan['skip'] = 'Its PDF labels disagree ({}).'.format(row['pdf'])
        return plan
    if member.get('key') != label['key']:
        plan['size'] = (label['key'], label['text'])
    if label.get('studs') is not None and member.get('studs') != label['studs']:
        plan['studs'] = label['studs']
    if label.get('camber') is not None and not same_camber(member.get('camber'), label['camber']):
        plan['camber'] = label['camber']
    if plan['size'] is None and plan['studs'] is None and plan['camber'] is None:
        plan['skip'] = 'Already matches the PDF.'
    return plan


def choose_type(candidates, key, family_name):
    """Pick the loaded type for a size: same family first, then any family.

    candidates: (family name, size key, type) tuples. Returns the type or None.
    """
    matching = [candidate for candidate in candidates if candidate[1] == key]
    for candidate in matching:
        if candidate[0] == family_name:
            return candidate[2]
    return matching[0][2] if matching else None
