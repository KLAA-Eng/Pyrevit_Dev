from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.section_check.conditions import (
    ALONG,
    CUT,
    FLOOR,
    FOUNDATION,
    FRAMING,
    SKEW,
    WALL,
    condition,
    detail_content,
    orientation,
    read_label,
    side,
)
from lib.section_check.markers import (
    assign_notes,
    box_segment_distance,
    cut_line,
    note_flags,
    right_of,
)
from lib.section_check.score import (
    compare_detail,
    compare_sections,
    pair_score,
    rating,
)


class NoteFlagTest(unittest.TestCase):
    def test_sim_and_oh_spellings(self):
        for text in ('SIM', 'sim.', 'SIMILAR', '(SIM)', 'SIM OH'):
            self.assertTrue(note_flags(text)['sim'], text)
        for text in ('OH', 'O.H.', 'OPP HAND', 'Opposite Hand', 'SIM OPP', 'SIM, OH'):
            self.assertTrue(note_flags(text)['oh'], text)

    def test_words_containing_the_letters_do_not_count(self):
        for text in ('SIMPSON HANGER', 'JOHN', 'SHOP DWG', 'OHIO', 'OPPOSING'):
            flags = note_flags(text)
            self.assertFalse(flags['sim'] or flags['oh'], text)


class CutLineTest(unittest.TestCase):
    def test_collinear_pieces_and_look_side(self):
        # A broken cut line along X with the head flag drawn on the +Y side.
        line = cut_line([((0.0, 0.0), (4.0, 0.0)), ((6.0, 0.0), (10.0, 0.0)),
                         ((10.0, 0.0), (10.5, 1.0))], [(9.5, 0.8)])
        self.assertEqual(line['start'], (0.0, 0.0))
        self.assertEqual(line['end'], (10.0, 0.0))
        self.assertEqual(line['look'], (0.0, 1.0))

    def test_balanced_symbols_leave_look_unknown(self):
        line = cut_line([((0.0, 0.0), (8.0, 0.0))], [(0.0, 1.0), (0.0, -1.0)])
        self.assertIsNone(line['look'])
        self.assertIsNone(cut_line([]))

    def test_right_of_look(self):
        self.assertEqual(right_of((0.0, 1.0)), (1.0, -0.0))


class NoteAssignmentTest(unittest.TestCase):
    def test_box_segment_distance(self):
        self.assertEqual(box_segment_distance((1, -1), (2, 1), (0, 0), (5, 0)), 0.0)
        self.assertAlmostEqual(box_segment_distance((1, 2), (2, 3), (0, 0), (5, 0)), 2.0)
        self.assertAlmostEqual(box_segment_distance((8, 0), (9, 1), (0, 0), (5, 0)), 3.0)

    def test_note_goes_to_nearest_marker_only(self):
        markers = {1: ((0.0, 0.0), (10.0, 0.0)), 2: ((0.0, 5.0), (10.0, 5.0))}
        notes = [('SIM', (11.0, 0.5), (12.0, 1.0)), ('OH', (11.0, 5.5), (12.0, 6.0)),
                 ('TYP', (11.0, 0.0), (12.0, 0.4)), ('SIM', (40.0, 40.0), (41.0, 41.0))]
        result = assign_notes(markers, notes, reach=3.0)
        self.assertEqual((result[1]['sim'], result[1]['oh']), (True, False))
        self.assertEqual((result[2]['sim'], result[2]['oh']), (False, True))
        self.assertEqual(result[1]['texts'], ['SIM'])


class ConditionTest(unittest.TestCase):
    def test_read_label(self):
        self.assertEqual(read_label('W-Wide Flange: W16x31'), ({'W16X31'}, {'STEEL'}))
        self.assertEqual(read_label('HSS6X6X1/4'), ({'HSS6X6X1/4'}, {'STEEL'}))
        self.assertEqual(read_label('Basic Wall: 8" CMU'), ({'8IN'}, {'CMU'}))
        self.assertEqual(read_label('(2)2x10 DF'), ({'2X10'}, {'WOOD'}))
        self.assertEqual(read_label('(2)1 3/4" x 11 7/8" LVL')[1], {'LVL'})
        self.assertIn('11-7/8IN', read_label('(2)1 3/4" x 11 7/8" LVL')[0])

    def test_orientation_and_side(self):
        right = (1.0, 0.0)
        self.assertEqual(orientation((1.0, 0.2), right), ALONG)
        self.assertEqual(orientation((0.1, 1.0), right), CUT)
        self.assertEqual(orientation((1.0, 1.0), right), SKEW)
        self.assertIsNone(orientation((0.0, 0.0), right))
        self.assertEqual([side(-3.0), side(0.5), side(2.0), side(None)], ['L', 'C', 'R', None])

    def test_detail_content(self):
        content = detail_content(['Wood Joist: 2x10', 'CMU'],
                                 ['8" CMU WALL', 'W16X31 BEAM', '4" SLAB ON GRADE'])
        self.assertEqual(content['groups'], {WALL, FRAMING, FLOOR})
        self.assertTrue({'2X10', '8IN', 'W16X31', '4IN'} <= content['sizes'])
        self.assertTrue({'CMU', 'WOOD', 'STEEL'} <= content['materials'])


def _beam(label='W-Wide Flange: W16X31', orient=CUT, offset=0.0):
    return condition(FRAMING, label, orient, offset)


def _wall(label='8" CMU', orient=ALONG, offset=-2.0):
    return condition(WALL, label, orient, offset)


class SectionScoreTest(unittest.TestCase):
    def test_identical_cuts_match_fully(self):
        result = compare_sections([_beam(), _wall()], [_beam(), _wall()])
        self.assertEqual(result['percent'], 100.0)
        self.assertEqual(result['rating'], 'Likely match')
        self.assertEqual(result['notes'], [])

    def test_size_difference_scores_lower_and_suggests_sim(self):
        here, ref = [_beam('W-Wide Flange: W18X35'), _wall()], [_beam(), _wall()]
        plain = compare_sections(here, ref)
        self.assertEqual(plain['percent'], 87.5)
        self.assertTrue(any('add SIM' in n for n in plain['notes']))
        sim = compare_sections(here, ref, similar=True)
        self.assertEqual(sim['percent'], 95.0)
        self.assertFalse(any('add SIM' in n for n in sim['notes']))

    def test_missing_element_and_other_group(self):
        result = compare_sections([_beam()], [_beam(), _wall(), condition(FOUNDATION, 'Ftg')])
        self.assertEqual(result['percent'], 50.0)
        self.assertTrue(any(n.startswith('Only in reference') for n in result['notes']))
        self.assertEqual(pair_score(_beam(), _wall()), 0.0)

    def test_opposite_hand(self):
        here, ref = [_wall(offset=2.0), _beam()], [_wall(offset=-2.0), _beam()]
        missing = compare_sections(here, ref)
        self.assertEqual(missing['percent'], 90.0)
        self.assertIn('Matches better mirrored: OH may be missing', missing['notes'])
        noted = compare_sections(here, ref, opposite=True)
        self.assertEqual(noted['percent'], 100.0)
        wrong = compare_sections(ref, ref, opposite=True)
        self.assertIn('Matches better mirrored: OH note may be wrong', wrong['notes'])

    def test_unknown_hand_takes_the_better_hand(self):
        result = compare_sections([_wall(offset=2.0)], [_wall(offset=-2.0)], hand_known=False)
        self.assertEqual(result['percent'], 100.0)
        self.assertIn('Hand not checked: marker direction unknown', result['notes'])

    def test_empty_cuts(self):
        self.assertIsNone(compare_sections([], [])['percent'])
        self.assertEqual(rating(None), "Can't tell")
        self.assertEqual(compare_sections([_beam()], [])['percent'], 0.0)


class DetailScoreTest(unittest.TestCase):
    def test_named_sizes_match_fully(self):
        detail = detail_content([], ['W16X31', '8" CMU WALL'])
        result = compare_detail([_beam(), _wall()], detail)
        self.assertEqual(result['percent'], 100.0)

    def test_loose_and_missing(self):
        detail = detail_content([], ['STEEL BEAM', 'CONC FOOTING'])
        result = compare_detail([_beam(), _wall()], detail)
        # Beam by material 0.8, wall unnamed 0, footing missing: 0.8 / 3.
        self.assertEqual(result['percent'], 26.7)
        self.assertEqual(result['rating'], 'Likely mismatch')
        self.assertTrue(any('Foundation' in n for n in result['notes']))
        self.assertTrue(any(n.startswith('Not named in detail') for n in result['notes']))
        sim = compare_detail([_beam()], detail_content([], ['STEEL BEAM']), similar=True)
        self.assertEqual(sim['percent'], 100.0)

    def test_unreadable_detail_and_oh(self):
        result = compare_detail([_beam()], detail_content([], ['SEE ARCH']), opposite=True)
        self.assertIsNone(result['percent'])
        self.assertIn('OH not checked against a drafting view', result['notes'])


if __name__ == '__main__':
    unittest.main()
