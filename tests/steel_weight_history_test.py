from __future__ import print_function

import csv
import os
import shutil
import sys
import tempfile
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.steel_weight.history import (
    HISTORY_CSV_HEADER,
    RUN_APPEND,
    RUN_INITIALIZE,
    HistoryCsvError,
    history_csv_rows,
    initialized_csv_path,
    workbook_path_for_csv,
    write_history_csv,
)


class SteelWeightHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _sample_result(self):
        return {
            'rows': [{'level_name': 'Level 1', 'steel_weight_lb': 100.0,
                      'floor_area_square_feet': 50.0, 'psf': 2.0}],
            'total': {'steel_weight_lb': 100.0, 'floor_area_square_feet': 50.0, 'psf': 2.0},
            'categories': [{'level_name': 'Level 1', 'category': 'Structural Framing', 'steel_weight_lb': 100.0}],
            'family_types': [{'level_name': 'Level 1', 'family_type': 'W12x26', 'steel_weight_lb': 100.0}],
            'floor_types': [{'level_name': 'Level 1', 'floor_type': 'Deck', 'floor_area_square_feet': 50.0}],
            'excluded_summaries': [{
                'reason': 'missing nominal weight',
                'level_name': 'Level 1',
                'category': 'Structural Framing',
                'family_type': 'Steel Joist: K-Series',
                'count': 2,
                'length_feet': 20.0,
            }],
        }

    def _read_csv(self, path):
        with open(path, 'r') as csv_file:
            return list(csv.reader(csv_file))

    def test_history_rows_are_tidy_summary_only_rows(self):
        rows = history_csv_rows(
            self._sample_result(),
            {
                'document_title': 'Sample',
                'selected_story_count': '1',
                'selected_story_names': 'Level 1',
            },
            'run-1',
            '2026-08-14T12:00:00',
            [(20, 'not a steel family instance')])

        self.assertIn([
            'run-1', '2026-08-14T12:00:00', 'Sample', '1', 'Level 1',
            'Level', 'Level 1', 'Level 1', 'PSF', '2.000', 'psf',
        ], rows)
        self.assertIn([
            'run-1', '2026-08-14T12:00:00', 'Sample', '1', 'Level 1',
            'Exclusion', 'Level 1',
            'Structural Framing | Steel Joist: K-Series | missing nominal weight',
            'Excluded Length', '20.000', 'ft',
        ], rows)
        self.assertIn([
            'run-1', '2026-08-14T12:00:00', 'Sample', '1', 'Level 1',
            'Exclusion', 'Unspecified', 'not a steel family instance',
            'Excluded Count', '1.000', 'count',
        ], rows)
        self.assertFalse(any('element_id' in cell or 'floor_id' in cell for row in rows for cell in row))

    def test_initialize_overwrites_csv_with_header_and_rows(self):
        path = os.path.join(self.tmpdir, 'history.csv')
        with open(path, 'w') as csv_file:
            csv_file.write('old,data\n')

        written = write_history_csv(path, [['run-1'] + [''] * 10], RUN_INITIALIZE)

        self.assertEqual(1, written)
        rows = self._read_csv(path)
        self.assertEqual(HISTORY_CSV_HEADER, rows[0])
        self.assertEqual(['run-1'] + [''] * 10, rows[1])

    def test_append_reuses_header_without_duplicate(self):
        path = os.path.join(self.tmpdir, 'history.csv')

        write_history_csv(path, [['run-1'] + [''] * 10], RUN_APPEND)
        write_history_csv(path, [['run-2'] + [''] * 10], RUN_APPEND)

        rows = self._read_csv(path)
        self.assertEqual(HISTORY_CSV_HEADER, rows[0])
        self.assertEqual(3, len(rows))
        self.assertEqual(['run-1'] + [''] * 10, rows[1])
        self.assertEqual(['run-2'] + [''] * 10, rows[2])

    def test_append_rejects_mismatched_header(self):
        path = os.path.join(self.tmpdir, 'history.csv')
        with open(path, 'w') as csv_file:
            csv_file.write('Wrong,Header\n')

        with self.assertRaises(HistoryCsvError):
            write_history_csv(path, [['run-1'] + [''] * 10], RUN_APPEND)

    def test_workbook_path_replaces_csv_extension(self):
        self.assertEqual(
            os.path.join(self.tmpdir, 'history.xlsx'),
            workbook_path_for_csv(os.path.join(self.tmpdir, 'history.csv')))

    def test_initialized_csv_path_uses_default_history_name(self):
        self.assertEqual(
            os.path.join(self.tmpdir, 'SteelPSF.csv'),
            initialized_csv_path(self.tmpdir))


if __name__ == '__main__':
    unittest.main()
