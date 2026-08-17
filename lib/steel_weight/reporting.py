# -*- coding: utf-8 -*-
"""Summary-only projections for the Steel PSF command."""
from __future__ import unicode_literals


OUTPUT_INTRO = 'Pounds = length (ft) × nominal section weight (lb/ft).'


def report_output_tables(result, adapter_skips=None):
    """Return native pyRevit output table definitions for the report window."""
    tables = []
    level_rows = [[
        row['level_name'],
        _display_number(row['steel_weight_lb']),
        _display_number(row['floor_area_square_feet']),
        _display_number(row['psf']),
    ] for row in result['rows']]
    total = result['total']
    level_rows.append([
        'TOTAL',
        _display_number(total['steel_weight_lb']),
        _display_number(total['floor_area_square_feet']),
        _display_number(total['psf']),
    ])
    tables.append({
        'title': 'Level Summaries',
        'rows': level_rows,
        'columns': ['Level', 'Steel Weight (lb)', 'Floor Area (sf)', 'PSF'],
    })
    tables.append(_three_column_table(
        'Category Summaries',
        result['categories'],
        'category',
        'Category',
        'steel_weight_lb',
        'Steel Weight (lb)',
    ))
    tables.append(_three_column_table(
        'Family/Type Summaries',
        result['family_types'],
        'family_type',
        'Family/Type',
        'steel_weight_lb',
        'Steel Weight (lb)',
    ))
    tables.append(_three_column_table(
        'Floor-Type Summaries',
        result['floor_types'],
        'floor_type',
        'Floor Type',
        'floor_area_square_feet',
        'Floor Area (sf)',
    ))
    excluded_rows = excluded_output_rows(result.get('excluded_summaries', []), adapter_skips)
    if excluded_rows:
        tables.append({
            'title': 'Excluded Or Unavailable Data',
            'rows': excluded_rows,
            'columns': ['Reason', 'Level', 'Category', 'Family/Type', 'Count', 'Total Length (ft)'],
        })
    return tables


def excluded_output_rows(excluded_summaries, adapter_skips=None):
    rows = [[
        item['reason'],
        item['level_name'],
        item['category'],
        item['family_type'],
        item['count'],
        _display_number(item['length_feet']),
    ] for item in excluded_summaries]
    adapter_reasons = {}
    for unused_id, reason in (adapter_skips or []):
        adapter_reasons[reason] = adapter_reasons.get(reason, 0) + 1
    for reason, count in sorted(adapter_reasons.items()):
        rows.append([reason, 'Unspecified', 'Unspecified', 'Unspecified', count, _display_number(0.0)])
    return rows


def _three_column_table(title, summaries, name_key, name_header, value_key, value_header):
    return {
        'title': title,
        'rows': [[
            row['level_name'],
            row[name_key],
            _display_number(row[value_key]),
        ] for row in summaries],
        'columns': ['Level', name_header, value_header],
    }


def summary_csv_rows(result, metadata):
    """Return CSV rows containing summaries and exclusions, never raw records."""
    rows = [[
        'Section', 'Name', 'Steel Weight (lb)', 'Floor Area (sf)', 'PSF',
        'Count', 'Total Length (ft)', 'Category',
    ]]
    for key in sorted(metadata):
        rows.append(['Metadata', key, str(metadata[key])])
    _append_level_rows(rows, result['rows'])
    total = result['total']
    rows.append(['Total', 'TOTAL', _number(total['steel_weight_lb']),
                 _number(total['floor_area_square_feet']), _number(total['psf'])])
    _append_summary_rows(rows, 'Category', result['categories'], 'category', 'steel_weight_lb')
    _append_summary_rows(rows, 'Family Type', result['family_types'], 'family_type', 'steel_weight_lb')
    _append_summary_rows(rows, 'Floor Type', result['floor_types'], 'floor_type', 'floor_area_square_feet')
    _append_exclusion_rows(rows, result.get('excluded_summaries', []))
    return rows


def _append_level_rows(rows, level_rows):
    for row in level_rows:
        rows.append(['Level', row['level_name'], _number(row['steel_weight_lb']),
                     _number(row['floor_area_square_feet']), _number(row['psf'])])


def _append_summary_rows(rows, section, summaries, name_key, value_key):
    for item in summaries:
        value = _number(item[value_key])
        name = '{} | {}'.format(item.get('level_name', 'Unspecified'), item[name_key])
        if value_key == 'steel_weight_lb':
            rows.append([section, name, value])
        else:
            rows.append([section, name, '', value])


def _append_exclusion_rows(rows, summaries):
    for item in summaries:
        name = '{} | {} | {}'.format(
            item.get('level_name', 'Unspecified'),
            item.get('family_type', 'Unspecified'),
            item.get('reason', 'Unspecified'),
        )
        rows.append([
            'Exclusion',
            name,
            '',
            '',
            '',
            str(item.get('count', 0)),
            _number(item.get('length_feet')),
            item.get('category', 'Unspecified'),
        ])


def _number(value):
    return '' if value is None else '{:.3f}'.format(value)


def _display_number(value):
    return 'N/A' if value is None else '{:.3f}'.format(value)
