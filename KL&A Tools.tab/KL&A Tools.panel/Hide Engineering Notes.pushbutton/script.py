# -*- coding: utf-8 -*-
__title__ = "Hide/Unhide Engineer Notes"

from pyrevit import revit, DB, forms, script
import clr

clr.AddReference("System")
from System.Collections.Generic import List

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
        script.toggle_icon(True)   # uses on.png
    except:
        pass


def set_button_orange_not_hidden():
    try:
        script.toggle_icon(False)  # uses off.png
    except:
        pass


def get_elementid_value(eid):
    """Revit 2024/2025/2026-compatible ElementId numeric value."""
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


def build_view_note_map(target_views, matching_notes):
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


hide_elements = forms.alert(
    "Choose action:\n\nYes = Hide engineer notes\nNo = Unhide engineer notes",
    yes=True,
    no=True,
    ok=False
)

if hide_elements is None:
    forms.alert("Operation cancelled.", exitscript=True)

target_views = collect_target_views(doc)
matching_notes = collect_matching_textnotes(doc)

if not target_views:
    forms.alert("No target views or sheets found.", exitscript=True)

if not matching_notes:
    set_button_orange_not_hidden()
    forms.alert("No matching engineer notes found.", exitscript=True)

view_note_map = build_view_note_map(target_views, matching_notes)

if not view_note_map:
    set_button_orange_not_hidden()
    forms.alert("No hideable matching engineer notes found in target views/sheets.", exitscript=True)

matched_count = len(matching_notes)
processed_views = 0
changed_views = 0
changed_notes = 0
sheet_views_changed = 0
non_sheet_views_changed = 0
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

            changed_views += 1
            changed_notes += len(valid_ids)

            if view.ViewType == DB.ViewType.DrawingSheet:
                sheet_views_changed += 1
            else:
                non_sheet_views_changed += 1

        except Exception as ex:
            failed.append("{}: {}".format(view.Name, str(ex)))

        processed_views += 1

    doc.Regenerate()

if hide_elements:
    set_button_green_hidden()
else:
    set_button_orange_not_hidden()

msg = (
    "Done.\n\n"
    "Action: {0}\n"
    "Matched text notes: {1}\n"
    "Views/Sheets processed: {2}\n"
    "Views/Sheets changed: {3}\n"
    " - Regular views changed: {4}\n"
    " - Sheets changed: {5}\n"
    "Note actions completed: {6}\n"
    "Button state set to: {7}"
).format(
    "Hide" if hide_elements else "Unhide",
    matched_count,
    processed_views,
    changed_views,
    non_sheet_views_changed,
    sheet_views_changed,
    changed_notes,
    "Green (on.png)" if hide_elements else "Orange (off.png)"
)

if failed:
    msg += "\n\nViews/Sheets with issues:\n- " + "\n- ".join(failed[:20])

forms.alert(msg)