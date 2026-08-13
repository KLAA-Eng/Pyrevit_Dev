# -*- coding: utf-8 -*-
"""Report host-model steel PSF summaries without changing the Revit model."""
from __future__ import print_function

import csv
import os
import sys
from collections import defaultdict

from Autodesk.Revit import Exceptions as RevitExceptions
from pyrevit import DB, forms, revit, script


COMMAND_TITLE = 'Steel PSF'


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

from steel_weight.aggregation import aggregate_steel_weight
from steel_weight.reporting import summary_csv_rows


def _level_record(doc, level_id):
    if level_id is None or level_id == DB.ElementId.InvalidElementId:
        return None
    level = doc.GetElement(level_id)
    if not isinstance(level, DB.Level):
        return None
    return {'level_id': level.Id.IntegerValue, 'level_name': level.Name}


def _assignment_level(doc, element, category_id):
    parameter_id = DB.BuiltInParameter.FAMILY_BASE_LEVEL_PARAM
    if category_id != int(DB.BuiltInCategory.OST_StructuralColumns):
        parameter_id = DB.BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM
    parameter = element.get_Parameter(parameter_id)
    level_id = parameter.AsElementId() if parameter and parameter.HasValue else element.LevelId
    return _level_record(doc, level_id)


def _first_parameter(element, parameter_id):
    parameter = element.get_Parameter(parameter_id)
    return parameter if parameter and parameter.HasValue else None


def _usable_length(element):
    location = element.Location
    if isinstance(location, DB.LocationCurve):
        return location.Curve.Length
    parameter = _first_parameter(element, DB.BuiltInParameter.INSTANCE_LENGTH_PARAM)
    return parameter.AsDouble() if parameter else None


def _nominal_weight_lb_per_foot(doc, element):
    parameter_id = DB.BuiltInParameter.STRUCTURAL_SECTION_COMMON_NOMINAL_WEIGHT
    parameter = _first_parameter(element, parameter_id)
    if parameter is None:
        type_element = doc.GetElement(element.GetTypeId())
        parameter = _first_parameter(type_element, parameter_id) if type_element else None
    if parameter is None:
        return None
    try:
        return DB.UnitUtils.ConvertFromInternalUnits(
            parameter.AsDouble(), DB.UnitTypeId.PoundsForcePerFoot)
    except (RevitExceptions.ArgumentException, RevitExceptions.InvalidOperationException):
        return None


def _family_type_label(doc, element):
    type_element = doc.GetElement(element.GetTypeId())
    if type_element is None:
        return 'Unspecified'
    family_name = getattr(type_element, 'FamilyName', '')
    return '{}: {}'.format(family_name, type_element.Name) if family_name else type_element.Name


def _steel_records(doc):
    records = []
    skipped = []
    categories = (DB.BuiltInCategory.OST_StructuralFraming, DB.BuiltInCategory.OST_StructuralColumns)
    for category in categories:
        for element in DB.FilteredElementCollector(doc).OfCategory(category).WhereElementIsNotElementType():
            _collect_steel_record(doc, element, int(category), records, skipped)
    return records, skipped


def _collect_steel_record(doc, element, category_id, records, skipped):
    if not isinstance(element, DB.FamilyInstance):
        return
    if element.StructuralMaterialType != DB.Structure.StructuralMaterialType.Steel:
        skipped.append((element.Id.IntegerValue, 'not a steel family instance'))
        return
    level = _assignment_level(doc, element, category_id)
    if level is None:
        skipped.append((element.Id.IntegerValue, 'assignment level unavailable'))
        return
    records.append({
        'element_id': element.Id.IntegerValue,
        'level_id': level['level_id'], 'level_name': level['level_name'],
        'length_feet': _usable_length(element),
        'nominal_weight_lb_per_foot': _nominal_weight_lb_per_foot(doc, element),
        'category': element.Category.Name, 'family_type': _family_type_label(doc, element),
    })


def _floor_area_records(doc):
    records = []
    skipped = []
    floors = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Floors).WhereElementIsNotElementType()
    for floor in floors:
        level = _level_record(doc, floor.LevelId)
        if level is None:
            skipped.append((floor.Id.IntegerValue, 'floor level unavailable'))
            continue
        parameter = _first_parameter(floor, DB.BuiltInParameter.HOST_AREA_COMPUTED)
        floor_type = doc.GetElement(floor.GetTypeId())
        records.append({
            'element_id': floor.Id.IntegerValue, 'level_id': level['level_id'],
            'level_name': level['level_name'],
            'area_square_feet': parameter.AsDouble() if parameter else None,
            'floor_type': floor_type.Name if floor_type else 'Unspecified',
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
    _print_summary(output, 'Category summaries', [[row['category'], _number(row['steel_weight_lb'])] for row in result['categories']], ['Category', 'Steel Weight (lb)'])
    _print_summary(output, 'Family/type summaries', [[row['family_type'], _number(row['steel_weight_lb'])] for row in result['family_types']], ['Family/type', 'Steel Weight (lb)'])
    _print_summary(output, 'Floor-type summaries', [[row['floor_type'], _number(row['floor_area_square_feet'])] for row in result['floor_types']], ['Floor type', 'Floor Area (sf)'])
    _print_exclusions(output, result['excluded'], adapter_skips)


def _print_exclusions(output, aggregation_skips, adapter_skips):
    reasons = defaultdict(int)
    for item in aggregation_skips:
        reasons[item['reason']] += 1
    for unused_id, reason in adapter_skips:
        reasons[reason] += 1
    if reasons:
        output.print_md('## Excluded or unavailable data')
        output.print_table([[reason, count] for reason, count in sorted(reasons.items())], columns=['Reason', 'Count'])


def _export_summary_csv(result, metadata):
    path = forms.save_file(file_ext='csv', title='Save Steel PSF summary CSV')
    if not path:
        return None
    try:
        with open(path, 'wb') as csv_file:
            csv.writer(csv_file).writerows(summary_csv_rows(result, metadata))
    except (IOError, OSError) as error:
        forms.alert('Could not write CSV: {}'.format(error), title=COMMAND_TITLE, warn_icon=True)
        return None
    return path


def main():
    output = script.get_output()
    doc = revit.doc
    steel_records, steel_skips = _steel_records(doc)
    area_records, floor_skips = _floor_area_records(doc)
    result = aggregate_steel_weight(steel_records, area_records)
    metadata = {'document_title': doc.Title, 'weight_basis': 'length_ft x nominal_lb_per_ft'}
    _print_report(output, result, steel_skips + floor_skips, metadata)
    csv_path = _export_summary_csv(result, metadata)
    if csv_path:
        output.print_md('Summary CSV: `{}`'.format(csv_path))
    if not result['rows']:
        forms.alert('No eligible steel or floor data was found.', title=COMMAND_TITLE)


if __name__ == '__main__':
    main()
