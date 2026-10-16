"""Host-independent Model Checker rules and report rows.

All coordinates and discrepancies are in inches. Host extraction supplies
original solid face equations; no Revit objects are imported here.
"""

import math

from steel_model_review.geometry import (
    SpatialIndex, distance, intersection, line_distance, projection,
    section_interval,
)

CHECKS = ('SMR-01', 'SMR-02', 'SMR-03', 'SMR-04')
DEFAULTS = {'epsilon': 0.000001, 'search': 12.0, 'near': 0.0625,
            'checks': CHECKS, 'grid_mode': 'Nearest intersection'}


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
            end='', related=None):
    """Build a plain result record with separate evaluation and review state."""
    related = [dict((key, r[key]) for key in ('uid', 'id', 'name') if key in r)
               for r in (related or [])]
    return {'check': check, 'uid': member['uid'], 'id': member['id'],
            'member': member.get('name', str(member['id'])),
            'level': member.get('level', ''), 'severity': level,
            'value': value, 'end': end, 'reason': reason,
            'related': related, 'status': 'Open', 'exception': '',
            'key': (check, member['uid'], str(end),
                    tuple(sorted(r['uid'] for r in related)))}


def _vertical(member, support, point, target, epsilon):
    own = section_interval(member, point, epsilon)
    if own is None:
        return None, 'Beam local section boundaries could not be resolved.'
    if support['kind'] == 'column':
        low, high = support['bounds'][0][2], support['bounds'][1][2]
        gap = max(low - own[1], own[0] - high, 0.0)
        return gap, 'Beam end versus finite column vertical extent.'
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


def _collinear(a, b):
    """Identify framing along the same plan direction with unresolved support role."""
    if a['kind'] != 'beam' or b['kind'] != 'beam':
        return False
    u = tuple(a['end'][i] - a['start'][i] for i in (0, 1))
    v = tuple(b['end'][i] - b['start'][i] for i in (0, 1))
    denom = distance(u, (0, 0)) * distance(v, (0, 0))
    return bool(denom and abs(sum(u[i] * v[i] for i in (0, 1))) /
                denom > 0.999999)


def endpoint_checks(member, index, settings):
    """Return endpoint and vertical results, preserving unresolved evidence."""
    rows = []
    eps, search = settings['epsilon'], settings['search']
    for end, point in enumerate((member['start'], member['end'])):
        candidates = []
        for support in index.query(point, search):
            if support['uid'] == member['uid']:
                continue
            target, ambiguous = _target(
                point, support, member['end'] if end == 0 else member['start'])
            if target is None or distance(point[:2], target) > search:
                continue
            lo, hi = support['bounds']
            own = section_interval(member, point, eps)
            zlo, zhi = own if own else (point[2], point[2])
            if zlo - hi[2] > search or lo[2] - zhi > search:
                continue
            candidates.append((support, target, ambiguous or
                               _collinear(member, support)))
        if not candidates:
            rows.append(finding('SMR-01', member,
                                'No eligible support within {0:g} in search.'
                                .format(search), 'Critical', end=end))
        elif len(candidates) > 1 or candidates[0][2]:
            rows.append(finding('SMR-01', member,
                                'Ambiguous support or end-to-end relationship.',
                                end=end, related=[c[0] for c in candidates]))
        else:
            support, target, _ambiguous = candidates[0]
            gap = distance(point[:2], target)
            dx, dy = (target[i] - point[i] for i in (0, 1))
            vx = member['end'][0] - member['start'][0]
            vy = member['end'][1] - member['start'][1]
            length = math.sqrt(vx * vx + vy * vy)
            outward = -1 if end == 0 else 1
            along = outward * (dx * vx + dy * vy) / length
            lateral = (dx * vy - dy * vx) / length
            reason = ('Endpoint plan miss; along {0:+.8f} in '
                      '(positive shortfall), lateral {1:+.8f} in.'
                      .format(along, lateral))
            rows.append(finding('SMR-01', member, reason,
                                severity(gap, eps), gap, end, [support]))
            value, reason = _vertical(member, support, point, target, eps)
            rows.append(finding('SMR-02', member, reason,
                                severity(value, eps) if value is not None else
                                'Not evaluated', value, end, [support]))
            continue
        rows.append(finding('SMR-02', member,
                            'Support relationship unresolved; see SMR-01.',
                            'Not evaluated', end=end))
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
    reason = ('Off-grid column: review intended location. {0} / {1}; '
              'line offsets {2:.8f}, {3:.8f} in; target ({4:.8f}, {5:.8f}) in.'
              .format(a['name'], b['name'], line_distance(member['start'], a),
                      line_distance(member['start'], b), point[0], point[1]))
    return finding('SMR-03', member, reason, severity(gap, settings['epsilon']),
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
                       value=overlap, related=[b])
    return None


def evaluate(records, grids, settings, expected=None, progress=None):
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
            rows.extend(r for r in endpoint_checks(member, index, settings)
                        if r['check'] in settings['checks'])
        if member['kind'] == 'column' and 'SMR-03' in settings['checks']:
            rows.append(grid_check(member, grids, settings,
                                   expected.get(member['uid']), grid_pairs))
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
