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
    def __init__(self, template=False, allows_overrides=True):
        self.IsTemplate = template
        self.allows_overrides = allows_overrides
        self.Name = 'Level 1'
        self.Id = FakeElementId(42)

    def AreGraphicsOverridesAllowed(self):
        return self.allows_overrides


class FakeElementId(object):
    def __init__(self, value):
        self.Value = value


class FakeCollector(list):
    def OfClass(self, unused_class):
        return self


class FakeDB(object):
    ViewPlan = object()

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


class FakeSubTransaction(object):
    def __init__(self, document):
        self.document = document
        self.status = None

    def Start(self):
        self.initial_position = self.document.position
        self.initial_marker = self.document.marker
        self.status = FakeTransactionStatus.Started
        return self.status

    def Commit(self):
        self.status = FakeTransactionStatus.Committed
        return self.status

    def RollBack(self):
        self.document.position = self.initial_position
        self.document.marker = self.initial_marker
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


class FakeXYZ(object):
    def __init__(self, x, y, z):
        self.X = x
        self.Y = y
        self.Z = z

    def DotProduct(self, other):
        return self.X * other.X + self.Y * other.Y + self.Z * other.Z


class BeamReactionDeclutterCommandTests(unittest.TestCase):
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
