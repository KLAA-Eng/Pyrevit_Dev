# -*- coding: utf-8 -*-
__title__ = 'Find and Replace in Views'
__version__ = 'v1.0'

from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector, View, ViewSheet
from pyrevit.api import AdWindows
from GUI import tool_dialogs
from GUI.dialogs import view_fields
from Snippets._selection import select_from_dict
from find_replace.controller import run
from find_replace.planning import view_entries
from find_replace.revit_batch import apply_batch
from find_replace.workflow import distinct_view_labels


def selected_views(uidoc):
    """Use browser selection, or offer distinct unchecked non-template views."""
    doc = uidoc.Document
    selected = []
    for element_id in uidoc.Selection.GetElementIds():
        view = doc.GetElement(element_id)
        if isinstance(view, View) and not isinstance(view, ViewSheet):
            selected.append(view)
    if selected:
        return selected
    all_views = FilteredElementCollector(doc).OfCategory(
        BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()
    eligible = [view for view in all_views
                if isinstance(view, View) and not isinstance(view, ViewSheet)
                and not view.IsTemplate]
    eligible.sort(key=lambda view: (view.Name.lower(), str(view.ViewType)))
    labels = distinct_view_labels([(view.Name, str(view.ViewType)) for view in eligible])
    return select_from_dict(dict(zip(labels, eligible)), title=__title__,
                            label='Select Views', button_name='Select',
                            version=__version__, initial_checked_names=[])


def main(uidoc):
    views = selected_views(uidoc)
    if not views:
        tool_dialogs.alert('No matching elements for renaming were selected.',
                           title=__title__, version=__version__)
        return
    doc = uidoc.Document
    return run(__title__, __version__, views, view_fields(), view_entries,
               lambda action, entries: apply_batch(doc, action, entries),
               owner=AdWindows.ComponentManager.ApplicationWindow)


if __name__ == '__main__':
    main(__revit__.ActiveUIDocument)
