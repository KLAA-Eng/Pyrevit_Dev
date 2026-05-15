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


###LAST SEMI WORKING ATTEMPT
#
# __title__ = "Hide/Unhide KLAA Text Notes"
# from pyrevit import revit, DB, forms
# import clr
# clr.AddReference("System")
# from System.Collections.Generic import List

# doc = revit.doc

# TEXTNOTE_TYPE_PREFIX = "KLAA - ENGINEER'S NOTE"
# TARGET_VIEW_TYPES = {
#     DB.ViewType.EngineeringPlan,
#     DB.ViewType.Legend,
#     DB.ViewType.DraftingView,
#     DB.ViewType.Detail,
#     DB.ViewType.Schedule,
# }

# hide_elements = forms.alert(
#     "Choose action:\n\nYes = Hide text notes\nNo = Unhide text notes",
#     yes=True,
#     no=True,
#     ok=False
# )

# if hide_elements is None:
#     forms.alert("Operation cancelled.", exitscript=True)


# def get_type_name(element, document):
#     etype = document.GetElement(element.GetTypeId())
#     if not etype:
#         return None
#     p = etype.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
#     if p and p.HasValue:
#         return p.AsString()
#     return etype.Name


# textnotes = (
#     DB.FilteredElementCollector(doc)
#     .OfClass(DB.TextNote)
#     .WhereElementIsNotElementType()
#     .ToElements()
# )

# view_to_ids = {}
# match_count = 0

# for note in textnotes:
#     type_name = get_type_name(note, doc)
#     if not type_name:
#         continue
#     if not type_name.upper().startswith(TEXTNOTE_TYPE_PREFIX.upper()):
#         continue

#     owner_view = doc.GetElement(note.OwnerViewId)
#     if not owner_view or owner_view.IsTemplate:
#         continue
#     if owner_view.ViewType not in TARGET_VIEW_TYPES:
#         continue

#     match_count += 1
#     key = owner_view.Id.IntegerValue
#     if key not in view_to_ids:
#         view_to_ids[key] = {"view": owner_view, "ids": List[DB.ElementId]()}
#     view_to_ids[key]["ids"].Add(note.Id)

# processed = 0
# failed = []

# with revit.Transaction("Hide/Unhide KLAA text notes by owner view"):
#     for item in view_to_ids.values():
#         view = item["view"]
#         ids_in_view = item["ids"]

#         try:
#             ids_to_process = List[DB.ElementId]()
#             for eid in ids_in_view:
#                 try:
#                     is_hidden = view.IsElementHidden(eid)
#                     if hide_elements and not is_hidden:
#                         ids_to_process.Add(eid)
#                     elif not hide_elements and is_hidden:
#                         ids_to_process.Add(eid)
#                 except:
#                     pass

#             if ids_to_process.Count > 0:
#                 if hide_elements:
#                     view.HideElements(ids_to_process)
#                 else:
#                     view.UnhideElements(ids_to_process)

#             processed += 1
#         except Exception as ex:
#             failed.append("{}: {}".format(view.Name, str(ex)))

# msg = "Done.\n\nAction: {0}\nMatched text notes: {1}\nViews processed: {2}".format(
#     "Hide" if hide_elements else "Unhide",
#     match_count,
#     processed
# )

# if failed:
#     msg += "\n\nViews with issues:\n- " + "\n- ".join(failed[:20])

# forms.alert(msg)


#another attempt

# # -*- coding: utf-8 -*-
# __title__ = "Hide/Unhide KLAA Text Notes"

# from pyrevit import revit, DB, forms
# import clr
# clr.AddReference("System")
# from System.Collections.Generic import List

# doc = revit.doc

# TEXTNOTE_TYPE_PREFIX = "KLAA - ENGINEER'S NOTE"
# TARGET_VIEW_TYPES = {
#     DB.ViewType.EngineeringPlan,
#     DB.ViewType.Legend,
#     DB.ViewType.DraftingView,
#     DB.ViewType.Detail,
#     DB.ViewType.Schedule,
# }

# hide_elements = forms.alert(
#     "Choose action:\n\nYes = Hide text notes\nNo = Unhide text notes",
#     yes=True,
#     no=True,
#     ok=False
# )

# if hide_elements is None:
#     forms.alert("Operation cancelled.", exitscript=True)


# def get_textnote_type_name(note):
#     note_type = doc.GetElement(note.GetTypeId())
#     if not note_type:
#         return None

#     p = note_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
#     if p and p.HasValue:
#         return p.AsString()

#     return note_type.Name


# textnotes = (
#     DB.FilteredElementCollector(doc)
#     .OfClass(DB.TextNote)
#     .WhereElementIsNotElementType()
#     .ToElements()
# )

# view_map = {}
# matched = 0

# for note in textnotes:
#     type_name = get_textnote_type_name(note)
#     if not type_name:
#         continue
#     if not type_name.upper().startswith(TEXTNOTE_TYPE_PREFIX.upper()):
#         continue

#     owner_view = doc.GetElement(note.OwnerViewId)
#     if owner_view is None or owner_view.IsTemplate:
#         continue
#     if owner_view.ViewType not in TARGET_VIEW_TYPES:
#         continue

#     try:
#         if not note.CanBeHidden(owner_view):
#             continue
#     except:
#         continue

#     key = owner_view.Id.IntegerValue
#     if key not in view_map:
#         view_map[key] = {
#             "view": owner_view,
#             "ids": []
#         }

#     view_map[key]["ids"].append(note.Id)
#     matched += 1

# processed = 0
# changed = 0
# failed = []

# with revit.Transaction("Hide/Unhide KLAA text notes"):
#     for item in view_map.values():
#         view = item["view"]
#         raw_ids = item["ids"]

#         try:
#             valid_ids = []
#             for eid in raw_ids:
#                 try:
#                     el = doc.GetElement(eid)
#                     if el is None:
#                         continue
#                     if hide_elements:
#                         if not view.IsElementHidden(eid):
#                             valid_ids.append(eid)
#                     else:
#                         if view.IsElementHidden(eid):
#                             valid_ids.append(eid)
#                 except:
#                     pass

#             if valid_ids:
#                 net_ids = List[DB.ElementId](valid_ids)

#                 if hide_elements:
#                     view.HideElements(net_ids)
#                 else:
#                     view.UnhideElements(net_ids)

#                 changed += len(valid_ids)

#             processed += 1

#         except Exception as ex:
#             failed.append("{}: {}".format(view.Name, str(ex)))

#     doc.Regenerate()

# msg = (
#     "Done.\n\n"
#     "Action: {0}\n"
#     "Matched text notes: {1}\n"
#     "Views processed: {2}\n"
#     "Notes changed: {3}"
# ).format(
#     "Hide" if hide_elements else "Unhide",
#     matched,
#     processed,
#     changed
# )

# if failed:
#     msg += "\n\nViews with issues:\n- " + "\n- ".join(failed[:20])

# forms.alert(msg)


#TRY JUST A SINGLE SELECTED NOTE
# -*- coding: utf-8 -*-
from pyrevit import revit, DB, forms
import clr
clr.AddReference("System")
from System.Collections.Generic import List

uidoc = revit.uidoc
doc = revit.doc
view = doc.ActiveView

sel_ids = list(uidoc.Selection.GetElementIds())
if len(sel_ids) != 1:
    forms.alert("Select exactly one text note in the active view first.", exitscript=True)

eid = sel_ids[0]
el = doc.GetElement(eid)

lines = []
lines.append("Element class: {}".format(el.GetType().Name))
lines.append("Element id: {}".format(eid.IntegerValue))
lines.append("Active view: {}".format(view.Name))
lines.append("OwnerViewId: {}".format(el.OwnerViewId.IntegerValue if hasattr(el, "OwnerViewId") else "n/a"))

try:
    lines.append("CanBeHidden(active view): {}".format(el.CanBeHidden(view)))
except Exception as ex:
    lines.append("CanBeHidden error: {}".format(str(ex)))

try:
    lines.append("Before hidden: {}".format(view.IsElementHidden(eid)))
except Exception as ex:
    lines.append("Before hidden check error: {}".format(str(ex)))

hide_error = None
try:
    with revit.Transaction("Test Hide One Text Note"):
        ids = List[DB.ElementId]()
        ids.Add(eid)
        view.HideElements(ids)
        doc.Regenerate()
except Exception as ex:
    hide_error = str(ex)

if hide_error:
    lines.append("HideElements error: {}".format(hide_error))
else:
    try:
        lines.append("After hidden: {}".format(view.IsElementHidden(eid)))
    except Exception as ex:
        lines.append("After hidden check error: {}".format(str(ex)))

forms.alert("\n".join(lines))