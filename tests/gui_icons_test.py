"""Deterministic artwork generation; actual WPF rendering has a separate probe."""
import importlib.util
import json
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
    def test_message_roles_preserve_other_severity_consumers_and_use_pinned_sources(self):
        self.assertNotIn('Error', icons.ROLES, 'circle-x was merged into the error alert role')
        self.assertEqual('octagon-alert', icons.ROLES['ErrorAlert'])
        self.assertEqual('check-check', icons.ROLES['SuccessAlert'])
        self.assertEqual('chevron-right', icons.ROLES['ChevRight'])
        self.assertEqual('chevron-down', icons.ROLES['ChevDown'])
        self.assertNotIn('FutureCurrentSelection', icons.ROLES, 'merged into SuccessAlert')
        source = json.loads((icons.ASSETS / 'source.json').read_text(encoding='utf-8'))
        self.assertEqual('be09619c1c1124ad09c19fc3e87ee3b939409bbd', source['commit'])
        self.assertTrue(set(icons.ROLES.values()).issubset(source['icons']))

    def test_generated_geometry_dictionary_is_a_leaf_that_matches_the_sources(self):
        self.assertEqual(19, len(icons.ROLES))
        self.assertEqual(icons.generate_icons(), (icons.ASSETS / 'KLCodeIcons.xaml').read_text(encoding='utf-8'))
        dictionary = ET.fromstring(icons.generate_icons())
        self.assertEqual({P + 'GeometryGroup'}, {node.tag for node in dictionary})
        self.assertEqual({'klgeo' + role for role in icons.ROLES}, {node.attrib.get(X + 'Key') for node in dictionary})
        self.assertNotIn('StaticResource', icons.generate_icons())

    def test_geometry_is_the_only_icon_form(self):
        foundation_path = ROOT / 'lib' / 'GUI' / 'Resources' / 'KLCodeFoundation.xaml'
        foundation = foundation_path.read_text(encoding='utf-8')
        # Parsed, not matched as text: the foundation may be reformatted.
        shell = ET.fromstring(foundation)
        self.assertEqual([], list(shell.iter(P + 'DrawingImage')), 'no generated ImageSources')
        self.assertEqual([], [node for node in shell.iter(P + 'Pen') if node.attrib.get(X + 'Key') == 'KlaGuiIconPen'])
        self.assertNotIn('generated-icons', foundation)
        self.assertIn('KlaGuiIcon', {node.attrib.get(X + 'Key') for node in shell.iter(P + 'Style')})
        merged = [node.attrib.get('Source') for node in shell.iter(P + 'ResourceDictionary')]
        self.assertIn('../../_icons/gui/KLCodeIcons.xaml', merged)
        tokens = (ROOT / 'lib' / 'GUI' / 'Resources' / 'KLCodeFoundationTokens.xaml').read_text(encoding='utf-8')
        self.assertNotIn('KLCodeIcons.xaml', tokens, 'icons are merged by the foundation, not by the tokens')
        self.assertFalse(hasattr(icons, 'generate_images'))

    def test_wordmark_keeps_svg_geometry_separate_from_the_drawing_offset(self):
        self.assertEqual(icons.generate_wordmark(), icons.WORDMARK_XAML.read_text(encoding='utf-8'))
        dictionary = ET.fromstring(icons.generate_wordmark())
        keys = [node.attrib.get(X + 'Key') for node in dictionary]
        self.assertEqual(['KlaWordmarkSlashGeometry', 'KlaWordmarkLettersGeometry', 'KlaWordmarkOrigin', 'KlaWordmarkCanvasWidth', 'KlaWordmarkCanvasHeight'], keys)
        for geo in dictionary.findall(P + 'PathGeometry'):
            self.assertIsNone(geo.find(P + 'PathGeometry.Transform'))
        shift = dictionary.find(P + 'TranslateTransform')
        self.assertEqual(('-32', '-64'), (shift.attrib['X'], shift.attrib['Y']))
        primitives = (ROOT / 'lib' / 'GUI' / 'Resources' / 'KLCodeSharedPrimitives.xaml').read_text(encoding='utf-8')
        self.assertIn('Data="{StaticResource KlaWordmarkSlashGeometry}"', primitives)
        self.assertIn('Fill="{StaticResource KlaBorderBrush}"', primitives)
        self.assertEqual(2, primitives.count('RenderTransform="{StaticResource KlaWordmarkOrigin}"'))
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
