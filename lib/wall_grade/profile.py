# -*- coding: utf-8 -*-
"""Grade profile along a wall: stations, clearance classes, flagged runs.

All lengths and elevations are in feet (Revit internal units). A station is a
distance along the wall's location curve from its start. Clearance at a
station is top of wall minus grade; it is negative where grade is above the
top of the wall.
"""

import math


DEFAULT_INTERVAL_FEET = 1.0
DEFAULT_CLEARANCE_INCHES = 8.0
MAX_CLEARANCE_INCHES = 48.0
PROBE_OFFSET_FEET = 3.0 / 12.0
LINE_OFFSET_FEET = 1.0 / 12.0
INCHES_PER_FOOT = 12.0

OK = 'ok'
CLOSE = 'close'
OVER = 'over'
NO_DATA = 'nodata'

# Worse statuses sort higher; a segment takes the worse of its two ends.
_SEVERITY = {NO_DATA: -1, OK: 0, CLOSE: 1, OVER: 2}

# WallLocationLine enum values and where each puts the exterior face,
# measured from the location line toward the exterior, as a fraction of the
# wall width. Core faces are treated as finish faces: foundation walls are
# normally one layer, and the probe offset absorbs a thin finish.
_EXTERIOR_FRACTION = {
    0: 0.5,   # Wall Centerline
    1: 0.5,   # Core Centerline
    2: 0.0,   # Finish Face: Exterior
    3: 1.0,   # Finish Face: Interior
    4: 0.0,   # Core Face: Exterior
    5: 1.0,   # Core Face: Interior
}


def clamp_clearance(value, default=DEFAULT_CLEARANCE_INCHES, maximum=MAX_CLEARANCE_INCHES):
    """Return clearance inches from user text: positive, at most maximum, else default."""
    try:
        value = float(str(value).strip().rstrip('"').strip())
    except (TypeError, ValueError):
        return default
    if value != value or value <= 0:
        return default
    return min(value, maximum)


def stations(length, interval=DEFAULT_INTERVAL_FEET):
    """Return stations from 0 to length at interval, always including both ends."""
    if length <= 0:
        return [0.0]
    count = max(int(math.ceil(length / float(interval) - 1e-9)), 1)
    step = length / float(count)
    return [step * index for index in range(count)] + [float(length)]


def exterior_offset(location_line, width):
    """Return the distance from the location line to the exterior face."""
    return _EXTERIOR_FRACTION.get(int(location_line), 0.5) * width


def classify(clearance, limit_feet):
    """Return OK, CLOSE, OVER, or NO_DATA for one clearance in feet."""
    if clearance is None:
        return NO_DATA
    if clearance <= 0:
        return OVER
    if clearance < limit_feet:
        return CLOSE
    return OK


def build_profile(chainages, grades, tops, limit_feet):
    """Return per-station dicts with chainage, grade, top, clearance, status."""
    points = []
    for chainage, grade, top in zip(chainages, grades, tops):
        clearance = None if grade is None or top is None else top - grade
        points.append({
            'chainage': chainage,
            'grade': grade,
            'top': top,
            'clearance': clearance,
            'status': classify(clearance, limit_feet),
        })
    return points


def segments(profile):
    """Return drawable segments between neighboring stations that both have grade.

    Each segment is (index_a, index_b, status) where status is the worse of
    its two ends.
    """
    result = []
    for index in range(len(profile) - 1):
        a, b = profile[index], profile[index + 1]
        if a['status'] == NO_DATA or b['status'] == NO_DATA:
            continue
        status = max(a['status'], b['status'], key=lambda value: _SEVERITY[value])
        result.append((index, index + 1, status))
    return result


def flagged_runs(profile):
    """Return runs of consecutive CLOSE or OVER stations.

    Each run is a dict with start/end chainage, the index of its worst
    (smallest clearance) station, and the run status (OVER if any station in
    it is OVER).
    """
    runs = []
    current = None
    for index, point in enumerate(profile):
        if point['status'] in (CLOSE, OVER):
            if current is None:
                current = {'first': index, 'last': index, 'worst': index}
            current['last'] = index
            if point['clearance'] < profile[current['worst']]['clearance']:
                current['worst'] = index
        elif current is not None:
            runs.append(current)
            current = None
    if current is not None:
        runs.append(current)
    for run in runs:
        statuses = [profile[i]['status'] for i in range(run['first'], run['last'] + 1)]
        run['status'] = OVER if OVER in statuses else CLOSE
        run['start'] = profile[run['first']]['chainage']
        run['end'] = profile[run['last']]['chainage']
        run['clearance'] = profile[run['worst']]['clearance']
    return runs


def no_data_ranges(profile):
    """Return (start, end) chainages of consecutive stations without grade."""
    ranges = []
    start = None
    for index, point in enumerate(profile):
        if point['status'] == NO_DATA:
            if start is None:
                start = index
        elif start is not None:
            ranges.append((profile[start]['chainage'], profile[index - 1]['chainage']))
            start = None
    if start is not None:
        ranges.append((profile[start]['chainage'], profile[-1]['chainage']))
    return ranges


def min_clearance(profile):
    values = [point['clearance'] for point in profile if point['clearance'] is not None]
    return min(values) if values else None


def format_inches(feet):
    """Return a length in feet as whole and half inches, e.g. 5 1/2\"."""
    halves = int(round(abs(feet) * INCHES_PER_FOOT * 2.0))
    whole, half = divmod(halves, 2)
    if half and whole:
        return '{} 1/2"'.format(whole)
    if half:
        return '1/2"'
    return '{}"'.format(whole)


def format_feet_inches(feet):
    """Return an elevation or length as feet and inches, e.g. 94'-7 1/2\"."""
    sign = '-' if feet < 0 else ''
    halves = int(round(abs(feet) * INCHES_PER_FOOT * 2.0))
    whole_feet, rest = divmod(halves, 24)
    inches, half = divmod(rest, 2)
    inch_text = '{} 1/2'.format(inches) if half else str(inches)
    return '{}{}\'-{}"'.format(sign, whole_feet, inch_text)


def note_text(clearance):
    """Return the flag note for a clearance in feet."""
    if abs(clearance) * INCHES_PER_FOOT < 0.25:
        return 'GRADE AT T/WALL'
    if clearance > 0:
        return 'GRADE {} BELOW T/WALL'.format(format_inches(clearance))
    return 'GRADE {} ABOVE T/WALL'.format(format_inches(clearance))
