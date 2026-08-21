# -*- coding: utf-8 -*-
"""Import the Concrete Mix workbook block into a Revit schedule header."""
from __future__ import print_function

import os
import sys
import traceback

from pyrevit import DB, forms, revit, script


COMMAND_TITLE = 'Concrete Mix Header'
EXAMPLE_EXCEL_PATH = (
    r'J:\Standards Committees\Team Dynamo\_Scripting\Script Sandbox'
    r'\LTM Sandbox\24_Conc Mix Table\Concrete Mix Design Requirements\_260626.xlsm'
)

# Prototype tuning values. These should be adjusted after inspecting the real workbook.
EXCEL_TABLE_NAME = 'tblMixHistory'
EXCEL_WORKSHEET_NAME = ''
CLEAR_EXISTING_HEADER_TEXT = True
IMPORT_START_ROW_OFFSET = 3
IMPORT_START_COLUMN_OFFSET = 0
TEMPLATE_MIX_ROW_COUNT = 30
TEMPLATE_COLUMN_COUNT = 11
PRESERVE_NOTES_START_ROW_OFFSET = 33
COLUMN_WIDTHS_FEET = [
    0.021795362256215287,
    0.10374592433958478,
    0.06015938453670739,
    0.047705688906404017,
    0.030966850693630685,
    0.030966850693630685,
    0.062770643297900025,
    0.049898476712277338,
    0.02615443470745835,
    0.02615443470745828,
    0.041847095531933352,
]


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
from concrete_mix_schedule_header import (
    build_write_plan,
    build_mix_history_schedule_grid,
    element_match_key,
    non_empty_cell_count,
    normalize_grid,
)


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


def _excel_path():
    default_dir = os.path.dirname(EXAMPLE_EXCEL_PATH)
    init_dir = default_dir if os.path.isdir(default_dir) else None
    picked = forms.pick_file(
        file_ext='xlsm',
        init_dir=init_dir,
        title='Select Concrete Mix Design Requirements workbook')
    if picked:
        return picked
    picked = forms.pick_file(
        file_ext='xlsx',
        title='Select Concrete Mix Design Requirements workbook')
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
    if worksheet_name:
        for index in range(1, workbook.Worksheets.Count + 1):
            worksheet = workbook.Worksheets[index]
            if worksheet.Name == worksheet_name:
                return worksheet
        raise ValueError('Worksheet not found: {}'.format(worksheet_name))
    return workbook.Worksheets[1]


def _table_by_name(workbook, worksheet_name, table_name):
    if not table_name:
        raise ValueError('Excel table name is required.')
    worksheets = []
    if worksheet_name:
        worksheets.append(_worksheet_by_name(workbook, worksheet_name))
    else:
        for index in range(1, workbook.Worksheets.Count + 1):
            worksheets.append(workbook.Worksheets[index])

    for worksheet in worksheets:
        for index in range(1, worksheet.ListObjects.Count + 1):
            table = worksheet.ListObjects[index]
            if table.Name == table_name:
                return worksheet, table
    raise ValueError('Excel table not found: {}'.format(table_name))


def _com_range_values_to_rows(values, row_count, column_count):
    if values is None:
        return normalize_grid([], row_count, column_count)
    if row_count == 1 and column_count == 1:
        return normalize_grid([[values]], row_count, column_count)

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
    return normalize_grid(rows, row_count, column_count)


def _table_headers(table, column_count):
    headers = []
    try:
        for index in range(1, table.ListColumns.Count + 1):
            headers.append(table.ListColumns[index].Name)
    except Exception:
        headers = []
    if len(headers) == column_count and any(headers):
        return normalize_grid([headers], 1, column_count)[0]

    try:
        header_values = table.HeaderRowRange.Value2
        headers = _com_range_values_to_rows(header_values, 1, column_count)[0]
    except Exception:
        headers = []
    return normalize_grid([headers], 1, column_count)[0]


def _read_excel_table_data(workbook_path, worksheet_name, table_name):
    excel = _load_excel_application()
    excel.Visible = False
    excel.DisplayAlerts = False
    workbook = None
    try:
        workbook = excel.Workbooks.Open(workbook_path, ReadOnly=True)
        worksheet, table = _table_by_name(workbook, worksheet_name, table_name)
        data_range = table.DataBodyRange
        if data_range is None:
            raise ValueError('Excel table has no data rows: {}'.format(table_name))
        row_count = data_range.Rows.Count
        column_count = data_range.Columns.Count
        headers = _table_headers(table, column_count)
        values = data_range.Value2
        grid = _com_range_values_to_rows(values, row_count, column_count)
        return {
            'workbook_path': workbook_path,
            'worksheet_name': worksheet.Name,
            'table_name': table.Name,
            'headers': headers,
            'grid': grid,
        }
    finally:
        if workbook is not None:
            workbook.Close(False)
        excel.Quit()


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


def _target_schedule(document):
    options = _schedule_options(document)
    if not options:
        forms.alert('No schedules were found in the active model.', title=COMMAND_TITLE, warn_icon=True)
        return None
    selected = select_from_dict(
        options,
        title=COMMAND_TITLE,
        label='Select target schedule:',
        button_name='Use Schedule',
        version='DevSandbox Prototype',
        SelectMultiple=False,
    )
    if isinstance(selected, list):
        return selected[0] if selected else None
    return selected


def _ensure_header_size(header, row_count, column_count):
    warnings = []
    while header.NumberOfRows < row_count:
        try:
            header.InsertRow(header.LastRowNumber + 1)
        except Exception as error:
            warnings.append('Could not insert header row {}: {}'.format(header.NumberOfRows + 1, error))
            break
    while header.NumberOfColumns < column_count:
        try:
            header.InsertColumn(header.LastColumnNumber + 1)
        except Exception as first_error:
            try:
                header.InsertColumn(header.LastColumnNumber)
            except Exception as second_error:
                warnings.append(
                    'Could not insert header column {}: {}; fallback failed: {}'.format(
                        header.NumberOfColumns + 1, first_error, second_error))
                break
    return warnings


def _clear_destination(header, row_count, column_count):
    first_row = header.FirstRowNumber + IMPORT_START_ROW_OFFSET
    first_column = header.FirstColumnNumber + IMPORT_START_COLUMN_OFFSET
    for row_offset in range(row_count):
        for column_offset in range(column_count):
            try:
                header.SetCellText(first_row + row_offset, first_column + column_offset, '')
            except Exception:
                pass


def _clear_pair(header, row_offset):
    first_row = header.FirstRowNumber + IMPORT_START_ROW_OFFSET + row_offset
    first_column = header.FirstColumnNumber + IMPORT_START_COLUMN_OFFSET
    for pair_row_offset in (0, 1):
        for column_offset in range(TEMPLATE_COLUMN_COUNT):
            try:
                header.SetCellText(first_row + pair_row_offset, first_column + column_offset, '')
            except Exception:
                pass


def _cell_text(header, row, column):
    try:
        return header.GetCellText(row, column) or ''
    except Exception:
        return ''


def _existing_mix_pairs(header):
    first_row = header.FirstRowNumber + IMPORT_START_ROW_OFFSET
    first_column = header.FirstColumnNumber + IMPORT_START_COLUMN_OFFSET
    pairs = []
    by_key = {}
    for row_offset in range(0, TEMPLATE_MIX_ROW_COUNT, 2):
        element_text = _cell_text(header, first_row + row_offset, first_column)
        record = {
            'row_offset': row_offset,
            'element': element_text,
            'key': element_match_key(element_text),
        }
        pairs.append(record)
        if record['key'] and record['key'] not in by_key:
            by_key[record['key']] = record
    return pairs, by_key


def _mapped_grid_pairs(grid):
    pairs = []
    for row_offset in range(0, len(grid), 2):
        top = grid[row_offset]
        bottom = grid[row_offset + 1] if row_offset + 1 < len(grid) else [''] * TEMPLATE_COLUMN_COUNT
        element_text = top[0] if top else ''
        if not element_match_key(element_text):
            continue
        pairs.append({
            'source_row_offset': row_offset,
            'element': element_text,
            'key': element_match_key(element_text),
            'grid': [top, bottom],
        })
    return pairs


def _empty_pairs(existing_pairs):
    return [pair for pair in existing_pairs if not pair['key']]


def _write_pair(header, destination_row_offset, pair_grid):
    plan = build_write_plan(
        normalize_grid(pair_grid, 2, TEMPLATE_COLUMN_COUNT),
        header.FirstRowNumber + IMPORT_START_ROW_OFFSET + destination_row_offset,
        header.FirstColumnNumber + IMPORT_START_COLUMN_OFFSET)
    written = 0
    for item in plan:
        if not item['text']:
            continue
        header.SetCellText(item['row'], item['column'], item['text'])
        written += 1
    return written


def _set_column_widths(header):
    warnings = []
    first_column = header.FirstColumnNumber
    for offset, width_feet in enumerate(COLUMN_WIDTHS_FEET):
        try:
            header.SetColumnWidth(first_column + offset, float(width_feet))
        except Exception as error:
            warnings.append('Could not set column {} width: {}'.format(offset + 1, error))
    return warnings


def _write_header(schedule, grid):
    table_data = schedule.GetTableData()
    header = table_data.GetSectionData(DB.SectionType.Header)
    row_count = len(grid)
    column_count = max([len(row) for row in grid] or [0])
    if column_count > TEMPLATE_COLUMN_COUNT:
        raise RuntimeError(
            'Mapped tblMixHistory output has {} columns, but the inspected schedule template has {} header columns.'.format(
                column_count, TEMPLATE_COLUMN_COUNT))

    required_rows = IMPORT_START_ROW_OFFSET + TEMPLATE_MIX_ROW_COUNT
    required_columns = IMPORT_START_COLUMN_OFFSET + TEMPLATE_COLUMN_COUNT
    warnings = _ensure_header_size(header, required_rows, required_columns)
    if header.NumberOfRows < required_rows or header.NumberOfColumns < required_columns:
        raise RuntimeError('Schedule header is smaller than the concrete mix template import region.')

    normalized_grid = normalize_grid(grid, TEMPLATE_MIX_ROW_COUNT, TEMPLATE_COLUMN_COUNT)
    mapped_pairs = _mapped_grid_pairs(normalized_grid)
    existing_pairs, existing_by_key = _existing_mix_pairs(header)
    empty_pairs = _empty_pairs(existing_pairs)

    written = 0
    updated = []
    added = []
    unmatched = []
    for pair in mapped_pairs:
        existing_pair = existing_by_key.get(pair['key'])
        if existing_pair:
            destination_row_offset = existing_pair['row_offset']
            _clear_pair(header, destination_row_offset)
            written += _write_pair(header, destination_row_offset, pair['grid'])
            updated.append([pair['element'], destination_row_offset])
            continue
        if empty_pairs:
            empty_pair = empty_pairs.pop(0)
            destination_row_offset = empty_pair['row_offset']
            _clear_pair(header, destination_row_offset)
            written += _write_pair(header, destination_row_offset, pair['grid'])
            added.append([pair['element'], destination_row_offset])
            continue
        unmatched.append(pair['element'])

    if unmatched:
        raise RuntimeError(
            'No matching or empty Revit schedule mix row was available for: {}'.format(
                ', '.join(unmatched)))

    warnings.extend(_set_column_widths(header))
    return {'written': written, 'warnings': warnings, 'updated': updated, 'added': added}


def _print_preview(output, excel_data, schedule, grid):
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('Workbook: `{}`'.format(excel_data['workbook_path']))
    output.print_md('Worksheet: `{}`'.format(excel_data['worksheet_name']))
    output.print_md('Excel table: `{}`'.format(excel_data['table_name']))
    output.print_md('Source: Excel headers are used for mapping only; header cells and Delete controls are not imported.')
    output.print_md('Detected Excel headers: `{}`'.format(' | '.join(excel_data.get('headers') or [])))
    if excel_data.get('grid'):
        output.print_md('First raw Excel data row: `{}`'.format(' | '.join(excel_data['grid'][0])))
    output.print_md('Target schedule: `{}`'.format(_element_name(schedule)))
    output.print_md('Destination: header row offsets {}-{}; notes preserved starting at offset {}.'.format(
        IMPORT_START_ROW_OFFSET,
        IMPORT_START_ROW_OFFSET + TEMPLATE_MIX_ROW_COUNT - 1,
        PRESERVE_NOTES_START_ROW_OFFSET))
    output.print_md(
        'Import mode: search existing mix rows by normalized Element text; update matches; add unmatched rows only into empty paired slots.')
    output.print_md('Mapped output rows: {}  Columns: {}  Non-empty cells: {}'.format(
        len(grid), max([len(row) for row in grid] or [0]), non_empty_cell_count(grid)))
    output.print_table(grid, columns=['C{}'.format(index + 1) for index in range(max([len(row) for row in grid] or [0]))])


def main():
    output = script.get_output()
    document = revit.doc
    workbook_path = _excel_path()
    if not workbook_path:
        return
    if not os.path.isfile(workbook_path):
        forms.alert('Workbook not found:\n{}'.format(workbook_path), title=COMMAND_TITLE, warn_icon=True)
        return
    schedule = _target_schedule(document)
    if schedule is None:
        return

    excel_data = _read_excel_table_data(workbook_path, EXCEL_WORKSHEET_NAME, EXCEL_TABLE_NAME)
    grid, column_map = build_mix_history_schedule_grid(
        excel_data['headers'], excel_data['grid'], TEMPLATE_MIX_ROW_COUNT)
    excel_data['column_map'] = column_map
    _print_preview(output, excel_data, schedule, grid)
    if not forms.alert(
            'Write mapped output of {} rows x {} columns into the schedule header?'.format(
                len(grid), max([len(row) for row in grid] or [0])),
            title=COMMAND_TITLE,
            ok=False,
            yes=True,
            no=True):
        output.print_md('Import cancelled before modifying the schedule.')
        return

    with revit.Transaction('Import Concrete Mix Schedule Header'):
        result = _write_header(schedule, grid)

    output.print_md('## Import complete')
    output.print_md('Header cells written: {}'.format(result['written']))
    if result.get('updated'):
        output.print_md('## Updated Existing Rows')
        output.print_table(result['updated'], columns=['Element', 'Revit Mix Row Offset'])
    if result.get('added'):
        output.print_md('## Added To Empty Rows')
        output.print_table(result['added'], columns=['Element', 'Revit Mix Row Offset'])
    if result['warnings']:
        output.print_md('## Formatting warnings')
        output.print_table([[warning] for warning in result['warnings']], columns=['Warning'])


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
            'Concrete Mix Header stopped with an error. Review the pyRevit output window for details.',
            title=COMMAND_TITLE,
            warn_icon=True)
