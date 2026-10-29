from __future__ import print_function

import math
import os
import sys
import unittest
import zlib


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.pdf_overlay.geometry import make_pose
from lib.pdf_overlay.members import (
    CAMBER_DIFFER,
    CONFLICT,
    MATCH,
    MISMATCH,
    STUDS_DIFFER,
    UNREADABLE,
    choose_type,
    describe_member,
    find_size_spans,
    format_inches,
    label_in_view,
    label_mark,
    match_members,
    parse_extras,
    parse_inches,
    parse_size,
    revision_plan,
    size_labels,
    sort_labels,
)
from lib.pdf_overlay.pdftext import PageText, PdfError, parse_cmap, read_page_text


def build_pdf(content, compress=False, rotate=0, to_unicode=None):
    """Return bytes of a one-page PDF drawing content with font /F1."""
    stream = zlib.compress(content) if compress else content
    filter_entry = b' /Filter /FlateDecode' if compress else b''
    font = b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica'
    if to_unicode is not None:
        font += b' /ToUnicode 5 0 R'
    font += b' /FirstChar 32 /Widths [' + b' '.join([b'500'] * 96) + b'] >>'
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 1000 500] >>',
        b'<< /Type /Page /Parent 2 0 R /Rotate ' + str(rotate).encode('ascii') +
        b' /Resources << /Font << /F1 4 0 R >> >> /Contents 6 0 R >>',
        font,
        b'<< /Length ' + str(len(to_unicode or b'')).encode('ascii') + b' >>\nstream\n' +
        (to_unicode or b'') + b'\nendstream',
        b'<< /Length ' + str(len(stream)).encode('ascii') + filter_entry + b' >>\nstream\n' +
        stream + b'\nendstream',
    ]
    out = [b'%PDF-1.4\n']
    for number, body in enumerate(objects, 1):
        out.append(str(number).encode('ascii') + b' 0 obj\n' + body + b'\nendobj\n')
    out.append(b'trailer\n<< /Root 1 0 R >>\n%%EOF\n')
    return b''.join(out)


CONTENT = (b'BT /F1 10 Tf 100 200 Td (W12x26) Tj ET\n'
           b'BT /F1 10 Tf 0 1 -1 0 300 50 Tm [(HSS5x5) -100 (x3/8)] TJ ET\n'
           b'q 2 0 0 2 0 0 cm BT /F1 5 Tf 400 100 Td (S16) Tj ET Q\n')


def words_by_text(page):
    return dict((word.text, word) for word in page.words)


class PdfTextTests(unittest.TestCase):
    def test_reads_words_with_positions_and_directions(self):
        for compress in (False, True):
            page = read_page_text(build_pdf(CONTENT, compress=compress))
            words = words_by_text(page)
            self.assertIn('W12x26', words)
            self.assertAlmostEqual(100.0, words['W12x26'].x)
            self.assertAlmostEqual(200.0, words['W12x26'].y)
            self.assertAlmostEqual(30.0, words['W12x26'].length)
            # Rotated by Tm; the small TJ kern stays inside the word.
            self.assertIn('HSS5x5x3/8', words)
            self.assertAlmostEqual(0.0, words['HSS5x5x3/8'].ux)
            self.assertAlmostEqual(1.0, words['HSS5x5x3/8'].uy)
            # The cm scale applies to position and glyph height.
            self.assertAlmostEqual(800.0, words['S16'].x)
            self.assertAlmostEqual(10.0, words['S16'].size)

    def test_word_span_keeps_glyph_positions(self):
        page = read_page_text(build_pdf(b'BT /F1 10 Tf 0 0 Td (W12x26W8x10) Tj ET'))
        word = page.words[0]
        spans = list(find_size_spans(word.text))
        self.assertEqual(['W12X26', 'W8X10'], [span[3] for span in spans])
        second = word.span(spans[1][0], spans[1][1])
        self.assertEqual('W8x10', second.text)
        self.assertAlmostEqual(30.0, second.x)

    def test_to_unicode_maps_subset_codes(self):
        cmap = (b'begincmap 2 beginbfchar <01> <0057> <02> <0031> endbfchar '
                b'1 beginbfrange <03> <05> <0032> endbfrange endcmap')
        self.assertEqual({1: u'W', 2: u'1', 3: u'2', 4: u'3', 5: u'4'}, parse_cmap(cmap))
        page = read_page_text(build_pdf(b'BT /F1 10 Tf 0 0 Td <0102030405> Tj ET', to_unicode=cmap))
        self.assertEqual(['W1234'], [word.text for word in page.words])

    def test_page_to_unit_follows_rotation(self):
        page = PageText([], (0.0, 0.0, 1000.0, 500.0), 0)
        self.assertEqual((0.1, 0.6), page.page_to_unit(100.0, 200.0))
        rotated = PageText([], (0.0, 0.0, 1000.0, 500.0), 90)
        self.assertEqual((500.0, 1000.0), rotated.display_size())
        self.assertEqual((0.4, 0.1), rotated.page_to_unit(100.0, 200.0))

    def test_missing_page_and_encryption_are_reported(self):
        with self.assertRaises(PdfError):
            read_page_text(build_pdf(CONTENT), page_number=2)
        with self.assertRaises(PdfError):
            read_page_text(build_pdf(CONTENT).replace(b'/Root 1 0 R', b'/Root 1 0 R /Encrypt 9 0 R'))


class SizeParsingTests(unittest.TestCase):
    def test_sizes_compare_numerically_and_ignore_case_and_marks(self):
        self.assertEqual(parse_size('W12x26')[0], parse_size('w12X26')[0])
        self.assertEqual(parse_size('*W18x65')[0], parse_size('W18X65')[0])
        self.assertEqual(parse_size('HSS5x5x3/8')[0], parse_size('HSS5X5X.375')[0])
        self.assertEqual(parse_size('HSS6x4x1/4')[0], parse_size('HSS6X4X0.25')[0])
        self.assertNotEqual(parse_size('W12x26')[0], parse_size('W12x19')[0])
        self.assertEqual('W12X26', parse_size('W-Wide Flange : W12x26')[1])

    def test_non_sizes_are_ignored(self):
        for text in ('S16', 'CFS', 'SHEET', '1/4" = 1\'-0"', '', None, 'HSS'):
            self.assertIsNone(parse_size(text), text)

    def test_spans_split_run_together_labels(self):
        spans = list(find_size_spans('W12x19W12x19W16x31'))
        self.assertEqual(['W12X19', 'W12X19', 'W16X31'], [span[3] for span in spans])
        self.assertEqual([(0, 6), (6, 12), (12, 18)], [span[:2] for span in spans])


class LabelPlacementTests(unittest.TestCase):
    def test_label_maps_through_page_raster_and_pose(self):
        page = read_page_text(build_pdf(CONTENT))
        word = words_by_text(page)['W12x26']
        # Raster at 2 px per point; pose: 0.5 ft per px, page center at (10, 20).
        pose = make_pose((10.0, 20.0), 0.5)
        center, direction, height = label_in_view(word, page, pose, (2000, 1000))
        cx, cy = word.center()
        self.assertAlmostEqual(10.0 + (cx - 500.0), center[0])
        self.assertAlmostEqual(20.0 + (cy - 250.0), center[1])
        self.assertEqual((1.0, 0.0), direction)
        self.assertAlmostEqual(10.0, height)

    def test_pose_rotation_turns_label_direction(self):
        page = read_page_text(build_pdf(CONTENT))
        pose = make_pose((0.0, 0.0), 0.5, math.pi / 2.0)
        labels = dict((label['text'], label) for label in size_labels(page, pose, (2000, 1000)))
        self.assertAlmostEqual(0.0, labels['W12X26']['direction'][0])
        self.assertAlmostEqual(1.0, labels['W12X26']['direction'][1])


def label(text, center, direction=(1.0, 0.0), height=1.0):
    key, display = parse_size(text)
    return {'text': display, 'key': key, 'center': center,
            'direction': direction, 'height': height}


def member(member_id, size, start, end):
    parsed = parse_size(size)
    return {'id': member_id, 'size': size, 'key': parsed[0] if parsed else None,
            'start': start, 'end': end}


class MatchMembersTests(unittest.TestCase):
    def setUp(self):
        # Two horizontal beams 6 ft apart and one vertical girder.
        self.members = [
            member(1, 'W12X26', (0.0, 0.0), (20.0, 0.0)),
            member(2, 'W12X26', (0.0, 6.0), (20.0, 6.0)),
            member(3, 'W16X31', (25.0, -5.0), (25.0, 15.0)),
            member(4, 'W8X10', (40.0, 0.0), (50.0, 0.0)),
            member(5, 'Custom Joist', (0.0, -10.0), (20.0, -10.0)),
        ]

    def test_classifies_match_mismatch_conflict_and_leftovers(self):
        labels = [
            label('W12x26', (10.0, 1.0)),                       # beam 1 match
            label('W12x19', (10.0, 5.0)),                       # beam 2 mismatch
            label('W16x31', (24.0, 5.0), (0.0, 1.0)),           # girder match
            label('W8x10', (42.0, 0.8)),                        # beam 4 ...
            label('W8x12', (48.0, 0.8)),                        # ... conflict
            label('W14x22', (60.0, 30.0)),                      # nothing near
            label('W12x26', (10.0, -9.0)),                      # unreadable Revit size
        ]
        result = match_members(labels, self.members)
        status = dict((row['id'], row['status']) for row in result['rows'])
        self.assertEqual({1: MATCH, 2: MISMATCH, 3: MATCH, 4: CONFLICT, 5: UNREADABLE}, status)
        mismatch = [row for row in result['rows'] if row['id'] == 2][0]
        self.assertEqual(('W12X26', 'W12X19'), (mismatch['revit'], mismatch['pdf']))
        self.assertEqual(['W14X22'], [item['text'] for item in result['unmatched_labels']])
        self.assertEqual([], result['unlabelled'])

    def test_label_goes_to_nearest_parallel_member_only(self):
        # Closer to the vertical girder, but horizontal like beam 1.
        result = match_members([label('W12x26', (23.5, 1.0))], self.members, tolerance_feet=4.5)
        self.assertEqual([1], [row['id'] for row in result['rows']])
        # Too far from any member at this tolerance.
        result = match_members([label('W12x26', (10.0, 3.0))], self.members, tolerance_feet=1.0)
        self.assertEqual([], result['rows'])
        self.assertEqual(1, len(result['unmatched_labels']))
        self.assertEqual(5, len(result['unlabelled']))

    def test_angle_tolerance_admits_skewed_labels(self):
        skewed = label('W12x26', (10.0, 1.0), (math.cos(math.radians(20)), math.sin(math.radians(20))))
        self.assertEqual([], match_members([skewed], self.members)['rows'])
        result = match_members([skewed], self.members, max_angle=25.0)
        self.assertEqual([1], [row['id'] for row in result['rows']])


class StudsAndCamberTests(unittest.TestCase):
    def test_parse_extras_reads_common_plan_forms(self):
        cases = {
            ' (14) c=3/4"': (14, 0.75),
            ' [24] c=1"': (24, 1.0),
            ' (6,8)': (14, None),
            ' c=1 1/4"': (None, 1.25),
            ' c=1-1/2': (None, 1.5),
            ' C=.75': (None, 0.75),
            ' (HIGH)': (None, None),
            ' 51K': (None, None),
            '': (None, None),
        }
        for text, expected in cases.items():
            extras = parse_extras(text)
            self.assertEqual(expected, (extras['studs'], extras['camber']), text)

    def test_inches_round_trip(self):
        self.assertEqual(0.75, parse_inches('3/4"'))
        self.assertEqual(1.25, parse_inches('1 1/4'))
        self.assertIsNone(parse_inches('none'))
        self.assertEqual(['3/4"', '1"', '1 1/4"', '1/16"'],
                         [format_inches(value) for value in (0.75, 1.0, 1.25, 0.06)])
        self.assertEqual('W16X26 (14) c=3/4"', describe_member('W16X26', 14, 0.75))
        self.assertEqual('W16X26', describe_member('W16X26', None, 0.0))

    def test_labels_pick_up_studs_and_camber_from_following_words(self):
        content = (b'BT /F1 10 Tf 100 200 Td (W16x26) Tj ET\n'
                   b'BT /F1 10 Tf 140 200 Td (\\(14\\)) Tj ET\n'
                   b'BT /F1 10 Tf 170 200 Td (c=3/4") Tj ET\n'
                   b'BT /F1 10 Tf 100 100 Td (W12x19\\(8\\)W12x26) Tj ET\n'
                   b'BT /F1 10 Tf 100 50 Td (W8x10) Tj ET\n'
                   b'BT /F1 10 Tf 400 50 Td (\\(20\\)) Tj ET\n')
        page = read_page_text(build_pdf(content))
        labels = dict((label['display'], label) for label in
                      size_labels(page, make_pose((0.0, 0.0), 0.1), (1000, 500)))
        self.assertIn('W16X26 (14) c=3/4"', labels)
        self.assertEqual((14, 0.75), (labels['W16X26 (14) c=3/4"']['studs'],
                                      labels['W16X26 (14) c=3/4"']['camber']))
        # Studs between two sizes belong to the first; distant text is not a tail.
        self.assertIn('W12X19 (8)', labels)
        self.assertIn('W12X26', labels)
        self.assertIn('W8X10', labels)

    def setUp(self):
        self.beam = member(1, 'W16X26', (0.0, 0.0), (20.0, 0.0))
        self.beam.update({'studs': 10, 'camber': 0.5})

    def test_studs_and_camber_differences_are_flagged_after_size(self):
        def status_for(text, studs=None, camber=None):
            item = label(text, (10.0, 1.0))
            item.update({'studs': studs, 'camber': camber})
            return match_members([item], [self.beam])['rows'][0]['status']

        self.assertEqual(MATCH, status_for('W16x26'))
        self.assertEqual(MATCH, status_for('W16x26', 10, 0.5))
        self.assertEqual(STUDS_DIFFER, status_for('W16x26', 14))
        self.assertEqual(CAMBER_DIFFER, status_for('W16x26', 10, 0.75))
        self.assertEqual(MISMATCH, status_for('W18x35', 14, 0.75))

    def test_revision_plan_sets_only_what_the_pdf_shows(self):
        item = label('W18x35', (10.0, 1.0))
        item.update({'studs': 14, 'camber': 0.75})
        row = match_members([item], [self.beam])['rows'][0]
        plan = revision_plan(row, self.beam)
        self.assertEqual((parse_size('W18x35')[0], 'W18X35'), plan['size'])
        self.assertEqual((14, 0.75, None), (plan['studs'], plan['camber'], plan['skip']))

        size_only = label('W18x35', (10.0, 1.0))
        plan = revision_plan(match_members([size_only], [self.beam])['rows'][0], self.beam)
        self.assertEqual((None, None), (plan['studs'], plan['camber']))

        same = label('W16x26', (10.0, 1.0))
        plan = revision_plan(match_members([same], [self.beam])['rows'][0], self.beam)
        self.assertEqual('Already matches the PDF.', plan['skip'])
        self.assertEqual('No PDF label is matched to this member.', revision_plan(None, self.beam)['skip'])

    def test_conflicting_labels_are_not_revised(self):
        first, second = label('W16x26', (5.0, 1.0)), label('W16x26', (15.0, 1.0))
        first['studs'], second['studs'] = 10, 14
        row = match_members([first, second], [self.beam])['rows'][0]
        self.assertEqual(CONFLICT, row['status'])
        self.assertIn('disagree', revision_plan(row, self.beam)['skip'])

    def test_choose_type_prefers_the_members_family(self):
        key = parse_size('W18x35')[0]
        candidates = [('W Shapes', key, 'other family'), ('W-Wide Flange', key, 'same family'),
                      ('W-Wide Flange', parse_size('W18x40')[0], 'wrong size')]
        self.assertEqual('same family', choose_type(candidates, key, 'W-Wide Flange'))
        self.assertEqual('other family', choose_type(candidates, key, 'Custom'))
        self.assertIsNone(choose_type(candidates, parse_size('W21x44')[0], 'W-Wide Flange'))


class LabelMarkTests(unittest.TestCase):
    def test_mark_circle_is_the_match_window_and_line_follows_label(self):
        mark = label_mark(label('W12x26', (10.0, 5.0), (0.0, 1.0)), 2.5)
        self.assertEqual((10.0, 5.0), mark['center'])
        self.assertEqual(2.5, mark['radius'])
        self.assertEqual(((10.0, 2.5), (10.0, 7.5)), mark['line'])

    def test_sort_labels_groups_by_size_then_position(self):
        labels = [label('W16x26', (0.0, 0.0)), label('W12x19', (5.0, 0.0)),
                  label('W12x19', (1.0, 0.0)), label('W12x19', (1.0, 9.0))]
        ordered = [(item['text'], item['center']) for item in sort_labels(labels)]
        self.assertEqual([('W12X19', (1.0, 9.0)), ('W12X19', (1.0, 0.0)),
                          ('W12X19', (5.0, 0.0)), ('W16X26', (0.0, 0.0))], ordered)


if __name__ == '__main__':
    unittest.main()
