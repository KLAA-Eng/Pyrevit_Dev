"""Host-free dialog data. Compatible with IronPython 2.7 and CPython."""
from __future__ import unicode_literals


class DialogResult(object):
    """Inspect action explicitly; cancellation and accepted empty values differ.

    ``is_cancelled`` is true for ``cancel`` and for Action Choice's ``close``:
    either way the user did not choose. ``action`` still tells them apart.
    """
    def __init__(self, action='cancel', value=None):
        self.action = action
        self.value = value

    @property
    def is_cancelled(self):
        return self.action in ('cancel', 'close')


class SelectionItem(object):
    def __init__(self, key, label, value=None, description='', groups=(),
                 checked=False, enabled=True):
        if key is None:
            raise ValueError('Selection keys cannot be None.')
        self.Key = key
        self.Label = label
        self.Value = value
        self.Description = description or ''
        self.Groups = tuple(groups)
        self.CanSelect = bool(enabled)
        self.IsChecked = bool(checked and enabled)

    def clone(self):
        return SelectionItem(self.Key, self.Label, self.Value, self.Description,
                             self.Groups, self.IsChecked, self.CanSelect)


class SelectionGroup(object):
    def __init__(self, key, label):
        self.Key = key
        self.Label = label


class SelectionState(object):
    """Checks belong to stable keys and survive filtering; labels need not be unique."""
    def __init__(self, items, multiple=True, groups=None):
        self.items = [item.clone() for item in items]
        self._by_key = dict((item.Key, item) for item in self.items)
        if len(self._by_key) != len(self.items):
            raise ValueError('Selection keys must be unique.')
        self.multiple = bool(multiple)
        if not multiple and sum(item.IsChecked for item in self.items) > 1:
            raise ValueError('Single selection accepts at most one initial check.')
        self.query = ''
        self.group = None
        if groups is None:
            keys = []
            for item in self.items:
                for key in item.Groups:
                    if key not in keys:
                        keys.append(key)
            groups = [SelectionGroup(key, key) for key in keys]
        self.groups = list(groups)
        group_keys = [group.Key for group in self.groups]
        if None in group_keys or len(set(group_keys)) != len(group_keys):
            raise ValueError('Group keys must be unique; None is reserved for All Items.')

    @property
    def visible_items(self):
        query = self.query.strip().lower()
        return [item for item in self.items
                if (self.group is None or self.group in item.Groups)
                and (not query or query in (item.Label + ' ' + item.Description).lower())]

    @property
    def selected_values(self):
        return [item.Value for item in self.items if item.CanSelect and item.IsChecked]

    def set_checked(self, key, checked):
        item = self._by_key[key]
        if not item.CanSelect:
            item.IsChecked = False
            return
        if checked and not self.multiple:
            for row in self.items:
                row.IsChecked = False
        item.IsChecked = bool(checked)

    def set_visible_checked(self, checked):
        if checked and not self.multiple:
            raise ValueError('Check All is available only for multiple selection.')
        for item in self.visible_items:
            self.set_checked(item.Key, checked)


class ActionChoice(object):
    def __init__(self, key, label, description='', enabled=True):
        if key is None:
            raise ValueError('Action keys cannot be None.')
        self.Key = key
        self.Label = label
        self.Description = description or ''
        self.CanSelect = bool(enabled)


def validate_text(value, required=False, validator=None):
    """Validate without trimming the returned value. Validators return an error or None."""
    if required and not value.strip():
        return 'Enter a value.'
    if validator is not None:
        return validator(value)
    return None
