# -*- coding: utf-8 -*-
"""CSV history export helpers for the Steel PSF command."""
from __future__ import unicode_literals

import csv
import os
import sys


RUN_ONLY = 'run_only'
RUN_APPEND = 'run_append'
RUN_INITIALIZE = 'run_initialize'
DEFAULT_HISTORY_CSV_NAME = 'SteelPSF.csv'

HISTORY_CSV_HEADER = [
    'RunId',
    'RunTimestamp',
    'DocumentTitle',
    'SelectedStoryCount',
    'SelectedStoryNames',
    'Section',
    'Level',
    'GroupName',
    'Metric',
    'Value',
    'Unit',
]


class HistoryCsvError(Exception):
    """Raised when a history CSV cannot be safely written."""


def history_csv_rows(result, metadata, run_id, run_timestamp, adapter_skips=None):
    """Return tidy summary-only history rows for charting over time."""
    rows = []
    for item in result['rows']:
        _append_metric_rows(
            rows, metadata, run_id, run_timestamp, 'Level', item['level_name'],
            item['level_name'], [
                ('Steel Weight', item['steel_weight_lb'], 'lb'),
                ('Floor Area', item['floor_area_square_feet'], 'sf'),
                ('PSF', item['psf'], 'psf'),
            ])

    total = result['total']
    _append_metric_rows(
        rows, metadata, run_id, run_timestamp, 'Total', 'TOTAL', 'TOTAL', [
            ('Steel Weight', total['steel_weight_lb'], 'lb'),
            ('Floor Area', total['floor_area_square_feet'], 'sf'),
            ('PSF', total['psf'], 'psf'),
        ])

    for item in result['categories']:
        _append_metric_rows(
            rows, metadata, run_id, run_timestamp, 'Category', item['level_name'],
            item['category'], [('Steel Weight', item['steel_weight_lb'], 'lb')])

    for item in result['family_types']:
        _append_metric_rows(
            rows, metadata, run_id, run_timestamp, 'Family/Type', item['level_name'],
            item['family_type'], [('Steel Weight', item['steel_weight_lb'], 'lb')])

    for item in result['floor_types']:
        _append_metric_rows(
            rows, metadata, run_id, run_timestamp, 'Floor Type', item['level_name'],
            item['floor_type'], [('Floor Area', item['floor_area_square_feet'], 'sf')])

    for item in result.get('excluded_summaries', []):
        group_name = '{} | {} | {}'.format(
            item.get('category', 'Unspecified'),
            item.get('family_type', 'Unspecified'),
            item.get('reason', 'Unspecified'),
        )
        _append_metric_rows(
            rows, metadata, run_id, run_timestamp, 'Exclusion',
            item.get('level_name', 'Unspecified'), group_name, [
                ('Excluded Count', item.get('count', 0), 'count'),
                ('Excluded Length', item.get('length_feet'), 'ft'),
            ])

    adapter_reasons = {}
    for unused_id, reason in (adapter_skips or []):
        adapter_reasons[reason] = adapter_reasons.get(reason, 0) + 1
    for reason, count in sorted(adapter_reasons.items()):
        _append_metric_rows(
            rows, metadata, run_id, run_timestamp, 'Exclusion', 'Unspecified',
            reason, [('Excluded Count', count, 'count')])
    return rows


def write_history_csv(path, rows, mode):
    """Write history rows in append or initialize mode and return count written."""
    if mode not in (RUN_APPEND, RUN_INITIALIZE):
        raise ValueError('Unsupported history CSV mode: {}'.format(mode))
    if mode == RUN_APPEND:
        _validate_append_header(path)
    _ensure_parent_dir(path)
    write_header = mode == RUN_INITIALIZE or not _file_has_content(path)
    csv_mode = 'wb' if mode == RUN_INITIALIZE else 'ab'
    with _open_csv(path, csv_mode) as csv_file:
        writer = csv.writer(csv_file, lineterminator='\n')
        if write_header:
            writer.writerow(HISTORY_CSV_HEADER)
        writer.writerows(rows)
    return len(rows)


def workbook_path_for_csv(csv_path):
    root, unused_ext = os.path.splitext(csv_path)
    return root + '.xlsx'


def initialized_csv_path(folder_path):
    return os.path.join(folder_path, DEFAULT_HISTORY_CSV_NAME)


def _append_metric_rows(rows, metadata, run_id, run_timestamp, section, level, group_name, metrics):
    for metric, value, unit in metrics:
        rows.append([
            run_id,
            run_timestamp,
            str(metadata.get('document_title', '')),
            str(metadata.get('selected_story_count', '')),
            str(metadata.get('selected_story_names', '')),
            section,
            level,
            group_name,
            metric,
            _csv_number(value),
            unit,
        ])


def _csv_number(value):
    if value is None:
        return ''
    try:
        return '{:.3f}'.format(float(value))
    except Exception:
        return str(value)


def _validate_append_header(path):
    if not _file_has_content(path):
        return
    with _open_csv(path, 'rb') as csv_file:
        reader = csv.reader(csv_file)
        try:
            header = next(reader)
        except StopIteration:
            return
    if header != HISTORY_CSV_HEADER:
        raise HistoryCsvError(
            'Existing CSV header does not match Steel PSF history format. '
            'Choose Run And Initialize CSV or select a different file.'
        )


def _file_has_content(path):
    return os.path.exists(path) and os.path.getsize(path) > 0


def _ensure_parent_dir(path):
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)


def _open_csv(path, mode):
    if sys.version_info[0] >= 3:
        return open(path, mode.replace('b', ''), newline='')
    return open(path, mode)
