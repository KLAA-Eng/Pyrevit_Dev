# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Model Checker"
__version__ = "v0.0"

#  ___ __  __ ____   ___  ____ _____ ____
# |_ _|  \/  |  _ \ / _ \|  _ \_   _/ ___|
#  | || |\/| | |_) | (_) | |_) || | \___ \
# ==================================================================
# Imports
# ------------------------------------------------------------------
import datetime
import json
import math
import os
import sys
import traceback
from collections import Counter

from pyrevit import DB, forms, revit, script
from System import AppDomain
from System.Collections.Generic import List

from steel_model_review import host
from steel_model_review.live import ReviewSession
from steel_model_review.engine import CHECKS, DEFAULTS, Cancelled, assemble_report, evaluate
from steel_model_review.records import RULESET_VERSION, SCHEMA_VERSION
from steel_model_review.reporting import CHECK_LABELS
from steel_model_review.session import carry_exceptions, signature


BUNDLE = os.path.dirname(__file__)
RUN_STAGE = 'Starting Model Checker'


#  _____ _   _ _   _  ____ _____ ___ ___  _   _ ____
# |  ___| | | | \ | |/ ___|_   _|_ _/ _ \| \ | / ___|
# | |_  | |_| |  \| | |     | |  | | (_) |  \| \___ \
# ==================================================================
# Workflow helpers
# ------------------------------------------------------------------
def _stage(message):
    """Record the current workflow boundary for actionable failure reports."""
    global RUN_STAGE
    RUN_STAGE = message


def _report_failure(details):
    """Show diagnostics directly, independent of the runtime logging service.

    Args:
        details: Captured exception traceback, preserved before further calls.

    Returns:
        None. The task dialog always receives the complete traceback, even
        when the pyRevit logger or output renderer cannot display it.
    """
    context = 'Stage: {0}\nPython: {1}'.format(RUN_STAGE, sys.version)
    report = context + '\n\n' + details
    try:
        script.get_logger().error(report)
    except Exception:
        pass
    try:
        output = script.get_output()
        output.print_md('## Model Checker could not complete')
        output.print_code(report)
    except Exception:
        print(report)
    summary = details.strip().splitlines()[-1] if details.strip() else 'Unknown error'
    forms.alert('Model Checker stopped during: {0}\n\n{1}\n\n'
                'Review-view graphics may have changed. Expand the details below for the '
                'complete traceback.'.format(RUN_STAGE, summary),
                expanded=report, title=__title__)


def _pick(mapping, title):
    """Return a selected mapping value or None on dialog cancellation."""
    selected = forms.SelectFromList.show(sorted(mapping), title=title,
                                         button_name='Continue', multiselect=False)
    return mapping.get(selected) if selected else None


def _distance_prompt(label, default, epsilon=False, units='inches'):
    """Read a finite positive inch setting, retrying invalid input."""
    while True:
        value = forms.ask_for_string(default=str(default), prompt=label,
                                     title=__title__)
        if value is None:
            return None
        try:
            value = float(value)
            if math.isnan(value) or math.isinf(value) or value <= 0:
                raise ValueError()
            if epsilon and value >= 0.0001:
                raise ValueError()
            if units == 'degrees' and value >= 90:
                raise ValueError()
            return value
        except ValueError:
            forms.alert('Enter a positive decimal in {0}.{1}'.format(units,
                ' Numerical zero must be smaller than 0.0001 in.' if epsilon
                else ' Angle must be smaller than 90 degrees.' if units == 'degrees'
                else ''), title=__title__)


def _configure(document):
    """Confirm whole-model phase, option, check, and tolerance settings.

    Args:
        document: Active project document.

    Returns:
        Settings, chosen phase ElementId, option IDs, and scope labels;
        or None when any required choice is cancelled.
    """
    _stage('Choosing the export phase')
    phase = _pick(dict(('{0} [{1}]'.format(host.name(p), host.id_value(p.Id)), p)
                       for p in document.Phases), 'Model Checker - Export phase')
    if phase is None:
        return None
    _stage('Choosing design options')
    option_groups = {}
    for option in DB.FilteredElementCollector(document).OfClass(DB.DesignOption):
        set_id = option.get_Parameter(DB.BuiltInParameter.OPTION_SET_ID).AsElementId()
        option_groups.setdefault(host.id_value(set_id), []).append(option)
    options, option_labels = [], []
    for set_id, group in sorted(option_groups.items()):
        choices = {'Main model only for this set': -1}
        choices.update(('{0} [{1}]'.format(host.name(o), host.id_value(o.Id)),
                        host.id_value(o.Id)) for o in group)
        label = forms.SelectFromList.show(sorted(choices), multiselect=False,
                                         title='Export option set {0}'.format(set_id),
                                         button_name='Continue')
        if not label:
            return None
        if choices[label] >= 0:
            options.append(choices[label])
        option_labels.append('{0}: {1}'.format(set_id, label))
    _stage('Choosing model checks')
    selected = forms.SelectFromList.show(
        [forms.TemplateListItem(CHECK_LABELS[c], checked=True) for c in CHECKS],
        multiselect=True,
        title='Whole-model checks - select checks to run', button_name='Continue')
    if not selected:
        return None
    settings = dict(DEFAULTS)
    settings['checks'] = [c for c in CHECKS if CHECK_LABELS[c] in selected]
    if 'SMR-03' in settings['checks']:
        _stage('Choosing the column grid mode')
        mode = forms.CommandSwitchWindow.show(
            ['Nearest intersection', 'Explicit grid pairs', 'Disabled'],
            message='Column grid review (intentional offsets can be accepted)')
        if not mode:
            return None
        settings['grid_mode'] = mode
        if mode == 'Disabled':
            settings['checks'].remove('SMR-03')
    if not settings['checks']:
        forms.alert('Enable at least one check.', title=__title__)
        return None
    for key, label, epsilon in (
            ('search', 'Support search distance in inches (proposed default 12).', False),
            ('epsilon', 'Numerical zero in inches (proposed default 0.000001).', True),
            ('near', 'Near-duplicate range in inches (proposed default 0.0625).', False),
            ('angle_degrees', 'Plan angle tolerance in degrees (proposed default 0.01).', False)):
        _stage('Reading the {0} tolerance'.format(key))
        value = _distance_prompt(label, settings[key], epsilon,
                                 'degrees' if key == 'angle_degrees' else 'inches')
        if value is None:
            return None
        settings[key] = value
    labels = {'phase': host.name(phase), 'options': option_labels or ['Main model']}
    _stage('Confirming review settings')
    confirmed = forms.alert(
        'Review the whole host model, across all views and levels.\n\n'
        'Phase: {0}\nOptions: {1}\nChecks: {2}\n'
        'Search: {3:g} in; zero: {4:g} in; near duplicates: {5:g} in.\n\n'
        'Nonzero offsets below 1/16 in: CRITICAL.\n'
        'Offsets at or above 1/16 in: WARNING.\n'
        'Beam roles: girder, splice, Corner/End. Column axes and faces are separate.\n'
        'Bottom-face work planes are informational; crossing errors have no severity tier yet.\n'
        'Plan angle tolerance: {6:g} degrees (proposed default).\n'
        'Links are excluded; unresolved geometry is reported.\n'
        'Creates/updates a dedicated 3D review view and its color overrides.\n'
        'Member geometry is reviewed without edits.'
        .format(labels['phase'], '; '.join(labels['options']),
                ', '.join(settings['checks']), settings['search'],
                settings['epsilon'], settings['near'], settings['angle_degrees']),
        title=__title__, yes=True, no=True)
    return (settings, phase.Id, options, labels) if confirmed else None


def _elements(document):
    """Collect document-wide categories used by review and scope fingerprints."""
    categories = ((DB.BuiltInCategory.OST_StructuralFraming, 'beam'),
                  (DB.BuiltInCategory.OST_StructuralColumns, 'column'),
                  (DB.BuiltInCategory.OST_Walls, 'wall'),
                  (DB.BuiltInCategory.OST_Grids, 'grid'))
    return [(element, kind) for category, kind in categories
            for element in host.collect(document, category)]


def _material_overrides(elements, phase, options):
    """Ask for explicit reviewed classification of unknown family/wall types."""
    unknown = {'steel': {}, 'concrete': {}}
    for element, kind in elements:
        if kind == 'grid':
            continue
        try:
            if (host.in_scope(element, phase, options) and
                    host.classification(element, kind) == 'unknown'):
                type_id = host.id_value(element.GetTypeId())
                expected = 'concrete' if kind == 'wall' else 'steel'
                unknown[expected]['{0} [{1}]'.format(
                    host.name(element.Document.GetElement(element.GetTypeId())),
                    type_id)] = type_id
        except Exception:
            # Extraction records the actual classification failure per element.
            continue
    overrides = {}
    for material, mapping in sorted(unknown.items()):
        if not mapping:
            continue
        selected = forms.SelectFromList.show(
            sorted(mapping), multiselect=True,
            title='Classify unknown types as {0}; unselected stay unsupported'
                  .format(material), button_name='Apply reviewed classifications')
        for label in selected or []:
            overrides[mapping[label]] = material
    return overrides


def _versions(document):
    """Fingerprint relevant members, types, materials, grids, phases and options."""
    entries = [(e.UniqueId, str(e.VersionGuid)) for e, _kind in _elements(document)]
    for cls in (DB.FamilySymbol, DB.WallType, DB.Material, DB.PropertySetElement,
                DB.Level, DB.Phase, DB.DesignOption, DB.Floor, DB.RoofBase,
                DB.SketchPlane, DB.ReferencePlane, DB.BeamSystem):
        entries.extend((e.UniqueId, str(e.VersionGuid))
                       for e in DB.FilteredElementCollector(document).OfClass(cls))
    return signature(sorted(entries))


def _stamp(versions, settings, phase, options, expected, overrides):
    """Fingerprint all comparison settings and model-scope version evidence."""
    return signature([SCHEMA_VERSION, RULESET_VERSION, versions, settings,
                      host.id_value(phase), options, expected, sorted(overrides.items())])


def _summary(coverage, settings, labels, rows, links):
    """Describe scope and per-check coverage without certifying export readiness."""
    counts = Counter(item[2] for item in coverage)
    text = ('Phase {0}; {1}. Eligible {2}; excluded {3}; unsupported {4}; '
            'failed {5}; excluded link instances {6}.\nSearch {7:g} in; zero '
            '{8:g} in; near duplicates {9:g} in; grid mode {10}; plan angle {11:g} degrees.'
            .format(labels['phase'], '; '.join(labels['options']),
                    counts['Eligible'], counts['Excluded'], counts['Unsupported'],
                    counts['Failed'], links, settings['search'],
                    settings['epsilon'], settings['near'], settings['grid_mode'],
                    settings['angle_degrees']))
    for check in CHECKS:
        outcomes = [r for r in rows if r['check'] == check]
        done = len(set(r['uid'] for r in outcomes
                       if r['severity'] != 'Not evaluated'))
        if check in ('SMR-04', 'SMR-06'):
            done = len(set([r['uid'] for r in outcomes
                            if r['severity'] != 'Not evaluated'] +
                           [item['uid'] for r in outcomes for item in r['related']
                            if r['severity'] != 'Not evaluated']))
        skipped = len(set(r['uid'] for r in outcomes
                          if r['severity'] == 'Not evaluated'))
        text += '\n{0}: {1}'.format(
            check, 'Not run' if check not in settings['checks'] else
            '{0} members with evaluated outcomes; {1} members with unresolved '
            'outcomes (may overlap).'.format(done, skipped))
    return text


def _run(document, elements, settings, phase, options, labels, overrides,
         expected, previous, versions):
    """Run extraction and rules, retaining explicit cancellation state."""
    coverage, rows, records, grids = [], [], [], []
    relationships = []
    state = 'Complete'
    with forms.ProgressBar(title='Model Checker: {value}/{max_value}',
                           cancellable=True, step=10) as bar:
        def progress(value, total):
            bar.update_progress(value, max(total, 1))
            if bar.cancelled:
                raise Cancelled()
        try:
            _stage('Extracting model geometry')
            records, grids, coverage, rows = host.extract_model(
                document, elements, phase, options, overrides,
                settings['checks'], progress)
            _stage('Comparing model geometry')
            for member in records:
                member['source_model'] = document.ProjectInformation.UniqueId
                member['scope'] = {'phase_id': host.id_value(phase), 'option_ids': options}
            rows.extend(evaluate(records, grids, settings, expected, progress, relationships))
        except Cancelled:
            state = 'Cancelled - incomplete; partial extraction may be omitted'
    stamp = _stamp(versions, settings, phase, options, expected, overrides)
    report = assemble_report(records, rows, relationships)
    if state == 'Complete':
        carry_exceptions(rows, previous, stamp)
    links = len(host.collect(document, DB.BuiltInCategory.OST_RvtLinks))
    report.update({'model': document.Title, 'version': __version__,
            'time': datetime.datetime.now().isoformat(), 'state': state,
            'settings': settings, 'labels': labels, 'stamp': stamp, 'phase_id': host.id_value(phase),
            'versions': versions, 'coverage': coverage,
            'grids': grids, 'expected': expected,
            'summary': _summary(coverage, settings, labels, rows, links)})
    return report


def _navigate(document, row):
    """Select and zoom existing finding elements inside a Revit API callback."""
    identities = [row['uid']] + [r['uid'] for r in row['related']]
    elements = [document.GetElement(uid) for uid in identities]
    missing = sum(1 for e in elements if e is None)
    ids = List[DB.ElementId]([e.Id for e in elements if e is not None])
    if ids.Count:
        revit.uidoc.Selection.SetElementIds(ids)
        try:
            revit.uidoc.ShowElements(ids)
        except Exception as error:
            forms.alert('Selected elements, but Zoom could not complete:\n{0}'
                        .format(error), title=__title__)
    if missing:
        forms.alert('{0} referenced elements no longer exist. Rerun the review.'
                    .format(missing), title=__title__)


def _assign_grids(row, grids, expected):
    """Assign a reviewer-selected grid pair for one column finding."""
    if row['check'] != 'SMR-03':
        forms.alert('Select a column grid finding first.', title=__title__)
        return
    mapping = dict(('{0} [{1}]'.format(g['name'], g['id']), g['uid']) for g in grids)
    selected = forms.SelectFromList.show(sorted(mapping), multiselect=True,
                                         title='Choose exactly two expected grids')
    if selected and len(selected) == 2:
        expected[row['uid']] = [mapping[s] for s in selected]
    elif selected:
        forms.alert('Choose exactly two grids.', title=__title__)


#  __  __    _    ___ _   _
# |  \/  |  / \  |_ _| \ | |
# | |\/| | / _ \  | ||  \| |
# ==================================================================
# Main workflow
# ------------------------------------------------------------------
def main():
    """Review steel geometry and open its modeless report with a colored 3D view."""
    _stage('Reading the active project')
    document = revit.doc
    if document is None or document.IsFamilyDocument:
        forms.alert('Open a Revit project to run Model Checker.', title=__title__)
        return
    if int(document.Application.VersionNumber) < 2024:
        forms.alert('Model Checker targets Revit 2024 and later.', title=__title__)
        return
    registry_key = 'KLA_MODEL_CHECKER_WINDOW_' + str(document.GetHashCode())
    existing = AppDomain.CurrentDomain.GetData(registry_key)
    if existing is not None and not existing.closed and not existing.closing:
        existing.window.Activate()
        return
    context = _configure(document)
    if context is None:
        return
    settings, phase, options, labels = context
    _stage('Collecting whole-model elements')
    elements = _elements(document)
    _stage('Reviewing material classifications')
    overrides = _material_overrides(elements, phase, options)
    _stage('Loading the previous session report')
    model_identity = [document.PathName, document.ProjectInformation.UniqueId]
    cache_key = 'KLA_MODEL_CHECKER_V{0}_R{1}_'.format(
        SCHEMA_VERSION, RULESET_VERSION) + signature(model_identity)
    cached = AppDomain.CurrentDomain.GetData(cache_key)
    previous = json.loads(cached) if cached else None
    expected = dict(previous.get('expected', {})) if previous else {}
    _stage('Fingerprinting model versions')
    versions = _versions(document)
    current = None
    if previous:
        action = forms.CommandSwitchWindow.show(
            ['Run new review', 'Open previous report', 'Cancel'],
            message='A previous complete report is available for this model.')
        if action is None or action == 'Cancel':
            return
        if action == 'Open previous report':
            current = previous
    if current is None:
        current = _run(document, elements, settings, phase, options, labels,
                       overrides, expected, previous, versions)
    if current['state'] != 'Complete':
        forms.alert('Review cancelled. This run is incomplete. The previous '
                    'complete report is preserved; no review view will be created.', title=__title__)

    def fresh(snapshot):
        return snapshot['stamp'] == _stamp(
            _versions(document), settings, phase, options, expected, overrides)

    def run_review(prior):
        _stage('Rerunning the model checks')
        return _run(document, _elements(document), settings, phase, options, labels,
                    overrides, expected, prior, _versions(document))

    def save(snapshot):
        if snapshot['state'] == 'Complete':
            AppDomain.CurrentDomain.SetData(cache_key, json.dumps(snapshot))

    def grids(row, snapshot):
        _assign_grids(row, snapshot['grids'], expected)
        snapshot['expected'] = dict(expected)

    def coverage(snapshot):
        output = script.get_output()
        output.print_md('## Model Checker coverage - {0}'.format(snapshot['state']))
        output.print_table(table_data=snapshot['coverage'],
                           columns=['Element ID', 'Kind', 'State', 'Reason'])
        forms.alert(snapshot['summary'], title='Model Checker coverage')

    def failure():
        _stage('Updating the modeless report or review view')
        _report_failure(traceback.format_exc())

    _stage('Opening the modeless report and 3D review view')
    callbacks = {'fresh': fresh, 'run': run_review, 'save': save,
                 'navigate': lambda row: _navigate(document, row),
                 'grids': grids, 'coverage': coverage, 'failure': failure}
    session = ReviewSession(revit.uidoc.Application, document,
                            os.path.join(BUNDLE, 'review.xaml'), current,
                            callbacks, registry_key)
    AppDomain.CurrentDomain.SetData(registry_key, session)
    save(current)
    session.show()


def run_command():
    """Execute the tool and surface failures without relying on logger output."""
    try:
        main()
    except Exception:
        _report_failure(traceback.format_exc())


if __name__ == '__main__':
    run_command()
