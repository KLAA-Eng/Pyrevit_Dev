# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Check Hanger\nLocations"
__version__ = "v0.0"

from pyrevit import forms, revit, script

from hanger_check.classify import (
    DEFAULT_HANGER_FAMILY,
    STATUS_REVIEW_DETAILS,
    is_problem,
    match_label,
)
from hanger_check.revit_check import (
    check_hangers,
    hanger_info,
    hangers_in_view,
    id_value,
    member_label,
    refresh_highlights,
    selected_hangers,
    zoom_to,
)


COMMAND_TITLE = 'Check Hanger Locations'


def _stop(message):
    forms.alert(message, title=COMMAND_TITLE, warn_icon=True)
    script.exit()


def _member_cell(output, doc, elements, member_id):
    if member_id is None:
        return '-'
    element = elements[member_id]
    return '{} {}'.format(output.linkify(element.Id), member_label(doc, element))


def _print_report(output, doc, view, source, results, elements, colored):
    problems = [i for i, r in results.items() if is_problem(r)]
    details = [i for i, r in results.items() if r['status'] == STATUS_REVIEW_DETAILS]
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('**Hangers reported:** {} ({}) | **Problems:** {} | **Review details:** {} | '
                    '**View:** {}'.format(len(results), source, len(problems), len(details),
                                          view.Name))
    if colored:
        output.print_md('Colors: supported member = blue, supporting member = orange, '
                        'both = purple. Hanger hexagon outline: red = problem, teal = '
                        'review details. Use Hanger Highlights to turn them off.')
    else:
        output.print_md('Graphics overrides are not allowed in this view; nothing was colored.')
    output.print_md('Click an Id to select it (press Esc in Revit to clear the selection). '
                    'To zoom to a hanger, select it and run this command again.')
    if problems:
        output.print_md('Select problem hangers: {}'.format(
            output.linkify([elements[i].Id for i in problems])))
    rows = []
    order = lambda i: (not is_problem(results[i]),
                       results[i]['status'] != STATUS_REVIEW_DETAILS, i)
    for hanger_id in sorted(results, key=order):
        result = results[hanger_id]
        hanger = elements[hanger_id]
        rows.append([output.linkify(hanger.Id), hanger_info(result['hanger_values']),
                     result['status'], match_label(result), result['mismatch'],
                     result['mounting'],
                     _member_cell(output, doc, elements, result['supported']),
                     _member_cell(output, doc, elements, result['supporting']),
                     '; '.join(result['notes']) or '-'])
    output.print_table(rows, columns=['Hanger', 'Hanger info', 'Status', 'Location match',
                                      'Size mismatch', 'Mounting', 'Supported member',
                                      'Supporting member', 'Notes'])


def main():
    doc, uidoc, view = revit.doc, revit.uidoc, revit.active_view
    if doc.IsFamilyDocument:
        _stop('Open a project model and run the command again.')

    picked = selected_hangers(uidoc)
    in_view = hangers_in_view(doc, view)
    if not picked and not in_view:
        _stop('No "{}" hanger families were selected or visible in the active view.'.format(
            DEFAULT_HANGER_FAMILY))
    picked_ids = set(id_value(h.Id) for h in picked)
    view_ids = set(id_value(h.Id) for h in in_view)
    hangers = in_view + [h for h in picked if id_value(h.Id) not in view_ids]

    elements = {}
    results = check_hangers(doc, view, hangers, elements)
    colored = view.AreGraphicsOverridesAllowed()
    if colored:
        refresh_highlights(doc, view, results, elements, revit.Transaction)

    if picked:
        zoom_to(uidoc, view, picked)
        results = dict((i, r) for i, r in results.items() if i in picked_ids)
    _print_report(script.get_output(), doc, view, 'selection' if picked else 'active view',
                  results, elements, colored)


if __name__ == '__main__':
    main()
