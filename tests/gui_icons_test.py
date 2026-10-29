"""Deterministic icon conversion; actual WPF rendering has a separate probe."""
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gui_icon_generator', ROOT / 'scripts' / 'generate_gui_icons.py')
icons = importlib.util.module_from_spec(spec)
spec.loader.exec_module(icons)


class GuiIconTests(unittest.TestCase):
    def test_generated_dictionary_matches_approved_sources(self):
        self.assertEqual(17, len(icons.ROLES))
        self.assertEqual(icons.generate(), (icons.ASSETS / 'KLCodeIcons.xaml').read_text(encoding='utf-8'))
        dictionary = ET.fromstring(icons.generate())
        keys = {node.attrib.get('{' + icons.XAML + '}Key') for node in dictionary}
        for role in icons.ROLES:
            self.assertIn('Kla' + role + 'Geometry', keys)
            self.assertIn('KlaIcon' + role, keys)
        for image in dictionary.findall('{' + icons.WPF + '}DrawingImage'):
            drawing = image.find('.//{' + icons.WPF + '}GeometryDrawing')
            self.assertEqual('Transparent', drawing.attrib['Brush'])
            self.assertEqual('0,0,24,24', drawing.find('.//{' + icons.WPF + '}RectangleGeometry').attrib['Rect'])

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
