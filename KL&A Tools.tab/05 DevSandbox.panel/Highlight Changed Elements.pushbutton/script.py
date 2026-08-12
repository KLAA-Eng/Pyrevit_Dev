# -*- coding: utf-8 -*-
"""Highlight changed host-model elements visible on the active sheet.

This DevSandbox prototype compares a current local project with a local baseline
RVT. It intentionally excludes links, view-specific annotations, and automatic
revision-cloud generation.
"""
from __future__ import print_function

import os

from Autodesk.Revit import Exceptions as RevitExceptions
from pyrevit import DB, forms, revit, script

from changed_elements.comparison import compare_fingerprints
from graphics.overrides import create_red_projection_override


COMMAND_TITLE = 'Highlight Changed Elements'
MINIMUM_REVIT_VERSION = 2024
COORDINATE_PRECISION = 6


def _stop(message):
    forms.alert(message, title=COMMAND_TITLE, warn_icon=True)
    script.exit()


def _is_supported_revit_version(app):
    try:
        return int(app.VersionNumber) >= MINIMUM_REVIT_VERSION
    except (TypeError, ValueError):
        return False


def _select_baseline_path(current_doc):
    path = forms.pick_file(file_ext='rvt', title='Select local baseline RVT')
    if not path:
        return None
    normalized_path = os.path.normcase(os.path.abspath(path))
    current_path = os.path.normcase(os.path.abspath(current_doc.PathName or ''))
    if not normalized_path.lower().endswith('.rvt') or not os.path.isfile(normalized_path):
        _stop('Select an existing local .rvt baseline file.')
    if current_path and normalized_path == current_path:
        _stop('The baseline must be a different RVT file from the active model.')
    return normalized_path


def _open_baseline_document(app, baseline_path):
    model_path = DB.ModelPathUtils.ConvertUserVisiblePathToModelPath(baseline_path)
    open_options = DB.OpenOptions()
    return app.OpenDocumentFile(model_path, open_options)


def _is_host_model_element(element):
    if element is None or element.Category is None:
        return False
    if element.ViewSpecific or isinstance(element, DB.RevitLinkInstance):
        return False
    return True


def _type_key(doc, element):
    type_id = element.GetTypeId()
    if type_id == DB.ElementId.InvalidElementId:
        return ''
    type_element = doc.GetElement(type_id)
    return type_element.UniqueId if type_element else ''


def _rounded_coordinate(value):
    return round(value, COORDINATE_PRECISION)


def _location_key(element):
    location = element.Location
    if isinstance(location, DB.LocationPoint):
        point = location.Point
        return (
            'point',
            _rounded_coordinate(point.X),
            _rounded_coordinate(point.Y),
            _rounded_coordinate(point.Z),
            _rounded_coordinate(location.Rotation),
        )
    if isinstance(location, DB.LocationCurve):
        curve = location.Curve
        start = curve.GetEndPoint(0)
        end = curve.GetEndPoint(1)
        return (
            'curve',
            _rounded_coordinate(start.X), _rounded_coordinate(start.Y), _rounded_coordinate(start.Z),
            _rounded_coordinate(end.X), _rounded_coordinate(end.Y), _rounded_coordinate(end.Z),
        )
    return ('none',)


def _fingerprints_by_unique_id(doc):
    fingerprints = {}
    elements = DB.FilteredElementCollector(doc).WhereElementIsNotElementType()
    for element in elements:
        if _is_host_model_element(element):
            fingerprints[element.UniqueId] = (_type_key(doc, element), _location_key(element))
    return fingerprints


def _placed_views(doc, sheet):
    views = []
    for view_id in sheet.GetAllPlacedViews():
        view = doc.GetElement(view_id)
        if view is not None and view.AreGraphicsOverridesAllowed():
            views.append(view)
    return views


def _has_existing_overrides(override_settings):
    colors = (
        override_settings.ProjectionLineColor,
        override_settings.CutLineColor,
        override_settings.SurfaceForegroundPatternColor,
        override_settings.SurfaceBackgroundPatternColor,
        override_settings.CutForegroundPatternColor,
        override_settings.CutBackgroundPatternColor,
    )
    pattern_ids = (
        override_settings.ProjectionLinePatternId,
        override_settings.CutLinePatternId,
        override_settings.SurfaceForegroundPatternId,
        override_settings.SurfaceBackgroundPatternId,
        override_settings.CutForegroundPatternId,
        override_settings.CutBackgroundPatternId,
    )
    if any(color.IsValid for color in colors):
        return True
    if any(pattern_id != DB.ElementId.InvalidElementId for pattern_id in pattern_ids):
        return True
    if override_settings.ProjectionLineWeight != DB.OverrideGraphicSettings.InvalidPenNumber:
        return True
    if override_settings.CutLineWeight != DB.OverrideGraphicSettings.InvalidPenNumber:
        return True
    if override_settings.DetailLevel != DB.ViewDetailLevel.Undefined:
        return True
    return override_settings.Halftone or override_settings.Transparency != 0


def _visible_changed_elements(doc, views, changed_ids):
    visible = []
    preserved = []
    processed = set()
    for view in views:
        collector = DB.FilteredElementCollector(doc, view.Id).WhereElementIsNotElementType()
        for element in collector:
            pair = (view.Id.IntegerValue, element.Id.IntegerValue)
            if pair in processed or element.UniqueId not in changed_ids:
                continue
            processed.add(pair)
            if _has_existing_overrides(view.GetElementOverrides(element.Id)):
                preserved.append((view, element, 'Existing element override preserved'))
                continue
            visible.append((view, element))
    return visible, preserved


def _red_override_settings():
    settings = create_red_projection_override(DB)
    settings.SetCutLineColor(DB.Color(255, 0, 0))
    return settings


def _apply_highlights(doc, visible_elements):
    settings = _red_override_settings()
    highlighted = []
    skipped = []
    with revit.Transaction('Highlight changed elements on active sheet', doc=doc):
        for view, element in visible_elements:
            try:
                view.SetElementOverrides(element.Id, settings)
                highlighted.append((view, element))
            except (RevitExceptions.ArgumentException, RevitExceptions.InvalidOperationException) as error:
                skipped.append((view, element, str(error)))
    return highlighted, skipped


def _print_change_report(output, sheet, baseline_path, comparison, highlighted, skipped):
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('**Sheet:** {} — {}'.format(sheet.SheetNumber, sheet.Name))
    output.print_md('**Baseline:** `{}`'.format(baseline_path))
    output.print_table([
        ['New', len(comparison['new'])],
        ['Modified', len(comparison['modified'])],
        ['Unchanged', len(comparison['unchanged'])],
        ['Deleted (report only)', len(comparison['deleted'])],
        ['Highlighted in active sheet', len(highlighted)],
        ['Skipped overrides', len(skipped)],
    ], columns=['Result', 'Count'])
    if comparison['modified']:
        output.print_md('## Modified elements')
        rows = []
        for unique_id in comparison['modified']:
            rows.append([unique_id, ', '.join(comparison['reasons'][unique_id])])
        output.print_table(rows, columns=['UniqueId', 'Detected change'])
    if comparison['deleted']:
        output.print_md('## Deleted baseline elements')
        output.print_table([[unique_id] for unique_id in comparison['deleted']], columns=['UniqueId'])
    if skipped:
        output.print_md('## Skipped overrides')
        rows = [[view.Name, element.Id.IntegerValue, reason] for view, element, reason in skipped]
        output.print_table(rows, columns=['View', 'ElementId', 'Reason'])
    output.print_md(
        '> This prototype does not change the baseline RVT, compare linked '
        'models, or clear highlights automatically.'
    )


def main():
    output = script.get_output()
    doc = revit.doc
    sheet = revit.active_view

    if not _is_supported_revit_version(doc.Application):
        _stop('This prototype requires Revit {} or newer.'.format(MINIMUM_REVIT_VERSION))
    if doc.IsFamilyDocument or not isinstance(sheet, DB.ViewSheet):
        _stop('Open a project sheet and run the command again.')

    baseline_path = _select_baseline_path(doc)
    if baseline_path is None:
        return

    baseline_doc = None
    try:
        baseline_doc = _open_baseline_document(doc.Application, baseline_path)
        if baseline_doc.IsFamilyDocument:
            _stop('The selected baseline must be a Revit project, not a family.')
        comparison = compare_fingerprints(
            _fingerprints_by_unique_id(baseline_doc),
            _fingerprints_by_unique_id(doc),
        )
    except (RevitExceptions.ArgumentException, RevitExceptions.FileAccessException,
            RevitExceptions.FileNotFoundException, RevitExceptions.InvalidOperationException) as error:
        _stop('Could not open the baseline safely: {}'.format(error))
    finally:
        if baseline_doc is not None:
            baseline_doc.Close(False)

    changed_ids = set(comparison['new'] + comparison['modified'])
    views = _placed_views(doc, sheet)
    visible_elements, preserved = _visible_changed_elements(doc, views, changed_ids)
    highlighted, skipped = _apply_highlights(doc, visible_elements)
    skipped.extend(preserved)
    _print_change_report(output, sheet, baseline_path, comparison, highlighted, skipped)


if __name__ == '__main__':
    main()
