# -*- coding: utf-8 -*-
__title__ = 'Find and Replace in Sheets'
__version__ = 'v1.1'

from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet
from pyrevit.api import AdWindows
from GUI.dialogs import sheet_fields
from Snippets._selection import get_selected_sheets
from find_replace.controller import run
from find_replace.planning import sheet_entries
from find_replace.revit_batch import apply_batch


def update_project_browser():
    """Refresh displayed sheet numbers after a committed model change."""
    from Autodesk.Revit.UI import DockablePanes, DockablePane
    browser = DockablePane(DockablePanes.BuiltInDockablePanes.ProjectBrowser)
    browser.Hide()
    browser.Show()


def main(uidoc):
    sheets = get_selected_sheets(given_uidoc=uidoc, title=__title__,
                                label='Select Sheet to Rename', exit_if_none=True,
                                version=__version__, initial_checked_names=[])
    if not sheets:
        return
    doc = uidoc.Document
    def plan(items, request):
        all_sheets = (FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
                      if request['operation'] == 'rename' else [])
        return sheet_entries(items, request, all_sheets)
    return run(__title__, __version__, sheets, sheet_fields(), plan,
               lambda action, entries: apply_batch(doc, action, entries),
               after_change=update_project_browser,
               owner=AdWindows.ComponentManager.ApplicationWindow)


if __name__ == '__main__':
    main(__revit__.ActiveUIDocument)
