"""Deterministic steel PSF aggregation rules."""
from __future__ import unicode_literals


def aggregate_steel_weight(steel_records, floor_area_records):
    """Aggregate normalized records without retaining raw output rows."""
    levels = {}
    category_weights = {}
    family_type_weights = {}
    floor_type_areas = {}
    excluded = []
    for record in steel_records:
        _add_steel_record(record, levels, category_weights, family_type_weights, excluded)
    for record in floor_area_records:
        _add_floor_area_record(record, levels, floor_type_areas, excluded)
    rows = sorted([_row_for_level(level) for level in levels.values()], key=_row_sort_key)
    return {
        'rows': rows,
        'total': _total_for_rows(rows),
        'categories': _summary_rows(category_weights, 'category', 'steel_weight_lb'),
        'family_types': _summary_rows(family_type_weights, 'family_type', 'steel_weight_lb'),
        'floor_types': _summary_rows(floor_type_areas, 'floor_type', 'floor_area_square_feet'),
        'excluded': excluded,
    }


def records_for_level_ids(records, level_ids):
    """Return records assigned to one of the selected level ids."""
    selected_ids = set(level_ids or [])
    if not selected_ids:
        return []
    return [record for record in records if record.get('level_id') in selected_ids]


def _add_steel_record(record, levels, category_weights, family_type_weights, excluded):
    level = _level_for_record(record, levels)
    if level is None:
        _exclude(excluded, record, 'missing level')
        return
    length = _positive_number(record.get('length_feet'))
    if length is None:
        _exclude(excluded, record, 'missing or zero usable length')
        return
    nominal_weight = _positive_number(record.get('nominal_weight_lb_per_foot'))
    if nominal_weight is None:
        _exclude(excluded, record, 'missing or zero nominal section weight')
        return
    pounds = length * nominal_weight
    level['steel_weight_lb'] += pounds
    _add_summary_value(category_weights, record.get('category'), pounds, 'Unspecified')
    _add_summary_value(family_type_weights, record.get('family_type'), pounds, 'Unspecified')


def _add_floor_area_record(record, levels, floor_type_areas, excluded):
    level = _level_for_record(record, levels)
    if level is None:
        _exclude(excluded, record, 'missing level')
        return
    area = _positive_number(record.get('area_square_feet'))
    if area is None:
        _exclude(excluded, record, 'missing or zero floor area')
        return
    level['floor_area_square_feet'] += area
    _add_summary_value(floor_type_areas, record.get('floor_type'), area, 'Unspecified')


def _level_for_record(record, levels):
    level_id = record.get('level_id')
    level_name = record.get('level_name')
    if level_id is None or not level_name:
        return None
    if level_id not in levels:
        levels[level_id] = {
            'level_id': level_id,
            'level_name': level_name,
            'steel_weight_lb': 0.0,
            'floor_area_square_feet': 0.0,
        }
    return levels[level_id]


def _positive_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0.0 else None


def _add_summary_value(summary, key, value, default_key):
    summary[key or default_key] = summary.get(key or default_key, 0.0) + value


def _exclude(excluded, record, reason):
    excluded.append({'element_id': record.get('element_id'), 'reason': reason})


def _row_for_level(level):
    area = level['floor_area_square_feet']
    weight = level['steel_weight_lb']
    return {
        'level_id': level['level_id'], 'level_name': level['level_name'],
        'steel_weight_lb': weight, 'floor_area_square_feet': area,
        'psf': weight / area if area > 0.0 else None,
    }


def _row_sort_key(row):
    return (row['level_name'].lower(), str(row['level_id']))


def _total_for_rows(rows):
    weight = sum(row['steel_weight_lb'] for row in rows)
    area = sum(row['floor_area_square_feet'] for row in rows)
    return {'steel_weight_lb': weight, 'floor_area_square_feet': area,
            'psf': weight / area if area > 0.0 else None}


def _summary_rows(values, key_name, value_name):
    return [{key_name: key, value_name: values[key]} for key in sorted(values, key=lambda item: item.lower())]
