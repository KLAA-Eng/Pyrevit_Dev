# -*- coding: utf-8 -*-
"""Prepare post-processing workbook values for Carbon GWP charts.

This module contains the deterministic, host-independent portion of the
Carbon GWP chart workflow.  It deliberately has no Revit, pyRevit, Excel COM,
or .NET drawing dependencies so the workbook contract can be tested outside
Revit.
"""
from __future__ import print_function

import math
import re

from .workflow import safe_text


GWP_CHART_UNIT = u'kgCO\u2082e'
VOLUME_CHART_UNIT = 'CF'
CHART_WIDTH_INCHES = 7.875
CHART_BASE_HEIGHT_INCHES = 4.75
CHART_GROWTH_START_COUNT = 6
CHART_EXTRA_HEIGHT_PER_SLICE_INCHES = 0.65
DISPLAY_LABEL_GWP_PATTERN = re.compile(r'gwp', re.IGNORECASE)
MATERIAL_CHART_COLORS = (
    ('steel', '#558ED5'),
    ('concrete', '#D9D9D9'),
    ('wood', '#9BBB59'),
    ('mason', '#7F7F7F'),
)
CHART_FALLBACK_COLORS = (
    '#4E79A7', '#F28E2B', '#E15759', '#76B7B2', '#59A14F', '#EDC948',
    '#B07AA1', '#FF9DA7', '#9C755F', '#BAB0AC', '#2F5597', '#70AD47',
)


def _numeric_value(value, measure_name):
    """Return a finite numeric value or a reason that it cannot be charted."""
    text = safe_text(value).strip()
    if not text:
        return None, 'blank {} value'.format(measure_name)
    try:
        number = float(text.replace(',', ''))
    except (TypeError, ValueError):
        return None, 'non-numeric {} value'.format(measure_name)
    if math.isnan(number) or math.isinf(number):
        return None, 'non-finite {} value'.format(measure_name)
    if number <= 0:
        return None, 'non-positive {} value'.format(measure_name)
    return number, None


def fallback_chart_color(parameter_name):
    """Return a repeatable palette color from a normalized source name.

    Do not use Python's built-in ``hash`` here. Its value can vary between
    runtimes, while a chart category must retain its fallback color on rerun.
    """
    normalized = safe_text(parameter_name).strip().lower()
    for material_name, color in MATERIAL_CHART_COLORS:
        if material_name in normalized:
            return color
    value = 0
    for index, character in enumerate(normalized):
        value += (index + 1) * ord(character)
    return CHART_FALLBACK_COLORS[value % len(CHART_FALLBACK_COLORS)]


def display_label_from_source_name(source_name):
    """Remove the implementation-oriented GWP token from a material name."""
    label = DISPLAY_LABEL_GWP_PATTERN.sub('', safe_text(source_name))
    return label.strip(' -_') or safe_text(source_name).strip()


def chart_slices_from_export_rows(rows, value_column=1, measure_name='GWP'):
    """Build chart slices from the three-column ``Export`` contract.

    Column A is the stable material/source name, B is GWP in ``kgCO₂e``, and
    C is material volume in cubic feet. ``value_column`` selects the requested
    measure. Invalid values are skipped with an audit reason instead of
    blocking other valid material rows. Labels and colors are intentionally
    derived from column A and the fixed material palette; no extra workbook
    columns are consumed.

    Args:
        rows: Iterable Export worksheet rows.
        value_column: Zero-based column containing the requested measure.
        measure_name: User-facing name used in skipped-row reasons.

    Returns:
        Tuple ``(slices, skipped)``. Each slice contains row, source_name,
        display_label, value, color, and color_source fields.
    """
    slices = []
    skipped = []
    for row_index, row in enumerate(rows or [], start=1):
        source_name = safe_text(row[0] if len(row) > 0 else '').strip()
        raw_value = row[value_column] if len(row) > value_column else ''
        if not source_name:
            skipped.append({
                'row': row_index,
                'source_name': '',
                'display_label': '',
                'reason': 'blank source name',
                'value': safe_text(raw_value),
            })
            continue
        value, reason = _numeric_value(raw_value, measure_name)
        if reason:
            skipped.append({
                'row': row_index,
                'source_name': source_name,
                'display_label': display_label_from_source_name(source_name),
                'reason': reason,
                'value': safe_text(raw_value),
            })
            continue
        slices.append({
            'row': row_index,
            'source_name': source_name,
            'display_label': display_label_from_source_name(source_name),
            'value': value,
            'color': fallback_chart_color(source_name),
            'color_source': 'fixed material palette',
        })
    return slices, skipped


def chart_total(slices):
    """Return the unrounded total of chart slices."""
    return sum([item['value'] for item in slices or []])


def chart_percent(value, total):
    """Return a chart percentage or zero when the total cannot be charted."""
    if not total:
        return 0.0
    return (float(value) / float(total)) * 100.0


def format_chart_amount(value, unit=GWP_CHART_UNIT):
    """Format a chart amount as a nearest-whole number with its unit."""
    return '{:,} {}'.format(int(round(float(value))), unit)


def format_chart_table_amount(value):
    """Format a report-table amount with two decimals and no separators."""
    return '{:.2f}'.format(float(value))


def chart_canvas_height_inches(slice_count):
    """Return the chart canvas height for a number of legend entries."""
    extra_count = max(0, int(slice_count or 0) - CHART_GROWTH_START_COUNT)
    return CHART_BASE_HEIGHT_INCHES + (
        extra_count * CHART_EXTRA_HEIGHT_PER_SLICE_INCHES)


def format_chart_detail(chart_slice, total, unit=GWP_CHART_UNIT):
    """Return the second, smaller line of a legend entry."""
    return u'{} \u2022 {:.1f}%'.format(
        format_chart_amount(chart_slice['value'], unit),
        chart_percent(chart_slice['value'], total))


def format_chart_label(chart_slice, total, unit=GWP_CHART_UNIT):
    """Return the two-line legend label used by the rendered chart."""
    return u'{}\n{}'.format(
        chart_slice['display_label'],
        format_chart_detail(chart_slice, total, unit))
