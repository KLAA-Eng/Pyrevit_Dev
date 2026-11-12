from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
for path in (PROJECT_ROOT, TESTS_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)


from lib.pdf_overlay.geometry import make_pose
from lib.pdf_overlay.pdftext import read_page_text
from lib.wall_grade import pdf_grade, profile
from lib.wall_grade.profile import CLOSE, NO_DATA, OK, OVER
from pdf_overlay_members_test import build_pdf


class StationTests(unittest.TestCase):
    def test_stations_include_both_ends_evenly(self):
        self.assertEqual(profile.stations(3.0), [0.0, 1.0, 2.0, 3.0])
        result = profile.stations(2.5)
        self.assertEqual(len(result), 4)
        self.assertAlmostEqual(result[1], 2.5 / 3)
        self.assertEqual(result[-1], 2.5)

    def test_short_or_empty_wall(self):
        self.assertEqual(profile.stations(0.4), [0.0, 0.4])
        self.assertEqual(profile.stations(0.0), [0.0])

    def test_exterior_offset_by_location_line(self):
        self.assertEqual(profile.exterior_offset(0, 1.0), 0.5)
        self.assertEqual(profile.exterior_offset(2, 1.0), 0.0)
        self.assertEqual(profile.exterior_offset(3, 1.0), 1.0)
        self.assertEqual(profile.exterior_offset(99, 1.0), 0.5)

    def test_clamp_clearance(self):
        self.assertEqual(profile.clamp_clearance('6'), 6.0)
        self.assertEqual(profile.clamp_clearance(' 7.5" '), 7.5)
        self.assertEqual(profile.clamp_clearance('x'), 8.0)
        self.assertEqual(profile.clamp_clearance('-2'), 8.0)
        self.assertEqual(profile.clamp_clearance('100'), 48.0)


class ProfileTests(unittest.TestCase):
    LIMIT = 8.0 / 12.0

    def test_classify_limits(self):
        self.assertEqual(profile.classify(None, self.LIMIT), NO_DATA)
        self.assertEqual(profile.classify(1.0, self.LIMIT), OK)
        self.assertEqual(profile.classify(self.LIMIT, self.LIMIT), OK)  # exactly 8" passes
        self.assertEqual(profile.classify(0.5, self.LIMIT), CLOSE)
        self.assertEqual(profile.classify(0.0, self.LIMIT), OVER)
        self.assertEqual(profile.classify(-0.2, self.LIMIT), OVER)

    def build(self, grades, top=100.0):
        chainages = [float(i) for i in range(len(grades))]
        return profile.build_profile(chainages, grades, [top] * len(grades), self.LIMIT)

    def test_segments_take_worse_end_and_skip_no_data(self):
        points = self.build([98.0, 99.5, None, 99.0, 100.5])
        self.assertEqual(profile.segments(points), [(0, 1, CLOSE), (3, 4, OVER)])

    def test_flagged_runs_find_worst_station(self):
        points = self.build([98.0, 99.5, 99.6, 98.0, 99.7, 100.2, 99.8, 98.0])
        runs = profile.flagged_runs(points)
        self.assertEqual(len(runs), 2)
        self.assertEqual((runs[0]['start'], runs[0]['end'], runs[0]['status']), (1.0, 2.0, CLOSE))
        self.assertEqual(runs[0]['worst'], 2)
        self.assertEqual((runs[1]['start'], runs[1]['end'], runs[1]['status']), (4.0, 6.0, OVER))
        self.assertEqual(runs[1]['worst'], 5)
        self.assertAlmostEqual(runs[1]['clearance'], -0.2)

    def test_no_data_ranges_and_min_clearance(self):
        points = self.build([None, None, 98.0, None])
        self.assertEqual(profile.no_data_ranges(points), [(0.0, 1.0), (3.0, 3.0)])
        self.assertAlmostEqual(profile.min_clearance(points), 2.0)
        self.assertIsNone(profile.min_clearance(self.build([None])))

    def test_note_text(self):
        self.assertEqual(profile.note_text(5.0 / 12), 'GRADE 5" BELOW T/WALL')
        self.assertEqual(profile.note_text(5.5 / 12), 'GRADE 5 1/2" BELOW T/WALL')
        self.assertEqual(profile.note_text(-3.0 / 12), 'GRADE 3" ABOVE T/WALL')
        self.assertEqual(profile.note_text(0.01), 'GRADE AT T/WALL')

    def test_format_feet_inches(self):
        self.assertEqual(profile.format_feet_inches(94.625), '94\'-7 1/2"')
        self.assertEqual(profile.format_feet_inches(-0.5), '-0\'-6"')


class LabelParsingTests(unittest.TestCase):
    def test_parse_word_forms(self):
        self.assertEqual(pdf_grade.parse_word('FG94.25'), ('FG', '94.25', ''))
        self.assertEqual(pdf_grade.parse_word('BW=93.5'), ('BW', '93.5', ''))
        self.assertEqual(pdf_grade.parse_word('94.25FG'), ('', '94.25', 'FG'))
        self.assertEqual(pdf_grade.parse_word('95'), ('', '95', ''))
        self.assertIsNone(pdf_grade.parse_word('(94.10)'))
        self.assertIsNone(pdf_grade.parse_word('2.0%'))
        self.assertIsNone(pdf_grade.parse_word("12.50'"))
        self.assertIsNone(pdf_grade.parse_word('94.125'))

    def test_classify_label(self):
        self.assertEqual(pdf_grade.classify_label('FG', '94'), pdf_grade.SPOT)
        self.assertEqual(pdf_grade.classify_label('', '94.25'), pdf_grade.SPOT)
        self.assertEqual(pdf_grade.classify_label('', '95'), pdf_grade.CONTOUR)
        self.assertIsNone(pdf_grade.classify_label('TW', '96.00'))
        self.assertIsNone(pdf_grade.classify_label('EX', '93.00'))
        self.assertIsNone(pdf_grade.classify_label('XYZ', '93.00'))

    def test_reads_labels_from_pdf_words(self):
        content = (b'BT /F1 10 Tf 100 200 Td (FG 94.25) Tj ET\n'
                   b'BT /F1 10 Tf 100 300 Td (TW 96.00) Tj ET\n'
                   b'BT /F1 10 Tf 400 200 Td (93.50) Tj ET\n'
                   b'BT /F1 10 Tf 600 200 Td (95) Tj ET\n'
                   b'BT /F1 10 Tf 700 200 Td (A-201) Tj ET\n'
                   b'BT /F1 10 Tf 800 200 Td (\\(94.00\\)) Tj ET\n'
                   b'BT /F1 10 Tf 900 200 Td (12) Tj ET\n')
        page = read_page_text(build_pdf(content))
        found = sorted((kind, value) for _, kind, value in pdf_grade.elevation_words(page.words))
        self.assertEqual(found, [('contour', 12.0), ('contour', 95.0),
                                 ('spot', 93.5), ('spot', 94.25)])
        # The elevation range drops the stray 12; placement goes through the pose.
        pose = make_pose((0.0, 0.0), 0.1)
        labels = pdf_grade.elevation_labels(page, pose, (1000, 500), (80.0, 110.0))
        self.assertEqual(sorted(label['value'] for label in labels), [93.5, 94.25, 95.0])
        spot = [label for label in labels if label['value'] == 94.25][0]
        self.assertLess(spot['x'], 0)  # left half of the page

    def test_parse_usgs_elevation(self):
        self.assertEqual(pdf_grade.parse_elevation('5432.50'), 5432.5)
        self.assertEqual(pdf_grade.parse_elevation(' 5432 '), 5432.0)
        self.assertEqual(pdf_grade.parse_elevation("5432'-6\""), 5432.5)
        self.assertAlmostEqual(pdf_grade.parse_elevation("5432'-6 1/2\""), 5432 + 6.5 / 12)
        self.assertAlmostEqual(pdf_grade.parse_elevation("5432' 1/2\""), 5432 + 0.5 / 12)
        self.assertEqual(pdf_grade.parse_elevation("5432'"), 5432.0)
        self.assertAlmostEqual(pdf_grade.parse_elevation("-2'-6\""), -2.5)
        self.assertIsNone(pdf_grade.parse_elevation(''))
        self.assertIsNone(pdf_grade.parse_elevation('USGS'))
        self.assertIsNone(pdf_grade.parse_elevation("5'-1/0\""))

    def test_datum_round_trip(self):
        z = pdf_grade.to_internal(94.25, origin_internal_z=-3.0, origin_reported_z=100.0)
        self.assertAlmostEqual(z, -8.75)
        self.assertAlmostEqual(pdf_grade.to_reported(z, -3.0, 100.0), 94.25)


def straight_path(length=40.0):
    """Exterior face along +x from (0, 0), exterior toward -y."""
    return [{'chainage': c, 'x': c, 'y': 0.0, 'nx': 0.0, 'ny': -1.0}
            for c in profile.stations(length, 10.0)]


class AlongWallTests(unittest.TestCase):
    def label(self, x, y, value):
        return {'x': x, 'y': y, 'value': value}

    def test_project_keeps_exterior_band_only(self):
        labels = [self.label(5.0, -3.0, 94.0),     # outside, kept
                  self.label(15.0, 4.0, 99.0),     # inside the building
                  self.label(20.0, -15.0, 90.0),   # past the band
                  self.label(-6.0, -2.0, 93.0),    # just before the start
                  self.label(70.0, -2.0, 93.0)]    # far past the end
        hits = pdf_grade.project_labels(straight_path(), labels)
        self.assertEqual([(round(c, 3), round(o, 3), v) for c, o, v in hits],
                         [(-6.0, 2.0, 93.0), (5.0, 3.0, 94.0)])

    def test_project_keeps_nearer_duplicate(self):
        labels = [self.label(5.0, -6.0, 90.0), self.label(5.2, -1.0, 94.0)]
        hits = pdf_grade.project_labels(straight_path(), labels)
        self.assertEqual([hit[2] for hit in hits], [94.0])

    def test_project_on_bent_path(self):
        # Corner at (10, 0) turning to +y; exterior to the right (-y then +x).
        path = [{'chainage': 0.0, 'x': 0.0, 'y': 0.0, 'nx': 0.0, 'ny': -1.0},
                {'chainage': 10.0, 'x': 10.0, 'y': 0.0, 'nx': 0.7071, 'ny': -0.7071},
                {'chainage': 20.0, 'x': 10.0, 'y': 10.0, 'nx': 1.0, 'ny': 0.0}]
        hits = pdf_grade.project_labels(path, [self.label(12.0, 6.0, 95.0)])
        self.assertAlmostEqual(hits[0][0], 16.0)
        self.assertAlmostEqual(hits[0][1], 2.0, places=3)

    def test_interpolate_linear_hold_and_sparse(self):
        samples = [(10.0, 1.0, 94.0), (20.0, 1.0, 96.0), (60.0, 1.0, 90.0)]
        chainages = [0.0, 6.0, 10.0, 15.0, 20.0, 23.0, 40.0, 57.0, 64.0, 70.0]
        self.assertEqual(pdf_grade.interpolate(chainages, samples),
                         [None, 94.0, 94.0, 95.0, 96.0, 96.0, None, 90.0, 90.0, None])

    def test_interpolate_without_samples(self):
        self.assertEqual(pdf_grade.interpolate([0.0, 1.0], []), [None, None])


if __name__ == '__main__':
    unittest.main()
