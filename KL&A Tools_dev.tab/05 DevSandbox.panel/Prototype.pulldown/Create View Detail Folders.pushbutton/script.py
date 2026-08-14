# -*- coding: utf-8 -*-
"""Create destination folders for Detail and Drafting Views of selected types."""
from __future__ import print_function

import os
import sys

from pyrevit import DB, forms, revit, script
from System.Collections.Generic import List


COMMAND_TITLE = 'Create View Detail Folders'
MINIMUM_REVIT_VERSION = 2022
JPEG_LONG_EDGE_PIXELS = 2400
TARGET_VIEW_FAMILIES = (DB.ViewFamily.Detail, DB.ViewFamily.Drafting)
TARGET_VIEW_TYPES = (DB.ViewType.Detail, DB.ViewType.DraftingView)


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
from detail_view_deliverables import (
    build_deliverable_plan, has_export_failures, is_direct_child_path)
from detail_view_folders import build_folder_plan, create_folder_paths
from detail_view_html import render_detail_html


def _element_id_value(element_id):
    if element_id is None:
        return None
    for property_name in ('Value', 'IntegerValue'):
        try:
            return int(getattr(element_id, property_name))
        except (AttributeError, TypeError, ValueError):
            pass
    return None


def _view_type_label(view_type):
    family_name = 'Detail' if view_type.ViewFamily == DB.ViewFamily.Detail else 'Drafting'
    return '{}: {}'.format(family_name, view_type.Name)


def _view_type_options(document):
    options = {}
    view_types = DB.FilteredElementCollector(document).OfClass(DB.ViewFamilyType)
    for view_type in view_types:
        if view_type.ViewFamily not in TARGET_VIEW_FAMILIES:
            continue
        label = _view_type_label(view_type)
        if label in options:
            label = '{} ({})'.format(label, _element_id_value(view_type.Id))
        options[label] = view_type
    return options


def _select_view_types(document):
    options = _view_type_options(document)
    if not options:
        forms.alert('No Detail or Drafting view types were found.', title=COMMAND_TITLE, warn_icon=True)
        return []
    return select_from_dict(
        options,
        title=COMMAND_TITLE,
        label='Select Detail and Drafting view types:',
        button_name='Create View Folders',
        version='DevSandbox Prototype',
        SelectMultiple=True,
    )


def _select_destination():
    path = forms.pick_folder(title='Select destination folder')
    if not path:
        return None
    normalized_path = os.path.abspath(path)
    if not os.path.isdir(normalized_path):
        forms.alert('Select an existing destination folder.', title=COMMAND_TITLE, warn_icon=True)
        return None
    return normalized_path


def _has_supported_revit_version(application):
    try:
        return int(application.VersionNumber) >= MINIMUM_REVIT_VERSION
    except (AttributeError, TypeError, ValueError):
        return False


def _detail_number(view):
    parameter_id = getattr(DB.BuiltInParameter, 'VIEWPORT_DETAIL_NUMBER', None)
    if parameter_id is None:
        return None
    parameter = view.get_Parameter(parameter_id)
    if parameter is None or not parameter.HasValue:
        return None
    value = parameter.AsString()
    return value if value and value.strip() and value.strip() != '-' else None


def _matching_view_records(document, selected_view_types):
    selected_ids = set(_element_id_value(view_type.Id) for view_type in selected_view_types)
    records = []
    views = DB.FilteredElementCollector(document).OfClass(DB.View).WhereElementIsNotElementType()
    for view in views:
        if view.IsTemplate or view.ViewType not in TARGET_VIEW_TYPES:
            continue
        if _element_id_value(view.GetTypeId()) not in selected_ids:
            continue
        records.append({
            'view_id': _element_id_value(view.Id),
            'detail_number': _detail_number(view),
            'view_name': view.Name,
        })
    return records


def _existing_destination_paths(destination):
    try:
        return [os.path.join(destination, name) for name in os.listdir(destination)]
    except OSError:
        forms.alert('Could not read the destination folder.', title=COMMAND_TITLE, warn_icon=True)
        return None


def _show_preflight_errors(errors):
    forms.alert('\n'.join(errors), title=COMMAND_TITLE, warn_icon=True)


def _element_id_list(view_id):
    view_ids = List[DB.ElementId]()
    view_ids.Add(DB.ElementId(view_id))
    return view_ids


def _export_pdf(document, view, item):
    options = DB.PDFExportOptions()
    options.Combine = True
    options.FileName = 'detail'
    options.PaperFormat = DB.ExportPaperFormat.ANSI_A
    options.PaperOrientation = DB.PageOrientationType.Auto
    options.PaperPlacement = DB.PaperPlacementType.Center
    options.ZoomType = DB.ZoomFitType.FitToPage
    options.RasterQuality = DB.RasterQualityType.High
    document.Export(item['path'], _element_id_list(item['view_id']), options)
    if not os.path.isfile(item['artifacts']['pdf']):
        raise IOError('Revit did not create detail.pdf.')


def _jpeg_fit_direction(view):
    crop_box = getattr(view, 'CropBox', None)
    if crop_box is not None:
        width = abs(crop_box.Max.X - crop_box.Min.X)
        height = abs(crop_box.Max.Y - crop_box.Min.Y)
        if height > width:
            return DB.FitDirectionType.Vertical
    return DB.FitDirectionType.Horizontal


def _export_jpeg(document, view, item):
    options = DB.ImageExportOptions()
    options.ExportRange = DB.ExportRange.SetOfViews
    options.FilePath = os.path.splitext(item['artifacts']['jpeg'])[0]
    options.FitDirection = _jpeg_fit_direction(view)
    options.HLRandWFViewsFileType = DB.ImageFileType.JPEG
    options.PixelSize = JPEG_LONG_EDGE_PIXELS
    options.ShadowViewsFileType = DB.ImageFileType.JPEG
    options.ShouldCreateWebSite = False
    options.ZoomType = DB.ZoomFitType.FitToPage
    options.SetViewsAndSheets(_element_id_list(item['view_id']))
    generated_path = DB.ImageExportOptions.GetFileName(document, view.Id)
    document.ExportImage(options)
    if not os.path.isabs(generated_path):
        generated_path = os.path.join(item['path'], generated_path)
    if not is_direct_child_path(item['path'], generated_path):
        raise IOError('Revit returned an image path outside the detail folder.')
    if os.path.abspath(generated_path) != item['artifacts']['jpeg']:
        os.rename(generated_path, item['artifacts']['jpeg'])
    if not os.path.isfile(item['artifacts']['jpeg']):
        raise IOError('Revit did not create detail.jpg.')


def _export_html(item):
    if not os.path.isfile(item['artifacts']['pdf']) or not os.path.isfile(item['artifacts']['jpeg']):
        raise IOError('PDF and JPEG must exist before index.html is created.')
    page = render_detail_html(item['folder_name'], 'detail.jpg', 'detail.pdf')
    with open(item['artifacts']['html'], 'wb') as html_file:
        html_file.write(page.encode('utf-8'))


def _export_view_deliverables(document, item):
    result = {'folder_name': item['folder_name'], 'pdf': 'Not created',
              'jpeg': 'Not created', 'html': 'Not created'}
    view = document.GetElement(DB.ElementId(item['view_id']))
    if view is None or not view.CanBePrinted:
        result['pdf'] = 'View is not printable.'
        return result
    for name, exporter in (('pdf', _export_pdf), ('jpeg', _export_jpeg)):
        try:
            exporter(document, view, item)
            result[name] = 'Created'
        except Exception as error:
            result[name] = 'Failed: {}'.format(error)
    try:
        _export_html(item)
        result['html'] = 'Created'
    except Exception as error:
        result['html'] = 'Failed: {}'.format(error)
    return result


def _report(output, selected_view_types, records, result, export_results):
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('Selected view types: {}'.format(', '.join(
        _view_type_label(view_type) for view_type in selected_view_types)))
    output.print_md('Matching individual views: {}'.format(len(records)))
    if result['created']:
        output.print_table([[name] for name in result['created']], columns=['Created Folder'])
    if result['errors']:
        output.print_table(
            [[item['folder_name'], item['reason']] for item in result['errors']],
            columns=['Folder', 'Result'])
    if export_results:
        output.print_table(
            [[item['folder_name'], item['pdf'], item['jpeg'], item['html']]
             for item in export_results],
            columns=['Folder', 'PDF', 'JPEG', 'HTML'])


def main():
    document = revit.doc
    if not _has_supported_revit_version(revit.app):
        forms.alert(
            'Revit {} or later is required for native PDF export.'.format(
                MINIMUM_REVIT_VERSION),
            title=COMMAND_TITLE,
            warn_icon=True)
        return
    selected_view_types = _select_view_types(document)
    if not selected_view_types:
        return
    destination = _select_destination()
    if destination is None:
        return
    records = _matching_view_records(document, selected_view_types)
    if not records:
        forms.alert('No individual Detail or Drafting views match the selected types.', title=COMMAND_TITLE)
        return
    existing_paths = _existing_destination_paths(destination)
    if existing_paths is None:
        return
    plan = build_folder_plan(destination, records, existing_paths)
    if plan['errors']:
        _show_preflight_errors(plan['errors'])
        return
    deliverable_plan = build_deliverable_plan(destination, plan['folders'], existing_paths)
    if deliverable_plan['errors']:
        _show_preflight_errors(deliverable_plan['errors'])
        return
    result = create_folder_paths(destination, plan['folders'])
    export_results = []
    if not result['errors']:
        for item in deliverable_plan['items']:
            export_results.append(_export_view_deliverables(document, item))
    _report(script.get_output(), selected_view_types, records, result, export_results)
    if result['errors']:
        forms.alert('Folder creation stopped. Review the output for created folders.', title=COMMAND_TITLE, warn_icon=True)
    elif has_export_failures(export_results):
        forms.alert('Some deliverables failed. Review the output for details.', title=COMMAND_TITLE, warn_icon=True)
    else:
        forms.alert('Created {} detail deliverable packages.'.format(
            len(result['created'])), title=COMMAND_TITLE)


if __name__ == '__main__':
    main()
