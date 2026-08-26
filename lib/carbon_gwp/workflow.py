# -*- coding: utf-8 -*-
"""Host-independent helpers for the Carbon GWP Pull prototype."""
from __future__ import print_function

import re


DEFAULT_SCHEDULE_NAMES = [
    'Material Classfication, Area, and Volume',
    '2x Wood Wall Volume',
    'Composite Deck Volume',
]
DEFAULT_EXPORT_CONTAINER_PATH = (
    r'G:\_Carbon\10 Internal GWP Studies\Revit Material Quantification'
    r'\Team Carbon GWP Pull_Data Container.xlsx'
)
DEFAULT_POST_PROCESSING_PATH = (
    r'G:\_Carbon\10 Internal GWP Studies\Revit Material Quantification'
    r'\Revit Material and GWP Quantification Post-Processing_v2.xlsx'
)
EXPORT_WORKSHEET_NAME = 'Export'
CARBON_PIE_FAMILY_NAME = 'Carbon Pie.JMP'


try:
    TEXT_TYPES = (unicode,)
except NameError:
    TEXT_TYPES = (str,)


INVALID_WORKSHEET_CHARS = re.compile(r'[:\\/\?\*\[\]]')


def safe_text(value):
    """Return a stable text value for Excel/Revit COM values."""
    if value is None:
        return ''
    if isinstance(value, TEXT_TYPES):
        return value
    try:
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
    except Exception:
        pass
    text = str(value)
    if text.endswith('.0'):
        try:
            return str(int(float(text)))
        except Exception:
            pass
    return text


def clean_schedule_title(value):
    """Match the Dynamo graph's visible cleanup of selected schedule titles."""
    text = safe_text(value).strip()
    for marker in ('=', ')'):
        index = text.find(marker)
        if index >= 0:
            text = text[index + 1:]
    return text.strip()


def worksheet_name_for_schedule(schedule_title):
    """Return an Excel-safe worksheet name for a schedule export."""
    cleaned = clean_schedule_title(schedule_title)
    if not cleaned:
        cleaned = 'Schedule'
    name = 'DYN Out - {}'.format(cleaned)
    name = INVALID_WORKSHEET_CHARS.sub('_', name).strip("'").strip()
    if not name:
        name = 'DYN Out - Schedule'
    return name[:31]


def uniquify_worksheet_names(names):
    """Return Excel-safe unique worksheet names preserving the 31-char limit."""
    used = set()
    result = []
    for name in names:
        base = safe_text(name)[:31] or 'Sheet'
        candidate = base
        index = 2
        while candidate.lower() in used:
            suffix = ' ({})'.format(index)
            candidate = base[:31 - len(suffix)] + suffix
            index += 1
        used.add(candidate.lower())
        result.append(candidate)
    return result


def normalize_grid(values):
    """Convert nested values to a rectangular text grid."""
    rows = []
    max_columns = 0
    for row in values or []:
        normalized = [safe_text(cell) for cell in row]
        rows.append(normalized)
        if len(normalized) > max_columns:
            max_columns = len(normalized)
    for row in rows:
        while len(row) < max_columns:
            row.append('')
    return rows


def parameter_value_pairs_from_export_rows(rows):
    """Return parameter/value pairs from Excel Export worksheet rows.

    The Dynamo graph imports the sheet, transposes it, then uses index 0 for
    parameter names and index 1 for values. That is equivalent to reading the
    first two Excel columns row by row.
    """
    pairs = []
    skipped = []
    for row_index, row in enumerate(rows or [], start=1):
        parameter_name = safe_text(row[0] if len(row) > 0 else '').strip()
        value = safe_text(row[1] if len(row) > 1 else '')
        if not parameter_name:
            skipped.append({
                'row': row_index,
                'reason': 'blank parameter name',
                'value': value,
            })
            continue
        pairs.append({
            'row': row_index,
            'parameter_name': parameter_name,
            'value': value,
        })
    return pairs, skipped


def validate_parameter_value_pairs(pairs):
    """Classify duplicate or empty parameter/value pairs before Revit writes."""
    valid = []
    skipped = []
    seen = set()
    for pair in pairs or []:
        name = safe_text(pair.get('parameter_name')).strip()
        if not name:
            skipped.append(dict(pair, reason='blank parameter name'))
            continue
        if name.lower() in seen:
            skipped.append(dict(pair, reason='duplicate parameter name'))
            continue
        seen.add(name.lower())
        valid.append({
            'row': pair.get('row'),
            'parameter_name': name,
            'value': safe_text(pair.get('value')),
        })
    return valid, skipped

