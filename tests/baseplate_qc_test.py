from __future__ import print_function

import ast
import io
import math
import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.baseplate_qc.details import describe, plate_geometry, read_type_details
from lib.baseplate_qc.layout import layout_plate, nearest_wall, parse_column_size
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

    def column_notes(self, rows, xs, top, first, last):
        """Cells for rows first..last drawn as one multi-line note per column."""
        ymax = top - first * ROW + ROW / 2.0
        ymin = top - last * ROW - ROW / 2.0
        cells = []
        for column, x in enumerate(xs):
            lines = [row[column] if column < len(row) else '' for row in rows[first:last + 1]]
            cells.append({'text': '\r'.join(lines) + '\r', 'xmin': x - 0.2, 'xmax': x + 0.2,
                          'ymin': ymin, 'ymax': ymax})
        return cells

    def test_reads_drafted_column_notes(self):
        cells = table(BASE_PLATE_ROWS[:3] + BASE_PLATE_ROWS[8:], BASE_PLATE_XS, 10.0)
        cells = [c for c in cells if 'NOTE' not in c['text']]
        cells += self.column_notes(BASE_PLATE_ROWS, BASE_PLATE_XS, 10.0, 3, 7)
        cells += table(ANCHOR_ROWS[:2], ANCHOR_XS, 7.0, heights={1: 0.2})
        cells += self.column_notes(ANCHOR_ROWS, ANCHOR_XS, 7.0, 2, 6)
        entries, problems = read_base_plate_schedule(cells)
        self.assertEqual([], problems)
        self.assertEqual(['BP1', 'BP11', 'BP4', 'BP7', 'BP9'], sorted(entries))
        self.assertEqual(('C', 15.0, 12.0, 24.0), tuple(
            entries['BP11'][key] for key in ('type', 'length', 'width', 'embed')))
        self.assertEqual(2.0, read_edge_distances(cells)[0.875])

    def test_reads_one_note_per_row(self):
        cells = table(BASE_PLATE_ROWS[:3], BASE_PLATE_XS, 10.0)
        for index, row in enumerate(BASE_PLATE_ROWS[3:8]):
            cells.append({'text': '\t'.join(row), 'xmin': -0.2, 'xmax': 7.2,
                          'ymin': 10.0 - (3 + index) * ROW - 0.05,
                          'ymax': 10.0 - (3 + index) * ROW + 0.05})
        entries, problems = read_base_plate_schedule(cells)
        self.assertEqual([], problems)
        self.assertEqual(1.25, entries['BP4']['thickness'])
        self.assertEqual(0.75, entries['BP9']['rod_diameter'])

    def test_reads_drafted_schedule_from_a_project(self):
        # Text notes dumped from a project's drafted schedule view: note boxes
        # are taller than the row pitch and the diameter glyph reads as a letter.
        path = os.path.join(PROJECT_ROOT, 'tests', 'fixtures', 'baseplate_schedule_text.txt')
        cells = []
        with io.open(path, encoding='utf-8') as dump:
            for line in dump.read().splitlines()[2:]:
                xmin, xmax, ymin, ymax, text = line.split(', ', 4)
                cells.append({'text': ast.literal_eval(text), 'xmin': float(xmin), 'xmax': float(xmax),
                              'ymin': float(ymin), 'ymax': float(ymax)})
        entries, problems = read_base_plate_schedule(cells)
        self.assertEqual([], problems)
        self.assertEqual(['BP{}'.format(n) for n in range(1, 12)],
                         sorted(entries, key=lambda mark: int(mark[2:])))
        self.assertEqual(('B', 10.0, 6.0, 0.75, 4, 0.75, 9.0), tuple(
            entries['BP9'][key] for key in ('type', 'length', 'width', 'thickness',
                                            'rod_count', 'rod_diameter', 'embed')))
        self.assertEqual(24.0, entries['BP11']['embed'])
        self.assertEqual({0.75: 1.5, 0.875: 2.0, 1.0: 2.5, 1.25: 2.5, 1.5: 2.5},
                         read_edge_distances(cells))

    def test_letter_marks_and_a_second_type_column(self):
        # BPA-style marks, with a second TYPE (anchor type) under ANCHOR.
        xs = [0, 1, 2, 3, 4, 5.5, 7, 8, 9]
        rows = [['MARK', 'TYPE', 'DIM L', 'DIM W', 'THICKNESS', 'TYPE', 'NUMBER', 'SIZE', 'EMBED'],
                ['BPA', 'A', '11"', '11"', '3/4"', 'CAST-IN OR POST INSTALLED', '4', u'3/4"à', '9"'],
                ['BPB', 'B', '9"', '5 1/2"', '3/4"', 'CAST-IN', '4', '3/4"', '9"'],
                ['NOTE'],
                ['BPZ', 'Z', '1"', '1"', '1"', '', '4', '3/4"', '9"']]
        cells = table(rows, xs, 0.0)
        cells[14]['xmin'] -= 0.8  # The long anchor type text is wider than its column.
        cells[14]['xmax'] += 0.8
        entries, problems = read_base_plate_schedule(cells)
        self.assertEqual([], problems)
        self.assertEqual(['BPA', 'BPB'], sorted(entries))
        self.assertEqual(('A', 11.0, 11.0, 0.75, 4, 0.75, 9.0), tuple(
            entries['BPA'][key] for key in ('type', 'length', 'width', 'thickness',
                                            'rod_count', 'rod_diameter', 'embed')))
        self.assertEqual(5.5, entries['BPB']['width'])

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


def outline(points):
    return list(points) + [points[0]]


def square(cx, cy, half):
    return outline([(cx - half, cy - half), (cx + half, cy - half), (cx + half, cy + half),
                    (cx - half, cy + half)])


def rod(cx, cy, radius=0.03):
    """A rod drawn as a circle inside a square washer: (polylines, arcs)."""
    circle = [(cx + radius * math.cos(a), cy + radius * math.sin(a))
              for a in (i * math.pi / 8 for i in range(17))]
    return [circle, square(cx, cy, 0.05)], [{'center': (cx, cy), 'radius': radius, 'sweep': 2 * math.pi}]


def dim(value, text, origin, horizontal, equal=False):
    return {'value': value, 'text': text, 'origin': origin,
            'direction': (1.0, 0.0) if horizontal else (0.0, 1.0), 'equal': equal}


def detail_sheet():
    """Linework, dimensions, and labels laid out like the S-500.S base plate detail.

    Details are not to scale: plates about 1 ft across, "C" drawn 0.15 ft.
    TYPE A is square, TYPE B L-shaped, TYPE C rectangular with a true 2 1/2"
    rod spacing, and TYPE D an octagon the reader must reject.
    """
    cells = [cell('NOTE: ALL ANCHOR RODS ARE F1554 GRADE 55', 3.4, -9.9, width=8.0)]
    polylines, arcs, dims = [], [], []

    def add_rods(points):
        for x, y in points:
            lines, circles = rod(x, y)
            polylines.extend(lines)
            arcs.extend(circles)

    # TYPE A: square plate, rods C in from both edges, centerlines and a weld leader.
    cells.append(cell('TYPE A', 1.8, -13.3, width=1.0, height=0.46))
    polylines.append(outline([(1.3, -12.3), (2.3, -12.3), (2.3, -11.3), (1.3, -11.3)]))
    polylines.append(square(1.8, -11.8, 0.12))
    polylines += [[(1.8, -12.5), (1.8, -11.1)], [(1.1, -11.8), (2.5, -11.8)]]
    polylines.append([(0.5, -12.6), (1.6, -12.6), (1.9, -12.3)])
    add_rods([(1.45, -12.15), (2.15, -12.15), (1.45, -11.45), (2.15, -11.45)])
    dims += [dim(1.0, 'L', (1.8, -11.1), True), dim(1.0, 'W', (2.5, -11.8), False),
             dim(0.15, '"C"', (2.2, -12.5), True), dim(0.5, '', (1.55, -11.0), True, equal=True)]

    # TYPE B: L-shaped plate, legs 1.0 long and 0.6 wide meeting at the bottom left.
    cells.append(cell('TYPE B', 6.17, -13.3, width=1.0, height=0.46))
    polylines.append(outline([(5.0, -12.4), (6.0, -12.4), (6.0, -11.8), (5.6, -11.8),
                              (5.6, -11.4), (5.0, -11.4)]))
    polylines.append(square(5.3, -12.1, 0.1))
    add_rods([(5.85, -12.25), (5.85, -11.95), (5.15, -11.55), (5.45, -11.55)])
    dims += [dim(1.0, 'L', (5.5, -11.2), True), dim(0.6, 'W', (5.3, -11.3), True),
             dim(0.15, 'C', (5.9, -12.6), True)]

    # TYPE C: rectangular plate, rod pairs C from each end, 2 1/2" apart across W.
    cells.append(cell('TYPE C', 10.54, -13.3, width=1.0, height=0.46))
    polylines.append(outline([(9.9, -12.3), (11.1, -12.3), (11.1, -11.7), (9.9, -11.7)]))
    polylines.append(square(10.5, -12.0, 0.1))
    add_rods([(10.05, -12.104), (10.05, -11.896), (10.95, -12.104), (10.95, -11.896)])
    dims += [dim(1.2, 'L', (10.5, -11.5), True), dim(0.6, 'W', (11.3, -12.0), False),
             dim(0.15, 'C', (11.0, -12.5), True), dim(2.5 / 12, '', (9.7, -12.0), False)]

    # TYPE D: an octagonal plate is too complex.
    cells.append(cell('TYPE D', 14.9, -13.3, width=1.0, height=0.46))
    polylines.append(outline([(14.6, -12.4), (15.2, -12.4), (15.4, -12.2), (15.4, -11.6),
                              (15.2, -11.4), (14.6, -11.4), (14.4, -11.6), (14.4, -12.2)]))
    add_rods([(14.9, -12.2), (14.9, -11.6)])
    return cells, polylines, arcs, dims


def embed_sheet():
    """Two rows of details with the patterns of an embed plate schedule.

    TYPE P: rods 2" (dimensioned) from the top edge and C from the others.
    TYPE Q: column at one end 3" from the start, rods chained 3" + 3 1/2".
    TYPE R: anchors drawn as small squares only.
    TYPE S: a column drawn over the plate's bottom edge.
    """
    cells = [cell('NOTE: ALL ANCHOR RODS ARE F1554 GRADE 55', 4.0, -1.0, width=8.0)]
    polylines, arcs, dims = [], [], []

    def add_rods(points):
        for x, y in points:
            lines, circles = rod(x, y)
            polylines.extend(lines)
            arcs.extend(circles)

    cells += [cell('TYPE P', 2.0, -5.0, width=1.0, height=0.46),
              cell('TYPE Q', 6.0, -5.0, width=1.0, height=0.46),
              cell('TYPE R', 2.0, -9.0, width=1.0, height=0.46),
              cell('TYPE S', 6.0, -9.0, width=1.0, height=0.46)]

    polylines.append(outline([(1.5, -4.2), (2.5, -4.2), (2.5, -3.2), (1.5, -3.2)]))
    polylines.append(square(2.0, -3.7, 0.12))
    add_rods([(1.65, -4.05), (2.35, -4.05), (1.65, -3.4), (2.35, -3.4)])
    dims += [dim(1.0, 'L', (2.0, -3.0), True), dim(0.15, 'C', (2.4, -4.4), True),
             dim(0.2, '2"', (2.7, -3.3), False)]

    polylines.append(outline([(5.4, -4.0), (6.6, -4.0), (6.6, -3.5), (5.4, -3.5)]))
    polylines.append(square(5.65, -3.75, 0.1))
    add_rods([(5.95, -3.75), (6.45, -3.75)])
    dims += [dim(1.2, 'L', (6.0, -3.3), True), dim(0.15, 'C', (6.5, -4.2), True),
             dim(0.25, '3"', (5.5, -4.2), True), dim(0.3, '3 1/2"', (5.8, -4.2), True)]

    polylines.append(outline([(1.5, -8.4), (2.5, -8.4), (2.5, -7.8), (1.5, -7.8)]))
    polylines.append(outline([(1.85, -8.2), (2.15, -8.2), (2.15, -8.0), (1.85, -8.0)]))
    for x, y in ((1.65, -8.25), (2.35, -8.25), (1.65, -7.95), (2.35, -7.95)):
        polylines.append(square(x, y, 0.03))
    dims += [dim(1.0, 'L', (2.0, -7.6), True), dim(0.15, 'C', (2.4, -8.6), True)]

    # The plate's bottom edge stops at the column, which pokes 0.1 below it.
    polylines += [[(5.9, -8.4), (5.4, -8.4), (5.4, -7.8), (6.6, -7.8), (6.6, -8.4), (6.1, -8.4)],
                  [(5.9, -8.0), (5.9, -8.5), (6.1, -8.5), (6.1, -8.0), (5.9, -8.0)]]
    add_rods([(5.55, -8.25), (6.45, -8.25), (5.55, -7.95), (6.45, -7.95)])
    dims += [dim(1.2, 'L', (6.0, -7.6), True), dim(0.15, 'C', (6.5, -8.7), True)]
    return cells, polylines, arcs, dims


def rule_names(definition):
    return sorted((u[0], v[0]) for u, v in definition['rods'])


class EmbedDetailTests(unittest.TestCase):
    def setUp(self):
        self.definitions, self.problems = read_type_details(*embed_sheet())

    def test_every_type_reads(self):
        self.assertEqual({}, self.problems)
        self.assertEqual(['P', 'Q', 'R', 'S'], sorted(self.definitions))

    def test_rods_use_a_dimensioned_edge_distance(self):
        geometry = plate_geometry(self.definitions['P'], 14.0, 14.0, 1.5)
        self.assertEqual([(1.5, 1.5), (1.5, 12.0), (12.5, 1.5), (12.5, 12.0)], sorted(geometry['rods']))

    def test_column_at_one_end_and_chained_dimensions(self):
        definition = self.definitions['Q']
        self.assertIn('column off center', describe(definition))
        geometry = plate_geometry(definition, 21.0, 5.5, 1.5)
        self.assertEqual((3.0, 2.75), geometry['column'])
        self.assertEqual([(6.5, 2.75), (19.5, 2.75)], sorted(geometry['rods']))

    def test_square_anchor_symbols_count_as_rods(self):
        self.assertEqual('rectangular plate, 4 rods', describe(self.definitions['R']))

    def test_column_over_the_plate_edge_keeps_the_plate_size(self):
        geometry = plate_geometry(self.definitions['S'], 15.0, 8.0, 1.5)
        self.assertEqual([(1.5, 1.5), (1.5, 6.5), (13.5, 1.5), (13.5, 6.5)], sorted(geometry['rods']))
        self.assertEqual(7.5, geometry['column'][0])  # Drawn at the bottom edge, centered along L.


class DetailTests(unittest.TestCase):
    def setUp(self):
        self.definitions, self.problems = read_type_details(*detail_sheet())

    def test_shapes_are_read(self):
        self.assertEqual(['A', 'B', 'C'], sorted(self.definitions))
        self.assertEqual('square plate, 4 rods', describe(self.definitions['A']))
        self.assertEqual('L-shaped plate, 4 rods', describe(self.definitions['B']))
        self.assertEqual('rectangular plate, 4 rods', describe(self.definitions['C']))

    def test_complex_type_is_left_out(self):
        self.assertEqual(['D'], list(self.problems))
        self.assertIn('8 corners', self.problems['D'])

    def test_square_rods_sit_c_from_each_edge(self):
        geometry = plate_geometry(self.definitions['A'], 14.0, 14.0, 1.5)
        self.assertEqual([(1.5, 1.5), (1.5, 12.5), (12.5, 1.5), (12.5, 12.5)], sorted(geometry['rods']))
        self.assertEqual((7.0, 7.0), geometry['column'])

    def test_l_rods_sit_at_the_leg_ends(self):
        geometry = plate_geometry(self.definitions['B'], 10.0, 6.0, 1.5)
        self.assertEqual([(1.5, 8.5), (4.5, 8.5), (8.5, 1.5), (8.5, 4.5)], sorted(geometry['rods']))
        self.assertEqual(6, len(geometry['plate']))
        self.assertEqual((3.0, 3.0), geometry['column'])

    def test_rectangular_rods_use_the_dimensioned_spacing(self):
        geometry = plate_geometry(self.definitions['C'], 15.0, 12.0, 1.5)
        rods = sorted((round(u, 4), round(v, 4)) for u, v in geometry['rods'])
        self.assertEqual([(1.5, 4.75), (1.5, 7.25), (13.5, 4.75), (13.5, 7.25)], rods)

    def test_typed_over_spacing_is_the_true_size(self):
        # The spacing is drawn 0.3 ft apart but its dimension text reads 2 1/2".
        cells, polylines, arcs, dims = detail_sheet()
        for arc in arcs:
            x, y = arc['center']
            if 9.9 < x < 11.1:
                arc['center'] = (x, -12.15 if y < -12.0 else -11.85)
        dims[-1] = dim(0.3, '2 1/2"', (9.7, -12.0), False)
        definitions, _ = read_type_details(cells, polylines, arcs, dims)
        geometry = plate_geometry(definitions['C'], 15.0, 12.0, 1.5)
        self.assertEqual([4.75, 7.25], sorted(set(round(v, 4) for _, v in geometry['rods'])))

    def test_changed_detail_changes_the_rods(self):
        # Move TYPE C's rods to C from the long edges: the rule follows the drawing.
        cells, polylines, arcs, dims = detail_sheet()
        for arc in arcs:
            x, y = arc['center']
            if 9.9 < x < 11.1:
                arc['center'] = (x, -12.15 if y < -12.0 else -11.85)
        definitions, _ = read_type_details(cells, polylines, arcs, dims)
        self.assertEqual([('C from the end', 'C from the end'), ('C from the end', 'C from the start'),
                          ('C from the start', 'C from the end'), ('C from the start', 'C from the start')],
                         rule_names(definitions['C']))


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.definitions, _ = read_type_details(*detail_sheet())

    def entry(self, plate_type='A', length=9.0, width=8.0):
        return {'mark': 'BP7', 'type': plate_type, 'length': length, 'width': width,
                'rod_count': 4, 'rod_diameter': 0.75}

    def layout(self, plate_type, length, width, center, column=None, column_axis=(1.0, 0.0), walls=(),
               edge=1.5):
        return layout_plate(self.entry(plate_type, length, width), self.definitions[plate_type], edge,
                            center, column, column_axis, walls)

    def test_column_sizes(self):
        self.assertEqual({'shape': 'rect', 'depth': 3.0, 'width': 3.0}, parse_column_size('HSS3x3x3/8'))
        self.assertEqual({'shape': 'rect', 'depth': 8.0, 'width': 4.0}, parse_column_size('HSS8X4X1/2'))
        self.assertEqual({'shape': 'rect', 'depth': 3.5, 'width': 3.5},
                         parse_column_size('HSS3-1/2x3-1/2x1/4'))
        self.assertEqual({'shape': 'round', 'depth': 6.625, 'width': 6.625},
                         parse_column_size('HSS-Round HSS6.625X.280'))
        self.assertEqual(3.0, parse_column_size('HSS-Square Column HSS3x3x3/8')['width'])
        self.assertIsNone(parse_column_size('W10x68'))

    def test_plate_runs_along_the_wall(self):
        wall = {'id': 1, 'points': [(0.0, 0.0), (0.0, 20.0)], 'width': 1.0}
        found = nearest_wall((0.1, 5.0), [wall])
        self.assertEqual((0.0, 1.0), found['axis'])
        result = self.layout('A', 9.0, 8.0, (0.1, 5.0), parse_column_size('HSS3x3x3/8'), walls=[wall])
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
        result = self.layout('A', 9.0, 8.0, (5.0, 3.0), column_axis=(math.cos(angle), math.sin(angle)),
                             walls=[wall])
        self.assertEqual('column', result['axis_source'])
        self.assertAlmostEqual(angle, math.atan2(result['axis'][1], result['axis'][0]))
        self.assertEqual([], result['issues'])

    def test_overhang_and_clashes_are_flagged(self):
        wall = {'id': 1, 'points': [(0.0, 0.0), (10.0, 0.0)], 'width': 0.5}
        result = self.layout('A', 12.0, 8.0, (5.0, 0.0), parse_column_size('HSS10x10x1/2'), walls=[wall])
        issues = ' '.join(result['issues'])
        self.assertIn('hangs 1"', issues)  # 8" plate on a 6" wall
        self.assertIn('larger than the plate', issues)
        self.assertIn('rod falls on the column', issues)

    def test_missing_edge_and_rod_count(self):
        entry = dict(self.entry('C', 15.0, 12.0), rod_count=6)
        result = layout_plate(entry, self.definitions['C'], None, (0.0, 0.0))
        self.assertEqual([], result['rods'])
        issues = ' '.join(result['issues'])
        self.assertIn('rods not drawn', issues)
        self.assertIn('Schedule lists 6 rods; the TYPE C detail shows 4', issues)

    def test_l_plate_follows_both_walls(self):
        # Wall 1 runs mostly toward -x from the column; wall 2 runs toward +y.
        walls = [{'id': 1, 'points': [(-10.0, 0.0), (3.0, 0.0)], 'width': 1.0},
                 {'id': 2, 'points': [(0.0, 0.0), (0.0, 8.0)], 'width': 1.0}]
        result = self.layout('B', 10.0, 6.0, (0.0, 0.0), parse_column_size('HSS3x3x3/8'), walls=walls)
        xs = [x for x, _ in result['plate']]
        ys = [y for _, y in result['plate']]
        self.assertAlmostEqual(-7.0 / 12, min(xs))
        self.assertAlmostEqual(3.0 / 12, max(xs))
        self.assertAlmostEqual(-3.0 / 12, min(ys))
        self.assertAlmostEqual(7.0 / 12, max(ys))
        self.assertEqual([], result['issues'])

    def test_l_plate_without_crossing_wall_is_flagged(self):
        walls = [{'id': 1, 'points': [(-10.0, 0.0), (3.0, 0.0)], 'width': 1.0}]
        result = self.layout('B', 10.0, 6.0, (0.0, 0.0), walls=walls)
        self.assertTrue(any('crossing wall' in issue for issue in result['issues']))


if __name__ == '__main__':
    unittest.main()
