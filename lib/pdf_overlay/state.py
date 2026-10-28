# -*- coding: utf-8 -*-
"""Per-overlay cache files and their JSON sidecar state.

Each overlay keeps three local files that share one stem: the page raster as
Revit rendered it (``_source.png``), the tinted and rotated overlay that the
Revit ImageType loads (``.png``), and this module's state (``.json``). The
ImageType is matched back to its state through the overlay PNG file name.
"""

import json
import os
import re
import tempfile

from .geometry import make_pose
from .members import DEFAULT_TOLERANCE_DEGREES, DEFAULT_TOLERANCE_FEET
from .style import DEFAULT_OPACITY, DEFAULT_TINT, TINTS, clamp_opacity


# Version 2 measures pose centers from the model origin on the view's
# right/up axes (version 1 used the view origin). Hosts re-read the center
# from a placed image before use, so version 1 files still load.
STATE_VERSION = 2
OVERLAY_PREFIX = 'pdfoverlay_'
SOURCE_SUFFIX = '_source.png'
OVERLAY_SUFFIX = '.png'
STATE_SUFFIX = '.json'
_UNSAFE = re.compile(r'[^A-Za-z0-9]+')


def default_cache_root(environ=None):
    environ = os.environ if environ is None else environ
    base = environ.get('LOCALAPPDATA') or tempfile.gettempdir()
    return os.path.join(base, 'KLA Tools', 'PDF Overlay')


def overlay_stem(pdf_path, page, unique):
    """Return a file-system safe, recognizable stem for one overlay."""
    name = os.path.splitext(os.path.basename(pdf_path))[0]
    slug = _UNSAFE.sub('-', name)[:40].strip('-') or 'pdf'
    return '{}{}_p{}_{}'.format(OVERLAY_PREFIX, slug, int(page), unique)


def overlay_paths(cache_root, stem):
    base = os.path.join(cache_root, stem)
    return {
        'source': base + SOURCE_SUFFIX,
        'overlay': base + OVERLAY_SUFFIX,
        'state': base + STATE_SUFFIX,
    }


def stem_from_image_name(name):
    """Return the overlay stem for an ImageType name or path, else None."""
    if not name:
        return None
    base = os.path.basename(name)
    root, ext = os.path.splitext(base)
    if not root.startswith(OVERLAY_PREFIX) or ext.lower() != OVERLAY_SUFFIX:
        return None
    return root


def make_state(pdf_path, page, dpi, page_size, pose,
               tint=DEFAULT_TINT, opacity=DEFAULT_OPACITY, created='',
               tolerance_feet=DEFAULT_TOLERANCE_FEET,
               tolerance_degrees=DEFAULT_TOLERANCE_DEGREES):
    return {
        'version': STATE_VERSION,
        'pdf_path': pdf_path,
        'page': int(page),
        'dpi': int(dpi),
        'page_size': [int(page_size[0]), int(page_size[1])],
        'pose': pose,
        'tint': tint,
        'opacity': clamp_opacity(opacity),
        'created': created or '',
        'tolerance_feet': clamp_tolerance(tolerance_feet, DEFAULT_TOLERANCE_FEET, 100.0),
        'tolerance_degrees': clamp_tolerance(tolerance_degrees, DEFAULT_TOLERANCE_DEGREES, 45.0),
    }


def clamp_tolerance(value, default, maximum):
    """Return a positive tolerance no larger than maximum, or default if unreadable."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    if value != value or value <= 0:
        return default
    return min(value, maximum)


def validate_state(state):
    """Return a normalized copy of state, or raise ValueError."""
    try:
        pose = state['pose']
        size = [int(value) for value in state['page_size']]
        normalized = make_state(
            state['pdf_path'], state['page'], state['dpi'], size,
            make_pose(pose['center'], pose['feet_per_pixel'], pose.get('rotation', 0.0)),
            state.get('tint', DEFAULT_TINT), state.get('opacity', DEFAULT_OPACITY),
            state.get('created', ''),
            state.get('tolerance_feet', DEFAULT_TOLERANCE_FEET),
            state.get('tolerance_degrees', DEFAULT_TOLERANCE_DEGREES))
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ValueError('Overlay state is incomplete.')
    if size[0] <= 0 or size[1] <= 0 or normalized['pose']['feet_per_pixel'] <= 0:
        raise ValueError('Overlay state has an invalid size or scale.')
    if normalized['tint'] not in TINTS:
        normalized['tint'] = DEFAULT_TINT
    return normalized


def describe_overlay(state, in_view, fallback_created=''):
    """Return a list label that tells repeated imports of one PDF apart."""
    created = state.get('created') or fallback_created
    when = ''
    match = re.match(r'\d{4}-(\d{2})-(\d{2})[T ](\d{2}:\d{2})', created or '')
    if match:
        when = '{}/{} {}'.format(match.group(1), match.group(2), match.group(3))
    parts = ['{}  p{}'.format(os.path.basename(state['pdf_path']), state['page']),
             '{} DPI'.format(state['dpi'])]
    if when:
        parts.append(when)
    parts.append('in this view' if in_view else 'not in this view')
    return u' · '.join(parts)


def load_state(path):
    with open(path, 'r') as state_file:
        return validate_state(json.load(state_file))


def save_state(path, state):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    temp_path = path + '.tmp'
    with open(temp_path, 'w') as state_file:
        json.dump(validate_state(state), state_file, indent=2, sort_keys=True)
    if os.path.exists(path):
        os.remove(path)
    os.rename(temp_path, path)
