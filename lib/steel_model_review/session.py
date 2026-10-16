"""Serializable session report and intentional-exception handling."""

import hashlib
import json


def signature(value):
    """Return a deterministic digest of JSON-compatible snapshot evidence."""
    payload = json.dumps(value, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def row_key(row):
    """Return a stable string key regardless of JSON tuple/list round trips."""
    return json.dumps(row['key'], sort_keys=True)


def carry_exceptions(rows, previous, stamp):
    """Carry acceptance only when the complete model/settings stamp matches.

    Args:
        rows: New run result records, updated in place.
        previous: Prior complete snapshot, or None.
        stamp: Digest of settings, model scope, and all relevant element versions.

    Returns:
        None. Model changes conservatively invalidate all previous acceptance.
    """
    if not previous or previous.get('stamp') != stamp:
        return
    accepted = dict((row_key(r), r) for r in previous['rows']
                    if r['status'] == 'Accepted exception')
    for row in rows:
        prior = accepted.get(row_key(row))
        if prior:
            row['status'] = 'Accepted exception'
            row['exception'] = prior['exception']
