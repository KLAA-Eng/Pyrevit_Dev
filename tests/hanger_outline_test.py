from __future__ import print_function

import math
import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.hanger_check.classify import STATUS_OK, classify_hanger
from lib.hanger_check.outline import find_hexagons, loop_segments


def _polygon(sides, radius=0.25, center=(5.0, 3.0), rotation=0.0):
    points = [(center[0] + radius * math.cos(rotation + 2 * math.pi * i / sides),
               center[1] + radius * math.sin(rotation + 2 * math.pi * i / sides))
              for i in range(sides)]
    return loop_segments(points)


class FindHexagonTest(unittest.TestCase):
    def test_finds_hexagon_among_other_linework(self):
        leader = [((5.25, 3.0), (7.0, 3.0)), ((7.0, 3.0), (7.0, 4.0))]
        segments = _polygon(4, 1.0) + leader + _polygon(6, rotation=0.3)
        hexagons = find_hexagons(segments)
        self.assertEqual(len(hexagons), 1)
        self.assertEqual(len(hexagons[0]), 6)

    def test_reversed_and_split_order(self):
        segments = [(b, a) for a, b in reversed(_polygon(6))]
        self.assertEqual(len(find_hexagons(segments)), 1)

    def test_irregular_or_open_shapes_are_ignored(self):
        self.assertEqual(find_hexagons(_polygon(6)[:-1]), [])
        stretched = [((a[0] * 3, a[1]), (b[0] * 3, b[1])) for a, b in _polygon(6)]
        self.assertEqual(find_hexagons(stretched), [])

    def test_prism_top_and_bottom_project_to_one_loop(self):
        self.assertEqual(len(find_hexagons(_polygon(6) + _polygon(6))), 1)


class PlanOnlyTest(unittest.TestCase):
    def test_framing_far_above_hanger_is_found_in_plan(self):
        header = {'id': 1, 'start': (-10.0, 0.0, 9.0), 'end': (10.0, 0.0, 9.0)}
        joist = {'id': 2, 'start': (2.0, 0.15, 9.0), 'end': (2.0, 14.0, 9.0)}
        in_3d = classify_hanger((2.0, 0.15, 0.0), [header, joist], (0.0, 1.0))
        self.assertIsNone(in_3d['supported'])
        in_plan = classify_hanger((2.0, 0.15, None), [header, joist], (0.0, 1.0))
        self.assertEqual(in_plan['status'], STATUS_OK)
        self.assertEqual((in_plan['supported'], in_plan['supporting']), (2, 1))


if __name__ == '__main__':
    unittest.main()
