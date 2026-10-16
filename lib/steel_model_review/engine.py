"""Host-independent Model Checker rules and report rows.

All coordinates and discrepancies are in inches. Host extraction supplies
original solid face equations; no Revit objects are imported here.
"""

import math

from steel_model_review.geometry import (
    SpatialIndex, distance, intersection, line_distance, projection,
    section_interval,
)
from steel_model_review.connections import (
    crossing_relationship, discover_end, end_relationship,
)
from steel_model_review.records import (
    SCHEMA_VERSION, bind_result, member_record, relationship,
)

CHECKS = ('SMR-01', 'SMR-02', 'SMR-03', 'SMR-04', 'SMR-05', 'SMR-06')
DEFAULTS = {'epsilon': 0.000001, 'search': 12.0, 'near': 0.0625,
            'checks': CHECKS, 'grid_mode': 'Nearest intersection',
            'angle_degrees': 0.01}


class Cancelled(Exception):
    """Signal that the reviewer cancelled an incomplete run."""


def severity(value, epsilon=0.000001):
    """Classify an inch offset using the confirmed smaller-is-Critical rule."""
    value = abs(value)
    if math.isnan(value) or math.isinf(value):
        raise ValueError('An offset must be finite.')
    if value <= epsilon:
        return 'Pass'
    if abs(value - 0.0625) <= epsilon:
        value = 0.0625
    return 'Critical' if value < 0.0625 else 'Warning'


def finding(check, member, reason, level='Warning', value=None,
            end='', related=None, measurement='Offset'):
    """Build a plain result record with separate evaluation and review state."""
    related = [dict((key, r[key]) for key in ('uid', 'id', 'name') if key in r)
               for r in (related or [])]
    return {'check': check, 'uid': member['uid'], 'id': member['id'],
            'record_type': 'CheckResult', 'schema_version': SCHEMA_VERSION,
            'member_uid': member['uid'], 'relationship_id': None,
            'category': '', 'error_type': '',
            'evaluation': 'Not evaluated' if level == 'Not evaluated' else 'Evaluated',
            'member': member.get('name', str(member['id'])),
            'level': member.get('level', ''), 'severity': level,
            'value': value, 'measurement': measurement, 'end': end, 'reason': reason,
            'units': 'in' if value is not None else None,
            'related': related, 'status': 'Open', 'exception': '',
            'key': (check, member['uid'], str(end),
                    tuple(sorted(r['uid'] for r in related)))}


def _column_vertical(member, support, point, target, epsilon):
    """Separate full-depth shaft containment from local column-top bearing.

    Partial overlap is a shaft containment failure. A beam whose underside is
    at/above the finite column top is a bearing candidate, not a shaft Pass.
    """
    own = section_interval(member, point, epsilon)
    if own is None:
        return ('Column Vertical', None,
                'Beam local section boundaries could not be resolved.', {})
    low, high = support['bounds'][0][2], support['bounds'][1][2]
    facts = {'beam_bottom': own[0], 'beam_top': own[1],
             'column_bottom': low, 'column_top': high,
             'bottom_clearance': own[0] - low, 'top_protrusion': own[1] - high,
             'extent_basis': 'Original solid finite vertical extent'}
    if own[0] >= high - epsilon:
        other = section_interval(support, target, epsilon)
        if other is None:
            return ('Column Top Bearing', None,
                    'Column-top bearing candidate; local column top could not be resolved.', facts)
        facts.update(local_column_top=other[1], bearing_gap=own[0] - other[1])
        return ('Column Top Bearing', facts['bearing_gap'],
                'Beam underside minus local column top (bearing; positive is a gap).', facts)
    below = max(low - own[0], 0.0)
    above = max(own[1] - high, 0.0)
    value = -below if below > above else above
    reason = ('Full beam depth must lie within the finite column shaft. '
              'Below-base extent {0:.8f} in; above-top extent {1:.8f} in. '
              'Signed governing extent: negative below base, positive above top.'
              .format(below, above))
    return 'Column Shaft', value, reason, facts


def _vertical(member, support, point, target, epsilon):
    own = section_interval(member, point, epsilon)
    if own is None:
        return None, 'Beam local section boundaries could not be resolved.'
    other = section_interval(support, target, epsilon)
    if other is None:
        return None, 'Support local section boundaries could not be resolved.'
    if support['kind'] == 'wall':
        return own[0] - other[1], 'Beam underside minus wall top (bearing).'
    return own[1] - other[1], 'Beam top of steel minus support top of steel.'


def _target(point, support, other_end):
    """Resolve a finite target, using beam approach to choose a wall face."""
    if support['kind'] == 'column':
        return support['start'][:2], False
    if support['kind'] == 'wall':
        ray = {'start': other_end, 'end': point}
        hits = []
        for start, end in support.get('sides', []):
            hit = intersection(ray, {'start': start, 'end': end})
            if hit is None:
                continue
            _nearest, side_fraction = projection(hit, start, end)
            _nearest, ray_fraction = projection(hit, other_end, point)
            if 0 <= side_fraction <= 1 and ray_fraction > 0:
                hits.append((ray_fraction, hit))
        # Both crossings ahead establish the face first approached from outside.
        # Starting inside the wall does not establish a unique bearing face.
        if len(hits) == 2:
            hits.sort()
            return hits[0][1], abs(hits[0][0] - hits[1][0]) < 1e-9
    choices = []
    segments = support.get('sides', []) if support['kind'] == 'wall' else [
        (support['start'], support['end'])]
    for start, end in segments:
        target, fraction = projection(point, start, end)
        # A support span cannot be extended to establish connectivity.
        if 0.0 <= fraction <= 1.0:
            choices.append((distance(point[:2], target), target))
    if not choices:
        return None, False
    choices.sort()
    tie = len(choices) > 1 and abs(choices[0][0] - choices[1][0]) < 1e-6
    return choices[0][1], tie or support['kind'] == 'wall'


def endpoint_checks(member, index, settings, relationships=None):
    """Evaluate finite exact-first relationships, retaining each actual joint role."""
    rows = []
    relationships = relationships if relationships is not None else []
    eps, search = settings['epsilon'], settings['search']
    for end, point in enumerate((member['start'], member['end'])):
        candidates = discover_end(member, end, index, settings, _target)
        if not candidates:
            reason = 'No eligible finite support target within {0:g} in search.'.format(search)
            rel = relationship(member, None, 'Missing support', end, search_inches=search)
            relationships.append(rel)
            rows.append(bind_result(finding('SMR-01', member, reason, 'Critical',
                                             end=end), rel, 'Missing support'))
        elif (any(c.get('ambiguous') for c in candidates) or
              (len(candidates) > 1 and candidates[0]['proximity'] > eps)):
            reason = 'Ambiguous near-miss or wall-face relationship.'
            related = [c['member'] for c in candidates]
            rel = relationship(member, None, 'Ambiguous candidates', end,
                               candidates=[{'uid': c['member']['uid'],
                                            'category': c['category'], 'gap': c['gap']}
                                           for c in candidates])
            relationships.append(rel)
            rows.append(bind_result(finding('SMR-01', member, reason, end=end,
                                             related=related), rel))
        else:
            for candidate in candidates:
                support, target, gap = (candidate[k] for k in ('member', 'target', 'gap'))
                rel = end_relationship(member, end, candidate, len(candidates))
                relationships.append(rel)
                dx, dy = (target[i] - point[i] for i in (0, 1))
                vx = member['end'][0] - member['start'][0]
                vy = member['end'][1] - member['start'][1]
                length = math.sqrt(vx * vx + vy * vy)
                along = (-1 if end == 0 else 1) * (dx * vx + dy * vy) / length
                lateral = (dx * vy - dy * vx) / length
                rel['evidence'].update(along=along, lateral=lateral)
                reason = ('{0}; reference plan miss {1:.8f} in; along {2:+.8f} in '
                          '(positive shortfall), lateral {3:+.8f} in. Joint roles: {4}.'
                          .format(candidate['category'], gap, along, lateral, len(candidates)))
                rows.append(bind_result(finding('SMR-01', member, reason,
                                                 severity(gap, eps), gap, end, [support]),
                                        rel, 'Endpoint miss' if gap > eps else ''))
                vertical_rel, measurement = rel, 'Offset'
                if support['kind'] == 'column':
                    category, value, reason, facts = _column_vertical(
                        member, support, point, target, eps)
                    vertical_rel = relationship(member, support, category, end, **facts)
                    relationships.append(vertical_rel)
                    measurement = ('Bearing gap' if category == 'Column Top Bearing'
                                   else 'Shaft containment')
                elif candidate['category'] in ('Splice connection', 'Corner/End'):
                    value, reason = None, 'Vertical expectation for {0} is pending review.'.format(
                        candidate['category'])
                else:
                    value, reason = _vertical(member, support, point, target, eps)
                rows.append(bind_result(finding('SMR-02', member, reason,
                                                 severity(value, eps) if value is not None else
                                                 'Not evaluated', value, end, [support],
                                                 measurement=measurement), vertical_rel))
                if support['kind'] == 'column':
                    faces = candidate.get('faces', [])
                    for face in faces or [{'category': 'Column Face', 'target': None, 'gap': None}]:
                        face_rel = relationship(member, support, face['category'], end,
                                                target=face['target'], point_basis='Reference endpoint',
                                                face_miss=face['gap'])
                        relationships.append(face_rel)
                        reason = ('Reference-end distance to approached finite column face; '
                                  'physical cut-end policy pending.' if face['gap'] is not None else
                                  'Approached finite column face could not be resolved.')
                        rows.append(bind_result(finding('SMR-01', member, reason,
                                                         'Information' if face['gap'] is not None else
                                                         'Not evaluated', face['gap'], end, [support]), face_rel))
            continue
        rows.append(bind_result(finding('SMR-02', member,
                                         'Support relationship unresolved; see SMR-01.',
                                         'Not evaluated', end=end), rel))
    return rows


def grid_check(member, grids, settings, expected=None, pairs=None):
    """Measure a vertical column against a selected or nearest grid pair."""
    if settings.get('grid_mode') == 'Explicit grid pairs' and not expected:
        return finding('SMR-03', member, 'Assign an expected grid pair, then rerun.',
                       'Not evaluated')
    candidates = []
    if pairs is None or expected:
        chosen = [g for g in grids if not expected or g['uid'] in expected]
        pairs = []
        for i, a in enumerate(chosen):
            for b in chosen[i + 1:]:
                point = intersection(a, b)
                if point is not None:
                    pairs.append((point, a, b))
    for point, a, b in pairs:
        candidates.append((distance(member['start'][:2], point),
                           a['uid'], b['uid'], point, a, b))
    if not candidates:
        return finding('SMR-03', member, 'No reliable eligible grid pair.',
                       'Not evaluated')
    candidates.sort(key=lambda c: (c[0], c[1], c[2]))
    first = candidates[0]
    # Distinct datum pairs at the same intersection have the same expectation.
    ambiguous = any(abs(c[0] - first[0]) <= settings['epsilon'] and
                    distance(c[3], first[3]) > settings['epsilon']
                    for c in candidates[1:])
    if ambiguous:
        return finding('SMR-03', member, 'Equally plausible grid intersections.')
    gap, _a, _b, point, a, b = first
    result = severity(gap, settings['epsilon'])
    location = ('Column aligned to grid intersection.' if result == 'Pass' else
                'Off-grid column: review intended location.')
    reason = (location + ' {0} / {1}; '
              'line offsets {2:.8f}, {3:.8f} in; target ({4:.8f}, {5:.8f}) in.'
              .format(a['name'], b['name'], line_distance(member['start'], a),
                      line_distance(member['start'], b), point[0], point[1]))
    return finding('SMR-03', member, reason, result,
                   gap, related=[a, b])


def duplicate_check(a, b, settings):
    """Return a duplicate/overlap finding for an unordered member pair, or None."""
    if a['kind'] != b['kind'] or a['kind'] not in ('beam', 'column'):
        return None
    eps = settings['epsilon']
    forward = max(distance(a['start'], b['start']),
                  distance(a['end'], b['end']))
    reverse = max(distance(a['start'], b['end']),
                  distance(a['end'], b['start']))
    gap = min(forward, reverse)
    if gap <= settings['near']:
        av, bv = a.get('vertices', []), b.get('vertices', [])
        if not av or len(av) != len(bv):
            return finding('SMR-04', a, 'Coincident reference placement; '
                           'section equivalence is unresolved.', related=[b])
        # Geometry displacement prevents adjacent justified members matching.
        shape_gap = max(distance(x, y) for x, y in zip(sorted(av), sorted(bv)))
        if shape_gap > settings['near']:
            return None
        gap = max(gap, shape_gap)
        if a['type'] != b['type']:
            return finding('SMR-04', a, 'Coincident geometry across different '
                           'types; verify section equivalence.', related=[b])
        return finding('SMR-04', a,
                       'Exact duplicate.' if gap <= eps else 'Near duplicate.',
                       'Critical' if gap <= eps else severity(gap, eps),
                       gap, related=[b])
    # Check finite 3D collinearity, including vertical columns.
    delta = tuple(a['end'][i] - a['start'][i] for i in range(3))
    length = distance(a['start'], a['end'])
    if length <= eps:
        return None
    unit = tuple(v / length for v in delta)
    fractions = []
    for point in (b['start'], b['end']):
        along = sum((point[i] - a['start'][i]) * unit[i] for i in range(3))
        closest = tuple(a['start'][i] + along * unit[i] for i in range(3))
        if distance(point, closest) > eps:
            return None
        fractions.append(along)
    overlap = min(length, max(fractions)) - max(0.0, min(fractions))
    if overlap > eps:
        return finding('SMR-04', a, 'Collinear partial overlap; verify section '
                       'placement. Overlap {0:.8f} in.'.format(overlap),
                       value=overlap, related=[b], measurement='Overlap length')
    return None


def evaluate(records, grids, settings, expected=None, progress=None, relationships=None):
    """Evaluate selected checks over normalized whole-model records.

    Args:
        records: Eligible normalized beam, column, and wall records.
        grids: Eligible straight grid records.
        settings: Validated check settings in inches.
        expected: Optional column unique ID to expected grid-ID pair mapping.
        progress: Optional callback taking completed and total work counts.
            Raise Cancelled to abort; no complete results are then returned.

    Returns:
        A deterministic list of findings, including Pass and Not evaluated.
    """
    rows, expected = [], expected or {}
    relationships = relationships if relationships is not None else []
    records = sorted(records, key=lambda r: r['uid'])
    index = SpatialIndex(records)
    grid_pairs = []
    if 'SMR-03' in settings['checks']:
        for i, a in enumerate(grids):
            if progress:
                progress(i, len(grids))
            for b in grids[i + 1:]:
                point = intersection(a, b)
                if point is not None:
                    grid_pairs.append((point, a, b))
    for number, member in enumerate(records):
        if progress:
            progress(number, len(records))
        if member['kind'] == 'beam' and any(
                c in settings['checks'] for c in ('SMR-01', 'SMR-02')):
            rows.extend(r for r in endpoint_checks(member, index, settings, relationships)
                        if r['check'] in settings['checks'])
        if member['kind'] == 'beam' and 'SMR-05' in settings['checks']:
            attachment = member.get('bottom_attachment', {'state': 'Unresolved',
                'reason': 'Bottom-face work-plane evidence is unavailable.'})
            target = attachment.get('host')
            rel = relationship(member, target, attachment['state'],
                               work_plane=attachment)
            relationships.append(rel)
            rows.append(bind_result(finding('SMR-05', member,
                                             attachment.get('reason', attachment['state']),
                                             'Not evaluated' if attachment['state'] == 'Unresolved'
                                             else 'Information', related=[target] if target else []), rel))
        if member['kind'] == 'column' and 'SMR-03' in settings['checks']:
            rows.append(grid_check(member, grids, settings,
                                   expected.get(member['uid']), grid_pairs))
    if 'SMR-06' in settings['checks']:
        seen, involved = set(), set()
        for number, member in enumerate(records):
            if progress:
                progress(number, len(records))
            if member['kind'] != 'beam':
                continue
            for other in index.query_bounds(member['bounds']):
                key = tuple(sorted((member['uid'], other['uid'])))
                if other['kind'] != 'beam' or member['uid'] == other['uid'] or key in seen:
                    continue
                seen.add(key)
                rel = crossing_relationship(member, other, settings['epsilon'])
                if rel is None:
                    continue
                involved.update(key)
                relationships.append(rel)
                kind = rel['category']
                level = {'Interior Crossing': 'Error', 'Separated Plan Crossing': 'Information',
                         'Unresolved Plan Crossing': 'Not evaluated'}[kind]
                reason = ('Interior Crossing error: both reference spans cross internally and '
                          'local section vertical intervals overlap. Critical/Warning policy pending.'
                          if level == 'Error' else
                          'Plan crossing has separated physical elevations; no interior-intersection error.'
                          if level == 'Information' else
                          'Plan crossing found; local section elevations could not be resolved.')
                rows.append(bind_result(finding('SMR-06', member, reason, level,
                                                 rel['evidence']['vertical_gap'], related=[other],
                                                 measurement='Vertical separation'), rel,
                                        'Interior Crossing' if level == 'Error' else ''))
        for member in records:
            if member['kind'] == 'beam' and member['uid'] not in involved:
                rows.append(finding('SMR-06', member, 'No interior reference-span crossing detected.', 'Pass'))
    if 'SMR-04' in settings['checks']:
        seen = set()
        matched = set()
        for number, a in enumerate(records):
            if progress:
                progress(number, len(records))
            if a['kind'] not in ('beam', 'column'):
                continue
            for point in (a['start'], a['end']):
                for b in index.query(point, settings['near']):
                    key = tuple(sorted((a['uid'], b['uid'])))
                    if a['uid'] == b['uid'] or key in seen:
                        continue
                    seen.add(key)
                    result = duplicate_check(a, b, settings)
                    if result:
                        rows.append(result)
                        matched.update(key)
        for member in records:
            if member['kind'] in ('beam', 'column') and member['uid'] not in matched:
                if not member.get('vertices'):
                    rows.append(finding('SMR-04', member,
                                        'Original section placement is unavailable.',
                                        'Not evaluated'))
                else:
                    rows.append(finding('SMR-04', member,
                                        'No duplicate or partial overlap detected.',
                                        'Pass'))
    return rows


def assemble_report(records, rows, relationships):
    """Build one member registry and bind all results to relationship identities."""
    members = dict((r['uid'], member_record(r)) for r in records)
    for row in rows:
        if row['uid'] not in members:
            members[row['uid']] = member_record({'uid': row['uid'], 'id': row['id'],
                'name': row['member'], 'level': row['level'], 'extraction': 'Not evaluated'})
        if row.get('relationship_id'):
            continue
        related = row['related']
        rel = relationship(members[row['uid']], related[0] if related else None,
                           row.get('category') or row['check'], row['end'],
                           participants=[r['uid'] for r in related], value=row['value'],
                           measurement=row['measurement'])
        relationships.append(rel)
        bind_result(row, rel)
    unique = dict((r['relationship_id'], r) for r in relationships)
    return {'schema_version': SCHEMA_VERSION,
            'members': [members[k] for k in sorted(members)],
            'relationships': [unique[k] for k in sorted(unique)], 'rows': rows}
