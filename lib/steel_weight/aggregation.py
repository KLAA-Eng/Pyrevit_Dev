"""Deterministic steel PSF aggregation rules."""
from __future__ import unicode_literals


def aggregate_steel_weight(steel_records, floor_area_records):
    """Aggregate normalized records without retaining raw output rows."""
    levels = {}
    category_weights = {}
    family_type_weights = {}
    floor_type_areas = {}
    excluded_summaries = {}
    excluded = []
    for record in steel_records:
        _add_steel_record(
            record, levels, category_weights, family_type_weights,
            excluded, excluded_summaries)
    for record in floor_area_records:
        _add_floor_area_record(record, levels, floor_type_areas, excluded, excluded_summaries)
    rows = sorted([_row_for_level(level) for level in levels.values()], key=_row_sort_key)
    return {
        'rows': rows,
        'total': _total_for_rows(rows),
        'categories': _level_summary_rows(category_weights, 'category', 'steel_weight_lb'),
        'family_types': _level_summary_rows(family_type_weights, 'family_type', 'steel_weight_lb'),
        'floor_types': _level_summary_rows(floor_type_areas, 'floor_type', 'floor_area_square_feet'),
        'excluded': excluded,
        'excluded_summaries': _excluded_summary_rows(excluded_summaries),
    }


def records_for_level_ids(records, level_ids):
    """Return records assigned to one of the selected level ids."""
    selected_ids = set(level_ids or [])
    if not selected_ids:
        return []
    return [record for record in records if record.get('level_id') in selected_ids]


def _add_steel_record(record, levels, category_weights, family_type_weights,
                      excluded, excluded_summaries):
    level = _level_for_record(record, levels)
    if level is None:
        _exclude(excluded, excluded_summaries, record, 'missing level')
        return
    length = _positive_number(record.get('length_feet'))
    if length is None:
        _exclude(excluded, excluded_summaries, record, 'missing or zero usable length')
        return
    nominal_weight = _positive_number(record.get('nominal_weight_lb_per_foot'))
    if nominal_weight is None:
        _exclude(excluded, excluded_summaries, record, 'missing or zero nominal section weight')
        return
    pounds = length * nominal_weight
    level['steel_weight_lb'] += pounds
    _add_level_summary_value(category_weights, record, 'category', pounds, 'Unspecified')
    _add_level_summary_value(family_type_weights, record, 'family_type', pounds, 'Unspecified')


def _add_floor_area_record(record, levels, floor_type_areas, excluded, excluded_summaries):
    level = _level_for_record(record, levels)
    if level is None:
        _exclude(excluded, excluded_summaries, record, 'missing level')
        return
    area = _positive_number(record.get('area_square_feet'))
    if area is None:
        _exclude(excluded, excluded_summaries, record, 'missing or zero floor area')
        return
    level['floor_area_square_feet'] += area
    _add_level_summary_value(floor_type_areas, record, 'floor_type', area, 'Unspecified')


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
    except Exception:
        return None
    return number if number > 0.0 else None


def _add_level_summary_value(summary, record, key_field, value, default_key):
    key = (
        record.get('level_id'),
        record.get('level_name') or 'Unspecified',
        record.get(key_field) or default_key,
    )
    summary[key] = summary.get(key, 0.0) + value


def _exclude(excluded, summaries, record, reason):
    excluded.append({'element_id': record.get('element_id'), 'reason': reason})
    length = _positive_number(record.get('length_feet')) or 0.0
    key = (
        reason,
        record.get('level_id'),
        record.get('level_name') or 'Unspecified',
        record.get('category') or 'Unspecified',
        record.get('family_type') or record.get('floor_type') or 'Unspecified',
    )
    if key not in summaries:
        summaries[key] = {'count': 0, 'length_feet': 0.0}
    summaries[key]['count'] += 1
    summaries[key]['length_feet'] += length


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


def _level_summary_rows(values, key_name, value_name):
    rows = []
    for key in sorted(values, key=lambda item: (item[1].lower(), item[2].lower())):
        unused_level_id, level_name, name = key
        rows.append({
            'level_name': level_name,
            key_name: name,
            value_name: values[key],
        })
    return rows


def _excluded_summary_rows(values):
    rows = []
    for key in sorted(values, key=lambda item: (
            item[2].lower(), item[4].lower(), item[0].lower())):
        reason, unused_level_id, level_name, category, family_type = key
        rows.append({
            'reason': reason,
            'level_name': level_name,
            'category': category,
            'family_type': family_type,
            'count': values[key]['count'],
            'length_feet': values[key]['length_feet'],
        })
    return rows
