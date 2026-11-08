"""Production selector contracts at the shared-dialog/collector boundary."""
from __future__ import unicode_literals
import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_ROOT = os.environ.get('KLC_SELECTION_SOURCE_ROOT', PROJECT_ROOT)
sys.path.insert(0, os.path.join(SOURCE_ROOT, 'lib'))
import GUI
GUI.__path__.insert(0, os.path.join(PROJECT_ROOT, 'lib', 'GUI'))
from GUI import tool_selectors as selectors
from GUI.dialogs.models import DialogResult, SelectionItem, SelectionState

class _Record(object):
    def __init__(self, **attributes):
        self.__dict__.update(attributes)

class _Window(object):
    def __init__(self, rows, options, interaction):
        self.state = SelectionState(rows, options['multiple'], options['groups'])
        self.result = DialogResult()
        self.accept_button = _Record(Content='Select')
        self.interaction = interaction
    def ShowDialog(self):
        self.interaction(self)

class ToolSelectorTests(unittest.TestCase):
    def setUp(self):
        self.originals = []
        self.calls = []
        self.interaction = lambda window: setattr(window, 'result', DialogResult('accept'))
        self.replace(selectors, '_owner', lambda value: value)
        def create(title, rows, **options):
            window = _Window(rows, options, self.interaction)
            self.calls.append((title, options, window))
            return window
        self.replace(selectors.dialogs, 'create_selection', create)
    def replace(self, module, name, value):
        self.originals.append((module, name, getattr(module, name)))
        setattr(module, name, value)
    def tearDown(self):
        for module, name, value in reversed(self.originals):
            setattr(module, name, value)
    def test_revisions_preserve_filter_identity_unchecked_defaults_and_empty_accept(self):
        revision = object()
        predicate = lambda value: True
        observed = []
        def collect(document, filterfunc=None):
            observed.append((document, filterfunc))
            return [SelectionItem('r', 'Revision', revision)]
        self.replace(selectors.collectors, 'revision_items', collect)
        document = object()
        self.assertEqual([], selectors.select_revisions(document, 'Tool', filterfunc=predicate,
                                                        button_name='Select_Revisions', version='v1', owner=42))
        self.assertEqual([(document, predicate)], observed)
        title, options, window = self.calls[0]
        self.assertFalse(window.state.items[0].IsChecked)
        self.assertFalse(options['required'])
        self.assertEqual(42, options['owner'])
        self.assertEqual('v1', options['version'])
        self.assertEqual('Select__Revisions', window.accept_button.Content)
    def test_revision_filter_keeps_issued_policy_in_callers(self):
        unissued = _Record(Issued=False)
        issued = _Record(Issued=True)
        def collect(document, filterfunc=None):
            return [SelectionItem(str(index), str(index), revision)
                    for index, revision in enumerate([unissued, issued])
                    if filterfunc is None or filterfunc(revision)]
        self.replace(selectors.collectors, 'revision_items', collect)
        def check_all(window):
            window.state.set_visible_checked(True)
            window.result = DialogResult('accept')
        self.interaction = check_all
        self.assertEqual([unissued], selectors.select_revisions(object(), 'Set',
                         filterfunc=lambda value: not value.Issued))
        self.assertEqual([unissued, issued], selectors.select_revisions(object(), 'Remove'))
        self.assertEqual([unissued, issued], selectors.select_revisions(object(), 'Set config',
                         filterfunc=lambda value: True))

    def test_sheet_placeholder_flag_groups_and_legacy_number_sort(self):
        ten = _Record(SheetNumber='S10')
        two = _Record(SheetNumber='S2')
        calls = []
        group = selectors.dialogs.SelectionGroup('set', 'Set')
        def collect(document, include, predicate):
            calls.append((include, predicate))
            return [SelectionItem('2', 'Two', two, groups=['set']),
                    SelectionItem('10', 'Ten', ten, groups=['set'])], [group]
        self.replace(selectors.collectors, 'sheet_items', collect)
        self.assertEqual([], selectors.select_sheets(object(), 'Sheets'))
        self.assertEqual([(True, None)], calls)
        title, options, window = self.calls[-1]
        self.assertEqual([ten, two], [row.Value for row in window.state.items])
        self.assertEqual('All Sheets', options['all_label'])
        self.assertEqual([group], options['groups'])
        self.assertFalse(any(row.IsChecked for row in window.state.items))

    def test_sheet_cancel_returns_none_and_false_placeholder_option_reaches_collector(self):
        calls = []
        self.replace(selectors.collectors, 'sheet_items',
                     lambda doc, include, predicate: (calls.append(include) or [], []))
        self.interaction = lambda window: None
        self.assertIsNone(selectors.select_sheets(object(), 'Sheets', include_placeholder=False))
        self.assertEqual([False], calls)

    def test_documents_exclude_current_links_but_include_families_and_duplicate_titles(self):
        def document(title, linked=False, family=False):
            return _Record(Title=title, IsLinked=linked, IsFamilyDocument=family, PathName='')
        active = document('Current')
        linked = document('Link', linked=True)
        first = document('Same')
        family = document('Same', family=True)
        app = _Record(Documents=[active, linked, first, family, first])
        def check_all(window):
            window.state.set_visible_checked(True)
            window.result = DialogResult('accept')
        self.interaction = check_all
        self.assertEqual([first, family], selectors.select_open_documents(app, active, 'Documents'))
        self.assertEqual('OK', self.calls[-1][2].accept_button.Content)
        self.assertEqual([family], selectors.select_open_documents(app, active, 'Documents',
                         filterfunc=lambda document: document.IsFamilyDocument))

    def test_no_other_documents_reports_message_and_returns_none_without_selection(self):
        active = _Record(Title='Current', IsLinked=False, IsFamilyDocument=False, PathName='')
        alerts = []
        self.replace(selectors, '_alert', lambda message, title, **options: alerts.append(message))
        self.assertIsNone(selectors.select_open_documents(_Record(Documents=[active]), active, 'Tool'))
        self.assertEqual([], self.calls)
        self.assertEqual(1, len(alerts))
        self.assertIn('At least two documents must be open', alerts[0])

    def test_filtered_empty_document_list_opens_selector_like_original(self):
        active = _Record(Title='Current', IsLinked=False, IsFamilyDocument=False, PathName='')
        other = _Record(Title='Other', IsLinked=False, IsFamilyDocument=False, PathName='')
        self.assertEqual([], selectors.select_open_documents(_Record(Documents=[active, other]), active,
                         'Tool', filterfunc=lambda value: False))
        self.assertEqual(1, len(self.calls))

    def test_use_selected_views_preserves_identity_filter_and_skips_query_on_yes(self):
        selected = _Record(UniqueId='selected', ViewType='Legend')
        wrong = _Record(UniqueId='wrong', ViewType='FloorPlan')
        self.replace(selectors, '_all_views', lambda document: self.fail('Selection accepted; no query allowed'))
        alerts = []
        def confirm(message, title, **options):
            alerts.append((message, options))
            return True
        self.replace(selectors, '_alert', confirm)
        self.assertEqual([selected], selectors.select_views(object(), 'Legends', use_selection=True,
                         selected_views=[wrong, selected], filterfunc=lambda view: view.ViewType == 'Legend'))
        self.assertEqual([], self.calls)
        self.assertIn('1 views', alerts[0][0])
        self.assertTrue(alerts[0][1]['yes'])
        self.assertTrue(alerts[0][1]['no'])
        self.assertIs(selected, selectors.select_views(object(), 'Legend', use_selection=True,
                      selected_views=[selected], multiple=False))

    def test_declined_current_selection_queries_filtered_sorted_views_unchecked(self):
        selected = _Record(UniqueId='selected', ViewType='Legend')
        zulu = _Record(UniqueId='zulu', Name='Zulu', ViewType='Legend')
        alpha = _Record(UniqueId='alpha', Name='Alpha', ViewType='Legend')
        wrong = _Record(UniqueId='wrong', Name='Other', ViewType='FloorPlan')
        self.replace(selectors, '_alert', lambda *args, **options: False)
        self.replace(selectors, '_all_views', lambda document: [zulu, wrong, alpha])
        self.replace(selectors, '_view_name', lambda view: view.Name + ' (' + view.ViewType + ')')
        def choose(window):
            self.assertEqual([alpha, zulu], [row.Value for row in window.state.items])
            self.assertFalse(any(row.IsChecked for row in window.state.items))
            window.state.set_checked('alpha', True)
            window.result = DialogResult('accept')
        self.interaction = choose
        result = selectors.select_views(object(), 'Legends', use_selection=True, selected_views=[selected],
                                       filterfunc=lambda view: view.ViewType == 'Legend')
        self.assertEqual([alpha], result)

    def test_named_fallback_single_returns_original_object_and_cancel_none(self):
        schedule = object()
        def choose(window):
            self.assertEqual(['Alpha', 'Zulu'], [row.Label for row in window.state.items])
            self.assertFalse(any(row.IsChecked for row in window.state.items))
            window.state.set_checked('Zulu', True)
            window.result = DialogResult('accept')
        self.interaction = choose
        self.assertIs(schedule, selectors.select_named_item({'Zulu': schedule, 'Alpha': object()}, 'Schedule',
                      prompt='Select schedule to inspect:', button_name='Inspect Schedule'))
        self.assertEqual('Select schedule to inspect', self.calls[-1][1]['prompt'])
        self.interaction = lambda window: None
        self.assertIsNone(selectors.select_named_item({'Zulu': schedule}, 'Schedule'))

    def test_factory_failure_propagates_without_opening_another_dialog(self):
        def fail(*args, **options):
            raise RuntimeError('factory failed')
        self.replace(selectors.dialogs, 'create_selection', fail)
        self.assertRaises(RuntimeError, selectors.select_named_item, {'A': object()}, 'Schedule')