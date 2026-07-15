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
output = script.get_output()

SCRIPT_VERSION = "2.0-debug"

# ---------------------------------------------------------------------------
# DEBUG: True  -> full diagnostic funnel printed to the pyRevit output window
#         False -> quiet (only the summary alert)
# ---------------------------------------------------------------------------
DEBUG = True
try:
    if __shiftclick__:
        DEBUG = True
except NameError:
    pass

TEXTNOTE_TYPE_PREFIX = u"KLAA - ENGINEER'S NOTE"

TARGET_VIEW_TYPES = {
    DB.ViewType.EngineeringPlan,
    DB.ViewType.Legend,
    DB.ViewType.DraftingView,
    DB.ViewType.Detail,
    DB.ViewType.Schedule,
    DB.ViewType.DrawingSheet,

    # DB.ViewType.FloorPlan,
    # DB.ViewType.CeilingPlan,
    # DB.ViewType.Section,
    # DB.ViewType.Elevation,
}


def normalize_name(s):
    """Normalize a type name for comparison: unify apostrophe variants,
    strip whitespace, uppercase. Catches curly-quote / spacing mismatches."""
    if s is None:
        return u""
    s = s.replace(u"\u2019", u"'").replace(u"\u2018", u"'")  # curly -> straight
    s = s.replace(u"\u00a0", u" ")                            # nbsp -> space
    return s.strip().upper()


NORMALIZED_PREFIX = normalize_name(TEXTNOTE_TYPE_PREFIX)


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
    """Returns (matches, type_name_census).
    type_name_census maps every distinct textnote type name found in the
    model -> [instance_count, matched_bool]. Used by the diagnostic report
    to expose curly apostrophes / renamed types."""
    notes = (
        DB.FilteredElementCollector(document)
        .OfClass(DB.TextNote)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    matches = []
    census = {}

    for note in notes:
        type_name = get_textnote_type_name(note)
        key = type_name if type_name is not None else u"<unnamed / no type>"

        is_match = bool(
            type_name and normalize_name(type_name).startswith(NORMALIZED_PREFIX)
        )

        if key not in census:
            census[key] = [0, is_match]
        census[key][0] += 1

        if is_match:
            matches.append(note)

    return matches, census


def sheet_appears_in_sheet_list(sheet, diag):
    """Uses the built-in parameter (locale-proof). Falls back to the display
    name lookup. Returns True/False; records missing-parameter events."""
    p = None
    try:
        p = sheet.get_Parameter(DB.BuiltInParameter.SHEET_SCHEDULED)
    except:
        p = None

    if p is None:
        p = sheet.LookupParameter("Appears In Sheet List")

    if p is None:
        diag["sheets_param_missing"] += 1
        return False

    try:
        return p.AsInteger() == 1
    except:
        diag["sheets_param_unreadable"] += 1
        return False


def collect_allowed_sheet_ids_and_placed_view_ids(document, diag):
    allowed_sheet_ids = set()
    placed_view_ids = set()

    sheets = (
        DB.FilteredElementCollector(document)
        .OfClass(DB.ViewSheet)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    diag["sheets_total"] = len(sheets)

    for sheet in sheets:
        try:
            if not sheet_appears_in_sheet_list(sheet, diag):
                diag["sheets_excluded_not_in_list"] += 1
                continue

            sheet_key = get_elementid_value(sheet.Id)
            if sheet_key is not None:
                allowed_sheet_ids.add(sheet_key)

            placed_ids = sheet.GetAllPlacedViews()
            for vid in placed_ids:
                key = get_elementid_value(vid)
                if key is not None:
                    placed_view_ids.add(key)
        except Exception as ex:
            diag["sheet_scan_errors"].append(u"{}: {}".format(
                getattr(sheet, "Name", "?"), ex))

    return allowed_sheet_ids, placed_view_ids


def build_view_note_map(document, target_views, matching_notes,
                        allowed_sheet_ids, placed_view_ids, diag):
    target_view_dict = {}
    for v in target_views:
        key = get_elementid_value(v.Id)
        if key is not None:
            target_view_dict[key] = v

    view_note_map = {}

    for note in matching_notes:
        owner_view_id = note.OwnerViewId
        if owner_view_id == DB.ElementId.InvalidElementId:
            diag["notes_no_owner_view"] += 1
            continue

        key = get_elementid_value(owner_view_id)
        if key is None:
            diag["notes_no_owner_view"] += 1
            continue

        view = target_view_dict.get(key)
        if view is None:
            # Diagnostic
            owner = document.GetElement(owner_view_id)
            if owner is None:
                label = u"<owner view not found>"
            elif getattr(owner, "IsTemplate", False):
                label = u"<view template>"
            else:
                label = u"{} (e.g. '{}')".format(
                    str(owner.ViewType), getattr(owner, "Name", "?"))
            diag["notes_owner_not_target"][label] = \
                diag["notes_owner_not_target"].get(label, 0) + 1
            continue

        if view.ViewType == DB.ViewType.DrawingSheet:
            if key not in allowed_sheet_ids:
                diag["notes_sheet_not_in_list"] += 1
                continue
        else:
            if key not in placed_view_ids:
                diag["notes_view_not_placed"] += 1
                continue

        try:
            if not note.CanBeHidden(view):
                diag["notes_cannot_be_hidden"] += 1
                continue
        except Exception as ex:
            diag["notes_canbehidden_errors"].append(
                u"View '{}': {}".format(view.Name, ex))
            continue

        if key not in view_note_map:
            view_note_map[key] = {"view": view, "ids": []}
        view_note_map[key]["ids"].append(note.Id)
        diag["notes_eligible"] += 1

    return view_note_map


def ask_hide_or_unhide():
    dlg = TaskDialog("Hide Engineering Notes")
    dlg.TitleAutoPrefix = False
    dlg.MainInstruction = "Choose action"
    dlg.MainContent = "Select whether to hide or unhide engineer notes."
    dlg.AddCommandLink(TaskDialogCommandLinkId.CommandLink1, "Hide engineer notes")
    dlg.AddCommandLink(TaskDialogCommandLinkId.CommandLink2, "Unhide engineer notes")
    dlg.CommonButtons = TaskDialogCommonButtons.Cancel
    result = dlg.Show()

    if result == TaskDialogResult.CommandLink1:
        return True, "Hide", "hidden"
    elif result == TaskDialogResult.CommandLink2:
        return False, "Unhide", "unhidden"
    else:
        return None, None, None


def print_diagnostics(diag, census, target_views, matching_notes,
                      allowed_sheet_ids, placed_view_ids, view_note_map):
    lines = []
    lines.append(u"=" * 70)
    lines.append(u"ENGINEER NOTES DIAGNOSTIC REPORT  (script v{})".format(SCRIPT_VERSION))
    lines.append(u"Document: {}".format(doc.Title))
    try:
        lines.append(u"Workshared: {}".format(doc.IsWorkshared))
    except:
        pass
    lines.append(u"=" * 70)

    lines.append(u"")
    lines.append(u"--- STAGE 1: Text note type names found in model ---")
    lines.append(u"Prefix filter (normalized): {}".format(repr(NORMALIZED_PREFIX)))
    if not census:
        lines.append(u"  !! No TextNote instances exist in this model at all.")
    for name in sorted(census.keys()):
        count, matched = census[name]
        flag = u"MATCH" if matched else u"skip "
        # repr() exposes curly quotes, non-breaking spaces, trailing spaces
        lines.append(u"  [{}] x{:<4} {}".format(flag, count, repr(name)))
    lines.append(u"  Matching note instances: {}".format(len(matching_notes)))
    if not matching_notes:
        lines.append(u"  >> ROOT CAUSE LIKELY HERE: no type name matched the prefix.")
        lines.append(u"     Compare the repr() strings above against the prefix -")
        lines.append(u"     look for \\u2019 (curly apostrophe), extra spaces, or renames.")

    lines.append(u"")
    lines.append(u"--- STAGE 2: Target views ---")
    by_type = {}
    for v in target_views:
        t = str(v.ViewType)
        by_type[t] = by_type.get(t, 0) + 1
    lines.append(u"  Target views found: {}".format(len(target_views)))
    for t in sorted(by_type.keys()):
        lines.append(u"    {}: {}".format(t, by_type[t]))

    lines.append(u"")
    lines.append(u"--- STAGE 3: Sheet eligibility ---")
    lines.append(u"  Sheets in model: {}".format(diag["sheets_total"]))
    lines.append(u"  Sheets excluded (not in sheet list): {}".format(
        diag["sheets_excluded_not_in_list"]))
    lines.append(u"  Eligible sheets: {}".format(len(allowed_sheet_ids)))
    lines.append(u"  Views placed on eligible sheets: {}".format(len(placed_view_ids)))
    if diag["sheets_param_missing"]:
        lines.append(u"  !! 'Appears In Sheet List' parameter NOT FOUND on {} sheets.".format(
            diag["sheets_param_missing"]))
        lines.append(u"     >> ROOT CAUSE LIKELY HERE (localized Revit / param lookup).")
    if diag["sheets_param_unreadable"]:
        lines.append(u"  !! Parameter unreadable on {} sheets.".format(
            diag["sheets_param_unreadable"]))
    for e in diag["sheet_scan_errors"][:10]:
        lines.append(u"  !! Sheet scan error: {}".format(e))

    lines.append(u"")
    lines.append(u"--- STAGE 4: Why matching notes were excluded ---")
    lines.append(u"  No owner view: {}".format(diag["notes_no_owner_view"]))
    if diag["notes_owner_not_target"]:
        lines.append(u"  Owner view type NOT in TARGET_VIEW_TYPES:")
        for label in sorted(diag["notes_owner_not_target"].keys()):
            lines.append(u"    {} : {} note(s)".format(
                label, diag["notes_owner_not_target"][label]))
        lines.append(u"    >> If notes are landing in FloorPlan/CeilingPlan/Section,")
        lines.append(u"       add those types to TARGET_VIEW_TYPES.")
    else:
        lines.append(u"  Owner view type not targeted: 0")
    lines.append(u"  On sheets excluded from sheet list: {}".format(
        diag["notes_sheet_not_in_list"]))
    lines.append(u"  In views not placed on eligible sheets: {}".format(
        diag["notes_view_not_placed"]))
    lines.append(u"  CanBeHidden() returned False: {}".format(
        diag["notes_cannot_be_hidden"]))
    for e in diag["notes_canbehidden_errors"][:10]:
        lines.append(u"  !! CanBeHidden threw: {}".format(e))
    lines.append(u"  ELIGIBLE notes surviving all filters: {}".format(
        diag["notes_eligible"]))

    lines.append(u"")
    lines.append(u"--- STAGE 5: Hide/Unhide execution ---")
    lines.append(u"  Views/sheets with eligible notes: {}".format(len(view_note_map)))
    lines.append(u"  Skipped (already in requested state): {}".format(
        diag["notes_already_in_state"]))
    lines.append(u"  State-check exceptions (silently skipped notes): {}".format(
        diag["notes_state_check_errors"]))
    lines.append(u"  Changed in views: {}".format(diag["view_notes_changed"]))
    lines.append(u"  Changed on sheets: {}".format(diag["sheet_notes_changed"]))
    for f in diag["hide_failures"]:
        lines.append(u"  !! FAILED: {}".format(f))
    lines.append(u"=" * 70)

    print(u"\n".join(lines))


# ===========================================================================
# MAIN
# ===========================================================================

hide_elements, action_label, action_word = ask_hide_or_unhide()

if hide_elements is None:
    forms.alert("Operation cancelled.", exitscript=True)

diag = {
    "sheets_total": 0,
    "sheets_excluded_not_in_list": 0,
    "sheets_param_missing": 0,
    "sheets_param_unreadable": 0,
    "sheet_scan_errors": [],
    "notes_no_owner_view": 0,
    "notes_owner_not_target": {},
    "notes_sheet_not_in_list": 0,
    "notes_view_not_placed": 0,
    "notes_cannot_be_hidden": 0,
    "notes_canbehidden_errors": [],
    "notes_eligible": 0,
    "notes_already_in_state": 0,
    "notes_state_check_errors": 0,
    "view_notes_changed": 0,
    "sheet_notes_changed": 0,
    "hide_failures": [],
}

target_views = collect_target_views(doc)
matching_notes, type_census = collect_matching_textnotes(doc)
allowed_sheet_ids, placed_view_ids = \
    collect_allowed_sheet_ids_and_placed_view_ids(doc, diag)

view_note_map = build_view_note_map(
    doc, target_views, matching_notes,
    allowed_sheet_ids, placed_view_ids, diag
)

# --- Execute ---
processed_views = 0
failed = diag["hide_failures"]

if view_note_map:
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
                                diag["notes_already_in_state"] += 1
                        else:
                            if el.IsHidden(view):
                                valid_ids.append(eid)
                            else:
                                diag["notes_already_in_state"] += 1
                    except:
                        diag["notes_state_check_errors"] += 1

                if not valid_ids:
                    processed_views += 1
                    continue

                net_ids = List[DB.ElementId](valid_ids)

                if hide_elements:
                    view.HideElements(net_ids)
                else:
                    view.UnhideElements(net_ids)

                if view.ViewType == DB.ViewType.DrawingSheet:
                    diag["sheet_notes_changed"] += len(valid_ids)
                else:
                    diag["view_notes_changed"] += len(valid_ids)

            except Exception as ex:
                failed.append(u"{}: {}".format(view.Name, ex))

            processed_views += 1

        doc.Regenerate()

# --- Button icon state ---
if view_note_map and (diag["view_notes_changed"] or diag["sheet_notes_changed"]):
    if hide_elements:
        set_button_green_hidden()
    else:
        set_button_orange_not_hidden()

# --- Diagnostics to pyRevit output window ---
if DEBUG:
    print_diagnostics(diag, type_census, target_views, matching_notes,
                      allowed_sheet_ids, placed_view_ids, view_note_map)

# --- Summary alert ---
total_changed = diag["view_notes_changed"] + diag["sheet_notes_changed"]

msg = (
    u"Action: {0}  (script v{1})\n\n"
    u"Notes {2} in views: {3}\n"
    u"Notes {2} on sheets: {4}"
).format(action_label, SCRIPT_VERSION, action_word,
         diag["view_notes_changed"], diag["sheet_notes_changed"])

if total_changed == 0:
    # Make silent failure LOUD, with the most likely reason inline.
    if not matching_notes:
        reason = (u"No text notes matched the type prefix.\n"
                  u"Check the diagnostic report for the exact type names "
                  u"found in this model.")
    elif diag["notes_owner_not_target"]:
        worst = max(diag["notes_owner_not_target"].items(), key=lambda kv: kv[1])
        reason = (u"{} matching note(s) exist, but their views are not in "
                  u"the targeted view types (most common: {}).").format(
                      len(matching_notes), worst[0])
    elif len(allowed_sheet_ids) == 0 and diag["sheets_total"] > 0:
        reason = (u"No sheets qualified via 'Appears In Sheet List' "
                  u"({} sheets scanned, param missing on {}).").format(
                      diag["sheets_total"], diag["sheets_param_missing"])
    elif diag["notes_sheet_not_in_list"] or diag["notes_view_not_placed"]:
        reason = (u"Matching notes were found, but they are on excluded "
                  u"sheets or in views not placed on eligible sheets.")
    elif diag["notes_already_in_state"]:
        reason = u"All matching notes were already {}.".format(action_word)
    else:
        reason = u"See the diagnostic report in the pyRevit output window."
    msg += u"\n\nNOTHING WAS CHANGED.\n" + reason
    if DEBUG:
        msg += u"\n\nFull diagnostic report is in the pyRevit output window."

if failed:
    msg += u"\n\nItems with issues:\n- " + u"\n- ".join(failed[:20])

forms.alert(msg)