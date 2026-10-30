"""Rename rule contracts without WPF, pyRevit or an active document."""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))


class RenameTests(unittest.TestCase):
    def test_public_import_is_host_free(self):
        code = ("import sys; sys.path.insert(0, 'lib'); "
                "from GUI.dialogs import RenameField, create_rename, rename; "
                "assert 'wpf' not in sys.modules; assert 'pyrevit' not in sys.modules")
        subprocess.check_call([sys.executable, '-B', '-c', code], cwd=ROOT)

    def test_rules_are_cloned_and_returned_as_an_independent_snapshot(self):
        from GUI.dialogs.rename_models import RenameField, RenameState
        original = RenameField('name', 'View Name', find='A', replace='b', prefix=' ', suffix='!')
        state = RenameState([original, RenameField('number', 'Number', allow_case=False)])
        state.fields[0].Prefix = 'PRE-'
        result = state.rename_result()
        self.assertEqual('accept', result.action)
        self.assertEqual({'operation': 'rename', 'fields': {
            'name': {'find': 'A', 'replace': 'b', 'prefix': 'PRE-', 'suffix': '!'},
            'number': {'find': '', 'replace': '', 'prefix': '', 'suffix': ''}}}, result.value)
        self.assertEqual(' ', original.Prefix)
        state.fields[0].Find = 'changed'
        self.assertEqual('A', result.value['fields']['name']['find'])

    def test_factory_failure_retains_the_public_modal_helper_after_lazy_import(self):
        import GUI.dialogs as dialogs
        with self.assertRaises(ValueError):
            dialogs.create_rename('Bad configuration', [])
        self.assertTrue(callable(dialogs.rename), 'Importing the WPF adapter must preserve the public modal helper')

    def test_all_rules_validate_before_rename_and_report_the_field(self):
        from GUI.dialogs.rename_models import RenameField, RenameState
        state = RenameState([RenameField('ok', 'Valid', prefix='A'),
                             RenameField('bad', 'Sheet Number', replace='replacement')])
        with self.assertRaises(ValueError) as error:
            state.rename_result()
        self.assertEqual('Sheet Number: Enter Find text before using Replace.', str(error.exception))
        state.fields[1].Find = ' '
        self.assertEqual(' ', state.rename_result().value['fields']['bad']['find'])

    def test_case_actions_ignore_rule_text_and_only_target_the_requested_field(self):
        from GUI.dialogs.rename_models import RenameField, RenameState
        state = RenameState([RenameField('name', 'Name', replace='invalid'),
                             RenameField('number', 'Number', replace='also invalid', allow_case=False)])
        for mode in ('upper', 'lower'):
            result = state.case_result('name', mode)
            self.assertEqual('accept', result.action)
            self.assertEqual({'operation': mode, 'field': 'name'}, result.value)
        for key, mode in (('number', 'upper'), ('missing', 'upper'), ('name', 'title')):
            with self.assertRaises(ValueError):
                state.case_result(key, mode)

    def test_literal_rules_keep_existing_case_sensitive_prefix_suffix_semantics(self):
        from GUI.dialogs.rename_models import RenameField, RenameState
        from find_replace.workflow import rename_value
        rule = RenameState([RenameField('name', 'Name', find='A.', replace='b',
                                        prefix='[', suffix=']')]).rename_result().value['fields']['name']
        self.assertEqual('[b a. A]', rename_value('A. a. A', rule['find'], rule['replace'],
                                                 rule['prefix'], rule['suffix']))

    def test_one_to_three_unique_non_null_hashable_keys_are_required_before_wpf(self):
        from GUI.dialogs import RenameField, create_rename
        from GUI.dialogs.rename_models import RenameState
        for rows in ([], [RenameField(str(i), 'Name') for i in range(4)],
                     [RenameField('x', 'First'), RenameField('x', 'Second')],
                     [RenameField(None, 'Missing')], [RenameField([], 'Unhashable')]):
            with self.assertRaises(ValueError):
                create_rename('Invalid configuration', rows)
        for count in (1, 2, 3):
            state = RenameState(RenameField(str(i), 'Same label') for i in range(count))
            self.assertEqual(count, len(state.fields))


if __name__ == '__main__':
    unittest.main()
