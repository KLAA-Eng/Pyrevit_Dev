"""Verify readable measurements and result filtering without loading Revit."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))

from steel_model_review.engine import finding
from steel_model_review.reporting import CHECK_LABELS, ReviewRow, evidence_text, filtered_rows


def row(level='Critical', value=0.000002):
    member = {'uid': 'beam', 'id': 12345, 'name': 'W12x26', 'level': 'Roof'}
    support = {'uid': 'column', 'id': 67890, 'name': 'HSS8x8'}
    return finding('SMR-01', member, 'Endpoint plan miss.', level,
                   value, 0, [support])


class ReportingTests(unittest.TestCase):
    def test_small_nonzero_discrepancy_remains_visible(self):
        self.assertEqual('+0.00000200', ReviewRow(row()).Offset)
        self.assertEqual('-0.03125000', ReviewRow(row(value=-0.03125)).Offset)

    def test_missing_measurement_is_blank_not_zero(self):
        self.assertEqual('', ReviewRow(row(value=None)).Offset)

    def test_extracted_names_do_not_repeat_element_ids(self):
        result = row()
        result['member'] = '12345: W12x26'
        self.assertEqual('12345: W12x26', ReviewRow(result).Member)

    def test_column_vertical_details_show_both_boundaries_and_bearing(self):
        relation = {'category': 'Column Shaft', 'evidence': {
            'beam_bottom': 0, 'beam_top': 12, 'column_bottom': 2, 'column_top': 10,
            'bottom_clearance': -2, 'top_protrusion': 2}}
        details = evidence_text(relation, {})
        self.assertIn('Underside above column base (negative below): -2.00000000 in', details)
        self.assertIn('Beam top above column top (negative within): 2.00000000 in', details)
        relation = {'category': 'Column Top Bearing', 'evidence': {
            'local_column_top': -0.03125, 'bearing_gap': 0.03125}}
        self.assertIn('Underside minus local column top: 0.03125000 in',
                      evidence_text(relation, {}))

    def test_overlap_length_is_identified_separately(self):
        result = row(value=50)
        result['measurement'] = 'Overlap length'
        self.assertEqual('Overlap length', ReviewRow(result).Measurement)
        self.assertEqual('Offset', ReviewRow(row()).Measurement)

    def test_search_finds_member_and_support_names_and_ids(self):
        for search in ('12345', '67890', ' w12X26 ', 'hss8X8', 'plan miss'):
            self.assertEqual(1, len(filtered_rows([row()], search=search)))
        self.assertEqual([], filtered_rows([row()], search='unknown'))

    def test_default_issues_filter_retains_unresolved_but_hides_passes(self):
        rows = [row('Pass'), row('Not evaluated'), row('Warning'), row()]
        self.assertEqual(['Critical', 'Warning', 'Not evaluated'],
                         [r.Severity for r in filtered_rows(rows)])
        self.assertEqual(4, len(filtered_rows(rows, severity='All')))

    def test_filters_combine_with_readable_check_name(self):
        result = row()
        result['status'] = 'Accepted exception'
        selected = filtered_rows([result], check=CHECK_LABELS['SMR-01'],
                                 level='Roof', status='Accepted exception')
        self.assertEqual(1, len(selected))
        self.assertEqual('Critical', selected[0].Severity)
        self.assertEqual([], filtered_rows([result], level='L1'))
        self.assertEqual([], filtered_rows([result], status='Open'))
        self.assertEqual([], filtered_rows([result], check=CHECK_LABELS['SMR-02']))


if __name__ == '__main__':
    unittest.main()
