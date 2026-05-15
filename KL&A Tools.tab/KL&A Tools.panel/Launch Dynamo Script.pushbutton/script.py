# # -*- coding: utf-8 -*-
# import os
# import clr

# from pyrevit import HOST_APP, forms
# from Autodesk.Revit.UI import Result

# bundle_dir = os.path.dirname(__file__)
# dyn_path = os.path.join(bundle_dir, 'script.dyn')

# if not os.path.exists(dyn_path):
#     forms.alert('Could not find script.dyn:\n{}'.format(dyn_path), exitscript=True)

# uiapp = HOST_APP.uiapp
# uidoc = uiapp.ActiveUIDocument

# if uidoc is None or uidoc.Document is None:
#     forms.alert('Open a Revit model or family first.', exitscript=True)

# try:
#     clr.AddReference('DynamoRevitDS')
# except:
#     clr.AddReference('DynamoRevit')

# from Dynamo.Applications import DynamoRevit, DynamoRevitCommandData, JournalKeys

# journal_data = {
#     JournalKeys.ShowUiKey: 'True',
#     JournalKeys.AutomationModeKey: 'True',
#     JournalKeys.DynPathKey: dyn_path,
#     JournalKeys.DynPathExecuteKey: 'True',
#     JournalKeys.ForceManualRunKey: 'False',
#     JournalKeys.ModelShutDownKey: 'False',
#     JournalKeys.ModelNodesInfo: 'True'
# }

# cmd = DynamoRevitCommandData()
# cmd.Application = uiapp
# cmd.JournalData = journal_data

# result = DynamoRevit().ExecuteCommand(cmd)

# forms.alert('Dynamo launch returned: {}'.format(result))


# # -*- coding: utf-8 -*-
# __title__ = "Hide/Unhide KLAA Notes"

# from pyrevit import revit, DB, forms

# doc = revit.doc

# # -----------------------------------------------------------------------------
# # USER SETTINGS
# # -----------------------------------------------------------------------------

# # Generic Annotation family/type name prefixes from the Dynamo graph
# GENERIC_ANNOTATION_PREFIXES = [
#     "KLAA_",
#     "BGA",
#     "ZTBA"
# ]

# # Text style prefix from the Dynamo graph
# TEXTNOTE_TYPE_PREFIX = "KLAA - ENGINEER'S NOTE"

# # View types from the Dynamo graph
# TARGET_VIEW_TYPES = {
#     DB.ViewType.EngineeringPlan,
#     DB.ViewType.Legend,
#     DB.ViewType.DraftingView,
#     DB.ViewType.Detail,
#     DB.ViewType.Schedule,
# }

# # True = Hide, False = Unhide
# hide_elements = forms.alert(
#     "Choose action:\n\nYes = Hide elements\nNo = Unhide elements",
#     yes=True,
#     no=True,
#     ok=False
# )

# if hide_elements is None:
#     forms.alert("Operation cancelled.", exitscript=True)

# # -----------------------------------------------------------------------------
# # HELPERS
# # -----------------------------------------------------------------------------

# def get_type_name(element, document):
#     """Return the element type name for an element instance."""
#     type_id = element.GetTypeId()
#     if type_id == DB.ElementId.InvalidElementId:
#         return None
#     etype = document.GetElement(type_id)
#     if etype:
#         return etype.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString() \
#                or etype.Name
#     return None

# def starts_with_any(value, prefixes):
#     if not value:
#         return False
#     value_upper = value.upper()
#     return any(value_upper.startswith(p.upper()) for p in prefixes)

# def collect_target_views(document):
#     views = DB.FilteredElementCollector(document).OfClass(DB.View).ToElements()
#     result = []
#     for v in views:
#         if v.IsTemplate:
#             continue
#         if v.ViewType in TARGET_VIEW_TYPES:
#             result.append(v)
#     return result

# def collect_generic_annotation_instances(document):
#     elems = (
#         DB.FilteredElementCollector(document)
#         .OfCategory(DB.BuiltInCategory.OST_GenericAnnotation)
#         .WhereElementIsNotElementType()
#         .ToElements()
#     )

#     matches = []
#     for elem in elems:
#         type_name = get_type_name(elem, document)
#         if starts_with_any(type_name, GENERIC_ANNOTATION_PREFIXES):
#             matches.append(elem)
#     return matches

# def collect_textnote_instances_by_type_prefix(document):
#     textnotes = (
#         DB.FilteredElementCollector(document)
#         .OfClass(DB.TextNote)
#         .WhereElementIsNotElementType()
#         .ToElements()
#     )

#     matches = []
#     for note in textnotes:
#         type_name = get_type_name(note, document)
#         if type_name and type_name.upper().startswith(TEXTNOTE_TYPE_PREFIX.upper()):
#             matches.append(note)
#     return matches

# def view_can_process_elements(view):
#     try:
#         return not view.IsTemplate
#     except:
#         return False

# # -----------------------------------------------------------------------------
# # MAIN
# # -----------------------------------------------------------------------------

# ga_elements = collect_generic_annotation_instances(doc)
# textnote_elements = collect_textnote_instances_by_type_prefix(doc)
# target_views = collect_target_views(doc)

# all_element_ids = list({e.Id.IntegerValue: e.Id for e in (ga_elements + textnote_elements)}.values())

# if not all_element_ids:
#     forms.alert("No matching elements found.", exitscript=True)

# if not target_views:
#     forms.alert("No matching target views found.", exitscript=True)

# processed_views = 0
# failed_views = []

# with revit.Transaction("Hide/Unhide targeted annotation elements in views"):
#     for view in target_views:
#         if not view_can_process_elements(view):
#             continue

#         try:
#             if hide_elements:
#                 hideable_ids = DB.List[DB.ElementId]()
#                 for eid in all_element_ids:
#                     try:
#                         if not view.IsElementHidden(eid):
#                             hideable_ids.Add(eid)
#                     except:
#                         pass

#                 if hideable_ids.Count > 0:
#                     view.HideElements(hideable_ids)

#             else:
#                 unhideable_ids = DB.List[DB.ElementId]()
#                 for eid in all_element_ids:
#                     try:
#                         if view.IsElementHidden(eid):
#                             unhideable_ids.Add(eid)
#                     except:
#                         pass

#                 if unhideable_ids.Count > 0:
#                     view.UnhideElements(unhideable_ids)

#             processed_views += 1

#         except Exception as ex:
#             failed_views.append("{}: {}".format(view.Name, str(ex)))

# msg = (
#     "Done.\n\n"
#     "Action: {0}\n"
#     "Target views processed: {1}\n"
#     "Generic annotations matched: {2}\n"
#     "Text notes matched: {3}\n"
#     "Total unique elements targeted: {4}"
# ).format(
#     "Hide" if hide_elements else "Unhide",
#     processed_views,
#     len(ga_elements),
#     len(textnote_elements),
#     len(all_element_ids)
# )

# if failed_views:
#     msg += "\n\nViews with issues:\n- " + "\n- ".join(failed_views[:20])

# forms.alert(msg)

# -*- coding: utf-8 -*-
__title__ = "Hide/Unhide KLAA Text Notes"
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
    "Choose action:\n\nYes = Hide text notes\nNo = Unhide text notes",
    yes=True,
    no=True,
    ok=False
)

if hide_elements is None:
    forms.alert("Operation cancelled.", exitscript=True)


def get_type_name(element, document):
    etype = document.GetElement(element.GetTypeId())
    if not etype:
        return None
    p = etype.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    if p and p.HasValue:
        return p.AsString()
    return etype.Name


textnotes = (
    DB.FilteredElementCollector(doc)
    .OfClass(DB.TextNote)
    .WhereElementIsNotElementType()
    .ToElements()
)

view_to_ids = {}
match_count = 0

for note in textnotes:
    type_name = get_type_name(note, doc)
    if not type_name:
        continue
    if not type_name.upper().startswith(TEXTNOTE_TYPE_PREFIX.upper()):
        continue

    owner_view = doc.GetElement(note.OwnerViewId)
    if not owner_view or owner_view.IsTemplate:
        continue
    if owner_view.ViewType not in TARGET_VIEW_TYPES:
        continue

    match_count += 1
    key = owner_view.Id.IntegerValue
    if key not in view_to_ids:
        view_to_ids[key] = {"view": owner_view, "ids": List[DB.ElementId]()}
    view_to_ids[key]["ids"].Add(note.Id)

processed = 0
failed = []

with revit.Transaction("Hide/Unhide KLAA text notes by owner view"):
    for item in view_to_ids.values():
        view = item["view"]
        ids_in_view = item["ids"]

        try:
            ids_to_process = List[DB.ElementId]()
            for eid in ids_in_view:
                try:
                    is_hidden = view.IsElementHidden(eid)
                    if hide_elements and not is_hidden:
                        ids_to_process.Add(eid)
                    elif not hide_elements and is_hidden:
                        ids_to_process.Add(eid)
                except:
                    pass

            if ids_to_process.Count > 0:
                if hide_elements:
                    view.HideElements(ids_to_process)
                else:
                    view.UnhideElements(ids_to_process)

            processed += 1
        except Exception as ex:
            failed.append("{}: {}".format(view.Name, str(ex)))

msg = "Done.\n\nAction: {0}\nMatched text notes: {1}\nViews processed: {2}".format(
    "Hide" if hide_elements else "Unhide",
    match_count,
    processed
)

if failed:
    msg += "\n\nViews with issues:\n- " + "\n- ".join(failed[:20])

forms.alert(msg)