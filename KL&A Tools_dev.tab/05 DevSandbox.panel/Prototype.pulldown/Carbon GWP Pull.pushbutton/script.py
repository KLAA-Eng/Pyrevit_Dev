# -*- coding: utf-8 -*-
"""Export Carbon GWP schedules and write post-processed values to Revit."""
from __future__ import print_function

import os
import sys
import traceback

from pyrevit import DB, forms, revit, script


COMMAND_TITLE = 'Carbon GWP Pull'


def _extension_root(path):
    current = os.path.abspath(path)
    while True:
        if current.lower().endswith('.extension'):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return os.path.abspath(path)
        current = parent


EXTENSION_ROOT = _extension_root(__file__)
LIB_DIR = os.path.join(EXTENSION_ROOT, 'lib')
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from GUI.forms import select_from_dict
from carbon_gwp.workflow import (
    CARBON_PIE_FAMILY_NAME,
    DEFAULT_EXPORT_CONTAINER_PATH,
    DEFAULT_POST_PROCESSING_PATH,
    DEFAULT_SCHEDULE_NAMES,
    EXPORT_WORKSHEET_NAME,
    normalize_grid,
    parameter_value_pairs_from_export_rows,
    uniquify_worksheet_names,
    validate_parameter_value_pairs,
    worksheet_name_for_schedule,
)


try:
    TEXT_TYPES = (unicode,)
except NameError:
    TEXT_TYPES = (str,)


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


def _select_schedules(document):
    options = _schedule_options(document)
    if not options:
        forms.alert('No schedules were found in the active model.', title=COMMAND_TITLE, warn_icon=True)
        return None

    selected = select_from_dict(
        options,
        title=COMMAND_TITLE,
        label='Select exactly three schedules to export:',
        button_name='Use Schedules',
        version='DevSandbox Prototype',
        SelectMultiple=True,
        initial_checked_names=DEFAULT_SCHEDULE_NAMES,
    )
    if not selected:
        return None
    if not isinstance(selected, list):
        selected = [selected]
    if len(selected) != 3:
        forms.alert(
            'Select exactly three schedules. You selected {}.'.format(len(selected)),
            title=COMMAND_TITLE,
            warn_icon=True)
        return None
    return selected


def _pick_workbook(title, default_path):
    init_dir = os.path.dirname(default_path) if default_path and os.path.isdir(os.path.dirname(default_path)) else None
    picked = forms.pick_file(file_ext='xlsx', init_dir=init_dir, title=title)
    if picked:
        return picked
    picked = forms.pick_file(file_ext='xlsm', init_dir=init_dir, title=title)
    return picked


def _load_excel_application():
    import clr
    try:
        clr.AddReference('Microsoft.Office.Interop.Excel')
    except Exception:
        clr.AddReferenceByName(
            'Microsoft.Office.Interop.Excel, Version=11.0.0.0, '
            'Culture=neutral, PublicKeyToken=71e9bce111e9429c')
    from Microsoft.Office.Interop import Excel
    return Excel.ApplicationClass()


def _worksheet_by_name(workbook, worksheet_name):
    for index in range(1, workbook.Worksheets.Count + 1):
        worksheet = workbook.Worksheets[index]
        if worksheet.Name == worksheet_name:
            return worksheet
    return None


def _ensure_worksheet(workbook, worksheet_name):
    worksheet = _worksheet_by_name(workbook, worksheet_name)
    if worksheet is not None:
        return worksheet
    worksheet = workbook.Worksheets.Add(After=workbook.Worksheets[workbook.Worksheets.Count])
    worksheet.Name = worksheet_name
    return worksheet


def _clear_worksheet(worksheet):
    try:
        worksheet.Cells.Clear()
    except Exception:
        worksheet.UsedRange.Clear()


def _write_grid_to_worksheet(worksheet, grid):
    _clear_worksheet(worksheet)
    if not grid:
        return
    row_count = len(grid)
    column_count = max([len(row) for row in grid] or [0])
    if column_count == 0:
        return
    for row_index, row in enumerate(grid, start=1):
        for column_index in range(1, column_count + 1):
            value = row[column_index - 1] if column_index - 1 < len(row) else ''
            worksheet.Cells[row_index, column_index].Value2 = value
    try:
        worksheet.Columns.AutoFit()
    except Exception:
        pass


def _schedule_cell_text(schedule, section_type, section, row, column):
    try:
        return _safe_text(schedule.GetCellText(section_type, row, column))
    except Exception:
        pass
    for method_name in ('GetCellText', 'GetCellCalculatedValue'):
        try:
            value = getattr(section, method_name)(row, column)
            return _safe_text(value)
        except Exception:
            pass
    return ''


def _section_rows(schedule, section_type):
    try:
        section = schedule.GetTableData().GetSectionData(section_type)
    except Exception:
        return []
    first_row = getattr(section, 'FirstRowNumber', None)
    last_row = getattr(section, 'LastRowNumber', None)
    first_column = getattr(section, 'FirstColumnNumber', None)
    last_column = getattr(section, 'LastColumnNumber', None)
    if None in (first_row, last_row, first_column, last_column):
        return []
    rows = []
    for row in range(int(first_row), int(last_row) + 1):
        values = []
        for column in range(int(first_column), int(last_column) + 1):
            values.append(_schedule_cell_text(schedule, section_type, section, row, column))
        rows.append(values)
    return rows


def _schedule_table_grid(schedule):
    rows = []
    rows.extend(_section_rows(schedule, DB.SectionType.Header))
    rows.extend(_section_rows(schedule, DB.SectionType.Body))
    return normalize_grid(rows)


def _export_schedules_to_workbook(workbook_path, schedules):
    excel = _load_excel_application()
    excel.Visible = False
    excel.DisplayAlerts = False
    workbook = None
    exports = []
    try:
        if not os.path.isfile(workbook_path):
            workbook = excel.Workbooks.Add()
            workbook.SaveAs(workbook_path)
        else:
            workbook = excel.Workbooks.Open(workbook_path)
        raw_sheet_names = [worksheet_name_for_schedule(_element_name(schedule)) for schedule in schedules]
        sheet_names = uniquify_worksheet_names(raw_sheet_names)
        for schedule, sheet_name in zip(schedules, sheet_names):
            grid = _schedule_table_grid(schedule)
            worksheet = _ensure_worksheet(workbook, sheet_name)
            _write_grid_to_worksheet(worksheet, grid)
            exports.append({
                'schedule_name': _element_name(schedule),
                'worksheet_name': sheet_name,
                'rows': len(grid),
                'columns': max([len(row) for row in grid] or [0]),
            })
        workbook.Save()
        return exports
    finally:
        if workbook is not None:
            workbook.Close(True)
        excel.Quit()


def _com_range_values_to_rows(values, row_count, column_count):
    if values is None:
        return normalize_grid([])
    if row_count == 1 and column_count == 1:
        return normalize_grid([[values]])
    rows = []
    row_lower_bound = 1
    column_lower_bound = 1
    try:
        row_lower_bound = int(values.GetLowerBound(0))
        column_lower_bound = int(values.GetLowerBound(1))
    except Exception:
        pass
    for row_index in range(1, row_count + 1):
        row = []
        for column_index in range(1, column_count + 1):
            try:
                if hasattr(values, 'GetValue'):
                    row.append(values.GetValue(
                        row_lower_bound + row_index - 1,
                        column_lower_bound + column_index - 1))
                else:
                    row.append(values[
                        row_lower_bound + row_index - 1,
                        column_lower_bound + column_index - 1])
            except Exception:
                row.append(None)
        rows.append(row)
    return normalize_grid(rows)


def _read_export_rows(workbook_path):
    excel = _load_excel_application()
    excel.Visible = False
    excel.DisplayAlerts = False
    workbook = None
    try:
        workbook = excel.Workbooks.Open(workbook_path, ReadOnly=True)
        try:
            workbook.RefreshAll()
        except Exception:
            pass
        try:
            excel.CalculateUntilAsyncQueriesDone()
        except Exception:
            pass
        try:
            excel.CalculateFullRebuild()
        except Exception:
            try:
                excel.Calculate()
            except Exception:
                pass
        worksheet = _worksheet_by_name(workbook, EXPORT_WORKSHEET_NAME)
        if worksheet is None:
            raise ValueError('Worksheet not found: {}'.format(EXPORT_WORKSHEET_NAME))
        used_range = worksheet.UsedRange
        row_count = int(used_range.Rows.Count)
        column_count = int(used_range.Columns.Count)
        rows = _com_range_values_to_rows(used_range.Value2, row_count, column_count)
        return rows
    finally:
        if workbook is not None:
            workbook.Close(False)
        excel.Quit()


def _family_symbols_by_family_name(document, family_name):
    symbols = []
    collector = DB.FilteredElementCollector(document).OfClass(DB.FamilySymbol)
    for symbol in collector:
        family = getattr(symbol, 'Family', None)
        if family is not None and _element_name(family) == family_name:
            symbols.append(symbol)
    return symbols


def _set_parameter_value(parameter, value):
    if parameter is None:
        return False, 'missing parameter'
    if getattr(parameter, 'IsReadOnly', False):
        return False, 'read-only parameter'
    storage_type = parameter.StorageType
    text = _safe_text(value)
    try:
        if storage_type == DB.StorageType.String:
            parameter.Set(text)
        elif storage_type == DB.StorageType.Integer:
            parameter.Set(int(float(text)) if text else 0)
        elif storage_type == DB.StorageType.Double:
            parameter.Set(float(text) if text else 0.0)
        elif storage_type == DB.StorageType.ElementId:
            parameter.Set(DB.ElementId(int(float(text))))
        else:
            return False, 'unsupported storage type'
    except Exception as error:
        return False, _safe_text(error)
    return True, ''


def _write_family_type_parameters(symbols, pairs):
    successes = []
    skips = []
    for symbol in symbols:
        symbol_name = _element_name(symbol)
        for pair in pairs:
            parameter_name = pair['parameter_name']
            parameter = symbol.LookupParameter(parameter_name)
            ok, reason = _set_parameter_value(parameter, pair['value'])
            if ok:
                successes.append([symbol_name, parameter_name, pair['value']])
            else:
                skips.append([symbol_name, parameter_name, reason])
    return successes, skips


def _print_report(output, metadata, exports, valid_pairs, skipped_rows, successes, write_skips):
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('Export container workbook: `{}`'.format(metadata['export_workbook']))
    output.print_md('Post-processing workbook: `{}`'.format(metadata['post_processing_workbook']))
    output.print_md('Target family: `{}`'.format(CARBON_PIE_FAMILY_NAME))
    output.print_md('Family types found: {}'.format(metadata['family_type_count']))
    output.print_md('Parameter/value pairs attempted per type: {}'.format(len(valid_pairs)))
    output.print_md('Successful writes: {}'.format(len(successes)))
    if exports:
        output.print_md('## Schedule Exports')
        output.print_table(
            [[item['schedule_name'], item['worksheet_name'], item['rows'], item['columns']] for item in exports],
            columns=['Schedule', 'Worksheet', 'Rows', 'Columns'])
    if valid_pairs:
        output.print_md('## Export Sheet Parameter Values')
        output.print_table(
            [[pair['row'], pair['parameter_name'], pair['value']] for pair in valid_pairs],
            columns=['Row', 'Parameter', 'Value'])
    if skipped_rows:
        output.print_md('## Skipped Export Rows')
        output.print_table(
            [[item.get('row'), item.get('reason'), item.get('value', '')] for item in skipped_rows],
            columns=['Row', 'Reason', 'Value'])
    if write_skips:
        output.print_md('## Skipped Parameter Writes')
        output.print_table(write_skips, columns=['Family Type', 'Parameter', 'Reason'])
    if successes:
        output.print_md('## Successful Writes')
        output.print_table(successes, columns=['Family Type', 'Parameter', 'Value'])


def main():
    output = script.get_output()
    document = revit.doc

    schedules = _select_schedules(document)
    if not schedules:
        return

    export_workbook = _pick_workbook('Select Team Carbon GWP export container workbook',
                                     DEFAULT_EXPORT_CONTAINER_PATH)
    if not export_workbook:
        return
    post_processing_workbook = _pick_workbook('Select Team Carbon GWP post-processing workbook',
                                             DEFAULT_POST_PROCESSING_PATH)
    if not post_processing_workbook:
        return
    if not os.path.isfile(post_processing_workbook):
        forms.alert('Post-processing workbook not found:\n{}'.format(post_processing_workbook),
                    title=COMMAND_TITLE, warn_icon=True)
        return

    exports = _export_schedules_to_workbook(export_workbook, schedules)
    export_rows = _read_export_rows(post_processing_workbook)
    pairs, skipped_rows = parameter_value_pairs_from_export_rows(export_rows)
    valid_pairs, validation_skips = validate_parameter_value_pairs(pairs)
    skipped_rows.extend(validation_skips)
    if not valid_pairs:
        forms.alert('No parameter/value pairs were found on the Export worksheet.',
                    title=COMMAND_TITLE, warn_icon=True)
        return

    symbols = _family_symbols_by_family_name(document, CARBON_PIE_FAMILY_NAME)
    if not symbols:
        forms.alert('Family not found in active model: {}'.format(CARBON_PIE_FAMILY_NAME),
                    title=COMMAND_TITLE, warn_icon=True)
        return

    with revit.Transaction('Carbon GWP Pull - Write Family Type Parameters'):
        successes, write_skips = _write_family_type_parameters(symbols, valid_pairs)

    metadata = {
        'export_workbook': export_workbook,
        'post_processing_workbook': post_processing_workbook,
        'family_type_count': len(symbols),
    }
    _print_report(output, metadata, exports, valid_pairs, skipped_rows, successes, write_skips)


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
            'Carbon GWP Pull stopped with an error. Review the pyRevit output window for details.',
            title=COMMAND_TITLE,
            warn_icon=True)
