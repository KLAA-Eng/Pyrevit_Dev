# -*- coding: utf-8 -*-
"""Hide selected revisions' cloud elements on selected sheets and views."""
from __future__ import print_function

from System.Collections.Generic import List
from pyrevit import DB, forms, revit, script

from GUI.forms import select_from_dict


COMMAND_TITLE = 'Hide Revision Clouds'


def _stop(message):
    forms.alert(message, title=COMMAND_TITLE, warn_icon=True)
    script.exit()


def _element_id_value(element_id):
    if element_id is None:
        return None
    for property_name in ('Value', 'IntegerValue'):
        try:
            return int(getattr(element_id, property_name))
        except Exception:
            pass
    return None


def _sheet_label(sheet):
    return '{} - {}'.format(sheet.SheetNumber, sheet.Name)


def _revision_label(revision):
    try:
        sequence = revision.SequenceNumber
    except Exception:
        sequence = '?'
    try:
        name = revit.query.get_name(revision)
    except Exception:
        name = revision.Name
    try:
        date = revision.RevisionDate
    except Exception:
        date = ''
    if date:
        return '{} - {} ({})'.format(sequence, name, date)
    return '{} - {}'.format(sequence, name)


def _revision_option_label(revision):
    element_id = _element_id_value(revision.Id)
    return '{} [Id {}]'.format(_revision_label(revision), element_id)


def _view_label(view):
    if isinstance(view, DB.ViewSheet):
        return _sheet_label(view)
    return '{}'.format(revit.query.get_name(view))


def _select_revisions(doc):
    revisions = [
        revision for revision in
        DB.FilteredElementCollector(doc)
        .OfCategory(DB.BuiltInCategory.OST_Revisions)
        .WhereElementIsNotElementType()
        .ToElements()
    ]
    if not revisions:
        _stop('No revisions were found in the active model.')

    revision_options = {
        _revision_option_label(revision): revision for revision in revisions
    }
    selected_revisions = select_from_dict(
        revision_options,
        title=COMMAND_TITLE,
        label='Select revisions to hide clouds for:',
        button_name='Select Revisions',
        version='DevSandbox Prototype',
        SelectMultiple=True,
    )
    if not selected_revisions:
        _stop('Select at least one revision.')
    return selected_revisions


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
        label='Select sheets to hide revision clouds on:',
        button_name='Hide Clouds On Selected Sheets',
        version='DevSandbox Prototype',
        SelectMultiple=True,
    )
    if not selected_sheets:
        _stop('Select at least one sheet.')
    return selected_sheets


def _target_views(doc, sheets):
    views = []
    seen = set()

    for sheet in sheets:
        sheet_key = _element_id_value(sheet.Id)
        if sheet_key is not None and sheet_key not in seen:
            seen.add(sheet_key)
            views.append(sheet)

        try:
            view_ids = sheet.GetAllPlacedViews()
        except Exception:
            continue

        for view_id in view_ids:
            key = _element_id_value(view_id)
            if key in seen:
                continue

            view = doc.GetElement(view_id)
            if view is None:
                continue

            seen.add(key)
            views.append(view)

    return views


def _clouds_by_owner_view(doc):
    clouds = {}
    all_clouds = (
        DB.FilteredElementCollector(doc)
        .OfCategory(DB.BuiltInCategory.OST_RevisionClouds)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    for cloud in all_clouds:
        key = _element_id_value(cloud.OwnerViewId)
        if key is None:
            continue
        if key not in clouds:
            clouds[key] = []
        clouds[key].append(cloud)

    return clouds


def _matching_view_clouds(view, clouds, revision_id_values, report):
    view_key = _element_id_value(view.Id)
    if view_key is None:
        return []

    matching_clouds = []
    clouds_on_view = clouds.get(view_key, [])
    if not clouds_on_view:
        report['views_without_matching_clouds'].append(_view_label(view))
        return matching_clouds

    for cloud in clouds_on_view:
        revision_key = _element_id_value(cloud.RevisionId)
        if revision_key not in revision_id_values:
            continue

        try:
            if cloud.IsHidden(view):
                report['already_hidden'] += 1
                continue
        except Exception:
            pass

        try:
            if not cloud.CanBeHidden(view):
                report['not_hideable'] += 1
                continue
        except Exception:
            report['not_hideable'] += 1
            continue

        matching_clouds.append(cloud.Id)

    if not matching_clouds:
        report['views_without_matching_clouds'].append(_view_label(view))
    return matching_clouds


def _hide_clouds_by_view(view_cloud_ids, report):
    with revit.Transaction('Hide Revision Clouds', doc=revit.doc):
        for view, cloud_ids in view_cloud_ids:
            if not cloud_ids:
                continue
            try:
                view.HideElements(List[DB.ElementId](cloud_ids))
                report['hidden'] += len(cloud_ids)
            except Exception as error:
                report['hide_errors'].append(
                    '{}: {}'.format(_view_label(view), error)
                )


def _print_report(revisions, sheets, views, report):
    output = script.get_output()
    output.close_others()

    output.print_md('## {}'.format(COMMAND_TITLE))
    output.print_md('**Selected revisions:** {}'.format(
        ', '.join([_revision_label(revision) for revision in revisions])
    ))
    output.print_md('**Selected sheets:** {}'.format(
        ', '.join([_sheet_label(sheet) for sheet in sheets])
    ))
    output.print_md('**Sheet views checked:** {}'.format(len(sheets)))
    output.print_md('**Total sheet/placed views scanned:** {}'.format(
        len(views)))
    output.print_md('**Revision clouds hidden:** {}'.format(report['hidden']))
    output.print_md('**Already hidden:** {}'.format(report['already_hidden']))
    output.print_md('**Not hideable:** {}'.format(report['not_hideable']))

    if report['views_without_matching_clouds']:
        output.print_md('### Views With No Matching Clouds To Hide')
        for view_name in report['views_without_matching_clouds']:
            print('- {}'.format(view_name))

    if report['hide_errors']:
        output.print_md('### Hide Errors')
        for error in report['hide_errors']:
            print('- {}'.format(error))

    print('\nSEARCH COMPLETED.')


def main():
    doc = revit.doc
    revisions = _select_revisions(doc)
    revision_id_values = set([
        _element_id_value(revision.Id) for revision in revisions
    ])
    revision_id_values.discard(None)

    selected_sheets = _select_sheets(doc)
    target_views = _target_views(doc, selected_sheets)
    if not target_views:
        _stop('No sheets or placed views were found to check.')

    report = {
        'hidden': 0,
        'already_hidden': 0,
        'not_hideable': 0,
        'views_without_matching_clouds': [],
        'hide_errors': [],
    }

    clouds = _clouds_by_owner_view(doc)
    view_cloud_ids = []
    for view in target_views:
        matching_cloud_ids = _matching_view_clouds(
            view, clouds, revision_id_values, report)
        if matching_cloud_ids:
            view_cloud_ids.append((view, matching_cloud_ids))

    if view_cloud_ids:
        _hide_clouds_by_view(view_cloud_ids, report)

    _print_report(revisions, selected_sheets, target_views, report)


if __name__ == '__main__':
    main()
