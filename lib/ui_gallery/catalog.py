"""Filesystem-bounded catalog of XAML sources."""
from __future__ import unicode_literals

import os

from .classification import classify_xaml


EXCLUDED_DIRECTORIES = set(['.agents', '.codex', '.git', '.local.manaai'])


def catalog_xaml_sources(extension_root):
    """Return sorted metadata for XAML files physically contained by the root."""
    if not extension_root or not os.path.isdir(extension_root):
        return []
    normalized_input = os.path.abspath(extension_root)
    root = os.path.realpath(normalized_input)
    if normalized_input != os.path.normpath(normalized_input):
        return []

    entries = []
    for directory, subdirectories, filenames in os.walk(root, followlinks=False):
        subdirectories[:] = [
            item for item in subdirectories
            if item not in EXCLUDED_DIRECTORIES and not os.path.islink(os.path.join(directory, item))
        ]
        for filename in filenames:
            if not filename.lower().endswith('.xaml'):
                continue
            source_path = os.path.realpath(os.path.join(directory, filename))
            if not _is_within_root(source_path, root):
                continue
            metadata = classify_xaml(source_path)
            metadata['path'] = source_path
            metadata['relative_path'] = os.path.relpath(source_path, root).replace(os.sep, '/')
            entries.append(metadata)
    return sorted(entries, key=lambda item: item['relative_path'].lower())


def _is_within_root(path, root):
    normalized_path = os.path.normcase(os.path.abspath(path))
    normalized_root = os.path.normcase(os.path.abspath(root))
    return normalized_path == normalized_root or normalized_path.startswith(
        normalized_root + os.sep
    )
