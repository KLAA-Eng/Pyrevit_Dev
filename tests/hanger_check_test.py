from __future__ import print_function

import math
import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.hanger_check.classify import (
    ROLE_BOTH,
    ROLE_SUPPORTED,
    ROLE_SUPPORTING,
    STATUS_NO_FRAMING,
    STATUS_NO_SUPPORTED,
    STATUS_NO_SUPPORTING,
    STATUS_OK,
    STATUS_ORIENTATION,
    STATUS_SHARED,
    classify_hanger,
    flag_shared_ends,
    match_label,
    matches_family,
    member_roles,
    slope_label,
)


def _member(member_id, start, end):
    return {'id': member_id, 'start': start, 'end': end}


def _line_at(member_id, through, degrees, half_length=10.0):
    dx = math.cos(math.radians(degrees)) * half_length
    dy = math.sin(math.radians(degrees)) * half_length
    return _member(member_id, (through[0] - dx, through[1] - dy, 10.0),
                   (through[0] + dx, through[1] + dy, 10.0))


# Header along X at y=0; joist along Y ending at the header face (y=0.15).
# The hanger text runs along the joist (plan Y).
HEADER = _member(1, (-10.0, 0.0, 10.0), (10.0, 0.0, 10.0))
JOIST = _member(2, (2.0, 0.15, 10.0), (2.0, 14.0, 10.0))
HANGER = (2.0, 0.15, 10.0)
ALONG_Y = (0.0, 1.0)


class ClassifyHangerTest(unittest.TestCase):
    def test_joist_into_header(self):
        result = classify_hanger(HANGER, [HEADER, JOIST], ALONG_Y)
        self.assertEqual(result['status'], STATUS_OK)
        self.assertEqual((result['supported'], result['supported_end']), (2, 0))
        self.assertEqual(result['supporting'], 1)
        self.assertEqual(result['skew_deg'], 0.0)
        self.assertEqual(match_label(result), 'Yes')
        # The joint is the supported end projected onto the supporting member's line.
        self.assertEqual(result['joint'], (2.0, 0.0, 10.0))

    def test_joint_without_supporting_member(self):
        result = classify_hanger(HANGER, [JOIST], ALONG_Y)
        self.assertEqual(result['joint'], JOIST['start'])
        self.assertIsNone(classify_hanger(HANGER, [HEADER], ALONG_Y)['joint'])

    def test_text_direction_sign_does_not_matter(self):
        result = classify_hanger(HANGER, [HEADER, JOIST], (0.0, -1.0))
        self.assertEqual((result['supported'], result['supporting']), (2, 1))

    def test_orientation_beats_closest_end(self):
        joist = _member(2, (2.0, 0.55, 10.0), (2.0, 14.0, 10.0))
        stub = _member(4, (2.05, 0.15, 10.0), (12.0, 0.15, 10.0))
        result = classify_hanger(HANGER, [stub, HEADER, joist], ALONG_Y)
        self.assertEqual((result['supported'], result['supporting']), (2, 1))

    def test_hanger_turned_across_member(self):
        result = classify_hanger(HANGER, [HEADER, JOIST], (1.0, 0.0))
        self.assertEqual(result['status'], STATUS_ORIENTATION)
        self.assertIsNone(result['supported'])
        self.assertIn('Member Id 2', result['notes'][0])
        self.assertEqual(match_label(result), 'No')

    def test_skewed_supporting_member(self):
        skewed = _line_at(1, (2.0, 0.0), 30.0)
        result = classify_hanger(HANGER, [skewed, JOIST], ALONG_Y)
        self.assertEqual(result['status'], STATUS_OK)
        self.assertEqual(result['skew_deg'], 30.0)
        self.assertEqual(match_label(result), 'Yes (skewed 30.0 deg)')
        self.assertIn('Skewed 30.0 deg', result['notes'])

    def test_skew_beyond_limit_is_not_supporting(self):
        too_skewed = _line_at(1, (2.0, 0.0), 70.0)
        result = classify_hanger(HANGER, [too_skewed, JOIST], ALONG_Y)
        self.assertEqual(result['status'], STATUS_NO_SUPPORTING)

    def test_hanger_box_is_longer_along_text(self):
        along = _member(2, (2.0, 1.9, 10.0), (2.0, 14.0, 10.0))
        across = _member(2, (3.5, 0.15, 10.0), (3.5, 14.0, 10.0))
        self.assertEqual(classify_hanger(HANGER, [HEADER, along], ALONG_Y)['supported'], 2)
        self.assertIsNone(classify_hanger(HANGER, [HEADER, across], ALONG_Y)['supported'])

    def test_without_text_direction(self):
        result = classify_hanger(HANGER, [HEADER, JOIST])
        self.assertEqual((result['supported'], result['supporting']), (2, 1))

    def test_no_framing(self):
        self.assertEqual(classify_hanger(HANGER, [], ALONG_Y)['status'], STATUS_NO_FRAMING)

    def test_header_only_has_no_supported_member(self):
        result = classify_hanger(HANGER, [HEADER], ALONG_Y)
        self.assertEqual(result['status'], STATUS_NO_SUPPORTED)
        self.assertEqual(result['supporting'], 1)

    def test_parallel_member_is_not_supporting(self):
        rim = _member(3, (2.5, -10.0, 10.0), (2.5, 10.0, 10.0))
        result = classify_hanger(HANGER, [JOIST, rim], ALONG_Y)
        self.assertEqual(result['status'], STATUS_NO_SUPPORTING)

    def test_member_out_of_vertical_reach_is_ignored(self):
        low_header = _member(1, (-10.0, 0.0, 7.0), (10.0, 0.0, 7.0))
        result = classify_hanger(HANGER, [low_header, JOIST], ALONG_Y)
        self.assertEqual(result['status'], STATUS_NO_SUPPORTING)

    def test_opposite_joists_tie_is_noted(self):
        far_joist = _member(5, (2.0, -0.15, 10.0), (2.0, -14.0, 10.0))
        result = classify_hanger(HANGER, [HEADER, far_joist, JOIST], ALONG_Y)
        self.assertEqual(result['supported'], 2)
        self.assertEqual(result['notes'], [])
        centred = classify_hanger((2.0, 0.0, 10.0), [HEADER, far_joist, JOIST], ALONG_Y)
        self.assertEqual(len(centred['notes']), 1)


class ResultSetTest(unittest.TestCase):
    def test_shared_end_flags_both_hangers(self):
        results = {10: classify_hanger(HANGER, [HEADER, JOIST], ALONG_Y),
                   11: classify_hanger((2.1, 0.15, 10.0), [HEADER, JOIST], ALONG_Y)}
        flag_shared_ends(results)
        self.assertEqual(results[10]['status'], STATUS_SHARED)
        self.assertIn('Id 11', results[10]['notes'][-1])
        self.assertIn('Id 10', results[11]['notes'][-1])
        self.assertEqual(match_label(results[10]), 'Yes')

    def test_member_roles(self):
        girder = _member(6, (-10.2, -20.0, 10.0), (-10.2, 20.0, 10.0))
        header_end = classify_hanger((-10.0, 0.0, 10.0), [girder, HEADER], (1.0, 0.0))
        joist_end = classify_hanger(HANGER, [HEADER, JOIST], ALONG_Y)
        roles = member_roles({20: header_end, 21: joist_end})
        self.assertEqual(roles, {1: ROLE_BOTH, 2: ROLE_SUPPORTED, 6: ROLE_SUPPORTING})

    def test_matches_family(self):
        self.assertTrue(matches_family('HANGERS_CLEVER_KLAA - Face'))
        self.assertFalse(matches_family('Simpson LUS'))
        self.assertFalse(matches_family(None))


class SlopeLabelTest(unittest.TestCase):
    def test_flat_and_sloped(self):
        self.assertEqual(slope_label((0.0, 0.0, 10.0), (12.0, 0.0, 10.0)), 'Flat')
        self.assertEqual(slope_label((0.0, 0.0, 10.0), (20.0, 0.0, 10.05)), 'Flat')
        self.assertEqual(slope_label((0.0, 0.0, 10.0), (12.0, 0.0, 14.0)), 'Sloped 4.0:12 (18.4 deg)')
        self.assertEqual(slope_label((0.0, 12.0, 14.0), (0.0, 0.0, 10.0)), 'Sloped 4.0:12 (18.4 deg)')


if __name__ == '__main__':
    unittest.main()
