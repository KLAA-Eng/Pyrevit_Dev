import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
from find_replace.controller import retry_elements
from find_replace.workflow import new_result, record
from GUI.dialogs import ActionChoice, DialogResult, view_fields


class RenameWindow(object):
    def __init__(self, fields, operation, events):
        self.state = type('State', (), {'fields': fields})()
        self.result = operation
        self.events = events

    def ShowDialog(self):
        self.events.append('rename_closed')

    def sync_fields(self):
        pass


class Dialogs(object):
    ActionChoice = ActionChoice

    def __init__(self, requests, retry=True):
        self.requests = list(requests)
        self.fields = []
        self.reports = []
        self.events = []
        self.retry = retry

    def create_rename(self, title, fields, **options):
        self.fields.append([field.clone() for field in fields])
        for field in fields:
            field.Prefix = 'P-'
        return RenameWindow(fields, self.requests.pop(0), self.events)

    def choose_action(self, title, choices, **options):
        self.reports.append((choices, options))
        return (DialogResult('accept', {'kind': 'command', 'key': 'edit_retry'})
                if self.retry else DialogResult('close'))


def request():
    return DialogResult('accept', {'operation': 'rename', 'fields': {
        'name': {'find': '', 'replace': '', 'prefix': 'P-', 'suffix': ''}}})


class RetryTests(unittest.TestCase):
    def test_partial_retry_excludes_committed_and_unchanged_elements(self):
        first, second, third = object(), object(), object()
        entries = [dict(element=first, label='A'), dict(element=second, label='B'),
                   dict(element=third, label='C')]
        result = new_result('Rename')
        record(result, 'changed', 'A')
        record(result, 'skipped', 'B', 'Collision')
        record(result, 'unchanged', 'C')
        self.assertEqual([second], retry_elements([first, second, third], entries, result))

    def test_clean_success_finishes_after_modal_closes_without_result_popup(self):
        from find_replace.controller import run
        api = Dialogs([request()])
        element = object()
        def execute(action, entries):
            self.assertEqual(['rename_closed'], api.events)
            result = new_result(action)
            record(result, 'changed', 'A')
            return result
        result = run('Tool', 'v1.0', [element], view_fields(),
                     lambda items, value: [dict(element=items[0], label='A')],
                     execute, dialogs_api=api)
        self.assertEqual(1, len(result['changed']))
        self.assertEqual([], api.reports)

    def test_partial_result_edits_rules_and_retries_only_unresolved(self):
        from find_replace.controller import run
        first, second = object(), object()
        api = Dialogs([request(), request()])
        targets = []
        def plan(items, value):
            targets.append(items)
            return [dict(element=item, label='A' if item is first else 'B') for item in items]
        def execute(action, entries):
            result = new_result(action)
            if len(entries) == 2:
                record(result, 'changed', 'A')
                record(result, 'skipped', 'B', 'Collision')
            else:
                record(result, 'changed', 'B')
            return result
        run('Tool', 'v1.0', [first, second], view_fields(), plan, execute, dialogs_api=api)
        self.assertEqual([[first, second], [second]], targets)
        self.assertEqual('P-', api.fields[1][0].Prefix)
        choices, options = api.reports[0]
        self.assertEqual('Edit and Retry', choices[0].Label)
        self.assertIn('Collision', options['details'])

    def test_cancel_does_not_plan_or_mutate(self):
        from find_replace.controller import run
        api = Dialogs([DialogResult()])
        def unexpected(*args):
            self.fail('Cancellation must not execute')
        self.assertIsNone(run('Tool', None, [object()], view_fields(), unexpected,
                              unexpected, dialogs_api=api))

    def test_browser_refresh_error_never_retries_committed_success(self):
        from find_replace.controller import run
        api = Dialogs([request()], retry=False)
        def execute(action, entries):
            result = new_result(action)
            record(result, 'changed', 'A')
            return result
        def refresh():
            raise RuntimeError('Browser unavailable')
        run('Tool', None, [object()], view_fields(),
            lambda items, value: [dict(element=items[0], label='A')], execute,
            after_change=refresh, dialogs_api=api)
        choices, options = api.reports[0]
        self.assertEqual([], choices)
        self.assertIn('Browser unavailable', options['details'])

    def test_no_op_can_edit_rules_and_keeps_selection(self):
        from find_replace.controller import run
        element = object()
        api = Dialogs([request(), DialogResult()])
        def execute(action, entries):
            result = new_result(action)
            record(result, 'unchanged', 'A')
            return result
        run('Tool', None, [element], view_fields(),
            lambda items, value: [dict(element=items[0], label='A')], execute,
            dialogs_api=api)
        self.assertEqual(2, len(api.fields))
        self.assertEqual('P-', api.fields[1][0].Prefix)
        self.assertIn('0 changed, 1 unchanged', api.reports[0][1]['prompt'])

    def test_planning_error_reports_details_without_mutation(self):
        from find_replace.controller import run
        api = Dialogs([request(), DialogResult()])
        def plan(*args):
            raise ValueError('Element unavailable')
        def execute(*args):
            self.fail('A planning error must not mutate the model')
        run('Tool', None, [object()], view_fields(), plan, execute, dialogs_api=api)
        self.assertIn('Element unavailable', api.reports[0][1]['details'])
        self.assertEqual(2, len(api.fields))

    def test_case_retry_retains_typed_rules_and_owner(self):
        from find_replace.controller import run
        api = Dialogs([DialogResult('accept', {'operation': 'upper', 'field': 'name'}),
                       DialogResult()])
        owners = []
        original = api.create_rename
        def create(title, fields, **options):
            owners.append(options['owner'])
            return original(title, fields, **options)
        api.create_rename = create
        def execute(action, entries):
            self.assertEqual('Uppercase', action)
            result = new_result(action)
            record(result, 'failed', 'A', 'Read-only')
            return result
        run('Tool', None, [object()], view_fields(),
            lambda items, value: [dict(element=items[0], label='A')], execute,
            owner=42, dialogs_api=api)
        self.assertEqual([42, 42], owners)
        self.assertEqual('P-', api.fields[1][0].Prefix)


if __name__ == '__main__':
    unittest.main()
