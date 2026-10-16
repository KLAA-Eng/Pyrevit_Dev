"""Verify Model Checker geometry and severity without loading Revit."""

import copy
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))

from steel_model_review.engine import (
    Cancelled, DEFAULTS, duplicate_check, endpoint_checks, evaluate, grid_check,
    severity,
)
from steel_model_review.geometry import SpatialIndex, section_interval
from steel_model_review.session import carry_exceptions, signature


def box_faces(low, high):
    x0, y0, z0 = low
    x1, y1, z1 = high
    polygon = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [((0, 0, 1), (x0, y0, z1), [polygon]),
            ((0, 0, -1), (x0, y0, z0), [polygon])]


def member(uid='a', kind='beam', start=(0, 0, 0), end=(100, 0, 0),
           bottom=0, top=12, type_id=1):
    low = (min(start[0], end[0]) - 3, min(start[1], end[1]) - 3, bottom)
    high = (max(start[0], end[0]) + 3, max(start[1], end[1]) + 3, top)
    vertices = [(x, y, z) for x in (low[0], high[0])
                for y in (low[1], high[1]) for z in (low[2], high[2])]
    return {'uid': uid, 'id': uid, 'kind': kind, 'start': start, 'end': end,
            'bounds': (low, high), 'type': type_id, 'vertices': vertices,
            'faces': box_faces(low, high), 'name': uid, 'level': 'L1'}


def grid(uid, start, end):
    return {'uid': uid, 'id': uid, 'name': uid, 'start': start, 'end': end}


class SeverityTests(unittest.TestCase):
    def test_confirmed_order_and_signs(self):
        for value, expected in ((0, 'Pass'), (1e-7, 'Pass'),
                                (1.0 / 32, 'Critical'),
                                (1.0 / 16, 'Warning'), (1.0 / 8, 'Warning')):
            self.assertEqual(expected, severity(value))
            self.assertEqual(expected, severity(-value))

    def test_boundary_normalization(self):
        self.assertEqual('Warning', severity(0.0625 - 0.5e-6))
        self.assertEqual('Critical', severity(0.0625 - 2e-6))
        self.assertEqual('Warning', severity(0.0625 + 0.5e-6))

    def test_nonfinite_rejected(self):
        for value in (float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                severity(value)


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.settings = dict(DEFAULTS)
        self.beam = member()
        self.column = member('col', 'column', (100, 0, -20),
                             (100, 0, 100), -20, 100)

    def rows(self, supports):
        return [r for r in endpoint_checks(
            self.beam, SpatialIndex([self.beam] + supports), self.settings)
                if r['end'] == 1]

    def test_endpoint_and_column_shaft_pass(self):
        self.assertEqual(['Pass', 'Pass'],
                         [r['severity'] for r in self.rows([self.column])])

    def test_endpoint_small_and_large_miss(self):
        for gap, expected in ((1.0 / 32, 'Critical'), (1.0 / 8, 'Warning')):
            self.column['start'] = (100 + gap, 0, -20)
            self.assertEqual(expected, self.rows([self.column])[0]['severity'])

    def test_missing_and_ambiguous(self):
        self.assertEqual('Critical', self.rows([])[0]['severity'])
        self.assertEqual('Not evaluated', self.rows([])[1]['severity'])
        other = copy.deepcopy(self.column)
        other['uid'] = 'other'
        self.assertEqual('Warning', self.rows([self.column, other])[0]['severity'])

    def test_different_depths_aligned_tops_pass(self):
        support = member('girder', start=(100, -50, -12),
                         end=(100, 50, -12), bottom=-12, top=12)
        self.assertEqual('Pass', self.rows([support])[1]['severity'])

    def test_vertical_offset_keeps_separate_severity(self):
        support = member('girder', start=(100 + 1.0 / 32, -50, 0),
                         end=(100 + 1.0 / 32, 50, 0), bottom=0, top=12.125)
        self.assertEqual(['Critical', 'Warning'],
                         [r['severity'] for r in self.rows([support])])

    def test_infinite_extension_is_not_a_support(self):
        support = member('girder', start=(100, 10, 0), end=(100, 50, 0))
        self.assertEqual('Critical', self.rows([support])[0]['severity'])

    def test_end_to_end_is_ambiguous(self):
        support = member('next', start=(100, 0, 0), end=(200, 0, 0))
        self.assertEqual('Warning', self.rows([support])[0]['severity'])
        self.assertIn('Ambiguous', self.rows([support])[0]['reason'])

    def test_wrong_floor_is_not_support(self):
        self.column['bounds'] = ((97, -3, 200), (103, 3, 300))
        self.assertEqual('Critical', self.rows([self.column])[0]['severity'])

    def test_wall_face_and_bearing(self):
        wall = member('wall', 'wall', (104, -50, 0), (104, 50, 0), -100, 0)
        wall['faces'] = box_faces((100, -50, -100), (108, 50, 0))
        wall['bounds'] = ((100, -50, -100), (108, 50, 0))
        wall['sides'] = [((100, -50), (100, 50)), ((108, -50), (108, 50))]
        self.assertEqual(['Pass', 'Pass'],
                         [r['severity'] for r in self.rows([wall])])
        self.beam['end'] = (104, 0, 0)
        row = self.rows([wall])[0]
        self.assertEqual('Warning', row['severity'])
        self.assertEqual(4, row['value'])
        self.beam['end'] = (107, 0, 0)
        # The nearest face would be 108; approach from the left requires 100.
        self.assertEqual(7, self.rows([wall])[0]['value'])

    def test_unreliable_section_is_not_pass(self):
        self.beam['faces'] = []
        self.assertEqual('Not evaluated', self.rows([self.column])[1]['severity'])


class GridTests(unittest.TestCase):
    def setUp(self):
        self.settings = dict(DEFAULTS)
        self.column = member('col', 'column', (0, 0, 0), (0, 0, 100))
        self.grids = [grid('A', (0, -10), (0, 10)),
                      grid('1', (-10, 0), (10, 0)),
                      grid('2', (-10, 100), (10, 100))]

    def test_grid_and_intentional_offset(self):
        self.assertEqual('Pass', grid_check(self.column, self.grids,
                                           self.settings)['severity'])
        self.column['start'] = (1.0 / 32, 0, 0)
        self.assertEqual('Critical', grid_check(self.column, self.grids,
                                               self.settings)['severity'])

    def test_explicit_pair_controls(self):
        row = grid_check(self.column, self.grids, self.settings, ('A', '2'))
        self.assertEqual(100, row['value'])
        self.assertEqual('Warning', row['severity'])

    def test_explicit_mode_requires_assignment(self):
        self.settings['grid_mode'] = 'Explicit grid pairs'
        self.assertEqual('Not evaluated', grid_check(self.column, self.grids,
                                                    self.settings)['severity'])

    def test_parallel_and_no_grids_unresolved(self):
        self.assertEqual('Not evaluated', grid_check(self.column, [],
                                                    self.settings)['severity'])
        self.assertEqual('Not evaluated', grid_check(self.column, self.grids[1:],
                                                    self.settings)['severity'])

    def test_equal_distance_distinct_intersections_ambiguous(self):
        self.column['start'] = (0, 50, 0)
        self.assertEqual('Warning', grid_check(self.column, self.grids,
                                               self.settings)['severity'])


class DuplicateTests(unittest.TestCase):
    def setUp(self):
        self.settings = dict(DEFAULTS)
        self.a = member()
        self.b = member('b')

    def test_exact_and_reversed_endpoints(self):
        self.b['start'], self.b['end'] = self.b['end'], self.b['start']
        self.assertEqual('Critical', duplicate_check(self.a, self.b,
                                                    self.settings)['severity'])

    def test_near_duplicate(self):
        for key in ('start', 'end'):
            p = self.b[key]
            self.b[key] = (p[0], p[1] + 1.0 / 32, p[2])
        self.b['vertices'] = [(x, y + 1.0 / 32, z)
                              for x, y, z in self.b['vertices']]
        self.assertEqual('Critical', duplicate_check(self.a, self.b,
                                                    self.settings)['severity'])

    def test_adjacent_justified_geometry_not_duplicate(self):
        self.b['vertices'] = [(x, y + 3, z) for x, y, z in self.b['vertices']]
        self.assertIsNone(duplicate_check(self.a, self.b, self.settings))

    def test_different_types_require_review(self):
        self.b['type'] = 2
        self.assertEqual('Warning', duplicate_check(self.a, self.b,
                                                   self.settings)['severity'])

    def test_partial_overlap_and_crossing(self):
        self.b['start'], self.b['end'] = (50, 0, 0), (150, 0, 0)
        row = duplicate_check(self.a, self.b, self.settings)
        self.assertEqual('Warning', row['severity'])
        self.assertEqual(50, row['value'])
        self.b['start'], self.b['end'] = (50, -50, 0), (50, 50, 0)
        self.assertIsNone(duplicate_check(self.a, self.b, self.settings))

    def test_shared_endpoint_not_overlap(self):
        self.b['start'], self.b['end'] = (100, 0, 0), (200, 0, 0)
        self.assertIsNone(duplicate_check(self.a, self.b, self.settings))

    def test_duplicate_pair_emitted_once(self):
        self.settings['checks'] = ['SMR-04']
        rows = evaluate([self.a, self.b], [], self.settings)
        self.assertEqual(1, len(rows))

    def test_clean_member_has_evaluated_outcome(self):
        self.settings['checks'] = ['SMR-04']
        rows = evaluate([self.a], [], self.settings)
        self.assertEqual('Pass', rows[0]['severity'])


class CoverageAndSessionTests(unittest.TestCase):
    def test_cancelled_run_cannot_return_complete_rows(self):
        def cancel(value, total):
            raise Cancelled()
        with self.assertRaises(Cancelled):
            evaluate([member()], [], DEFAULTS, progress=cancel)

    def test_exception_carry_requires_same_complete_evidence(self):
        settings = dict(DEFAULTS, checks=['SMR-01'])
        rows = evaluate([member()], [], settings)
        previous = {'stamp': 'same', 'rows': copy.deepcopy(rows)}
        previous['rows'][0]['status'] = 'Accepted exception'
        previous['rows'][0]['exception'] = 'Intentional cantilever.'
        carry_exceptions(rows, previous, 'changed')
        self.assertEqual('Open', rows[0]['status'])
        carry_exceptions(rows, previous, 'same')
        self.assertEqual('Accepted exception', rows[0]['status'])
        self.assertEqual('Critical', rows[0]['severity'])

    def test_json_round_trip_keeps_exception_identity(self):
        import json
        rows = evaluate([member()], [], dict(DEFAULTS, checks=['SMR-01']))
        previous = {'stamp': 'same', 'rows': copy.deepcopy(rows)}
        previous['rows'][0]['status'] = 'Accepted exception'
        previous['rows'][0]['exception'] = 'Intentional.'
        previous = json.loads(json.dumps(previous))
        carry_exceptions(rows, previous, 'same')
        self.assertEqual('Accepted exception', rows[0]['status'])

    def test_settings_signature_order_is_stable(self):
        self.assertEqual(signature({'a': 1, 'b': 2}), signature({'b': 2, 'a': 1}))

    def test_section_hole_does_not_create_false_top(self):
        a = member()
        hole = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        for normal, origin, loops in a['faces']:
            loops.append(hole)
        self.assertIsNone(section_interval(a, (0, 0), 1e-6))

    def test_large_spatial_envelopes_remain_queryable(self):
        a = member()
        a['bounds'] = ((-1e6, -1e6, 0), (1e6, 1e6, 12))
        self.assertEqual([a], list(SpatialIndex([a]).query((0, 0), 12)))


if __name__ == '__main__':
    unittest.main()
