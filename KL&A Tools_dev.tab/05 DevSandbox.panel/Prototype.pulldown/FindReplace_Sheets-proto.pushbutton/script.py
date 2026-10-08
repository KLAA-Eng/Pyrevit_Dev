# -*- coding: utf-8 -*-

__title__ = "Find and Replace in Sheets"
__version__ = "v0.1"

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝ IMPORTS
# ==================================================================
from Autodesk.Revit.DB import *

#pyRevit
from pyrevit import forms
import os
import wpf

# CUSTOM
from Snippets._selection        import get_selected_sheets
from GUI.forms                  import my_WPF
from find_replace.revit_batch import apply_batch
from find_replace.window import present
from find_replace.workflow import case_value, new_result, rename_value

# .NET IMPORTS
from clr import AddReference
AddReference("System")
from System.Diagnostics.Process import Start
from System.Windows.Window      import DragMove
from System.Windows.Input       import MouseButtonState

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝ VARIABLES
# ==================================================================
uidoc   = __revit__.ActiveUIDocument
doc     = __revit__.ActiveUIDocument.Document

selected_sheets = get_selected_sheets(given_uidoc=uidoc, title=__title__,
                                      label='Select Sheet to Rename',
                                      exit_if_none=True, version=__version__)

# ╔═╗╦ ╦╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔╔═╗
# ╠╣ ║ ║║║║║   ║ ║║ ║║║║╚═╗
# ╚  ╚═╝╝╚╝╚═╝ ╩ ╩╚═╝╝╚╝╚═╝ FUNCTIONS
# ==================================================================
def update_project_browser():
    """Function to close and reopen ProjectBrowser so changes to Sheetnumber would become visible."""
    from Autodesk.Revit.UI import DockablePanes, DockablePane
    project_browser_id = DockablePanes.BuiltInDockablePanes.ProjectBrowser
    project_browser = DockablePane(project_browser_id)
    project_browser.Hide()
    project_browser.Show()

# ╔═╗╦  ╔═╗╔═╗╔═╗╔═╗╔═╗
# ║  ║  ╠═╣╚═╗╚═╗║╣ ╚═╗
# ╚═╝╩═╝╩ ╩╚═╝╚═╝╚═╝╚═╝ CLASSES
# ==================================================================

class MyWindow(my_WPF):
    """GUI for ViewSheet renaming tool."""
    def __init__(self, xaml_file_name):
        self.add_wpf_resource()
        wpf.LoadComponent(self, os.path.join(os.path.dirname(__file__), xaml_file_name))
        self.main_title.Text = __title__
        self.footer_version.Text = __version__


    def rename(self):
        """Apply exact title and number changes together for each sheet."""
        try:
            entries = self._rename_entries()
        except ValueError as error:
            result = new_result("Rename")
            result["error"] = str(error)
            present(self, result)
            return
        except Exception as error:
            result = new_result("Rename")
            result["error"] = "Could not plan sheet renames: {0}".format(error)
            present(self, result)
            return
        self._run_batch("Rename", entries)



    def convert_sheet_names(self, case_mode):
        action = "UPPERCASE" if case_mode == "upper" else "lowercase"
        entries = []
        try:
            for sheet in selected_sheets:
                old = sheet.Name
                new = case_value(old, case_mode)
                entries.append({"element": sheet, "label": self._sheet_label(sheet),
                                "changes": [("Name", new)] if new != old else []})
        except Exception as error:
            result = new_result(action)
            result["error"] = "Could not plan case conversion: {0}".format(error)
            present(self, result)
        else:
            self._run_batch(action, entries)



    def _sheet_label(self, sheet):
        return u"{0} - {1} [{2}]".format(sheet.SheetNumber, sheet.Name,
                                          sheet.Id.IntegerValue)

    def _rename_entries(self):
        entries = []
        for sheet in selected_sheets:
            old_name = sheet.Name
            old_number = sheet.SheetNumber
            new_name = rename_value(old_name, self.sheet_name_find,
                                    self.sheet_name_replace,
                                    self.sheet_name_prefix, self.sheet_name_suffix)
            new_number = rename_value(old_number, self.sheet_number_find,
                                      self.sheet_number_replace,
                                      self.sheet_number_prefix, self.sheet_number_suffix)
            changes = []
            if new_name != old_name:
                changes.append(("Name", new_name))
            if new_number != old_number:
                changes.append(("SheetNumber", new_number))
            entries.append({"element": sheet, "label": self._sheet_label(sheet),
                            "changes": changes, "number": new_number,
                            "number_changed": new_number != old_number})

        # Check the initial state so swaps and duplicate batch targets do not
        # depend on the order in which sheets happen to be selected.
        all_sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
        occupied = {sheet.SheetNumber.lower(): sheet.Id.IntegerValue
                    for sheet in all_sheets}
        requested = {}
        for entry in entries:
            if entry["number_changed"]:
                key = entry["number"].lower()
                requested[key] = requested.get(key, 0) + 1
        for entry in entries:
            if not entry["number_changed"]:
                continue
            key = entry["number"].lower()
            owner = occupied.get(key)
            if owner is not None and owner != entry["element"].Id.IntegerValue:
                entry["issue"] = "Sheet number is already in use"
            elif requested[key] > 1:
                entry["issue"] = "Multiple selected sheets request this number"
        return entries

    def _run_batch(self, action, entries):
        result = apply_batch(doc, action, entries)
        if result["changed"]:
            try:
                update_project_browser()
            except Exception as error:
                result["error"] = "Project Browser refresh failed: {0}".format(error)
        present(self, result)

    ### GUI PROPERTIES
    # SHEETNUMBER PROPERTIES
    @property
    def sheet_number_find(self):
        return self.input_sheet_number_find.Text

    @property
    def sheet_number_replace(self):
        return self.input_sheet_number_replace.Text

    @property
    def sheet_number_prefix(self):
        return self.input_sheet_number_prefix.Text

    @property
    def sheet_number_suffix(self):
        return self.input_sheet_number_suffix.Text

    # SHEETNAME PROPERTIES
    @property
    def sheet_name_find(self):
        return self.input_sheet_name_find.Text

    @property
    def sheet_name_replace(self):
        return self.input_sheet_name_replace.Text

    @property
    def sheet_name_prefix(self):
        return self.input_sheet_name_prefix.Text

    @property
    def sheet_name_suffix(self):
        return self.input_sheet_name_suffix.Text

    # GUI EVENT HANDLERS:
    def button_close(self,sender,e):
        """Stop application by clicking on a <Close> button in the top right corner."""
        self.Close()

    def Hyperlink_RequestNavigate(self, sender, e):
        """Forwarding for a Hyperlink"""
        Start(e.Uri.AbsoluteUri)

    def header_drag(self,sender,e):
        """Drag window by holding LeftButton on the header."""
        if e.LeftButton == MouseButtonState.Pressed:
            DragMove(self)

    def button_run(self, sender, e):
        """Button action: Rename view with given """
        self.rename()

    def button_uppercase(self, sender, e):
        """Button action: Convert selected Sheet titles to uppercase."""
        self.convert_sheet_names("upper")

    def button_lowercase(self, sender, e):
        """Button action: Convert selected Sheet titles to lowercase."""
        self.convert_sheet_names("lower")

# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝ MAIN
# ==================================================================
if __name__ == '__main__':
    MyWindow("Script.xaml").ShowDialog()
