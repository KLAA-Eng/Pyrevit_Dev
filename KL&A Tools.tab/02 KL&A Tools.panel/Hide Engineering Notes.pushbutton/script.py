# -*- coding: utf-8 -*-
# __title__ = "Hide/Unhide Engineer Notes"

from pyrevit import revit, DB, forms, script
import clr

clr.AddReference("System")
from System.Collections.Generic import List
from Autodesk.Revit.UI import (
    TaskDialog,
    TaskDialogCommandLinkId,
    TaskDialogCommonButtons,
    TaskDialogResult
)

doc = revit.doc

TEXTNOTE_TYPE_PREFIX = "KLAA - ENGINEER'S NOTE"
TARGET_VIEW_TYPES = {
    DB.ViewType.EngineeringPlan,
    DB.ViewType.Legend,
    DB.ViewType.DraftingView,
    DB.ViewType.Detail,
    DB.ViewType.Schedule,
    DB.ViewType.DrawingSheet,
}


def set_button_green_hidden():
    try:
        script.toggle_icon(True)
    except:
        pass


def set_button_orange_not_hidden():
    try:
        script.toggle_icon(False)
    except:
        pass


def get_elementid_value(eid):
    if eid is None:
        return None

    try:
        return eid.Value
    except:
        try:
            return eid.IntegerValue
        except:
            return None


def get_textnote_type_name(note):
    note_type = doc.GetElement(note.GetTypeId())
    if note_type is None:
        return None

    p = note_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    if p and p.HasValue:
        return p.AsString()

    return note_type.Name


def collect_target_views(document):
    views = DB.FilteredElementCollector(document).OfClass(DB.View).ToElements()
    result = []
    for v in views:
        if v.IsTemplate:
            continue
        if v.ViewType in TARGET_VIEW_TYPES:
            result.append(v)
    return result


def collect_matching_textnotes(document):
    notes = (
        DB.FilteredElementCollector(document)
        .OfClass(DB.TextNote)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    matches = []
    for note in notes:
        type_name = get_textnote_type_name(note)
        if type_name and type_name.upper().startswith(TEXTNOTE_TYPE_PREFIX.upper()):
            matches.append(note)
    return matches


def sheet_appears_in_sheet_list(sheet):
    p = sheet.LookupParameter("Appears In Sheet List")
    if p is None:
        return False

    try:
        return p.AsInteger() == 1
    except:
        return False


def collect_allowed_sheet_ids_and_placed_view_ids(document):
    allowed_sheet_ids = set()
    placed_view_ids = set()

    sheets = (
        DB.FilteredElementCollector(document)
        .OfClass(DB.ViewSheet)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    for sheet in sheets:
        try:
            if not sheet_appears_in_sheet_list(sheet):
                continue

            sheet_key = get_elementid_value(sheet.Id)
            if sheet_key is not None:
                allowed_sheet_ids.add(sheet_key)

            placed_ids = sheet.GetAllPlacedViews()
            for vid in placed_ids:
                key = get_elementid_value(vid)
                if key is not None:
                    placed_view_ids.add(key)
        except:
            pass

    return allowed_sheet_ids, placed_view_ids


def build_view_note_map(target_views, matching_notes, allowed_sheet_ids, placed_view_ids):
    target_view_dict = {}
    for v in target_views:
        key = get_elementid_value(v.Id)
        if key is not None:
            target_view_dict[key] = v

    view_note_map = {}

    for note in matching_notes:
        owner_view_id = note.OwnerViewId
        if owner_view_id == DB.ElementId.InvalidElementId:
            continue

        key = get_elementid_value(owner_view_id)
        if key is None:
            continue

        view = target_view_dict.get(key)
        if view is None:
            continue

        if view.ViewType == DB.ViewType.DrawingSheet:
            if key not in allowed_sheet_ids:
                continue
        else:
            if key not in placed_view_ids:
                continue

        try:
            if not note.CanBeHidden(view):
                continue
        except:
            continue

        if key not in view_note_map:
            view_note_map[key] = {
                "view": view,
                "ids": []
            }

        view_note_map[key]["ids"].append(note.Id)

    return view_note_map


def ask_hide_or_unhide():
    dlg = TaskDialog("Hide Engineering Notes")
    dlg.TitleAutoPrefix = False
    dlg.MainInstruction = "Choose action"
    dlg.MainContent = "Select whether to hide or unhide engineer notes."

    dlg.AddCommandLink(
        TaskDialogCommandLinkId.CommandLink1,
        "Hide engineer notes"
    )
    dlg.AddCommandLink(
        TaskDialogCommandLinkId.CommandLink2,
        "Unhide engineer notes"
    )

    dlg.CommonButtons = TaskDialogCommonButtons.Cancel
    result = dlg.Show()

    if result == TaskDialogResult.CommandLink1:
        return True, "Hide", "hidden"
    elif result == TaskDialogResult.CommandLink2:
        return False, "Unhide", "unhidden"
    else:
        return None, None, None


hide_elements, action_label, action_word = ask_hide_or_unhide()

if hide_elements is None:
    forms.alert("Operation cancelled.", exitscript=True)

target_views = collect_target_views(doc)
matching_notes = collect_matching_textnotes(doc)
allowed_sheet_ids, placed_view_ids = collect_allowed_sheet_ids_and_placed_view_ids(doc)

if not target_views:
    forms.alert("No target views or sheets found.", exitscript=True)

if not matching_notes:
    set_button_orange_not_hidden()
    forms.alert("No matching engineer notes found.", exitscript=True)

view_note_map = build_view_note_map(
    target_views,
    matching_notes,
    allowed_sheet_ids,
    placed_view_ids
)

if not view_note_map:
    set_button_orange_not_hidden()
    forms.alert(
        "No hideable matching engineer notes found on eligible sheets "
        "or in views placed on eligible sheets.",
        exitscript=True
    )

processed_views = 0
view_notes_changed = 0
sheet_notes_changed = 0
failed = []

with revit.Transaction("Hide/Unhide Engineer Notes"):
    for item in view_note_map.values():
        view = item["view"]
        ids_for_view = item["ids"]

        try:
            valid_ids = []

            for eid in ids_for_view:
                el = doc.GetElement(eid)
                if el is None:
                    continue

                try:
                    if hide_elements:
                        if not el.IsHidden(view) and el.CanBeHidden(view):
                            valid_ids.append(eid)
                    else:
                        if el.IsHidden(view):
                            valid_ids.append(eid)
                except:
                    pass

            if not valid_ids:
                processed_views += 1
                continue

            net_ids = List[DB.ElementId](valid_ids)

            if hide_elements:
                view.HideElements(net_ids)
            else:
                view.UnhideElements(net_ids)

            if view.ViewType == DB.ViewType.DrawingSheet:
                sheet_notes_changed += len(valid_ids)
            else:
                view_notes_changed += len(valid_ids)

        except Exception as ex:
            failed.append("{}: {}".format(view.Name, str(ex)))

        processed_views += 1

    doc.Regenerate()

if hide_elements:
    set_button_green_hidden()
else:
    set_button_orange_not_hidden()

#DEBUG REPORT
msg = (
    "Done.\n\n"
    "Action: {0}\n"
    "Views/Sheets processed: {1}\n"
    "Notes {2} in views placed on eligible sheets: {3}\n"
    "Notes {2} on eligible sheets: {4}"
).format(
    action_label,
    processed_views,
    action_word,
    view_notes_changed,
    sheet_notes_changed
)

msg = (
    "Number of engineer's notes {0} in views: {1}\n"
    "Number of engineer's notes {0} on sheets: {2}"
).format(
    action_word,
    view_notes_changed,
    sheet_notes_changed
)

if failed:
    msg += "\n\nItems with issues:\n- " + "\n- ".join(failed[:20])

forms.alert(msg)