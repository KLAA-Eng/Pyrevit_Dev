# -*- coding: utf-8 -*-

__title__ = "Find and Replace in Views"
__version__ = "v1.0"

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝ IMPORTS
#====================================================================
from Autodesk.Revit.DB import *
from pyrevit import forms
import os
import wpf

# Custom
from Renaming.BaseClass_FindReplace import BaseRenaming
from Snippets._selection import select_from_dict
from find_replace.revit_batch import apply_batch
from find_replace.window import present
from find_replace.workflow import (case_value, distinct_view_labels,
                                   new_result, rename_value)

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝ VARIABLES
#====================================================================
doc   = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument


# ╔═╗╦  ╔═╗╔═╗╔═╗
# ║  ║  ╠═╣╚═╗╚═╗
# ╚═╝╩═╝╩ ╩╚═╝╚═╝ CLASS
#====================================================================

class RenameViews(BaseRenaming):
    uidoc = __revit__.ActiveUIDocument
    doc   = __revit__.ActiveUIDocument.Document

    def __init__(self):
        self.start(title=__title__, version=__version__)

    def start(self, title, version="Version: _"):
        xaml_file_name = os.path.join(os.path.dirname(__file__), "Script.xaml")

        self.add_wpf_resource()
        wpf.LoadComponent(self, xaml_file_name)
        self.main_title.Text = title
        self.footer_version.Text = version
        self.selected_elements = self.get_selected_elements()

        if self.selected_elements:
            self.ShowDialog()
        else:
            forms.alert("No matching elements for renaming were selected. \nPlease Try again.", exitscript=True, title="Script Cancelled.")

    def get_selected_elements(self):
        """Use browser selection, or offer distinct non-template views."""
        selected = []
        for element_id in uidoc.Selection.GetElementIds():
            view = doc.GetElement(element_id)
            if isinstance(view, View) and not isinstance(view, ViewSheet):
                selected.append(view)
        if selected:
            return selected

        all_views = FilteredElementCollector(doc).OfCategory(
            BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()
        eligible_views = [view for view in all_views
                          if isinstance(view, View) and not isinstance(view, ViewSheet)
                          and not view.IsTemplate]
        eligible_views.sort(key=lambda view: (view.Name.lower(), str(view.ViewType)))
        labels = distinct_view_labels([(view.Name, str(view.ViewType))
                                       for view in eligible_views])
        choices = dict(zip(labels, eligible_views))
        return select_from_dict(choices, title=__title__, label="Select Views",
                                button_name="Select", version=__version__,
                                initial_checked_names=[])

    def rename_elements(self):
        """Rename every selected view from its current name."""
        entries = []
        try:
            for view in self.selected_elements:
                old = view.Name
                new = rename_value(old, self.find, self.replace,
                                   self.prefix, self.suffix)
                entries.append({"element": view,
                                "label": u"{0} [{1}]".format(old, view.Id.IntegerValue),
                                "changes": [("Name", new)] if new != old else []})
        except ValueError as error:
            result = new_result("Rename")
            result["error"] = str(error)
        except Exception as error:
            result = new_result("Rename")
            result["error"] = "Could not plan view renames: {0}".format(error)
        else:
            result = apply_batch(self.doc, "Rename", entries)
        present(self, result)

    def convert_element_names(self, case_mode):
        """Convert selected View names directly, without a preview."""
        action = "Uppercase" if case_mode == "upper" else "Lowercase"
        entries = []
        try:
            for view in self.selected_elements:
                old = view.Name
                new = case_value(old, case_mode)
                entries.append({"element": view,
                                "label": u"{0} [{1}]".format(old, view.Id.IntegerValue),
                                "changes": [("Name", new)] if new != old else []})
        except Exception as error:
            result = new_result(action)
            result["error"] = "Could not plan case conversion: {0}".format(error)
        else:
            result = apply_batch(self.doc, action, entries)
        present(self, result)

    def button_run(self, sender, e):
        self.rename_elements()

    def button_uppercase(self, sender, e):
        """Button action: Convert selected View names to uppercase."""
        self.convert_element_names("upper")

    def button_lowercase(self, sender, e):
        """Button action: Convert selected View names to lowercase."""
        self.convert_element_names("lower")

# ╔╦╗╔═╗╦╔╗╔
# ║║║╠═╣║║║║
# ╩ ╩╩ ╩╩╝╚╝ MAIN
#====================================================================
if __name__ == '__main__':
    x = RenameViews()

