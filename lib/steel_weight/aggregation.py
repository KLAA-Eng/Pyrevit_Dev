"""Deterministic steel weight and floor-area aggregation rules."""
from __future__ import unicode_literals


POUNDS_PER_KILOGRAM = 2.20462262185


def aggregate_steel_weight(material_records, floor_area_records):
    """Return per-level and total steel-weight results without Revit objects."""
    levels = {}
    excluded = []
    for record in material_records:
        _add_material_record(record, levels, excluded)
    for record in floor_area_records:
        _add_floor_area_record(record, levels, excluded)
    rows = [_row_for_level(levels[level_id]) for level_id in levels]
    rows.sort(key=_row_sort_key)
    return {
        'rows': rows,
        'total': _total_for_rows(rows),
        'excluded': excluded,
    }


def _add_material_record(record, levels, excluded):
    level = _level_for_record(record, levels)
    if level is None:
        _exclude(excluded, record, 'missing level')
        return
    volume = _positive_number(record.get('volume_cubic_feet'))
    if volume is None:
        _exclude(excluded, record, 'missing or zero material volume')
        return
    density = _positive_number(record.get('density_kg_per_cubic_foot'))
    if density is None:
        _exclude(excluded, record, 'missing or zero material density')
        return
    level['steel_weight_lb'] += volume * density * POUNDS_PER_KILOGRAM


def _add_floor_area_record(record, levels, excluded):
    level = _level_for_record(record, levels)
    if level is None:
        _exclude(excluded, record, 'missing level')
        return
    area = _positive_number(record.get('area_square_feet'))
    if area is None:
        _exclude(excluded, record, 'missing or zero floor area')
        return
    level['floor_area_square_feet'] += area


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


def _exclude(excluded, record, reason):
    excluded.append({
        'element_id': record.get('element_id'),
        'material_id': record.get('material_id'),
        'reason': reason,
    })


def _row_for_level(level):
    area = level['floor_area_square_feet']
    weight = level['steel_weight_lb']
    return {
        'level_id': level['level_id'],
        'level_name': level['level_name'],
        'steel_weight_lb': weight,
        'floor_area_square_feet': area,
        'psf': weight / area if area > 0.0 else None,
    }


def _row_sort_key(row):
    return (row['level_name'].lower(), str(row['level_id']))


def _total_for_rows(rows):
    weight = sum(row['steel_weight_lb'] for row in rows)
    area = sum(row['floor_area_square_feet'] for row in rows)
    return {
        'steel_weight_lb': weight,
        'floor_area_square_feet': area,
        'psf': weight / area if area > 0.0 else None,
    }
