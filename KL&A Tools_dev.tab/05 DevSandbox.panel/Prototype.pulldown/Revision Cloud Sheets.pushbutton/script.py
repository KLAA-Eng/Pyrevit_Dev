# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Revision\nCloud Sheets"
__version__ = "v0.0"

import traceback

from pyrevit import DB, revit, script

from revision_cloud_sheets.mapping import sheet_number_sort_key, sheets_by_cloud


COMMAND_TITLE = 'Revision Cloud Sheets'


def _element_id_value(element_id):
    for property_name in ('Value', 'IntegerValue'):
        try:
            return int(getattr(element_id, property_name))
        except Exception:
            pass
    return None


def _view_name(view):
    try:
        return revit.query.get_name(view)
    except Exception:
        return view.Name


def _sheet_label(sheet):
    return '{} - {}'.format(sheet.SheetNumber, sheet.Name)


def _project_sheets(doc):
    return [
        sheet for sheet in
        DB.FilteredElementCollector(doc)
        .OfCategory(DB.BuiltInCategory.OST_Sheets)
        .WhereElementIsNotElementType()
        .ToElements()
        if not sheet.IsPlaceholder
    ]


def _all_clouds(doc):
    return list(
        DB.FilteredElementCollector(doc)
        .OfCategory(DB.BuiltInCategory.OST_RevisionClouds)
        .WhereElementIsNotElementType()
        .ToElements()
    )


def _selected_clouds(doc, uidoc):
    clouds = []
    for element_id in uidoc.Selection.GetElementIds():
        element = doc.GetElement(element_id)
        if isinstance(element, DB.RevisionCloud):
            clouds.append(element)
    return clouds


def _revision_label(doc, cloud):
    revision = doc.GetElement(cloud.RevisionId)
    if revision is None:
        return (2147483647, 'Revision not found')
    try:
        number = revision.RevisionNumber
    except Exception:
        number = str(revision.SequenceNumber)
    label = 'Seq {} / Rev {} - {}'.format(
        revision.SequenceNumber, number, revision.Description or '')
    return (revision.SequenceNumber, label)


def _owner_view_name(doc, cloud):
    owner_view = doc.GetElement(cloud.OwnerViewId)
    if owner_view is None:
        return 'Owner view not found'
    if isinstance(owner_view, DB.ViewSheet):
        return 'Sheet: {}'.format(_sheet_label(owner_view))
    return _view_name(owner_view)


def main():
    output = script.get_output()
    output.close_others()
    doc = revit.doc

    clouds = _selected_clouds(doc, revit.uidoc)
    scope = 'Selected revision clouds'
    if not clouds:
        clouds = _all_clouds(doc)
        scope = 'All revision clouds in the model'

    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('**Scope:** {} ({})'.format(scope, len(clouds)))
    if not clouds:
        output.print_md('No revision clouds were found.')
        return

    sheets = _project_sheets(doc)
    sheets_by_id = dict((_element_id_value(sheet.Id), sheet) for sheet in sheets)
    # GetAllRevisionCloudIds includes clouds on the sheet and in its placed
    # (including dependent) views, matching what the sheet actually shows.
    sheet_clouds = [
        (_element_id_value(sheet.Id),
         [_element_id_value(cloud_id) for cloud_id in sheet.GetAllRevisionCloudIds()])
        for sheet in sheets
    ]
    clouds_by_id = dict((_element_id_value(cloud.Id), cloud) for cloud in clouds)
    cloud_sheets = sheets_by_cloud(sheet_clouds, list(clouds_by_id.keys()))

    rows = []
    unplaced = []
    for cloud_id, cloud in clouds_by_id.items():
        sequence, revision = _revision_label(doc, cloud)
        cloud_sheet_list = sorted(
            (sheets_by_id[sheet_id] for sheet_id in cloud_sheets[cloud_id]),
            key=lambda sheet: sheet_number_sort_key(sheet.SheetNumber))
        row = [
            revision,
            output.linkify(cloud.Id),
            _owner_view_name(doc, cloud),
            len(cloud_sheet_list),
            '<br>'.join(_sheet_label(sheet) for sheet in cloud_sheet_list) or '-',
        ]
        rows.append(((sequence, cloud_id), row))
        if not cloud_sheet_list:
            unplaced.append(cloud_id)

    rows.sort(key=lambda item: item[0])
    output.print_table(
        [row for _, row in rows],
        columns=['Revision', 'Cloud', 'Owner view', 'Sheet count', 'Sheets'])

    all_sheet_ids = set()
    for sheet_ids in cloud_sheets.values():
        all_sheet_ids.update(sheet_ids)
    output.print_md('**Distinct sheets:** {}'.format(len(all_sheet_ids)))
    if unplaced:
        output.print_md(
            '**{} cloud(s) are not shown on any sheet** (their view is not '
            'placed on a sheet).'.format(len(unplaced)))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        output = script.get_output()
        output.print_md('# {}'.format(COMMAND_TITLE))
        output.print_md('## Runtime error')
        output.print_md('```text\n{}\n```'.format(traceback.format_exc()))
