from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.steel_weight.reporting import OUTPUT_INTRO, report_output_tables, summary_csv_rows


class SteelWeightReportingTests(unittest.TestCase):
    def _sample_result(self):
        return {
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

    def test_projects_summary_rows_without_raw_element_or_floor_rows(self):
        rows = summary_csv_rows(self._sample_result(), {'document_title': 'Sample'})

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

    def test_report_output_tables_use_title_case_and_uniform_summary_columns(self):
        tables = report_output_tables(self._sample_result(), [(20, 'not a steel family instance')])

        self.assertEqual('Pounds = length (ft) × nominal section weight (lb/ft).', OUTPUT_INTRO)
        self.assertEqual([
            'Level Summaries',
            'Category Summaries',
            'Family/Type Summaries',
            'Floor-Type Summaries',
            'Excluded Or Unavailable Data',
        ], [table['title'] for table in tables])
        self.assertEqual(['Level', 'Category', 'Steel Weight (lb)'], tables[1]['columns'])
        self.assertEqual(['Level', 'Family/Type', 'Steel Weight (lb)'], tables[2]['columns'])
        self.assertEqual(['Level', 'Floor Type', 'Floor Area (sf)'], tables[3]['columns'])
        self.assertEqual([3, 3, 3], [len(table['columns']) for table in tables[1:4]])
        self.assertIn(
            ['not a steel family instance', 'Unspecified', 'Unspecified', 'Unspecified', 1, '0.000'],
            tables[4]['rows'])


if __name__ == '__main__':
    unittest.main()
