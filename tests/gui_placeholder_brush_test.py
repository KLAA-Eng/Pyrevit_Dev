"""Placeholder text shares one token whose value is the footer version gray (owner decision, 2026-10-31)."""
import os
import unittest
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = '{http://schemas.microsoft.com/winfx/2006/xaml/presentation}'
X = '{http://schemas.microsoft.com/winfx/2006/xaml}'


def parse(relative):
    return ET.parse(os.path.join(ROOT, relative)).getroot()


def named(root, name):
    return next(node for node in root.iter() if node.attrib.get(X + 'Name') == name)


class PlaceholderBrushTests(unittest.TestCase):
    def test_placeholder_brush_matches_the_footer_version_gray(self):
        brushes = dict((node.attrib.get(X + 'Key'), node.attrib.get('Color'))
                       for node in parse('lib/GUI/Resources/KLCode_palette.xaml').iter(P + 'SolidColorBrush'))
        self.assertEqual('#808080', brushes['KlaPlaceholderBrush'])
        self.assertEqual(brushes['KlaFooterVersionBrush'], brushes['KlaPlaceholderBrush'])

    def test_text_watermark_and_switch_hint_use_the_placeholder_token(self):
        expected = '{StaticResource KlaPlaceholderBrush}'
        text = named(parse('lib/GUI/dialogs/TextPromptDialog.xaml'), 'input_placeholder')
        hint = named(parse('lib/GUI/dialogs/CommandSwitchDialog.xaml'), 'search_hint')
        self.assertEqual(expected, text.attrib.get('Foreground'))
        self.assertEqual(expected, hint.attrib.get('Foreground'))


if __name__ == '__main__':
    unittest.main()
