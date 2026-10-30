"""Explicit preview variants and session-only choices; no host imports."""
from __future__ import unicode_literals


def variants(entry):
    return entry.get('variants') or [dict(id=entry['id'], label='Default')]


def variant_labels(entry):
    return ', '.join(item['label'] for item in variants(entry))


def preview_launcher(entry, variant_id=None):
    choices = variants(entry)
    identity = variant_id or choices[0]['id']
    choice = next((item for item in choices if item['id'] == identity), None)
    if choice is None:
        raise ValueError('Unsupported preview variant: {}'.format(identity))
    launcher = dict(entry)
    launcher.pop('variants', None)
    launcher['id'] = identity
    if choice['label'] != 'Default':
        launcher['title'] = '{} - {}'.format(entry['title'], choice['label'])
    return launcher


def preview_entries(entries):
    """Expand reviewed family variants for exhaustive validation, not discovery."""
    for entry in entries:
        for choice in variants(entry):
            yield preview_launcher(entry, choice['id'])


class PreviewMemory(object):
    def __init__(self):
        self._choices = {}

    def get(self, entry):
        choices = variants(entry)
        identity, state = self._choices.get(entry['id'], (choices[0]['id'], 'Normal'))
        if identity not in [item['id'] for item in choices]:
            identity = choices[0]['id']
        states = entry['states']
        if state not in states:
            state = 'Normal' if 'Normal' in states else (states[0] if states else None)
        return identity, state

    def set(self, entry, variant_id, state):
        preview_launcher(entry, variant_id)
        if state not in entry['states'] and not (state is None and not entry['states']):
            raise ValueError('Unsupported preview state: {}'.format(state))
        self._choices[entry['id']] = (variant_id, state)
