"""Host-independent supported/supporting member decisions for hanger checks.

Ported from the KL&A Dynamo graph "Check Hanger Locations 1.0.3". Each hanger
gets a search box around its insertion point (plan +/- PLAN_REACH_FT, vertical
+/- VERTICAL_REACH_FT, the Dynamo D1/D2 inputs). Members are plain dicts:

    {'id': 123, 'start': (x, y, z), 'end': (x, y, z)}    # feet, location line

  * Supported member: the framing member whose start OR end point lies in the
    box; the end closest to the hanger in plan wins.
  * Supporting member: another framing member, not parallel to the supported
    member, whose location line passes through the box. Members that run
    through the hanger are preferred over members that only end there, then
    the closest in plan wins.
"""

from __future__ import division

import math


DEFAULT_HANGER_FAMILY = 'Hangers_Clever_KLAA'
PLAN_REACH_FT = 1.0
VERTICAL_REACH_FT = 2.0
PARALLEL_DOT = 0.95
AMBIGUOUS_FT = 1.0 / 12.0

STATUS_OK = 'OK'
STATUS_NO_FRAMING = 'No framing at hanger'
STATUS_NO_SUPPORTED = 'No supported member'
STATUS_NO_SUPPORTING = 'No supporting member'
STATUS_SHARED = 'Shared member end'

ROLE_SUPPORTED = 'supported'
ROLE_SUPPORTING = 'supporting'
ROLE_BOTH = 'both'


def closest_on_segment(point, start, end):
    """Closest point on the member line to the hanger in plan -> (t, z, plan dist)."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length_sq = dx * dx + dy * dy
    t = 0.0
    if length_sq > 0:
        t = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / length_sq
        t = max(0.0, min(1.0, t))
    cx, cy = start[0] + t * dx, start[1] + t * dy
    z = start[2] + t * (end[2] - start[2])
    return t, z, math.hypot(point[0] - cx, point[1] - cy)


def plan_direction(member):
    """Unit plan direction of a member, or None for a vertical/zero-length line."""
    dx = member['end'][0] - member['start'][0]
    dy = member['end'][1] - member['start'][1]
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return None
    return dx / length, dy / length


def is_parallel(member_a, member_b):
    a, b = plan_direction(member_a), plan_direction(member_b)
    if a is None or b is None:
        return False
    return abs(a[0] * b[0] + a[1] * b[1]) > PARALLEL_DOT


def _in_box(point, other, plan_reach, vertical_reach):
    plan = math.hypot(point[0] - other[0], point[1] - other[1])
    return plan <= plan_reach and abs(point[2] - other[2]) <= vertical_reach, plan


def nearest_end(point, member, plan_reach=PLAN_REACH_FT, vertical_reach=VERTICAL_REACH_FT):
    """(end index, plan dist) of the member end inside the hanger box, else None."""
    best = None
    for index, key in ((0, 'start'), (1, 'end')):
        inside, plan = _in_box(point, member[key], plan_reach, vertical_reach)
        if inside and (best is None or plan < best[1]):
            best = (index, plan)
    return best


def classify_hanger(point, members, plan_reach=PLAN_REACH_FT, vertical_reach=VERTICAL_REACH_FT):
    """Pick the supported and supporting member for one hanger insertion point."""
    result = {'supported': None, 'supported_end': None, 'supporting': None,
              'status': STATUS_OK, 'notes': []}
    if not members:
        result['status'] = STATUS_NO_FRAMING
        return result

    ends = []
    for member in members:
        end = nearest_end(point, member, plan_reach, vertical_reach)
        if end is not None:
            ends.append((end[1], end[0], member))
    ends.sort(key=lambda item: item[0])
    supported = ends[0][2] if ends else None
    if supported is not None:
        result['supported'], result['supported_end'] = supported['id'], ends[0][1]
        tied = [item[2]['id'] for item in ends[1:] if item[0] - ends[0][0] <= AMBIGUOUS_FT]
        if tied:
            result['notes'].append('Another member end is equally close (Id %s); '
                                   'confirm the supported member' % ', '.join(map(str, tied)))

    through = []
    for member in members:
        if supported is not None and (member['id'] == supported['id']
                                      or is_parallel(member, supported)):
            continue
        t, z, plan = closest_on_segment(point, member['start'], member['end'])
        if plan > plan_reach or abs(z - point[2]) > vertical_reach:
            continue
        ends_here = nearest_end(point, member, plan_reach, vertical_reach) is not None
        through.append((ends_here, plan, member))
    through.sort(key=lambda item: (item[0], item[1]))
    if through:
        result['supporting'] = through[0][2]['id']
        if through[0][0]:
            result['notes'].append('Supporting member also ends at this hanger')

    if supported is None:
        result['status'] = STATUS_NO_SUPPORTED
    elif result['supporting'] is None:
        result['status'] = STATUS_NO_SUPPORTING
    return result


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
