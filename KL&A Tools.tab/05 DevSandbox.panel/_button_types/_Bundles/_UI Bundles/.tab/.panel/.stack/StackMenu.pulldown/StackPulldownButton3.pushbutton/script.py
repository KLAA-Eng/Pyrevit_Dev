# -*- coding: utf-8 -*-
__title__ = "Stack Pulldown Button 3"
__doc__ = """Date    = 01.01.2023
_____________________________________________________________________
Description:
Examples of ISelectionFilter to limit Element Selection.
_____________________________________________________________________
Author: Erik Frits"""

# ╦╔╦╗╔═╗╔═╗╦═╗╔╦╗╔═╗
# ║║║║╠═╝║ ║╠╦╝ ║ ╚═╗
# ╩╩ ╩╩  ╚═╝╩╚═ ╩ ╚═╝ IMPORTS
#==================================================
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import Room, RoomTag
from Autodesk.Revit.UI.Selection import ObjectType, PickBoxStyle, Selection, ISelectionFilter

# .NET Imports
import clr
clr.AddReference("System")
from System.Collections.Generic import List

# ╦  ╦╔═╗╦═╗╦╔═╗╔╗ ╦  ╔═╗╔═╗
# ╚╗╔╝╠═╣╠╦╝║╠═╣╠╩╗║  ║╣ ╚═╗
#  ╚╝ ╩ ╩╩╚═╩╩ ╩╚═╝╩═╝╚═╝╚═╝ VARIABLES
#==================================================
uidoc = __revit__.ActiveUIDocument
doc   = __revit__.ActiveUIDocument.Document

selection = uidoc.Selection # type: Selection

# ╔═╗╦  ╔═╗╔═╗╔═╗
# ║  ║  ╠═╣╚═╗╚═╗
# ╚═╝╩═╝╩ ╩╚═╝╚═╝ CLASSES
#==================================================

#🔶 ISelectionFilter
class CustomFilter(ISelectionFilter):

    def AllowElement(self, element):
        if element.Category.BuiltInCategory == BuiltInCategory.OST_Walls:
            return True

# custom_filter     = CustomFilter()
# selected_elements = selection.PickElementsByRectangle(custom_filter, "Select rooms ")
# print(selected_elements)



class ISelectionFilter_Classes(ISelectionFilter):
    def __init__(self, allowed_types):
        """ ISelectionFilter made to filter with types
        :param allowed_types: list of allowed Types"""
        self.allowed_types = allowed_types

    def AllowElement(self, element):
        if type(element) in self.allowed_types:
            return True

# filter_types    = ISelectionFilter_Classes([Room, RoomTag])
# selected_elements = selection.PickObjects(ObjectType.Element, filter_types)


class ISelectionFilter_Categories(ISelectionFilter):
    def __init__(self, allowed_categories):
        """ ISelectionFilter made to filter with categories
        :param allowed_types: list of allowed Categories"""
        self.allowed_categories = allowed_categories

    def AllowElement(self, element):
        if element.Category.BuiltInCategory in self.allowed_categories:
            return True



filter_cats       = ISelectionFilter_Categories([BuiltInCategory.OST_Walls])
selected_elements = selection.PickObjects(ObjectType.Element, filter_cats)

for ref in selected_elements:
    el = doc.GetElement(ref)
    print(el)








# [More Advanced example] ONLY Pick Wall with Height between 1-2 meters and 'Beton' in Type Name
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
#🔻 Define ISelectionFilter
class WallSelectionFilter(ISelectionFilter):
    def AllowElement(self, element):
        if type(element) == Wall:
            # Get Type Name
            type_name = element.get_Parameter(BuiltInParameter.ELEM_TYPE_PARAM).AsValueString()

            # Get Height
            height_ft = element.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()
            height_m = convert_internal_units(height_ft, get_internal=False, units='m')

            # Check if height is between 1 to 2 meters
            if 1 <= height_m <= 2 and 'Beton' in type_name:
                return True


# 🎯 Pick a Wall matching criteria
ref_wall = uidoc.Selection.PickObject(ObjectType.Element,
                                      WallSelectionFilter(),
                                      "Select a wall")
wall = doc.GetElement(ref_wall)




