from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.steel_weight.aggregation import aggregate_steel_weight


class AggregateSteelWeightTests(unittest.TestCase):
    def test_aggregates_material_weights_by_level_and_uses_total_denominator(self):
        records = [
            {
                'element_id': 11,
                'material_id': 101,
                'level_id': 1,
                'level_name': 'Level 1',
                'volume_cubic_feet': 10.0,
                'density_kg_per_cubic_foot': 2.0,
            },
            {
                'element_id': 12,
                'material_id': 102,
                'level_id': 1,
                'level_name': 'Level 1',
                'volume_cubic_feet': 5.0,
                'density_kg_per_cubic_foot': 1.0,
            },
            {
                'element_id': 21,
                'material_id': 201,
                'level_id': 2,
                'level_name': 'Level 2',
                'volume_cubic_feet': 20.0,
                'density_kg_per_cubic_foot': 1.0,
            },
        ]
        areas = [
            {'level_id': 2, 'level_name': 'Level 2', 'area_square_feet': 100.0},
            {'level_id': 1, 'level_name': 'Level 1', 'area_square_feet': 200.0},
            {'level_id': 1, 'level_name': 'Level 1', 'area_square_feet': 50.0},
        ]

        result = aggregate_steel_weight(records, areas)

        self.assertEqual(['Level 1', 'Level 2'], [row['level_name'] for row in result['rows']])
        self.assertAlmostEqual(55.11556554625, result['rows'][0]['steel_weight_lb'])
        self.assertEqual(250.0, result['rows'][0]['floor_area_square_feet'])
        self.assertAlmostEqual(0.220462262185, result['rows'][0]['psf'])
        self.assertAlmostEqual(44.092452437, result['rows'][1]['steel_weight_lb'])
        self.assertAlmostEqual(99.20801798325, result['total']['steel_weight_lb'])
        self.assertEqual(350.0, result['total']['floor_area_square_feet'])
        self.assertAlmostEqual(0.28345147995214284, result['total']['psf'])
        self.assertEqual([], result['excluded'])

    def test_reports_invalid_weight_inputs_and_keeps_no_area_psf_unavailable(self):
        records = [
            {
                'element_id': 31,
                'material_id': 301,
                'level_id': 3,
                'level_name': 'Roof',
                'volume_cubic_feet': 10.0,
                'density_kg_per_cubic_foot': 1.0,
            },
            {
                'element_id': 32,
                'material_id': 302,
                'level_id': 3,
                'level_name': 'Roof',
                'volume_cubic_feet': 0.0,
                'density_kg_per_cubic_foot': 1.0,
            },
            {
                'element_id': 33,
                'material_id': 303,
                'level_id': None,
                'level_name': '',
                'volume_cubic_feet': 1.0,
                'density_kg_per_cubic_foot': 1.0,
            },
        ]

        result = aggregate_steel_weight(records, [])

        self.assertEqual(1, len(result['rows']))
        self.assertEqual('Roof', result['rows'][0]['level_name'])
        self.assertAlmostEqual(22.0462262185, result['rows'][0]['steel_weight_lb'])
        self.assertEqual(0.0, result['rows'][0]['floor_area_square_feet'])
        self.assertIsNone(result['rows'][0]['psf'])
        self.assertIsNone(result['total']['psf'])
        self.assertEqual(['missing or zero material volume', 'missing level'],
                         [item['reason'] for item in result['excluded']])

    def test_reports_invalid_floor_area_without_affecting_other_levels(self):
        records = [{
            'element_id': 41,
            'material_id': 401,
            'level_id': 4,
            'level_name': 'Level 4',
            'volume_cubic_feet': 1.0,
            'density_kg_per_cubic_foot': 1.0,
        }]
        areas = [
            {'level_id': 4, 'level_name': 'Level 4', 'area_square_feet': 0.0},
            {'level_id': 5, 'level_name': 'Level 5', 'area_square_feet': 50.0},
        ]

        result = aggregate_steel_weight(records, areas)

        self.assertEqual(['Level 4', 'Level 5'], [row['level_name'] for row in result['rows']])
        self.assertIsNone(result['rows'][0]['psf'])
        self.assertEqual(0.0, result['rows'][1]['steel_weight_lb'])
        self.assertEqual(50.0, result['total']['floor_area_square_feet'])
        self.assertAlmostEqual(0.044092452437, result['total']['psf'])
        self.assertEqual(['missing or zero floor area'],
                         [item['reason'] for item in result['excluded']])


if __name__ == '__main__':
    unittest.main()
