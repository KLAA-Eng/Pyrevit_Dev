"""Deterministic artwork generation; actual WPF rendering has a separate probe."""
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gui_icon_generator', ROOT / 'scripts' / 'generate_gui_icons.py')
icons = importlib.util.module_from_spec(spec)
spec.loader.exec_module(icons)
P = '{' + icons.WPF + '}'
X = '{' + icons.XAML + '}'


class GuiIconTests(unittest.TestCase):
    def test_generated_geometry_dictionary_is_a_leaf_that_matches_the_sources(self):
        self.assertEqual(17, len(icons.ROLES))
        self.assertEqual(icons.generate_icons(), (icons.ASSETS / 'KLCodeIcons.xaml').read_text(encoding='utf-8'))
        dictionary = ET.fromstring(icons.generate_icons())
        self.assertEqual({P + 'GeometryGroup'}, {node.tag for node in dictionary})
        self.assertEqual({'Kla' + role + 'Geometry' for role in icons.ROLES}, {node.attrib.get(X + 'Key') for node in dictionary})
        self.assertNotIn('StaticResource', icons.generate_icons())

    def test_foundation_block_draws_every_role_with_the_token_pen_and_text_brush(self):
        foundation = icons.FOUNDATION.read_text(encoding='utf-8')
        self.assertEqual(foundation, icons.apply_foundation_block(foundation, icons.generate_images()))
        block = ET.fromstring('<ResourceDictionary xmlns="%s" xmlns:x="%s">%s</ResourceDictionary>' % (
            icons.WPF, icons.XAML, icons.generate_images().split('\n', 1)[1].rsplit('\n', 2)[0]))
        images = block.findall(P + 'DrawingImage')
        self.assertEqual({'KlaIcon' + role for role in icons.ROLES}, {image.attrib.get(X + 'Key') for image in images})
        for image in images:
            drawing = image.find('.//' + P + 'GeometryDrawing')
            self.assertEqual('Transparent', drawing.attrib['Brush'])
            self.assertEqual('0,0,24,24', drawing.find('.//' + P + 'RectangleGeometry').attrib['Rect'])
            for part in image.findall('.//' + P + 'GeometryDrawing')[1:]:
                self.assertEqual('{StaticResource KlaGuiIconPen}', part.attrib['Pen'])
                self.assertIn(part.attrib.get('Brush', '{StaticResource KlaTextBrush}'), ('{StaticResource KlaTextBrush}',))
        self.assertIn('x:Key="KlaGuiIconPen" Brush="{StaticResource KlaTextBrush}" Thickness="{StaticResource KlaIconStroke}"', foundation)
        self.assertIn('<ResourceDictionary Source="../../_icons/gui/KLCodeIcons.xaml"/>', foundation)
        tokens = (ROOT / 'lib' / 'GUI' / 'Resources' / 'KLCodeFoundationTokens.xaml').read_text(encoding='utf-8')
        self.assertNotIn('KLCodeIcons.xaml', tokens, 'icons are merged by the foundation, not by the tokens')

    def test_wordmark_geometry_is_generated_from_the_svg_at_the_origin(self):
        self.assertEqual(icons.generate_wordmark(), icons.WORDMARK_XAML.read_text(encoding='utf-8'))
        dictionary = ET.fromstring(icons.generate_wordmark())
        keys = [node.attrib.get(X + 'Key') for node in dictionary]
        self.assertEqual(['KlaWordmarkSlashGeometry', 'KlaWordmarkLettersGeometry', 'KlaWordmarkCanvasWidth', 'KlaWordmarkCanvasHeight'], keys)
        for geo in dictionary.findall(P + 'PathGeometry'):
            shift = geo.find('.//' + P + 'TranslateTransform')
            self.assertEqual(('-32', '-64'), (shift.attrib['X'], shift.attrib['Y']))
        primitives = (ROOT / 'lib' / 'GUI' / 'Resources' / 'KLCodeSharedPrimitives.xaml').read_text(encoding='utf-8')
        self.assertIn('Data="{StaticResource KlaWordmarkSlashGeometry}"', primitives)
        self.assertIn('Fill="{StaticResource KlaBorderBrush}"', primitives)
        self.assertNotIn('#33714F', primitives)

    def test_path_points_tracks_relative_commands(self):
        points = icons.path_points('M 10,10 h 5 v -2 l 1,1 c 1,1 2,2 3,3 Z')
        self.assertEqual((10.0, 10.0), points[0])
        self.assertEqual((19.0, 12.0), points[-1])

    def test_conversion_preserves_circle_and_rounded_rectangle_geometry(self):
        name, attrs = icons.geometry(ET.fromstring('<circle cx="11" cy="11" r="8"/>'))
        self.assertEqual(('EllipseGeometry', {'Center': '11,11', 'RadiusX': '8', 'RadiusY': '8'}), (name, attrs))
        name, attrs = icons.geometry(ET.fromstring('<rect x="3" y="3" width="7" height="7" rx="1"/>'))
        self.assertEqual('RectangleGeometry', name)
        self.assertEqual('1', attrs['RadiusY'])
        self.assertEqual('3,3,7,7', attrs['Rect'])

    def test_unsupported_primitives_and_transforms_fail_instead_of_dropping_art(self):
        for source in ('<image href="external"/>', '<path d="M0,0" transform="scale(2)"/>'):
            with self.assertRaises(ValueError):
                icons.geometry(ET.fromstring(source))


if __name__ == '__main__':
    unittest.main()
