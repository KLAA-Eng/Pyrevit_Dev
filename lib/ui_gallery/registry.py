"""Standalone Gallery inventory and presentation metadata; never loads a UI."""
from __future__ import unicode_literals

import os

from .catalog import catalog_xaml_sources
from .launchers import gallery_launchers


ORIGINS = ('Repository custom', 'pyRevit built-in', 'Revit/Windows native')
STATES = ('Normal', 'Empty', 'Error', 'Disabled', 'Long content')
_OVERLAYS = set(('pyrevit-warning-bar', 'pyrevit-show-balloon', 'pyrevit-progress-bar'))
_NATIVE = set(('pyrevit-alert', 'pyrevit-ask-for-color', 'pyrevit-pick-file',
               'pyrevit-pick-folder', 'native-revit-task-dialog', 'native-open-file'))
_LISTS = set(('pyrevit-select-list', 'pyrevit-select-list-single',
              'pyrevit-select-open-docs', 'pyrevit-select-parameters',
              'pyrevit-select-revisions', 'pyrevit-select-sheets', 'pyrevit-select-views'))
_API_KEYS = {
    'pyrevit-alert': 'pyrevit:alert', 'pyrevit-ask-for-color': 'pyrevit:ask_for_color',
    'pyrevit-ask-for-string': 'pyrevit:ask_for_string',
    'pyrevit-command-switch': 'pyrevit:CommandSwitchWindow',
    'pyrevit-pick-file': 'pyrevit:pick_file', 'pyrevit-pick-folder': 'pyrevit:pick_folder',
    'pyrevit-select-list': 'pyrevit:SelectFromList',
    'pyrevit-select-list-single': 'pyrevit:SelectFromList',
    'pyrevit-select-open-docs': 'pyrevit:select_open_docs',
    'pyrevit-select-parameters': 'pyrevit:select_parameters',
    'pyrevit-select-revisions': 'pyrevit:select_revisions',
    'pyrevit-select-sheets': 'pyrevit:select_sheets',
    'pyrevit-select-views': 'pyrevit:select_views',
    'native-revit-task-dialog': 'native:TaskDialog',
    'native-open-file': 'native:OpenFileDialog',
}


def canonical_path(path):
    path = path.replace('\\', '/')
    prefix = 'KL&A Tools_dev.tab/'
    return 'KL&A Tools.tab/' + path[len(prefix):] if path.startswith(prefix) else path


def resolve_source(extension_root, relative_path):
    """Resolve a contained source, accepting either development/release tab alias."""
    if not relative_path or ':' in relative_path or relative_path.startswith(('/', '\\')):
        return None
    root = os.path.realpath(extension_root)
    path = canonical_path(relative_path)
    candidates = [path]
    if path.startswith('KL&A Tools.tab/'):
        candidates.insert(0, 'KL&A Tools_dev.tab/' + path[len('KL&A Tools.tab/'):])
    for candidate in candidates:
        resolved = os.path.realpath(os.path.join(root, *candidate.split('/')))
        if (os.path.normcase(resolved).startswith(os.path.normcase(root + os.sep))
                and os.path.isfile(resolved)):
            return resolved
    return None


def _extra_rows():
    return [
        dict(id='native-revit-task-dialog', title='Revit task dialog / command links',
             category='Native host', relative_path='', called_by='Autodesk.Revit.UI.TaskDialog',
             description='Actual Revit task dialog with fictional command choices.', can_launch=True),
        dict(id='native-open-file', title='Windows file picker (compiled tools)',
             category='Native host', relative_path='', called_by='Microsoft.Win32.OpenFileDialog',
             description='Actual native picker. A chosen path is discarded; no file is opened.', can_launch=True),
    ]


def _prepare(row, extension_root):
    row = dict(row)
    identity = row['id']
    compiled = row['category'] == 'Compiled add-in'
    row['origin'] = (ORIGINS[2] if identity in _NATIVE else
                     ORIGINS[1] if identity.startswith('pyrevit-') else ORIGINS[0])
    row['caller_key'] = _API_KEYS.get(identity, canonical_path(row.get('relative_path', '')))
    row['states'] = list(STATES)
    row['preview_status'] = 'Interactive preview'
    row['unavailable_reason'] = ''
    row['callers'] = []
    row['source_path'] = resolve_source(extension_root, row.get('relative_path', ''))
    if identity in _LISTS:
        row['can_launch'] = True
        row['uses_seed_data'] = True
        row['sample_data_label'] = 'Fictional data in pyRevit list window'
        row['description'] += ' Uses the real shared pyRevit list view with fictional items; the model-query wrapper is not executed.'
    elif identity in ('pyrevit-ask-for-color', 'pyrevit-pick-file', 'pyrevit-pick-folder', 'native-open-file'):
        row['states'] = ['Normal']
        row['sample_data_label'] = 'Native picker; selection discarded'
    elif identity in ('pyrevit-ask-for-string', 'pyrevit-command-switch', 'native-revit-task-dialog', 'pyrevit-alert'):
        row['states'] = ['Normal', 'Error', 'Long content']
    elif identity in ('ui-gallery', 'ui-gallery-preview-fixture'):
        row['states'] = ['Normal']
    if compiled:
        row['can_launch'] = False
        row['states'] = []
        row['preview_status'] = 'Deferred'
        row['unavailable_reason'] = 'Working compiled previews are future work; this window remains listed and disabled.'
    elif row.get('relative_path') and not row['source_path']:
        row['can_launch'] = False
        row['states'] = []
        row['preview_status'] = 'Source unavailable'
        row['unavailable_reason'] = 'This source is not present in the current checkout.'
    return row


def gallery_entries(extension_root, caller_index=None):
    """Inventory standalone sources without authorizing arbitrary discovered XAML."""
    if caller_index is None:
        from .callers import discover_callers
        caller_index = discover_callers(extension_root)
    rows = [_prepare(row, extension_root) for row in gallery_launchers() + _extra_rows()
            if row['id'] not in _OVERLAYS]
    known = set(canonical_path(row.get('relative_path', '')) for row in rows)
    for source in catalog_xaml_sources(extension_root):
        path = canonical_path(source['relative_path'])
        if source['root_kind'] != 'Window' or path in known:
            continue
        row = dict(id='source:' + path, category='Discovered window', relative_path=path,
                   title=source['title'] or os.path.basename(path), called_by=path,
                   description='Standalone source found in this checkout.', can_launch=False)
        if path == ('KL&A Tools.tab/05 DevSandbox.panel/Model Review.pulldown/'
                    'Model Checker.pushbutton/review.xaml'):
            row.update(id='kla-model-checker', category='KL&A custom', can_launch=True,
                       description='Model Checker review window with fictional findings and simulated actions.')
        row = _prepare(row, extension_root)
        if not row['can_launch'] and row['source_path']:
            row['preview_status'] = 'Needs preview adapter'
            row['unavailable_reason'] = 'Cataloged automatically. A reviewed sample-data adapter is required before this source can open.'
            row['states'] = []
        rows.append(row)
        known.add(path)
    for row in rows:
        row['callers'] = list(caller_index.get(row['caller_key'], []))
    return sorted(rows, key=lambda item: (item['origin'], item['title'].lower()))


def matching_entries(entries, query='', origin='All origins'):
    """Filter by origin or any visible identity, caller name/path, and metadata."""
    query = (query or '').lower().strip()
    result = []
    for row in entries:
        if origin != 'All origins' and row.get('origin') != origin:
            continue
        values = [row.get(key, '') for key in ('title', 'origin', 'relative_path',
                  'description', 'called_by', 'preview_status', 'unavailable_reason')]
        values.extend(caller.get(key, '') for caller in row.get('callers', [])
                      for key in ('title', 'path'))
        if not query or any(query in value.lower() for value in values):
            result.append(row)
    return result
