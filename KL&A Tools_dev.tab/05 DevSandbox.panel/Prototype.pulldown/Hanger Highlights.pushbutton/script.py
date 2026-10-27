# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Hanger\nHighlights"
__version__ = "v0.0"

from pyrevit import forms, revit, script

from hanger_check.classify import is_problem
from hanger_check.revit_check import (
    check_hangers,
    clear_highlights,
    has_highlights,
    hangers_in_view,
    refresh_highlights,
)


COMMAND_TITLE = 'Hanger Highlights'


def main():
    doc, view = revit.doc, revit.active_view
    if doc.IsFamilyDocument or not view.AreGraphicsOverridesAllowed():
        forms.alert('Open a project view that allows graphic overrides.',
                    title=COMMAND_TITLE, warn_icon=True)
        script.exit()

    if has_highlights(doc, view):
        cleared = clear_highlights(doc, view, revit.Transaction)
        forms.alert('Hanger highlights off: cleared {} element(s) in "{}".'.format(
            cleared, view.Name), title=COMMAND_TITLE)
        return

    hangers = hangers_in_view(doc, view)
    if not hangers:
        forms.alert('No hangers are visible in "{}".'.format(view.Name), title=COMMAND_TITLE)
        return
    elements = {}
    results = check_hangers(doc, hangers, elements)
    refresh_highlights(doc, view, results, elements, revit.Transaction)
    problems = sum(1 for r in results.values() if is_problem(r))
    forms.alert('Hanger highlights on: {} hanger(s) checked, {} with a problem. Run Check '
                'Hanger Locations for the report.'.format(len(results), problems),
                title=COMMAND_TITLE)


if __name__ == '__main__':
    main()
