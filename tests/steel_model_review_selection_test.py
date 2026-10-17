"""Verify bidirectional selection without filter changes or selection feedback."""

import ast
import io
import os
import sys
import types
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))

from steel_model_review import reporting
from steel_model_review_reporting_test import row
import steel_model_review_view_test as view_tests


class SelectionMatchingTests(unittest.TestCase):
    def test_owned_finding_precedes_related_support_match(self):
        beam = row()
        column = dict(row(), uid='column', id=67890)
        self.assertIs(column, reporting.selection_match([beam, column], ['column']))

    def test_current_owned_finding_is_preserved_among_several_results(self):
        first, second = row(), row()
        self.assertIs(second, reporting.selection_match([first, second], ['beam'], second))

    def test_related_match_is_available_when_no_owned_row_is_visible(self):
        beam = row()
        self.assertIs(beam, reporting.selection_match([beam], ['column']))

    def test_empty_unmatched_and_filtered_out_selections_have_no_match(self):
        for rows, uids in (([row()], []), ([row()], ['other']), ([], ['beam'])):
            self.assertIsNone(reporting.selection_match(rows, uids))


def browser_fixture():
    path = os.path.join(ROOT, 'lib', 'steel_model_review', 'browser.py')
    with io.open(path, encoding='utf-8') as stream:
        tree = ast.parse(stream.read(), path)
    tree.body = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    scope = {'forms': types.SimpleNamespace(WPFWindow=object),
             'evidence_text': reporting.evidence_text, 'selection_match': reporting.selection_match}
    exec(compile(tree, path, 'exec'), scope)
    window = scope['ReviewWindow'].__new__(scope['ReviewWindow'])
    class Grid(object):
        def __init__(self):
            self.Items = reporting.filtered_rows([row(), row('Warning')], severity='All')
            self._selected = None
            self.ScrollIntoView = mock.Mock()

        @property
        def SelectedItem(self):
            return self._selected

        @SelectedItem.setter
        def SelectedItem(self, value):
            self._selected = value
            window._detail(None, None)
    window.findings = Grid()
    window._syncing_selection = False
    window._ready = True
    window.detail = types.SimpleNamespace(Text='')
    window.selection_status = types.SimpleNamespace(Text='')
    window.relationships, window.members = {}, {}
    window.request = mock.Mock()
    return window


class BrowserSelectionTests(unittest.TestCase):
    def test_model_selection_selects_visible_row_without_requesting_selection_back(self):
        window = browser_fixture()
        window.select_members(['beam'])
        self.assertIs(window.findings.Items[0], window.findings.SelectedItem)
        window.findings.ScrollIntoView.assert_called_once()
        window.request.assert_not_called()
        self.assertIn('Endpoint plan miss.', window.detail.Text)

    def test_unmatched_model_selection_clears_old_row_and_explains_filters(self):
        window = browser_fixture()
        window.select_members(['beam'])
        window.select_members(['other'])
        self.assertIsNone(window.findings.SelectedItem)
        self.assertIn('current filters', window.selection_status.Text)
        self.assertEqual('', window.detail.Text)
        window.request.assert_not_called()

    def test_user_row_selection_requests_own_member_and_keeps_camera_action_separate(self):
        window = browser_fixture()
        window.findings.SelectedItem = window.findings.Items[1]
        window.request.assert_called_once_with('highlight', window.findings.Items[1].row)


class SelectionSessionTests(unittest.TestCase):
    """Use the actual controller with the existing Revit boundary fixture."""

    def setUp(self):
        view_tests.LiveSessionTests.setUp(self)
        self.session.colors_dirty = self.session.scope_dirty = False

    def execute(self):
        self.session.Execute(self.uiapp)

    def test_table_selection_is_queued_then_selects_only_owning_member_without_zoom(self):
        result = self.session.snapshot['rows'][0]
        element = types.SimpleNamespace(Id=42, UniqueId=result['uid'])
        self.document.views[result['uid']] = self.document.views[42] = element
        def selection_echo(identities):
            self.uidoc.Selection.GetElementIds.return_value = identities
            self.session._selection_changed(None, None)
        self.uidoc.Selection.SetElementIds.side_effect = selection_echo
        self.session.request('highlight', result)
        self.uidoc.Selection.SetElementIds.assert_not_called()
        self.execute()
        self.uidoc.Selection.SetElementIds.assert_called_once_with([42])
        self.uidoc.RequestViewChange.assert_not_called()
        self.callbacks['navigate'].assert_not_called()
        self.scope['DB'].Transaction.assert_not_called()
        self.window.select_members.assert_called_once_with([result['uid']])
        self.event.Raise.assert_called_once()

    def test_model_event_does_not_write_selection_until_external_event_and_updates_report(self):
        self.document.views[42] = types.SimpleNamespace(UniqueId='a')
        self.uidoc.Selection.GetElementIds.return_value = [42]
        self.session._selection_changed(None, None)
        self.uidoc.Selection.SetElementIds.assert_not_called()
        self.window.select_members.assert_not_called()
        self.execute()
        self.window.select_members.assert_called_once_with(['a'])
        self.uidoc.Selection.SetElementIds.assert_not_called()
        self.scope['DB'].Transaction.assert_not_called()
        self.callbacks['save'].assert_not_called()

    def test_selection_echo_does_not_raise_a_new_request(self):
        self.session.setting_selection = True
        self.session._selection_changed(None, None)
        self.event.Raise.assert_not_called()

    def test_latest_table_click_wins_and_model_click_cancels_pending_table_request(self):
        first, second = self.session.snapshot['rows']
        self.session.request('highlight', first)
        self.session.request('highlight', second)
        self.assertEqual([('highlight', second)], self.session.actions)
        self.session._selection_changed(None, None)
        self.assertEqual([], self.session.actions)

    def test_other_document_selection_event_is_ignored(self):
        self.uiapp.ActiveUIDocument = None
        self.session._selection_changed(None, None)
        self.event.Raise.assert_not_called()

    def test_table_selection_is_blocked_after_switching_projects(self):
        self.session.request('highlight', self.session.snapshot['rows'][0])
        self.uiapp.ActiveUIDocument = types.SimpleNamespace(Document=view_tests.Document())
        self.execute()
        self.uidoc.Selection.SetElementIds.assert_not_called()
        self.window.select_members.assert_not_called()

    def test_already_selected_member_does_not_rewrite_native_selection(self):
        result = self.session.snapshot['rows'][0]
        element = types.SimpleNamespace(Id=42, UniqueId=result['uid'])
        self.document.views[result['uid']] = self.document.views[42] = element
        self.uidoc.Selection.GetElementIds.return_value = [42]
        self.session.request('highlight', result)
        self.execute()
        self.uidoc.Selection.SetElementIds.assert_not_called()

    def test_deleted_row_cannot_change_selection(self):
        self.session.request('highlight', self.session.snapshot['rows'][0])
        self.execute()
        self.uidoc.Selection.SetElementIds.assert_not_called()


if __name__ == '__main__':
    unittest.main()
