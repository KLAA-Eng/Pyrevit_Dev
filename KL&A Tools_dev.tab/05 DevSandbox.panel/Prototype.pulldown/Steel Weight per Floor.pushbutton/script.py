# -*- coding: utf-8 -*-
"""Report host-model steel weight per level without changing the Revit model."""
from __future__ import print_function

import os
import sys
from collections import defaultdict

from Autodesk.Revit import Exceptions as RevitExceptions
from pyrevit import DB, forms, revit, script


COMMAND_TITLE = 'Steel Weight per Floor'


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


def _level_record(doc, level_id):
    if level_id is None or level_id == DB.ElementId.InvalidElementId:
        return None
    level = doc.GetElement(level_id)
    if not isinstance(level, DB.Level):
        return None
    return {'level_id': level.Id.IntegerValue, 'level_name': level.Name}


def _parameter_level_id(element, parameter_id):
    parameter = element.get_Parameter(parameter_id)
    if parameter and parameter.HasValue:
        return parameter.AsElementId()
    return None


def _assignment_level(doc, element, category_id):
    if category_id == int(DB.BuiltInCategory.OST_StructuralColumns):
        level_id = _parameter_level_id(element, DB.BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
    else:
        level_id = _parameter_level_id(element, DB.BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM)
    if level_id is None or level_id == DB.ElementId.InvalidElementId:
        level_id = element.LevelId
    return _level_record(doc, level_id)


def _density_kg_per_cubic_foot(doc, material):
    asset_id = material.StructuralAssetId
    if asset_id == DB.ElementId.InvalidElementId:
        return None
    property_set = doc.GetElement(asset_id)
    if property_set is None:
        return None
    asset = property_set.GetStructuralAsset()
    if asset is None:
        return None
    try:
        density = asset.Density
        return density if density > 0.0 else None
    finally:
        asset.Dispose()


def _material_record(doc, element, material_id, level):
    material = doc.GetElement(material_id)
    if not isinstance(material, DB.Material):
        return None, 'unresolved material'
    try:
        volume = element.GetMaterialVolume(material_id)
    except RevitExceptions.ArgumentException:
        return None, 'material volume unavailable'
    density = _density_kg_per_cubic_foot(doc, material)
    if density is None:
        return None, 'material structural-asset density unavailable'
    return {
        'element_id': element.Id.IntegerValue,
        'material_id': material.Id.IntegerValue,
        'level_id': level['level_id'],
        'level_name': level['level_name'],
        'volume_cubic_feet': volume,
        'density_kg_per_cubic_foot': density,
    }, None


def _steel_material_records(doc):
    records = []
    skipped = []
    categories = (
        DB.BuiltInCategory.OST_StructuralFraming,
        DB.BuiltInCategory.OST_StructuralColumns,
    )
    for category in categories:
        collector = DB.FilteredElementCollector(doc).OfCategory(category)
        for element in collector.WhereElementIsNotElementType():
            _collect_element_materials(doc, element, int(category), records, skipped)
    return records, skipped


def _collect_element_materials(doc, element, category_id, records, skipped):
    if not isinstance(element, DB.FamilyInstance):
        return
    if element.StructuralMaterialType != DB.Structure.StructuralMaterialType.Steel:
        skipped.append((element.Id.IntegerValue, 'not a steel family instance'))
        return
    level = _assignment_level(doc, element, category_id)
    if level is None:
        skipped.append((element.Id.IntegerValue, 'assignment level unavailable'))
        return
    try:
        material_ids = element.GetMaterialIds(False)
    except RevitExceptions.InvalidOperationException:
        skipped.append((element.Id.IntegerValue, 'material quantities unavailable'))
        return
    for material_id in material_ids:
        record, reason = _material_record(doc, element, material_id, level)
        if record is None:
            skipped.append((element.Id.IntegerValue, reason))
        else:
            records.append(record)


def _floor_area_records(doc):
    records = []
    skipped = []
    floors = DB.FilteredElementCollector(doc).OfCategory(
        DB.BuiltInCategory.OST_Floors
    ).WhereElementIsNotElementType()
    for floor in floors:
        level = _level_record(doc, floor.LevelId)
        if level is None:
            skipped.append((floor.Id.IntegerValue, 'floor level unavailable'))
            continue
        parameter = floor.get_Parameter(DB.BuiltInParameter.HOST_AREA_COMPUTED)
        area = parameter.AsDouble() if parameter and parameter.HasValue else None
        records.append({
            'element_id': floor.Id.IntegerValue,
            'material_id': None,
            'level_id': level['level_id'],
            'level_name': level['level_name'],
            'area_square_feet': area,
        })
    return records, skipped


def _print_report(output, result, adapter_skips):
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md(
        'Host-model steel framing and columns only. Weight = material volume × '
        'structural-asset density. Columns use Base Level; framing uses Reference Level.'
    )
    rows = []
    for row in result['rows']:
        rows.append([
            row['level_name'],
            '{:,.0f}'.format(row['steel_weight_lb']),
            '{:,.0f}'.format(row['floor_area_square_feet']),
            '{:.3f}'.format(row['psf']) if row['psf'] is not None else 'N/A',
        ])
    total = result['total']
    rows.append([
        'TOTAL',
        '{:,.0f}'.format(total['steel_weight_lb']),
        '{:,.0f}'.format(total['floor_area_square_feet']),
        '{:.3f}'.format(total['psf']) if total['psf'] is not None else 'N/A',
    ])
    output.print_table(rows, columns=['Level', 'Steel Weight (lb)', 'Floor Area (sf)', 'PSF'])
    _print_exclusions(output, result['excluded'], adapter_skips)


def _print_exclusions(output, aggregation_skips, adapter_skips):
    reasons = defaultdict(int)
    for item in aggregation_skips:
        reasons[item['reason']] += 1
    for unused_id, reason in adapter_skips:
        reasons[reason] += 1
    if not reasons:
        return
    output.print_md('## Excluded or unavailable data')
    output.print_table(
        [[reason, count] for reason, count in sorted(reasons.items())],
        columns=['Reason', 'Count'],
    )


def main():
    output = script.get_output()
    doc = revit.doc
    material_records, material_skips = _steel_material_records(doc)
    area_records, floor_skips = _floor_area_records(doc)
    result = aggregate_steel_weight(material_records, area_records)
    _print_report(output, result, material_skips + floor_skips)
    if not result['rows']:
        forms.alert('No eligible steel or floor data was found.', title=COMMAND_TITLE)


if __name__ == '__main__':
    main()
