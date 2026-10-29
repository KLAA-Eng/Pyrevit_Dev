from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.revision_cloud_sheets.mapping import sheet_number_sort_key, sheets_by_cloud


class SheetsByCloudTests(unittest.TestCase):
    def test_inverts_sheet_clouds_and_lists_shared_clouds_on_each_sheet(self):
        result = sheets_by_cloud([
            ('S-101', [1, 2]),
            ('S-102', [2]),
            ('S-103', []),
        ])
        self.assertEqual({1: ['S-101'], 2: ['S-101', 'S-102']}, result)

    def test_requested_clouds_are_filtered_and_unplaced_clouds_kept(self):
        result = sheets_by_cloud([('S-101', [1, 2]), ('S-102', [2])], [2, 9])
        self.assertEqual({2: ['S-101', 'S-102'], 9: []}, result)

    def test_repeated_cloud_on_one_sheet_is_listed_once(self):
        self.assertEqual({1: ['S-101']}, sheets_by_cloud([('S-101', [1, 1])]))


class SheetNumberSortKeyTests(unittest.TestCase):
    def test_sorts_numbers_naturally(self):
        numbers = ['S-10', 'S-2', 's-1', 'A-1', 'S-2.1']
        self.assertEqual(
            ['A-1', 's-1', 'S-2', 'S-2.1', 'S-10'],
            sorted(numbers, key=sheet_number_sort_key))

    def test_missing_number_sorts_first(self):
        self.assertEqual([None, 'S-1'], sorted(['S-1', None], key=sheet_number_sort_key))


if __name__ == '__main__':
    unittest.main()
