"""
Toggle visibility of engineering note elements across all views.
Identifies elements where the Type Name parameter contains 'ENGINEER'.
"""
__title__ = "Engineer\nNotes"
__doc__ = "Hides or unhides all engineering note text elements across all views."

import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from System.Collections.Generic import List
from Autodesk.Revit.DB import ElementId

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    TextNote,
    BuiltInCategory,
    Transaction,
    View,
    ViewType,
)
from pyrevit import script, forms
from pyrevit import HOST_APP

# State Tracking
STATE_KEY   = "engineer_notes_hidden"
current_raw = script.get_envvar(STATE_KEY)
is_hidden   = current_raw == "1"          # True  = notes are currently hidden
going_hidden = not is_hidden              # what we're about to do

# Bring in Revit file
doc   = HOST_APP.doc
uidoc = HOST_APP.uidoc

# Collect all TextNote elements whose Type Name contains "ENGINEER"
all_text_notes = (
    FilteredElementCollector(doc)
    .OfCategory(BuiltInCategory.OST_TextNotes)
    .WhereElementIsNotElementType()
    .ToElements()
)

engineer_notes = []
for tn in all_text_notes:
    try:
        type_el   = doc.GetElement(tn.GetTypeId())
        type_name = type_el.get_Parameter(
            Autodesk.Revit.DB.BuiltInParameter.ALL_MODEL_TYPE_NAME
        ).AsString()
        if "ENGINEER" in type_name.upper():
            engineer_notes.append(tn)
    except Exception:
        continue

if not engineer_notes:
    forms.alert(
        "No text elements with 'ENGINEER' in the type name were found.",
        title="Engineer Notes"
    )
    # Don't flip state — nothing happened
    raise SystemExit

# Collect all views that support Hide in View
UNSUPPORTED_VIEW_TYPES = {
    ViewType.Schedule,
    ViewType.ColumnSchedule,
    ViewType.PanelSchedule,
    ViewType.Legend,
    ViewType.Rendering,
    ViewType.SystemBrowser,
    ViewType.ProjectBrowser,
    ViewType.Undefined,
}

all_views = (
    FilteredElementCollector(doc)
    .OfClass(View)
    .ToElements()
)

target_views = [
    v for v in all_views
    if not v.IsTemplate
    and v.ViewType not in UNSUPPORTED_VIEW_TYPES
    and not v.IsCallout          # callouts share parent view overrides
]

# Hide or Unhide across all target views in a single transaction
note_ids    = [n.Id for n in engineer_notes]
hidden_count = 0
error_views  = []

with Transaction(doc, "Toggle Engineer Notes Visibility") as t:
    t.Start()
    for view in target_views:
        try:
            if going_hidden:
                view.HideElements(List[ElementId](note_ids))
            else:
                view.UnhideElements(List[ElementId](note_ids))
            hidden_count += 1
        except Exception:
            error_views.append(view.Name)
            continue
    t.Commit()

# Flip state and update button graphically
script.set_envvar(STATE_KEY, "1" if going_hidden else "0")

this_script = script.get_script_bundle()
if this_script:
    this_script.set_highlight(going_hidden)   # color ON when hidden

# Confirmation prompt
note_count = len(engineer_notes)

if going_hidden:
    msg = "{} engineer note{} hidden across {} view{}.".format(
        note_count,
        "s" if note_count != 1 else "",
        hidden_count,
        "s" if hidden_count != 1 else "",
    )
    forms.alert(msg, title="Engineer Notes Hidden")
else:
    forms.alert(
        "Engineering notes active.",
        title="Engineer Notes Visible"
    )

# report any views that threw errors
if error_views:
    forms.alert(
        "Could not process {} view(s):\n{}".format(
            len(error_views),
            "\n".join(error_views[:20])   # cap at 20 to avoid giant dialog
        ),
        title="Some Views Skipped",
        warn_icon=True
    )