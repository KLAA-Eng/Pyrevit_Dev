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
    EXCLUSIONS_KEY,
    EXCLUSION_SUMMARIES_KEY,
    FLOORS_KEY,
    FLOOR_TYPE_SUMMARIES_KEY,
    FAMILY_TYPE_SUMMARIES_KEY,
    CATEGORY_SUMMARIES_KEY,
    LEVEL_SUMMARIES_KEY,
    STEEL_KEY,
    HistoryCsvError,
    export_set_paths,
    raw_history_csv_rows,
    summary_history_csv_rows,
    workbook_path_for_folder,
    write_history_export_set,
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


def _export_history_csv_and_workbook(output, result, steel_records, floor_records, adapter_skips, metadata, export_mode):
    folder = _history_folder_for_mode(export_mode)
    if not folder:
        return None
    now = datetime.datetime.now()
    run_timestamp = now.strftime('%Y-%m-%dT%H:%M:%S')
    run_id = now.strftime('%Y%m%d-%H%M%S')
    rows_by_key = raw_history_csv_rows(
        steel_records, floor_records, adapter_skips, metadata, run_id, run_timestamp)
    rows_by_key.update(summary_history_csv_rows(result, metadata, run_id, run_timestamp))
    try:
        row_counts = write_history_export_set(folder, rows_by_key, export_mode)
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

    paths = export_set_paths(folder)
    output.print_md('## CSV Raw Export')
    output.print_md('Mode: {}'.format('Append' if export_mode == RUN_APPEND else 'Initialize'))
    output.print_md('Steel rows written: {}'.format(row_counts.get(STEEL_KEY, 0)))
    output.print_md('Floor rows written: {}'.format(row_counts.get(FLOORS_KEY, 0)))
    output.print_md('Exclusion rows written: {}'.format(row_counts.get(EXCLUSIONS_KEY, 0)))
    output.print_md('Level summary rows written: {}'.format(row_counts.get(LEVEL_SUMMARIES_KEY, 0)))
    output.print_md('Category summary rows written: {}'.format(row_counts.get(CATEGORY_SUMMARIES_KEY, 0)))
    output.print_md('Family/type summary rows written: {}'.format(row_counts.get(FAMILY_TYPE_SUMMARIES_KEY, 0)))
    output.print_md('Floor-type summary rows written: {}'.format(row_counts.get(FLOOR_TYPE_SUMMARIES_KEY, 0)))
    output.print_md('Excluded/unavailable summary rows written: {}'.format(row_counts.get(EXCLUSION_SUMMARIES_KEY, 0)))
    output.print_md('Steel CSV: `{}`'.format(paths[STEEL_KEY]))
    output.print_md('Floor CSV: `{}`'.format(paths[FLOORS_KEY]))
    output.print_md('Exclusions CSV: `{}`'.format(paths[EXCLUSIONS_KEY]))
    output.print_md('Level summaries CSV: `{}`'.format(paths[LEVEL_SUMMARIES_KEY]))
    output.print_md('Category summaries CSV: `{}`'.format(paths[CATEGORY_SUMMARIES_KEY]))
    output.print_md('Family/type summaries CSV: `{}`'.format(paths[FAMILY_TYPE_SUMMARIES_KEY]))
    output.print_md('Floor-type summaries CSV: `{}`'.format(paths[FLOOR_TYPE_SUMMARIES_KEY]))
    output.print_md('Excluded/unavailable summaries CSV: `{}`'.format(paths[EXCLUSION_SUMMARIES_KEY]))
    workbook_status = _ensure_history_workbook(folder)
    if workbook_status['warning']:
        output.print_md('Workbook warning: {}'.format(workbook_status['warning']))
    elif workbook_status['created']:
        output.print_md('Workbook created: `{}`'.format(workbook_status['path']))
    else:
        output.print_md('Workbook already exists: `{}`'.format(workbook_status['path']))
    return folder


def _history_folder_for_mode(export_mode):
    title = 'Select folder for Steel PSF raw CSV files'
    if export_mode == RUN_APPEND:
        title = 'Select Steel PSF raw CSV folder to append'
    return forms.pick_folder(title=title)


def _ensure_history_workbook(folder_path):
    workbook_path = workbook_path_for_folder(folder_path)
    if os.path.exists(workbook_path):
        return {'path': workbook_path, 'created': False, 'warning': None}
    try:
        _create_history_workbook(folder_path, workbook_path)
    except Exception as error:
        return {'path': workbook_path, 'created': False, 'warning': str(error)}
    return {'path': workbook_path, 'created': True, 'warning': None}


def _create_history_workbook(folder_path, workbook_path):
    import clr
    try:
        clr.AddReference('Microsoft.Office.Interop.Excel')
    except Exception:
        clr.AddReferenceByName(
            'Microsoft.Office.Interop.Excel, Version=11.0.0.0, '
            'Culture=neutral, PublicKeyToken=71e9bce111e9429c')
    from Microsoft.Office.Interop import Excel

    max_chart_rows = 2000
    paths = export_set_paths(folder_path)
    excel = Excel.ApplicationClass()
    excel.Visible = False
    excel.DisplayAlerts = False
    workbook = None
    try:
        workbook = excel.Workbooks.Add()
        steel_sheet = workbook.Worksheets[1]
        _connect_csv_sheet(steel_sheet, 'Steel Raw', paths[STEEL_KEY], 'SteelPSFRawSteel')
        floor_sheet = workbook.Worksheets.Add(After=steel_sheet)
        _connect_csv_sheet(floor_sheet, 'Floor Raw', paths[FLOORS_KEY], 'SteelPSFRawFloors')
        exclusion_sheet = workbook.Worksheets.Add(After=floor_sheet)
        _connect_csv_sheet(exclusion_sheet, 'Exclusion Raw', paths[EXCLUSIONS_KEY], 'SteelPSFRawExclusions')
        level_summary_sheet = workbook.Worksheets.Add(After=exclusion_sheet)
        _connect_csv_sheet(level_summary_sheet, 'Level Summaries', paths[LEVEL_SUMMARIES_KEY], 'SteelPSFLevelSummaries')
        category_summary_sheet = workbook.Worksheets.Add(After=level_summary_sheet)
        _connect_csv_sheet(category_summary_sheet, 'Category Summaries', paths[CATEGORY_SUMMARIES_KEY], 'SteelPSFCategorySummaries')
        family_type_summary_sheet = workbook.Worksheets.Add(After=category_summary_sheet)
        _connect_csv_sheet(family_type_summary_sheet, 'Family Type Summaries', paths[FAMILY_TYPE_SUMMARIES_KEY], 'SteelPSFFamilyTypeSummaries')
        floor_type_summary_sheet = workbook.Worksheets.Add(After=family_type_summary_sheet)
        _connect_csv_sheet(floor_type_summary_sheet, 'Floor Type Summaries', paths[FLOOR_TYPE_SUMMARIES_KEY], 'SteelPSFFloorTypeSummaries')
        exclusion_summary_sheet = workbook.Worksheets.Add(After=floor_type_summary_sheet)
        _connect_csv_sheet(exclusion_summary_sheet, 'Excluded Unavailable', paths[EXCLUSION_SUMMARIES_KEY], 'SteelPSFExcludedUnavailable')

        pivot_sheet = workbook.Worksheets.Add(After=exclusion_summary_sheet)
        pivot_sheet.Name = 'Pivot Tables'
        _populate_pivot_tables(workbook, pivot_sheet, steel_sheet, floor_sheet, exclusion_sheet,
                               level_summary_sheet, category_summary_sheet, family_type_summary_sheet,
                               floor_type_summary_sheet, exclusion_summary_sheet)

        summary_sheet = workbook.Worksheets.Add(After=pivot_sheet)
        summary_sheet.Name = 'Pivot Summaries'
        _populate_pivot_summary_sheet(summary_sheet, max_chart_rows)

        charts = workbook.Worksheets.Add(After=summary_sheet)
        charts.Name = 'Steel PSF Charts'
        _add_line_chart(charts, summary_sheet, 'Steel PSF - PSF History', 'A1:C{}'.format(max_chart_rows + 1), 20, 20)
        _add_line_chart(charts, summary_sheet, 'Steel PSF - Steel Weight History', 'E1:G{}'.format(max_chart_rows + 1), 20, 260)
        _add_line_chart(charts, summary_sheet, 'Steel PSF - Floor Area History', 'I1:K{}'.format(max_chart_rows + 1), 20, 500)
        workbook.SaveAs(workbook_path)
    finally:
        if workbook is not None:
            workbook.Close(False)
        excel.Quit()


def _connect_csv_sheet(sheet, sheet_name, csv_path, table_name):
    sheet.Name = sheet_name
    query_table = sheet.QueryTables.Add('TEXT;{}'.format(csv_path), sheet.Range('A1'))
    query_table.Name = table_name + 'Csv'
    query_table.TextFileParseType = 1
    query_table.TextFileCommaDelimiter = True
    query_table.RefreshOnFileOpen = True
    query_table.Refresh(False)
    try:
        sheet.ListObjects.Add(1, sheet.UsedRange, None, 1).Name = table_name
    except Exception:
        pass
    sheet.Columns.AutoFit()


def _populate_pivot_summary_sheet(sheet, max_chart_rows):
    headers = [
        ('A1', 'Run Timestamp'), ('B1', 'Level'), ('C1', 'PSF'),
        ('E1', 'Run Timestamp'), ('F1', 'Level'), ('G1', 'Steel Weight'),
        ('I1', 'Run Timestamp'), ('J1', 'Level'), ('K1', 'Floor Area'),
        ('M1', 'Run Timestamp'), ('N1', 'Reason'), ('O1', 'Family Type'), ('P1', 'Count'),
    ]
    for cell, value in headers:
        sheet.Range(cell).Value2 = value
    for row in range(2, max_chart_rows + 2):
        sheet.Range('E{}'.format(row)).Formula = '=IF(\'Steel Raw\'!$N{}="Eligible",\'Steel Raw\'!$B{},NA())'.format(row, row)
        sheet.Range('F{}'.format(row)).Formula = '=IF(\'Steel Raw\'!$N{}="Eligible",\'Steel Raw\'!$H{},NA())'.format(row, row)
        sheet.Range('G{}'.format(row)).Formula = '=IF(\'Steel Raw\'!$N{}="Eligible",\'Steel Raw\'!$M{},NA())'.format(row, row)
        sheet.Range('I{}'.format(row)).Formula = '=IF(\'Floor Raw\'!$K{}="Eligible",\'Floor Raw\'!$B{},NA())'.format(row, row)
        sheet.Range('J{}'.format(row)).Formula = '=IF(\'Floor Raw\'!$K{}="Eligible",\'Floor Raw\'!$H{},NA())'.format(row, row)
        sheet.Range('K{}'.format(row)).Formula = '=IF(\'Floor Raw\'!$K{}="Eligible",\'Floor Raw\'!$J{},NA())'.format(row, row)
        sheet.Range('A{}'.format(row)).Formula = '=E{}'.format(row)
        sheet.Range('B{}'.format(row)).Formula = '=F{}'.format(row)
        sheet.Range('C{}'.format(row)).Formula = '=IFERROR(G{}/SUMIFS($K:$K,$I:$I,E{},$J:$J,F{}),NA())'.format(row, row, row)
        sheet.Range('M{}'.format(row)).Formula = '=IF(\'Exclusion Raw\'!$F{}<>"",\'Exclusion Raw\'!$B{},NA())'.format(row, row)
        sheet.Range('N{}'.format(row)).Formula = '=IF(\'Exclusion Raw\'!$F{}<>"",\'Exclusion Raw\'!$M{},NA())'.format(row, row)
        sheet.Range('O{}'.format(row)).Formula = '=IF(\'Exclusion Raw\'!$F{}<>"",\'Exclusion Raw\'!$K{},NA())'.format(row, row)
        sheet.Range('P{}'.format(row)).Formula = '=IF(\'Exclusion Raw\'!$F{}<>"",\'Exclusion Raw\'!$O{},NA())'.format(row, row)
    sheet.Columns.AutoFit()


def _populate_pivot_tables(workbook, pivot_sheet, steel_sheet, floor_sheet, exclusion_sheet,
                           level_summary_sheet, category_summary_sheet, family_type_summary_sheet,
                           floor_type_summary_sheet, exclusion_summary_sheet):
    pivot_sheet.Range('A1').Value2 = 'Steel Weight By Run And Level'
    pivot_sheet.Range('A18').Value2 = 'Floor Area By Run And Level'
    pivot_sheet.Range('A35').Value2 = 'Exclusions By Run, Reason, And Family Type'
    pivot_sheet.Range('A52').Value2 = 'Output Level Summaries'
    pivot_sheet.Range('A69').Value2 = 'Output Category Summaries'
    pivot_sheet.Range('A86').Value2 = 'Output Family/Type Summaries'
    pivot_sheet.Range('A103').Value2 = 'Output Floor-Type Summaries'
    pivot_sheet.Range('A120').Value2 = 'Output Excluded Or Unavailable Summaries'
    try:
        _add_pivot_table(
            workbook, steel_sheet, pivot_sheet.Range('A2'), 'SteelWeightPivot',
            ['RunTimestamp', 'LevelName'], 'ComputedPounds', 'Sum of ComputedPounds',
            'EligibilityStatus', 'Eligible')
        _add_pivot_table(
            workbook, floor_sheet, pivot_sheet.Range('A19'), 'FloorAreaPivot',
            ['RunTimestamp', 'LevelName'], 'AreaSquareFeet', 'Sum of AreaSquareFeet',
            'EligibilityStatus', 'Eligible')
        _add_pivot_table(
            workbook, exclusion_sheet, pivot_sheet.Range('A36'), 'ExclusionsPivot',
            ['RunTimestamp', 'Reason', 'FamilyType'], 'Count', 'Count of Exclusions',
            None, None)
        _add_pivot_table(
            workbook, level_summary_sheet, pivot_sheet.Range('A53'), 'OutputLevelSummariesPivot',
            ['RunTimestamp', 'LevelName'], 'SteelWeightLb', 'Sum of SteelWeightLb',
            None, None)
        _add_pivot_table(
            workbook, category_summary_sheet, pivot_sheet.Range('A70'), 'OutputCategorySummariesPivot',
            ['RunTimestamp', 'LevelName', 'Category'], 'SteelWeightLb', 'Sum of SteelWeightLb',
            None, None)
        _add_pivot_table(
            workbook, family_type_summary_sheet, pivot_sheet.Range('A87'), 'OutputFamilyTypeSummariesPivot',
            ['RunTimestamp', 'LevelName', 'FamilyType'], 'SteelWeightLb', 'Sum of SteelWeightLb',
            None, None)
        _add_pivot_table(
            workbook, floor_type_summary_sheet, pivot_sheet.Range('A104'), 'OutputFloorTypeSummariesPivot',
            ['RunTimestamp', 'LevelName', 'FloorType'], 'FloorAreaSf', 'Sum of FloorAreaSf',
            None, None)
        _add_pivot_table(
            workbook, exclusion_summary_sheet, pivot_sheet.Range('A121'), 'OutputExcludedUnavailablePivot',
            ['RunTimestamp', 'Reason', 'LevelName', 'FamilyType'], 'Count', 'Sum of Count',
            None, None)
    except Exception:
        pivot_sheet.Range('A138').Value2 = 'PivotTable creation failed. Refresh raw data tabs and build pivots from the CSV-backed tables.'
    pivot_sheet.Columns.AutoFit()


def _add_pivot_table(workbook, source_sheet, target_range, pivot_name,
                     row_fields, data_field, data_caption, page_field, page_value):
    pivot_cache = workbook.PivotCaches().Create(1, source_sheet.UsedRange)
    pivot_table = pivot_cache.CreatePivotTable(target_range, pivot_name)
    for field_name in row_fields:
        field = pivot_table.PivotFields(field_name)
        field.Orientation = 1
    if page_field:
        field = pivot_table.PivotFields(page_field)
        field.Orientation = 3
        try:
            field.CurrentPage = page_value
        except Exception:
            pass
    pivot_table.AddDataField(pivot_table.PivotFields(data_field), data_caption, -4157)
    return pivot_table


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
            output, result, steel_records, area_records, steel_skips + floor_skips, metadata, export_mode)
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
