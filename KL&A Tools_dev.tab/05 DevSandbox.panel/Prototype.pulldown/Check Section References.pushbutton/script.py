# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Check Section\nReferences"
__version__ = "v0.0"

from pyrevit import DB, forms, revit, script

from section_check.conditions import describe
from section_check.revit_sections import (
    KIND_SECTION,
    check_markers,
    other_marker_count,
    reference_markers,
)
from section_check.score import LIKELY_MATCH


COMMAND_TITLE = 'Check Section References'


def _stop(message):
    forms.alert(message, title=COMMAND_TITLE, warn_icon=True)
    script.exit()


def _list(conditions):
    return '<br>'.join(describe(c) for c in conditions) or '-'


def _percent(result):
    return '-' if result['percent'] is None else '{:.0f}%'.format(result['percent'])


def _print_report(output, view, results, others):
    scored = [r['percent'] for r in results if r['percent'] is not None]
    review = [r for r in results if r['percent'] is None or r['percent'] < LIKELY_MATCH]
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('**View:** {} | **Reference sections:** {} | **Average match:** {} | '
                    '**To review (under {:.0f}% or unknown):** {}'.format(
                        view.Name, len(results),
                        '{:.0f}%'.format(sum(scored) / len(scored)) if scored else '-',
                        LIKELY_MATCH, len(review)))
    if others:
        output.print_md('{} other section, callout, or elevation marker(s) in this view are '
                        'live views of their own location and were not checked.'.format(others))
    output.print_md('The match is an approximate review guide comparing the modeled walls, '
                    'floors, framing, columns, foundations, and roofs cut at each marker with '
                    'the referenced section (or the names and notes in a referenced drafting '
                    'view). SIM accepts size and type differences; OH mirrors the reference. '
                    'Linked models are not read.')
    output.print_md('Click a marker Id to select it and show it in the view.')
    if review:
        output.print_md('Select markers to review: {}'.format(
            output.linkify([r['marker'].Id for r in review])))
    order = lambda r: (r['percent'] is not None, r['percent'], r['reference'])
    rows = []
    for result in sorted(results, key=order):
        flags = result['flags']
        noted = ', '.join(n for n, on in (('SIM', flags['sim']), ('OH', flags['oh'])) if on)
        rows.append([output.linkify(result['marker'].Id), result['reference'], result['kind'],
                     noted or '-', _percent(result), result['rating'],
                     _list(result['here']),
                     _list(result['ref']) if result['kind'] == KIND_SECTION else '-',
                     '<br>'.join(result['notes']) or '-'])
    output.print_table(rows, columns=['Marker', 'References', 'Compared with', 'SIM/OH',
                                      'Match', 'Rating', 'Cut at marker', 'Cut in reference',
                                      'Findings'])


def main():
    doc, view = revit.doc, revit.active_view
    if doc.IsFamilyDocument:
        _stop('Open a project model and run the command again.')
    if not isinstance(view, DB.ViewPlan):
        _stop('Open the plan view that shows the section markers and run again.')
    if not reference_markers(doc, view):
        _stop('No reference sections (sections set to "Reference Other View") are in "{}".'
              .format(view.Name))
    results = check_markers(doc, view)
    _print_report(script.get_output(), view, results,
                  other_marker_count(doc, view, results))


if __name__ == '__main__':
    main()
