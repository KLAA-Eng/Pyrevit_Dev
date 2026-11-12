# -*- coding: utf-8 -*-
"""Grade from the elevation labels of a PDF grading plan.

Spot elevations (``FG 94.25``, ``BW=93.50``, ``94.25``) and contour labels
(``95``) are read from a page's positioned words, placed in the aligned
overlay's view coordinates, projected onto a wall's exterior face, and
interpolated along the wall.

Lengths and elevations are in feet. Elevations stay in the PDF's datum until
``to_internal`` converts them with the chosen Revit base point.
"""

import math
import re

try:
    from pdf_overlay.members import label_in_view
except ImportError:  # Tests import the library as the lib package.
    from lib.pdf_overlay.members import label_in_view


# Prefixes whose number is finished grade at that spot.
GRADE_PREFIXES = frozenset([
    'FG', 'FS', 'BW', 'BOW', 'TOS', 'HP', 'LP', 'GR', 'ME', 'BC',
])
# Prefixes whose number is not grade (wall, curb, floor, footing, pipe tops),
# or is existing grade, which the proposed grade replaces.
SKIP_PREFIXES = frozenset([
    'TW', 'TOW', 'TC', 'TOC', 'FF', 'FFE', 'FFL', 'TF', 'TOF', 'BF', 'BOF',
    'INV', 'IE', 'RIM', 'EX', 'EG', 'EXG', 'EXIST',
])

SPOT = 'spot'
CONTOUR = 'contour'

DEFAULT_BAND_FEET = 10.0
INSIDE_TOLERANCE_FEET = 0.5
HOLD_FEET = 5.0
SPARSE_GAP_FEET = 25.0
DUPLICATE_FEET = 0.5
PREFIX_GAP_RATIO = 1.5

_NUMBER = r'[+-]?\d{1,4}(?:\.\d{1,2})?'
_WORD = re.compile(r'^([A-Za-z]{1,5})?\s*[=:]?\s*(' + _NUMBER + r')\s*([A-Za-z]{1,5})?$')
_PREFIX_ONLY = re.compile(r'^([A-Za-z]{1,5})\s*[=:]?$')


def parse_word(text):
    """Return (prefix, number_text, suffix) for a label word, else None.

    Parenthesized numbers are existing grade on most civil sheets and are
    not read.
    """
    text = (text or '').strip()
    if not text or text.startswith('('):
        return None
    match = _WORD.match(text)
    if not match:
        return None
    return ((match.group(1) or '').upper(), match.group(2), (match.group(3) or '').upper())


def classify_label(prefix, number_text):
    """Return SPOT, CONTOUR, or None for a label's prefix and number.

    A prefixed label counts only for a grade prefix. A plain number is a spot
    elevation when it has decimals and a contour label when it is whole.
    """
    if prefix:
        if prefix in GRADE_PREFIXES:
            return SPOT
        return None
    return SPOT if '.' in number_text else CONTOUR


def _along(word, ux, uy):
    return word.x * ux + word.y * uy


def _across(word, ux, uy):
    return -word.x * uy + word.y * ux


def _neighbor_text(word, words, before):
    """Return the text of the word just before (or after) word on its baseline."""
    ux, uy, size = word.ux, word.uy, word.size
    base = _across(word, ux, uy)
    start = _along(word, ux, uy)
    best, best_gap = None, None
    for other in words:
        if other is word or other.ux * ux + other.uy * uy < 0.999:
            continue
        if abs(_across(other, ux, uy) - base) > 0.5 * size:
            continue
        other_start = _along(other, ux, uy)
        if before:
            gap = start - (other_start + other.length)
        else:
            gap = other_start - (start + word.length)
        if -0.25 * size <= gap <= PREFIX_GAP_RATIO * size and (best_gap is None or gap < best_gap):
            best, best_gap = other, gap
    return best.text if best is not None else ''


def _side_prefix(text):
    match = _PREFIX_ONLY.match((text or '').strip())
    return match.group(1).upper() if match else ''


def elevation_words(words):
    """Return (word, kind, value) for every grade label among words."""
    found = []
    for word in words:
        parsed = parse_word(word.text)
        if parsed is None:
            continue
        prefix, number_text, suffix = parsed
        prefix = prefix or suffix
        if not prefix:
            prefix = (_side_prefix(_neighbor_text(word, words, True))
                      or _side_prefix(_neighbor_text(word, words, False)))
        kind = classify_label(prefix, number_text)
        if kind is None:
            continue
        found.append((word, kind, float(number_text)))
    return found


def elevation_labels(page_text, pose, page_size, elevation_range=None):
    """Return grade labels placed in view feet: dicts with x, y, value, kind.

    elevation_range, (low, high) in the PDF datum, drops numbers that cannot
    be grade near these walls (sheet numbers, dimensions, note numbers).
    """
    labels = []
    for word, kind, value in elevation_words(page_text.words):
        if elevation_range is not None and not elevation_range[0] <= value <= elevation_range[1]:
            continue
        center = label_in_view(word, page_text, pose, page_size)[0]
        labels.append({'x': center[0], 'y': center[1], 'value': value, 'kind': kind,
                       'text': word.text})
    return labels


_FEET_INCHES = re.compile(
    r"^([+-]?\d+(?:\.\d+)?)\s*'\s*-?\s*(?:(\d+(?:\.\d+)?)?\s*(?:(\d+)\s*/\s*(\d+))?\s*\"?)?$")


def parse_elevation(text):
    """Return feet from '5432.50', '5432', or 5432'-6 1/2\"; None if unreadable."""
    text = (text or '').strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        pass
    match = _FEET_INCHES.match(text)
    if not match:
        return None
    inches = float(match.group(2) or 0.0)
    if match.group(3):
        if float(match.group(4)) == 0:
            return None
        inches += float(match.group(3)) / float(match.group(4))
    sign = -1.0 if match.group(1).startswith('-') else 1.0
    return sign * (abs(float(match.group(1))) + inches / 12.0)


def to_internal(value, origin_internal_z, origin_reported_z):
    """Convert a PDF (USGS) elevation to Revit internal Z.

    The reference is one known pair: origin_internal_z is a Revit elevation
    (a level's internal Z) and origin_reported_z is the USGS elevation the
    drawings give for it.
    """
    return value - origin_reported_z + origin_internal_z


def to_reported(z, origin_internal_z, origin_reported_z):
    return z - origin_internal_z + origin_reported_z


# -- Along the wall ----------------------------------------------------------------

def project_labels(path, labels, band=DEFAULT_BAND_FEET,
                   inside_tolerance=INSIDE_TOLERANCE_FEET):
    """Return (chainage, offset, value) for labels beside the wall's exterior face.

    path is a list of dicts with chainage, x, y (exterior face points) and
    nx, ny (exterior unit normals), ordered by chainage. Offset is measured
    outward from the face; labels inside the wall, past the band, or more
    than the band beyond either end are dropped. When two labels fall within
    DUPLICATE_FEET along the wall, the one nearer the wall is kept.
    """
    if len(path) < 2:
        return []
    length = path[-1]['chainage']
    hits = []
    for label in labels:
        best = None
        for index in range(len(path) - 1):
            a, b = path[index], path[index + 1]
            dx, dy = b['x'] - a['x'], b['y'] - a['y']
            seg = math.hypot(dx, dy)
            if seg <= 0:
                continue
            t = ((label['x'] - a['x']) * dx + (label['y'] - a['y']) * dy) / (seg * seg)
            low = -float('inf') if index == 0 else 0.0
            high = float('inf') if index == len(path) - 2 else 1.0
            t = min(max(t, low), high)
            px, py = a['x'] + t * dx, a['y'] + t * dy
            distance = math.hypot(label['x'] - px, label['y'] - py)
            if best is None or distance < best[0]:
                # The segment's own perpendicular, turned to the exterior side.
                nx, ny = dy / seg, -dx / seg
                if nx * (a['nx'] + b['nx']) + ny * (a['ny'] + b['ny']) < 0:
                    nx, ny = -nx, -ny
                offset = (label['x'] - px) * nx + (label['y'] - py) * ny
                chainage = a['chainage'] + t * (b['chainage'] - a['chainage'])
                best = (distance, chainage, offset)
        if best is None:
            continue
        _, chainage, offset = best
        if not -inside_tolerance <= offset <= band:
            continue
        if not -band <= chainage <= length + band:
            continue
        hits.append((chainage, offset, label['value']))
    hits.sort()
    kept = []
    for hit in hits:
        if kept and hit[0] - kept[-1][0] < DUPLICATE_FEET:
            if abs(hit[1]) < abs(kept[-1][1]):
                kept[-1] = hit
            continue
        kept.append(hit)
    return kept


def interpolate(chainages, samples, hold=HOLD_FEET, sparse_gap=SPARSE_GAP_FEET):
    """Return grade at each chainage from (chainage, offset, value) samples.

    Between two samples no more than sparse_gap apart the grade is linear.
    Before the first sample, after the last, or inside a wider gap, grade is
    held at the nearer sample's value within hold of it, and is None (no
    data) beyond that.
    """
    points = sorted((sample[0], sample[2]) for sample in samples)
    grades = []
    for chainage in chainages:
        grade = None
        if points:
            first, last = points[0], points[-1]
            if chainage <= first[0]:
                if first[0] - chainage <= hold:
                    grade = first[1]
            elif chainage >= last[0]:
                if chainage - last[0] <= hold:
                    grade = last[1]
            else:
                for (c0, v0), (c1, v1) in zip(points, points[1:]):
                    if c0 <= chainage <= c1:
                        if c1 - c0 <= sparse_gap:
                            grade = v0 + (v1 - v0) * (chainage - c0) / (c1 - c0) if c1 > c0 else v0
                        elif chainage - c0 <= hold:
                            grade = v0
                        elif c1 - chainage <= hold:
                            grade = v1
                        break
        grades.append(grade)
    return grades
