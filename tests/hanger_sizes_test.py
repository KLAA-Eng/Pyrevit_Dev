from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.hanger_check.classify import (
    STATUS_NO_SUPPORTING,
    STATUS_OK,
    STATUS_REVIEW,
    STATUS_REVIEW_DETAILS,
    apply_review,
    is_problem,
    match_label,
)
from lib.hanger_check.sizes import (
    KIND_COLUMN,
    KIND_STEEL,
    KIND_WALL,
    MISMATCH_BOTH,
    MISMATCH_SUPPORTED,
    MISMATCH_SUPPORTING,
    MOUNT_FACE,
    MOUNT_TOP_FLANGE,
    MOUNT_WEB_PACKOUT,
    compare_size,
    compare_supporting,
    has_top_flange,
    mismatch_label,
    mounting_label,
    parse_member,
    parse_size,
    support_kind,
)


class ParseSizeTest(unittest.TestCase):
    def test_hanger_key_formats(self):
        self.assertEqual(parse_size('6 3/4x15 GLB'),
                         {'plies': None, 'width': 6.75, 'depth': 15.0, 'material': 'GLB', 'series': None})
        self.assertEqual(parse_size('(3)14" LVL'),
                         {'plies': 3, 'width': None, 'depth': 14.0, 'material': 'LVL', 'series': None})
        self.assertEqual(parse_size('(2)9 1/2" LVL')['depth'], 9.5)
        self.assertEqual(parse_size('(2)2x10'),
                         {'plies': 2, 'width': 2.0, 'depth': 10.0, 'material': None, 'series': None})

    def test_revit_type_labels(self):
        self.assertEqual(parse_size('Glulam: 6 3/4" x 15"')['width'], 6.75)
        self.assertEqual(parse_size('LVL 2.0E: 1-3/4" x 11-7/8"')['depth'], 11.875)
        self.assertEqual(parse_size('TJI 210: 11 7/8"')['depth'], 11.875)

    def test_non_breaking_space_in_fraction(self):
        # Hanger schedules write 7<no-break space>1/4"; IronPython's regex space misses it.
        joist = u'7' + chr(0xa0) + u'1/4" LVL'
        self.assertEqual(parse_size(joist)['depth'], 7.25)
        self.assertTrue(compare_size(joist, 'LVL_Framing_KLAA_15SE: 7 1/4" LVL', 1.75, 7.25)[0])


class CompareSizeTest(unittest.TestCase):
    def test_glulam_header_matches(self):
        self.assertEqual(compare_size('6 3/4x15 GLB', 'Glulam: 6 3/4" x 15"'), (True, ''))

    def test_glulam_header_wrong_depth(self):
        ok, reason = compare_size('6 3/4x15 GLB', 'Glulam: 6 3/4" x 13 1/2"')
        self.assertFalse(ok)
        self.assertEqual(reason, 'depth differs (hanger vs member: depth 15" vs 13 1/2" '
                                 'from type name)')

    def test_family_name_and_codes_are_not_sizes(self):
        member = parse_member('Framing_KLAA_15SE: (2)11 7/8" LVL')
        self.assertEqual((member['plies'], member['depth'], member['material']),
                         (2, 11.875, 'LVL'))
        self.assertIsNone(parse_member('Framing_KLAA_15SE: Custom')['depth'])
        self.assertIsNone(parse_size('LVL 15SE')['depth'])
        self.assertEqual(parse_member('TJI 210: 11 7/8"')['series'], 'TJI 210')
        self.assertTrue(compare_size('(2)11 7/8" LVL', 'Framing_KLAA_15SE: (2)11 7/8" LVL',
                                     3.5, 15.0)[0])
        self.assertTrue(compare_size('(2)11 7/8" LVL', 'Framing_KLAA_15SE: 3 1/2" x 11 7/8"')[0])

    def test_type_name_depth_wins_over_parameter(self):
        # '(2)11 7/8" LVL' type whose depth parameter holds something else.
        self.assertTrue(compare_size('(2)11 7/8" LVL', 'LVL: (2)11 7/8" LVL', 3.5, 24.0)[0])
        self.assertTrue(compare_size('(2)11 7/8" LVL', 'LVL 2.0E: (2)11 7/8"', 3.5, 9.25)[0])
        self.assertEqual(compare_size('(2)11 7/8" LVL', 'LVL: (2)9 1/2" LVL', 3.5, 11.875),
                         (False, 'depth differs (hanger vs member: depth 11 7/8" vs 9 1/2" '
                                 'from type name)'))
        ok, reason = compare_size('6 3/4x15 GLB', 'Glulam: GL-1', 6.75, 12.0)
        self.assertIn('from depth parameter', reason)

    def test_ply_lvl_must_be_modeled_full_width(self):
        self.assertTrue(compare_size('(3)14" LVL', 'LVL: 5 1/4" x 14"')[0])
        self.assertEqual(compare_size('(3)14" LVL', 'LVL: 1 3/4" x 14"'),
                         (False, 'width differs (hanger vs member: width 5 1/4" vs 1 3/4")'))
        self.assertFalse(compare_size('(3)14" LVL', 'LVL: 3 1/2" x 14"')[0])

    def test_material_mismatch(self):
        ok, reason = compare_size('(2)9 1/2" LVL', 'Parallam PSL: 3 1/2" x 9 1/2"')
        self.assertFalse(ok)
        self.assertEqual(reason, 'material differs')

    def test_parameters_used_when_label_has_no_size(self):
        self.assertTrue(compare_size('6 3/4x15 GLB', 'Glulam: GL-1', 6.75, 15.0)[0])
        self.assertFalse(compare_size('6 3/4x15 GLB', 'Glulam: GL-1', 6.75, 12.0)[0])

    def test_sawn_lumber_plies_are_1_1_2_inch(self):
        self.assertTrue(compare_size('(2)2x10', 'Dimension Lumber: 3x10')[0])
        self.assertTrue(compare_size('(2)2x10', 'Dimension Lumber: (2)2x10')[0])
        self.assertTrue(compare_size('(2)2x10', 'Dimension Lumber: Double', 3.0, 9.25)[0])
        self.assertTrue(compare_size('(1)2x8', 'Dimension Lumber: 2x8')[0])
        self.assertFalse(compare_size('(2)2x10', 'Dimension Lumber: 2x10')[0])

    def test_undecided_without_sizes(self):
        self.assertIsNone(compare_size('SEE PLAN', 'LVL: 1 3/4" x 14"')[0])
        self.assertIsNone(compare_size('(3)14" LVL', 'LVL: Custom')[0])


class StrictSupportedTest(unittest.TestCase):
    def test_tji_series_must_agree(self):
        self.assertTrue(compare_size('11 7/8" TJI 360', 'TJI 360: 11 7/8"')[0])
        ok, reason = compare_size('11 7/8" TJI 360', 'TJI 210: 11 7/8"')
        self.assertFalse(ok)
        self.assertEqual(reason, 'series differs')

    def test_nominal_lumber_matches_actual_size(self):
        self.assertTrue(compare_size('2x8', 'Dimension Lumber: 1 1/2" x 7 1/4"')[0])
        self.assertTrue(compare_size('2x10', 'Dimension Lumber: 2x10')[0])
        self.assertFalse(compare_size('2x10', 'Dimension Lumber: 1 1/2" x 7 1/4"')[0])

    def test_ply_type_name_with_full_width_parameter(self):
        # '(2)11 7/8" LVL' type modeled as one member 3 1/2" wide.
        for label, width in (('LVL: (2)11 7/8" LVL', 3.5), ('LVL: 2-PLY 11 7/8', 3.5)):
            self.assertTrue(compare_size('(2)11 7/8" LVL', label, width, 11.875)[0], label)
        self.assertTrue(compare_size('(3)11 7/8" LVL', 'LVL: (3)11 7/8" LVL', 5.25, 11.875)[0])
        self.assertTrue(compare_size('(2)11 7/8" LVL', 'LVL: (2)1 3/4" x 11 7/8"')[0])

    def test_member_type_plies_vs_modeled_width(self):
        self.assertEqual(compare_size('(2)11 7/8" LVL', 'LVL: (2)11 7/8" LVL', 1.75, 11.875),
                         (False, 'member width/width differs (hanger vs member: type (2) '
                                 'needs 3 1/2", modeled 1 3/4", width 3 1/2" vs 1 3/4")'))

    def test_hanger_and_member_plies_must_agree(self):
        self.assertEqual(compare_size('(3)11 7/8" LVL', 'LVL: (2)11 7/8" LVL', 3.5, 11.875),
                         (False, 'plies/width differs (hanger vs member: (3) vs (2), '
                                 'width 5 1/4" vs 3 1/2")'))

    def test_unknown_material_is_noted(self):
        self.assertEqual(compare_size('(2)11 7/8" LVL', 'Rectangular: 3 1/2" x 11 7/8"'),
                         (True, 'material LVL not confirmed'))


class LooseSupportingTest(unittest.TestCase):
    def test_alternatives(self):
        self.assertTrue(compare_supporting('LVL OR 2x8', 'Dimension Lumber: 2x8')[0])
        self.assertTrue(compare_supporting('(2)LVL OR PACKOUT', 'LVL: 3 1/2" x 14"')[0])
        self.assertIsNone(compare_supporting('(2)LVL OR PACKOUT', 'Parallam PSL: 5 1/4" x 14"')[0])
        self.assertFalse(compare_supporting('LVL', 'Parallam PSL: 5 1/4" x 14"')[0])

    def test_width_not_checked(self):
        self.assertTrue(compare_supporting('6 3/4x15 GLB', 'Glulam: 5 1/8" x 15"')[0])

    def test_steel(self):
        self.assertTrue(compare_supporting('WF BEAM', 'W Shapes: W12X26')[0])
        self.assertFalse(compare_supporting('WF BEAM', 'LVL: 3 1/2" x 14"')[0])
        self.assertIsNone(compare_supporting('(2)LVL OR PACKOUT', 'W Shapes: W12X26')[0])

    def test_wall_supports_not_compared(self):
        for header in ('2x PLATE', '(2)LVL LEDGE', 'CONCRETE WALL', 'HSS COLUMN'):
            self.assertIsNone(compare_supporting(header, 'LVL: 3 1/2" x 14"')[0], header)


class MountingTest(unittest.TestCase):
    def test_support_kind(self):
        self.assertEqual(support_kind('WF BEAM'), KIND_STEEL)
        self.assertEqual(support_kind('(2)LVL OR PACKOUT', 'W-Wide Flange: W16X31'), KIND_STEEL)
        self.assertEqual(support_kind('2x PLATE'), KIND_WALL)
        self.assertEqual(support_kind('(2)LVL LEDGE'), KIND_WALL)
        self.assertEqual(support_kind('CONCRETE WALL'), KIND_WALL)
        self.assertEqual(support_kind('HSS COLUMN'), KIND_COLUMN)
        self.assertIsNone(support_kind('(1)LVL FASCIA'))
        self.assertIsNone(support_kind('(2)LVL OR PACKOUT', 'LVL: 3 1/2" x 14"'))

    def test_top_flange(self):
        self.assertFalse(has_top_flange('--'))
        self.assertFalse(has_top_flange(None))
        self.assertTrue(has_top_flange('(6)1 1/2"x0.148"'))

    def test_labels(self):
        self.assertEqual(mounting_label(KIND_STEEL, '(6)1 1/2"x0.148"'), MOUNT_TOP_FLANGE)
        self.assertEqual(mounting_label(KIND_STEEL, '--'), MOUNT_WEB_PACKOUT)
        self.assertEqual(mounting_label(KIND_WALL, '--'), 'Face mounted - wall ledger or plate')
        self.assertEqual(mounting_label(KIND_WALL, '(4)10d'), 'Top flange mounted - wall ledger or plate')
        self.assertEqual(mounting_label(KIND_COLUMN, ''), 'Face mounted - column, see detail')
        self.assertEqual(mounting_label(None, '--'), MOUNT_FACE)
        self.assertEqual(mounting_label(None, '(4)10d'), MOUNT_TOP_FLANGE)


class ReviewStatusTest(unittest.TestCase):
    def _result(self, status=STATUS_OK):
        return {'status': status, 'skew_deg': None, 'notes': []}

    def test_mismatch_is_review(self):
        result = apply_review(self._result(), MISMATCH_SUPPORTED)
        self.assertEqual(result['status'], STATUS_REVIEW)
        self.assertTrue(is_problem(result))
        self.assertEqual(match_label(result), 'Yes')

    def test_wall_is_review_details_not_problem(self):
        result = apply_review(self._result(STATUS_NO_SUPPORTING), '', wall_or_column=True)
        self.assertEqual(result['status'], STATUS_REVIEW_DETAILS)
        self.assertFalse(is_problem(result))
        self.assertEqual(match_label(result), 'Yes')

    def test_wall_mismatch_is_review(self):
        result = apply_review(self._result(), MISMATCH_SUPPORTED, wall_or_column=True)
        self.assertEqual(result['status'], STATUS_REVIEW)

    def test_location_problem_wins(self):
        result = apply_review(self._result(STATUS_NO_SUPPORTING), MISMATCH_SUPPORTED)
        self.assertEqual(result['status'], STATUS_NO_SUPPORTING)
        self.assertEqual(apply_review(self._result(), '')['status'], STATUS_OK)


class MismatchLabelTest(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(mismatch_label(True, True), '')
        self.assertEqual(mismatch_label(None, None), '')
        self.assertEqual(mismatch_label(False, True), MISMATCH_SUPPORTED)
        self.assertEqual(mismatch_label(None, False), MISMATCH_SUPPORTING)
        self.assertEqual(mismatch_label(False, False), MISMATCH_BOTH)

    def test_mismatch_is_a_problem(self):
        result = {'status': STATUS_OK, 'mismatch': MISMATCH_SUPPORTED}
        self.assertTrue(is_problem(result))
        self.assertFalse(is_problem({'status': STATUS_OK, 'mismatch': ''}))


class SourceEncodingTest(unittest.TestCase):
    def test_sources_are_ascii_for_ironpython(self):
        # IronPython 2.7 refuses non-ASCII source without a coding line.
        folders = [os.path.join(PROJECT_ROOT, 'lib', 'hanger_check')]
        pulldown = os.path.join(PROJECT_ROOT, 'KL&A Tools_dev.tab', '05 DevSandbox.panel',
                                'Prototype.pulldown')
        folders += [os.path.join(pulldown, name) for name in
                    ('Check Hanger Locations.pushbutton', 'Hanger Highlights.pushbutton',
                     'Zoom to Selection.pushbutton')]
        for folder in folders:
            for name in os.listdir(folder):
                if name.endswith('.py'):
                    with open(os.path.join(folder, name), 'rb') as stream:
                        data = stream.read()
                    self.assertFalse(any(byte > 127 for byte in bytearray(data)),
                                     '%s contains non-ASCII text' % name)


if __name__ == '__main__':
    unittest.main()
