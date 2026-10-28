from __future__ import print_function

import math
import os
import shutil
import sys
import tempfile
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.pdf_overlay.geometry import (
    fit_pose,
    image_size_feet,
    initial_feet_per_pixel,
    make_pose,
    pixel_to_view,
    rotated_canvas_size,
    snap_rotation,
    view_to_pixel,
)
from lib.pdf_overlay.state import (
    default_cache_root,
    load_state,
    make_state,
    overlay_paths,
    overlay_stem,
    save_state,
    stem_from_image_name,
    validate_state,
)
from lib.pdf_overlay.style import (
    DEFAULT_OPACITY,
    apply_color_matrix,
    clamp_opacity,
    color_matrix,
    tint_rgb,
)


PAGE = (3600, 2400)


class PdfOverlayGeometryTests(unittest.TestCase):
    def assertPointAlmostEqual(self, expected, actual, places=6):
        self.assertAlmostEqual(expected[0], actual[0], places=places)
        self.assertAlmostEqual(expected[1], actual[1], places=places)

    def test_initial_scale_matches_printed_view_scale(self):
        # 1/8" = 1'-0" is scale 96: one inch on paper is eight feet.
        self.assertAlmostEqual(8.0 / 150.0, initial_feet_per_pixel(96, 150))
        with self.assertRaises(ValueError):
            initial_feet_per_pixel(0, 150)

    def test_page_center_maps_to_pose_center_and_y_points_up(self):
        pose = make_pose((10.0, 20.0), 0.5)
        self.assertPointAlmostEqual((10.0, 20.0), pixel_to_view(pose, PAGE, (1800, 1200)))
        # Pixel rows grow downward, so a lower row is lower in the view.
        self.assertPointAlmostEqual((10.0, 15.0), pixel_to_view(pose, PAGE, (1800, 1210)))

    def test_view_to_pixel_inverts_pixel_to_view(self):
        pose = make_pose((-4.0, 7.5), 0.03, math.radians(33.0))
        for pixel in ((0, 0), (3600, 2400), (1234.5, 87.25)):
            point = pixel_to_view(pose, PAGE, pixel)
            self.assertPointAlmostEqual(pixel, view_to_pixel(pose, PAGE, point))

    def test_fit_pose_recovers_known_similarity(self):
        expected = make_pose((100.0, -50.0), 0.0625, math.radians(17.0))
        pixels = [(300.0, 400.0), (3100.0, 2000.0)]
        targets = [pixel_to_view(expected, PAGE, pixel) for pixel in pixels]
        pose = fit_pose(PAGE, pixels, targets)
        self.assertAlmostEqual(expected['feet_per_pixel'], pose['feet_per_pixel'])
        self.assertAlmostEqual(expected['rotation'], pose['rotation'])
        self.assertPointAlmostEqual(expected['center'], pose['center'])

    def test_fit_pose_snaps_small_pick_error_to_orthogonal(self):
        pixels = [(300.0, 400.0), (3100.0, 400.0)]
        # A horizontal grid span picked with a 0.2 degree wobble.
        wobble = math.radians(0.2)
        length = 2800.0 * 0.05
        targets = [(0.0, 0.0), (length * math.cos(wobble), length * math.sin(wobble))]
        pose = fit_pose(PAGE, pixels, targets)
        self.assertEqual(0.0, pose['rotation'])
        self.assertAlmostEqual(0.05, pose['feet_per_pixel'], places=5)
        # The fit splits the residual evenly between the two picks.
        first = pixel_to_view(pose, PAGE, pixels[0])
        second = pixel_to_view(pose, PAGE, pixels[1])
        self.assertAlmostEqual(-first[1], second[1] - targets[1][1], places=6)

    def test_fit_pose_keeps_deliberate_rotation_and_quarter_turns(self):
        pixels = [(0.0, 0.0), (1000.0, 0.0)]
        rotated = fit_pose(PAGE, pixels, [(0.0, 0.0), (10.0, 10.0)])
        self.assertAlmostEqual(math.radians(45.0), rotated['rotation'])
        quarter = fit_pose(PAGE, pixels, [(0.0, 0.0), (0.05, 10.0)])
        self.assertAlmostEqual(math.pi / 2.0, quarter['rotation'])
        half = fit_pose(PAGE, pixels, [(0.0, 0.0), (-10.0, 0.01)])
        self.assertAlmostEqual(math.pi, half['rotation'])

    def test_fit_pose_rejects_coincident_picks(self):
        with self.assertRaises(ValueError):
            fit_pose(PAGE, [(10.0, 10.0), (12.0, 10.0)], [(0.0, 0.0), (5.0, 0.0)])
        with self.assertRaises(ValueError):
            fit_pose(PAGE, [(10.0, 10.0), (900.0, 10.0)], [(0.0, 0.0), (0.01, 0.0)])

    def test_snap_rotation_window(self):
        self.assertEqual(0.0, snap_rotation(math.radians(0.4)))
        self.assertIsNone(snap_rotation(math.radians(0.6)))
        self.assertAlmostEqual(-math.pi / 2.0, snap_rotation(math.radians(-89.7)))

    def test_rotated_canvas_size(self):
        self.assertEqual((3600, 2400), rotated_canvas_size(3600, 2400, 0.0))
        self.assertEqual((2400, 3600), rotated_canvas_size(3600, 2400, math.pi / 2.0))
        width, height = rotated_canvas_size(100, 100, math.radians(45.0))
        self.assertEqual((142, 142), (width, height))

    def test_image_size_uses_rotated_canvas(self):
        pose = make_pose((0.0, 0.0), 0.5, math.pi / 2.0)
        self.assertEqual((1200.0, 1800.0), image_size_feet(pose, PAGE))


class PdfOverlayStyleTests(unittest.TestCase):
    def test_white_paper_is_clear_and_black_lines_take_opacity(self):
        matrix = color_matrix(tint_rgb('Red'), 60)
        white = apply_color_matrix(matrix, (1.0, 1.0, 1.0, 1.0))
        black = apply_color_matrix(matrix, (0.0, 0.0, 0.0, 1.0))
        self.assertAlmostEqual(0.0, white[3])
        self.assertAlmostEqual(0.6, black[3])
        self.assertAlmostEqual(220 / 255.0, black[0])
        self.assertEqual(0.0, black[1])

    def test_original_tint_keeps_source_color(self):
        matrix = color_matrix(tint_rgb('Original'), 100)
        pixel = apply_color_matrix(matrix, (0.2, 0.4, 0.6, 1.0))
        self.assertEqual((0.2, 0.4, 0.6), pixel[:3])

    def test_zero_opacity_hides_everything(self):
        matrix = color_matrix(tint_rgb('Blue'), 0)
        self.assertEqual(0.0, apply_color_matrix(matrix, (0.0, 0.0, 0.0, 1.0))[3])

    def test_clamp_opacity_and_unknown_tint(self):
        self.assertEqual(100, clamp_opacity(140))
        self.assertEqual(0, clamp_opacity(-3))
        self.assertEqual(DEFAULT_OPACITY, clamp_opacity('abc'))
        self.assertEqual(tint_rgb('Red'), tint_rgb('Chartreuse'))


class PdfOverlayStateTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.folder)

    def test_cache_root_prefers_local_app_data(self):
        root = default_cache_root({'LOCALAPPDATA': 'C:\\Local'})
        self.assertEqual(os.path.join('C:\\Local', 'KLA Tools', 'PDF Overlay'), root)

    def test_stem_round_trips_through_image_type_name(self):
        stem = overlay_stem('C:\\x\\24343_Snake River Lodge_S24 East roof plan.pdf', 1, 'ab12cd34')
        self.assertEqual('pdfoverlay_24343-Snake-River-Lodge-S24-East-roof-pl_p1_ab12cd34', stem)
        paths = overlay_paths(self.folder, stem)
        self.assertEqual(stem, stem_from_image_name(os.path.basename(paths['overlay'])))
        self.assertEqual(stem, stem_from_image_name(paths['overlay']))
        self.assertIsNone(stem_from_image_name('site photo.png'))
        self.assertIsNone(stem_from_image_name(stem + '.jpg'))
        self.assertIsNone(stem_from_image_name(None))

    def test_state_save_and_load_round_trip(self):
        state = make_state('C:\\plans.pdf', 2, 150, (3600, 2400),
                           make_pose((1.0, 2.0), 0.05, 0.1), 'Blue', 45)
        path = overlay_paths(self.folder, 'pdfoverlay_x_p2_1')['state']
        save_state(path, state)
        save_state(path, state)
        self.assertEqual(state, load_state(path))

    def test_validate_state_rejects_bad_scale_and_repairs_tint(self):
        state = make_state('C:\\plans.pdf', 1, 150, (10, 10), make_pose((0, 0), 0.05))
        state['tint'] = 'Plaid'
        self.assertEqual('Red', validate_state(state)['tint'])
        state['pose']['feet_per_pixel'] = 0
        with self.assertRaises(ValueError):
            validate_state(state)
        with self.assertRaises(ValueError):
            validate_state({'pdf_path': 'x'})


if __name__ == '__main__':
    unittest.main()
