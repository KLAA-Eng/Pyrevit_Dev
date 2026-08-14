"""Pure planning helpers for Detail and Drafting View folder output."""
from __future__ import unicode_literals

import os


INVALID_FOLDER_CHARACTERS = set('<>:"/\\|?*')
MAX_FOLDER_NAME_LENGTH = 255
RESERVED_WINDOWS_NAMES = set([
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
])


def build_folder_plan(destination, views, existing_paths=None):
    """Return a safe, all-or-nothing folder plan for normalized view records."""
    destination_error = _destination_error(destination)
    if destination_error:
        return _result([], [destination_error])
    if not isinstance(views, (list, tuple)):
        return _result([], ['Views must be a list of view records.'])

    root = os.path.abspath(destination)
    folders, errors = _folder_records(root, views)
    errors.extend(_collision_errors(folders, existing_paths))
    if errors:
        return _result([], errors)
    return _result(sorted(folders, key=lambda item: item['folder_name'].lower()), [])


def create_folder_paths(destination, folders, make_directory=None):
    """Create validated direct-child folders and stop after the first failure."""
    destination_error = _destination_error(destination)
    if destination_error:
        return {'created': [], 'errors': [{'folder_name': '', 'reason': destination_error}]}
    if not isinstance(folders, (list, tuple)):
        return {'created': [], 'errors': [{'folder_name': '', 'reason': 'Folder plan is invalid.'}]}

    root = os.path.abspath(destination)
    create_directory = make_directory or os.mkdir
    created = []
    for folder in folders:
        error = _creation_record_error(root, folder)
        if error:
            return {'created': created, 'errors': [error]}
        try:
            create_directory(folder['path'])
        except (IOError, OSError):
            return {'created': created, 'errors': [{
                'folder_name': folder['folder_name'], 'reason': 'Could not create folder.'}]}
        created.append(folder['folder_name'])
    return {'created': created, 'errors': []}


def _destination_error(destination):
    if not _is_text(destination) or not destination.strip():
        return 'Select an existing destination folder.'
    if not os.path.isabs(destination):
        return 'Destination folder must be an absolute path.'
    return None


def _creation_record_error(root, folder):
    if not isinstance(folder, dict):
        return {'folder_name': '', 'reason': 'Folder plan is invalid.'}
    folder_name = folder.get('folder_name')
    path = folder.get('path')
    if not _is_text(folder_name) or not _is_text(path):
        return {'folder_name': '', 'reason': 'Folder plan is invalid.'}
    if os.path.dirname(os.path.abspath(path)) != root:
        return {'folder_name': folder_name, 'reason': 'Folder plan is outside the destination.'}
    return None


def _folder_records(root, views):
    folders = []
    errors = []
    for index, view in enumerate(views):
        record, error = _folder_record(root, view, index)
        if error:
            errors.append(error)
        else:
            folders.append(record)
    return folders, errors


def _folder_record(root, view, index):
    if not isinstance(view, dict):
        return None, 'View {} is not a valid record.'.format(index + 1)
    view_id = view.get('view_id', index + 1)
    view_name = _safe_folder_part(view.get('view_name'))
    if not view_name:
        return None, 'View {} has no usable name.'.format(view_id)
    detail_number = _safe_folder_part(view.get('detail_number')) or 'Unplaced'
    folder_name = '{} - {}'.format(detail_number, view_name)
    if len(folder_name) > MAX_FOLDER_NAME_LENGTH:
        return None, 'View {} folder name exceeds {} characters.'.format(
            view_id, MAX_FOLDER_NAME_LENGTH)
    path = os.path.abspath(os.path.join(root, folder_name))
    if os.path.dirname(path) != root:
        return None, 'View {} resolves outside the destination folder.'.format(view_id)
    return {'view_id': view_id, 'folder_name': folder_name, 'path': path}, None


def _safe_folder_part(value):
    if not _is_text(value):
        return ''
    characters = []
    for character in value.strip():
        if character in INVALID_FOLDER_CHARACTERS or ord(character) < 32:
            characters.append('_')
        else:
            characters.append(character)
    name = ''.join(characters).lstrip('.').rstrip('. ')
    if not name:
        return ''
    if name.split('.')[0].upper() in RESERVED_WINDOWS_NAMES:
        return '_' + name
    return name


def _collision_errors(folders, existing_paths):
    normalized_paths = {}
    errors = []
    for folder in folders:
        key = _normalized_path(folder['path'])
        if key in normalized_paths:
            errors.append('Multiple views resolve to the folder "{}".'.format(
                normalized_paths[key]['folder_name']))
        else:
            normalized_paths[key] = folder
    for path in existing_paths or []:
        key = _normalized_path(path)
        if key in normalized_paths:
            errors.append('Destination already contains "{}".'.format(
                normalized_paths[key]['folder_name']))
    return errors


def _normalized_path(path):
    return os.path.normcase(os.path.abspath(path)).lower()


def _is_text(value):
    try:
        return isinstance(value, basestring)
    except NameError:
        return isinstance(value, str)


def _result(folders, errors):
    return {'folders': folders, 'errors': errors}
