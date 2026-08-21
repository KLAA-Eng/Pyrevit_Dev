# -*- coding: utf-8 -*-
"""Host-independent helpers for the Concrete Mix schedule header import."""
from __future__ import print_function

import re


CELL_REF_RE = re.compile(r'^([A-Za-z]+)([0-9]+)$')
MIX_HISTORY_ALIASES = {
    'element': 'element',
    'elements': 'element',
    "fcpsi": 'strength',
    "fc": 'strength',
    "f'cpsi": 'strength',
    "f'c": 'strength',
    'cementtype': 'cement_type',
    'maxwc': 'max_wc',
    'maxw/c': 'max_wc',
    'maxagg': 'max_agg',
    'aircontent': 'air_content',
    'aircontent%': 'air_content',
    'slump': 'slump',
    'f': 'freeze_thaw',
    's': 'sulfate',
    'w': 'water',
    'c': 'corrosion',
}


def column_name_to_index(column_name):
    """Return a 1-based Excel column index for a column name such as A or AA."""
    if not column_name:
        raise ValueError('Column name is required.')
    index = 0
    for char in column_name.upper():
        if char < 'A' or char > 'Z':
            raise ValueError('Invalid Excel column name: {}'.format(column_name))
        index = (index * 26) + (ord(char) - ord('A') + 1)
    return index


def parse_cell_ref(cell_ref):
    """Return a 1-based (row, column) tuple from an Excel cell reference."""
    match = CELL_REF_RE.match(str(cell_ref).strip())
    if not match:
        raise ValueError('Invalid Excel cell reference: {}'.format(cell_ref))
    return int(match.group(2)), column_name_to_index(match.group(1))


def parse_a1_range(range_address):
    """Return 1-based (start_row, start_col, end_row, end_col)."""
    if not range_address:
        raise ValueError('Excel range is required.')
    parts = str(range_address).replace('$', '').split(':')
    if len(parts) == 1:
        start_row, start_col = parse_cell_ref(parts[0])
        return start_row, start_col, start_row, start_col
    if len(parts) != 2:
        raise ValueError('Invalid Excel range: {}'.format(range_address))
    start_row, start_col = parse_cell_ref(parts[0])
    end_row, end_col = parse_cell_ref(parts[1])
    if end_row < start_row or end_col < start_col:
        raise ValueError('Excel range must read top-left to bottom-right: {}'.format(range_address))
    return start_row, start_col, end_row, end_col


def range_size(range_address):
    start_row, start_col, end_row, end_col = parse_a1_range(range_address)
    return end_row - start_row + 1, end_col - start_col + 1


def safe_cell_text(value):
    """Convert Excel COM values into text suitable for a Revit header cell."""
    if value is None:
        return ''
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


def normalize_header_name(value):
    text = safe_cell_text(value).lower()
    text = text.replace('(%)', '%')
    text = re.sub(r'[\s_\-()]', '', text)
    return text


def element_match_key(value):
    text = safe_cell_text(value).lower()
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'[^a-z0-9]+', '', text)
    return text


def mix_history_column_map(headers):
    mapping = {}
    for index, header in enumerate(headers):
        key = normalize_header_name(header)
        mapped_name = MIX_HISTORY_ALIASES.get(key)
        if mapped_name:
            mapping[mapped_name] = index
    return mapping


def mapped_value(row, column_map, name):
    index = column_map.get(name)
    if index is None or index >= len(row):
        return ''
    return safe_cell_text(row[index])


def build_mix_history_schedule_grid(headers, rows, max_mix_rows):
    """Map tblMixHistory data rows into the paired-row Revit header layout."""
    column_map = mix_history_column_map(headers)
    required = [
        'element',
        'strength',
        'cement_type',
        'max_wc',
        'max_agg',
        'air_content',
        'slump',
        'freeze_thaw',
        'sulfate',
        'water',
        'corrosion',
    ]
    missing = [name for name in required if name not in column_map]
    if missing:
        raise ValueError(
            'tblMixHistory is missing mapped columns: {}. Detected headers: {}'.format(
                ', '.join(missing),
                ', '.join([safe_cell_text(header) for header in headers])))

    max_data_rows = max_mix_rows // 2
    if len(rows) > max_data_rows:
        raise ValueError(
            'tblMixHistory has {} data rows, but the Revit template mix region has room for {} rows.'.format(
                len(rows), max_data_rows))

    grid = []
    for row in rows:
        top = [''] * 11
        bottom = [''] * 11
        top[0] = mapped_value(row, column_map, 'element')
        top[2] = mapped_value(row, column_map, 'strength')
        top[3] = mapped_value(row, column_map, 'cement_type')
        top[4] = mapped_value(row, column_map, 'max_wc')
        top[5] = mapped_value(row, column_map, 'max_agg')
        top[6] = mapped_value(row, column_map, 'air_content')
        top[7] = mapped_value(row, column_map, 'slump')
        top[8] = mapped_value(row, column_map, 'freeze_thaw')
        top[9] = mapped_value(row, column_map, 'corrosion')
        bottom[8] = mapped_value(row, column_map, 'sulfate')
        bottom[9] = mapped_value(row, column_map, 'water')
        grid.append(top)
        grid.append(bottom)
    return normalize_grid(grid, max_mix_rows, 11), column_map


def normalize_grid(values, row_count=None, column_count=None):
    """Return a rectangular grid of strings from nested Excel values."""
    if values is None:
        rows = []
    else:
        rows = [[safe_cell_text(cell) for cell in row] for row in values]

    if row_count is None:
        row_count = len(rows)
    if column_count is None:
        column_count = max([len(row) for row in rows] or [0])

    normalized = []
    for row_index in range(row_count):
        source_row = rows[row_index] if row_index < len(rows) else []
        normalized.append([
            source_row[column_index] if column_index < len(source_row) else ''
            for column_index in range(column_count)
        ])
    return normalized


def non_empty_cell_count(grid):
    return sum(1 for row in grid for value in row if value)


def build_write_plan(grid, first_row, first_column):
    """Return dictionaries with absolute Revit header coordinates and text."""
    plan = []
    for row_offset, row in enumerate(grid):
        for column_offset, value in enumerate(row):
            plan.append({
                'row': first_row + row_offset,
                'column': first_column + column_offset,
                'row_offset': row_offset,
                'column_offset': column_offset,
                'text': value,
            })
    return plan
