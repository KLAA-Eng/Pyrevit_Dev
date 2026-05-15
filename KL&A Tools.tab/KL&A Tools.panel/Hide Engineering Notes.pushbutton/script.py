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
    view_note_map = {}

    for view in target_views:
        ids_for_view = []

        for note in matching_notes:
            try:
                if note.CanBeHidden(view):
                    ids_for_view.append(note.Id)
            except:
                pass

        if ids_for_view:
            view_note_map[view.Id.IntegerValue] = {
                "view": view,
                "ids": ids_for_view
            }

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
    forms.alert("No target views found.", exitscript=True)

if not matching_notes:
    set_button_orange_not_hidden()
    forms.alert("No matching engineer notes found.", exitscript=True)

view_note_map = build_view_note_map(target_views, matching_notes)

if not view_note_map:
    set_button_orange_not_hidden()
    forms.alert("No hideable matching engineer notes found in target views.", exitscript=True)

matched_count = len(matching_notes)
processed_views = 0
changed_views = 0
changed_notes = 0
failed = []

with revit.Transaction("Hide/Unhide Engineer Notes"):
    for item in view_note_map.values():
        view = item["view"]
        ids_for_view = item["ids"]

        try:
            net_ids = List[DB.ElementId](ids_for_view)

            if hide_elements:
                view.HideElements(net_ids)
            else:
                try:
                    view.UnhideElements(net_ids)
                except:
                    pass

            changed_views += 1
            changed_notes += len(ids_for_view)

        except Exception as ex:
            failed.append("{}: {}".format(view.Name, str(ex)))

        processed_views += 1

    doc.Regenerate()

# Set icon directly from the action that just happened
if hide_elements:
    set_button_green_hidden()
else:
    set_button_orange_not_hidden()

msg = (
    "Done.\n\n"
    "Action: {0}\n"
    "Matched text notes: {1}\n"
    "Views processed: {2}\n"
    "Views changed: {3}\n"
    "Note actions attempted: {4}\n"
    "Button state set to: {5}"
).format(
    "Hide" if hide_elements else "Unhide",
    matched_count,
    processed_views,
    changed_views,
    changed_notes,
    "Green (on.png)" if hide_elements else "Orange (off.png)"
)

if failed:
    msg += "\n\nViews with issues:\n- " + "\n- ".join(failed[:20])

forms.alert(msg)