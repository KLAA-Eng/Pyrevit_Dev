# -*- coding: utf-8 -*-
"""Fictional, host-independent data and interactions for Gallery previews."""
from __future__ import unicode_literals

import math
import re


STATES = ('Normal', 'Empty', 'Error', 'Disabled', 'Long content')
LONG_NAME = ('S101 - Coordination plan for the north and south structural '
             'framing areas, transfer levels, and equipment supports')


def validate_state(state):
    if state not in STATES:
        raise ValueError('Unsupported preview state: {}'.format(state))
    return state


class PreviewItem(object):
    """Simple WPF-bindable row; selection is confined to the preview instance."""
    def __init__(self, name, checked=False, value='', category='Sample'):
        self.Name = name
        self.IsChecked = checked
        self.IsSelected = checked
        self.DisplayValue = value
        self.Category = category


def selection_items(state='Normal'):
    validate_state(state)
    if state == 'Empty':
        return []
    names = ['A101 - Floor Plan', 'A201 - Building Section',
             'S101 - Foundation Plan', 'M101 - HVAC Plan']
    if state == 'Long content':
        names = ['{} - {:02d}'.format(LONG_NAME, i) for i in range(1, 31)]
    return [PreviewItem(name, i == 0 and state != 'Error')
            for i, name in enumerate(names)]


def recall_items(state='Normal'):
    validate_state(state)
    if state == 'Empty':
        return []
    rows = [('Mark', 'A-101'), ('Comments', 'Coordination review'),
            ('Phase Created', 'Existing'), ('Detail Level', 'Fine')]
    if state == 'Long content':
        rows = [('Parameter {:02d} - {}'.format(i, LONG_NAME), LONG_NAME)
                for i in range(1, 31)]
    return [PreviewItem(name, state != 'Error', value)
            for name, value in rows]


def filtered_items(items, text='', regex=False):
    """Return visible rows and an optional validation message."""
    if not text:
        return list(items), ''
    if regex:
        try:
            pattern = re.compile(text, re.IGNORECASE)
        except re.error:
            return list(items), 'Preview: invalid regular expression.'
        return [item for item in items if pattern.search(item.Name)
                or pattern.search(item.DisplayValue)], ''
    text = text.lower()
    return [item for item in items if text in item.Name.lower()
            or text in item.DisplayValue.lower()], ''


def set_checked(items, value=None, toggle=False):
    for item in items:
        checked = not item.IsChecked if toggle else bool(value)
        item.IsChecked = checked
        item.IsSelected = checked


def rename_samples(names, find='', replace='', prefix='', suffix='', action='Rename'):
    """Plan exact sample-name changes without invoking a production command."""
    names = list(names)
    if action == 'Rename' and replace and not find:
        return names, 'Enter Find text when Replace is supplied.'
    if action == 'Uppercase':
        targets = [name.upper() for name in names]
    elif action == 'Lowercase':
        targets = [name.lower() for name in names]
    elif action == 'Rename':
        targets = [prefix + name.replace(find, replace) + suffix for name in names]
    else:
        raise ValueError('Unsupported sample action: {}'.format(action))
    if len(set(targets)) != len(targets):
        return names, 'Sample target names collide; change the rename fields.'
    return targets, ''


def naming_values(state='Normal', numbers=False):
    """Seed visible fields as well as sample outcomes for naming-form states."""
    validate_state(state)
    if state == 'Empty':
        return dict((key, '') for key in ('find', 'replace', 'prefix', 'suffix'))
    values = ({'find': 'A', 'replace': 'S', 'prefix': 'Sample-', 'suffix': '-R1'}
              if numbers else {'find': 'Office', 'replace': 'Studio',
                               'prefix': 'Sample - ', 'suffix': ' - Review'})
    if state == 'Error':
        values['find'] = ''
    elif state == 'Long content':
        values = {'find': LONG_NAME, 'replace': 'Revised - ' + LONG_NAME,
                  'prefix': LONG_NAME + ' - ', 'suffix': ' - ' + LONG_NAME}
    return values


def parse_offset(text):
    """Validate complete decimal input, including pasted values and negatives."""
    try:
        value = float(text)
    except (TypeError, ValueError):
        raise ValueError('Enter a finite decimal offset, such as 15 or -2.5.')
    if math.isnan(value) or math.isinf(value):
        raise ValueError('Enter a finite decimal offset, such as 15 or -2.5.')
    return value


def alert_message(state='Normal'):
    validate_state(state)
    if state == 'Empty':
        return ''
    if state == 'Error':
        return 'Sample validation failed. Correct the fictional input and try again.'
    if state == 'Long content':
        return '\n\n'.join('Sample issue {}: {}'.format(i, LONG_NAME)
                            for i in range(1, 9))
    return 'Fictional preview data. Actions affect this preview only.'


def review_items(state='Normal'):
    """Bind the optional Model Checker view without running any checks."""
    validate_state(state)
    if state == 'Empty':
        return []
    rows = []
    for index, severity in enumerate(('Critical', 'Error', 'Warning', 'Information')):
        item = PreviewItem('Sample member {}'.format(index + 1))
        item.Severity = severity
        item.Check = 'Column grid alignment' if index % 2 else 'Beam support'
        item.Category = 'Sample relationship'
        item.Member = item.Name
        item.End = 'A'
        item.Level = 'Level 01'
        item.Offset = '0.50 in'
        item.Measurement = 'Sample perpendicular distance'
        item.Value = 0.5
        item.Related = 'Sample support {}'.format(index + 1)
        item.Status = 'Open'
        item.Reason = LONG_NAME if state == 'Long content' else 'Fictional finding for visual review.'
        rows.append(item)
    return rows
