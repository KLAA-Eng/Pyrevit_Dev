# -*- coding: utf-8 -*-
"""Host-independent helpers for the Concrete Mix schedule header import."""
from __future__ import print_function

import re
from fractions import Fraction


CELL_REF_RE = re.compile(r'^([A-Za-z]+)([0-9]+)$')
SUPERSCRIPT_DIGITS = {
    '⁰': '0',
    '¹': '1',
    '²': '2',
    '³': '3',
    '⁴': '4',
    '⁵': '5',
    '⁶': '6',
    '⁷': '7',
    '⁸': '8',
    '⁹': '9',
}
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
TEMPLATE_ELEMENTS = [
    'Drilled Piers',
    'Pier Caps',
    'Top of Piers in contact with concrete columns & pilasters',
    'Footings',
    'Grade beams, Tiebeams, Stem Walls',
    'Foundation Walls not integral to pilasters & columns',
    'Foundation Walls integral to pilasters or supporting concrete columns',
    'Interior Slab on Grade (SOG)',
    'Slab on Metal Deck',
    'Exterior Slab on Grade, Garage Slab on Grade',
    'Columns',
    'Core, Shear, and Bearing Walls',
    'PT Slab, and Non-PT Structural Slabs, Beams, and Joists',
    'Garage Slabs/Beams and Slabs exposed to DeIcing Chemicals',
    'Other ⁵',
]


def template_element_records():
    records = []
    for index, element in enumerate(TEMPLATE_ELEMENTS):
        records.append({
            'index': index,
            'element': element,
            'key': element_match_key(element),
        })
    return records


def template_element_key_map():
    return dict((record['key'], record) for record in template_element_records())


def classify_template_reconciliation(excel_pairs, current_pairs):
    """Classify Excel/header pairs against the built-in template element list."""
    template_by_key = template_element_key_map()
    current_by_key = dict(
        (pair.get('key'), pair)
        for pair in current_pairs
        if pair.get('key') in template_by_key
    )
    excel_by_key = {}
    duplicate_excel = []
    unknown_excel = []
    for pair in excel_pairs:
        key = pair.get('key')
        if not key:
            continue
        if key not in template_by_key:
            unknown_excel.append(pair)
            continue
        if key in excel_by_key:
            duplicate_excel.append(pair)
            continue
        excel_by_key[key] = pair

    known_excel = []
    to_update = []
    to_add = []
    for record in template_element_records():
        key = record['key']
        pair = excel_by_key.get(key)
        if not pair:
            continue
        known_excel.append(pair)
        if key in current_by_key:
            to_update.append(pair)
        else:
            to_add.append(pair)

    missing_from_excel = []
    for record in template_element_records():
        key = record['key']
        if key in current_by_key and key not in excel_by_key:
            missing_from_excel.append(current_by_key[key])

    return {
        'known_excel': known_excel,
        'to_update': to_update,
        'to_add': to_add,
        'missing_from_excel': missing_from_excel,
        'unknown_excel': unknown_excel,
        'duplicate_excel': duplicate_excel,
    }


def insertion_anchor_offset(template_key, current_pairs, notes_start_offset):
    """Return the row offset before which a missing template pair should be inserted."""
    template_records = template_element_records()
    template_index_by_key = dict((record['key'], record['index']) for record in template_records)
    target_index = template_index_by_key.get(template_key)
    if target_index is None:
        return notes_start_offset

    current_by_key = dict(
        (pair.get('key'), pair)
        for pair in current_pairs
        if pair.get('key') in template_index_by_key
    )
    for record in template_records[target_index + 1:]:
        next_pair = current_by_key.get(record['key'])
        if next_pair:
            return next_pair.get('row_offset', notes_start_offset)
    return notes_start_offset


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


def format_fractional_inches(value, max_denominator=16):
    """Format numeric inch values as fractions, leaving non-numeric text alone."""
    text = safe_cell_text(value).strip()
    if not text:
        return ''
    if '"' in text or '/' in text:
        return text
    try:
        number = float(text)
    except Exception:
        return text

    fraction = Fraction(number).limit_denominator(max_denominator)
    whole = fraction.numerator // fraction.denominator
    remainder = fraction.numerator % fraction.denominator
    if remainder == 0:
        return '{}"'.format(whole)
    if whole:
        return '{} {}/{}"'.format(whole, remainder, fraction.denominator)
    return '{}/{}"'.format(remainder, fraction.denominator)


def normalize_header_name(value):
    text = safe_cell_text(value).lower()
    text = text.replace('(%)', '%')
    text = re.sub(r'[\s_\-()]', '', text)
    return text


def element_match_key(value):
    text = safe_cell_text(value).lower()
    for superscript, digit in SUPERSCRIPT_DIGITS.items():
        text = text.replace(superscript, digit)
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
        top[5] = format_fractional_inches(mapped_value(row, column_map, 'max_agg'))
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
