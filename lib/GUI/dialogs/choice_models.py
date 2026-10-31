"""Host-free Action Choice requests, defaults and explicit result snapshots."""
from __future__ import unicode_literals

from .models import ActionChoice, DialogResult

try:
    _TEXT_TYPES = (basestring,)
except NameError:
    _TEXT_TYPES = (str,)

_BUTTON_ORDER = ('ok', 'yes', 'no', 'retry', 'cancel', 'close')


def _clone_choices(choices):
    rows = []
    keys = set()
    for choice in choices:
        try:
            if choice.Key is None or choice.Key in keys:
                raise ValueError('Action keys must be unique and non-None.')
            keys.add(choice.Key)
        except TypeError:
            raise ValueError('Action keys must be hashable.')
        label = choice.Label
        if (not isinstance(label, _TEXT_TYPES) or not label.strip()
                or label.splitlines() != [label]):
            raise ValueError('Action labels must be nonblank single-line text.')
        rows.append(ActionChoice(choice.Key, label, choice.Description, choice.CanSelect))
        if len(rows) > 4:
            raise ValueError('Action Choice supports at most four command links.')
    return rows


def _standard_buttons(buttons):
    try:
        supplied = tuple(buttons)
    except TypeError:
        raise ValueError('Buttons must be a collection of standard button names.')
    seen = set()
    for button in supplied:
        if not isinstance(button, _TEXT_TYPES) or button not in _BUTTON_ORDER:
            raise ValueError('Unknown standard button: {0}.'.format(button))
        if button in seen:
            raise ValueError('Standard buttons must be unique.')
        seen.add(button)
    return tuple(button for button in _BUTTON_ORDER if button in seen)


class ChoiceState(object):
    """Small command links and standard buttons; callers own subsequent actions."""
    def __init__(self, choices, buttons=('cancel',), default=None, allow_cancel=True,
                 checkbox_text='', checkbox_checked=False):
        self.choices = _clone_choices(choices)
        self.buttons = _standard_buttons(buttons)
        if not self.choices and not self.buttons:
            self.buttons = ('close',)
        self._by_key = dict((row.Key, row) for row in self.choices)
        self.can_cancel = bool(allow_cancel or 'cancel' in self.buttons)
        self.checkbox_text = checkbox_text or ''
        self.checked = bool(checkbox_checked) if self.checkbox_text else None
        self.default = self._resolve_default(default)
        if self.default is None and not self.can_cancel:
            raise ValueError('Action Choice needs an enabled action or cancellation.')

    def _available(self, kind, key):
        if kind == 'command':
            try:
                choice = self._by_key.get(key)
            except TypeError:
                return False
            return choice is not None and choice.CanSelect
        if kind == 'button':
            return key in self.buttons
        return False

    def _known(self, kind, key):
        if kind == 'command':
            try:
                return key in self._by_key
            except TypeError:
                return False
        return kind == 'button' and key in self.buttons

    def _resolve_default(self, default):
        # An unknown target is a caller error and fails here; a known but
        # disabled command falls back to the first enabled action.
        if default is not None:
            if not (isinstance(default, (tuple, list)) and len(default) == 2
                    and self._known(default[0], default[1])):
                raise ValueError('Unknown default action: {0!r}.'.format(default))
            kind, key = default
            if self._available(kind, key):
                return (kind, self._by_key[key].Key if kind == 'command' else key)
        for choice in self.choices:
            if choice.CanSelect:
                return ('command', choice.Key)
        return ('button', self.buttons[0]) if self.buttons else None

    def _result(self, kind, key):
        if kind == 'command':
            key = self._by_key[key].Key
        action = key if kind == 'button' and key in ('cancel', 'close') else 'accept'
        checked = bool(self.checked) if self.checkbox_text else None
        return DialogResult(action, {'kind': kind, 'key': key, 'checked': checked})

    def choose(self, kind, key):
        """Activate an available explicit control, returning a fresh result."""
        if self._available(kind, key):
            return self._result(kind, key)
        return None

    def forced_close(self):
        """A close from code, the owner or the system always ends the dialog, as ``close``."""
        return self._result('button', 'close')

    def dismiss(self, reason='cancel'):
        """Escape/Close obey cancellation policy even without a matching button."""
        if reason not in ('cancel', 'close'):
            raise ValueError('Dismissal reason must be cancel or close.')
        if self.can_cancel:
            return self._result('button', reason)
        return None
