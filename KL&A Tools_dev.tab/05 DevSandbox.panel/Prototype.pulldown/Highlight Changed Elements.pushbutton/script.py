# -*- coding: utf-8 -*-
"""Highlight changed host-model elements visible on selected sheets.

This DevSandbox prototype compares selected-sheet content with a local baseline
RVT. It excludes links, title blocks, and revision clouds.
"""
from __future__ import print_function

import os

from Autodesk.Revit import Exceptions as RevitExceptions
from pyrevit import DB, forms, revit, script

from changed_elements.comparison import compare_fingerprints
from GUI.forms import select_from_dict
from graphics.overrides import create_red_projection_override


COMMAND_TITLE = 'Highlight Changed Elements'
MINIMUM_REVIT_VERSION = 2024
COORDINATE_PRECISION = 6
HIGHLIGHT_COLOR = DB.Color(255, 0, 0)


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


def _sheet_label(sheet):
    return '{} - {}'.format(sheet.SheetNumber, sheet.Name)


def _select_sheets(doc):
    sheets = [
        sheet for sheet in
        DB.FilteredElementCollector(doc)
        .OfCategory(DB.BuiltInCategory.OST_Sheets)
        .WhereElementIsNotElementType()
        .ToElements()
        if not sheet.IsPlaceholder
    ]
    if not sheets:
        _stop('No project sheets were found in the active model.')

    sheet_options = {_sheet_label(sheet): sheet for sheet in sheets}
    selected_sheets = select_from_dict(
        sheet_options,
        title=COMMAND_TITLE,
        label='Select sheets to highlight:',
        button_name='Highlight Selected Sheets',
        version='DevSandbox Prototype',
        SelectMultiple=True,
    )
    if not selected_sheets:
        _stop('Select at least one sheet.')
    return selected_sheets


def _open_baseline_document(app, baseline_path):
    model_path = DB.ModelPathUtils.ConvertUserVisiblePathToModelPath(baseline_path)
    open_options = DB.OpenOptions()
    return app.OpenDocumentFile(model_path, open_options)


def _worksharing_conflict_message():
    return (
        'Revit cannot open a local model and its central model in the same '
        'session. Select a detached/archive baseline RVT that is not connected '
        'to the active model central/local pair, then run the command again.'
    )


def _is_supported_element(element):
    if element is None or element.Category is None:
        return False
    if isinstance(element, DB.RevitLinkInstance):
        return False
    category_id = element.Category.Id.IntegerValue
    excluded = (int(DB.BuiltInCategory.OST_TitleBlocks), int(DB.BuiltInCategory.OST_RevisionClouds))
    if category_id in excluded:
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


def _parameter_value(parameter):
    value = parameter.AsValueString()
    if value is not None:
        return value
    storage = parameter.StorageType
    if storage == DB.StorageType.String:
        return parameter.AsString() or ''
    if storage == DB.StorageType.Integer:
        return str(parameter.AsInteger())
    if storage == DB.StorageType.Double:
        return str(_rounded_coordinate(parameter.AsDouble()))
    if storage == DB.StorageType.ElementId:
        return str(parameter.AsElementId().IntegerValue)
    return ''


def _content_key(element):
    values = []
    try:
        for parameter in element.Parameters:
            if parameter.HasValue:
                values.append((parameter.Definition.Name, _parameter_value(parameter)))
    except RevitExceptions.InvalidOperationException as error:
        return None, 'parameter content unavailable: {}'.format(error)
    values.sort()
    return tuple(values), None


def _schedule_content_key(schedule):
    try:
        parameter_values, parameter_error = _content_key(schedule)
        if parameter_error:
            return None, parameter_error
        values = list(parameter_values)
        for section in (DB.SectionType.Header, DB.SectionType.Body):
            section_data = schedule.GetTableData().GetSectionData(section)
            for row in range(section_data.FirstRowNumber, section_data.LastRowNumber + 1):
                for column in range(section_data.FirstColumnNumber, section_data.LastColumnNumber + 1):
                    values.append((str(section), row, column, schedule.GetCellText(section, row, column)))
        return tuple(values), None
    except (RevitExceptions.ArgumentException, RevitExceptions.InvalidOperationException) as error:
        return None, 'schedule content unavailable: {}'.format(error)


def _fingerprint(doc, element, is_schedule=False):
    content, unsupported = _schedule_content_key(element) if is_schedule else _content_key(element)
    return (_type_key(doc, element), _location_key(element), content), unsupported


def _elements_owned_by_view(doc, view_id):
    return DB.FilteredElementCollector(doc).OwnedByView(view_id).WhereElementIsNotElementType()


def _elements_visible_in_view(doc, view_id):
    return DB.FilteredElementCollector(doc, view_id).WhereElementIsNotElementType()


def _sheet_in_document(doc, sheet):
    return doc.GetElement(sheet.UniqueId)


def _fingerprints_for_sheets(doc, current_sheets):
    fingerprints = {}
    unsupported = []
    for current_sheet in current_sheets:
        sheet = _sheet_in_document(doc, current_sheet)
        if sheet is None:
            continue
        for view in _placed_views(doc, sheet):
            for element in _elements_visible_in_view(doc, view.Id):
                _add_fingerprint(doc, element, fingerprints, unsupported)
        for element in _elements_owned_by_view(doc, sheet.Id):
            _add_fingerprint(doc, element, fingerprints, unsupported)
        for instance in _schedule_instances(doc, sheet):
            schedule = doc.GetElement(instance.ScheduleId)
            if schedule is not None:
                _add_fingerprint(doc, schedule, fingerprints, unsupported, True)
    return fingerprints, unsupported


def _add_fingerprint(doc, element, fingerprints, unsupported, is_schedule=False):
    if not _is_supported_element(element):
        return
    fingerprint, reason = _fingerprint(doc, element, is_schedule)
    fingerprints[element.UniqueId] = fingerprint
    if reason:
        unsupported.append((element.UniqueId, reason))


def _placed_views(doc, sheet):
    views = []
    for view_id in sheet.GetAllPlacedViews():
        view = doc.GetElement(view_id)
        if view is not None and view.AreGraphicsOverridesAllowed():
            views.append(view)
    return views


def _schedule_instances(doc, sheet):
    instances = []
    for instance in DB.FilteredElementCollector(doc).OfClass(DB.ScheduleSheetInstance):
        if instance.OwnerViewId == sheet.Id:
            instances.append(instance)
    return instances


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


def _visible_changed_elements(targets):
    visible = []
    preserved = []
    processed = set()
    for view, element, kind in targets:
        pair = (view.Id.IntegerValue, element.Id.IntegerValue)
        if pair in processed:
            continue
        processed.add(pair)
        if _has_existing_overrides(view.GetElementOverrides(element.Id)):
            preserved.append((view, element, kind, 'Existing element override preserved'))
            continue
        visible.append((view, element, kind))
    return visible, preserved


def _is_highlight_override(override_settings):
    colors = (
        override_settings.ProjectionLineColor,
        override_settings.CutLineColor,
    )
    for color in colors:
        if color.IsValid and color.Red == 255 and color.Green == 0 and color.Blue == 0:
            return True
    return False


def _red_override_settings():
    settings = create_red_projection_override(DB)
    settings.SetCutLineColor(HIGHLIGHT_COLOR)
    return settings


def _clear_override_settings():
    return DB.OverrideGraphicSettings()


def _apply_highlights(doc, visible_elements):
    settings = _red_override_settings()
    highlighted = []
    skipped = []
    with revit.Transaction('Highlight changed elements on selected sheets', doc=doc):
        for view, element, kind in visible_elements:
            try:
                view.SetElementOverrides(element.Id, settings)
                highlighted.append((view, element, kind))
            except (RevitExceptions.ArgumentException, RevitExceptions.InvalidOperationException) as error:
                skipped.append((view, element, kind, str(error)))
    return highlighted, skipped


def _clear_highlights(doc, visible_elements):
    settings = _clear_override_settings()
    cleared = []
    skipped = []
    with revit.Transaction('Clear changed element highlights on selected sheets', doc=doc):
        for view, element, kind in visible_elements:
            try:
                view.SetElementOverrides(element.Id, settings)
                cleared.append((view, element, kind))
            except (RevitExceptions.ArgumentException, RevitExceptions.InvalidOperationException) as error:
                skipped.append((view, element, kind, str(error)))
    return cleared, skipped


def _changed_targets(doc, sheets, changed_ids):
    changed = []
    processed = set()
    for sheet in sheets:
        for view in _placed_views(doc, sheet):
            _append_changed_visible_elements(doc, view, 'placed-view element', changed_ids, processed, changed)
        _append_changed_owned_elements(doc, sheet, sheet, 'sheet-owned element', changed_ids, processed, changed)
        for instance in _schedule_instances(doc, sheet):
            schedule = doc.GetElement(instance.ScheduleId)
            if schedule is not None and schedule.UniqueId in changed_ids:
                _append_target(sheet, instance, 'schedule placement', processed, changed)
    return changed


def _append_changed_owned_elements(doc, owner, override_view, kind, changed_ids, processed, changed):
    for element in _elements_owned_by_view(doc, owner.Id):
        if _is_supported_element(element) and element.UniqueId in changed_ids:
            _append_target(override_view, element, kind, processed, changed)


def _append_changed_visible_elements(doc, view, kind, changed_ids, processed, changed):
    for element in _elements_visible_in_view(doc, view.Id):
        if _is_supported_element(element) and element.UniqueId in changed_ids:
            _append_target(view, element, kind, processed, changed)


def _append_target(view, element, kind, processed, changed):
    pair = (view.Id.IntegerValue, element.Id.IntegerValue)
    if pair not in processed:
        processed.add(pair)
        changed.append((view, element, kind))


def _highlighted_changed_elements(doc, sheets, changed_ids):
    highlighted = []
    for view, element, kind in _changed_targets(doc, sheets, changed_ids):
        if _is_highlight_override(view.GetElementOverrides(element.Id)):
            highlighted.append((view, element, kind))
    return highlighted


def _highlight_sheet(doc, sheet, changed_ids, clear_existing):
    views = _placed_views(doc, sheet)
    targets = _changed_targets(doc, [sheet], changed_ids)
    if clear_existing:
        red_elements = []
        for view, element, kind in targets:
            if _is_highlight_override(view.GetElementOverrides(element.Id)):
                red_elements.append((view, element, kind))
        changed, skipped = _clear_highlights(doc, red_elements)
    else:
        visible_elements, preserved = _visible_changed_elements(targets)
        changed, skipped = _apply_highlights(doc, visible_elements)
        skipped.extend(preserved)
    return {
        'sheet': sheet,
        'views': views,
        'changed': changed,
        'skipped': skipped,
    }


def _print_change_report(output, sheets, baseline_path, comparison, sheet_results, unsupported, clear_existing):
    action_label = 'Cleared' if clear_existing else 'Highlighted'
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('**Action:** {}'.format(action_label))
    output.print_md('**Sheets selected:** {}'.format(len(sheets)))
    output.print_md('**Baseline:** `{}`'.format(baseline_path))
    output.print_table([
        ['New', len(comparison['new'])],
        ['Modified', len(comparison['modified'])],
        ['Unchanged', len(comparison['unchanged'])],
        ['Deleted (report only)', len(comparison['deleted'])],
        ['{} in selected sheets'.format(action_label), sum(len(r['changed']) for r in sheet_results)],
        ['Skipped overrides', sum(len(r['skipped']) for r in sheet_results)],
    ], columns=['Result', 'Count'])
    output.print_md('## Sheet results')
    output.print_table([
        [
            _sheet_label(result['sheet']),
            len(result['views']),
            len(result['changed']),
            len(result['skipped']),
        ]
        for result in sheet_results
    ], columns=['Sheet', 'Placed views checked', action_label, 'Skipped'])
    if comparison['modified']:
        output.print_md('## Modified elements')
        rows = []
        for unique_id in comparison['modified']:
            rows.append([unique_id, ', '.join(comparison['reasons'][unique_id])])
        output.print_table(rows, columns=['UniqueId', 'Detected change'])
    if comparison['deleted']:
        output.print_md('## Deleted baseline elements')
        output.print_table([[unique_id] for unique_id in comparison['deleted']], columns=['UniqueId'])

    skipped_rows = []
    for result in sheet_results:
        for view, element, kind, reason in result['skipped']:
            skipped_rows.append([
                _sheet_label(result['sheet']),
                view.Name,
                kind,
                element.Id.IntegerValue,
                reason,
            ])
    if skipped_rows:
        output.print_md('## Skipped overrides')
        output.print_table(skipped_rows, columns=['Sheet', 'Target', 'Kind', 'ElementId', 'Reason'])
    if unsupported:
        output.print_md('## Unsupported comparison data')
        output.print_table(unsupported, columns=['UniqueId', 'Reason'])
    output.print_md(
        '> This prototype does not change the baseline RVT, compare linked '
        'models, or track highlight ownership outside current red element overrides.'
    )


def main():
    output = script.get_output()
    doc = revit.doc

    if not _is_supported_revit_version(doc.Application):
        _stop('This prototype requires Revit {} or newer.'.format(MINIMUM_REVIT_VERSION))
    if doc.IsFamilyDocument:
        _stop('Open a project model and run the command again.')

    selected_sheets = _select_sheets(doc)
    baseline_path = _select_baseline_path(doc)
    if baseline_path is None:
        return

    baseline_doc = None
    try:
        baseline_doc = _open_baseline_document(doc.Application, baseline_path)
        if baseline_doc.IsFamilyDocument:
            _stop('The selected baseline must be a Revit project, not a family.')
        baseline_fingerprints, baseline_unsupported = _fingerprints_for_sheets(
            baseline_doc, selected_sheets)
        current_fingerprints, current_unsupported = _fingerprints_for_sheets(
            doc, selected_sheets)
        comparison = compare_fingerprints(baseline_fingerprints, current_fingerprints)
        unsupported = baseline_unsupported + current_unsupported
    except RevitExceptions.CannotOpenBothCentralAndLocalException:
        _stop(_worksharing_conflict_message())
    except (RevitExceptions.ArgumentException, RevitExceptions.FileAccessException,
            RevitExceptions.FileNotFoundException, RevitExceptions.InvalidOperationException) as error:
        _stop('Could not open the baseline safely: {}'.format(error))
    finally:
        if baseline_doc is not None:
            baseline_doc.Close(False)

    changed_ids = set(comparison['new'] + comparison['modified'])
    clear_existing = bool(_highlighted_changed_elements(doc, selected_sheets, changed_ids))
    sheet_results = [
        _highlight_sheet(doc, sheet, changed_ids, clear_existing)
        for sheet in selected_sheets
    ]
    _print_change_report(output, selected_sheets, baseline_path, comparison, sheet_results, unsupported, clear_existing)


if __name__ == '__main__':
    main()
