# -*- coding: utf-8 -*-

__title__ = "Find and Replace in Views"
__version__ = "v0.0"

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
from Snippets._context_manager import ef_Transaction, try_except
from Snippets._selection import get_selected_views

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
        """Get Selected Views or let user select Views from a list."""
        return get_selected_views(uidoc, title=__title__, version=__version__)

    def rename_elements(self):
        """Function to rename selected Views."""
        with ef_Transaction(self.doc, __title__, debug=True):
            for view in self.selected_elements:

                with try_except(debug=True):
                    current_name  = view.Name
                    new_name      = self.prefix + current_name.replace(self.find,self.replace) + self.suffix

                    if new_name and  new_name != current_name:
                        view.Name = new_name

    def convert_element_names(self, case_mode):
        """Convert selected View names to uppercase or lowercase."""
        with ef_Transaction(self.doc, __title__, debug=True):
            for view in self.selected_elements:

                with try_except(debug=True):
                    current_name = view.Name
                    if case_mode == "upper":
                        new_name = current_name.upper()
                    else:
                        new_name = current_name.lower()

                    if new_name and new_name != current_name:
                        view.Name = new_name

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

