"""Launcher metadata for the DevSandbox UI Gallery.

The gallery uses these stable identifiers to open known dialog families with
sample data.  Keeping the list host-independent allows it to be tested outside
of Revit and prevents filesystem XAML discovery from becoming executable.
"""
from __future__ import unicode_literals


_LAUNCHERS = (
    {
        'id': 'kla-custom-alert',
        'category': 'KL&A custom',
        'title': 'KL&A alert',
        'description': 'Branded informational and warning dialog.',
        'uses_seed_data': True,
    },
    {
        'id': 'kla-find-replace',
        'category': 'KL&A custom',
        'title': 'Find and replace',
        'description': 'Branded rename form in safe preview mode.',
        'uses_seed_data': True,
    },
    {
        'id': 'kla-select-from-dict',
        'category': 'KL&A custom',
        'title': 'KL&A list selection',
        'description': 'Branded selectable list with sample family types.',
        'uses_seed_data': True,
    },
    {
        'id': 'kla-steel-psf',
        'category': 'KL&A custom',
        'title': 'Steel PSF story selection',
        'description': 'DevSandbox branded story selector with sample levels.',
        'uses_seed_data': True,
    },
    {
        'id': 'pyrevit-alert',
        'category': 'pyRevit standard',
        'title': 'Alert',
        'description': 'Standard pyRevit notification dialog.',
        'uses_seed_data': True,
    },
    {
        'id': 'pyrevit-ask-for-string',
        'category': 'pyRevit standard',
        'title': 'Text input',
        'description': 'Standard pyRevit single-value text prompt.',
        'uses_seed_data': True,
    },
    {
        'id': 'pyrevit-command-switch',
        'category': 'pyRevit standard',
        'title': 'Command switch',
        'description': 'Standard pyRevit action picker with sample commands.',
        'uses_seed_data': True,
    },
    {
        'id': 'pyrevit-select-list',
        'category': 'pyRevit standard',
        'title': 'List selection (multi-select)',
        'description': 'Standard pyRevit list selector with seeded names.',
        'uses_seed_data': True,
    },
    {
        'id': 'pyrevit-select-list-single',
        'category': 'pyRevit standard',
        'title': 'List selection (single-select)',
        'description': 'Standard pyRevit single-choice list with seeded names.',
        'uses_seed_data': True,
    },
)


def gallery_launchers():
    """Return independent launcher dictionaries ordered by identifier."""
    return [dict(launcher) for launcher in _LAUNCHERS]


def launcher_by_id(launcher_id):
    """Return a launcher definition for an exact identifier, if available."""
    for launcher in _LAUNCHERS:
        if launcher['id'] == launcher_id:
            return dict(launcher)
    return None
