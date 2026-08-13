from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.steel_weight.reporting import summary_csv_rows


class SteelWeightReportingTests(unittest.TestCase):
    def test_projects_summary_rows_without_raw_element_or_floor_rows(self):
        result = {
            'rows': [{'level_name': 'Level 1', 'steel_weight_lb': 100.0,
                      'floor_area_square_feet': 50.0, 'psf': 2.0}],
            'total': {'steel_weight_lb': 100.0, 'floor_area_square_feet': 50.0, 'psf': 2.0},
            'categories': [{'level_name': 'Level 1', 'category': 'Structural Framing', 'steel_weight_lb': 100.0}],
            'family_types': [{'level_name': 'Level 1', 'family_type': 'W12x26', 'steel_weight_lb': 100.0}],
            'floor_types': [{'level_name': 'Level 1', 'floor_type': 'Deck', 'floor_area_square_feet': 50.0}],
            'excluded': [{'element_id': 10, 'reason': 'missing nominal weight'}],
            'excluded_summaries': [{
                'reason': 'missing nominal weight',
                'level_name': 'Level 1',
                'category': 'Structural Framing',
                'family_type': 'Steel Joist: K-Series',
                'count': 2,
                'length_feet': 20.0,
            }],
        }

        rows = summary_csv_rows(result, {'document_title': 'Sample'})

        self.assertIn(['Metadata', 'document_title', 'Sample'], rows)
        self.assertIn(['Level', 'Level 1', '100.000', '50.000', '2.000'], rows)
        self.assertIn([
            'Exclusion',
            'Level 1 | Steel Joist: K-Series | missing nominal weight',
            '',
            '',
            '',
            '2',
            '20.000',
            'Structural Framing',
        ], rows)
        self.assertFalse(any('element_id' in row or 'floor_id' in row for row in rows))


if __name__ == '__main__':
    unittest.main()
