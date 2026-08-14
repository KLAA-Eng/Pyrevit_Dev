"""Pure planning helpers for Detail and Drafting View deliverables."""
from __future__ import unicode_literals

import os


ARTIFACT_FILENAMES = {
    'pdf': 'detail.pdf',
    'jpeg': 'detail.jpg',
    'html': 'index.html',
}


def build_deliverable_plan(destination, folders, existing_paths=None):
    """Return validated PDF, JPEG, and HTML work items for folder records."""
    if not _is_existing_absolute_directory(destination):
        return _result([], ['Select an existing destination folder.'])
    if not isinstance(folders, (list, tuple)):
        return _result([], ['Folder plan is invalid.'])

    root = os.path.abspath(destination)
    items = []
    errors = []
    for folder in folders:
        item, error = _item_for_folder(root, folder)
        if error:
            errors.append(error)
        else:
            items.append(item)
    errors.extend(_existing_artifact_errors(items, existing_paths))
    if errors:
        return _result([], errors)
    return _result(sorted(items, key=lambda item: item['folder_name'].lower()), [])


def has_export_failures(export_results):
    """Return whether any PDF, JPEG, or HTML export did not complete."""
    for result in export_results:
        if not isinstance(result, dict):
            return True
        if any(result.get(name) != 'Created' for name in ('pdf', 'jpeg', 'html')):
            return True
    return False


def is_direct_child_path(folder, candidate):
    """Return whether candidate resolves to a direct child of folder."""
    if not _is_text(folder) or not _is_text(candidate):
        return False
    return os.path.dirname(os.path.abspath(candidate)) == os.path.abspath(folder)


def _item_for_folder(root, folder):
    if not isinstance(folder, dict):
        return None, 'Folder plan is invalid.'
    view_id = folder.get('view_id')
    folder_name = folder.get('folder_name')
    folder_path = folder.get('path')
    if view_id is None or not _is_text(folder_name) or not _is_text(folder_path):
        return None, 'Folder plan is invalid.'
    path = os.path.abspath(folder_path)
    if os.path.dirname(path) != root:
        return None, 'View {} folder is outside the destination.'.format(view_id)
    artifacts = {}
    for kind, filename in ARTIFACT_FILENAMES.items():
        artifact_path = os.path.abspath(os.path.join(path, filename))
        if os.path.dirname(artifact_path) != path:
            return None, 'View {} artifact is outside its folder.'.format(view_id)
        artifacts[kind] = artifact_path
    return {
        'view_id': view_id,
        'folder_name': folder_name,
        'path': path,
        'artifacts': artifacts,
    }, None


def _existing_artifact_errors(items, existing_paths):
    expected_paths = {}
    for item in items:
        for artifact_path in item['artifacts'].values():
            expected_paths[_normalized_path(artifact_path)] = item
    errors = []
    for path in existing_paths or []:
        item = expected_paths.get(_normalized_path(path))
        if item:
            errors.append('Destination already contains "{}" for view {}.'.format(
                os.path.basename(path), item['view_id']))
    return errors


def _is_existing_absolute_directory(path):
    return _is_text(path) and os.path.isabs(path) and os.path.isdir(path)


def _normalized_path(path):
    return os.path.normcase(os.path.abspath(path)).lower()


def _is_text(value):
    try:
        return isinstance(value, basestring)
    except NameError:
        return isinstance(value, str)


def _result(items, errors):
    return {'items': items, 'errors': errors}
