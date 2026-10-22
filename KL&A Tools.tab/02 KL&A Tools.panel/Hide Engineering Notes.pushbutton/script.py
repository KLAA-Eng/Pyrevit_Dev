# -*- coding: utf-8 -*-

__title__ = "Hide/Unhide\nEng Notes"
__version__ = "v1.1"

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

# ---------------------------------------------------------------------------
# DEBUG: True  -> full diagnostic funnel printed to the pyRevit output window
#         False -> completion report only
# You can also hold SHIFT while clicking the button to force debug mode.
# ---------------------------------------------------------------------------
DEBUG = False
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
    # Structural plans use EngineeringPlan. Other disciplines use FloorPlan or
    # CeilingPlan, so all three plan types are eligible.
    DB.ViewType.FloorPlan,
    DB.ViewType.CeilingPlan,
    DB.ViewType.Section,
    DB.ViewType.Elevation,
}


def normalize_name(s):
    """Return a comparable engineering-note type name.

    Args:
        s: Text note type name, or ``None`` when the type cannot be read.

    Returns:
        A trimmed, uppercase unicode string with apostrophe and nonbreaking
        space variants normalized.
    """
    if s is None:
        return u""
    s = s.replace(u"\u2019", u"'").replace(u"\u2018", u"'")  # curly -> straight
    s = s.replace(u"\u00a0", u" ")                            # nbsp -> space
    return s.strip().upper()


NORMALIZED_PREFIX = normalize_name(TEXTNOTE_TYPE_PREFIX)


def get_elementid_value(eid):
    """Return the comparable integer value for a Revit ElementId.

    Args:
        eid: Revit ElementId, or ``None``.

    Returns:
        The ElementId value, or ``None`` when it cannot be read. Supports the
        ElementId members used by the extension's supported Revit versions.
    """
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
    """Return a text note's type name from the active Revit document.

    Args:
        note: Revit TextNote instance in ``doc``.

    Returns:
        The type name, or ``None`` when its type cannot be found.
    """
    note_type = doc.GetElement(note.GetTypeId())
    if note_type is None:
        return None
    p = note_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    if p and p.HasValue:
        return p.AsString()
    return note_type.Name


def is_dependent_view(view):
    """Return whether a Revit view has a primary view.

    Args:
        view: Revit View instance to inspect.

    Returns:
        ``True`` for a dependent view; otherwise ``False``. Unreadable view
        relationships are treated as not dependent.
    """
    try:
        return view.GetPrimaryViewId() != DB.ElementId.InvalidElementId
    except:
        return False


def get_dependent_view_ids(view):
    """Return the ElementIds for a primary view's dependent views.

    Args:
        view: Revit View instance to inspect.

    Returns:
        A list of Revit ElementIds, or an empty list if the relationship cannot
        be read or the view has no dependents.
    """
    try:
        return list(view.GetDependentViewIds())
    except:
        return []


def collect_target_views(document):
    """Collect supported, non-template views from a Revit project.

    Args:
        document: Active Revit project document.

    Returns:
        Views whose ViewType is in ``TARGET_VIEW_TYPES``. This function reads
        the document and does not change view visibility.
    """
    views = DB.FilteredElementCollector(document).OfClass(DB.View).ToElements()
    result = []
    for v in views:
        if v.IsTemplate:
            continue
        if v.ViewType in TARGET_VIEW_TYPES:
            result.append(v)
    return result


def collect_matching_textnotes(document):
    """Collect text notes whose type names match the engineering-note prefix.

    Args:
        document: Active Revit project document.

    Returns:
        A tuple of matching TextNote instances and a census mapping each type
        name to ``[instance_count, matched_bool]``. The function only reads the
        document.
    """
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
    """Return whether a sheet is included in the Revit Sheet List.

    Args:
        sheet: Revit ViewSheet to inspect.
        diag: Diagnostics dictionary updated for missing or unreadable
            parameters.

    Returns:
        ``True`` only when the sheet's scheduled parameter is set. The
        built-in parameter is preferred; the localized name is a fallback.
    """
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
    """Collect eligible sheets and views placed on them.

    Args:
        document: Active Revit project document.
        diag: Diagnostics dictionary updated with sheet eligibility results.

    Returns:
        A tuple of integer sheet IDs and placed-view IDs. Only sheets that
        appear in the Sheet List contribute IDs.
    """
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


def get_placed_dependents(document, view, placed_view_ids, target_view_dict):
    """Return a primary view's dependents placed on eligible sheets.

    Args:
        document: Active Revit project document.
        view: Primary Revit View whose dependents are inspected.
        placed_view_ids: Integer IDs for views placed on eligible sheets.
        target_view_dict: Mapping of supported integer view IDs to View objects.

    Returns:
        ``[(view_id, dependent_view), ...]`` for placed dependent views.
    """
    placed = []
    for did in get_dependent_view_ids(view):
        dkey = get_elementid_value(did)
        if dkey is None or dkey not in placed_view_ids:
            continue
        dv = target_view_dict.get(dkey)
        if dv is None:
            dv = document.GetElement(did)
        if dv is not None:
            placed.append((dkey, dv))
    return placed


def build_view_note_map(document, target_views, matching_notes,
                        allowed_sheet_ids, placed_view_ids, diag):
    """Map eligible engineering notes to the views where visibility will change.

    Args:
        document: Active Revit project document.
        target_views: Supported, non-template Revit views.
        matching_notes: TextNote instances whose type matches the prefix.
        allowed_sheet_ids: Integer IDs for sheets in the Sheet List.
        placed_view_ids: Integer IDs for views placed on eligible sheets.
        diag: Diagnostics dictionary updated with exclusions and eligibility.

    Returns:
        A mapping of integer view IDs to their View object and note ElementIds.
        This function reads visibility eligibility but does not change it.
    """
    target_view_dict = {}
    for v in target_views:
        key = get_elementid_value(v.Id)
        if key is not None:
            target_view_dict[key] = v

    view_note_map = {}
    dependent_view_keys = set()

    def add_note_to_view(key, view, note_id, via_dependent=False):
        """Add one note ID to a target view without duplicates."""
        if key not in view_note_map:
            view_note_map[key] = {"view": view, "ids": []}
            if via_dependent:
                dependent_view_keys.add(key)
        # avoid duplicate ids per view
        if note_id not in view_note_map[key]["ids"]:
            view_note_map[key]["ids"].append(note_id)

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
            # Record the excluded owner type so Shift-click diagnostics explain
            # why matching notes were not eligible for this run.
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

        placed_dependents = []

        if view.ViewType == DB.ViewType.DrawingSheet:
            if key not in allowed_sheet_ids:
                diag["notes_sheet_not_in_list"] += 1
                continue
        else:
            owner_placed = key in placed_view_ids

            # A primary view qualifies when a dependent is placed on an
            # eligible sheet; this supports notes owned by primary views.
            placed_dependents = get_placed_dependents(
                document, view, placed_view_ids, target_view_dict)

            if not owner_placed and not placed_dependents:
                diag["notes_view_not_placed"] += 1
                continue

            if not owner_placed and placed_dependents:
                diag["notes_qualified_via_dependents"] += 1

        try:
            if not note.CanBeHidden(view):
                diag["notes_skipped_not_hideable"] += 1
                continue
        except Exception as ex:
            diag["state_check_failures"].append(
                u"View '{}': CanBeHidden failed: {}".format(view.Name, ex))
            continue

        diag["notes_eligible"] += 1

        # Apply the owner-view change first. Revit may propagate it to
        # dependents, but each placed dependent is evaluated independently.
        add_note_to_view(key, view, note.Id)

        # Target placed dependents explicitly so their visibility is evaluated
        # even when primary-view propagation does not apply.
        for dkey, dv in placed_dependents:
            add_note_to_view(dkey, dv, note.Id, via_dependent=True)

    diag["dependent_views_targeted"] = len(dependent_view_keys)
    return view_note_map


def ask_hide_or_unhide():
    """Prompt for a visibility action before starting a Revit transaction.

    Returns:
        A tuple of ``(hide_elements, action_label, action_word)``. All values
        are ``None`` when the user cancels.
    """
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
    """Print the Shift-click diagnostic report to pyRevit output.

    Args:
        diag: Collected classification and execution results.
        census: Text note type-name census from ``collect_matching_textnotes``.
        target_views: Supported views inspected by the command.
        matching_notes: Notes whose type names match the configured prefix.
        allowed_sheet_ids: Eligible Sheet List IDs.
        placed_view_ids: Views placed on eligible sheets.
        view_note_map: Eligible notes grouped by target view.
    """
    lines = []
    lines.append(u"=" * 70)
    lines.append(u"ENGINEER NOTES DIAGNOSTIC REPORT  (release v{})".format(
        __version__))
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
        lines.append(u"  [{}] x{:<4} {}".format(flag, count, repr(name)))
    lines.append(u"  Matching note instances: {}".format(len(matching_notes)))
    if not matching_notes:
        lines.append(u"  >> ROOT CAUSE LIKELY HERE: no type name matched the prefix.")

    lines.append(u"")
    lines.append(u"--- STAGE 2: Target views ---")
    by_type = {}
    dependents_in_targets = 0
    for v in target_views:
        t = str(v.ViewType)
        by_type[t] = by_type.get(t, 0) + 1
        if is_dependent_view(v):
            dependents_in_targets += 1
    lines.append(u"  Target views found: {}".format(len(target_views)))
    for t in sorted(by_type.keys()):
        lines.append(u"    {}: {}".format(t, by_type[t]))
    lines.append(u"  Of which dependent views: {}".format(dependents_in_targets))

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
    else:
        lines.append(u"  Owner view type not targeted: 0")
    lines.append(u"  On sheets excluded from sheet list: {}".format(
        diag["notes_sheet_not_in_list"]))
    lines.append(u"  In views not placed (and no placed dependents): {}".format(
        diag["notes_view_not_placed"]))
    lines.append(u"  Qualified ONLY via placed dependent views: {}".format(
        diag["notes_qualified_via_dependents"]))
    lines.append(u"  Skipped (not hideable): {}".format(
        diag["notes_skipped_not_hideable"]))
    lines.append(u"  ELIGIBLE notes surviving all filters: {}".format(
        diag["notes_eligible"]))

    lines.append(u"")
    lines.append(u"--- STAGE 5: Hide/Unhide execution ---")
    lines.append(u"  Views/sheets with eligible notes: {}".format(len(view_note_map)))
    lines.append(u"  Dependent views explicitly targeted: {}".format(
        diag["dependent_views_targeted"]))
    lines.append(u"  Skipped (already in requested state): {}".format(
        diag["notes_already_in_state"]))
    lines.append(u"  Failed state checks: {}".format(
        len(diag["state_check_failures"])))
    lines.append(u"  Changed in views: {}".format(diag["view_notes_changed"]))
    lines.append(u"    ...of which in dependent views: {}".format(
        diag["dependent_notes_changed"]))
    lines.append(u"  Changed on sheets: {}".format(diag["sheet_notes_changed"]))
    for failure in diag["state_check_failures"][:10]:
        lines.append(u"  !! STATE CHECK FAILED: {}".format(failure))
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
    "notes_qualified_via_dependents": 0,
    "notes_skipped_not_hideable": 0,
    "state_check_failures": [],
    "notes_eligible": 0,
    "notes_already_in_state": 0,
    "view_notes_changed": 0,
    "dependent_notes_changed": 0,
    "sheet_notes_changed": 0,
    "dependent_views_targeted": 0,
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

if view_note_map:
    with revit.Transaction("Hide/Unhide Engineer Notes"):
        for item in view_note_map.values():
            view = item["view"]
            ids_for_view = item["ids"]
            view_is_dependent = is_dependent_view(view)
            valid_ids = []

            for eid in ids_for_view:
                el = doc.GetElement(eid)
                if el is None:
                    diag["state_check_failures"].append(
                        u"View '{}': note {} no longer exists.".format(
                            view.Name, get_elementid_value(eid)))
                    continue
                try:
                    if hide_elements:
                        if el.IsHidden(view):
                            diag["notes_already_in_state"] += 1
                        elif el.CanBeHidden(view):
                            valid_ids.append(eid)
                        else:
                            diag["notes_skipped_not_hideable"] += 1
                    elif el.IsHidden(view):
                        valid_ids.append(eid)
                    else:
                        diag["notes_already_in_state"] += 1
                except Exception as ex:
                    diag["state_check_failures"].append(
                        u"View '{}', note {}: {}".format(
                            view.Name, get_elementid_value(eid), ex))

            if not valid_ids:
                continue

            try:
                net_ids = List[DB.ElementId](valid_ids)
                if hide_elements:
                    view.HideElements(net_ids)
                else:
                    view.UnhideElements(net_ids)

                if view.ViewType == DB.ViewType.DrawingSheet:
                    diag["sheet_notes_changed"] += len(valid_ids)
                else:
                    diag["view_notes_changed"] += len(valid_ids)
                    if view_is_dependent:
                        diag["dependent_notes_changed"] += len(valid_ids)
            except Exception as ex:
                diag["hide_failures"].append(
                    u"View '{}': {}".format(view.Name, ex))

        doc.Regenerate()

if DEBUG:
    print_diagnostics(diag, type_census, target_views, matching_notes,
                      allowed_sheet_ids, placed_view_ids, view_note_map)

total_changed = diag["view_notes_changed"] + diag["sheet_notes_changed"]
failed_count = len(diag["state_check_failures"]) + len(diag["hide_failures"])

output.print_md("# Hide Engineering Notes")
output.print_md("**Action:** {}".format(action_label))
output.print_md("**Changed in views:** {}".format(
    diag["view_notes_changed"]))
output.print_md("**Changed on sheets:** {}".format(
    diag["sheet_notes_changed"]))
output.print_md("**Already {}:** {}".format(
    action_word, diag["notes_already_in_state"]))
output.print_md("**Skipped (not hideable):** {}".format(
    diag["notes_skipped_not_hideable"]))
output.print_md("**Failed (state/write error):** {}".format(failed_count))

if total_changed == 0:
    if not matching_notes:
        reason = (u"No text notes matched the type prefix. Hold Shift while "
                  u"clicking to review the type-name census.")
    elif diag["notes_owner_not_target"]:
        worst = max(diag["notes_owner_not_target"].items(),
                    key=lambda kv: kv[1])
        reason = (u"Matching notes exist, but their owner views are not "
                  u"supported (most common: {}).").format(worst[0])
    elif len(allowed_sheet_ids) == 0 and diag["sheets_total"] > 0:
        reason = (u"No sheets qualified via 'Appears In Sheet List' "
                  u"({} sheets scanned).").format(diag["sheets_total"])
    elif diag["notes_already_in_state"]:
        reason = u"All eligible notes were already {}.".format(action_word)
    else:
        reason = u"Review the reported skips and failures before retrying."
    output.print_md("## Nothing changed")
    output.print_md(reason)

if diag["state_check_failures"] or diag["hide_failures"]:
    failures = diag["state_check_failures"] + diag["hide_failures"]
    output.print_md("## Items with issues")
    for failure in failures[:20]:
        output.print_md("- {}".format(failure))

if DEBUG:
    output.print_md("## Diagnostics")
    output.print_md("Full diagnostic report printed above.")
