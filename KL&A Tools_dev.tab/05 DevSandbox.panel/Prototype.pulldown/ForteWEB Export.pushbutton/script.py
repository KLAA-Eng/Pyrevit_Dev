# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "ForteWEB\nExport"
__version__ = "v0.0"

import os

from Autodesk.Revit.Exceptions import OperationCanceledException
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType
from pyrevit import EXEC_PARAMS, forms, revit, script

from forteweb_export.revit_export import ExportError, is_exportable, run_export
from forteweb_export.workflow import (
    DEFAULT_HANGER_FAMILY,
    DEFAULT_TOLERANCE_IN,
    SYSTEM_OVERRIDES,
    parse_tolerance,
)


COMMAND_TITLE = 'ForteWEB Export'
config = script.get_config('forteweb_export')


def _stop(message):
    forms.alert(message, title=COMMAND_TITLE, warn_icon=True)
    script.exit()


def _settings():
    return {
        'template': config.get_option('template_path', ''),
        'tolerance': config.get_option('tolerance_in', DEFAULT_TOLERANCE_IN),
        'hanger': config.get_option('hanger_family', DEFAULT_HANGER_FAMILY),
        'system': config.get_option('system_override', 'auto'),
    }


def _pick_template(current=''):
    init_dir = os.path.dirname(current) if current else ''
    path = forms.pick_file(file_ext='4wf', init_dir=init_dir,
                           title='Select ForteWEB template .4wf (one member of each kind)')
    if path:
        config.template_path = path
        script.save_config()
    return path


def _edit_settings():
    """Shift+Click: template, tolerance, hanger family and floor/roof override."""
    current = _settings()
    if not _pick_template(current['template']) and not current['template']:
        return
    tolerance = forms.ask_for_string(
        default=str(current['tolerance']), title=COMMAND_TITLE,
        prompt='Bearing-on-top tolerance (in):')
    if tolerance is not None:
        value = parse_tolerance(tolerance)
        if value is None:
            forms.alert('Tolerance must be a positive number; kept {}.'.format(
                current['tolerance']), title=COMMAND_TITLE)
        else:
            config.tolerance_in = value
    hanger = forms.ask_for_string(
        default=current['hanger'], title=COMMAND_TITLE,
        prompt='Hanger family name (matched case-insensitively):')
    if hanger:
        config.hanger_family = hanger.strip()
    system = forms.CommandSwitchWindow.show(
        list(SYSTEM_OVERRIDES),
        message='Structural system (auto: level name containing ROOF -> roof):')
    if system:
        config.system_override = system
    script.save_config()
    forms.alert('ForteWEB Export settings saved.', title=COMMAND_TITLE)


class _ExportableFilter(ISelectionFilter):
    def AllowElement(self, element):
        return is_exportable(element)

    def AllowReference(self, reference, point):
        return False


def _selected_ids():
    ids = list(revit.uidoc.Selection.GetElementIds())
    if ids:
        return ids
    try:
        refs = revit.uidoc.Selection.PickObjects(
            ObjectType.Element, _ExportableFilter(),
            'Select structural framing members or beam systems, then click Finish')
    except OperationCanceledException:
        script.exit()
    return [ref.ElementId for ref in refs]


def _print_results(path, report, warnings):
    output = script.get_output()
    output.print_md('## ForteWEB Export')
    output.print_md('Written: `{}`'.format(path))
    output.print_table(table_data=report[1:], columns=report[0],
                       title='{} member(s) exported'.format(len(report) - 1))
    if warnings:
        output.print_md('### Warnings')
        for warning in warnings:
            output.print_md('- ' + warning)


def main():
    if EXEC_PARAMS.config_mode:
        _edit_settings()
        return

    settings = _settings()
    template = settings['template']
    if not template or not os.path.isfile(template):
        template = _pick_template(template)
        if not template:
            return

    ids = _selected_ids()
    default_name = os.path.splitext(revit.doc.Title)[0] or 'ForteWEB Export'
    out_path = forms.save_file(file_ext='4wf', default_name=default_name,
                               title='Save ForteWEB .4wf')
    if not out_path:
        return

    try:
        path, report, warnings = run_export(
            revit.doc, ids, template, out_path,
            settings['system'], settings['tolerance'], settings['hanger'])
    except ExportError as error:
        _stop(str(error))
    except ValueError as error:
        _stop('The template could not be used: {}'.format(error))
    _print_results(path, report, warnings)


main()
