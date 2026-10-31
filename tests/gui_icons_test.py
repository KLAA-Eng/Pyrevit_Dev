"""Deterministic artwork generation; actual WPF rendering has a separate probe."""
import importlib.util
import json
import re
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
        self.assertEqual(icons.generate_icons(), icons.ICONS_XAML.read_text(encoding='utf-8'))
        dictionary = ET.fromstring(icons.generate_icons())
        groups = dictionary.findall(P + 'GeometryGroup')
        self.assertEqual({'klicon' + role for role in icons.ROLES}, {node.attrib.get(X + 'Key') for node in groups})
        self.assertEqual(len(icons.ROLES) + 1, len(dictionary), 'icon groups and the one klcLogo template')
        text = icons.generate_icons()
        self.assertNotIn('StaticResource', text, 'every resource is self-contained')
        self.assertEqual({'KlaBorderBrush', 'KlaTextBrush'}, set(re.findall(r'\{DynamicResource ([^}]+)\}', text)))
        self.assertEqual([], [node for node in dictionary.iter() if node.tag.endswith('Brush')], 'defines no brushes')
        self.assertFalse((ROOT / 'lib' / '_logos' / 'KLCodeWordmark.xaml').exists(), 'the logo lives in klIcons.xaml')
        self.assertFalse((icons.ASSETS / 'klIcons.xaml').exists(), 'klIcons.xaml lives in lib/GUI/Resources')

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
        self.assertNotIn('klIcons.xaml', merged, 'merged once, through the shared primitives')
        primitives = ET.fromstring((ROOT / 'lib' / 'GUI' / 'Resources' / 'KLCodeSharedPrimitives.xaml').read_text(encoding='utf-8'))
        self.assertIn('klIcons.xaml', [node.attrib.get('Source') for node in primitives.iter(P + 'ResourceDictionary')])
        tokens = (ROOT / 'lib' / 'GUI' / 'Resources' / 'KLCodeFoundationTokens.xaml').read_text(encoding='utf-8')
        self.assertNotIn('klIcons.xaml', tokens, 'icons are merged by the foundation, not by the tokens')
        self.assertFalse(hasattr(icons, 'generate_images'))

    def test_logo_is_one_self_contained_template_that_keeps_the_svg_geometry(self):
        self.assertEqual('klcLogo.svg', icons.LOGO_SVG.name)
        dictionary = ET.fromstring(icons.generate_icons())
        keys = [node.attrib.get(X + 'Key') for node in dictionary if not node.tag.endswith('GeometryGroup')]
        self.assertEqual(['klcLogo'], keys, 'the logo is one resource')
        svg_paths = [path.attrib['d'] for path in ET.parse(icons.LOGO_SVG).getroot().iter('{%s}path' % icons.SVG)]
        for transform in ('matrix(1,0.2,0,1,0,0)', 'scale(-1,1)', 'scale(0)'):
            with self.assertRaises(ValueError, msg=transform):
                icons._matrix(transform)
        template = dictionary.find(P + 'DataTemplate')
        self.assertEqual('klcLogo', template.attrib.get(X + 'Key'))
        box = template.find(P + 'Viewbox')
        self.assertNotIn('Width', box.attrib, 'unsized: the header slot sets 128 x 18')
        self.assertNotIn('Height', box.attrib)
        canvas = box.find(P + 'Canvas')
        self.assertEqual(('1024', '146'), (canvas.attrib['Width'], canvas.attrib['Height']), 'the SVG view box')
        paths = canvas.findall(P + 'Path')
        self.assertEqual(svg_paths, [path.attrib['Data'] for path in paths], 'outlines keep the SVG coordinates')
        self.assertEqual(['{DynamicResource KlaBorderBrush}', '{DynamicResource KlaTextBrush}'], [path.attrib['Fill'] for path in paths])
        # The SVG group's scale and offset, unrounded, on each outline.
        self.assertEqual({'1.0666642,0,0,1.0681867,-34.133255,-69.02212'}, {path.attrib['RenderTransform'] for path in paths})
        self.assertNotIn('#33714F', icons.generate_icons())
        primitives = (ROOT / 'lib' / 'GUI' / 'Resources' / 'KLCodeSharedPrimitives.xaml').read_text(encoding='utf-8')
        self.assertNotIn('<DataTemplate x:Key="klcLogo">', primitives, 'the template is generated into klIcons.xaml')

    def test_path_points_tracks_relative_commands(self):
        points = icons.path_points('M 10,10 h 5 v -2 l 1,1 c 1,1 2,2 3,3 Z')
        self.assertEqual((10.0, 10.0), points[0])
        self.assertEqual((19.0, 12.0), points[-1])

    def test_path_points_reads_exponents_and_compact_numbers(self):
        # Inkscape may write exponents; SVG's compact form lets "1.5.5" mean 1.5 and .5.
        points = icons.path_points('M 1e1,2E+1 l 1.5.5')
        self.assertEqual([(10.0, 20.0), (11.5, 20.5)], points)

    def test_path_points_rejects_numbers_without_a_command(self):
        for data in ('10,10 L 1,1', 'M 0,0 Z 5,5', 'M 0,0 L 1', 'M 0,0 H'):
            with self.assertRaises(ValueError, msg=data):
                icons.path_points(data)

    def test_regeneration_writes_lf_line_endings(self):
        import sys
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'klIcons.xaml'
            with patch.object(icons, 'ICONS_XAML', target), patch.object(sys, 'argv', ['generate_gui_icons.py']):
                icons.main()
            written = target.read_bytes()
        self.assertNotIn(b'\r\n', written)
        self.assertEqual(icons.generate_icons().encode('utf-8'), written)

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
