"""Legacy select_from_dict signature backed by the standard Selection dialog."""
from __future__ import unicode_literals

from GUI import dialogs
from GUI.dialogs.models import SelectionItem
from GUI.window_chrome import access_text


def select_from_dict(elements_dict, title, label='Select Elements',
                     button_name='Select', version=None, SelectMultiple=True,
                     initial_checked_names=None):
    """Return checked values as a list; cancellation returns an empty list.

    Keep legacy sorting, list deduplication, first-row defaults and captions at
    this boundary. Callers can adopt the richer dialog result API separately.
    """
    if isinstance(elements_dict, list):
        elements_dict = dict((item, item) for item in elements_dict)
    pairs = sorted((key, value) for key, value in elements_dict.items() if key)
    checked = (set([pairs[0][0]]) if pairs else set()) if initial_checked_names is None else set(initial_checked_names)
    rows = [SelectionItem(key, key, value, checked=key in checked)
            for key, value in pairs]

    # The old API permits several explicit initial checks even in single mode.
    # Preserve those until a user check enforces exclusivity; the standard
    # factory correctly rejects ambiguous initial checks for its own callers.
    restore_checks = not SelectMultiple and sum(row.IsChecked for row in rows) > 1
    if restore_checks:
        for row in rows:
            row.IsChecked = False
    window = dialogs.create_selection(title, rows, multiple=SelectMultiple,
                                      groups=[], prompt=label.rstrip().rstrip(':'),
                                      required=False, version=version)
    if restore_checks:
        for row in window.state.items:
            row.IsChecked = row.Key in checked
        window.update_checks()
    window.accept_button.Content = access_text(button_name)
    window.ShowDialog()
    # Read the canonical state rather than the scalar single-select result:
    # an accepted None-valued item still has to return [None], not [].
    return [] if window.result.is_cancelled else list(window.state.selected_values)
