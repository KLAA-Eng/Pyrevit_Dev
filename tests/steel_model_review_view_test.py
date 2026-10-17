"""Verify filtered view colors and modeless request/transaction boundaries."""

import ast
import copy
import io
import os
import sys
import types
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))

from steel_model_review import view
from steel_model_review.engine import finding
from steel_model_review.reporting import filtered_rows
from steel_model_review_test import member


def snapshot():
    beam, other = member(), member('b')
    wall = member('wall', 'wall')
    rows = [finding('SMR-01', beam, 'Endpoint miss', 'Warning', related=[other]),
            finding('SMR-02', beam, 'Vertical miss', 'Critical')]
    return {'members': [beam, other, wall], 'rows': rows, 'state': 'Complete',
            'stamp': 'current', 'phase_id': 1}


class ColorPlanTests(unittest.TestCase):
    def test_scope_excludes_grid_floor_and_extraction_identity_only(self):
        report = snapshot()
        report['members'] += [member('grid', 'grid'), member('floor', 'floor'),
                              {'uid': 'unknown', 'extraction': 'Not evaluated'}]
        self.assertEqual({'a', 'b', 'wall'}, set(view.scope_members(report)))

    def test_highest_open_severity_controls_member_not_support(self):
        report = snapshot()
        self.assertEqual({'a': 'Critical', 'b': 'Context', 'wall': 'Context'},
                          view.color_plan(report, report['rows']))

    def test_colors_follow_combined_report_filters_with_context_retained(self):
        report = snapshot()
        selected = filtered_rows(report['rows'], severity='Warning')
        self.assertEqual('Warning', view.color_plan(report, [r.row for r in selected])['a'])
        self.assertEqual({'a': 'Context', 'b': 'Context', 'wall': 'Context'},
                          view.color_plan(report, []))

    def test_acceptance_removes_only_accepted_result_from_color_aggregation(self):
        report = snapshot()
        report['rows'][1]['status'] = 'Accepted exception'
        self.assertEqual('Warning', view.color_plan(report, report['rows'])['a'])
        report['rows'][0]['status'] = 'Accepted exception'
        self.assertEqual('Context', view.color_plan(report, report['rows'])['a'])

    def test_pair_checks_color_both_members_but_no_external_identity(self):
        for check in ('SMR-04', 'SMR-06'):
            report = snapshot()
            result = report['rows'][0]
            result.update(check=check, severity='Error')
            result['related'].append({'uid': 'external', 'id': 99})
            plan = view.color_plan(report, [result])
            self.assertEqual('Error', plan['a'])
            self.assertEqual('Error', plan['b'])
            self.assertNotIn('external', plan)

    def test_pass_remains_neutral_and_unresolved_has_its_own_color(self):
        report = snapshot()
        result = report['rows'][0]
        result['severity'] = 'Pass'
        self.assertEqual('Context', view.color_plan(report, [result])['a'])
        result['severity'] = 'Not evaluated'
        self.assertEqual('Not evaluated', view.color_plan(report, [result])['a'])


class ViewCreationTests(unittest.TestCase):
    def create(self, occupied):
        """Enforce view-name uniqueness at the actual adapter's Name setter."""
        class Collector(list):
            def OfClass(self, kind):
                return self
        class NamedView(object):
            def __init__(self, document, name):
                self.document = document
                self._name = name
                self.IsTemplate = False

            @property
            def Name(self):
                return self._name

            @Name.setter
            def Name(self, value):
                if any(v is not self and v.Name.lower() == value.lower()
                       for v in self.document.views):
                    raise ValueError('Name must be unique. Parameter name: name')
                self._name = value
        document = types.SimpleNamespace(views=[])
        for name in occupied:
            document.views.append(NamedView(document, name))
        # A template participates in the same collision search as any view.
        if document.views:
            document.views[-1].IsTemplate = True
        original = list(document.views)
        new = NamedView(document, '{3D}')
        def create_isometric(doc, type_id):
            doc.views.append(new)
            return new
        family = types.SimpleNamespace(ViewFamily='3D', Id=42)
        view_class = object()
        type_class = object()
        def collector(doc):
            result = Collector()
            result.OfClass = lambda kind: Collector(
                [family] if kind is type_class else doc.views)
            return result
        db = types.SimpleNamespace(FilteredElementCollector=collector,
            View=view_class, ViewFamilyType=type_class,
            ViewFamily=types.SimpleNamespace(ThreeDimensional='3D'),
            View3D=types.SimpleNamespace(CreateIsometric=mock.Mock(side_effect=create_isometric)),
            ElementId=types.SimpleNamespace(InvalidElementId=-1),
            DisplayStyle=types.SimpleNamespace(FlatColors='FlatColors'))
        result = view.create(document, db)
        self.assertIs(new, result)
        self.assertEqual(occupied, [v.Name for v in original])
        self.assertEqual(48, result.Scale)
        db.View3D.CreateIsometric.assert_called_once_with(document, 42)
        return result.Name

    def test_unoccupied_prefixed_name_is_retained(self):
        self.assertEqual('KLA Model Checker - {3D}', self.create([]))

    def test_existing_review_name_gets_numbered_suffix(self):
        self.assertEqual('KLA Model Checker - {3D} (2)',
                          self.create(['KLA Model Checker - {3D}']))

    def test_existing_numbered_suffixes_are_skipped_including_case_only_matches(self):
        self.assertEqual('KLA Model Checker - {3D} (4)', self.create([
            'KLA Model Checker - {3D}', 'KLA Model Checker - {3D} (2)',
            'kla model checker - {3d} (3)']))


class ViewIsolationTests(unittest.TestCase):
    def fixture(self):
        class Collector(list):
            def WhereElementIsNotElementType(self):
                return self
        def element(uid, category, hidden=False, hideable=True):
            return types.SimpleNamespace(UniqueId=uid, Id=types.SimpleNamespace(Value=uid),
                Category=types.SimpleNamespace(Id=types.SimpleNamespace(Value=category)),
                IsHidden=mock.Mock(return_value=hidden), CanBeHidden=mock.Mock(return_value=hideable))
        elements = [element('a', 1, hidden=True), element('unchecked', 1),
                    element('other-wall', 3), element('floor', 9)]
        document = types.SimpleNamespace(Settings=types.SimpleNamespace(Categories=[
            types.SimpleNamespace(Id=types.SimpleNamespace(Value=value)) for value in (1, 2, 3, 9)]))
        db = types.SimpleNamespace(FilteredElementCollector=lambda _doc: Collector(elements),
            BuiltInCategory=types.SimpleNamespace(OST_StructuralFraming=1,
                OST_StructuralColumns=2, OST_Walls=3))
        target = mock.Mock()
        target.CanCategoryBeHidden.return_value = True
        return document, db, target, elements

    def test_only_checked_members_are_unhidden_and_other_scope_members_are_hidden(self):
        document, db, target, elements = self.fixture()
        with mock.patch.object(view, '_ids', side_effect=lambda _db, values: [e.UniqueId for e in values]):
            view.isolate(document, db, target, snapshot())
        target.UnhideElements.assert_called_once_with(['a'])
        target.HideElements.assert_called_once_with(['unchecked', 'other-wall'])
        hidden = dict((call.args[0].Value, call.args[1])
                      for call in target.SetCategoryHidden.call_args_list)
        self.assertEqual({1: False, 2: False, 3: False, 9: True}, hidden)

    def test_unhideable_unchecked_members_cannot_silently_leak_into_isolated_view(self):
        document, db, target, elements = self.fixture()
        elements[1].CanBeHidden.return_value = False
        with self.assertRaisesRegex(ValueError, 'unchecked'):
            view.isolate(document, db, target, snapshot())
        target.HideElements.assert_not_called()
        target.UnhideElements.assert_not_called()


class Hook(object):
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.handlers.remove(handler)
        return self


class Delegate(object):
    def __class_getitem__(cls, kind):
        return lambda handler: handler


class FakeView(object):
    IsTemplate = False
    UniqueId = 'owned-view'
    Id = 100

    def __init__(self):
        self.get_Parameter = mock.Mock()


class Document(object):
    IsValidObject = True

    def __init__(self):
        self.views = {}

    def Equals(self, other):
        return self is other

    def GetElement(self, uid):
        return self.views.get(uid)


def live_scope():
    """Load the actual controller with mocked Revit and WPF boundaries."""
    path = os.path.join(ROOT, 'lib', 'steel_model_review', 'live.py')
    with io.open(path, encoding='utf-8') as stream:
        tree = ast.parse(stream.read(), path)
    tree.body = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    event = mock.Mock()
    event.Raise.return_value = 'Accepted'
    db = types.SimpleNamespace(
        Events=types.SimpleNamespace(DocumentChangedEventArgs=object, DocumentClosingEventArgs=object),
        View3D=FakeView, ElementId=lambda value: value,
        BuiltInParameter=types.SimpleNamespace(VIEW_PHASE=1),
        TransactionStatus=types.SimpleNamespace(Started='Started', Committed='Committed'))
    transaction = mock.Mock()
    transaction.Commit.return_value = 'Committed'
    transaction.GetStatus.return_value = 'Started'
    db.Transaction = mock.Mock(return_value=transaction)
    ui = types.SimpleNamespace(IExternalEventHandler=object,
        Events=types.SimpleNamespace(ViewActivatedEventArgs=object),
        ExternalEvent=types.SimpleNamespace(Create=lambda handler: event))
    graphics = types.SimpleNamespace(scope_members=view.scope_members, color_plan=view.color_plan,
        create=mock.Mock(return_value=FakeView()), isolate=mock.Mock(),
        apply_colors=mock.Mock(), visibility_summary=mock.Mock(return_value='3 members visible'))
    domain = types.SimpleNamespace(CurrentDomain=types.SimpleNamespace(SetData=mock.Mock()))
    window = mock.Mock()
    window.Closed = Hook()
    scope = {'UI': ui, 'DB': db, 'EventHandler': Delegate, 'AppDomain': domain,
             'review_view': graphics, 'ReviewWindow': mock.Mock(return_value=window),
             'forms': mock.Mock()}
    exec(compile(tree, path, 'exec'), scope)
    return scope, event, transaction


class LiveSessionTests(unittest.TestCase):
    def setUp(self):
        self.scope, self.event, self.transaction = live_scope()
        self.document = Document()
        self.application = types.SimpleNamespace(DocumentChanged=Hook(), DocumentClosing=Hook())
        self.uidoc = types.SimpleNamespace(Document=self.document, RequestViewChange=mock.Mock())
        self.uiapp = types.SimpleNamespace(Application=self.application,
                                          ViewActivated=Hook(), ActiveUIDocument=self.uidoc)
        self.callbacks = dict((key, mock.Mock()) for key in
            ('fresh', 'run', 'save', 'navigate', 'grids', 'coverage', 'failure'))
        self.callbacks['fresh'].return_value = True
        self.session = self.scope['ReviewSession'](
            self.uiapp, self.document, 'review.xaml', snapshot(), self.callbacks, 'registry')
        self.window = self.session.window
        self.window.visible_rows.side_effect = lambda: self.session.snapshot['rows']

    def execute(self):
        self.session.Execute(self.uiapp)

    def test_filter_requests_coalesce_and_write_in_external_event_only(self):
        for _i in range(10):
            self.session.request('colors', None)
        self.scope['DB'].Transaction.assert_not_called()
        self.execute()
        self.assertEqual(1, self.scope['DB'].Transaction.call_count)
        self.transaction.Commit.assert_called_once()
        self.scope['review_view'].apply_colors.assert_called_once()
        self.assertFalse(self.session.writing)

    def test_wrong_document_blocks_all_model_mutations_and_review_actions(self):
        self.uiapp.ActiveUIDocument = types.SimpleNamespace(Document=Document())
        self.session.request('accept', self.session.snapshot['rows'][0])
        self.execute()
        self.scope['DB'].Transaction.assert_not_called()
        self.scope['forms'].ask_for_string.assert_not_called()
        self.assertEqual('Open', self.session.snapshot['rows'][0]['status'])

    def test_denied_request_is_not_replayed_on_a_later_filter_change(self):
        self.event.Raise.return_value = 'Denied'
        self.session.request('accept', self.session.snapshot['rows'][0])
        self.assertEqual([], self.session.actions)
        self.event.Raise.return_value = 'Accepted'
        self.session.request('colors', None)
        self.execute()
        self.scope['forms'].ask_for_string.assert_not_called()

    def test_old_row_after_rerun_cannot_be_accepted_in_current_report(self):
        old = self.session.snapshot['rows'][0]
        self.session.snapshot = copy.deepcopy(self.session.snapshot)
        self.session.request('accept', old)
        self.execute()
        self.scope['forms'].ask_for_string.assert_not_called()
        self.assertEqual('Open', self.session.snapshot['rows'][0]['status'])

    def test_graphic_failure_rolls_back_and_reports_without_cache_save(self):
        self.scope['review_view'].apply_colors.side_effect = RuntimeError('graphics failure')
        self.execute()
        self.transaction.RollBack.assert_called_once()
        self.callbacks['failure'].assert_called_once()
        self.callbacks['save'].assert_not_called()
        self.assertFalse(self.session.writing)
        self.assertTrue(self.window.IsEnabled)

    def test_cancelled_rerun_preserves_prior_report_and_view(self):
        old = self.session.snapshot
        self.session.colors_dirty = self.session.scope_dirty = False
        self.callbacks['run'].return_value = {'state': 'Cancelled'}
        self.session.request('rerun', None)
        self.execute()
        self.assertIs(old, self.session.snapshot)
        self.scope['DB'].Transaction.assert_not_called()

    def test_stale_report_cannot_accept_even_if_button_was_previously_enabled(self):
        self.callbacks['fresh'].return_value = False
        result = self.session.snapshot['rows'][0]
        self.session.request('accept', result)
        self.execute()
        self.assertEqual('Open', result['status'])
        self.scope['forms'].ask_for_string.assert_not_called()
        self.window.set_stale.assert_called_with(True)

    def test_own_view_transaction_does_not_mark_model_results_stale(self):
        args = types.SimpleNamespace(GetDocument=lambda: self.document)
        self.session.writing = True
        self.session._changed(None, args)
        self.event.Raise.assert_not_called()
        self.session.writing = False
        self.session._changed(None, args)
        self.event.Raise.assert_called_once()

    def test_close_discards_pending_actions_unsubscribes_and_disposes(self):
        self.session.request('accept', self.session.snapshot['rows'][0])
        self.session._closed(None, None)
        self.execute()
        self.assertTrue(self.session.closed)
        self.assertEqual([], self.application.DocumentChanged.handlers)
        self.assertEqual([], self.application.DocumentClosing.handlers)
        self.assertEqual([], self.uiapp.ViewActivated.handlers)
        self.event.Dispose.assert_called_once()
        self.scope['DB'].Transaction.assert_not_called()

    def test_rerun_updates_same_report_and_requests_scope_refresh(self):
        updated = copy.deepcopy(self.session.snapshot)
        updated['rows'][1]['severity'] = 'Pass'
        self.callbacks['run'].return_value = updated
        self.session.request('rerun', None)
        self.execute()
        self.assertIs(updated, self.session.snapshot)
        self.window.set_snapshot.assert_called_with(updated, False)
        self.scope['review_view'].isolate.assert_called_once()

    def test_close_during_a_nested_dialog_prevents_subsequent_view_writes(self):
        def close_during_rerun(prior):
            self.session._closed(None, None)
            return copy.deepcopy(prior)
        self.callbacks['run'].side_effect = close_during_rerun
        self.session.request('rerun', None)
        self.execute()
        self.assertTrue(self.session.closed)
        self.scope['DB'].Transaction.assert_not_called()

    def test_unchanged_colors_do_not_create_another_transaction(self):
        owned = FakeView()
        self.document.views[owned.UniqueId] = owned
        self.session.view_uid = owned.UniqueId
        self.execute()
        self.scope['DB'].Transaction.reset_mock()
        self.session.request('colors', None)
        self.execute()
        self.scope['DB'].Transaction.assert_not_called()


if __name__ == '__main__':
    unittest.main()
