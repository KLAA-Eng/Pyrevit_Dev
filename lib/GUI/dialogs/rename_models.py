"""Host-independent, caller-owned inputs and explicit rename requests."""
from __future__ import unicode_literals

from find_replace.workflow import rename_value

from .models import DialogResult


class RenameField(object):
    """One configurable naming group; rule strings are preserved verbatim."""
    def __init__(self, key, label, find='', replace='', prefix='', suffix='', allow_case=True):
        self.Key = key
        self.Label = label
        self.Find = find
        self.Replace = replace
        self.Prefix = prefix
        self.Suffix = suffix
        self.AllowCase = bool(allow_case)

    def clone(self):
        return RenameField(self.Key, self.Label, self.Find, self.Replace,
                           self.Prefix, self.Suffix, self.AllowCase)

    def rules(self):
        return {'find': self.Find, 'replace': self.Replace,
                'prefix': self.Prefix, 'suffix': self.Suffix}


class RenameState(object):
    """Edit cloned groups and return requests without applying any model changes."""
    def __init__(self, fields):
        self.fields = [field.clone() for field in fields]
        if not 1 <= len(self.fields) <= 2:
            raise ValueError('Rename requires one or two fields.')
        if sum(1 for field in self.fields if field.AllowCase) > 1:
            raise ValueError('Rename allows case actions on one field only.')
        keys = [field.Key for field in self.fields]
        try:
            valid_keys = None not in keys and len(set(keys)) == len(keys)
        except TypeError:
            valid_keys = False
        if not valid_keys:
            raise ValueError('Rename field keys must be unique, hashable and non-null.')
        self._by_key = dict((field.Key, field) for field in self.fields)

    @property
    def case_field(self):
        """The one field the shared Uppercase/Lowercase pair acts on, or None."""
        return next((field for field in self.fields if field.AllowCase), None)

    def rename_result(self):
        if not any(field.Find or field.Replace or field.Prefix or field.Suffix for field in self.fields):
            raise ValueError('Enter at least one rename rule.')
        for field in self.fields:
            try:
                # Reuse the existing literal-rule validator; no current names
                # are supplied, retained or previewed by this request dialog.
                rename_value('', field.Find, field.Replace, field.Prefix, field.Suffix)
            except ValueError as error:
                raise ValueError('{0}: {1}'.format(field.Label, error))
        return DialogResult('accept', {'operation': 'rename', 'fields':
                            dict((field.Key, field.rules()) for field in self.fields)})

    def case_result(self, key, operation):
        field = self._by_key.get(key)
        if operation not in ('upper', 'lower') or field is None or not field.AllowCase:
            raise ValueError('Choose an available field and case action.')
        return DialogResult('accept', {'operation': operation, 'field': key})


def view_fields():
    """The Views layout: one View Name group."""
    return [RenameField('name', 'View Name')]


def sheet_fields():
    """The Sheets layout: Sheet Number (no case actions) beside Sheet Name."""
    return [RenameField('number', 'Sheet Number', allow_case=False), RenameField('name', 'Sheet Name')]
