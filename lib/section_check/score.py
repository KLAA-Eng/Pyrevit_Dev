"""Approximate match percentage between a marker's cut and its referenced detail.

Model-to-model (the reference is a live section elsewhere): each element cut
at the marker is paired with the best unpaired element in the reference cut.
A pair needs the same group; it scores 1.0 for the same type, 0.75 for a
shared size or material, 0.5 for the group alone, then loses weight for a
different orientation to the cut or a different side. SIM accepts size and
type differences (0.9 minimum). OH mirrors the reference's sides first. The
percentage is 2 x paired score / (elements here + elements in the reference),
so missing and extra elements both lower it.

Model-to-drafting (the reference is a drafting view): each element here earns
credit when the detail names its size, material, or group; groups the detail
names that are not modeled here count against the match. Hand is not checked.

The score is a review guide, not a pass/fail.
"""

from __future__ import division

from .conditions import mirrored


SAME_TYPE, SHARED_SIZE, SAME_GROUP = 1.0, 0.75, 0.5
SIM_FLOOR = 0.9
ORIENT_FACTOR, SIDE_FACTOR = 0.6, 0.8
DETAIL_SIZE, DETAIL_MATERIAL, DETAIL_GROUP = 1.0, 0.8, 0.6
SIM_DETAIL_MATERIAL, SIM_DETAIL_GROUP = 1.0, 0.8
HAND_GAP = 10.0
LIKELY_MATCH, REVIEW = 80.0, 50.0


def rating(percent):
    if percent is None:
        return "Can't tell"
    if percent >= LIKELY_MATCH:
        return 'Likely match'
    return 'Review' if percent >= REVIEW else 'Likely mismatch'


def pair_score(here, ref, similar=False):
    if here['group'] != ref['group']:
        return 0.0
    if here['label'] == ref['label']:
        score = SAME_TYPE
    elif here['sizes'] & ref['sizes'] or here['materials'] & ref['materials']:
        score = SHARED_SIZE
    else:
        score = SAME_GROUP
    if similar:
        score = max(score, SIM_FLOOR)
    if here['orient'] and ref['orient'] and here['orient'] != ref['orient']:
        score *= ORIENT_FACTOR
    if here['side'] and ref['side'] and here['side'] != ref['side']:
        score *= SIDE_FACTOR
    return score


def _percent(total, count):
    return round(100.0 * total / count, 1) if count else None


def match_conditions(here, ref, similar=False):
    """{'percent', 'pairs': [(here, ref, score)], 'only_here', 'only_ref'}
    from the best greedy pairing."""
    candidates = sorted(((pair_score(a, b, similar), i, j)
                         for i, a in enumerate(here) for j, b in enumerate(ref)),
                        key=lambda c: (-c[0], c[1], c[2]))
    used_here, used_ref, pairs = set(), set(), []
    for score, i, j in candidates:
        if score <= 0 or i in used_here or j in used_ref:
            continue
        used_here.add(i)
        used_ref.add(j)
        pairs.append((here[i], ref[j], score))
    total = 2 * sum(p[2] for p in pairs)
    return {'percent': _percent(total, len(here) + len(ref)), 'pairs': pairs,
            'only_here': [c for i, c in enumerate(here) if i not in used_here],
            'only_ref': [c for j, c in enumerate(ref) if j not in used_ref]}


def _labels(conditions):
    return ', '.join('%s %s' % (c['group'], c['label']) for c in conditions)


def compare_sections(here, ref, similar=False, opposite=False, hand_known=True):
    """Match of the marker's cut (here) against a live referenced section's cut
    (ref), with the SIM / OH notes found beside the marker. hand_known is False
    when the marker's look direction could not be read; the better of the two
    hands is then used."""
    drawn = mirrored(ref) if opposite else ref
    result = match_conditions(here, drawn, similar)
    other = match_conditions(here, mirrored(drawn), similar)
    notes = []
    if not here:
        notes.append('Nothing modeled at the marker')
    if not ref:
        notes.append("Nothing modeled in the referenced section's cut")
    gap = (other['percent'] or 0) - (result['percent'] or 0)
    if not hand_known:
        if gap > 0:
            result = other
        if abs(gap) >= HAND_GAP:
            notes.append('Hand not checked: marker direction unknown')
    elif gap >= HAND_GAP:
        notes.append('Matches better mirrored: %s' % (
            'OH note may be wrong' if opposite else 'OH may be missing'))
    differ = [p for p in result['pairs'] if p[0]['label'] != p[1]['label']]
    if differ and not similar:
        notes.append('%d size/type difference(s): add SIM or check the reference (%s)' % (
            len(differ), '; '.join('%s vs %s' % (p[0]['label'], p[1]['label'])
                                   for p in differ)))
    if result['only_here']:
        notes.append('Only at marker: ' + _labels(result['only_here']))
    if result['only_ref']:
        notes.append('Only in reference: ' + _labels(result['only_ref']))
    result['notes'] = notes
    result['rating'] = rating(result['percent'])
    return result


def compare_detail(here, detail, similar=False, opposite=False):
    """Match of the marker's cut (here) against a drafting detail's content
    from conditions.detail_content."""
    credits, loose, unmatched = [], [], []
    for cond in here:
        if cond['sizes'] & detail['sizes']:
            credit = DETAIL_SIZE
        elif cond['materials'] & detail['materials']:
            credit = SIM_DETAIL_MATERIAL if similar else DETAIL_MATERIAL
        elif cond['group'] in detail['groups']:
            credit = SIM_DETAIL_GROUP if similar else DETAIL_GROUP
        else:
            credit = 0.0
        credits.append(credit)
        if credit == 0:
            unmatched.append(cond)
        elif credit < 1:
            loose.append(cond)
    missing = sorted(detail['groups'] - set(c['group'] for c in here))
    notes = []
    named = detail['groups'] or detail['sizes'] or detail['materials']
    if not named:
        notes.append('Detail components and notes name nothing recognizable')
    if not here:
        notes.append('Nothing modeled at the marker')
    if loose and not similar:
        notes.append('%d element(s) match the detail only loosely (size not named): %s' % (
            len(loose), _labels(loose)))
    if unmatched:
        notes.append('Not named in detail: ' + _labels(unmatched))
    if missing:
        notes.append('Detail shows %s, not modeled at marker' % ', '.join(missing))
    if opposite:
        notes.append('OH not checked against a drafting view')
    percent = _percent(sum(credits), len(here) + len(missing)) if named else None
    return {'percent': percent, 'rating': rating(percent), 'notes': notes}
