"""Tool-facing selectors backed by shared dialogs and read-only collectors.

Documents are explicit. Revit imports occur only at the host boundary; the
returned values remain the caller's original Revit objects, never UI rows.
"""
from __future__ import unicode_literals

from GUI import dialogs
from GUI.dialogs import collectors
from GUI.dialogs.models import SelectionItem
from GUI.window_chrome import access_text


def _owner(value):
    if value is not None:
        return value
    # Match pyRevit WPFWindow.setup_owner without querying the active model.
    from pyrevit.api import AdWindows
    return AdWindows.ComponentManager.ApplicationWindow


def _alert(message, title, **options):
    from GUI import tool_dialogs
    return tool_dialogs.alert(message, title=title, **options)


def _select(title, rows, button_name, multiple, prompt, version, owner,
            groups=None, all_label='All Items'):
    window = dialogs.create_selection(title, rows, multiple=multiple,
                                      groups=[] if groups is None else groups,
                                      prompt=prompt, required=False,
                                      all_label=all_label, version=version,
                                      owner=_owner(owner))
    window.accept_button.Content = access_text(button_name)
    window.ShowDialog()
    if window.result.is_cancelled:
        return None
    values = list(window.state.selected_values)
    return values if multiple else (values[0] if values else None)


def select_revisions(document, title, button_name='Select', multiple=True,
                     filterfunc=None, version=None, owner=None):
    """Keep revisions unchecked and let the caller decide issued filtering."""
    rows = collectors.revision_items(document, filterfunc)
    return _select(title, rows, button_name, multiple, 'Select Revisions',
                   version, owner)


def select_sheets(document, title, button_name='Select', multiple=True,
                  filterfunc=None, include_placeholder=True,
                  version=None, owner=None):
    """Select sheets, including placeholders by the legacy tool default."""
    rows, groups = collectors.sheet_items(document, include_placeholder, filterfunc)
    # Existing revision tools use pyRevit's sheet-number ordering, not the
    # opt-in collector's natural-number ordering.
    rows.sort(key=lambda row: row.Value.SheetNumber)
    return _select(title, rows, button_name, multiple, 'Select Sheets',
                   version, owner, groups, 'All Sheets')


def select_open_documents(application, active_document, title,
                          button_name='OK', multiple=True, filterfunc=None,
                          version=None, owner=None):
    """Exclude current/linked docs; retain family docs and session identities."""
    rows = collectors.document_items(application, active_document,
                                     include_active=False, include_families=True)
    if not rows:
        _alert('Only one active document is found. At least two documents must '
               'be open. Operation cancelled.', title,
               version=version, owner=_owner(owner))
        return None
    if filterfunc is not None:
        rows = [row for row in rows if filterfunc(row.Value)]
    return _select(title, rows, button_name, multiple, 'Select Documents',
                   version, owner)


def _current_views():
    from pyrevit import revit, DB
    return list(revit.get_selection().include(DB.View).elements)


def _all_views(document):
    from pyrevit import revit
    return list(revit.query.get_all_views(doc=document))


def _view_name(view):
    from pyrevit import revit
    return '{} ({})'.format(revit.query.get_name(view), view.ViewType)


def select_views(document, title, button_name='Select', multiple=True,
                 filterfunc=None, use_selection=False, selected_views=None,
                 version=None, owner=None):
    """Keep pyRevit's optional current-selection confirmation and view query.

    ``selected_views`` may supply the caller's already typed View selection.
    Omitting it queries the active UI selection only when use_selection=True.
    Declining or closing confirmation opens the full filtered selector.
    """
    if use_selection:
        selected = list(_current_views() if selected_views is None else selected_views)
        if filterfunc is not None:
            selected = [view for view in selected if filterfunc(view)]
        if selected:
            report = '{} views'.format(len(selected))
            message = ('You currently have {} selected. Do you want to proceed '
                       'with currently selected item(s)?').format(report)
            if not multiple:
                message = ('You currently have {} selected and only one is required. '
                           'Do you want to use the first selected item?').format(report)
            if _alert(message, title, yes=True, no=True,
                      version=version, owner=_owner(owner)):
                return selected if multiple else selected[0]
    views = _all_views(document)
    if filterfunc is not None:
        views = [view for view in views if filterfunc(view)]
    pairs = sorted([(_view_name(view), view) for view in views], key=lambda pair: pair[0])
    rows = [SelectionItem(view.UniqueId, label, view) for label, view in pairs]
    return _select(title, rows, button_name, multiple, 'Select Views',
                   version, owner)


def select_named_item(options, title, prompt='Select Item', button_name='Select',
                      version=None, owner=None):
    """Single-item recovery path for existing dictionary-selector callers.

    No first-row default is added: the retired fallback's list opened without
    an initial selection. Original values, including None, are returned intact.
    """
    rows = [SelectionItem(label, label, options[label]) for label in sorted(options)]
    return _select(title, rows, button_name, False, prompt.rstrip().rstrip(':'),
                   version, owner)