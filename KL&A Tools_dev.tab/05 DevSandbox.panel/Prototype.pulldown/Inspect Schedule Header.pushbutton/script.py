# -*- coding: utf-8 -*-
"""Export selected Revit schedule header layout metadata."""
from __future__ import print_function

import codecs
import csv
import datetime
import json
import os
import re
import traceback

from pyrevit import DB, forms, revit, script


COMMAND_TITLE = 'Inspect Schedule Header'

try:
    TEXT_TYPES = (unicode,)
    BINARY_TYPE = str
except NameError:
    TEXT_TYPES = (str,)
    BINARY_TYPE = bytes


def _element_id_value(element_id):
    if element_id is None:
        return None
    for property_name in ('Value', 'IntegerValue'):
        try:
            return int(getattr(element_id, property_name))
        except Exception:
            pass
    return None


def _element_name(element, default='Unnamed'):
    if element is None:
        return default
    try:
        name = DB.Element.Name.GetValue(element)
    except Exception:
        try:
            name = element.Name
        except Exception:
            name = None
    return name or default


def _safe_text(value):
    if value is None:
        return ''
    if isinstance(value, TEXT_TYPES):
        return value
    if isinstance(value, BINARY_TYPE):
        for encoding in ('utf-8', 'cp1252', 'latin-1'):
            try:
                return value.decode(encoding)
            except Exception:
                pass
        try:
            return value.decode('utf-8', 'replace')
        except Exception:
            pass
    try:
        return unicode(value)
    except NameError:
        return str(value)
    except Exception:
        return str(value)


def _json_value(value):
    if value is None:
        return None
    if isinstance(value, (bool, int, float)):
        return value
    try:
        element_id = _element_id_value(value)
        if element_id is not None:
            return element_id
    except Exception:
        pass
    return _safe_text(value)


def _enum_name(value):
    if value is None:
        return None
    try:
        return str(value)
    except Exception:
        return None


def _color_record(color):
    if color is None:
        return None
    try:
        return {
            'red': int(color.Red),
            'green': int(color.Green),
            'blue': int(color.Blue),
        }
    except Exception:
        return _safe_text(color)


def _schedule_options(document):
    schedules = DB.FilteredElementCollector(document).OfClass(DB.ViewSchedule)
    options = {}
    for schedule in schedules:
        if getattr(schedule, 'IsTemplate', False):
            continue
        if getattr(schedule, 'IsTitleblockRevisionSchedule', False):
            continue
        label = _element_name(schedule)
        if label in options:
            label = '{} ({})'.format(label, _element_id_value(schedule.Id))
        options[label] = schedule
    return options


def _select_schedule(document):
    options = _schedule_options(document)
    if not options:
        forms.alert('No schedules were found in the active model.', title=COMMAND_TITLE, warn_icon=True)
        return None
    try:
        from GUI.forms import select_from_dict
        selected = select_from_dict(
            options,
            title=COMMAND_TITLE,
            label='Select schedule to inspect:',
            button_name='Inspect Schedule',
            version='DevSandbox Prototype',
            SelectMultiple=False,
        )
    except Exception:
        selected = forms.SelectFromList.show(
            sorted(options.keys()),
            title=COMMAND_TITLE,
            button_name='Inspect Schedule')
        selected = options.get(selected)
    if isinstance(selected, list):
        return selected[0] if selected else None
    return selected


def _safe_call(warnings, label, func, default=None):
    try:
        return func()
    except Exception as error:
        warnings.append('{}: {}'.format(label, error))
        return default


def _section_value(section, attr_name):
    try:
        return getattr(section, attr_name)
    except Exception:
        return None


def _cell_text(section, row, column):
    for method_name in ('GetCellText', 'GetCellCalculatedValue'):
        try:
            method = getattr(section, method_name)
            value = method(row, column)
            if value is not None:
                return _safe_text(value)
        except Exception:
            pass
    return ''


def _row_height(section, row):
    try:
        return section.GetRowHeight(row)
    except Exception:
        return None


def _column_width(section, column):
    try:
        return section.GetColumnWidth(column)
    except Exception:
        return None


def _style_options(style):
    try:
        options = style.GetCellStyleOverrideOptions()
    except Exception:
        return {}
    names = [
        'BackgroundColor',
        'Bold',
        'Font',
        'FontColor',
        'FontHorizontalAlignment',
        'FontSize',
        'Italic',
        'TextOrientation',
        'Underline',
    ]
    result = {}
    for name in names:
        try:
            result[name] = _json_value(getattr(options, name))
        except Exception:
            pass
    return result


def _cell_style(section, row, column):
    try:
        style = section.GetCellStyle(row, column)
    except Exception:
        return {}
    values = {}
    for attr_name in (
            'BackgroundColor',
            'BorderBottomLineStyle',
            'BorderLeftLineStyle',
            'BorderRightLineStyle',
            'BorderTopLineStyle',
            'FontName',
            'IsFontBold',
            'IsFontItalic',
            'IsFontUnderline',
            'TextColor',
            'TextOrientation',
            'TextSize'):
        try:
            value = getattr(style, attr_name)
            if 'Color' in attr_name:
                values[attr_name] = _color_record(value)
            else:
                values[attr_name] = _json_value(value)
        except Exception:
            pass
    for attr_name in ('FontHorizontalAlignment', 'FontVerticalAlignment'):
        try:
            values[attr_name] = _enum_name(getattr(style, attr_name))
        except Exception:
            pass
    values['override_options'] = _style_options(style)
    return values


def _merged_cell(section, row, column):
    result = {
        'is_merged': False,
        'top': None,
        'left': None,
        'bottom': None,
        'right': None,
    }
    try:
        if hasattr(section, 'IsCellMerged'):
            result['is_merged'] = bool(section.IsCellMerged(row, column))
    except Exception:
        pass
    try:
        merged = section.GetMergedCell(row, column)
    except Exception:
        return result
    if merged is None:
        return result
    result['is_merged'] = True
    for source_name, target_name in (
            ('Top', 'top'),
            ('Left', 'left'),
            ('Bottom', 'bottom'),
            ('Right', 'right'),
            ('TopRow', 'top'),
            ('LeftColumn', 'left'),
            ('BottomRow', 'bottom'),
            ('RightColumn', 'right')):
        try:
            value = getattr(merged, source_name)
            if value is not None:
                result[target_name] = int(value)
        except Exception:
            pass
    return result


def _definition_record(schedule):
    definition = getattr(schedule, 'Definition', None)
    if definition is None:
        return {}
    values = {}
    for attr_name in (
            'ShowHeaders',
            'ShowTitle',
            'ShowGrandTotal',
            'ShowGrandTotalTitle',
            'ShowGrandTotalCount',
            'IsItemized'):
        try:
            values[attr_name] = _json_value(getattr(definition, attr_name))
        except Exception:
            pass
    try:
        values['field_count'] = int(definition.GetFieldCount())
    except Exception:
        pass
    return values


def _section_record(schedule, section_type, section_name, warnings):
    table_data = schedule.GetTableData()
    section = table_data.GetSectionData(section_type)
    record = {
        'name': section_name,
        'first_row': _section_value(section, 'FirstRowNumber'),
        'last_row': _section_value(section, 'LastRowNumber'),
        'first_column': _section_value(section, 'FirstColumnNumber'),
        'last_column': _section_value(section, 'LastColumnNumber'),
        'number_of_rows': _section_value(section, 'NumberOfRows'),
        'number_of_columns': _section_value(section, 'NumberOfColumns'),
        'rows': [],
        'columns': [],
        'cells': [],
    }

    first_row = record['first_row']
    last_row = record['last_row']
    first_column = record['first_column']
    last_column = record['last_column']
    if None in (first_row, last_row, first_column, last_column):
        warnings.append('{} section has incomplete row/column bounds.'.format(section_name))
        return record

    for row in range(int(first_row), int(last_row) + 1):
        record['rows'].append({
            'row': row,
            'offset': row - int(first_row),
            'height_feet': _row_height(section, row),
        })
    for column in range(int(first_column), int(last_column) + 1):
        record['columns'].append({
            'column': column,
            'offset': column - int(first_column),
            'width_feet': _column_width(section, column),
        })
    for row in range(int(first_row), int(last_row) + 1):
        for column in range(int(first_column), int(last_column) + 1):
            record['cells'].append({
                'row': row,
                'column': column,
                'row_offset': row - int(first_row),
                'column_offset': column - int(first_column),
                'text': _cell_text(section, row, column),
                'row_height_feet': _row_height(section, row),
                'column_width_feet': _column_width(section, column),
                'merged_cell': _merged_cell(section, row, column),
                'style': _cell_style(section, row, column),
            })
    return record


def _section_bounds_record(schedule, section_type, section_name):
    table_data = schedule.GetTableData()
    section = table_data.GetSectionData(section_type)
    return {
        'name': section_name,
        'first_row': _section_value(section, 'FirstRowNumber'),
        'last_row': _section_value(section, 'LastRowNumber'),
        'first_column': _section_value(section, 'FirstColumnNumber'),
        'last_column': _section_value(section, 'LastColumnNumber'),
        'number_of_rows': _section_value(section, 'NumberOfRows'),
        'number_of_columns': _section_value(section, 'NumberOfColumns'),
    }


def _inspection_record(document, schedule):
    warnings = []
    header = _safe_call(
        warnings,
        'Read header section',
        lambda: _section_record(schedule, DB.SectionType.Header, 'Header', warnings),
        {})
    body_summary = _safe_call(
        warnings,
        'Read body section bounds',
        lambda: _section_bounds_record(schedule, DB.SectionType.Body, 'Body'),
        {})
    return {
        'generated_at': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'document': {
            'title': getattr(document, 'Title', None),
            'path_name': getattr(document, 'PathName', None),
        },
        'schedule': {
            'name': _element_name(schedule),
            'id': _element_id_value(schedule.Id),
            'view_type': _enum_name(getattr(schedule, 'ViewType', None)),
            'definition': _definition_record(schedule),
        },
        'sections': {
            'header': header,
            'body_summary': body_summary,
        },
        'warnings': warnings,
    }


def _slug(text):
    cleaned = re.sub(r'[^A-Za-z0-9_.-]+', '_', _safe_text(text)).strip('._')
    return cleaned or 'schedule'


def _write_json(path, data):
    with codecs.open(path, 'w', 'utf-8') as json_file:
        json.dump(_sanitize_json(data), json_file, indent=2, sort_keys=True, ensure_ascii=False)


def _sanitize_json(value):
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, dict):
        return {
            _safe_text(key): _sanitize_json(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_sanitize_json(item) for item in value]
    return _safe_text(value)


def _csv_text(value):
    text = _safe_text(value)
    try:
        return text.encode('utf-8')
    except Exception:
        return text


def _write_csv(path, inspection):
    header = inspection.get('sections', {}).get('header', {})
    rows = header.get('cells', [])
    with open(path, 'wb') as csv_file:
        writer = csv.writer(csv_file, lineterminator='\n')
        writer.writerow([
            'row',
            'column',
            'row_offset',
            'column_offset',
            'text',
            'row_height_feet',
            'column_width_feet',
            'is_merged',
            'merge_top',
            'merge_left',
            'merge_bottom',
            'merge_right',
            'text_size',
            'is_bold',
            'horizontal_alignment',
            'vertical_alignment',
        ])
        for cell in rows:
            merged = cell.get('merged_cell') or {}
            style = cell.get('style') or {}
            writer.writerow([
                cell.get('row'),
                cell.get('column'),
                cell.get('row_offset'),
                cell.get('column_offset'),
                _csv_text(cell.get('text')),
                cell.get('row_height_feet'),
                cell.get('column_width_feet'),
                merged.get('is_merged'),
                merged.get('top'),
                merged.get('left'),
                merged.get('bottom'),
                merged.get('right'),
                style.get('TextSize'),
                style.get('IsFontBold'),
                _csv_text(style.get('FontHorizontalAlignment')),
                _csv_text(style.get('FontVerticalAlignment')),
            ])


def _print_report(output, inspection, json_path, csv_path):
    schedule = inspection['schedule']
    header = inspection['sections']['header']
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('Schedule: `{}`'.format(schedule.get('name')))
    output.print_md('Header rows: {}  Columns: {}'.format(
        header.get('number_of_rows'),
        header.get('number_of_columns')))
    output.print_md('JSON: `{}`'.format(json_path))
    output.print_md('CSV: `{}`'.format(csv_path))
    cells = header.get('cells') or []
    if cells:
        preview = [
            [
                cell.get('row_offset'),
                cell.get('column_offset'),
                cell.get('text'),
                cell.get('column_width_feet'),
                cell.get('row_height_feet'),
            ]
            for cell in cells[:40]
        ]
        output.print_table(
            preview,
            columns=['Row Offset', 'Column Offset', 'Text', 'Column Width Feet', 'Row Height Feet'])
    if inspection.get('warnings'):
        output.print_md('## Warnings')
        output.print_table([[item] for item in inspection['warnings']], columns=['Warning'])


def main():
    document = revit.doc
    output = script.get_output()
    schedule = _select_schedule(document)
    if schedule is None:
        return
    folder = forms.pick_folder(title='Select folder for schedule header inspection')
    if not folder:
        return
    if not os.path.isdir(folder):
        forms.alert('Select an existing export folder.', title=COMMAND_TITLE, warn_icon=True)
        return

    inspection = _inspection_record(document, schedule)
    timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    base_name = '{}_header_inspection_{}'.format(_slug(_element_name(schedule)), timestamp)
    json_path = os.path.join(folder, base_name + '.json')
    csv_path = os.path.join(folder, base_name.replace('_header_inspection_', '_header_cells_') + '.csv')
    _write_json(json_path, inspection)
    _write_csv(csv_path, inspection)
    _print_report(output, inspection, json_path, csv_path)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        output = script.get_output()
        output.print_md('# {}'.format(COMMAND_TITLE))
        output.print_md('The command stopped before it could finish.')
        output.print_md('```')
        output.print_md(traceback.format_exc())
        output.print_md('```')
        forms.alert(
            'Inspect Schedule Header stopped with an error. Review the pyRevit output window for details.',
            title=COMMAND_TITLE,
            warn_icon=True)
