"""Read-only Revit row collectors for opt-in dialogs.

Importing this module does not load Revit, pyRevit, WPF or an active document.
Call collectors in a valid Revit API context before constructing/showing UI,
never from WPF layout events. Callers retain responsibility for document lifetime.
"""
from __future__ import unicode_literals

from .models import SelectionGroup, SelectionItem

try:
    _text_type = unicode
except NameError:
    _text_type = str


def _text(value):
    return '' if value is None else _text_type(value)


def _db():
    # Revit has already loaded its API assemblies in a supported command context.
    from Autodesk.Revit import DB
    return DB


def _elements(api, document, element_type):
    collector = api.FilteredElementCollector(document)
    try:
        return list(collector.OfClass(element_type).WhereElementIsNotElementType().ToElements())
    finally:
        collector.Dispose()


def _project_document(document):
    if document is None:
        raise ValueError('Pass an explicit source document.')
    return not document.IsFamilyDocument


def sheet_items(document, include_placeholders=False, filterfunc=None):
    """Return (rows, sheet-set groups), with one shared row per sheet.

    The window's implicit All group should be labelled ``All Sheets``. Returned
    groups contain saved sheet sets only, keyed independently of display names.
    A predicate runs once per eligible unique source sheet, before set grouping.
    """
    if not _project_document(document):
        return [], []
    api = _db()
    sheets = []
    seen = set()
    for sheet in _elements(api, document, api.ViewSheet):
        key = _text(sheet.UniqueId)
        if key in seen:
            continue
        seen.add(key)
        if not include_placeholders and sheet.IsPlaceholder:
            continue
        if filterfunc is None or filterfunc(sheet):
            sheets.append(sheet)
    sheets.sort(key=lambda item: (_text(item.SheetNumber), _text(item.Name)))
    memberships = dict((_text(sheet.UniqueId), []) for sheet in sheets)
    groups = []
    seen_sets = set()
    sheet_sets = _elements(api, document, api.ViewSheetSet)
    sheet_sets.sort(key=lambda item: _text(item.Name).lower())
    for sheet_set in sheet_sets:
        group_key = 'sheet-set:' + _text(sheet_set.UniqueId)
        if group_key in seen_sets:
            continue
        seen_sets.add(group_key)
        label = _text(sheet_set.Name)
        if label.lower() == 'all sheets':
            label = 'Sheet Set: ' + label
        groups.append(SelectionGroup(group_key, label))
        for view in sheet_set.Views:
            key = _text(view.UniqueId)
            if key in memberships and group_key not in memberships[key]:
                memberships[key].append(group_key)
    rows = []
    for sheet in sheets:
        key = _text(sheet.UniqueId)
        label = '{} - {}'.format(sheet.SheetNumber, sheet.Name)
        if sheet.IsPlaceholder:
            label += ' (Placeholder)'
        rows.append(SelectionItem(key, label, sheet, groups=memberships[key]))
    return rows, groups


def revision_items(document, filterfunc=None):
    """Return revisions in sequence order, with dates and issued status.

    Per-sheet numbering has no project-wide RevisionNumber; show SequenceNumber
    there instead. Issued revisions remain selectable unless the caller filters.
    """
    if not _project_document(document):
        return []
    api = _db()
    revisions = [document.GetElement(key) for key in api.Revision.GetAllRevisionIds(document)]
    revisions = [revision for revision in revisions if filterfunc is None or filterfunc(revision)]
    revisions.sort(key=lambda item: item.SequenceNumber)
    settings = api.RevisionSettings.GetRevisionSettings(document)
    per_project = settings.RevisionNumbering == api.RevisionNumbering.PerProject
    rows = []
    for revision in revisions:
        number = _text(revision.RevisionNumber) if per_project else _text(revision.SequenceNumber)
        label = '{} - {}'.format(number or '(No number)', _text(revision.Description))
        status = 'Issued' if revision.Issued else 'Unissued'
        description = '{} | {}'.format(_text(revision.RevisionDate), status)
        rows.append(SelectionItem(_text(revision.UniqueId), label, revision, description))
    return rows


def document_items(application, active_document=None, include_active=False,
                   include_families=True, filterfunc=None):
    """Return original open documents, excluding links and normally the active one.

    Pass the Revit Application and explicit active_document. When there is no active
    document, use include_active=True; no implicit active-document query occurs.
    Document objects themselves are stable session keys, so duplicate titles or
    hash-code collisions cannot collapse distinct documents into one row.
    """
    if not include_active and active_document is None:
        raise ValueError('Pass active_document, or set include_active=True when no active document exists.')
    rows = []
    seen = set()
    for document in application.Documents:
        if document.IsLinked or (not include_active and document == active_document):
            continue
        if not include_families and document.IsFamilyDocument:
            continue
        if document in seen:
            continue
        seen.add(document)
        if filterfunc is not None and not filterfunc(document):
            continue
        kind = 'Family document' if document.IsFamilyDocument else 'Project document'
        path = _text(document.PathName) or 'No file path'
        rows.append(SelectionItem(document, _text(document.Title) or 'Untitled document', document,
                                  '{} | {}'.format(kind, path)))
    return rows
