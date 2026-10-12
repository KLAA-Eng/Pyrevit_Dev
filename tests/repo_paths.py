"""Resolve the active ribbon layout for repository tests."""

import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAB_NAMES = ('KL&A Tools_dev.tab', 'KL&A Tools.tab')


def find_tab(root):
    """Require one active tab rather than silently testing the wrong copy."""
    names = [name for name in TAB_NAMES if os.path.isdir(os.path.join(root, name))]
    if len(names) != 1:
        raise ValueError('Expected one KL&A Tools ribbon tab; found {}'.format(names))
    return names[0]


TAB_NAME = find_tab(ROOT)
