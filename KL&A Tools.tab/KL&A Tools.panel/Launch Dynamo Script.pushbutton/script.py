# # -*- coding: utf-8 -*-
# from __future__ import print_function
# import clr
# clr.AddReference("RevitAPI")
# clr.AddReference("RevitAPIUI")

# from Autodesk.Revit.DB import (
#     FilteredElementCollector,
#     TextNote,
#     BuiltInCategory,
#     BuiltInParameter,
#     Transaction,
#     View,
#     ViewType,
#     ElementId,
# )
# from System.Collections.Generic import List
# from pyrevit import script, forms, HOST_APP

# __title__ = "Engineer\nNotes"
# __doc__ = "Hides or unhides all engineering note text elements across all views."

# STATE_KEY    = "engineer_notes_hidden"
# current_raw  = script.get_envvar(STATE_KEY)
# is_hidden    = current_raw == "1"
# going_hidden = not is_hidden

# doc   = HOST_APP.doc
# uidoc = HOST_APP.uidoc

# # Collect all TextNote elements
# all_text_notes = (
#     FilteredElementCollector(doc)
#     .OfCategory(BuiltInCategory.OST_TextNotes)
#     .WhereElementIsNotElementType()
#     .ToElements()
# )

# # Debug: report total count so we know collector is working
# print("Total text notes found in model: {}".format(len(list(all_text_notes))))

# engineer_notes = []
# for tn in all_text_notes:
#     try:
#         type_el = doc.GetElement(tn.GetTypeId())
#         if type_el is None:
#             continue

#         # Try the standard type name parameter first
#         param = type_el.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)

#         # Fallback: try SYMBOL_NAME_PARAM
#         if param is None or not param.HasValue:
#             param = type_el.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)

#         # Fallback: check the element Name property directly
#         if param is None or not param.HasValue:
#             type_name = type_el.Name
#         else:
#             type_name = param.AsString()

#         if type_name and "ENGINEER" in type_name.upper():
#             engineer_notes.append(tn)

#     except Exception as e:
#         print("Error on element {}: {}".format(tn.Id, str(e)))
#         continue

# print("Engineer notes matched: {}".format(len(engineer_notes)))

# if not engineer_notes:
#     # Show a sample of type names so we can see what the actual values are
#     sample_names = []
#     count = 0
#     for tn in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TextNotes).WhereElementIsNotElementType().ToElements():
#         if count >= 10:
#             break
#         try:
#             type_el = doc.GetElement(tn.GetTypeId())
#             sample_names.append(type_el.Name if type_el else "None")
#             count += 1
#         except:
#             continue

#     forms.alert(
#         "No elements with 'ENGINEER' in type name found.\n\n"
#         "Sample type names from your text notes:\n{}".format(
#             "\n".join(sample_names)
#         ),
#         title="Debug Info"
#     )
#     raise SystemExit

# # Collect valid views
# UNSUPPORTED = {
#     ViewType.Schedule,
#     ViewType.ColumnSchedule,
#     ViewType.PanelSchedule,
#     ViewType.Legend,
#     ViewType.Rendering,
#     ViewType.SystemBrowser,
#     ViewType.ProjectBrowser,
#     ViewType.Undefined,
# }

# all_views = (
#     FilteredElementCollector(doc)
#     .OfClass(View)
#     .ToElements()
# )

# target_views = [
#     v for v in all_views
#     if not v.IsTemplate
#     and v.ViewType not in UNSUPPORTED
# ]

# note_ids    = [n.Id for n in engineer_notes]
# hidden_count = 0
# error_views  = []

# with Transaction(doc, "Toggle Engineer Notes Visibility") as t:
#     t.Start()
#     for view in target_views:
#         try:
#             if going_hidden:
#                 view.HideElements(List[ElementId](note_ids))
#             else:
#                 view.UnhideElements(List[ElementId](note_ids))
#             hidden_count += 1
#         except Exception:
#             error_views.append(view.Name)
#             continue
#     t.Commit()

# script.set_envvar(STATE_KEY, "1" if going_hidden else "0")

# this_script = script.get_script_bundle()
# if this_script:
#     this_script.set_highlight(going_hidden)

# note_count = len(engineer_notes)
# if going_hidden:
#     forms.alert(
#         "{} engineer note{} hidden across {} view{}.".format(
#             note_count, "s" if note_count != 1 else "",
#             hidden_count, "s" if hidden_count != 1 else "",
#         ),
#         title="Engineer Notes Hidden"
#     )
# else:
#     forms.alert("Engineering notes active.", title="Engineer Notes Visible")

# if error_views:
#     forms.alert(
#         "Could not process {} view(s):\n{}".format(
#             len(error_views),
#             "\n".join(error_views[:20])
#         ),
#         title="Some Views Skipped",
#         warn_icon=True
#     )







# # -*- coding: utf-8 -*-
# from __future__ import print_function
# import clr
# clr.AddReference("RevitAPI")
# clr.AddReference("RevitAPIUI")

# from Autodesk.Revit.DB import (
#     FilteredElementCollector,
#     BuiltInCategory,
#     BuiltInParameter,
#     Transaction,
#     View,
#     ViewType,
#     ElementId,
# )
# from System.Collections.Generic import List
# from pyrevit import script, forms, HOST_APP

# __title__ = "Engineer\nNotes"
# __doc__ = "DEBUG MODE - reports type names found in model."

# doc = HOST_APP.doc

# # -------------------------------------------------------------------
# # Collect all TextNote elements
# # -------------------------------------------------------------------
# all_text_notes = list(
#     FilteredElementCollector(doc)
#     .OfCategory(BuiltInCategory.OST_TextNotes)
#     .WhereElementIsNotElementType()
#     .ToElements()
# )

# total_count = len(all_text_notes)

# # -------------------------------------------------------------------
# # Gather ALL unique type names so we can see exactly what is in model
# # -------------------------------------------------------------------
# unique_type_names = {}  # name -> count

# for tn in all_text_notes:
#     try:
#         type_el = doc.GetElement(tn.GetTypeId())
#         if type_el is None:
#             name = "<<No Type Element>>"
#         else:
#             name = type_el.Name
#             if not name:
#                 # fallback to parameter
#                 p = type_el.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
#                 name = p.AsString() if (p and p.HasValue) else "<<Empty Name>>"
#     except Exception as ex:
#         name = "<<Error: {}>>".format(str(ex))

#     unique_type_names[name] = unique_type_names.get(name, 0) + 1

# # -------------------------------------------------------------------
# # Build a readable report for the alert popup
# # -------------------------------------------------------------------
# lines = ["Total TextNote elements: {}\n".format(total_count)]
# lines.append("Unique Type Names found:")
# for name, cnt in sorted(unique_type_names.items()):
#     lines.append("  [{}x]  {}".format(cnt, name))

# report = "\n".join(lines)

# forms.alert(
#     report,
#     title="Debug: TextNote Type Names",
#     warn_icon=False
# )






# -*- coding: utf-8 -*-
from __future__ import print_function
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
)
from pyrevit import forms, HOST_APP

__title__ = "Engineer\nNotes"
__doc__ = "DEBUG MODE - reports all unique TextNote type names."

doc = HOST_APP.doc

all_text_notes = list(
    FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_TextNotes)
    .WhereElementIsNotElementType()
    .ToElements()
)

total_count = len(all_text_notes)

# Collect every unique type name with instance count
unique_type_names = {}
for tn in all_text_notes:
    try:
        type_el = doc.GetElement(tn.GetTypeId())
        if type_el is None:
            name = "<<No Type Element>>"
        else:
            name = type_el.Name or "<<Empty Name>>"
    except Exception as ex:
        name = "<<Error: {}>>".format(str(ex))

    unique_type_names[name] = unique_type_names.get(name, 0) + 1

# Build popup report
lines = ["Total TextNote elements: {}\n".format(total_count)]
lines.append("All unique type names:")
for name, cnt in sorted(unique_type_names.items()):
    lines.append("  [{}x]  '{}'".format(cnt, name))

forms.alert("\n".join(lines), title="Debug: TextNote Type Names")