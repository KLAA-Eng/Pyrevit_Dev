from __future__ import print_function

import math
import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.section_detailer.annotations import (
    BOTTOM,
    LEFT,
    RIGHT,
    TOP,
    break_segment,
    crop_crossings,
    floor_label,
    inset_rect,
    is_concrete,
    lowest_bottoms,
    merge_crossings,
    plate_centers,
    sheathing_layer,
    stud_layer,
    unique_tops,
    visible_top,
)
from lib.section_detailer.matching import (
    METALS_FOLDER,
    STEEL,
    VIEW_SIDE,
    WOOD,
    WOOD_FOLDER,
    best_per_family,
    choose_wood_stack,
    family_base,
    family_matches_base,
    find_catalog_type,
    format_inches,
    is_wood_name,
    member_spec,
    normalize_designation,
    parse_library_filename,
    parse_number,
    parse_catalog_sizes,
    parse_type_catalog,
    pick_library_file,
    rank_candidates,
    shape_key,
    side_designation,
    wood_family_bases,
    wood_material,
    wood_size_key,
)
from lib.section_detailer.outline import boundary_segments, join_collinear
from lib.section_detailer.view_geometry import (
    END_ON,
    IN_PLANE,
    OBLIQUE,
    bounds_center,
    classify_member,
    clip_polygon,
    line_plane_point,
    clip_segment,
    crosses_plane,
    extent_along,
    member_size,
    offset_down,
    ply_offsets,
    rotation_in_view,
    side_segment,
    top_edges,
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
        self.assertEqual(spec['material'], 'Sawn')
        self.assertIsNone(spec['target'])
        self.assertEqual(spec['folder'], WOOD_FOLDER)
        self.assertEqual(spec['bases'], ['6_Lumber_Dimension_Section',
                                         '6_HeavyTimber_Section'])
        self.assertIsNone(member_spec('Rectangular Beam', 'Concrete'))
        flagged = member_spec('Beam 1', 'Rectangular Beam', VIEW_SIDE, wood=True)
        self.assertEqual(flagged['bases'], ['6_Lumber_Dimension_Side', '6_HeavyTimber_Side'])


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

    def test_inches_format_as_lumber_text(self):
        self.assertEqual(format_inches(11.875), '11 7/8')
        self.assertEqual(format_inches(1.75), '1 3/4')
        self.assertEqual(format_inches(12.0), '12')
        self.assertEqual(format_inches(0.5), '1/2')

    def test_material_from_type_or_family(self):
        self.assertEqual(wood_material('2x10'), 'Sawn')
        self.assertEqual(wood_material('1 3/4x11 7/8', 'LVL Beam'), 'LVL')
        self.assertEqual(wood_material('5 1/8x12', 'Glulam-Rectangular'), 'Glulam')
        self.assertEqual(wood_material('3 1/2x11 7/8 PSL'), 'PSL')
        self.assertTrue(is_wood_name('2x10'))
        self.assertTrue(is_wood_name('Beam', 'Dimension Lumber'))
        self.assertTrue(is_wood_name('11 7/8 Beam', 'LVL'))
        self.assertFalse(is_wood_name('Rectangular Beam', 'Concrete'))


class WoodStackTests(unittest.TestCase):
    LVL = [('1 3/4x11 7/8', 1.75, 11.875), ('Rim 1 3/4x11 7/8', 1.75, 11.875),
           ('3 1/2x11 7/8', 3.5, 11.875), ('1 3/4x14', 1.75, 14.0)]
    SAWN = [('PT 2x10', 1.5, 9.25), ('2x10', 1.5, 9.25), ('4x8', 3.5, 7.25),
            ('2x12', 1.5, 11.25)]

    def test_catalog_sizes_follow_the_header(self):
        width_first = (',Width##length##inches,Depth##length##inches,Type Comments##other##\n'
                       '1 3/4x11 7/8,1.75,11.875,LVL\n\n')
        depth_first = (',Depth##length##inches,Width##length##inches,Type Comments##Other##\n'
                       '6x10 WBx,9.5,5.5,WOOD BEAM\n')
        self.assertEqual(parse_catalog_sizes(width_first), [('1 3/4x11 7/8', 1.75, 11.875)])
        self.assertEqual(parse_catalog_sizes(depth_first), [('6x10 WBx', 5.5, 9.5)])
        self.assertEqual(parse_catalog_sizes(CATALOG), [])

    def test_lvl_stacks_single_plies_by_depth(self):
        self.assertEqual(choose_wood_stack(self.LVL, 11.875, 3.5, 'LVL'), ('1 3/4x11 7/8', 2))
        self.assertEqual(choose_wood_stack(self.LVL, 11.875, 5.25, 'LVL'), ('1 3/4x11 7/8', 3))
        self.assertEqual(choose_wood_stack(self.LVL, 14.0, 1.75, 'LVL'), ('1 3/4x14', 1))
        self.assertIsNone(choose_wood_stack(self.LVL, 9.25, 3.5, 'LVL'))

    def test_sawn_stacks_plies_or_uses_a_solid_size(self):
        self.assertEqual(choose_wood_stack(self.SAWN, 9.25, 4.5, 'Sawn'), ('2x10', 3))
        self.assertEqual(choose_wood_stack(self.SAWN, 7.25, 3.5, 'Sawn'), ('4x8', 1))
        self.assertIsNone(choose_wood_stack(self.SAWN, 9.25, 3.5, 'Sawn'))

    def test_solid_materials_prefer_fewest_pieces(self):
        psl = [('1 3/4x11 7/8', 1.75, 11.875), ('3 1/2x11 7/8', 3.5, 11.875)]
        self.assertEqual(choose_wood_stack(psl, 11.875, 3.5, 'PSL'), ('3 1/2x11 7/8', 1))

    def test_side_view_matches_depth_only(self):
        self.assertEqual(choose_wood_stack(self.SAWN, 9.25), ('2x10', 1))
        self.assertEqual(choose_wood_stack(self.LVL, 11.875, material='LVL'),
                         ('1 3/4x11 7/8', 1))
        self.assertEqual(choose_wood_stack(self.SAWN, 1.5, seen_width=True)[0], '2x10')

    def test_modeled_sizes_match_within_a_sixteenth(self):
        self.assertEqual(choose_wood_stack(self.SAWN, 9.26, 3.01, 'Sawn'), ('2x10', 2))
        self.assertIsNone(choose_wood_stack(self.SAWN, 9.5, 3.0, 'Sawn'))


class AnnotationTests(unittest.TestCase):
    RECT = (0.0, 0.0, 10.0, 10.0)

    def test_inset_rect(self):
        self.assertEqual(inset_rect(self.RECT, 0.25), (0.25, 0.25, 9.75, 9.75))
        self.assertIsNone(inset_rect(None))

    def test_horizontal_members_break_at_side_edges(self):
        joist = [(-5, 4), (8, 4), (8, 5), (-5, 5)]
        self.assertEqual(crop_crossings(joist, (1, 0), self.RECT), [(LEFT, 4, 5)])
        through = [(-5, 4), (15, 4), (15, 5), (-5, 5)]
        self.assertEqual(crop_crossings(through, (1, 0), self.RECT),
                         [(LEFT, 4, 5), (RIGHT, 4, 5)])
        inside = [(1, 4), (8, 4), (8, 5), (1, 5)]
        self.assertEqual(crop_crossings(inside, (1, 0), self.RECT), [])

    def test_vertical_members_break_at_top_and_bottom(self):
        column = [(4, 2), (5, 2), (5, 14), (4, 14)]
        self.assertEqual(crop_crossings(column, (0, 1), self.RECT), [(TOP, 4, 5)])
        self.assertEqual(crop_crossings(column, (1, 1), self.RECT), [])

    def test_touching_members_share_one_break(self):
        crossings = [(LEFT, 4.0, 5.0), (LEFT, 5.0, 5.1), (LEFT, 7.0, 8.0),
                     (TOP, 1.0, 2.0)]
        self.assertEqual(merge_crossings(crossings, 0.01),
                         [(LEFT, 4.0, 5.1), (LEFT, 7.0, 8.0), (TOP, 1.0, 2.0)])

    def test_break_lines_keep_the_outside_on_their_right(self):
        self.assertEqual(break_segment(LEFT, 4, 5, self.RECT), ((0, 5), (0, 4)))
        self.assertEqual(break_segment(RIGHT, 4, 5, self.RECT), ((10, 4), (10, 5)))
        self.assertEqual(break_segment(TOP, 4, 5, self.RECT), ((5, 10), (4, 10)))
        self.assertEqual(break_segment(BOTTOM, 4, 5, self.RECT), ((4, 0), (5, 0)))
        self.assertEqual(break_segment(LEFT, 4, 5, self.RECT, outside_on_right=False),
                         ((0, 4), (0, 5)))

    def test_floor_labels(self):
        self.assertEqual(floor_label('3/4" Plywood Subfloor'), 'T/SHEATHING')
        self.assertEqual(floor_label('Floor', ['OSB Sheathing']), 'T/SHEATHING')
        self.assertEqual(floor_label('6" Concrete Slab'), 'T/SLAB')
        self.assertEqual(floor_label('Generic 12"'), 'T/FLOOR')

    def test_floors_at_one_height_share_a_symbol(self):
        tops = [(10.0, 3.0, 'T/SHEATHING'), (10.005, 8.0, 'T/SHEATHING'),
                (0.0, 5.0, 'T/SLAB')]
        self.assertEqual(unique_tops(tops, 0.01),
                         [(0.0, 5.0, 'T/SLAB'), (10.005, 8.0, 'T/SHEATHING')])


class ElevationAndSheathingTests(unittest.TestCase):
    TRIM = (0.0, 0.0, 10.0, 10.0)

    def test_tops_show_only_inside_the_crop(self):
        beam = [(2.0, 4.0), (3.0, 4.0), (3.0, 5.0), (2.0, 5.0)]
        self.assertEqual(visible_top(beam, 'T/STEEL', self.TRIM), (5.0, 3.0, 'T/STEEL'))
        above = [(2.0, 11.0), (3.0, 12.0)]
        self.assertIsNone(visible_top(above, 'T/STEEL', self.TRIM))
        aside = [(11.0, 4.0), (12.0, 5.0)]
        self.assertIsNone(visible_top(aside, 'T/STEEL', self.TRIM))
        long_floor = [(-5.0, 6.0), (20.0, 6.5)]
        self.assertEqual(visible_top(long_floor, 'T/SHEATHING', self.TRIM)[1], 10.0)
        self.assertEqual(visible_top(above, 'T/STEEL', None), (12.0, 3.0, 'T/STEEL'))

    def test_sheathing_layer_from_materials(self):
        layers = [('Finish Flooring', 0.05), ('Plywood, Sheathing', 0.0625), ('Wood Joist', 1.0)]
        self.assertEqual(sheathing_layer('Wood Floor', layers), (0.05, 0.0625))
        self.assertEqual(sheathing_layer('3/4 OSB Sheathing', [('Default', 0.0625)]),
                         (0.0, 0.0625))
        self.assertIsNone(sheathing_layer('Concrete Slab', [('Concrete', 0.5)]))

    def test_stud_layer_from_materials_or_type_name(self):
        wall = [('Plywood, Sheathing', 0.05, False), ('Wood Stud Layer', 5.5 / 12, True),
                ('Gypsum Wall Board', 0.05, False)]
        self.assertEqual(stud_layer('Exterior - 2x6 Wood Stud', wall), (0.05, 5.5 / 12))
        generic = [('Default', 0.05, False), ('Default', 3.5 / 12, True)]
        self.assertEqual(stud_layer('Interior - 2x4 Wood Stud', generic), (0.05, 3.5 / 12))
        self.assertEqual(stud_layer('2x6 Stud', [('Default', 0.5, False)]), (0.0, 0.5))
        self.assertIsNone(stud_layer('8" CMU', [('Masonry - CMU', 0.6667, True)]))
        self.assertIsNone(stud_layer('Generic - 8"', generic))

    def test_concrete_walls_by_structure_material_or_name(self):
        wall = [('Concrete, Cast-in-Place', 0.6667, True), ('Gypsum Wall Board', 0.05, False)]
        self.assertTrue(is_concrete('Basic Wall 8"', wall))
        self.assertTrue(is_concrete('8" Concrete', [('Default', 0.6667, False)]))
        stud = [('Concrete Board', 0.05, False), ('Wood Stud Layer', 0.4583, True)]
        self.assertFalse(is_concrete('Exterior Stud Wall', stud))
        self.assertFalse(is_concrete('8" CMU', [('Masonry - CMU', 0.6667, True)]))

    def test_soil_goes_under_the_lowest_footings(self):
        upper = [(0.0, -1.0), (2.0, 0.0)]
        lower = [(5.0, -3.0), (7.0, -2.0)]
        level = [(9.0, -2.99), (10.0, -2.0)]
        self.assertEqual(lowest_bottoms([upper, lower, level, []], 0.05),
                         [(5.0, 7.0, -3.0), (9.0, 10.0, -2.99)])
        self.assertEqual(lowest_bottoms([], 0.05), [])

    def test_plates_stack_down_from_the_top_and_up_from_the_bottom(self):
        plate = 1.5 / 12
        centers = plate_centers(0.0, 9.0, 2.0, None)
        self.assertEqual(len(centers), 3)
        self.assertAlmostEqual(centers[0][1], 9.0 - plate / 2)
        self.assertAlmostEqual(centers[1][1], 9.0 - plate * 1.5)
        self.assertAlmostEqual(centers[2][1], plate / 2)
        self.assertEqual(len(plate_centers(0.0, 9.0, 2.0, (0.0, 1.0, 10.0, 20.0))), 2)
        self.assertEqual(plate_centers(0.0, 0.3, 2.0, None), [])


class OutlineTests(unittest.TestCase):
    @staticmethod
    def square(u, v, size=1.0):
        return [[(u, v), (u + size, v), (u + size, v + size), (u, v + size)]]

    @staticmethod
    def total(segments):
        return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segments)

    def test_shared_edges_are_dropped(self):
        segments = join_collinear(boundary_segments([self.square(0, 0), self.square(1, 0)]))
        self.assertEqual(len(segments), 4)
        self.assertAlmostEqual(self.total(segments), 6.0)

    def test_partial_overlap_keeps_the_exposed_part(self):
        segments = boundary_segments([self.square(0, 0, 2.0), self.square(2, 1)])
        self.assertAlmostEqual(self.total(segments), 10.0)

    def test_edges_inside_another_region_are_dropped(self):
        segments = boundary_segments([self.square(0, 0, 4.0), self.square(1, 1)])
        self.assertAlmostEqual(self.total(segments), 16.0)

    def test_corners_are_not_joined(self):
        segments = join_collinear([((0, 0), (1, 0)), ((1, 0), (1, 1)), ((1, 1), (2, 1))])
        self.assertEqual(len(segments), 3)


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

    def test_regions_clip_to_the_crop(self):
        wall = [(0.0, -2.0), (1.0, -2.0), (1.0, 20.0), (0.0, 20.0)]
        clipped = clip_polygon(wall, (-5.0, 0.0, 5.0, 10.0))
        self.assertEqual(sorted(clipped), [(0.0, 0.0), (0.0, 10.0), (1.0, 0.0), (1.0, 10.0)])
        self.assertEqual(clip_polygon(wall, (2.0, 0.0, 5.0, 10.0)), [])
        self.assertEqual(clip_polygon(wall, None), wall)

    def test_grid_meets_the_section_plane(self):
        point = line_plane_point((10.0, -50.0, 0.0), (10.0, 50.0, 0.0), (0.0, 3.0, 0.0),
                                 (0.0, 1.0, 0.0))
        self.assertEqual(point, (10.0, 3.0, 0.0))
        self.assertIsNone(line_plane_point((0.0, 3.0, 0.0), (10.0, 3.0, 0.0), (0.0, 0.0, 0.0),
                                           (0.0, 1.0, 0.0)))

    def test_roof_top_edges_follow_the_slope(self):
        # A 6:12 roof cut face with plumb ends, wound either way.
        roof = [(0.0, 0.0), (4.0, 2.0), (4.0, 3.0), (0.0, 1.0)]
        for loop in (roof, roof[::-1]):
            self.assertEqual(top_edges(loop), [((0.0, 1.0), (4.0, 3.0))])
        flat = [(0.0, 0.0), (5.0, 0.0), (5.0, 1.0), (0.0, 1.0)]
        self.assertEqual(top_edges(flat), [((0.0, 1.0), (5.0, 1.0))])

    def test_offset_down_is_square_to_the_segment(self):
        start, end = offset_down(((0.0, 1.0), (4.0, 3.0)), math.sqrt(5.0))
        self.assertAlmostEqual(start[0], 1.0)
        self.assertAlmostEqual(start[1], -1.0)
        self.assertAlmostEqual(end[0], 5.0)
        self.assertAlmostEqual(end[1], 1.0)
        self.assertEqual(offset_down(((0.0, 2.0), (3.0, 2.0)), 0.5), ((0.0, 1.5), (3.0, 1.5)))

    def test_member_size_is_square_to_the_axis(self):
        # A 3 1/2 wide x 11 7/8 deep beam, 10 ft long, skewed 45 deg in plan.
        half = math.sqrt(0.5)
        axis = (half, half, 0.0)
        across = (-half, half, 0.0)
        points = []
        for length in (0.0, 10.0):
            for width in (-1.75 / 12, 1.75 / 12):
                for height in (0.0, 11.875 / 12):
                    points.append(tuple(length * a + width * c + (height if i == 2 else 0.0)
                                        for i, (a, c) in enumerate(zip(axis, across))))
        depth, width = member_size(points, axis, (0.0, 0.0, 1.0))
        self.assertAlmostEqual(depth * 12, 11.875)
        self.assertAlmostEqual(width * 12, 3.5)
        tilted = member_size(points, axis, (0.1, 0.1, 1.0))
        self.assertAlmostEqual(tilted[0] * 12, 11.875)
        self.assertIsNone(member_size(points, axis, axis))

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
