"""Placeholder text is the input template's watermark, drawn from Tag in one token whose value is the footer version gray
(owner decision, 2026-10-31; moved into the template 2026-11-01)."""
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
                       for node in parse('lib/GUI/Resources/KLCodeTokens.xaml').iter(P + 'SolidColorBrush'))
        self.assertEqual('#808080', brushes['klcTextWatermarkColor'])
        self.assertEqual(brushes['klcFooterVersionColor'], brushes['klcTextWatermarkColor'])

    def test_the_input_template_draws_the_watermark_from_tag_while_empty(self):
        root = parse('lib/GUI/Resources/KLCodeFoundation.xaml')
        style = next(s for s in root.iter(P + 'Style') if s.attrib.get(X + 'Key') == 'KlaFoundationInput')
        mark = named(style, 'Watermark')
        self.assertEqual('{StaticResource klcTextWatermarkColor}', mark.attrib.get('Foreground'))
        self.assertEqual('{Binding Tag, RelativeSource={RelativeSource TemplatedParent}}', mark.attrib.get('Text'))
        self.assertEqual('Collapsed', mark.attrib.get('Visibility'))
        shown = [t for t in style.iter(P + 'Trigger') if t.attrib.get('Property') == 'Text' and t.attrib.get('Value') == '']
        self.assertEqual([('Watermark', 'Visibility', 'Visible')],
                         [(s.attrib.get('TargetName'), s.attrib.get('Property'), s.attrib.get('Value'))
                          for t in shown for s in t.iter(P + 'Setter')])

    def test_the_dialogs_supply_their_placeholders_and_draw_no_overlay(self):
        # Selection's filter takes KlaFilter's default watermark instead of its own Tag.
        components = parse('lib/GUI/Resources/KLCodeComponents.xaml')
        filter_style = next(s for s in components.iter(P + 'Style') if s.attrib.get(X + 'Key') == 'KlaFilter')
        self.assertIn(('Tag', 'Type to filter'),
                      [(s.attrib.get('Property'), s.attrib.get('Value')) for s in filter_style.findall(P + 'Setter')])
        expected = {'TextPromptDialog.xaml': ('input_text', '[ENTER TEXT]'),
                    'CommandSwitchDialog.xaml': ('search_text', 'Type to filter'),
                    'SelectionDialog.xaml': ('filter_text', None)}
        for name, (box, text) in expected.items():
            root = parse('lib/GUI/dialogs/' + name)
            self.assertEqual(text, named(root, box).attrib.get('Tag'), name)
            overlays = [node for node in root.iter(P + 'TextBlock')
                        if node.attrib.get('Foreground') == '{StaticResource klcTextWatermarkColor}']
            self.assertEqual([], overlays, name)

if __name__ == '__main__':
    unittest.main()
