from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.hanger_check.spatial import BoxIndex, boxes_intersect


class BoxIndexTest(unittest.TestCase):
    def setUp(self):
        self.index = BoxIndex()
        # A long header, a short joist, a joist far away, and one on another floor.
        self.index.add('header', (-40.0, -0.3, 9.0), (40.0, 0.3, 10.0))
        self.index.add('joist', (1.9, 0.0, 9.0), (2.1, 14.0, 10.0))
        self.index.add('far', (60.0, 60.0, 9.0), (61.0, 75.0, 10.0))
        self.index.add('upper', (1.9, 0.0, 30.0), (2.1, 14.0, 31.0))

    def test_near_matches_brute_force(self):
        low, high = (-1.0, -3.0, 7.0), (5.0, 3.0, 12.0)
        expected = [item for item, a, b in self.index.items if boxes_intersect(a, b, low, high)]
        self.assertEqual(self.index.near(low, high), expected)
        self.assertEqual(expected, ['header', 'joist'])

    def test_long_member_found_far_from_its_middle(self):
        self.assertEqual(self.index.near((37.0, -1.0, 9.5), (39.0, 1.0, 9.5)), ['header'])

    def test_touching_boxes_count_and_order_is_insertion_order(self):
        self.assertEqual(self.index.near((2.1, 14.0, 0.0), (3.0, 15.0, 40.0)), ['joist', 'upper'])

    def test_negative_coordinates_and_empty(self):
        self.assertEqual(self.index.near((-40.5, -0.5, 9.0), (-39.5, 0.5, 9.0)), ['header'])
        self.assertEqual(self.index.near((100.0, 100.0, 0.0), (101.0, 101.0, 1.0)), [])


if __name__ == '__main__':
    unittest.main()
