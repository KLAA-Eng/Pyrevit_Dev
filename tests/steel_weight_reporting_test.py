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
            'categories': [{'category': 'Structural Framing', 'steel_weight_lb': 100.0}],
            'family_types': [{'family_type': 'W12x26', 'steel_weight_lb': 100.0}],
            'floor_types': [{'floor_type': 'Deck', 'floor_area_square_feet': 50.0}],
            'excluded': [{'element_id': 10, 'reason': 'missing nominal weight'}],
        }

        rows = summary_csv_rows(result, {'document_title': 'Sample'})

        self.assertIn(['Metadata', 'document_title', 'Sample'], rows)
        self.assertIn(['Level', 'Level 1', '100.000', '50.000', '2.000'], rows)
        self.assertIn(['Exclusion', 'missing nominal weight', '1'], rows)
        self.assertFalse(any('element_id' in row or 'floor_id' in row for row in rows))


if __name__ == '__main__':
    unittest.main()
