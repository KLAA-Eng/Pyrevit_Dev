from __future__ import print_function

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
    STATUS_SHARED,
    classify_hanger,
    flag_shared_ends,
    matches_family,
    member_roles,
)


def _member(member_id, start, end):
    return {'id': member_id, 'start': start, 'end': end}


# Header along X at y=0; joist along Y ending at the header face (y=0.15).
HEADER = _member(1, (-10.0, 0.0, 10.0), (10.0, 0.0, 10.0))
JOIST = _member(2, (2.0, 0.15, 10.0), (2.0, 14.0, 10.0))
HANGER = (2.0, 0.15, 10.0)


class ClassifyHangerTest(unittest.TestCase):
    def test_joist_into_header(self):
        result = classify_hanger(HANGER, [HEADER, JOIST])
        self.assertEqual(result['status'], STATUS_OK)
        self.assertEqual(result['supported'], 2)
        self.assertEqual(result['supported_end'], 0)
        self.assertEqual(result['supporting'], 1)

    def test_supported_member_end_point(self):
        reversed_joist = _member(2, (2.0, 14.0, 10.0), (2.0, 0.15, 10.0))
        result = classify_hanger(HANGER, [HEADER, reversed_joist])
        self.assertEqual(result['supported'], 2)
        self.assertEqual(result['supported_end'], 1)

    def test_no_framing(self):
        self.assertEqual(classify_hanger(HANGER, [])['status'], STATUS_NO_FRAMING)

    def test_header_only_has_no_supported_member(self):
        result = classify_hanger(HANGER, [HEADER])
        self.assertEqual(result['status'], STATUS_NO_SUPPORTED)
        self.assertEqual(result['supporting'], 1)

    def test_joist_only_has_no_supporting_member(self):
        result = classify_hanger(HANGER, [JOIST])
        self.assertEqual(result['status'], STATUS_NO_SUPPORTING)
        self.assertEqual(result['supported'], 2)

    def test_parallel_member_is_not_supporting(self):
        rim = _member(3, (2.5, -10.0, 10.0), (2.5, 10.0, 10.0))
        result = classify_hanger(HANGER, [JOIST, rim])
        self.assertIsNone(result['supporting'])

    def test_member_out_of_vertical_reach_is_ignored(self):
        low_header = _member(1, (-10.0, 0.0, 7.0), (10.0, 0.0, 7.0))
        result = classify_hanger(HANGER, [low_header, JOIST])
        self.assertEqual(result['status'], STATUS_NO_SUPPORTING)

    def test_running_member_preferred_over_member_ending_here(self):
        stub = _member(4, (2.0, -0.4, 10.0), (-6.0, -0.4, 10.0))
        result = classify_hanger(HANGER, [stub, HEADER, JOIST])
        self.assertEqual(result['supporting'], 1)

    def test_closest_end_wins_and_tie_is_noted(self):
        far_joist = _member(5, (2.0, -0.15, 10.0), (2.0, -14.0, 10.0))
        result = classify_hanger(HANGER, [HEADER, far_joist, JOIST])
        self.assertEqual(result['supported'], 2)
        self.assertEqual(result['notes'], [])
        centred = classify_hanger((2.0, 0.0, 10.0), [HEADER, far_joist, JOIST])
        self.assertEqual(len(centred['notes']), 1)


class ResultSetTest(unittest.TestCase):
    def test_shared_end_flags_both_hangers(self):
        results = {10: classify_hanger(HANGER, [HEADER, JOIST]),
                   11: classify_hanger((2.1, 0.15, 10.0), [HEADER, JOIST])}
        flag_shared_ends(results)
        self.assertEqual(results[10]['status'], STATUS_SHARED)
        self.assertIn('Id 11', results[10]['notes'][-1])
        self.assertIn('Id 10', results[11]['notes'][-1])

    def test_member_roles(self):
        girder = _member(6, (-10.2, -20.0, 10.0), (-10.2, 20.0, 10.0))
        header_end = classify_hanger((-10.0, 0.0, 10.0), [girder, HEADER])
        joist_end = classify_hanger(HANGER, [HEADER, JOIST])
        roles = member_roles({20: header_end, 21: joist_end})
        self.assertEqual(roles, {1: ROLE_BOTH, 2: ROLE_SUPPORTED, 6: ROLE_SUPPORTING})

    def test_matches_family(self):
        self.assertTrue(matches_family('HANGERS_CLEVER_KLAA - Face'))
        self.assertFalse(matches_family('Simpson LUS'))
        self.assertFalse(matches_family(None))


if __name__ == '__main__':
    unittest.main()
