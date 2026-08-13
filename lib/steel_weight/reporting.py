"""Summary-only projections for the Steel PSF command."""
from __future__ import unicode_literals

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
