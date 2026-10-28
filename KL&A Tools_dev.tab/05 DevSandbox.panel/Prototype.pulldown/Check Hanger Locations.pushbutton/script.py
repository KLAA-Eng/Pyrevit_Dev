# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Check Hanger\nLocations"
__version__ = "v0.0"

from pyrevit import EXEC_PARAMS, coreutils, forms, revit, script

from hanger_check.classify import (
    DEFAULT_HANGER_FAMILY,
    STATUS_REVIEW_DETAILS,
    is_problem,
)
from hanger_check.revit_check import (
    check_hangers,
    hanger_info,
    hangers_in_view,
    id_value,
    joint_targets,
    member_label,
    refresh_highlights,
    ribbon_control_id,
    selected_hangers,
    zoom_to,
)


COMMAND_TITLE = 'Check Hanger Locations'
ZOOM_COMMAND = 'Zoom to Selection'
SELECT_LINK = ('<a class="elementlink" title="Click to select in Revit" '
               'href="revit://outputhelpers?command=select&element[]={0}&show=false">{0}</a>')


class _RibbonButton(object):
    """Stand-in for output.buttonify: only the control id is needed."""
    def __init__(self, control_id):
        self.Id = control_id


def _stop(message):
    forms.alert(message, title=COMMAND_TITLE, warn_icon=True)
    script.exit()


def _select_link(element):
    """Select-only Id link: pyRevit's magnifier uses Revit's ShowElements, which
    does not reliably zoom, so zooming goes through the Zoom to Selection button."""
    return coreutils.prepare_html_str(SELECT_LINK.format(id_value(element.Id)))


def _zoom_button(output):
    # The link runs the ribbon item with this exact id, so read it from the ribbon.
    control_id = ribbon_control_id(ZOOM_COMMAND, EXEC_PARAMS.command_controlid)
    if not control_id:
        return ''
    return output.buttonify(_RibbonButton(control_id), 'Zoom to selection')


def _member_cell(doc, elements, member_id):
    if member_id is None:
        return '-'
    element = elements[member_id]
    return '{} {}'.format(_select_link(element), member_label(doc, element))


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
    zoom = _zoom_button(output)
    output.print_md('Click an Id to select it in Revit, then {} to zoom the view to it '
                    '(hangers zoom to the supported/supporting member joint). If the button '
                    'does nothing, run Prototypes > Zoom to Selection. Press Esc in Revit to '
                    'clear the selection.'.format(zoom or 'run Prototypes > Zoom to Selection'))
    if problems:
        output.print_md('Select problem hangers: {}'.format(
            output.linkify([elements[i].Id for i in problems])))
    rows = []
    order = lambda i: (not is_problem(results[i]),
                       results[i]['status'] != STATUS_REVIEW_DETAILS, i)
    for hanger_id in sorted(results, key=order):
        result = results[hanger_id]
        hanger = elements[hanger_id]
        rows.append([_select_link(hanger), hanger_info(result['hanger_values']),
                     result['status'], result['mismatch'] or '-', result['mounting'],
                     _member_cell(doc, elements, result['supported']),
                     result['supported_slope'],
                     _member_cell(doc, elements, result['supporting']),
                     '; '.join(result['notes']) or '-'])
    output.print_table(rows, columns=['Hanger', 'Hanger info', 'Status', 'Size mismatch',
                                      'Mounting', 'Supported member', 'Supported slope',
                                      'Supporting member', 'Notes'])
    if zoom and len(rows) > 10:
        output.print_md('Zoom the view to the selected element: {}'.format(zoom))


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
        zoom_to(uidoc, view, picked, joint_targets(results))
        results = dict((i, r) for i, r in results.items() if i in picked_ids)
    _print_report(script.get_output(), doc, view, 'selection' if picked else 'active view',
                  results, elements, colored)


if __name__ == '__main__':
    main()
