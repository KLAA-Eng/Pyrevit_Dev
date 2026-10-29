"""Template contracts of the shared foundation that the WPF probes cannot see on a non-Windows host.

Each check reads the XAML as XML; nothing is rendered. They guard the 2026-10-29 template
correctness pass: orientation-aware scrollbars, layout-based Close centering, an indeterminate
checkbox state, a non-reflowing link focus, body-first keyboard order and no stacked opacity.
"""
import os
import re
import unittest
from xml.etree import ElementTree


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES = os.path.join(PROJECT_ROOT, 'lib', 'GUI', 'Resources')
P = '{http://schemas.microsoft.com/winfx/2006/xaml/presentation}'
X = '{http://schemas.microsoft.com/winfx/2006/xaml}'


def _read(name):
    with open(os.path.join(RESOURCES, name), 'r', encoding='utf-8') as stream:
        return stream.read()


def _root(name):
    return ElementTree.fromstring(_read(name))


def _style(root, key):
    for style in root.iter(P + 'Style'):
        if style.attrib.get(X + 'Key') == key:
            return style
    raise AssertionError('missing style ' + key)


class FoundationTemplateContracts(unittest.TestCase):
    def test_scrollbar_style_has_a_horizontal_template_with_an_unreversed_track(self):
        root = _root('KLCodeSharedPrimitives.xaml')
        bar = next(s for s in root.iter(P + 'Style') if s.attrib.get('TargetType') == 'ScrollBar')
        tracks = {t.attrib.get('IsDirectionReversed') for t in bar.iter(P + 'Track')}
        self.assertEqual({'true', 'false'}, tracks)
        triggers = [t for t in bar.iter(P + 'Trigger') if t.attrib.get('Property') == 'Orientation']
        self.assertEqual(['Horizontal'], [t.attrib.get('Value') for t in triggers])
        self.assertNotIn('Grid.Row="1"', _read('KLCodeSharedPrimitives.xaml').split('<Style TargetType="ScrollBar">')[1])

    def test_close_button_centers_its_glyphs_in_layout_not_with_a_render_transform(self):
        foundation = _read('KLCodeFoundation.xaml')
        self.assertNotIn('TranslateTransform', foundation)
        close = _style(_root('KLCodeFoundation.xaml'), 'KlaFoundationCloseButton')
        text = next(close.iter(P + 'TextBlock'))
        self.assertEqual('{StaticResource KlaCloseGlyphLift}', text.attrib.get('Margin'))

    def test_checkbox_has_an_indeterminate_state(self):
        box = _style(_root('KLCodeFoundation.xaml'), 'KlaFoundationCheckBox')
        values = [t.attrib.get('Value') for t in box.iter(P + 'Trigger') if t.attrib.get('Property') == 'IsChecked']
        self.assertEqual(['True', '{x:Null}'], values)
        names = {p.attrib.get(X + 'Name') for p in box.iter(P + 'Path')}
        self.assertEqual({'CheckMark', 'IndeterminateMark'}, names)

    def test_link_focus_changes_colour_only(self):
        link = _style(_root('KLCodeFoundation.xaml'), 'KlaFoundationLink')
        for trigger in link.iter(P + 'Trigger'):
            for setter in trigger.iter(P + 'Setter'):
                self.assertNotEqual('FontWeight', setter.attrib.get('Property'), 'focus must not reflow the footer')

    def test_shell_declares_the_body_before_the_chrome_so_keyboard_order_starts_in_the_body(self):
        shell = _style(_root('KLCodeFoundation.xaml'), 'KlaWindowShell')
        order = [e.attrib.get(X + 'Name') for e in shell.iter() if e.attrib.get(X + 'Name') in ('PART_Body', 'PART_Header', 'PART_Footer')]
        self.assertEqual(['PART_Body', 'PART_Header', 'PART_Footer'], order)
        version = next(e for e in shell.iter() if e.attrib.get(X + 'Name') == 'PART_Version')
        self.assertEqual('Tool version', version.attrib.get('{http://schemas.microsoft.com/winfx/2006/xaml/presentation}AutomationProperties.Name')
                         or version.attrib.get('AutomationProperties.Name'))

    def test_disabled_states_use_the_disabled_brushes_without_stacking_opacity(self):
        for name in ('KLCodeFoundation.xaml', 'KLCodeComponents.xaml'):
            self.assertNotRegex(_read(name), r'Property="Opacity"\s+Value="0\.6"', name)


if __name__ == '__main__':
    unittest.main()
