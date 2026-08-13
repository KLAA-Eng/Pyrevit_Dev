"""Pure comparison rules for Revit element fingerprints."""


def compare_fingerprints(baseline, current):
    """Classify fingerprints without changing either input mapping.

    Values may be legacy two-item tuples, three-item tuples with a content
    key, or mappings containing ``type``, ``location``, and ``content``.
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
    baseline_values = _fingerprint_values(baseline_fingerprint)
    current_values = _fingerprint_values(current_fingerprint)
    reasons = []
    if baseline_values['type'] != current_values['type']:
        reasons.append('type')
    if baseline_values['location'] != current_values['location']:
        reasons.append('location')
    if baseline_values['content'] != current_values['content']:
        reasons.append('content')
    return reasons


def _fingerprint_values(fingerprint):
    """Normalize supported fingerprint forms without changing the input."""
    if isinstance(fingerprint, dict):
        return {
            'type': fingerprint.get('type'),
            'location': fingerprint.get('location'),
            'content': fingerprint.get('content'),
        }
    return {
        'type': fingerprint[0] if len(fingerprint) > 0 else None,
        'location': fingerprint[1] if len(fingerprint) > 1 else None,
        'content': fingerprint[2] if len(fingerprint) > 2 else None,
    }
