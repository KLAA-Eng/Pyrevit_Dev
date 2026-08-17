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
    EXCLUSIONS_CSV_HEADER,
    EXCLUSIONS_KEY,
    EXCLUSION_SUMMARIES_CSV_HEADER,
    EXCLUSION_SUMMARIES_KEY,
    FLOORS_CSV_HEADER,
    FLOORS_KEY,
    FLOOR_TYPE_SUMMARIES_CSV_HEADER,
    FLOOR_TYPE_SUMMARIES_KEY,
    FAMILY_TYPE_SUMMARIES_CSV_HEADER,
    FAMILY_TYPE_SUMMARIES_KEY,
    CATEGORY_SUMMARIES_CSV_HEADER,
    CATEGORY_SUMMARIES_KEY,
    LEVEL_SUMMARIES_CSV_HEADER,
    LEVEL_SUMMARIES_KEY,
    RUN_APPEND,
    RUN_INITIALIZE,
    STEEL_CSV_HEADER,
    STEEL_KEY,
    HistoryCsvError,
    export_set_paths,
    raw_history_csv_rows,
    summary_history_csv_rows,
    workbook_path_for_folder,
    write_history_export_set,
)


class SteelWeightHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _metadata(self):
        return {
            'document_title': 'Sample',
            'selected_story_count': '1',
            'selected_story_names': 'Level 1',
        }

    def _steel_records(self):
        return [
            {
                'element_id': 10,
                'level_id': 100,
                'level_name': 'Level 1',
                'category': 'Structural Framing',
                'family_type': 'W12x26',
                'length_feet': 10.0,
                'nominal_weight_lb_per_foot': 26.0,
            },
            {
                'element_id': 11,
                'level_id': 100,
                'level_name': 'Level 1',
                'category': 'Structural Framing',
                'family_type': 'Steel Joist: K-Series',
                'length_feet': 20.0,
                'nominal_weight_lb_per_foot': None,
            },
        ]

    def _floor_records(self):
        return [
            {
                'element_id': 20,
                'level_id': 100,
                'level_name': 'Level 1',
                'floor_type': 'Deck',
                'area_square_feet': 50.0,
            },
            {
                'element_id': 21,
                'level_id': 100,
                'level_name': 'Level 1',
                'floor_type': 'No Area Deck',
                'area_square_feet': None,
            },
        ]

    def _result(self):
        return {
            'rows': [{'level_name': 'Level 1', 'steel_weight_lb': 260.0,
                      'floor_area_square_feet': 50.0, 'psf': 5.2}],
            'total': {'steel_weight_lb': 260.0, 'floor_area_square_feet': 50.0, 'psf': 5.2},
            'categories': [{'level_name': 'Level 1', 'category': 'Structural Framing',
                            'steel_weight_lb': 260.0}],
            'family_types': [{'level_name': 'Level 1', 'family_type': 'W12x26',
                              'steel_weight_lb': 260.0}],
            'floor_types': [{'level_name': 'Level 1', 'floor_type': 'Deck',
                             'floor_area_square_feet': 50.0}],
            'excluded_summaries': [{
                'reason': 'missing or zero nominal section weight',
                'level_name': 'Level 1',
                'category': 'Structural Framing',
                'family_type': 'Steel Joist: K-Series',
                'count': 1,
                'length_feet': 20.0,
            }],
        }

    def _read_csv(self, path):
        with open(path, 'r') as csv_file:
            return list(csv.reader(csv_file))

    def test_raw_history_rows_include_steel_floors_and_exclusions(self):
        rows = raw_history_csv_rows(
            self._steel_records(),
            self._floor_records(),
            [(30, 'not a steel family instance')],
            self._metadata(),
            'run-1',
            '2026-08-14T12:00:00')

        self.assertIn([
            'run-1', '2026-08-14T12:00:00', 'Sample', '1', 'Level 1',
            '10', '100', 'Level 1', 'Structural Framing', 'W12x26',
            '10.000', '26.000', '260.000', 'Eligible', '',
        ], rows[STEEL_KEY])
        self.assertIn([
            'run-1', '2026-08-14T12:00:00', 'Sample', '1', 'Level 1',
            '20', '100', 'Level 1', 'Deck', '50.000', 'Eligible', '',
        ], rows[FLOORS_KEY])
        self.assertIn([
            'run-1', '2026-08-14T12:00:00', 'Sample', '1', 'Level 1',
            'Steel', '11', '100', 'Level 1', 'Structural Framing',
            'Steel Joist: K-Series', '', 'missing or zero nominal section weight',
            '20.000', '1',
        ], rows[EXCLUSIONS_KEY])
        self.assertIn([
            'run-1', '2026-08-14T12:00:00', 'Sample', '1', 'Level 1',
            'AdapterSkip', '30', '', 'Unspecified', 'Unspecified',
            'Unspecified', '', 'not a steel family instance', '', '1',
        ], rows[EXCLUSIONS_KEY])

    def test_summary_history_rows_include_output_window_summaries(self):
        rows_by_key = summary_history_csv_rows(
            self._result(), self._metadata(), 'run-1', '2026-08-14T12:00:00')

        self.assertIn([
            'run-1', '2026-08-14T12:00:00', 'Sample', '1', 'Level 1',
            'Level 1', '260.000', '50.000', '5.200',
        ], rows_by_key[LEVEL_SUMMARIES_KEY])
        self.assertIn([
            'run-1', '2026-08-14T12:00:00', 'Sample', '1', 'Level 1',
            'Level 1', 'W12x26', '260.000',
        ], rows_by_key[FAMILY_TYPE_SUMMARIES_KEY])
        self.assertIn([
            'run-1', '2026-08-14T12:00:00', 'Sample', '1', 'Level 1',
            'missing or zero nominal section weight', 'Level 1',
            'Structural Framing', 'Steel Joist: K-Series', '1', '20.000',
        ], rows_by_key[EXCLUSION_SUMMARIES_KEY])

    def test_initialize_writes_all_csvs_with_headers(self):
        rows = raw_history_csv_rows(
            self._steel_records(), self._floor_records(), [],
            self._metadata(), 'run-1', '2026-08-14T12:00:00')
        rows.update(summary_history_csv_rows(
            self._result(), self._metadata(), 'run-1', '2026-08-14T12:00:00'))

        counts = write_history_export_set(self.tmpdir, rows, RUN_INITIALIZE)
        paths = export_set_paths(self.tmpdir)

        self.assertEqual(2, counts[STEEL_KEY])
        self.assertEqual(2, counts[FLOORS_KEY])
        self.assertEqual(2, counts[EXCLUSIONS_KEY])
        self.assertEqual(len(rows[LEVEL_SUMMARIES_KEY]), counts[LEVEL_SUMMARIES_KEY])
        self.assertEqual(len(rows[CATEGORY_SUMMARIES_KEY]), counts[CATEGORY_SUMMARIES_KEY])
        self.assertEqual(len(rows[FAMILY_TYPE_SUMMARIES_KEY]), counts[FAMILY_TYPE_SUMMARIES_KEY])
        self.assertEqual(len(rows[FLOOR_TYPE_SUMMARIES_KEY]), counts[FLOOR_TYPE_SUMMARIES_KEY])
        self.assertEqual(len(rows[EXCLUSION_SUMMARIES_KEY]), counts[EXCLUSION_SUMMARIES_KEY])
        self.assertEqual(STEEL_CSV_HEADER, self._read_csv(paths[STEEL_KEY])[0])
        self.assertEqual(FLOORS_CSV_HEADER, self._read_csv(paths[FLOORS_KEY])[0])
        self.assertEqual(EXCLUSIONS_CSV_HEADER, self._read_csv(paths[EXCLUSIONS_KEY])[0])
        self.assertEqual(LEVEL_SUMMARIES_CSV_HEADER, self._read_csv(paths[LEVEL_SUMMARIES_KEY])[0])
        self.assertEqual(CATEGORY_SUMMARIES_CSV_HEADER, self._read_csv(paths[CATEGORY_SUMMARIES_KEY])[0])
        self.assertEqual(FAMILY_TYPE_SUMMARIES_CSV_HEADER, self._read_csv(paths[FAMILY_TYPE_SUMMARIES_KEY])[0])
        self.assertEqual(FLOOR_TYPE_SUMMARIES_CSV_HEADER, self._read_csv(paths[FLOOR_TYPE_SUMMARIES_KEY])[0])
        self.assertEqual(EXCLUSION_SUMMARIES_CSV_HEADER, self._read_csv(paths[EXCLUSION_SUMMARIES_KEY])[0])

    def test_append_reuses_headers_without_duplicate(self):
        rows = raw_history_csv_rows(
            self._steel_records(), self._floor_records(), [],
            self._metadata(), 'run-1', '2026-08-14T12:00:00')
        rows.update(summary_history_csv_rows(
            self._result(), self._metadata(), 'run-1', '2026-08-14T12:00:00'))
        write_history_export_set(self.tmpdir, rows, RUN_APPEND)
        write_history_export_set(self.tmpdir, rows, RUN_APPEND)

        paths = export_set_paths(self.tmpdir)
        self.assertEqual(5, len(self._read_csv(paths[STEEL_KEY])))
        self.assertEqual(5, len(self._read_csv(paths[FLOORS_KEY])))
        self.assertEqual(5, len(self._read_csv(paths[EXCLUSIONS_KEY])))
        self.assertEqual(1 + (len(rows[LEVEL_SUMMARIES_KEY]) * 2), len(self._read_csv(paths[LEVEL_SUMMARIES_KEY])))
        self.assertEqual(1 + (len(rows[EXCLUSION_SUMMARIES_KEY]) * 2), len(self._read_csv(paths[EXCLUSION_SUMMARIES_KEY])))

    def test_append_rejects_mismatched_header_in_any_csv(self):
        rows = raw_history_csv_rows(
            self._steel_records(), self._floor_records(), [],
            self._metadata(), 'run-1', '2026-08-14T12:00:00')
        write_history_export_set(self.tmpdir, rows, RUN_INITIALIZE)
        with open(export_set_paths(self.tmpdir)[FLOORS_KEY], 'w') as csv_file:
            csv_file.write('Wrong,Header\n')

        with self.assertRaises(HistoryCsvError):
            write_history_export_set(self.tmpdir, rows, RUN_APPEND)

    def test_workbook_path_uses_folder_export_name(self):
        self.assertEqual(
            os.path.join(self.tmpdir, 'SteelPSF.xlsx'),
            workbook_path_for_folder(self.tmpdir))


if __name__ == '__main__':
    unittest.main()
