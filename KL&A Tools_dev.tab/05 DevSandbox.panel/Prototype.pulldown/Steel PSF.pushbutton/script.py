# -*- coding: utf-8 -*-
"""Report host-model steel PSF summaries without changing the Revit model."""
from __future__ import print_function

import datetime
import os
import sys
import traceback

from Autodesk.Revit import Exceptions as RevitExceptions
from pyrevit import DB, forms, revit, script
from System.Collections.Generic import List
import wpf


COMMAND_TITLE = 'Steel PSF'


def _element_name(element, default='Unspecified'):
    if element is None:
        return default
    try:
        name = DB.Element.Name.GetValue(element)
    except AttributeError:
        try:
            name = element.Name
        except AttributeError:
            name = None
    return name or default


def _pounds_force_per_foot_unit_id():
    if hasattr(DB, 'UnitTypeId') and hasattr(DB.UnitTypeId, 'PoundsForcePerFoot'):
        return DB.UnitTypeId.PoundsForcePerFoot
    if hasattr(DB, 'DisplayUnitType') and hasattr(DB.DisplayUnitType, 'DUT_POUNDS_FORCE_PER_FOOT'):
        return DB.DisplayUnitType.DUT_POUNDS_FORCE_PER_FOOT
    return None


def _square_feet_unit_id():
    if hasattr(DB, 'UnitTypeId') and hasattr(DB.UnitTypeId, 'SquareFeet'):
        return DB.UnitTypeId.SquareFeet
    if hasattr(DB, 'DisplayUnitType') and hasattr(DB.DisplayUnitType, 'DUT_SQUARE_FEET'):
        return DB.DisplayUnitType.DUT_SQUARE_FEET
    return None


def _element_id_value(element_id):
    if element_id is None:
        return None
    for property_name in ('Value', 'IntegerValue'):
        try:
            return int(getattr(element_id, property_name))
        except Exception:
            pass
    return None


def _is_invalid_element_id(element_id):
    invalid = DB.ElementId.InvalidElementId
    try:
        return element_id == invalid
    except Exception:
        return _element_id_value(element_id) == _element_id_value(invalid)


def _number_value(value):
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _parameter_double(parameter):
    if parameter is None:
        return None
    try:
        return _number_value(parameter.AsDouble())
    except Exception:
        return None


def _convert_from_internal_units(value, unit_id):
    number = _number_value(value)
    if number is None:
        return None
    if unit_id is None:
        return number
    try:
        return _number_value(DB.UnitUtils.ConvertFromInternalUnits(number, unit_id))
    except (RevitExceptions.ArgumentException, RevitExceptions.InvalidOperationException):
        return None
    except Exception:
        return None


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

from GUI.forms import my_WPF
from steel_weight.aggregation import aggregate_steel_weight
from steel_weight.history import (
    RUN_APPEND,
    RUN_INITIALIZE,
    RUN_ONLY,
    HistoryCsvError,
    history_csv_rows,
    initialized_csv_path,
    workbook_path_for_csv,
    write_history_csv,
)
from steel_weight.reporting import OUTPUT_INTRO, report_output_tables


class StoryListItem:
    def __init__(self, name='Unnamed', element=None, checked=False):
        self.Name = name
        self.IsChecked = checked
        self.element = element


class SteelPsfDialog(my_WPF):
    def __init__(self, items, title=COMMAND_TITLE):
        self.given_dict_items = {key: value for key, value in items.items() if key}
        self.items = self._generate_list_items()
        self.selected_items = []
        self.export_mode = RUN_ONLY
        self.add_wpf_resource()
        wpf.LoadComponent(self, os.path.join(os.path.dirname(__file__), 'SteelPsfDialog.xaml'))
        self.main_title.Text = title
        self.main_ListBox.ItemsSource = self.items
        self.ShowDialog()

    def _generate_list_items(self):
        list_of_items = List[type(StoryListItem())]()
        for name, element in sorted(self.given_dict_items.items()):
            list_of_items.Add(StoryListItem(name, element, False))
        return list_of_items

    def text_filter_updated(self, sender, e):
        filtered_list_of_items = List[type(StoryListItem())]()
        filter_keyword = self.textbox_filter.Text
        if not filter_keyword:
            self.main_ListBox.ItemsSource = self.items
            return
        for item in self.items:
            if filter_keyword.lower() in item.Name.lower():
                filtered_list_of_items.Add(item)
        self.main_ListBox.ItemsSource = filtered_list_of_items

    def UIe_ItemChecked(self, sender, e):
        return

    def select_mode(self, mode):
        list_of_items = List[type(StoryListItem())]()
        checked = True if mode == 'all' else False
        for item in self.main_ListBox.ItemsSource:
            item.IsChecked = checked
            list_of_items.Add(item)
        self.main_ListBox.ItemsSource = list_of_items

    def button_select_all(self, sender, e):
        self.select_mode('all')

    def button_select_none(self, sender, e):
        self.select_mode('none')

    def button_select(self, sender, e):
        self._finish_selection(RUN_ONLY)

    def button_initialize_csv(self, sender, e):
        self._finish_selection(RUN_INITIALIZE)

    def button_append_csv(self, sender, e):
        self._finish_selection(RUN_APPEND)

    def _finish_selection(self, export_mode):
        selected_items = []
        for item in self.main_ListBox.ItemsSource:
            if item.IsChecked:
                selected_items.append(item.element)
        self.selected_items = selected_items
        self.export_mode = export_mode
        self.textbox_filter.Text = ''
        self.Close()


def _level_record(doc, level_id):
    if level_id is None or _is_invalid_element_id(level_id):
        return None
    level = doc.GetElement(level_id)
    if not isinstance(level, DB.Level):
        return None
    return {'level_id': _element_id_value(level.Id), 'level_name': _element_name(level)}


def _assignment_level(doc, element, category_id):
    parameter_id = DB.BuiltInParameter.FAMILY_BASE_LEVEL_PARAM
    if category_id != int(DB.BuiltInCategory.OST_StructuralColumns):
        parameter_id = DB.BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM
    parameter = element.get_Parameter(parameter_id)
    level_id = element.LevelId
    try:
        if parameter and parameter.HasValue:
            level_id = parameter.AsElementId()
    except Exception:
        pass
    return _level_record(doc, level_id)


def _first_parameter(element, parameter_id):
    try:
        parameter = element.get_Parameter(parameter_id)
        return parameter if parameter and parameter.HasValue else None
    except Exception:
        return None


def _usable_length(element):
    try:
        location = element.Location
        if isinstance(location, DB.LocationCurve):
            return _number_value(location.Curve.Length)
    except Exception:
        pass
    parameter = _first_parameter(element, DB.BuiltInParameter.INSTANCE_LENGTH_PARAM)
    return _parameter_double(parameter)


def _nominal_weight_lb_per_foot(doc, element):
    parameter_id = DB.BuiltInParameter.STRUCTURAL_SECTION_COMMON_NOMINAL_WEIGHT
    parameter = _first_parameter(element, parameter_id)
    if parameter is None:
        type_element = doc.GetElement(element.GetTypeId())
        parameter = _first_parameter(type_element, parameter_id) if type_element else None
    if parameter is None:
        return None
    unit_id = _pounds_force_per_foot_unit_id()
    if unit_id is None:
        return None
    return _convert_from_internal_units(_parameter_double(parameter), unit_id)


def _floor_area_square_feet(parameter):
    return _convert_from_internal_units(_parameter_double(parameter), _square_feet_unit_id())


def _family_type_label(doc, element):
    type_element = doc.GetElement(element.GetTypeId())
    if type_element is None:
        return 'Unspecified'
    family_name = getattr(type_element, 'FamilyName', '')
    type_name = _element_name(type_element)
    return '{}: {}'.format(family_name, type_name) if family_name else type_name


def _level_label(level):
    return _element_name(level)


def _select_stories(doc):
    levels = list(DB.FilteredElementCollector(doc).OfClass(DB.Level).WhereElementIsNotElementType())
    if not levels:
        forms.alert('No project levels were found in the active model.', title=COMMAND_TITLE,
                    warn_icon=True)
        script.exit()

    level_options = {_level_label(level): level for level in levels}
    story_dialog = SteelPsfDialog(level_options)
    selected_levels = story_dialog.selected_items
    if not selected_levels:
        forms.alert('Select at least one story.', title=COMMAND_TITLE, warn_icon=True)
        script.exit()
    return selected_levels, story_dialog.export_mode


def _selected_level_ids(levels):
    return [_element_id_value(level.Id) for level in levels]


def _selected_level_names(levels):
    return [_level_label(level) for level in levels]


def _is_selected_level(level, selected_level_ids):
    return level is not None and level['level_id'] in selected_level_ids


def _steel_records(doc, selected_level_ids):
    records = []
    skipped = []
    categories = (DB.BuiltInCategory.OST_StructuralFraming, DB.BuiltInCategory.OST_StructuralColumns)
    for category in categories:
        for element in DB.FilteredElementCollector(doc).OfCategory(category).WhereElementIsNotElementType():
            _collect_steel_record(doc, element, int(category), selected_level_ids, records, skipped)
    return records, skipped


def _collect_steel_record(doc, element, category_id, selected_level_ids, records, skipped):
    if not isinstance(element, DB.FamilyInstance):
        return
    level = _assignment_level(doc, element, category_id)
    if not _is_selected_level(level, selected_level_ids):
        return
    if element.StructuralMaterialType != DB.Structure.StructuralMaterialType.Steel:
        skipped.append((_element_id_value(element.Id), 'not a steel family instance'))
        return
    records.append({
        'element_id': _element_id_value(element.Id),
        'level_id': level['level_id'], 'level_name': level['level_name'],
        'length_feet': _usable_length(element),
        'nominal_weight_lb_per_foot': _nominal_weight_lb_per_foot(doc, element),
        'category': element.Category.Name, 'family_type': _family_type_label(doc, element),
    })


def _floor_area_records(doc, selected_level_ids):
    records = []
    skipped = []
    floors = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Floors).WhereElementIsNotElementType()
    for floor in floors:
        level = _level_record(doc, floor.LevelId)
        if not _is_selected_level(level, selected_level_ids):
            continue
        parameter = _first_parameter(floor, DB.BuiltInParameter.HOST_AREA_COMPUTED)
        floor_type = doc.GetElement(floor.GetTypeId())
        records.append({
            'element_id': _element_id_value(floor.Id), 'level_id': level['level_id'],
            'level_name': level['level_name'],
            'area_square_feet': _floor_area_square_feet(parameter),
            'floor_type': _element_name(floor_type),
        })
    return records, skipped


def _print_summary(output, title, rows, columns):
    if rows:
        output.print_md('## {}'.format(title))
        output.print_table(rows, columns=columns)


def _print_report(output, result, adapter_skips, metadata):
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md(OUTPUT_INTRO)
    output.print_table([[key, value] for key, value in sorted(metadata.items())], columns=['Metadata', 'Value'])
    for table in report_output_tables(result, adapter_skips):
        _print_summary(output, table['title'], table['rows'], table['columns'])


def _export_history_csv_and_workbook(output, result, adapter_skips, metadata, export_mode):
    path = _history_csv_path_for_mode(export_mode)
    if not path:
        return None
    now = datetime.datetime.now()
    run_timestamp = now.strftime('%Y-%m-%dT%H:%M:%S')
    run_id = now.strftime('%Y%m%d-%H%M%S')
    rows = history_csv_rows(result, metadata, run_id, run_timestamp, adapter_skips)
    try:
        row_count = write_history_csv(path, rows, export_mode)
    except HistoryCsvError as error:
        forms.alert(str(error), title=COMMAND_TITLE, warn_icon=True)
        output.print_md('## CSV export stopped')
        output.print_md(str(error))
        return None
    except (IOError, OSError) as error:
        forms.alert('Could not write CSV: {}'.format(error), title=COMMAND_TITLE, warn_icon=True)
        output.print_md('## CSV export stopped')
        output.print_md('Could not write CSV: {}'.format(error))
        return None

    output.print_md('## CSV History Export')
    output.print_md('Mode: {}'.format('Append' if export_mode == RUN_APPEND else 'Initialize'))
    output.print_md('Rows written: {}'.format(row_count))
    output.print_md('CSV: `{}`'.format(path))
    workbook_status = _ensure_history_workbook(path)
    if workbook_status['warning']:
        output.print_md('Workbook warning: {}'.format(workbook_status['warning']))
    elif workbook_status['created']:
        output.print_md('Workbook created: `{}`'.format(workbook_status['path']))
    else:
        output.print_md('Workbook already exists: `{}`'.format(workbook_status['path']))
    return path


def _history_csv_path_for_mode(export_mode):
    if export_mode == RUN_INITIALIZE:
        folder = forms.pick_folder(title='Select folder for Steel PSF history files')
        if not folder:
            return None
        return initialized_csv_path(folder)
    return forms.pick_file(file_ext='csv', title='Select Steel PSF history CSV to append')


def _ensure_history_workbook(csv_path):
    workbook_path = workbook_path_for_csv(csv_path)
    if os.path.exists(workbook_path):
        return {'path': workbook_path, 'created': False, 'warning': None}
    try:
        _create_history_workbook(csv_path, workbook_path)
    except Exception as error:
        return {'path': workbook_path, 'created': False, 'warning': str(error)}
    return {'path': workbook_path, 'created': True, 'warning': None}


def _create_history_workbook(csv_path, workbook_path):
    import clr
    try:
        clr.AddReference('Microsoft.Office.Interop.Excel')
    except Exception:
        clr.AddReferenceByName(
            'Microsoft.Office.Interop.Excel, Version=11.0.0.0, '
            'Culture=neutral, PublicKeyToken=71e9bce111e9429c')
    from Microsoft.Office.Interop import Excel

    max_chart_rows = 2000
    data_sheet_name = 'Steel PSF Data'
    excel = Excel.ApplicationClass()
    excel.Visible = False
    excel.DisplayAlerts = False
    workbook = None
    try:
        workbook = excel.Workbooks.Add()
        history_sheet = workbook.Worksheets[1]
        history_sheet.Name = data_sheet_name
        query_table = history_sheet.QueryTables.Add('TEXT;{}'.format(csv_path), history_sheet.Range('A1'))
        query_table.Name = 'SteelPSFHistoryCsv'
        query_table.TextFileParseType = 1
        query_table.TextFileCommaDelimiter = True
        query_table.RefreshOnFileOpen = True
        query_table.Refresh(False)
        try:
            history_sheet.ListObjects.Add(1, history_sheet.UsedRange, None, 1).Name = 'SteelPSFHistory'
        except Exception:
            pass

        chart_data = workbook.Worksheets.Add(After=history_sheet)
        chart_data.Name = 'Steel PSF Chart Data'
        _populate_chart_data_sheet(chart_data, max_chart_rows, data_sheet_name)

        charts = workbook.Worksheets.Add(After=chart_data)
        charts.Name = 'Steel PSF Charts'
        _add_line_chart(charts, chart_data, 'Steel PSF - PSF History', 'A1:B{}'.format(max_chart_rows + 1), 20, 20)
        _add_line_chart(charts, chart_data, 'Steel PSF - Steel Weight History', 'D1:E{}'.format(max_chart_rows + 1), 20, 260)
        _add_line_chart(charts, chart_data, 'Steel PSF - Floor Area History', 'G1:H{}'.format(max_chart_rows + 1), 20, 500)
        workbook.SaveAs(workbook_path)
    finally:
        if workbook is not None:
            workbook.Close(False)
        excel.Quit()


def _populate_chart_data_sheet(sheet, max_chart_rows, data_sheet_name):
    headers = [
        ('A1', 'PSF Timestamp'), ('B1', 'PSF'),
        ('D1', 'Steel Weight Timestamp'), ('E1', 'Steel Weight'),
        ('G1', 'Floor Area Timestamp'), ('H1', 'Floor Area'),
    ]
    for cell, value in headers:
        sheet.Range(cell).Value2 = value
    quoted_data_sheet = "'{}'".format(data_sheet_name.replace("'", "''"))
    for row in range(2, max_chart_rows + 2):
        sheet.Range('A{}'.format(row)).Formula = '=IF({}!$I{}="PSF",{}!$B{},NA())'.format(quoted_data_sheet, row, quoted_data_sheet, row)
        sheet.Range('B{}'.format(row)).Formula = '=IF({}!$I{}="PSF",{}!$J{},NA())'.format(quoted_data_sheet, row, quoted_data_sheet, row)
        sheet.Range('D{}'.format(row)).Formula = '=IF({}!$I{}="Steel Weight",{}!$B{},NA())'.format(quoted_data_sheet, row, quoted_data_sheet, row)
        sheet.Range('E{}'.format(row)).Formula = '=IF({}!$I{}="Steel Weight",{}!$J{},NA())'.format(quoted_data_sheet, row, quoted_data_sheet, row)
        sheet.Range('G{}'.format(row)).Formula = '=IF({}!$I{}="Floor Area",{}!$B{},NA())'.format(quoted_data_sheet, row, quoted_data_sheet, row)
        sheet.Range('H{}'.format(row)).Formula = '=IF({}!$I{}="Floor Area",{}!$J{},NA())'.format(quoted_data_sheet, row, quoted_data_sheet, row)
    sheet.Columns.AutoFit()


def _add_line_chart(sheet, source_sheet, title, source_range, left, top):
    chart_object = sheet.ChartObjects().Add(left, top, 560, 210)
    chart = chart_object.Chart
    chart.ChartType = 65
    chart.SetSourceData(source_sheet.Range(source_range))
    chart.HasTitle = True
    chart.ChartTitle.Text = title


def main():
    output = script.get_output()
    doc = revit.doc
    selected_levels, export_mode = _select_stories(doc)
    selected_level_ids = _selected_level_ids(selected_levels)
    steel_records, steel_skips = _steel_records(doc, selected_level_ids)
    area_records, floor_skips = _floor_area_records(doc, selected_level_ids)
    result = aggregate_steel_weight(steel_records, area_records)
    metadata = {
        'document_title': doc.Title,
        'selected_story_count': str(len(selected_levels)),
        'selected_story_names': ', '.join(_selected_level_names(selected_levels)),
        'weight_basis': 'length_ft x nominal_lb_per_ft',
    }
    _print_report(output, result, steel_skips + floor_skips, metadata)
    if export_mode != RUN_ONLY:
        _export_history_csv_and_workbook(
            output, result, steel_skips + floor_skips, metadata, export_mode)
    if not result['rows']:
        forms.alert('No eligible steel or floor data was found for the selected stories.',
                    title=COMMAND_TITLE)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        output = script.get_output()
        output.print_md('# {}'.format(COMMAND_TITLE))
        output.print_md('## Runtime error')
        output.print_md('    {}'.format(traceback.format_exc().replace('\n', '\n    ')))
