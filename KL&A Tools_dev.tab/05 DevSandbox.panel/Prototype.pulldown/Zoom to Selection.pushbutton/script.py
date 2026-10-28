# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Zoom to\nSelection"
__version__ = "v0.0"

from pyrevit import forms, revit, script

from hanger_check.revit_check import zoom_to


COMMAND_TITLE = 'Zoom to Selection'


def main():
    doc, uidoc, view = revit.doc, revit.uidoc, revit.active_view
    elements = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
    if not elements:
        forms.alert('Select a hanger or member (click its Id in the Check Hanger Locations '
                    'report) and run again.', title=COMMAND_TITLE, warn_icon=True)
        script.exit()
    hidden = zoom_to(uidoc, view, elements)
    if len(hidden) == len(elements):
        forms.alert('None of the selected elements is visible in "{}". Open a view that '
                    'shows them and run again.'.format(view.Name),
                    title=COMMAND_TITLE, warn_icon=True)
    elif hidden:
        forms.alert('Zoomed to {} element(s); {} selected element(s) are not visible in "{}".'
                    .format(len(elements) - len(hidden), len(hidden), view.Name),
                    title=COMMAND_TITLE)


if __name__ == '__main__':
    main()
