"""Finite relationship discovery without loading Revit or assigning severity."""

import math

from steel_model_review.geometry import (
    distance, face_contains, intersection, projection, section_interval,
)
from steel_model_review.records import relationship


def _direction(member):
    return tuple(member['end'][i] - member['start'][i] for i in (0, 1))


def beam_target(member, end, support, settings):
    """Classify endpoint-to-body, splice, and corner targets over finite spans."""
    point = (member['start'], member['end'])[end]
    target, fraction = projection(point, support['start'], support['end'])
    a, b = _direction(member), _direction(support)
    lengths = distance(a, (0, 0)) * distance(b, (0, 0))
    if not lengths:
        return None
    cosine = max(-1.0, min(1.0, sum(a[i] * b[i] for i in (0, 1)) / lengths))
    angle = math.degrees(math.acos(abs(cosine)))
    parallel = angle <= settings.get('angle_degrees', 0.01)
    eps = settings['epsilon']
    ends = [support['start'][:2], support['end'][:2]]
    target_end = min((0, 1), key=lambda i: distance(point[:2], ends[i]))
    at_end = distance(target, ends[target_end]) <= eps
    if parallel:
        # Both spans must run away from the joint in opposite directions.
        own_out = tuple((member['end'] if end == 0 else member['start'])[i] -
                        point[i] for i in (0, 1))
        other_out = tuple((support['end'] if target_end == 0 else support['start'])[i] -
                          ends[target_end][i] for i in (0, 1))
        if not at_end or sum(own_out[i] * other_out[i] for i in (0, 1)) >= 0:
            return None
        # A parallel side-by-side pair is not a splice, even with nearby ends.
        if abs(a[0] * (ends[target_end][1] - point[1]) -
               a[1] * (ends[target_end][0] - point[0])) / distance(a, (0, 0)) > eps:
            return None
        target, category = ends[target_end], 'Splice connection'
    else:
        span = distance(support['start'][:2], support['end'][:2])
        if fraction < -eps / span or fraction > 1 + eps / span:
            return None
        category = 'Corner/End' if at_end else 'Girder connection'
    return {'target': target, 'category': category, 'target_end': target_end if
            at_end else '', 'station': max(0.0, min(1.0, fraction)), 'angle': angle}


def discover_end(member, end, index, settings, wall_target):
    """Return exact-first candidates; proximity and API joins remain evidence."""
    point = (member['start'], member['end'])[end]
    candidates = []
    own = section_interval(member, point, settings['epsilon'])
    for support in index.query(point, settings['search']):
        if support['uid'] == member['uid']:
            continue
        if support['kind'] == 'beam':
            item = beam_target(member, end, support, settings)
        elif support['kind'] == 'column':
            faces = column_faces(member, end, support, settings['epsilon'])
            item = {'target': support['start'][:2], 'category': 'Column Axis', 'faces': faces}
        elif support['kind'] == 'wall':
            target, ambiguous = wall_target(point, support,
                                           member['end'] if end == 0 else member['start'])
            item = {'target': target, 'category': 'Concrete Wall Face',
                    'ambiguous': ambiguous} if target is not None else None
        else:
            continue
        if item is None:
            continue
        gap = distance(point[:2], item['target'])
        proximity = min([gap] + [face['gap'] for face in item.get('faces', [])])
        lo, hi = support['bounds']
        zlo, zhi = own if own else (point[2], point[2])
        if proximity > settings['search'] or max(zlo - hi[2], lo[2] - zhi) > settings['search']:
            continue
        item.update(member=support, gap=gap, proximity=proximity)
        candidates.append(item)
    exact = [c for c in candidates if c['proximity'] <= settings['epsilon']]
    return exact or candidates


def end_relationship(member, end, candidate, count):
    """Preserve geometry, group identity and source join evidence separately."""
    support = candidate['member']
    own_join = member.get('joins', {}).get(str(end), {'state': 'Unavailable'})
    return relationship(
        member, support, candidate['category'], end, candidate.get('target_end', ''),
        target=list(candidate['target']), station=candidate.get('station'),
        angle_degrees=candidate.get('angle'), horizontal_miss=candidate['gap'],
        receiving_usage=support.get('structural_usage'),
        join=own_join, group=[member['uid'], end], group_size=count,
        target_join=support.get('joins', {}).get(str(candidate.get('target_end')), {}),
        coordinate_basis='Reference line in plan; elevation evaluated separately')


def column_faces(member, end, column, epsilon):
    """Find approached finite section faces and label reliably identified web faces.

    Face distances use the reference endpoint as diagnostic evidence. They do
    not require a reference endpoint and physical cut end to share one target.
    """
    point = (member['start'], member['end'])[end]
    other = (member['end'], member['start'])[end]
    section = section_interval(member, point, epsilon)
    z = sum(section) / 2 if section else point[2]
    containing = section_interval(column, other, epsilon)
    if containing is not None and containing[0] <= z <= containing[1]:
        return []
    hits = []
    for face in column.get('faces', []):
        normal, origin, _loops = face
        if abs(normal[2]) > 1e-8:
            continue
        direction = tuple(point[i] - other[i] for i in (0, 1))
        denominator = sum(normal[i] * direction[i] for i in (0, 1))
        if abs(denominator) <= 1e-12:
            continue
        t = sum(normal[i] * (origin[i] - other[i]) for i in (0, 1)) / denominator
        if t <= 0:
            continue
        hit = (other[0] + t * direction[0], other[1] + t * direction[1], z)
        if face_contains(face, hit, epsilon):
            hits.append((t, hit, normal))
    if not hits:
        return []
    hits.sort(key=lambda h: h[0])
    # Keep the face first approached from outside; never the opposite side.
    t, hit, normal = hits[0]
    kind = 'Column Section Face'
    web_normals = column.get('web_normals', [])
    if web_normals:
        if any(abs(sum(normal[i] * n[i] for i in range(3))) > 0.999999 and
               abs(sum(n[i] * (hit[i] - origin[i]) for i in range(3))) <= epsilon
               for n, origin in column.get('web_planes', [])):
            kind = 'Column Web Face'
        elif all(abs(sum(normal[i] * n[i] for i in range(3))) < 1e-6 for n in web_normals):
            kind = 'Column Flange Face'
    return [{'category': kind, 'target': hit[:2],
             'gap': distance(point[:2], hit[:2]), 'source': 'Reference endpoint'}]


def crossing_relationship(a, b, epsilon):
    """Return an interior crossing with local vertical evidence, if any."""
    hit = intersection(a, b)
    if hit is None:
        return None
    for member in (a, b):
        _nearest, fraction = projection(hit, member['start'], member['end'])
        length = distance(member['start'][:2], member['end'][:2])
        if not length or not epsilon / length < fraction < 1 - epsilon / length:
            return None
    own, other = (section_interval(m, hit, epsilon) for m in (a, b))
    gap = max(own[0] - other[1], other[0] - own[1], 0.0) if own and other else None
    category = 'Interior Crossing' if gap is not None and gap <= epsilon else (
        'Separated Plan Crossing' if gap is not None else 'Unresolved Plan Crossing')
    return relationship(a, b, category, target=list(hit), vertical_gap=gap,
                        evidence_basis='Original section vertical intervals at plan crossing')
