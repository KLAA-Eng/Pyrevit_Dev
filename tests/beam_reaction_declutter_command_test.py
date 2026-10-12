from __future__ import print_function

import importlib.util
import os
import sys
import types
import unittest

from repo_paths import TAB_NAME


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMAND_PATH = os.path.join(
    PROJECT_ROOT,
    TAB_NAME,
    '05 DevSandbox.panel',
    'Prototype.pulldown',
    'Beam Reaction Declutter.pushbutton',
    'script.py',
)


def load_command_module():
    """Load the command while replacing host-only pyRevit modules."""
    pyrevit = types.ModuleType('pyrevit')
    pyrevit.DB = object()
    pyrevit.forms = object()
    pyrevit.revit = object()
    pyrevit.script = object()
    gui = types.ModuleType('GUI')
    gui_forms = types.ModuleType('GUI.forms')
    gui_forms.select_from_dict = lambda *args, **kwargs: []

    old_modules = {
        name: sys.modules.get(name)
        for name in ('pyrevit', 'GUI', 'GUI.forms')
    }
    sys.modules['pyrevit'] = pyrevit
    sys.modules['GUI'] = gui
    sys.modules['GUI.forms'] = gui_forms
    library_path = os.path.join(PROJECT_ROOT, 'lib')
    sys.path.insert(0, library_path)
    try:
        spec = importlib.util.spec_from_file_location(
            'beam_reaction_declutter_command_test_module', COMMAND_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, previous in old_modules.items():
            if previous is None:
                del sys.modules[name]
            else:
                sys.modules[name] = previous
        sys.path.remove(library_path)


class FakeApplication(object):
    def __init__(self, version_number):
        self.VersionNumber = version_number


class FakeDocument(object):
    def __init__(self, version_number):
        self.Application = FakeApplication(version_number)


class FakeView(object):
    def __init__(self, template=False, allows_overrides=True, value=42):
        self.IsTemplate = template
        self.allows_overrides = allows_overrides
        self.Name = 'Level 1'
        self.Id = FakeElementId(value)

    def AreGraphicsOverridesAllowed(self):
        return self.allows_overrides


class FakeElementId(object):
    def __init__(self, value):
        self.Value = value


class FakeCollector(list):
    def OfClass(self, unused_class):
        return self

    def WhereElementIsNotElementType(self):
        return self


class FakeDB(object):
    ViewPlan = FakeView

    def __init__(self, views):
        self.views = views

    def FilteredElementCollector(self, unused_document):
        return FakeCollector(self.views)


class FakeColor(object):
    def __init__(self, red, green, blue):
        self.Red = red
        self.Green = green
        self.Blue = blue


class FakeOverride(object):
    def __init__(self, color):
        self.ProjectionLineColor = color


class FakeTransactionStatus(object):
    Started = 'started'
    Committed = 'committed'
    RolledBack = 'rolled back'


class FakeOuterTransaction(object):
    def __init__(self, document, name):
        self.document = document
        self.name = name
        self.status = None
        self.disposed = False
        self.calls = []
        document.outer_transaction = self

    def Start(self):
        self.calls.append('start')
        self.status = FakeTransactionStatus.Started
        return self.status

    def Commit(self):
        self.calls.append('commit')
        self.status = getattr(self.document, 'commit_result',
                              FakeTransactionStatus.Committed)
        return self.status

    def RollBack(self):
        self.calls.append('rollback')
        self.status = FakeTransactionStatus.RolledBack
        return self.status

    def GetStatus(self):
        if self.disposed:
            raise RuntimeError('The managed object is not valid')
        self.calls.append('status')
        return self.status

    def Dispose(self):
        self.calls.append('dispose')
        self.disposed = True


class FakeSubTransaction(object):
    def __init__(self, document):
        self.document = document
        self.status = None

    def Start(self):
        self.initial_position = self.document.position
        self.initial_marker = self.document.marker
        self.initial_overrides = dict(getattr(self.document, 'overrides', {}))
        self.status = FakeTransactionStatus.Started
        return self.status

    def Commit(self):
        self.status = FakeTransactionStatus.Committed
        return self.status

    def RollBack(self):
        self.document.position = self.initial_position
        self.document.marker = self.initial_marker
        if hasattr(self.document, 'overrides'):
            self.document.overrides.clear()
            self.document.overrides.update(self.initial_overrides)
        self.status = FakeTransactionStatus.RolledBack
        return self.status

    def GetStatus(self):
        return self.status

    def Dispose(self):
        pass


class FakeBadRollback(FakeSubTransaction):
    def RollBack(self):
        return FakeTransactionStatus.Started


class FakeMovingDocument(object):
    def __init__(self, regeneration_error=None):
        self.position = 0.0
        self.marker = None
        self.regenerations = 0
        self.regeneration_error = regeneration_error

    def Regenerate(self):
        self.regenerations += 1
        if self.regeneration_error:
            raise self.regeneration_error


class FakeMover(object):
    @staticmethod
    def MoveElement(document, unused_id, vector):
        document.position += vector


class FakeLine(object):
    IsBound = True


class FakeLocationCurve(object):
    def __init__(self, curve):
        self.Curve = curve


class FakeLink(object):
    pass


class FakeSheet(object):
    def __init__(self, value, placed, placeholder=False):
        self.Id = FakeElementId(value)
        self.SheetNumber = 'S{}'.format(value)
        self.Name = 'Sheet {}'.format(value)
        self.IsPlaceholder = placeholder
        self.placed = placed

    def GetAllPlacedViews(self):
        return [FakeElementId(value) for value in self.placed]


class FakeXYZ(object):
    def __init__(self, x, y, z):
        self.X = x
        self.Y = y
        self.Z = z

    def DotProduct(self, other):
        return self.X * other.X + self.Y * other.Y + self.Z * other.Z


class BeamReactionDeclutterCommandTests(unittest.TestCase):
    def test_outer_transaction_commit_is_checked_before_disposal(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(
            Transaction=FakeOuterTransaction,
            TransactionStatus=FakeTransactionStatus,
        )
        document = types.SimpleNamespace()
        expected = [{'view': object(), 'issues': []}]
        command._move_views = lambda unused_doc, unused_views: expected

        result = command._process_action(
            document, command.MOVE_ACTIVE_ACTION, [object()])

        self.assertIs(expected, result)
        self.assertEqual(['start', 'commit', 'dispose'],
                         document.outer_transaction.calls)

    def test_outer_transaction_rolls_back_a_processing_error(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(
            Transaction=FakeOuterTransaction,
            TransactionStatus=FakeTransactionStatus,
        )
        document = types.SimpleNamespace()
        command._move_views = lambda *args: (_ for _ in ()).throw(
            RuntimeError('processing failed'))

        with self.assertRaisesRegex(RuntimeError, 'processing failed'):
            command._process_action(
                document, command.MOVE_SHEETS_ACTION, [object()])

        self.assertEqual(['start', 'status', 'rollback', 'dispose'],
                         document.outer_transaction.calls)

    def test_outer_transaction_does_not_report_a_failed_commit_as_success(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(
            Transaction=FakeOuterTransaction,
            TransactionStatus=FakeTransactionStatus,
        )
        document = types.SimpleNamespace(commit_result=FakeTransactionStatus.RolledBack)
        command._clear_view = lambda unused_doc, view: {'view': view, 'issues': []}

        with self.assertRaisesRegex(RuntimeError, 'did not commit'):
            command._process_action(document, command.CLEAR_ACTION, [object()])

        self.assertEqual(['start', 'commit', 'status', 'dispose'],
                         document.outer_transaction.calls)

    def test_requires_revit_2024_or_newer(self):
        command = load_command_module()

        self.assertTrue(command._is_supported_revit_version(FakeDocument('2024')))
        self.assertTrue(command._is_supported_revit_version(FakeDocument('2026')))
        self.assertFalse(command._is_supported_revit_version(FakeDocument('2023')))
        self.assertFalse(command._is_supported_revit_version(FakeDocument('unknown')))

    def test_eligible_plan_views_excludes_templates_and_unsupported_views(self):
        command = load_command_module()
        expected = FakeView()
        command.DB = FakeDB([expected, FakeView(template=True), FakeView(False, False)])

        self.assertEqual([expected], command._eligible_plan_views(object()))

    def test_cancelled_view_selection_returns_an_empty_scope(self):
        command = load_command_module()
        command._eligible_plan_views = lambda document: [FakeView()]
        command.select_from_dict = lambda *args, **kwargs: []

        self.assertEqual([], command._select_plan_views(object()))

    def test_action_switch_has_both_move_scopes(self):
        command = load_command_module()
        shown = []
        command.forms = types.SimpleNamespace(CommandSwitchWindow=types.SimpleNamespace(
            show=lambda choices, **kwargs: shown.extend(choices) or command.MOVE_ACTIVE_ACTION))

        self.assertEqual(command.MOVE_ACTIVE_ACTION, command._select_action())
        self.assertEqual([
            'Move (Active View)', 'Move (Select Sheets)',
            'Clear Matching Red Overrides', 'Cancel',
        ], shown)

    def test_active_plan_view_runs_without_another_picker(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(ViewPlan=FakeView, ViewSheet=FakeSheet)
        plan = FakeView(value=10)

        self.assertEqual([plan], command._active_plan_views(
            types.SimpleNamespace(ActiveView=plan)))

    def test_active_sheet_uses_only_eligible_placed_plan_views(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(ViewPlan=FakeView, ViewSheet=FakeSheet)
        plan = FakeView(value=10)
        template = FakeView(template=True, value=11)
        sheet = FakeSheet(20, [10, 10, 11, 12])
        elements = {10: plan, 11: template, 12: object()}
        document = types.SimpleNamespace(
            ActiveView=sheet,
            GetElement=lambda element_id: elements[element_id.Value],
        )

        self.assertEqual([plan], command._active_plan_views(document))

    def test_selected_sheets_collect_distinct_placed_plans(self):
        command = load_command_module()
        first = FakeView(value=10)
        second = FakeView(value=11)
        sheets = [FakeSheet(20, [10, 11]), FakeSheet(21, [10, 12]),
                  FakeSheet(22, [11], placeholder=True)]
        command.DB = types.SimpleNamespace(
            ViewPlan=FakeView,
            ViewSheet=FakeSheet,
            FilteredElementCollector=lambda unused_doc: FakeCollector(sheets),
        )
        selected_options = []
        command.select_from_dict = lambda options, **kwargs: (
            selected_options.extend(options.values()) or sheets[:2])
        elements = {10: first, 11: second, 12: object()}
        document = types.SimpleNamespace(
            GetElement=lambda element_id: elements[element_id.Value])

        self.assertEqual([first, second], command._select_sheet_plan_views(document))
        self.assertEqual(sheets[:2], selected_options)

    def test_sheet_without_plan_stops_before_a_transaction(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(ViewPlan=FakeView, ViewSheet=FakeSheet)
        sheet = FakeSheet(20, [])
        command._stop = lambda message: (_ for _ in ()).throw(ValueError(message))

        with self.assertRaisesRegex(ValueError, 'no eligible plan views'):
            command._active_plan_views(types.SimpleNamespace(ActiveView=sheet))

    def test_selected_sheets_without_plan_stop_before_a_transaction(self):
        command = load_command_module()
        sheet = FakeSheet(20, [])
        command.DB = types.SimpleNamespace(
            ViewPlan=FakeView,
            ViewSheet=FakeSheet,
            FilteredElementCollector=lambda unused_doc: FakeCollector([sheet]),
        )
        command.select_from_dict = lambda *args, **kwargs: [sheet]
        command._stop = lambda message: (_ for _ in ()).throw(ValueError(message))

        with self.assertRaisesRegex(ValueError, 'no eligible plan views'):
            command._select_sheet_plan_views(
                types.SimpleNamespace(GetElement=lambda unused_id: None))

    def test_reset_recognizes_only_the_exact_source_marker(self):
        command = load_command_module()

        self.assertTrue(command._source_marker_override(FakeOverride(FakeColor(254, 0, 0))))
        self.assertFalse(command._source_marker_override(FakeOverride(FakeColor(255, 0, 0))))
        self.assertFalse(command._source_marker_override(FakeOverride(FakeColor(254, 1, 0))))

    def test_own_beam_is_not_considered_a_blocker(self):
        command = load_command_module()
        tag = types.SimpleNamespace(Id=FakeElementId(1))
        own_beam = types.SimpleNamespace(Id=FakeElementId(2))
        other = types.SimpleNamespace(Id=FakeElementId(3))
        command._bounds = lambda unused_element, unused_view: (0.0, 0.0, 1.0, 1.0)

        tag_bounds, blockers = command._blocker_bounds(
            object(), object(), tag, [tag, own_beam, other], beam_id=2)

        self.assertEqual((0.0, 0.0, 1.0, 1.0), tag_bounds)
        self.assertEqual([other], [element for element, unused_bounds in blockers])

    def test_conflicts_include_annotations_and_structural_members_only(self):
        command = load_command_module()
        categories = {
            'tag': (20, 'annotation'),
            'dimension': (21, 'annotation'),
            'framing': (10, 'model'),
            'column': (11, 'model'),
            'detail': (12, 'model'),
            'floor': (30, 'model'),
            'beam_system': (31, 'model'),
            'camera': (32, 'model'),
            'section_box': (40, 'annotation'),
            'grid': (41, 'annotation'),
            'elevation': (42, 'annotation'),
        }
        elements = [types.SimpleNamespace(
            name=name,
            Category=types.SimpleNamespace(
                Id=FakeElementId(category_id), CategoryType=category_type))
            for name, (category_id, category_type) in categories.items()]
        command.DB = types.SimpleNamespace(
            BuiltInCategory=types.SimpleNamespace(
                OST_StructuralFraming=10,
                OST_StructuralColumns=11,
                OST_DetailComponents=12,
                OST_SectionBox=40,
                OST_Grids=41,
                OST_Elev=42,
            ),
            CategoryType=types.SimpleNamespace(Annotation='annotation'),
            FilteredElementCollector=lambda unused_doc, unused_view: FakeCollector(elements),
        )

        filtered = command._visible_elements(object(), FakeView())

        self.assertEqual(
            {'tag', 'dimension', 'framing', 'column', 'detail'},
            {element.name for element in filtered})

    def test_tagged_beam_requires_one_local_straight_structural_reference(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(
            RevitLinkInstance=FakeLink,
            LocationCurve=FakeLocationCurve,
            Line=FakeLine,
            BuiltInCategory=types.SimpleNamespace(OST_StructuralFraming=10),
        )
        straight = types.SimpleNamespace(
            Id=FakeElementId(2),
            Category=types.SimpleNamespace(Id=FakeElementId(10)),
            Location=FakeLocationCurve(FakeLine()),
        )
        curved = types.SimpleNamespace(
            Id=FakeElementId(3),
            Category=types.SimpleNamespace(Id=FakeElementId(10)),
            Location=FakeLocationCurve(object()),
        )
        document = types.SimpleNamespace(
            GetElement=lambda element_id: {2: straight, 3: curved, 4: FakeLink()}[element_id.Value])
        tag = types.SimpleNamespace(
            GetTaggedReferences=lambda: [types.SimpleNamespace(ElementId=FakeElementId(2))])

        self.assertIs(straight, command._tagged_beam(document, tag)[0])
        tag.GetTaggedReferences = lambda: []
        self.assertIn('exactly one', command._tagged_beam(document, tag)[1])
        tag.GetTaggedReferences = lambda: [types.SimpleNamespace(ElementId=FakeElementId(2))] * 2
        self.assertIn('exactly one', command._tagged_beam(document, tag)[1])
        tag.GetTaggedReferences = lambda: [types.SimpleNamespace(ElementId=FakeElementId(3))]
        self.assertIn('Curved', command._tagged_beam(document, tag)[1])
        tag.GetTaggedReferences = lambda: [types.SimpleNamespace(ElementId=FakeElementId(4))]
        self.assertIn('Linked', command._tagged_beam(document, tag)[1])

    def test_view_bounds_follow_a_rotated_plan_axis(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(XYZ=FakeXYZ)
        box = types.SimpleNamespace(
            Min=FakeXYZ(2, 5, 0), Max=FakeXYZ(4, 8, 0),
            Transform=types.SimpleNamespace(OfPoint=lambda point: point),
        )
        element = types.SimpleNamespace(get_BoundingBox=lambda unused_view: box)
        view = types.SimpleNamespace(
            RightDirection=FakeXYZ(0, 1, 0),
            UpDirection=FakeXYZ(-1, 0, 0),
        )

        self.assertEqual((5, -4, 8, -2), command._bounds(element, view))

    def test_remaining_deferred_overlap_is_labeled_unresolved(self):
        command = load_command_module()
        tag = types.SimpleNamespace(Id=FakeElementId(1))
        blocker = types.SimpleNamespace(Id=FakeElementId(2))
        command._reaction_tags = lambda unused_doc, unused_view: [tag]
        command._visible_elements = lambda unused_doc, unused_view: [tag, blocker]
        command._declutter_tag = lambda *args: ('deferred', 'Center tag kept stationary')
        command._tag_data = lambda *args: ({'beam_id': 3}, None)
        command._bounds = lambda *args: (0, 0, 1, 1)

        result = command._move_view(object(), object())

        self.assertEqual('Unresolved', result['issues'][0][0])
        self.assertEqual(1, result['issues'][0][1])

    def test_shared_tag_is_planned_once_across_selected_views(self):
        command = load_command_module()
        tag = types.SimpleNamespace(Id=FakeElementId(1))
        views = [FakeView(value=10), FakeView(value=11)]
        calls = []
        command._reaction_tags = lambda unused_doc, unused_view: [tag]
        command._visible_elements = lambda unused_doc, unused_view: [tag]
        command._declutter_tag = lambda *args: calls.append(args[-1]) or ('moved', '')
        command._tag_data = lambda *args: ({'beam_id': 2}, None)
        command._blocker_bounds = lambda *args: ((0, 0, 1, 1), [])

        results = command._move_views(object(), views)

        self.assertEqual(1, len(calls))
        self.assertEqual(2, len(calls[0]))
        self.assertEqual([], [issue for result in results for issue in result['issues']])

    def test_shared_tag_failure_is_reported_in_each_overlapping_view(self):
        command = load_command_module()
        tag = types.SimpleNamespace(Id=FakeElementId(1))
        blocker = types.SimpleNamespace(Id=FakeElementId(2))
        views = [FakeView(value=10), FakeView(value=11)]
        command._reaction_tags = lambda unused_doc, unused_view: [tag]
        command._visible_elements = lambda unused_doc, unused_view: [tag, blocker]
        command._declutter_tag = lambda *args: ('unresolved', 'Eight-step cap')
        command._tag_data = lambda *args: ({'beam_id': 3}, None)
        command._bounds = lambda *args: (0, 0, 1, 1)

        results = command._move_views(object(), views)

        self.assertEqual([10, 11], [result['view'].Id.Value for result in results])
        self.assertEqual([1, 1], [result['issues'][0][1] for result in results])
        self.assertTrue(all('Eight-step cap' in result['issues'][0][2]
                            for result in results))

    def test_failed_final_clearance_rolls_back_the_tag(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(
            SubTransaction=FakeSubTransaction,
            TransactionStatus=FakeTransactionStatus,
            ElementTransformUtils=FakeMover,
        )
        document = FakeMovingDocument()
        tag = types.SimpleNamespace(Id=FakeElementId(1))
        command._blocker_bounds = lambda unused_doc, unused_view, unused_tag, unused_elements, unused_id: (
            (document.position, 0.0, document.position + 0.2, 1.0),
            [(object(), (0.1, 0.0, 0.8, 1.0))],
        )

        moved, reason = command._move_tag(
            document, object(), tag, [], beam_id=2, vector=0.4)

        self.assertFalse(moved)
        self.assertIn('Collision remains', reason)
        self.assertEqual(0.0, document.position)
        self.assertEqual(2, document.regenerations)

    def test_move_failure_is_reported_after_successful_rollback(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(
            SubTransaction=FakeSubTransaction,
            TransactionStatus=FakeTransactionStatus,
            ElementTransformUtils=types.SimpleNamespace(
                MoveElement=lambda *args: (_ for _ in ()).throw(RuntimeError('move rejected'))),
        )
        document = FakeMovingDocument()
        tag = types.SimpleNamespace(Id=FakeElementId(1))

        moved, reason = command._move_tag(document, object(), tag, [], beam_id=2, vector=0.4)

        self.assertFalse(moved)
        self.assertIn('move rejected', reason)
        self.assertEqual(0.0, document.position)
        self.assertEqual(1, document.regenerations)

    def test_failed_rollback_aborts_the_action(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(
            SubTransaction=FakeBadRollback,
            TransactionStatus=FakeTransactionStatus,
            ElementTransformUtils=types.SimpleNamespace(
                MoveElement=lambda *args: (_ for _ in ()).throw(RuntimeError('move rejected'))),
        )
        document = FakeMovingDocument()
        tag = types.SimpleNamespace(Id=FakeElementId(1))

        with self.assertRaisesRegex(RuntimeError, 'subtransaction ended with status'):
            command._move_tag(document, object(), tag, [], beam_id=2, vector=0.4)

    def test_marker_failure_rolls_back_the_tag(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(
            SubTransaction=FakeSubTransaction,
            TransactionStatus=FakeTransactionStatus,
            ElementTransformUtils=FakeMover,
        )
        document = FakeMovingDocument()
        tag = types.SimpleNamespace(Id=FakeElementId(1))
        view = types.SimpleNamespace(SetElementOverrides=lambda *args: (_ for _ in ()).throw(
            RuntimeError('marker failed')))
        command._blocker_bounds = lambda unused_doc, unused_view, unused_tag, unused_elements, unused_id: (
            (document.position, 0.0, document.position + 0.2, 1.0), [],
        )
        command._fresh_marker_override = lambda: object()

        moved, reason = command._move_tag(
            document, view, tag, [], beam_id=2, vector=0.4)

        self.assertFalse(moved)
        self.assertIn('marker failed', reason)
        self.assertEqual(0.0, document.position)
        self.assertIsNone(document.marker)

    def test_shared_tag_marker_failure_rolls_back_all_selected_views(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(
            SubTransaction=FakeSubTransaction,
            TransactionStatus=FakeTransactionStatus,
            ElementTransformUtils=FakeMover,
        )
        document = FakeMovingDocument()
        document.overrides = {}
        tag = types.SimpleNamespace(Id=FakeElementId(1))
        first_view = types.SimpleNamespace(
            SetElementOverrides=lambda unused_id, unused_settings: document.overrides.update({10: True}),
            GetElementOverrides=lambda unused_id: FakeOverride(FakeColor(
                254 if document.overrides.get(10) else 0, 0, 0)),
        )
        second_view = types.SimpleNamespace(SetElementOverrides=lambda *args: (_ for _ in ()).throw(
            RuntimeError('second view marker failed')))
        command._blocker_bounds = lambda *args: ((document.position, 0, document.position + 0.2, 1), [])
        command._fresh_marker_override = lambda: object()

        moved, reason = command._move_tag(
            document, first_view, tag, [], beam_id=2, vector=0.4,
            view_contexts=[(first_view, [], 2), (second_view, [], 2)])

        self.assertFalse(moved)
        self.assertIn('second view marker failed', reason)
        self.assertEqual(0.0, document.position)
        self.assertEqual({}, document.overrides)

    def test_move_rolls_back_if_marker_does_not_take_effect(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(
            SubTransaction=FakeSubTransaction,
            TransactionStatus=FakeTransactionStatus,
            ElementTransformUtils=FakeMover,
        )
        document = FakeMovingDocument()
        tag = types.SimpleNamespace(Id=FakeElementId(1))
        view = types.SimpleNamespace(
            SetElementOverrides=lambda *args: None,
            GetElementOverrides=lambda *args: FakeOverride(FakeColor(0, 0, 0)),
        )
        command._blocker_bounds = lambda *args: ((document.position, 0, document.position + 0.2, 1), [])
        command._fresh_marker_override = lambda: object()

        moved, reason = command._move_tag(document, view, tag, [], beam_id=2, vector=0.4)

        self.assertFalse(moved)
        self.assertIn('not applied', reason)
        self.assertEqual(0.0, document.position)

    def test_regeneration_failure_aborts_after_tag_rollback(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(
            SubTransaction=FakeSubTransaction,
            TransactionStatus=FakeTransactionStatus,
            ElementTransformUtils=FakeMover,
        )
        document = FakeMovingDocument(RuntimeError('regeneration failed'))
        tag = types.SimpleNamespace(Id=FakeElementId(1))

        with self.assertRaisesRegex(RuntimeError, 'regeneration failed'):
            command._move_tag(document, object(), tag, [], beam_id=2, vector=0.4)
        self.assertEqual(0.0, document.position)

    def test_successful_run_does_not_open_detailed_output(self):
        command = load_command_module()
        command.script = types.SimpleNamespace(
            get_output=lambda: self.fail('output must stay closed on success'))

        command._print_report('Move', [{'view': object(), 'issues': []}])

    def test_clear_reports_a_red_override_that_remains(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(
            SubTransaction=FakeSubTransaction,
            TransactionStatus=FakeTransactionStatus,
            OverrideGraphicSettings=object,
        )
        document = FakeMovingDocument()
        tag = types.SimpleNamespace(Id=FakeElementId(1))
        command._reaction_tags = lambda unused_document, unused_view: [tag]
        view = types.SimpleNamespace(
            GetElementOverrides=lambda unused_id: FakeOverride(FakeColor(254, 0, 0)),
            SetElementOverrides=lambda unused_id, unused_settings: None,
        )

        result = command._clear_view(document, view)

        self.assertEqual('Failed', result['issues'][0][0])
        self.assertIn('remains', result['issues'][0][2])

    def test_clear_succeeds_silently_when_matching_red_is_removed(self):
        command = load_command_module()
        command.DB = types.SimpleNamespace(
            SubTransaction=FakeSubTransaction,
            TransactionStatus=FakeTransactionStatus,
            OverrideGraphicSettings=object,
        )
        document = FakeMovingDocument()
        tag = types.SimpleNamespace(Id=FakeElementId(1))
        command._reaction_tags = lambda unused_document, unused_view: [tag]
        marker = {'color': FakeColor(254, 0, 0)}
        view = types.SimpleNamespace(
            GetElementOverrides=lambda unused_id: FakeOverride(marker['color']),
            SetElementOverrides=lambda unused_id, unused_settings: marker.update(color=FakeColor(0, 0, 0)),
        )

        self.assertEqual([], command._clear_view(document, view)['issues'])


if __name__ == '__main__':
    unittest.main()
