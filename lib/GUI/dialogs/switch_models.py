"""Host-free state for a compact command chooser and its optional switches."""
from __future__ import unicode_literals

from .models import ActionChoice, DialogResult


class CommandSwitch(object):
    """A configurable Boolean option; disabled options retain their initial value."""
    def __init__(self, key, label, checked=False, enabled=True):
        self.Key = key
        self.Label = label
        self.IsChecked = bool(checked)
        self.CanToggle = bool(enabled)

    def clone(self):
        return CommandSwitch(self.Key, self.Label, self.IsChecked, self.CanToggle)


def _index(rows, kind):
    result = {}
    for row in rows:
        try:
            if row.Key is None or row.Key in result:
                raise ValueError('{} keys must be unique and non-None.'.format(kind))
            result[row.Key] = row
        except TypeError:
            raise ValueError('{} keys must be hashable.'.format(kind))
    return result


class SwitchState(object):
    """Filtering never changes input order, optional switches or caller-owned rows."""
    def __init__(self, choices, switches=()):
        self.choices = [ActionChoice(row.Key, row.Label, row.Description, row.CanSelect)
                        for row in choices]
        self.switches = [row.clone() for row in switches]
        self._choices = _index(self.choices, 'Command')
        self._switches = _index(self.switches, 'Switch')
        self.query = ''

    @property
    def visible_choices(self):
        query = self.query.strip().lower()
        return [row for row in self.choices if not query
                or query in (row.Label + ' ' + row.Description).lower()]

    def set_switch(self, key, checked):
        row = self._switches[key]
        if row.CanToggle:
            row.IsChecked = bool(checked)
        return row.IsChecked

    def enter_choice(self, focused_key=None, search_focused=False):
        """Space handles toggles; Enter runs a command or sole search match only."""
        enabled = [row.Key for row in self.visible_choices if row.CanSelect]
        if focused_key is not None:
            return focused_key if focused_key in enabled else None
        if search_focused and len(enabled) == 1:
            return enabled[0]
        return None

    def result_for(self, key):
        row = self._choices[key]
        if not row.CanSelect:
            raise ValueError('This command is unavailable.')
        return DialogResult('accept', {
            'command': row.Key,
            'switches': dict((item.Key, item.IsChecked) for item in self.switches),
        })
