"""Host-independent supported/supporting member decisions for hanger checks.

Ported from the KL&A Dynamo graph "Check Hanger Locations 1.0.3". Members are
plain dicts in feet, using the framing location line:

    {'id': 123, 'start': (x, y, z), 'end': (x, y, z)}

The hanger text direction (the family's local X axis in plan) decides roles:

  * Supported member: runs along the top or base of the hanger text (within
    SUPPORTED_MAX_ANGLE_DEG of the text) and has an end inside the hanger box,
    ALONG_REACH_FT along the text and ACROSS_REACH_FT across it. The end
    closest to the hanger wins.
  * Supporting member: crosses the text at SUPPORTING_MIN_ANGLE_DEG or more
    (square, or skewed up to 90 - SUPPORTING_MIN_ANGLE_DEG) and passes within
    SUPPORT_REACH_FT of the supported member's end. Members that run through
    are preferred over members that only end there, then the closest wins.
  * Without a text direction both checks fall back to the member geometry.
  * A hanger point with z None is compared in plan only (as the Dynamo graph
    did by projecting onto the level); the supporting member is then still
    checked against the height of the supported member's end.
"""

from __future__ import division

import math


DEFAULT_HANGER_FAMILY = 'Hangers_Clever_KLAA'
ALONG_REACH_FT = 2.0
ACROSS_REACH_FT = 1.0
VERTICAL_REACH_FT = 2.0
SUPPORT_REACH_FT = 1.0
SEARCH_RADIUS_FT = ALONG_REACH_FT + SUPPORT_REACH_FT
SUPPORTED_MAX_ANGLE_DEG = 30.0
SUPPORTING_MIN_ANGLE_DEG = 30.0
SKEW_NOTE_DEG = 2.0
AMBIGUOUS_FT = 1.0 / 12.0

STATUS_OK = 'OK'
STATUS_NO_FRAMING = 'No framing at hanger'
STATUS_ORIENTATION = 'Hanger not aligned with member'
STATUS_NO_SUPPORTED = 'No supported member'
STATUS_NO_SUPPORTING = 'No supporting member'
STATUS_SHARED = 'Shared member end'
STATUS_REVIEW = 'Review'
STATUS_REVIEW_DETAILS = 'Review details'

ROLE_SUPPORTED = 'supported'
ROLE_SUPPORTING = 'supporting'
ROLE_BOTH = 'both'


def closest_on_segment(point, start, end):
    """Closest point on the member line to a point in plan -> (t, z, plan dist)."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length_sq = dx * dx + dy * dy
    t = 0.0
    if length_sq > 0:
        t = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / length_sq
        t = max(0.0, min(1.0, t))
    cx, cy = start[0] + t * dx, start[1] + t * dy
    z = start[2] + t * (end[2] - start[2])
    return t, z, math.hypot(point[0] - cx, point[1] - cy)


def unit_plan(vector):
    """Unit plan vector, or None for a vertical/zero-length vector."""
    if vector is None:
        return None
    length = math.hypot(vector[0], vector[1])
    if length < 1e-9:
        return None
    return vector[0] / length, vector[1] / length


def plan_direction(member):
    return unit_plan((member['end'][0] - member['start'][0],
                      member['end'][1] - member['start'][1]))


def axis_angle_deg(dir_a, dir_b):
    """Angle between two plan axes, ignoring direction: 0 (parallel) to 90 (square)."""
    if dir_a is None or dir_b is None:
        return None
    dot = min(1.0, abs(dir_a[0] * dir_b[0] + dir_a[1] * dir_b[1]))
    return math.degrees(math.acos(dot))


def _end_offset(point, end_point, text_dir):
    """(inside hanger box, plan distance) for one member end."""
    dx, dy = end_point[0] - point[0], end_point[1] - point[1]
    plan = math.hypot(dx, dy)
    if point[2] is not None and abs(end_point[2] - point[2]) > VERTICAL_REACH_FT:
        return False, plan
    if text_dir is None:
        return plan <= ACROSS_REACH_FT, plan
    along = dx * text_dir[0] + dy * text_dir[1]
    across = -dx * text_dir[1] + dy * text_dir[0]
    return abs(along) <= ALONG_REACH_FT and abs(across) <= ACROSS_REACH_FT, plan


def nearest_end(point, member, text_dir=None):
    """(end index, plan dist) of the member end inside the hanger box, else None."""
    best = None
    for index, key in ((0, 'start'), (1, 'end')):
        inside, plan = _end_offset(point, member[key], text_dir)
        if inside and (best is None or plan < best[1]):
            best = (index, plan)
    return best


def _end_point(member, index):
    return member['start'] if index == 0 else member['end']


def classify_hanger(point, members, text_dir=None):
    """Pick the supported and supporting member for one hanger.

    point is the hanger insertion point and text_dir its plan text direction
    (any sign); both in feet/model coordinates.
    """
    text_dir = unit_plan(text_dir)
    result = {'supported': None, 'supported_end': None, 'supporting': None,
              'skew_deg': None, 'status': STATUS_OK, 'notes': []}
    if not members:
        result['status'] = STATUS_NO_FRAMING
        return result

    ends, misaligned = [], []
    for member in members:
        end = nearest_end(point, member, text_dir)
        if end is None:
            continue
        angle = axis_angle_deg(plan_direction(member), text_dir)
        if angle is None or angle <= SUPPORTED_MAX_ANGLE_DEG:
            ends.append((end[1], end[0], member))
        else:
            misaligned.append((angle, member))
    ends.sort(key=lambda item: item[0])
    supported = ends[0][2] if ends else None
    if supported is not None:
        result['supported'], result['supported_end'] = supported['id'], ends[0][1]
        tied = [item[2]['id'] for item in ends[1:] if item[0] - ends[0][0] <= AMBIGUOUS_FT]
        if tied:
            result['notes'].append('Another member end is equally close (Id %s); '
                                   'confirm the supported member' % ', '.join(map(str, tied)))
    elif misaligned:
        misaligned.sort(key=lambda item: item[0])
        result['notes'].append('Member Id %d ends at the hanger but runs %.0f deg off the '
                               'hanger text' % (misaligned[0][1]['id'], misaligned[0][0]))

    anchor = _end_point(supported, ends[0][1]) if supported is not None else point
    reference = text_dir or (plan_direction(supported) if supported is not None else None)
    through = []
    for member in members:
        if supported is not None and member['id'] == supported['id']:
            continue
        angle = axis_angle_deg(plan_direction(member), reference)
        if angle is not None and angle < SUPPORTING_MIN_ANGLE_DEG:
            continue
        t, z, plan = closest_on_segment(anchor, member['start'], member['end'])
        if plan > SUPPORT_REACH_FT or (anchor[2] is not None
                                       and abs(z - anchor[2]) > VERTICAL_REACH_FT):
            continue
        ends_here = min(math.hypot(anchor[0] - p[0], anchor[1] - p[1])
                        for p in (member['start'], member['end'])) <= SUPPORT_REACH_FT
        through.append((ends_here, plan, member))
    through.sort(key=lambda item: (item[0], item[1]))
    if through:
        supporting = through[0][2]
        result['supporting'] = supporting['id']
        if through[0][0]:
            result['notes'].append('Supporting member also ends at this hanger')
        if supported is not None:
            skew = 90.0 - axis_angle_deg(plan_direction(supported), plan_direction(supporting))
            result['skew_deg'] = round(skew, 1)

    if supported is None:
        result['status'] = STATUS_ORIENTATION if misaligned else STATUS_NO_SUPPORTED
    elif result['supporting'] is None:
        result['status'] = STATUS_NO_SUPPORTING
    return result


def apply_review(result, mismatch, wall_or_column=False):
    """Set the reported status after the size check.

    The location status is kept in 'location_status'. A location problem wins,
    then a size mismatch ('Review'), then a wall or column support ('Review
    details': confirm the ledger, plate or connection detail). A wall or column
    support is not modeled framing, so a missing supporting member is expected.
    """
    location = result['status']
    if wall_or_column and location == STATUS_NO_SUPPORTING:
        location = STATUS_OK
        result['notes'].append('Supported by a wall or column; no framing member expected')
    result['location_status'] = location
    result['mismatch'] = mismatch
    if location != STATUS_OK:
        result['status'] = location
    elif mismatch:
        result['status'] = STATUS_REVIEW
    elif wall_or_column:
        result['status'] = STATUS_REVIEW_DETAILS
    else:
        result['status'] = STATUS_OK
    return result


def is_problem(result):
    """A hanger needs attention: location status or a Header/Joist size mismatch."""
    return (result['status'] not in (STATUS_OK, STATUS_REVIEW_DETAILS)
            or bool(result.get('mismatch')))


def match_label(result):
    """Short Yes/No answer for whether the hanger and its framing agree."""
    if result.get('location_status', result['status']) not in (STATUS_OK, STATUS_SHARED):
        return 'No'
    if result['skew_deg'] is not None and result['skew_deg'] >= SKEW_NOTE_DEG:
        return 'Yes (skewed %.1f deg)' % result['skew_deg']
    return 'Yes'


def flag_shared_ends(results):
    """Mark hangers that claim the same supported member end. results: {hanger id: result}."""
    claims = {}
    for hanger_id, result in results.items():
        if result['supported'] is not None:
            claims.setdefault((result['supported'], result['supported_end']), []).append(hanger_id)
    for hanger_ids in claims.values():
        if len(hanger_ids) < 2:
            continue
        for hanger_id in hanger_ids:
            result = results[hanger_id]
            others = sorted(other for other in hanger_ids if other != hanger_id)
            result['notes'].append('Same member end as hanger Id %s' % ', '.join(map(str, others)))
            if result['status'] == STATUS_OK:
                result['status'] = STATUS_SHARED
    return results


def member_roles(results):
    """Return {member id: supported|supporting|both} across all hanger results."""
    roles = {}
    for result in results.values():
        for member_id, role in ((result['supported'], ROLE_SUPPORTED),
                                (result['supporting'], ROLE_SUPPORTING)):
            if member_id is None:
                continue
            current = roles.get(member_id)
            roles[member_id] = role if current in (None, role) else ROLE_BOTH
    return roles


def matches_family(family_name, hanger_family=DEFAULT_HANGER_FAMILY):
    """Case-insensitive family-name match used to find hanger instances."""
    return bool(family_name) and (hanger_family or DEFAULT_HANGER_FAMILY).lower() in family_name.lower()
