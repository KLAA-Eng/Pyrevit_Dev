# -*- coding: utf-8 -*-
"""Remember the view settings changed to ghost topography, so Clear can restore them.

The state is a dict saved as JSON on this computer:

    {doc_key: {view_unique_id: {category_name: {'transparency': int,
                                                'halftone': bool,
                                                'hidden': bool}}}}

Only the first original per view and category is kept, so ghosting the same
view twice still restores the user's own settings.
"""

import json
import os


GHOST_TRANSPARENCY = 70
STRIP_TRANSPARENCY = 50
STRIP_WIDTH_FEET = 4.0
STRIP_APP_ID = 'KLA'
STRIP_DATA_ID = 'WallGradeCheck'


def default_state_path(environ=None):
    environ = os.environ if environ is None else environ
    root = environ.get('LOCALAPPDATA') or environ.get('TEMP') or '.'
    return os.path.join(root, 'KLA Tools', 'Wall Grade Check', 'ghosted_views.json')


def doc_key(path_name, title):
    """Return a key for a model: its file path, else its title for unsaved models."""
    return (path_name or '').strip().lower() or u'untitled:' + (title or '')


def remember(state, key, view_id, category, transparency, halftone, hidden):
    """Record a category's original view settings unless already recorded."""
    views = state.setdefault(key, {})
    categories = views.setdefault(view_id, {})
    if category not in categories:
        categories[category] = {
            'transparency': int(transparency),
            'halftone': bool(halftone),
            'hidden': bool(hidden),
        }
    return state


def take(state, key):
    """Remove and return the recorded views for a model ({} when none)."""
    return state.pop(key, None) or {}


def load(path):
    try:
        with open(path, 'r') as state_file:
            state = json.load(state_file)
    except (IOError, OSError, ValueError):
        return {}
    return state if isinstance(state, dict) else {}


def save(path, state):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    temp_path = path + '.tmp'
    with open(temp_path, 'w') as state_file:
        json.dump(state, state_file, indent=1, sort_keys=True)
    if os.path.exists(path):
        os.remove(path)
    os.rename(temp_path, path)


def strip_quads(edge, width, normals):
    """Return flat quads (4 points each) from edge points out along normals.

    edge is a list of (x, y, z) at grade on the wall face, with None where
    there is no grade; normals are the matching horizontal exterior unit
    (nx, ny). A quad is made only between two neighboring stations with grade.
    """
    quads = []
    for index in range(len(edge) - 1):
        a, b = edge[index], edge[index + 1]
        if a is None or b is None:
            continue
        na, nb = normals[index], normals[index + 1]
        quads.append([
            a,
            b,
            (b[0] + nb[0] * width, b[1] + nb[1] * width, b[2]),
            (a[0] + na[0] * width, a[1] + na[1] * width, a[2]),
        ])
    return quads
