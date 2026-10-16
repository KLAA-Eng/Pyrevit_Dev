"""Validate reviewed connection categories, record linkage and attachment evidence."""

import json
import os
import sys
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))

from steel_model_review import evidence
from steel_model_review.connections import beam_target, column_faces, crossing_relationship
from steel_model_review.engine import DEFAULTS, assemble_report, endpoint_checks, evaluate
from steel_model_review.geometry import SpatialIndex
from steel_model_review.reporting import evidence_text, filtered_rows
from steel_model_review_test import member


def side_face(x, low=0, high=100):
    return ((1, 0, 0), (x, 0, 0), [[(x, -10, low), (x, 10, low),
                                     (x, 10, high), (x, -10, high)]])


class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.a = member()
        self.settings = dict(DEFAULTS)

    def target(self, b):
        return beam_target(self.a, 1, b, self.settings)

    def test_girder_corner_and_skew(self):
        girder = member('b', start=(100, -50, 0), end=(100, 50, 0))
        self.assertEqual('Girder connection', self.target(girder)['category'])
        girder['start'] = (100, 0, 0)
        self.assertEqual('Corner/End', self.target(girder)['category'])
        girder['start'], girder['end'] = (50, -50, 0), (150, 50, 0)
        self.assertEqual('Girder connection', self.target(girder)['category'])

    def test_splice_reversed_endpoints_and_shortfall(self):
        b = member('b', start=(200, 0, 0), end=(100, 0, 0))
        self.assertEqual('Splice connection', self.target(b)['category'])
        b['end'] = (100.03125, 0, 0)
        self.assertEqual('Splice connection', self.target(b)['category'])

    def test_parallel_side_by_side_and_overlapping_spans_are_not_splices(self):
        for start, end in (((100, 1, 0), (200, 1, 0)), ((50, 0, 0), (150, 0, 0)),
                           ((0, 0, 0), (100, 0, 0))):
            self.assertIsNone(self.target(member('b', start=start, end=end)))

    def test_unique_exact_target_beats_nearby_candidate(self):
        exact = member('exact', start=(100, -50, 0), end=(100, 50, 0))
        near = member('near', start=(101, -50, 0), end=(101, 50, 0))
        rows = endpoint_checks(self.a, SpatialIndex([self.a, exact, near]), self.settings)
        ends = [r for r in rows if r['check'] == 'SMR-01' and r['end'] == 1]
        self.assertEqual(1, len(ends))
        self.assertEqual('Pass', ends[0]['severity'])
        self.assertEqual('exact', ends[0]['related'][0]['uid'])

    def test_multiple_near_misses_are_still_ambiguous(self):
        supports = [member(str(x), start=(x, -50, 0), end=(x, 50, 0)) for x in (101, 102)]
        rows = endpoint_checks(self.a, SpatialIndex([self.a] + supports), self.settings)
        self.assertEqual('Ambiguous candidates', [r for r in rows if r['end'] == 1][0]['category'])

    def test_actual_joint_keeps_all_relationships_and_join_evidence(self):
        a = member('girder', start=(100, -50, 0), end=(100, 50, 0))
        b = member('splice', start=(100, 0, 0), end=(200, 0, 0))
        self.a['joins'] = {'1': {'state': 'Read', 'allowed': False, 'participants': []}}
        relations = []
        rows = endpoint_checks(self.a, SpatialIndex([self.a, a, b]), self.settings, relations)
        ends = [r for r in rows if r['end'] == 1 and r['check'] == 'SMR-01']
        self.assertEqual({'Girder connection', 'Splice connection'}, set(r['category'] for r in ends))
        self.assertTrue(all(r['severity'] == 'Pass' for r in ends))
        self.assertEqual(False, [r for r in relations if r['end'] == 1][0]['evidence']['join']['allowed'])

    def test_column_axis_and_reference_face_distances_are_independent(self):
        column = member('col', 'column', (105, 0, 0), (105, 0, 100), 0, 100)
        column['faces'] += [side_face(100), side_face(110)]
        column['web_normals'] = [(1, 0, 0)]
        column['web_planes'] = [((1, 0, 0), (100, 0, 0))]
        rows = endpoint_checks(self.a, SpatialIndex([self.a, column]), self.settings)
        ends = [r for r in rows if r['end'] == 1 and r['check'] == 'SMR-01']
        by_category = dict((r['category'], r) for r in ends)
        self.assertEqual(5, by_category['Column Axis']['value'])
        self.assertEqual(0, by_category['Column Web Face']['value'])
        self.assertEqual('Information', by_category['Column Web Face']['severity'])

    def test_large_column_face_can_be_exact_outside_axis_search(self):
        column = member('col', 'column', (120, 0, 0), (120, 0, 100), 0, 100)
        column['faces'] += [side_face(100), side_face(140)]
        column['bounds'] = ((100, -10, 0), (140, 10, 100))
        rows = endpoint_checks(self.a, SpatialIndex([self.a, column]), self.settings)
        self.assertTrue(any(r['category'] == 'Column Section Face' and r['value'] == 0
                            for r in rows if r['end'] == 1))

    def test_rotated_column_face_uses_world_geometry(self):
        column = member('col', 'column', (105, 0, 0), (105, 0, 100), 0, 100)
        column['faces'] = [((1, 1, 0), (100, 0, 0),
                           [[(90, 10, 0), (110, -10, 0), (110, -10, 100), (90, 10, 100)]])]
        result = column_faces(self.a, 1, column, 1e-6)
        self.assertEqual((100, 0), result[0]['target'])

    def test_flange_face_is_distinct_from_web_and_unknown_section(self):
        column = member('col', 'column', (105, 0, 0), (105, 0, 100), 0, 100)
        column['faces'] += [side_face(100), side_face(110)]
        self.assertEqual('Column Section Face', column_faces(self.a, 1, column, 1e-6)[0]['category'])
        column['web_normals'] = [(0, 1, 0)]
        column['web_planes'] = [((0, 1, 0), (105, 0.25, 0))]
        self.assertEqual('Column Flange Face', column_faces(self.a, 1, column, 1e-6)[0]['category'])

    def test_crossing_requires_interiors_and_reports_elevation(self):
        b = member('b', start=(50, -50, 0), end=(50, 50, 0))
        self.assertEqual('Interior Crossing', crossing_relationship(self.a, b, 1e-6)['category'])
        b['faces'] = member('raised', bottom=24, top=36)['faces']
        self.assertEqual('Separated Plan Crossing', crossing_relationship(self.a, b, 1e-6)['category'])
        b['faces'] = []
        self.assertEqual('Unresolved Plan Crossing', crossing_relationship(self.a, b, 1e-6)['category'])
        b['start'], b['end'] = (100, -50, 0), (100, 50, 0)
        self.assertIsNone(crossing_relationship(self.a, b, 1e-6))

    def test_crossing_pair_once_and_spatial_index_finds_interior(self):
        b = member('b', start=(50, -1000, 0), end=(50, 1000, 0))
        rows = evaluate([self.a, b], [], dict(DEFAULTS, checks=['SMR-06']))
        self.assertEqual(1, len(rows))
        self.assertEqual('Error', rows[0]['severity'])
        self.assertEqual('Interior Crossing', rows[0]['error_type'])

    def test_serialized_report_links_results_to_separate_records(self):
        relations = []
        rows = evaluate([self.a], [], dict(DEFAULTS, checks=['SMR-01']), relationships=relations)
        report = json.loads(json.dumps(assemble_report([self.a], rows, relations)))
        identities = set(r['relationship_id'] for r in report['relationships'])
        self.assertTrue(all(r['relationship_id'] in identities for r in report['rows']))
        self.assertEqual(len(report['rows']), len(set(r['result_id'] for r in report['rows'])))
        self.assertEqual('Member', report['members'][0]['record_type'])
        self.assertTrue(all('faces' not in r for r in report['rows']))
        self.assertNotIn('record_type', self.a)

    def test_attachment_result_is_informational_and_has_target_navigation(self):
        self.a['bottom_attachment'] = {'state': 'Floor Bottom Work Plane', 'reason': 'Matched',
                                      'host': {'uid': 'floor', 'id': 99, 'name': 'Floor'}}
        rows = evaluate([self.a], [], dict(DEFAULTS, checks=['SMR-05']))
        self.assertEqual('Information', rows[0]['severity'])
        self.assertEqual(99, rows[0]['related'][0]['id'])

    def test_review_filter_exposes_information_and_errors(self):
        b = member('b', start=(50, -50, 0), end=(50, 50, 0))
        self.a['bottom_attachment'] = {'state': 'No Bottom-face Attachment Found'}
        rows = evaluate([self.a, b], [], dict(DEFAULTS, checks=['SMR-05', 'SMR-06']))
        self.assertIn('Information', [r.Severity for r in filtered_rows(rows, severity='Review')])
        self.assertEqual(1, len(filtered_rows(rows, severity='Error')))

    def test_evidence_detail_retains_small_offsets_and_empty_join_meaning(self):
        relation = {'category': 'Girder connection', 'evidence': {
            'horizontal_miss': 0.000002, 'join': {'state': 'Read', 'allowed': True, 'participants': []}}}
        text = evidence_text(relation, {})
        self.assertIn('0.00000200 in', text)
        self.assertIn('none returned', text)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        class Floor(object):
            pass
        class Roof(object):
            pass
        self.db = types.SimpleNamespace(Floor=Floor, RoofBase=Roof,
            BuiltInParameter=types.SimpleNamespace(),
            HostObjectUtils=types.SimpleNamespace(GetBottomFaces=lambda _host: [self.reference('bottom')]))
        self.floor = Floor()
        self.floor.Id = types.SimpleNamespace(Value=99)
        self.floor.UniqueId, self.floor.Name = 'floor', 'Floor'
        self.element = types.SimpleNamespace(HostFace=self.reference('bottom'),
            Id=types.SimpleNamespace(Value=1),
            Document=types.SimpleNamespace(GetElement=lambda _id: self.floor))

    def reference(self, label):
        return types.SimpleNamespace(ElementId=types.SimpleNamespace(Value=99),
                                     ConvertToStableRepresentation=lambda _doc: label)

    def test_bottom_face_identity_matches_but_top_face_does_not(self):
        self.assertEqual('Floor Bottom Work Plane', evidence.bottom_attachment(self.element, self.db)['state'])
        self.element.HostFace = self.reference('top')
        self.assertEqual('Other Work Plane', evidence.bottom_attachment(self.element, self.db)['state'])

    def test_no_face_reference_never_infers_attachment_from_elevation(self):
        self.element.HostFace = None
        result = evidence.bottom_attachment(self.element, self.db)
        self.assertEqual('No Bottom-face Attachment Found', result['state'])

    def test_failed_bottom_query_is_unresolved_not_absent(self):
        def fail(_host):
            raise RuntimeError('Unsupported host')
        self.db.HostObjectUtils.GetBottomFaces = fail
        self.assertEqual('Unresolved', evidence.bottom_attachment(self.element, self.db)['state'])

    def test_roof_underside_and_element_id_work_plane_are_reported(self):
        roof = self.db.RoofBase()
        roof.Id, roof.UniqueId, roof.Name = self.floor.Id, 'roof', 'Roof'
        self.element.Document.GetElement = lambda _id: roof
        self.db.BuiltInParameter.SKETCH_PLANE_PARAM = 'plane'
        self.element.get_Parameter = lambda _key: types.SimpleNamespace(
            HasValue=True, StorageType='ElementId', AsElementId=lambda: roof.Id)
        result = evidence.bottom_attachment(self.element, self.db)
        self.assertEqual('Roof Bottom Work Plane', result['state'])
        self.assertEqual('Roof', result['work_plane']['name'])

    def test_linked_host_face_is_explicitly_excluded(self):
        self.element.HostFace.LinkedElementId = types.SimpleNamespace(Value=42)
        result = evidence.bottom_attachment(self.element, self.db)
        self.assertEqual('Unresolved', result['state'])
        self.assertIn('Linked', result['reason'])

    def test_join_permission_is_independent_of_actual_participants(self):
        target = types.SimpleNamespace(UniqueId='other', Id=types.SimpleNamespace(Value=2))
        self.element.UniqueId = 'self'
        self.element.Location = types.SimpleNamespace(get_ElementsAtJoin=lambda _end: [self.element, target, target])
        def unavailable(*_args):
            raise ValueError('Not applicable')
        self.db.Structure = types.SimpleNamespace(StructuralFramingUtils=types.SimpleNamespace(
            IsJoinAllowedAtEnd=lambda *_args: False, GetEndReference=unavailable))
        facts = evidence.joins(self.element, self.db)
        self.assertFalse(facts['1']['allowed'])
        self.assertEqual(['other'], [p['uid'] for p in facts['1']['participants']])
        self.assertEqual('Unavailable', facts['1']['end_reference']['state'])

    def test_join_query_failure_is_not_empty_success(self):
        self.element.Location = object()
        result = evidence.joins(self.element, self.db)
        self.assertEqual('Unavailable', result['0']['state'])
        self.assertTrue(result['0']['errors'])

    def test_zero_parameter_is_not_missing_and_lengths_convert_once(self):
        self.db.BuiltInParameter = types.SimpleNamespace(Z_OFFSET_VALUE='z')
        self.element.get_Parameter = lambda _key: types.SimpleNamespace(HasValue=True, AsDouble=lambda: 0)
        values = evidence.parameters(self.element, self.db)
        self.assertEqual({'state': 'Value', 'value': 0, 'units': 'in'}, values['Z_OFFSET_VALUE'])
        self.assertEqual('Missing', values['END_Z_OFFSET_VALUE']['state'])

    def test_web_plane_recognition_requires_section_metadata_and_geometry(self):
        symbol = types.SimpleNamespace(Family=types.SimpleNamespace(StructuralSectionShape='IWideFlange'),
            get_Parameter=lambda _key: types.SimpleNamespace(HasValue=True, AsDouble=lambda: 0.5 / 12))
        self.db.BuiltInParameter.STRUCTURAL_SECTION_ISHAPE_WEBTHICKNESS = 'tw'
        column = types.SimpleNamespace(Symbol=symbol)
        faces = [side_face(-0.25), side_face(0.25), side_face(-5), side_face(5)]
        facts = evidence.column_section(column, faces, self.db)
        self.assertEqual(2, len(facts['web_planes']))
        symbol.Family.StructuralSectionShape = 'PipeStandard'
        self.assertEqual([], evidence.column_section(column, faces, self.db)['web_planes'])


if __name__ == '__main__':
    unittest.main()
