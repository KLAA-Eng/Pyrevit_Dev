"""Pure comparison rules for Revit element fingerprints."""


def compare_fingerprints(baseline, current):
    """Classify fingerprints without changing either input mapping.

    Each mapping value is a two-item tuple: ``(type_key, location_key)``.
    """
    result = {
        'new': [],
        'modified': [],
        'unchanged': [],
        'deleted': [],
        'reasons': {},
    }
    baseline_ids = set(baseline.keys())
    current_ids = set(current.keys())

    result['new'] = sorted(current_ids - baseline_ids)
    result['deleted'] = sorted(baseline_ids - current_ids)

    for unique_id in sorted(current_ids & baseline_ids):
        reasons = _change_reasons(baseline[unique_id], current[unique_id])
        if reasons:
            result['modified'].append(unique_id)
            result['reasons'][unique_id] = reasons
        else:
            result['unchanged'].append(unique_id)
    return result


def _change_reasons(baseline_fingerprint, current_fingerprint):
    """Return stable labels for the fingerprint fields that changed."""
    reasons = []
    if baseline_fingerprint[0] != current_fingerprint[0]:
        reasons.append('type')
    if baseline_fingerprint[1] != current_fingerprint[1]:
        reasons.append('location')
    return reasons
