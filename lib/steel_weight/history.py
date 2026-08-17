# -*- coding: utf-8 -*-
"""Raw CSV history export helpers for the Steel PSF command."""
from __future__ import unicode_literals

import csv
import os
import sys


RUN_ONLY = 'run_only'
RUN_APPEND = 'run_append'
RUN_INITIALIZE = 'run_initialize'

STEEL_KEY = 'steel'
FLOORS_KEY = 'floors'
EXCLUSIONS_KEY = 'exclusions'
LEVEL_SUMMARIES_KEY = 'level_summaries'
CATEGORY_SUMMARIES_KEY = 'category_summaries'
FAMILY_TYPE_SUMMARIES_KEY = 'family_type_summaries'
FLOOR_TYPE_SUMMARIES_KEY = 'floor_type_summaries'
EXCLUSION_SUMMARIES_KEY = 'exclusion_summaries'

EXPORT_FILENAMES = {
    STEEL_KEY: 'SteelPSF_Steel.csv',
    FLOORS_KEY: 'SteelPSF_Floors.csv',
    EXCLUSIONS_KEY: 'SteelPSF_Exclusions.csv',
    LEVEL_SUMMARIES_KEY: 'SteelPSF_LevelSummaries.csv',
    CATEGORY_SUMMARIES_KEY: 'SteelPSF_CategorySummaries.csv',
    FAMILY_TYPE_SUMMARIES_KEY: 'SteelPSF_FamilyTypeSummaries.csv',
    FLOOR_TYPE_SUMMARIES_KEY: 'SteelPSF_FloorTypeSummaries.csv',
    EXCLUSION_SUMMARIES_KEY: 'SteelPSF_ExcludedUnavailableSummaries.csv',
}
WORKBOOK_FILENAME = 'SteelPSF.xlsx'

COMMON_HEADER = [
    'RunId',
    'RunTimestamp',
    'DocumentTitle',
    'SelectedStoryCount',
    'SelectedStoryNames',
]

STEEL_CSV_HEADER = COMMON_HEADER + [
    'ElementId',
    'LevelId',
    'LevelName',
    'Category',
    'FamilyType',
    'LengthFeet',
    'NominalWeightLbPerFt',
    'ComputedPounds',
    'EligibilityStatus',
    'ExclusionReason',
]

FLOORS_CSV_HEADER = COMMON_HEADER + [
    'ElementId',
    'LevelId',
    'LevelName',
    'FloorType',
    'AreaSquareFeet',
    'EligibilityStatus',
    'ExclusionReason',
]

EXCLUSIONS_CSV_HEADER = COMMON_HEADER + [
    'SourceType',
    'ElementId',
    'LevelId',
    'LevelName',
    'Category',
    'FamilyType',
    'FloorType',
    'Reason',
    'LengthFeet',
    'Count',
]

LEVEL_SUMMARIES_CSV_HEADER = COMMON_HEADER + [
    'LevelName',
    'SteelWeightLb',
    'FloorAreaSf',
    'PSF',
]

CATEGORY_SUMMARIES_CSV_HEADER = COMMON_HEADER + [
    'LevelName',
    'Category',
    'SteelWeightLb',
]

FAMILY_TYPE_SUMMARIES_CSV_HEADER = COMMON_HEADER + [
    'LevelName',
    'FamilyType',
    'SteelWeightLb',
]

FLOOR_TYPE_SUMMARIES_CSV_HEADER = COMMON_HEADER + [
    'LevelName',
    'FloorType',
    'FloorAreaSf',
]

EXCLUSION_SUMMARIES_CSV_HEADER = COMMON_HEADER + [
    'Reason',
    'LevelName',
    'Category',
    'FamilyType',
    'Count',
    'TotalLengthFt',
]

EXPORT_HEADERS = {
    STEEL_KEY: STEEL_CSV_HEADER,
    FLOORS_KEY: FLOORS_CSV_HEADER,
    EXCLUSIONS_KEY: EXCLUSIONS_CSV_HEADER,
    LEVEL_SUMMARIES_KEY: LEVEL_SUMMARIES_CSV_HEADER,
    CATEGORY_SUMMARIES_KEY: CATEGORY_SUMMARIES_CSV_HEADER,
    FAMILY_TYPE_SUMMARIES_KEY: FAMILY_TYPE_SUMMARIES_CSV_HEADER,
    FLOOR_TYPE_SUMMARIES_KEY: FLOOR_TYPE_SUMMARIES_CSV_HEADER,
    EXCLUSION_SUMMARIES_KEY: EXCLUSION_SUMMARIES_CSV_HEADER,
}


class HistoryCsvError(Exception):
    """Raised when a history CSV cannot be safely written."""


def raw_history_csv_rows(steel_records, floor_records, adapter_skips, metadata,
                         run_id, run_timestamp):
    """Return raw steel, floor, and exclusion rows for one Steel PSF run."""
    export_rows = {
        STEEL_KEY: [],
        FLOORS_KEY: [],
        EXCLUSIONS_KEY: [],
    }
    for record in steel_records:
        status, reason, pounds = _steel_eligibility(record)
        export_rows[STEEL_KEY].append(
            _common_values(metadata, run_id, run_timestamp) + [
                _text(record.get('element_id')),
                _text(record.get('level_id')),
                _text(record.get('level_name')),
                _text(record.get('category')),
                _text(record.get('family_type')),
                _csv_number(record.get('length_feet')),
                _csv_number(record.get('nominal_weight_lb_per_foot')),
                _csv_number(pounds),
                status,
                reason,
            ])
        if status != 'Eligible':
            export_rows[EXCLUSIONS_KEY].append(_exclusion_row(
                metadata, run_id, run_timestamp, 'Steel', record, reason,
                record.get('length_feet'), 1))

    for record in floor_records:
        status, reason = _floor_eligibility(record)
        export_rows[FLOORS_KEY].append(
            _common_values(metadata, run_id, run_timestamp) + [
                _text(record.get('element_id')),
                _text(record.get('level_id')),
                _text(record.get('level_name')),
                _text(record.get('floor_type')),
                _csv_number(record.get('area_square_feet')),
                status,
                reason,
            ])
        if status != 'Eligible':
            export_rows[EXCLUSIONS_KEY].append(_exclusion_row(
                metadata, run_id, run_timestamp, 'Floor', record, reason,
                '', 1))

    for element_id, reason in (adapter_skips or []):
        export_rows[EXCLUSIONS_KEY].append(
            _common_values(metadata, run_id, run_timestamp) + [
                'AdapterSkip',
                _text(element_id),
                '',
                'Unspecified',
                'Unspecified',
                'Unspecified',
                '',
                _text(reason),
                '',
                '1',
            ])
    return export_rows


def summary_history_csv_rows(result, metadata, run_id, run_timestamp):
    """Return one CSV row set for each output-window summary table."""
    rows_by_key = {
        LEVEL_SUMMARIES_KEY: [],
        CATEGORY_SUMMARIES_KEY: [],
        FAMILY_TYPE_SUMMARIES_KEY: [],
        FLOOR_TYPE_SUMMARIES_KEY: [],
        EXCLUSION_SUMMARIES_KEY: [],
    }
    for item in result['rows']:
        rows_by_key[LEVEL_SUMMARIES_KEY].append(
            _common_values(metadata, run_id, run_timestamp) + [
                _text(item.get('level_name')),
                _csv_number(item.get('steel_weight_lb')),
                _csv_number(item.get('floor_area_square_feet')),
                _csv_number(item.get('psf')),
            ])

    total = result['total']
    rows_by_key[LEVEL_SUMMARIES_KEY].append(
        _common_values(metadata, run_id, run_timestamp) + [
            'TOTAL',
            _csv_number(total.get('steel_weight_lb')),
            _csv_number(total.get('floor_area_square_feet')),
            _csv_number(total.get('psf')),
        ])

    for item in result['categories']:
        rows_by_key[CATEGORY_SUMMARIES_KEY].append(
            _common_values(metadata, run_id, run_timestamp) + [
                _text(item.get('level_name')),
                _text(item.get('category')),
                _csv_number(item.get('steel_weight_lb')),
            ])

    for item in result['family_types']:
        rows_by_key[FAMILY_TYPE_SUMMARIES_KEY].append(
            _common_values(metadata, run_id, run_timestamp) + [
                _text(item.get('level_name')),
                _text(item.get('family_type')),
                _csv_number(item.get('steel_weight_lb')),
            ])

    for item in result['floor_types']:
        rows_by_key[FLOOR_TYPE_SUMMARIES_KEY].append(
            _common_values(metadata, run_id, run_timestamp) + [
                _text(item.get('level_name')),
                _text(item.get('floor_type')),
                _csv_number(item.get('floor_area_square_feet')),
            ])

    for item in result.get('excluded_summaries', []):
        rows_by_key[EXCLUSION_SUMMARIES_KEY].append(
            _common_values(metadata, run_id, run_timestamp) + [
                _text(item.get('reason')),
                _text(item.get('level_name')),
                _text(item.get('category')),
                _text(item.get('family_type')),
                _text(item.get('count')),
                _csv_number(item.get('length_feet')),
            ])
    return rows_by_key


def write_history_export_set(folder_path, rows_by_key, mode):
    """Write the Steel PSF raw CSV set and return per-file row counts."""
    if mode not in (RUN_APPEND, RUN_INITIALIZE):
        raise ValueError('Unsupported history CSV mode: {}'.format(mode))
    _ensure_dir(folder_path)
    paths = export_set_paths(folder_path)
    if mode == RUN_APPEND:
        _validate_export_set_headers(paths)

    counts = {}
    for key in (
            STEEL_KEY,
            FLOORS_KEY,
            EXCLUSIONS_KEY,
            LEVEL_SUMMARIES_KEY,
            CATEGORY_SUMMARIES_KEY,
            FAMILY_TYPE_SUMMARIES_KEY,
            FLOOR_TYPE_SUMMARIES_KEY,
            EXCLUSION_SUMMARIES_KEY):
        rows = rows_by_key.get(key, [])
        path = paths[key]
        write_header = mode == RUN_INITIALIZE or not _file_has_content(path)
        csv_mode = 'wb' if mode == RUN_INITIALIZE else 'ab'
        with _open_csv(path, csv_mode) as csv_file:
            writer = csv.writer(csv_file, lineterminator='\n')
            if write_header:
                writer.writerow(EXPORT_HEADERS[key])
            writer.writerows(rows)
        counts[key] = len(rows)
    return counts


def export_set_paths(folder_path):
    return {
        key: os.path.join(folder_path, filename)
        for key, filename in EXPORT_FILENAMES.items()
    }


def workbook_path_for_folder(folder_path):
    return os.path.join(folder_path, WORKBOOK_FILENAME)


def _validate_export_set_headers(paths):
    for key, path in paths.items():
        if not _file_has_content(path):
            continue
        with _open_csv(path, 'rb') as csv_file:
            reader = csv.reader(csv_file)
            try:
                header = next(reader)
            except StopIteration:
                continue
        if header != EXPORT_HEADERS[key]:
            raise HistoryCsvError(
                '{} header does not match Steel PSF raw export format. '
                'Choose Initialize CSV or select a different folder.'.format(
                    os.path.basename(path))
            )


def _common_values(metadata, run_id, run_timestamp):
    return [
        run_id,
        run_timestamp,
        _text(metadata.get('document_title')),
        _text(metadata.get('selected_story_count')),
        _text(metadata.get('selected_story_names')),
    ]


def _steel_eligibility(record):
    length = _positive_number(record.get('length_feet'))
    if length is None:
        return 'Excluded', 'missing or zero usable length', None
    nominal_weight = _positive_number(record.get('nominal_weight_lb_per_foot'))
    if nominal_weight is None:
        return 'Excluded', 'missing or zero nominal section weight', None
    return 'Eligible', '', length * nominal_weight


def _floor_eligibility(record):
    area = _positive_number(record.get('area_square_feet'))
    if area is None:
        return 'Excluded', 'missing or zero floor area'
    return 'Eligible', ''


def _exclusion_row(metadata, run_id, run_timestamp, source_type, record, reason,
                   length_feet, count):
    return _common_values(metadata, run_id, run_timestamp) + [
        source_type,
        _text(record.get('element_id')),
        _text(record.get('level_id')),
        _text(record.get('level_name') or 'Unspecified'),
        _text(record.get('category') or 'Unspecified'),
        _text(record.get('family_type') or 'Unspecified'),
        _text(record.get('floor_type') or ''),
        _text(reason),
        _csv_number(length_feet),
        _text(count),
    ]


def _positive_number(value):
    try:
        number = float(value)
    except Exception:
        return None
    return number if number > 0.0 else None


def _csv_number(value):
    if value is None or value == '':
        return ''
    try:
        return '{:.3f}'.format(float(value))
    except Exception:
        return _text(value)


def _text(value):
    return '' if value is None else str(value)


def _file_has_content(path):
    return os.path.exists(path) and os.path.getsize(path) > 0


def _ensure_dir(path):
    if path and not os.path.isdir(path):
        os.makedirs(path)


def _open_csv(path, mode):
    if sys.version_info[0] >= 3:
        return open(path, mode.replace('b', ''), newline='')
    return open(path, mode)
