# -*- coding: utf-8 -*-
"""Hide or unhide selected revision clouds on selected sheets and views."""
from __future__ import print_function

import clr

from System.Collections.Generic import List
from pyrevit import DB, forms, revit, script
from GUI.forms import select_from_dict

clr.AddReference('System')
from Autodesk.Revit.UI import (
    TaskDialog,
    TaskDialogCommandLinkId,
    TaskDialogCommonButtons,
    TaskDialogResult,
)


COMMAND_TITLE = 'Hide/Unhide Revision Clouds'


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
    return '{} [Id {}]'.format(
        _revision_label(revision), _element_id_value(revision.Id))


def _view_label(view):
    if isinstance(view, DB.ViewSheet):
        return _sheet_label(view)
    return revit.query.get_name(view)


def _ask_hide_or_unhide():
    dialog = TaskDialog(COMMAND_TITLE)
    dialog.TitleAutoPrefix = False
    dialog.MainInstruction = 'Choose action'
    dialog.MainContent = 'Select whether to hide or unhide revision clouds.'
    dialog.AddCommandLink(
        TaskDialogCommandLinkId.CommandLink1, 'Hide revision clouds')
    dialog.AddCommandLink(
        TaskDialogCommandLinkId.CommandLink2, 'Unhide revision clouds')
    dialog.CommonButtons = TaskDialogCommonButtons.Cancel
    result = dialog.Show()

    if result == TaskDialogResult.CommandLink1:
        return True, 'Hide', 'hidden', 'off'
    if result == TaskDialogResult.CommandLink2:
        return False, 'Unhide', 'unhidden', None
    return None, None, None, None


def _select_revisions(doc, action_label):
    revisions = list(
        DB.FilteredElementCollector(doc)
        .OfCategory(DB.BuiltInCategory.OST_Revisions)
        .WhereElementIsNotElementType()
        .ToElements()
    )
    if not revisions:
        _stop('No revisions were found in the active model.')

    options = {_revision_option_label(revision): revision for revision in revisions}
    selected_revisions = select_from_dict(
        options,
        title=COMMAND_TITLE,
        label='Select revisions to {}:'.format(action_label.lower()),
        button_name='Select Revisions',
        version='Core Tools',
        SelectMultiple=True,
        initial_checked_names=[],
    )
    if not selected_revisions:
        _stop('Select at least one revision.')
    return selected_revisions


def _select_sheets(doc, action_label):
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

    options = {_sheet_label(sheet): sheet for sheet in sheets}
    selected_sheets = select_from_dict(
        options,
        title=COMMAND_TITLE,
        label='Select sheets to {} revision clouds on:'.format(
            action_label.lower()),
        button_name='{} Clouds'.format(action_label),
        version='Core Tools',
        SelectMultiple=True,
        initial_checked_names=[],
    )
    if not selected_sheets:
        _stop('Select at least one sheet.')
    return selected_sheets


def _target_owners_by_selected_sheet(doc, sheets, report):
    """Returns selected sheets and their directly placed views by owner id."""
    owners = {}
    for sheet in sheets:
        sheet_value = _element_id_value(sheet.Id)
        owners[sheet_value] = {
            'view': sheet,
            'sheet_values': set([sheet_value]),
        }
        try:
            # GetAllPlacedViews returns only views placed directly on this sheet:
            # https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/816db942-4e9c-7278-7f59-53048becc46a.htm
            placed_view_ids = sheet.GetAllPlacedViews()
        except Exception as error:
            report['cloud_errors'].append(
                '{}: could not read placed views ({})'.format(
                    _sheet_label(sheet), error))
            continue

        for view_id in placed_view_ids:
            view = doc.GetElement(view_id)
            if view is None:
                report['cloud_errors'].append(
                    '{}: could not find placed view {}.'.format(
                        _sheet_label(sheet), _element_id_value(view_id)))
                continue
            view_value = _element_id_value(view.Id)
            if view_value not in owners:
                owners[view_value] = {
                    'view': view,
                    'sheet_values': set(),
                }
            owners[view_value]['sheet_values'].add(sheet_value)
    return owners


def _is_placed_dependent_of(view, owner_view_id):
    """True when a selected placed view depends on the cloud owner view."""
    try:
        return (_element_id_value(view.GetPrimaryViewId()) ==
                _element_id_value(owner_view_id))
    except Exception:
        return False


def _add_cloud_to_target(targets, view, cloud_id):
    """Adds a cloud once to the view where its visibility will be changed."""
    view_value = _element_id_value(view.Id)
    if view_value not in targets:
        targets[view_value] = {'view': view, 'cloud_ids': []}
    if cloud_id not in targets[view_value]['cloud_ids']:
        targets[view_value]['cloud_ids'].append(cloud_id)


def _matching_clouds_by_owner_view(doc, sheets, revision_id_values,
                                   hide_elements, report):
    """Returns matching clouds visible on selected sheets by owner view."""
    owners = _target_owners_by_selected_sheet(doc, sheets, report)
    sheets_with_matching_clouds = set()
    candidate_clouds = {}
    collector = (DB.FilteredElementCollector(doc)
                 .OfCategory(DB.BuiltInCategory.OST_RevisionClouds)
                 .WhereElementIsNotElementType()
                 .ToElements())

    for sheet in sheets:
        sheet_value = _element_id_value(sheet.Id)
        try:
            # Returns individual clouds visible on this selected sheet:
            # https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/dd1487e6-dffa-5c9c-8fcc-ff8f664b494e.htm
            cloud_ids = sheet.GetAllRevisionCloudIds()
        except Exception as error:
            report['cloud_errors'].append(
                '{}: could not read revision clouds ({})'.format(
                    _sheet_label(sheet), error))
            continue
        for cloud_id in cloud_ids:
            cloud = doc.GetElement(cloud_id)
            if cloud is None:
                report['cloud_errors'].append(
                    '{}: could not find revision cloud {}.'.format(
                        _sheet_label(sheet), _element_id_value(cloud_id)))
                continue
            cloud_value = _element_id_value(cloud.Id)
            if cloud_value not in candidate_clouds:
                candidate_clouds[cloud_value] = {
                    'cloud': cloud,
                    'sheet_values': set(),
                }
            candidate_clouds[cloud_value]['sheet_values'].add(sheet_value)

    # A cloud hidden by this command no longer appears in a visible-sheet list.
    # Find it in each selected placed view so the Unhide action can reverse it.
    for cloud in collector:
        if _element_id_value(cloud.RevisionId) not in revision_id_values:
            continue
        cloud_value = _element_id_value(cloud.Id)
        owner_value = _element_id_value(cloud.OwnerViewId)
        if cloud_value in candidate_clouds:
            continue
        for owner in owners.values():
            target_view = owner['view']
            is_direct_owner = owner_value == _element_id_value(target_view.Id)
            is_placed_dependent = _is_placed_dependent_of(
                target_view, cloud.OwnerViewId)
            if not is_direct_owner and not is_placed_dependent:
                continue
            if is_direct_owner:
                candidate_clouds[cloud_value] = {
                    'cloud': cloud,
                    'sheet_values': set(owner['sheet_values']),
                }
                break
            if hide_elements:
                continue
            try:
                is_hidden = cloud.IsHidden(target_view)
            except Exception:
                continue
            if is_hidden:
                candidate_clouds[cloud_value] = {
                    'cloud': cloud,
                    'sheet_values': set(owner['sheet_values']),
                }
                break

    clouds_by_owner = {}
    for candidate in candidate_clouds.values():
        cloud = candidate['cloud']
        if _element_id_value(cloud.RevisionId) not in revision_id_values:
            continue
        sheets_with_matching_clouds.update(candidate['sheet_values'])
        owner_view = doc.GetElement(cloud.OwnerViewId)
        if owner_view is None:
            report['cloud_errors'].append(
                'Cloud {} has no owner view.'.format(
                    _element_id_value(cloud.Id)))
            continue
        # Match the Engineering Notes behavior: change the owner view and
        # every selected placed dependent view that displays its annotations.
        # https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API/files/Revit_API_Developers_Guide/Basic_Interaction_with_Revit_Elements/Views/Revit_API_Revit_API_Developers_Guide_Basic_Interaction_with_Revit_Elements_Views_View_Graphics_html.html
        target_views = [owner_view]
        for owner in owners.values():
            if not owner['sheet_values'].intersection(
                    candidate['sheet_values']):
                continue
            placed_view = owner['view']
            if _is_placed_dependent_of(placed_view, cloud.OwnerViewId):
                target_views.append(placed_view)

        for target_view in target_views:
            try:
                is_hidden = cloud.IsHidden(target_view)
            except Exception:
                report['state_check_errors'] += 1
                continue

            if hide_elements:
                if is_hidden:
                    report['already_in_requested_state'] += 1
                    continue
                try:
                    if not cloud.CanBeHidden(target_view):
                        report['not_hideable'] += 1
                        continue
                except Exception:
                    report['not_hideable'] += 1
                    continue
            elif not is_hidden:
                report['already_in_requested_state'] += 1
                continue

            _add_cloud_to_target(clouds_by_owner, target_view, cloud.Id)

    for sheet in sheets:
        if _element_id_value(sheet.Id) not in sheets_with_matching_clouds:
            report['views_without_matching_clouds'].append(_sheet_label(sheet))

    return [
        (item['view'], item['cloud_ids'])
        for item in clouds_by_owner.values()
    ]


def _update_sheet_revision_schedules(sheets, revision_ids, turn_on, report):
    # Additional revision ids control the titleblock revision schedule:
    # https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/376a4009-17f7-af8e-8c32-d95243ad8e9e.htm
    for sheet in sheets:
        try:
            additional_ids = sheet.GetAdditionalRevisionIds()
            existing_values = set([
                _element_id_value(element_id) for element_id in additional_ids
            ])
            changed = False

            for revision_id in revision_ids:
                revision_value = _element_id_value(revision_id)
                if turn_on and revision_value not in existing_values:
                    additional_ids.Add(revision_id)
                    existing_values.add(revision_value)
                    report['schedule_entries_changed'] += 1
                    changed = True
                elif not turn_on and revision_value in existing_values:
                    additional_ids.Remove(revision_id)
                    existing_values.remove(revision_value)
                    report['schedule_entries_changed'] += 1
                    changed = True
                else:
                    report['schedule_entries_already_in_state'] += 1

            if changed:
                sheet.SetAdditionalRevisionIds(additional_ids)
        except Exception as error:
            report['schedule_errors'].append(
                '{}: {}'.format(_sheet_label(sheet), error))


def _apply_changes(view_cloud_ids, sheets, revision_ids, hide_elements, report):
    with revit.Transaction(COMMAND_TITLE, doc=revit.doc):
        for view, cloud_ids in view_cloud_ids:
            try:
                # Permanent per-view visibility uses HideElements/UnhideElements:
                # https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/ff7695bc-b1b1-6cfd-bb74-9cf4ece27f18.htm
                element_ids = List[DB.ElementId](cloud_ids)
                if hide_elements:
                    view.HideElements(element_ids)
                else:
                    view.UnhideElements(element_ids)
                report['clouds_changed'] += len(cloud_ids)
            except Exception as error:
                report['cloud_errors'].append(
                    '{}: {}'.format(_view_label(view), error))

        if hide_elements:
            _update_sheet_revision_schedules(
                sheets, revision_ids, False, report)


def _print_report(action_label, action_word, schedule_state, revisions,
                  sheets, report):
    output = script.get_output()
    output.close_others()

    output.print_md('## {}'.format(COMMAND_TITLE))
    output.print_md('**Action:** {}'.format(action_label))
    output.print_md('**Selected revisions:** {}'.format(
        ', '.join([_revision_label(revision) for revision in revisions])))
    output.print_md('**Selected sheets:** {}'.format(
        ', '.join([_sheet_label(sheet) for sheet in sheets])))
    output.print_md('**Selected sheets checked:** {}'.format(len(sheets)))
    output.print_md('**Revision clouds {}:** {}'.format(
        action_word, report['clouds_changed']))
    output.print_md('**Already {}:** {}'.format(
        action_word, report['already_in_requested_state']))
    if report['not_hideable']:
        output.print_md('**Not hideable:** {}'.format(report['not_hideable']))
    if report['state_check_errors']:
        output.print_md('**Cloud state check errors:** {}'.format(
            report['state_check_errors']))
    if schedule_state:
        output.print_md('**Titleblock revision entries turned {}:** {}'.format(
            schedule_state, report['schedule_entries_changed']))
        output.print_md('**Titleblock revision entries already {}:** {}'.format(
            schedule_state, report['schedule_entries_already_in_state']))
    else:
        output.print_md('**Titleblock revision schedule:** Unchanged during Unhide.')

    if report['views_without_matching_clouds']:
        output.print_md('### Selected Sheets With No Matching Clouds To {}'.format(
            action_label))
        for sheet_name in report['views_without_matching_clouds']:
            print('- {}'.format(sheet_name))

    if report['cloud_errors']:
        output.print_md('### Cloud Operation Errors')
        for error in report['cloud_errors']:
            print('- {}'.format(error))

    if report['schedule_errors']:
        output.print_md('### Titleblock Revision Schedule Errors')
        for error in report['schedule_errors']:
            print('- {}'.format(error))


def main():
    hide_elements, action_label, action_word, schedule_state = \
        _ask_hide_or_unhide()
    if hide_elements is None:
        forms.alert('Operation cancelled.', exitscript=True)

    doc = revit.doc
    revisions = _select_revisions(doc, action_label)
    revision_ids = [revision.Id for revision in revisions]
    revision_id_values = set([
        _element_id_value(revision_id) for revision_id in revision_ids
    ])
    revision_id_values.discard(None)

    sheets = _select_sheets(doc, action_label)
    report = {
        'clouds_changed': 0,
        'already_in_requested_state': 0,
        'not_hideable': 0,
        'state_check_errors': 0,
        'views_without_matching_clouds': [],
        'cloud_errors': [],
        'schedule_entries_changed': 0,
        'schedule_entries_already_in_state': 0,
        'schedule_errors': [],
    }

    view_cloud_ids = _matching_clouds_by_owner_view(
        doc, sheets, revision_id_values, hide_elements, report)

    _apply_changes(view_cloud_ids, sheets, revision_ids, hide_elements, report)
    _print_report(action_label, action_word, schedule_state, revisions,
                  sheets, report)


if __name__ == '__main__':
    main()
