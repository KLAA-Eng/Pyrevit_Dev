# -*- coding: utf-8 -*-
"""Report host-model steel PSF summaries without changing the Revit model."""
from __future__ import print_function

import csv
import os
import sys
import traceback
from collections import defaultdict

from Autodesk.Revit import Exceptions as RevitExceptions
from pyrevit import DB, forms, revit, script


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

from GUI.forms import select_from_dict
from GUI.CustomAlert import show_alert
from steel_weight.aggregation import aggregate_steel_weight
from steel_weight.reporting import summary_csv_rows


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
        show_alert('No project levels were found in the active model.', title=COMMAND_TITLE,
                   is_warning=True)
        script.exit()

    level_options = {_level_label(level): level for level in levels}
    selected_levels = select_from_dict(
        level_options,
        title=COMMAND_TITLE,
        label='Select stories to review:',
        button_name='Review Selected Stories',
        version='DevSandbox Prototype',
        SelectMultiple=True,
    )
    if not selected_levels:
        show_alert('Select at least one story.', title=COMMAND_TITLE, is_warning=True)
        script.exit()
    return selected_levels


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


def _number(value):
    return '{:.3f}'.format(value) if value is not None else 'N/A'


def _print_summary(output, title, rows, columns):
    if rows:
        output.print_md('## {}'.format(title))
        output.print_table(rows, columns=columns)


def _print_report(output, result, adapter_skips, metadata):
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('Read-only host-model structural framing and columns. Pounds = usable length (ft) × nominal section weight (lb/ft).')
    output.print_table([[key, value] for key, value in sorted(metadata.items())], columns=['Metadata', 'Value'])
    level_rows = [[row['level_name'], _number(row['steel_weight_lb']), _number(row['floor_area_square_feet']), _number(row['psf'])] for row in result['rows']]
    total = result['total']
    level_rows.append(['TOTAL', _number(total['steel_weight_lb']), _number(total['floor_area_square_feet']), _number(total['psf'])])
    _print_summary(output, 'Level summaries', level_rows, ['Level', 'Steel Weight (lb)', 'Floor Area (sf)', 'PSF'])
    _print_summary(output, 'Category summaries', [
        [row['level_name'], row['category'], _number(row['steel_weight_lb'])]
        for row in result['categories']
    ], ['Level', 'Category', 'Steel Weight (lb)'])
    _print_summary(output, 'Family/type summaries', [
        [row['level_name'], row['family_type'], _number(row['steel_weight_lb'])]
        for row in result['family_types']
    ], ['Level', 'Family/type', 'Steel Weight (lb)'])
    _print_summary(output, 'Floor-type summaries', [
        [row['level_name'], row['floor_type'], _number(row['floor_area_square_feet'])]
        for row in result['floor_types']
    ], ['Level', 'Floor type', 'Floor Area (sf)'])
    _print_exclusions(output, result, adapter_skips)


def _print_exclusions(output, result, adapter_skips):
    rows = [[
        item['reason'],
        item['level_name'],
        item['category'],
        item['family_type'],
        item['count'],
        _number(item['length_feet']),
    ] for item in result.get('excluded_summaries', [])]
    adapter_reasons = defaultdict(int)
    for unused_id, reason in adapter_skips:
        adapter_reasons[reason] += 1
    for reason, count in sorted(adapter_reasons.items()):
        rows.append([reason, 'Unspecified', 'Unspecified', 'Unspecified', count, _number(0.0)])
    if rows:
        output.print_md('## Excluded or unavailable data')
        output.print_table(
            rows,
            columns=['Reason', 'Level', 'Category', 'Family/type', 'Count', 'Total Length (ft)'])


def _export_summary_csv(result, metadata):
    path = forms.save_file(file_ext='csv', title='Save Steel PSF summary CSV')
    if not path:
        return None
    try:
        with open(path, 'wb') as csv_file:
            csv.writer(csv_file).writerows(summary_csv_rows(result, metadata))
    except (IOError, OSError) as error:
        show_alert('Could not write CSV: {}'.format(error), title=COMMAND_TITLE,
                   is_warning=True)
        return None
    return path


def main():
    output = script.get_output()
    doc = revit.doc
    selected_levels = _select_stories(doc)
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
    if not result['rows']:
        show_alert('No eligible steel or floor data was found for the selected stories.',
                   title=COMMAND_TITLE)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        output = script.get_output()
        output.print_md('# {}'.format(COMMAND_TITLE))
        output.print_md('## Runtime error')
        output.print_md('    {}'.format(traceback.format_exc().replace('\n', '\n    ')))
