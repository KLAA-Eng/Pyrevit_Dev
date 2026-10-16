"""Exercise extraction failure and scope contracts with a mocked host boundary."""

import importlib.util
import os
import sys
import types
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
from steel_model_review.engine import Cancelled


def load_host():
    path = os.path.join(ROOT, 'lib', 'steel_model_review', 'host.py')
    module_spec = importlib.util.spec_from_file_location('model_checker_host_test', path)
    module = importlib.util.module_from_spec(module_spec)
    fake_pyrevit = types.ModuleType('pyrevit')
    fake_pyrevit.DB = types.SimpleNamespace()
    with mock.patch.dict(sys.modules, {'pyrevit': fake_pyrevit}):
        module_spec.loader.exec_module(module)
    return module


class HostBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.host = load_host()

    def test_phase_name_does_not_use_descriptor_getvalue(self):
        self.host.DB.Element = types.SimpleNamespace(Name=object())
        phase = types.SimpleNamespace(Name='New Construction')
        self.assertEqual('New Construction', self.host.name(phase))

    def test_none_name_is_empty(self):
        self.assertEqual('', self.host.name(None))

    def test_name_preserves_unicode(self):
        element = types.SimpleNamespace(Name='Niveau \u00e9lev\u00e9')
        self.assertEqual('Niveau \u00e9lev\u00e9', self.host.name(element))

    def test_hidden_type_getter_uses_builtin_type_name(self):
        class HiddenTypeName(object):
            @property
            def Name(self):
                raise AttributeError('unreadable property')
            def get_Parameter(self, parameter_id):
                self.parameter_id = parameter_id
                return types.SimpleNamespace(AsString=lambda: 'W12x26')
        token = object()
        self.host.DB.BuiltInParameter = types.SimpleNamespace(SYMBOL_NAME_PARAM=token)
        element = HiddenTypeName()
        self.assertEqual('W12x26', self.host.name(element))
        self.assertIs(token, element.parameter_id)

    def test_unavailable_name_is_not_silently_fabricated(self):
        self.host.DB.BuiltInParameter = types.SimpleNamespace(SYMBOL_NAME_PARAM=1)
        element = types.SimpleNamespace(get_Parameter=lambda _key: None)
        with self.assertRaises(AttributeError):
            self.host.name(element)

    def test_inches_conversion_preserves_small_offsets(self):
        value = self.host.point(types.SimpleNamespace(X=1.0 / 384, Y=2, Z=-3))
        self.assertEqual((1.0 / 32, 24, -36), value)

    def test_phase_and_option_filtering(self):
        self.host.DB.ElementOnPhaseStatus = types.SimpleNamespace(
            New='new', Existing='existing')
        element = types.SimpleNamespace(
            DesignOption=None, HasPhases=lambda: True,
            GetPhaseStatus=lambda phase: 'existing')
        self.assertTrue(self.host.in_scope(element, 'phase', []))
        element.GetPhaseStatus = lambda phase: 'demolished'
        self.assertFalse(self.host.in_scope(element, 'phase', []))
        element.GetPhaseStatus = lambda phase: 'new'
        element.DesignOption = types.SimpleNamespace(Id=types.SimpleNamespace(Value=42))
        self.assertFalse(self.host.in_scope(element, 'phase', [43]))
        self.assertTrue(self.host.in_scope(element, 'phase', [42]))

    def test_datums_without_phases_remain_eligible(self):
        element = types.SimpleNamespace(DesignOption=None, HasPhases=lambda: False)
        self.assertTrue(self.host.in_scope(element, 'phase', []))

    def test_material_classification_does_not_guess_from_name(self):
        element = types.SimpleNamespace(StructuralMaterialType='Generic', Name='Steel W12')
        self.assertEqual('unknown', self.host.classification(element, 'beam'))
        element.StructuralMaterialType = 'Steel'
        self.assertEqual('steel', self.host.classification(element, 'beam'))
        element.StructuralMaterialType = 'Aluminum'
        self.assertEqual('other', self.host.classification(element, 'beam'))

    def test_original_geometry_is_transformed_once(self):
        class Solid(object):
            Volume = 1
            Faces = []
            Edges = []
        class GeometryInstance(object):
            pass
        class PlanarFace(object):
            pass
        self.host.DB.Options = types.SimpleNamespace
        self.host.DB.ViewDetailLevel = types.SimpleNamespace(Fine='Fine')
        self.host.DB.Solid = Solid
        self.host.DB.GeometryInstance = GeometryInstance
        self.host.DB.PlanarFace = PlanarFace
        geometry = mock.Mock()
        geometry.GetTransformed.return_value = [Solid()]
        element = mock.Mock()
        element.GetOriginalGeometry.return_value = geometry
        transform = object()
        element.GetTransform.return_value = transform
        self.host._geometry(element, 'beam')
        geometry.GetTransformed.assert_called_once_with(transform)
        element.get_Geometry.assert_not_called()
        options = element.GetOriginalGeometry.call_args[0][0]
        self.assertFalse(options.ComputeReferences)

    def test_failed_element_is_visible_and_does_not_stop_next_member(self):
        bad, good = object(), object()
        self.host._record = lambda element, kind: {
            'uid': 'bad' if element is bad else 'good',
            'id': 1 if element is bad else 2, 'type': 10,
            'kind': kind, 'name': 'member', 'level': 'L1'}
        self.host.in_scope = lambda *args: True
        def classify(element, kind):
            if element is bad:
                raise RuntimeError('Missing material asset.')
            return 'steel'
        self.host.classification = classify
        self.host.extract = lambda element, kind: {'uid': 'good'}
        records, grids, coverage, rows = self.host.extract_model(
            None, [(bad, 'column'), (good, 'column')], None, [], {},
            ['SMR-03'], lambda *args: None)
        self.assertEqual([{'uid': 'good', 'classification': {
            'material': 'steel', 'reviewed_override': False}}], records)
        self.assertEqual(['Failed', 'Eligible'], [r[2] for r in coverage])
        self.assertEqual('Not evaluated', rows[0]['severity'])
        self.assertIn('Missing material asset', rows[0]['reason'])

    def test_unknown_material_retains_unresolved_coverage(self):
        element = object()
        self.host._record = lambda *args: {'uid': 'a', 'id': 1, 'type': 10}
        self.host.in_scope = lambda *args: True
        self.host.classification = lambda *args: 'unknown'
        records, grids, coverage, rows = self.host.extract_model(
            None, [(element, 'column')], None, [], {}, ['SMR-03'],
            lambda *args: None)
        self.assertEqual([], records)
        self.assertEqual('Unsupported', coverage[0][2])
        self.assertEqual('Not evaluated', rows[0]['severity'])

    def test_extraction_cancel_is_not_converted_to_element_error(self):
        def cancel(*args):
            raise Cancelled()
        with self.assertRaises(Cancelled):
            self.host.extract_model(None, [(object(), 'beam')], None, [], {},
                                    ['SMR-01'], cancel)


if __name__ == '__main__':
    unittest.main()
