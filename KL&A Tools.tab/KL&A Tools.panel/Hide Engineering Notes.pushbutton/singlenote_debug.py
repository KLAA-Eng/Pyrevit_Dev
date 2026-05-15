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