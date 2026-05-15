# -*- coding: utf-8 -*-
__title__ = "Hide/Unhide Engineer Notes"

from pyrevit import revit, DB, forms
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

hide_elements = forms.alert(
    "Choose action:\n\nYes = Hide engineer notes\nNo = Unhide engineer notes",
    yes=True,
    no=True,
    ok=False
)

if hide_elements is None:
    forms.alert("Operation cancelled.", exitscript=True)


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


target_views = collect_target_views(doc)
matching_notes = collect_matching_textnotes(doc)

if not target_views:
    forms.alert("No target views found.", exitscript=True)

if not matching_notes:
    forms.alert("No matching engineer notes found.", exitscript=True)

matched_count = len(matching_notes)
processed_views = 0
changed_views = 0
changed_notes = 0
failed = []

with revit.Transaction("Hide/Unhide Engineer Notes"):
    for view in target_views:
        try:
            ids_for_view = []

            for note in matching_notes:
                try:
                    # Only attempt on notes that can be hidden in this view
                    if note.CanBeHidden(view):
                        ids_for_view.append(note.Id)
                except:
                    pass

            if not ids_for_view:
                processed_views += 1
                continue

            net_ids = List[DB.ElementId](ids_for_view)

            if hide_elements:
                view.HideElements(net_ids)
            else:
                try:
                    view.UnhideElements(net_ids)
                except:
                    # Some views may have none of these hidden; ignore
                    pass

            changed_views += 1
            changed_notes += len(ids_for_view)
            processed_views += 1

        except Exception as ex:
            failed.append("{}: {}".format(view.Name, str(ex)))
            processed_views += 1

    doc.Regenerate()

msg = (
    "Done.\n\n"
    "Action: {0}\n"
    "Matched text notes: {1}\n"
    "Views processed: {2}\n"
    "Views changed: {3}\n"
    "Note actions attempted: {4}"
).format(
    "Hide" if hide_elements else "Unhide",
    matched_count,
    processed_views,
    changed_views,
    changed_notes
)

if failed:
    msg += "\n\nViews with issues:\n- " + "\n- ".join(failed[:20])

forms.alert(msg)