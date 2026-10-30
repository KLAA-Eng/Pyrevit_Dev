from __future__ import print_function

import math
import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.section_detailer.matching import (
    METALS_FOLDER,
    STEEL,
    VIEW_SIDE,
    WOOD,
    WOOD_FOLDER,
    best_per_family,
    family_base,
    family_matches_base,
    find_catalog_type,
    member_spec,
    normalize_designation,
    parse_library_filename,
    parse_number,
    parse_type_catalog,
    parse_wood,
    pick_library_file,
    rank_candidates,
    shape_key,
    side_designation,
    wood_family_bases,
    wood_size_key,
)
from lib.section_detailer.view_geometry import (
    END_ON,
    IN_PLANE,
    OBLIQUE,
    bounds_center,
    classify_member,
    clip_segment,
    crosses_plane,
    extent_along,
    ply_offsets,
    rotation_in_view,
    side_segment,
    to_view,
    width_direction,
)


CATALOG = (
    ',W##other##,A##area##inches,d##length##inches,Type Comments##other##\n'
    'W44x335,335,98.5,44,W44x335\n'
    'W12x26,26,7.65,12.2,W12x26\n'
    '\n'
)


class DesignationTests(unittest.TestCase):
    def test_revit_catalog_and_typed_names_normalize_together(self):
        expected = normalize_designation('W12x26')
        self.assertEqual(expected, 'W12X26')
        self.assertEqual(normalize_designation('W12X26'), expected)
        self.assertEqual(normalize_designation(' w 12x26 '), expected)
        self.assertEqual(normalize_designation(None), '')

    def test_round_hss_decimal_zeros_are_insignificant(self):
        self.assertEqual(normalize_designation('HSS20.000X0.500'),
                         normalize_designation('HSS20x0.5'))
        self.assertEqual(normalize_designation('HSS6x.250'), 'HSS6X0.25')

    def test_fractions_are_kept(self):
        self.assertEqual(normalize_designation('L8x8x1-1/8'), 'L8X8X1-1/8')
        self.assertEqual(normalize_designation('Pipe1/2STD'), 'PIPE1/2STD')

    def test_shape_keys_use_longest_prefix(self):
        self.assertEqual(shape_key('W12X26'), 'W')
        self.assertEqual(shape_key('WT22x167.5'), 'WT')
        self.assertEqual(shape_key('HP14x117'), 'HP')
        self.assertEqual(shape_key('MC12x10.6'), 'MC')
        self.assertEqual(shape_key('C15x50'), 'C')
        self.assertEqual(shape_key('L8x8x1'), 'L')
        self.assertEqual(shape_key('HSS20x12x5/8'), 'HSS_RECT')
        self.assertEqual(shape_key('HSS20x0.500'), 'HSS_ROUND')
        self.assertEqual(shape_key('Pipe3/4STD'), 'PIPE')

    def test_unsupported_names_have_no_shape(self):
        self.assertIsNone(shape_key('S12x35'))
        self.assertIsNone(shape_key('Wood 2x10'))
        self.assertIsNone(shape_key(''))

    def test_family_base_follows_klaa_naming(self):
        self.assertEqual(family_base('W'), '5_WideFlange_Section')
        self.assertEqual(family_base('MC'), '5_Channel_Section')
        self.assertEqual(family_base('HSS_ROUND', 'Side'), '5_HSS_Round_Side')
        self.assertIsNone(family_base(None))


class SideAndSpecTests(unittest.TestCase):
    def test_rect_hss_side_uses_seen_face_and_wall(self):
        self.assertEqual(side_designation('HSS8X4X1/4'), 'HSS8X1/4')
        self.assertEqual(side_designation('HSS8X4X1/4', show_width=True), 'HSS4X1/4')
        self.assertEqual(normalize_designation('HSS5-1/2x1/4'),
                         side_designation('HSS5-1/2X3X1/4'))
        self.assertEqual(side_designation('W12X26'), 'W12X26')

    def test_steel_spec(self):
        spec = member_spec('W12X26', 'W-Wide Flange')
        self.assertEqual(spec['kind'], STEEL)
        self.assertEqual(spec['bases'], ['5_WideFlange_Section'])
        self.assertEqual(spec['folder'], METALS_FOLDER)
        side = member_spec('HSS6X4X3/8', view_kind=VIEW_SIDE)
        self.assertEqual(side['target'], 'HSS6X3/8')
        self.assertEqual(side['bases'], ['5_HSS_Side'])

    def test_wood_spec(self):
        spec = member_spec('3-2x10', 'Dimension Lumber')
        self.assertEqual(spec['kind'], WOOD)
        self.assertEqual(spec['plies'], 3)
        self.assertEqual(spec['target'], '2x10')
        self.assertEqual(spec['folder'], WOOD_FOLDER)
        self.assertEqual(spec['bases'], ['6_Lumber_Dimension_Section',
                                         '6_HeavyTimber_Section'])
        self.assertIsNone(member_spec('Rectangular Beam', 'Concrete'))


class WoodTests(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(parse_number('1 3/4'), 1.75)
        self.assertEqual(parse_number('1-3/4'), 1.75)
        self.assertEqual(parse_number('3/4'), 0.75)
        self.assertEqual(parse_number('11.875'), 11.875)
        self.assertIsNone(parse_number('abc'))

    def test_size_keys(self):
        self.assertEqual(wood_size_key('2x10'), (2.0, 10.0))
        self.assertEqual(wood_size_key('PT Sill 2x10'), (2.0, 10.0))
        self.assertEqual(wood_size_key('2x10 WBx'), (2.0, 10.0))
        self.assertEqual(wood_size_key('1 3/4x11 7/8'), (1.75, 11.875))
        self.assertEqual(wood_size_key('1-3/4x11-7/8'), (1.75, 11.875))
        self.assertEqual(wood_size_key('1 1/8x9 1/4RB'), (1.125, 9.25))
        self.assertIsNone(wood_size_key('W12x26'))
        self.assertIsNone(wood_size_key('HSS6x1/4'))

    def test_built_up_plies(self):
        cases = {
            '2x10': (1, '2x10'),
            '3-2x10': (3, '2x10'),
            '(2) 2x12': (2, '2x12'),
            '2x12 (2)': (2, '2x12'),
            '3 PLY 1 3/4x11 7/8 LVL': (3, '1 3/4x11 7/8'),
            '2-1 3/4x11 7/8': (2, '1 3/4x11 7/8'),
            '1-3/4x11-7/8': (1, '1-3/4x11-7/8'),
        }
        for name, (plies, size) in cases.items():
            parsed = parse_wood(name)
            self.assertEqual((parsed['plies'], parsed['size']), (plies, size), name)

    def test_material_from_type_or_family(self):
        self.assertEqual(parse_wood('2x10')['material'], 'Sawn')
        self.assertEqual(parse_wood('1 3/4x11 7/8', 'LVL Beam')['material'], 'LVL')
        self.assertEqual(parse_wood('5 1/8x12', 'Glulam-Rectangular')['material'], 'Glulam')
        self.assertEqual(parse_wood('3 1/2x11 7/8 PSL')['material'], 'PSL')
        self.assertIsNone(parse_wood('Rectangular Beam'))


class LibraryTests(unittest.TestCase):
    def test_library_filenames_parse_revision(self):
        self.assertEqual(parse_library_filename('5_WideFlange_Section_KLAA_12DC.rfa'),
                         ('5_WideFlange_Section', 12))
        self.assertEqual(parse_library_filename('5_WideFlange_Side_KLAA_DC.rfa'),
                         ('5_WideFlange_Side', 0))
        self.assertIsNone(parse_library_filename('5_ShearTab_KLAA_15DC.0001.rfa'))
        self.assertIsNone(parse_library_filename('5_WideFlange_Section_KLAA_12DC.txt'))

    def test_newest_revision_wins(self):
        files = ['5_HSS_Side_KLAA_12DC.rfa', '5_HSS_Side_KLAA_22DC.rfa',
                 '5_HSS_Side_KLAA_22DC.0001.rfa', '5_HSS_Section_KLAA_30DC.rfa']
        self.assertEqual(pick_library_file(files, '5_HSS_Side'),
                         '5_HSS_Side_KLAA_22DC.rfa')
        self.assertIsNone(pick_library_file(files, '5_Angle_Side'))

    def test_loaded_family_matches_any_revision(self):
        self.assertTrue(family_matches_base('5_WideFlange_Section_KLAA_12DC',
                                            '5_WideFlange_Section'))
        self.assertFalse(family_matches_base('5_WideFlange_Side_KLAA_DC',
                                             '5_WideFlange_Section'))

    def test_catalog_types_are_read_in_order(self):
        names = parse_type_catalog(CATALOG)
        self.assertEqual(names, ['W44x335', 'W12x26'])
        self.assertEqual(find_catalog_type(names, 'W12X26'), 'W12x26')
        self.assertIsNone(find_catalog_type(names, 'W14X22'))

    def test_wood_catalog_lookup_prefers_plain_name(self):
        names = ['PT 2x10', 'Rafter 2x10', '2x10', '2x12']
        self.assertEqual(find_catalog_type(names, '2x10', key=wood_size_key), '2x10')
        self.assertEqual(find_catalog_type(['PT 2x10'], '2x10', key=wood_size_key),
                         'PT 2x10')


class RankingTests(unittest.TestCase):
    CANDIDATES = [
        ('Other_Steel_DC', 'W12X26'),
        ('5_WideFlange_Section_KLAA_12DC', 'W12x26'),
        ('Office_WF', 'W12x26'),
        ('5_WideFlange_Section_KLAA_12DC', 'W14x22'),
    ]

    def test_only_exact_designations_match(self):
        ranked = rank_candidates('W12X26', self.CANDIDATES)
        self.assertEqual(len(ranked), 3)
        self.assertNotIn(('5_WideFlange_Section_KLAA_12DC', 'W14x22'), ranked)

    def test_klaa_family_ranks_before_others(self):
        ranked = rank_candidates('W12X26', self.CANDIDATES,
                                 bases='5_WideFlange_Section')
        self.assertEqual(ranked[0], ('5_WideFlange_Section_KLAA_12DC', 'W12x26'))
        self.assertEqual(ranked[1][0], 'Office_WF')

    def test_reference_detail_families_rank_first(self):
        ranked = rank_candidates('W12X26', self.CANDIDATES,
                                 bases=['5_WideFlange_Section'],
                                 preferred_families=['other_steel_dc'])
        self.assertEqual(ranked[0][0], 'Other_Steel_DC')

    def test_no_match_returns_empty(self):
        self.assertEqual(rank_candidates('W8X10', self.CANDIDATES), [])

    def test_wood_prefers_plain_names_and_earlier_bases(self):
        candidates = [
            ('6_Lumber_Dimension_Section_KLAA_12DC', 'PT 2x10'),
            ('6_Lumber_Dimension_Section_KLAA_12DC', '2x10'),
            ('6_HeavyTimber_Section_KLAA_DC', '2x10 WBx'),
            ('6_Lumber_LVL_Section_KLAA_20DC', '1 3/4x11 7/8'),
        ]
        bases = wood_family_bases('Sawn')
        ranked = rank_candidates('2x10', candidates, bases=bases,
                                 key=wood_size_key, family_only=True)
        self.assertEqual(ranked[0], ('6_Lumber_Dimension_Section_KLAA_12DC', '2x10'))
        self.assertEqual(best_per_family(ranked), [
            ('6_Lumber_Dimension_Section_KLAA_12DC', '2x10'),
            ('6_HeavyTimber_Section_KLAA_DC', '2x10 WBx'),
        ])

    def test_wood_sizes_do_not_cross_materials(self):
        candidates = [('6_Lumber_PSL_Section_KLAA_12DC', '1 3/4x11 7/8'),
                      ('Office_Wood', '1 3/4x11 7/8'),
                      ('Office_Wood', '1-3/4x11-7/8')]
        ranked = rank_candidates('1 3/4x11 7/8', candidates,
                                 bases=wood_family_bases('LVL'),
                                 key=wood_size_key, family_only=True)
        self.assertEqual(ranked, [('Office_Wood', '1 3/4x11 7/8')])


class ViewGeometryTests(unittest.TestCase):
    RIGHT = (1.0, 0.0, 0.0)
    UP = (0.0, 0.0, 1.0)
    VIEW = (0.0, -1.0, 0.0)

    def test_members_are_classified_against_the_view_direction(self):
        self.assertEqual(classify_member((0, 10, 0), self.VIEW), END_ON)
        self.assertEqual(classify_member((0, -3, 0.1), self.VIEW), END_ON)
        self.assertEqual(classify_member((5, 0, 0), self.VIEW), IN_PLANE)
        self.assertEqual(classify_member((0, 0, 12), self.VIEW), IN_PLANE)
        self.assertEqual(classify_member((1, 1, 0), self.VIEW), OBLIQUE)
        self.assertEqual(classify_member((0, 0, 0), self.VIEW), OBLIQUE)

    def test_segment_crossing_uses_signed_distances(self):
        origin = (0.0, 0.0, 0.0)
        self.assertTrue(crosses_plane((0, -2, 0), (0, 3, 0), origin, self.VIEW))
        self.assertTrue(crosses_plane((0, 0, 0), (0, 3, 0), origin, self.VIEW))
        self.assertFalse(crosses_plane((0, 1, 0), (0, 3, 0), origin, self.VIEW))

    def test_view_coordinates_and_center(self):
        origin = (10.0, 5.0, 2.0)
        self.assertEqual(to_view((12.0, 99.0, 5.0), origin, self.RIGHT, self.UP),
                         (2.0, 3.0))
        self.assertEqual(bounds_center([(0, 0), (4, 1), (2, 3)]), (2.0, 1.5))
        self.assertIsNone(bounds_center([]))

    def test_rotation_turns_view_up_onto_member_depth(self):
        self.assertEqual(rotation_in_view(self.UP, self.RIGHT, self.UP), 0.0)
        self.assertAlmostEqual(
            rotation_in_view((-1.0, 0.0, 0.0), self.RIGHT, self.UP), math.pi / 2)
        self.assertAlmostEqual(
            rotation_in_view((1.0, 0.0, 0.0), self.RIGHT, self.UP), -math.pi / 2)
        self.assertEqual(rotation_in_view(self.VIEW, self.RIGHT, self.UP), 0.0)

    def test_plies_sit_side_by_side_across_the_width(self):
        self.assertEqual(width_direction((0.0, 1.0)), (1.0, 0.0))
        self.assertEqual(ply_offsets(1, 0.125), [0.0])
        self.assertEqual(ply_offsets(3, 0.125), [-0.125, 0.0, 0.125])
        self.assertEqual(ply_offsets(2, 1.0), [-0.5, 0.5])
        self.assertEqual(extent_along([(0, 0), (4.5, 1)], (1.0, 0.0)), (0, 4.5))

    def test_side_segment_runs_full_length_at_mid_depth(self):
        outline = [(2, 9), (10, 9), (10, 10), (2, 10)]
        self.assertEqual(side_segment(outline, (1, 0), (0, 1)), ((2, 9.5), (10, 9.5)))
        # A depth below the axis flips the line so depth stays counterclockwise.
        start, end = side_segment(outline, (1, 0), (0, -1))
        self.assertEqual((start, end), ((10, 9.5), (2, 9.5)))
        self.assertIsNone(side_segment([], (1, 0), (0, 1)))

    def test_clip_segment_to_crop(self):
        rect = (0.0, 0.0, 10.0, 10.0)
        self.assertEqual(clip_segment((-5, 5), (15, 5), rect), ((0, 5), (10, 5)))
        self.assertEqual(clip_segment((2, 2), (3, 3), rect), ((2, 2), (3, 3)))
        self.assertIsNone(clip_segment((-5, 20), (15, 20), rect))
        self.assertEqual(clip_segment((-5, 5), (15, 5), None), ((-5, 5), (15, 5)))


if __name__ == '__main__':
    unittest.main()
