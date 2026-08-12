"""Explicit preview authorization for the gallery fixture."""
from __future__ import unicode_literals

import os


def can_preview(entry, fixture_path):
    """Allow only the reviewed, safe fixture that the catalog marked safe."""
    if not entry or not entry.get('is_previewable') or not fixture_path:
        return False
    return os.path.realpath(entry.get('path', '')) == os.path.realpath(fixture_path)
