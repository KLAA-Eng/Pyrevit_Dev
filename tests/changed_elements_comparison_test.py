from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.changed_elements.comparison import compare_fingerprints


class CompareFingerprintsTests(unittest.TestCase):
    def test_classifies_new_modified_unchanged_and_deleted_elements(self):
        baseline = {
            'unchanged': ('wall-type-a', ('point', 0.0, 0.0, 0.0, 0.0)),
            'type-change': ('wall-type-a', ('point', 1.0, 0.0, 0.0, 0.0)),
            'location-change': ('wall-type-a', ('point', 2.0, 0.0, 0.0, 0.0)),
            'deleted': ('wall-type-a', ('point', 3.0, 0.0, 0.0, 0.0)),
        }
        current = {
            'unchanged': ('wall-type-a', ('point', 0.0, 0.0, 0.0, 0.0)),
            'type-change': ('wall-type-b', ('point', 1.0, 0.0, 0.0, 0.0)),
            'location-change': ('wall-type-a', ('point', 4.0, 0.0, 0.0, 0.0)),
            'new': ('wall-type-a', ('point', 5.0, 0.0, 0.0, 0.0)),
        }

        result = compare_fingerprints(baseline, current)

        self.assertEqual(['new'], result['new'])
        self.assertEqual(['location-change', 'type-change'], result['modified'])
        self.assertEqual(['unchanged'], result['unchanged'])
        self.assertEqual(['deleted'], result['deleted'])

    def test_reports_each_modified_reason_without_mutating_inputs(self):
        baseline = {'item': ('type-a', ('point', 0.0, 0.0, 0.0, 0.0))}
        current = {'item': ('type-b', ('point', 1.0, 0.0, 0.0, 0.0))}

        result = compare_fingerprints(baseline, current)

        self.assertEqual(['type', 'location'], result['reasons']['item'])
        self.assertEqual({'item': ('type-a', ('point', 0.0, 0.0, 0.0, 0.0))}, baseline)
        self.assertEqual({'item': ('type-b', ('point', 1.0, 0.0, 0.0, 0.0))}, current)


if __name__ == '__main__':
    unittest.main()
