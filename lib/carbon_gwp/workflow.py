# -*- coding: utf-8 -*-
"""Transform Carbon GWP schedule and worksheet data outside Revit.

The helpers preserve the worksheet naming and chart-data conventions used by
the Carbon GWP Pull command without importing pyRevit, Revit, or Excel COM
APIs. They accept ordinary Python values so their behavior can be tested outside
the host applications.
"""
from __future__ import print_function

import re


DEFAULT_SCHEDULE_NAMES = [
    'z_Project Material Takeoff',
    '2x Wood Wall Volume',
    'Composite Deck Volume',
]
DEFAULT_EXPORT_CONTAINER_PATH = (
    r'G:\_Carbon\10 Internal GWP Studies\Revit Material Quantification'
    r'\Team Carbon GWP Pull_Data Container.xlsx'
)
EXPORT_WORKSHEET_NAME = 'Export'


# COMPAT: IronPython provides ``unicode`` while CPython 3 provides ``str``.
try:
    TEXT_TYPES = (unicode,)
except NameError:
    TEXT_TYPES = (str,)


INVALID_WORKSHEET_CHARS = re.compile(r'[:\\/\?\*\[\]]')


def safe_text(value):
    """Return a stable text value for Excel and Revit values.

    Args:
        value: A value returned by Excel, Revit, or a caller.

    Returns:
        Text with missing values represented by an empty string and whole
        numbers represented without a trailing decimal point.
    """
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
    """Apply the schedule-title cleanup used by the existing Dynamo graph.

    Args:
        value: A selected schedule title or other value convertible to text.

    Returns:
        The trimmed title text after Dynamo-style ``=`` and ``)`` markers have
        been removed.
    """
    text = safe_text(value).strip()
    for marker in ('=', ')'):
        index = text.find(marker)
        if index >= 0:
            text = text[index + 1:]
    return text.strip()


def worksheet_name_for_schedule(schedule_title):
    """Return an Excel-safe name for a schedule export worksheet.

    Args:
        schedule_title: The visible Revit schedule title.

    Returns:
        A ``DYN Out -`` worksheet name with invalid characters replaced and
        the Excel 31-character limit enforced.
    """
    cleaned = clean_schedule_title(schedule_title)
    if not cleaned:
        cleaned = 'Schedule'
    name = 'DYN Out - {}'.format(cleaned)
    name = INVALID_WORKSHEET_CHARS.sub('_', name).strip("'").strip()
    if not name:
        name = 'DYN Out - Schedule'
    return name[:31]


def uniquify_worksheet_names(names):
    """Return case-insensitively unique worksheet names within Excel limits.

    Args:
        names: An iterable of proposed worksheet names.

    Returns:
        A list of names no longer than 31 characters. Duplicate names receive
        a numeric suffix while preserving that limit.
    """
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
    """Convert nested values to a rectangular grid of text.

    Args:
        values: An iterable of row iterables, or ``None``.

    Returns:
        A list of text rows padded with empty strings to a shared width.
    """
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


def has_exportable_cells(grid):
    """Return whether a schedule grid contains at least one cell.

    An empty grid indicates that a required schedule could not provide table
    data. A row containing blank cell text is still a valid table row.
    """
    for row in grid or []:
        if row:
            return True
    return False
