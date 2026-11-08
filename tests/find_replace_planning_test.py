import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from find_replace.planning import sheet_entries, view_entries


class Element(object):
    def __init__(self, number, name, identity):
        self.Name = name
        self.SheetNumber = number
        self.Id = type('Id', (), {'IntegerValue': identity})()


def rules(find='', replace='', prefix='', suffix=''):
    return dict(find=find, replace=replace, prefix=prefix, suffix=suffix)


class PlanningTests(unittest.TestCase):
    def test_sheet_rename_plans_title_and_number_together(self):
        sheet = Element('A1', 'Plan', 1)
        request = dict(operation='rename', fields=dict(name=rules(prefix='New '),
                                                       number=rules('A', 'B')))
        entry = sheet_entries([sheet], request, [sheet])[0]
        self.assertEqual([('Name', 'New Plan'), ('SheetNumber', 'B1')], entry['changes'])
        self.assertNotIn('issue', entry)

    def test_occupied_numbers_and_swaps_remain_skipped(self):
        first, second = Element('A1', 'First', 1), Element('B1', 'Second', 2)
        request = dict(operation='rename', fields=dict(name=rules(), number=rules('A', 'B')))
        entry = sheet_entries([first], request, [first, second])[0]
        self.assertEqual('Sheet number is already in use', entry['issue'])

    def test_duplicate_batch_numbers_are_rejected_case_insensitively(self):
        sheets = [Element('AA1', 'First', 1), Element('A1', 'Second', 2)]
        request = dict(operation='rename', fields=dict(name=rules(), number=rules('A', '')))
        # Both distinct source numbers become the exact same target.
        entries = sheet_entries(sheets, request, [])
        self.assertEqual(['Multiple selected sheets request this number'] * 2,
                         [entry['issue'] for entry in entries if 'issue' in entry])

    def test_case_actions_ignore_rules_and_leave_sheet_number_unchanged(self):
        sheet = Element('a1', 'Sheet title', 1)
        entry = sheet_entries([sheet], dict(operation='upper', field='name'), [sheet])[0]
        self.assertEqual([('Name', 'SHEET TITLE')], entry['changes'])
        self.assertEqual('a1', sheet.SheetNumber)

    def test_view_rule_strings_preserve_spaces_and_case_sensitive_matching(self):
        view = Element('', 'View plan', 1)
        entry = view_entries([view], dict(operation='rename', fields=dict(
            name=rules('PLAN', 'X', prefix=' ', suffix=' '))))[0]
        self.assertEqual([('Name', ' View plan ')], entry['changes'])

    def test_invalid_replace_rejected_before_execution(self):
        with self.assertRaises(ValueError):
            view_entries([Element('', 'View', 1)], dict(operation='rename',
                         fields=dict(name=rules(replace='X'))))


if __name__ == '__main__':
    unittest.main()
