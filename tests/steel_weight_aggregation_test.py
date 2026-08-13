from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.steel_weight.aggregation import aggregate_steel_weight


class AggregateSteelWeightTests(unittest.TestCase):
    def test_aggregates_length_times_nominal_weight_by_level_and_uses_total_denominator(self):
        records = [
            {
                'element_id': 11,
                'level_id': 1,
                'level_name': 'Level 1',
                'length_feet': 10.0,
                'nominal_weight_lb_per_foot': 20.0,
                'category': 'Structural Framing',
                'family_type': 'W12x26',
            },
            {
                'element_id': 12,
                'level_id': 1,
                'level_name': 'Level 1',
                'length_feet': 5.0,
                'nominal_weight_lb_per_foot': 10.0,
                'category': 'Structural Columns',
                'family_type': 'HSS6x6',
            },
            {
                'element_id': 21,
                'level_id': 2,
                'level_name': 'Level 2',
                'length_feet': 20.0,
                'nominal_weight_lb_per_foot': 15.0,
                'category': 'Structural Framing',
                'family_type': 'W14x30',
            },
        ]
        areas = [
            {'element_id': 101, 'level_id': 2, 'level_name': 'Level 2', 'area_square_feet': 100.0, 'floor_type': 'Slab'},
            {'element_id': 102, 'level_id': 1, 'level_name': 'Level 1', 'area_square_feet': 200.0, 'floor_type': 'Deck'},
            {'element_id': 103, 'level_id': 1, 'level_name': 'Level 1', 'area_square_feet': 50.0, 'floor_type': 'Deck'},
        ]

        result = aggregate_steel_weight(records, areas)

        self.assertEqual(['Level 1', 'Level 2'], [row['level_name'] for row in result['rows']])
        self.assertEqual(250.0, result['rows'][0]['steel_weight_lb'])
        self.assertEqual(250.0, result['rows'][0]['floor_area_square_feet'])
        self.assertEqual(1.0, result['rows'][0]['psf'])
        self.assertEqual(300.0, result['rows'][1]['steel_weight_lb'])
        self.assertEqual(550.0, result['total']['steel_weight_lb'])
        self.assertEqual(350.0, result['total']['floor_area_square_feet'])
        self.assertAlmostEqual(550.0 / 350.0, result['total']['psf'])
        self.assertEqual(
            [('Structural Columns', 50.0), ('Structural Framing', 500.0)],
            [(row['category'], row['steel_weight_lb']) for row in result['categories']],
        )
        self.assertEqual([('Deck', 250.0), ('Slab', 100.0)],
                         [(row['floor_type'], row['floor_area_square_feet']) for row in result['floor_types']])
        self.assertEqual([], result['excluded'])

    def test_reports_invalid_length_or_nominal_weight_and_keeps_no_area_psf_unavailable(self):
        records = [
            {
                'element_id': 31,
                'level_id': 3,
                'level_name': 'Roof',
                'length_feet': 10.0,
                'nominal_weight_lb_per_foot': 20.0,
            },
            {
                'element_id': 32,
                'level_id': 3,
                'level_name': 'Roof',
                'length_feet': 0.0,
                'nominal_weight_lb_per_foot': 20.0,
            },
            {
                'element_id': 33,
                'level_id': None,
                'level_name': '',
                'length_feet': 1.0,
                'nominal_weight_lb_per_foot': 20.0,
            },
        ]

        result = aggregate_steel_weight(records, [])

        self.assertEqual(1, len(result['rows']))
        self.assertEqual('Roof', result['rows'][0]['level_name'])
        self.assertEqual(200.0, result['rows'][0]['steel_weight_lb'])
        self.assertEqual(0.0, result['rows'][0]['floor_area_square_feet'])
        self.assertIsNone(result['rows'][0]['psf'])
        self.assertIsNone(result['total']['psf'])
        self.assertEqual(['missing or zero usable length', 'missing level'],
                         [item['reason'] for item in result['excluded']])

    def test_reports_invalid_floor_area_without_affecting_other_levels(self):
        records = [{
            'element_id': 41,
                'level_id': 4,
                'level_name': 'Level 4',
                'length_feet': 1.0,
                'nominal_weight_lb_per_foot': 20.0,
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
        self.assertAlmostEqual(0.4, result['total']['psf'])
        self.assertEqual(['missing or zero floor area'],
                         [item['reason'] for item in result['excluded']])


if __name__ == '__main__':
    unittest.main()
