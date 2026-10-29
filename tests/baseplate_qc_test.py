from __future__ import print_function

import math
import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.baseplate_qc.layout import (
    TYPE_C_ROD_SPACING,
    layout_plate,
    nearest_wall,
    parse_column_size,
    rod_offsets,
)
from lib.baseplate_qc.schedule import (
    edge_distance,
    format_inches,
    normalize_mark,
    parse_inches,
    read_base_plate_schedule,
    read_edge_distances,
)


ROW = 0.25  # Row pitch in feet; text is 0.1 ft tall.


def cell(text, x, y, width=0.4, height=0.1):
    return {'text': text, 'xmin': x - width / 2.0, 'xmax': x + width / 2.0,
            'ymin': y - height / 2.0, 'ymax': y + height / 2.0}


def table(rows, xs, top, heights=None):
    cells = []
    for index, row in enumerate(rows):
        y = top - index * ROW
        for x, text in zip(xs, row):
            if text:
                height = (heights or {}).get(index, 0.1)
                cells.append(cell(text, x, y, height=height))
    return cells


BASE_PLATE_XS = [0, 1, 2, 3, 4, 5, 6, 7]
BASE_PLATE_ROWS = [
    ['BASE PLATE SCHEDULE'],
    ['', '', 'BASE PLATE', '', '', '', 'ANCHOR RODS'],
    ['MARK', 'TYPE', 'DIM L', 'DIM W', 'THICKNESS', 'NUMBER', 'SIZE', 'EMBED'],
    ['BP1', 'A', '14"', '14"', '1"', '4', u'3/4"Ø', '9"'],
    ['BP4', 'C', '16"', '14"', '1 1/4"', '4', '3/4"%%c', '9"'],
    ['BP7', 'A', '9"', '8"', '3/4"', '4', u'3/4"φ', '9"'],
    ['BP9', 'B', '10"', '6"', '3/4"', '4', '3/4"', '9"'],
    ['BP11', 'C', '15"', '12"', '1"', '4', '3/4"', '24"'],
    ['', '', '', '', 'NOTE: ALL BASE PLATE MATERIAL IS A36 STEEL, UNO'],
]

ANCHOR_XS = [0, 1.2, 2.4, 3.6, 4.8, 6.0]
ANCHOR_ROWS = [
    ['ANCHOR ROD REQUIREMENTS'],
    [u'ANCHOR ROD\nØ (IN)', u'MAX HOLE Ø\n(IN)', 'MIN PLATE\nWASHER SIZE (IN)',
     'MIN PLATE WASHER\nTHICKNESS (IN)', 'MIN EMBED\n(IN)', 'EDGE DISTANCE\n"C" (IN)'],
    ['3/4', '1 5/16', '2', '1/4', '9', '1 1/2'],
    ['7/8', '1 9/16', '2 1/2', '5/16', '10', '2'],
    ['1', '1 7/8', '3', '3/8', '12', '2 1/2'],
    ['1 1/4', '2 1/8', '3 1/2', '1/2', '18', '2 1/2'],
    ['1 1/2', '2 3/8', '3 1/2', '1/2', '18', '2 1/2'],
    ['NOTE: ALL ANCHOR RODS ARE F1554 GRADE 55'],
    ['1/4', 'EQ', '', '', '', 'C'],
]


class ParseTextTests(unittest.TestCase):
    def test_inches(self):
        self.assertEqual(14.0, parse_inches('14"'))
        self.assertEqual(1.25, parse_inches('1 1/4"'))
        self.assertEqual(0.75, parse_inches(u'3/4"Ø'))
        self.assertEqual(0.75, parse_inches('3/4"%%c'))
        self.assertEqual(1.5, parse_inches('1-1/2"'))
        self.assertEqual(14.0, parse_inches("1'-2\""))
        self.assertEqual(24.0, parse_inches("2'"))
        self.assertEqual(0.75, parse_inches('0.75'))
        self.assertIsNone(parse_inches('EQ'))
        self.assertIsNone(parse_inches(''))

    def test_marks_and_format(self):
        self.assertEqual('BP7', normalize_mark(' bp-7 '))
        self.assertEqual('BP7', normalize_mark('BP 7'))
        self.assertEqual('1 1/4"', format_inches(1.25))
        self.assertEqual('3/4"', format_inches(0.75))
        self.assertEqual('9"', format_inches(9.0))


class ScheduleTests(unittest.TestCase):
    def cells(self):
        cells = table(BASE_PLATE_ROWS, BASE_PLATE_XS, 10.0)
        cells += table(ANCHOR_ROWS, ANCHOR_XS, 7.0, heights={1: 0.2})
        # Unrelated text level with the header row, beside the table.
        cells.append(cell('W', 12.0, 10.0 - 2 * ROW))
        return cells

    def test_reads_base_plate_rows(self):
        entries, problems = read_base_plate_schedule(self.cells())
        self.assertEqual([], problems)
        self.assertEqual(['BP1', 'BP11', 'BP4', 'BP7', 'BP9'], sorted(entries))
        bp7 = entries['BP7']
        self.assertEqual(('A', 9.0, 8.0, 0.75, 4, 0.75, 9.0),
                         (bp7['type'], bp7['length'], bp7['width'], bp7['thickness'],
                          bp7['rod_count'], bp7['rod_diameter'], bp7['embed']))
        self.assertEqual(1.25, entries['BP4']['thickness'])
        self.assertEqual(24.0, entries['BP11']['embed'])

    def test_missing_header_reports_problem(self):
        entries, problems = read_base_plate_schedule([cell('MARK', 0, 0)])
        self.assertEqual({}, entries)
        self.assertTrue(problems)

    def test_unreadable_cells_are_reported(self):
        rows = [BASE_PLATE_ROWS[2], ['BP2', 'A', '??', '12"', '1"', '4', '3/4"', '9"']]
        entries, problems = read_base_plate_schedule(table(rows, BASE_PLATE_XS, 0.0))
        self.assertIsNone(entries['BP2']['length'])
        self.assertTrue(any('BP2' in problem and 'length' in problem for problem in problems))

    def test_reads_edge_distances(self):
        distances = read_edge_distances(self.cells())
        self.assertEqual({0.75: 1.5, 0.875: 2.0, 1.0: 2.5, 1.25: 2.5, 1.5: 2.5}, distances)
        self.assertEqual(2.0, edge_distance(0.875, distances))
        self.assertEqual(1.5, edge_distance(0.75, {}))  # built-in default
        self.assertIsNone(edge_distance(2.0, distances))


class LayoutTests(unittest.TestCase):
    def entry(self, plate_type='A', length=9.0, width=8.0):
        return {'mark': 'BP7', 'type': plate_type, 'length': length, 'width': width,
                'rod_count': 4, 'rod_diameter': 0.75}

    def test_column_sizes(self):
        self.assertEqual({'shape': 'rect', 'depth': 3.0, 'width': 3.0}, parse_column_size('HSS3x3x3/8'))
        self.assertEqual({'shape': 'rect', 'depth': 8.0, 'width': 4.0}, parse_column_size('HSS8X4X1/2'))
        self.assertEqual({'shape': 'rect', 'depth': 3.5, 'width': 3.5},
                         parse_column_size('HSS3-1/2x3-1/2x1/4'))
        self.assertEqual({'shape': 'round', 'depth': 6.625, 'width': 6.625},
                         parse_column_size('HSS-Round HSS6.625X.280'))
        self.assertEqual(3.0, parse_column_size('HSS-Square Column HSS3x3x3/8')['width'])
        self.assertIsNone(parse_column_size('W10x68'))

    def test_rod_patterns(self):
        self.assertEqual(sorted([(-3.0, -2.5), (-3.0, 2.5), (3.0, -2.5), (3.0, 2.5)]),
                         sorted(rod_offsets('A', 9.0, 8.0, 1.5)))
        offsets = rod_offsets('C', 12.0, 8.0, 1.5)
        self.assertEqual(sorted(set(abs(v) for _, v in offsets)), [TYPE_C_ROD_SPACING / 2.0])
        self.assertEqual(sorted(set(abs(u) for u, _ in offsets)), [4.5])

    def test_plate_runs_along_the_wall(self):
        wall = {'id': 1, 'points': [(0.0, 0.0), (0.0, 20.0)], 'width': 1.0}
        found = nearest_wall((0.1, 5.0), [wall])
        self.assertEqual((0.0, 1.0), found['axis'])
        result = layout_plate(self.entry(), 1.5, (0.1, 5.0), parse_column_size('HSS3x3x3/8'),
                              (1.0, 0.0), found)
        self.assertEqual('wall', result['axis_source'])
        xs = [x for x, _ in result['plate']]
        ys = [y for _, y in result['plate']]
        self.assertAlmostEqual(8.0 / 12, max(xs) - min(xs))  # W across the wall
        self.assertAlmostEqual(9.0 / 12, max(ys) - min(ys))  # L along the wall
        self.assertEqual(4, len(result['rods']))
        self.assertEqual([], result['issues'])
        self.assertEqual('BP7 (A) 9x8', result['text'])

    def test_far_wall_is_ignored_and_column_axis_used(self):
        wall = {'id': 1, 'points': [(0.0, 0.0), (10.0, 0.0)], 'width': 1.0}
        self.assertIsNone(nearest_wall((5.0, 3.0), [wall]))
        angle = math.radians(30)
        result = layout_plate(self.entry(), 1.5, (5.0, 3.0), None, (math.cos(angle), math.sin(angle)))
        self.assertEqual('column', result['axis_source'])
        self.assertAlmostEqual(angle, math.atan2(result['axis'][1], result['axis'][0]))
        self.assertEqual([], result['issues'])

    def test_overhang_and_clashes_are_flagged(self):
        wall = {'id': 1, 'points': [(0.0, 0.0), (10.0, 0.0)], 'width': 0.5}
        found = nearest_wall((5.0, 0.0), [wall])
        result = layout_plate(self.entry('C', 12.0, 8.0), 1.5, (5.0, 0.0),
                              parse_column_size('HSS10x10x1/2'), (1.0, 0.0), found)
        issues = ' '.join(result['issues'])
        self.assertIn('hangs 1"', issues)  # 8" plate on a 6" wall
        self.assertIn('larger than the plate', issues)
        self.assertIn('rod falls on the column', issues)

    def test_unknown_type_and_missing_edge(self):
        result = layout_plate(self.entry('D'), None, (0.0, 0.0))
        self.assertEqual([], result['rods'])
        issues = ' '.join(result['issues'])
        self.assertIn('Type D', issues)
        self.assertIn('rods not drawn', issues)


if __name__ == '__main__':
    unittest.main()
