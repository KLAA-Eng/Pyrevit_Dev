"""Template contracts of the shared foundation that the WPF probes cannot see on a non-Windows host.

Each check reads the XAML as XML; nothing is rendered. They guard the 2026-10-29 template
correctness pass (orientation-aware scrollbars, layout-based Close centering, an indeterminate
checkbox state, a non-reflowing link focus, body-first keyboard order and no stacked opacity) as
the 2026-10-31 shell rework left it: klcCloseButton centres its caption with alignment alone and
the shell names its parts klcShell_*, klcHeader_* and klcFooter_*.
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
        root = _root('KLCodeFoundation.xaml')
        bar = next(s for s in root.iter(P + 'Style') if s.attrib.get('TargetType') == 'ScrollBar')
        tracks = {t.attrib.get('IsDirectionReversed') for t in bar.iter(P + 'Track')}
        self.assertEqual({'true', 'false'}, tracks)
        triggers = [t for t in bar.iter(P + 'Trigger') if t.attrib.get('Property') == 'Orientation']
        self.assertEqual(['Horizontal'], [t.attrib.get('Value') for t in triggers])
        # Inspect the scrollbar style alone: the shell template later in the file uses Grid.Row legitimately.
        self.assertEqual([], [node for node in bar.iter() if 'Grid.Row' in node.attrib])

    def test_close_button_centers_its_caption_with_alignment_not_a_margin_or_render_transform(self):
        foundation = _read('KLCodeFoundation.xaml')
        self.assertNotIn('TranslateTransform', foundation)
        # The glyph-lift margin went with the 60 x 18 button on 2026-10-31; the 48 x 16 klcCloseButton
        # centres its caption in layout, so the token is the unused xxxCloseGlyphLift and nothing names it.
        self.assertNotIn('CloseGlyphLift', foundation)
        close = _style(_root('KLCodeFoundation.xaml'), 'klcCloseButton')
        text = next(close.iter(P + 'TextBlock'))
        self.assertNotIn('Margin', text.attrib)
        self.assertEqual(('Center', 'Center', 'Center'), (text.attrib.get('HorizontalAlignment'),
                         text.attrib.get('VerticalAlignment'), text.attrib.get('TextAlignment')))
        sizes = {setter.attrib.get('Property'): setter.attrib.get('Value') for setter in close.findall(P + 'Setter')}
        self.assertEqual({'Width': '{StaticResource klcCloseWidth}', 'Height': '{StaticResource klcCloseHeight}',
                          'FontSize': '{StaticResource klcCloseFontSize}'},
                         {key: sizes.get(key) for key in ('Width', 'Height', 'FontSize')})

    def test_checkbox_has_an_indeterminate_state(self):
        box = _style(_root('KLCodeFoundation.xaml'), 'KlaFoundationCheckBox')
        values = [t.attrib.get('Value') for t in box.iter(P + 'Trigger') if t.attrib.get('Property') == 'IsChecked']
        self.assertEqual(['True', '{x:Null}'], values)
        names = {p.attrib.get(X + 'Name') for p in box.iter(P + 'Path')}
        self.assertEqual({'CheckMark', 'IndeterminateMark'}, names)

    def test_link_focus_changes_colour_only(self):
        link = _style(_root('KLCodeFoundation.xaml'), 'klcFdnLink')
        for trigger in link.iter(P + 'Trigger'):
            for setter in trigger.iter(P + 'Setter'):
                self.assertNotEqual('FontWeight', setter.attrib.get('Property'), 'focus must not reflow the footer')

    def test_shell_declares_the_body_before_the_chrome_so_keyboard_order_starts_in_the_body(self):
        shell = _style(_root('KLCodeFoundation.xaml'), 'klcWindowShell')
        bands = ('klcShell_Body', 'klcShell_Header', 'klcShell_Footer')
        order = [e.attrib.get(X + 'Name') for e in shell.iter() if e.attrib.get(X + 'Name') in bands]
        self.assertEqual(list(bands), order)
        version = next(e for e in shell.iter() if e.attrib.get(X + 'Name') == 'klcFooter_version')
        self.assertEqual('Tool version', version.attrib.get(P + 'AutomationProperties.Name')
                         or version.attrib.get('AutomationProperties.Name'))

    def test_shell_names_every_part_the_python_and_csharp_chrome_binders_look_up(self):
        # GUI/window_chrome.py and src/KLCode.Wpf/WindowChrome.cs bind these by name through the template.
        shell = _style(_root('KLCodeFoundation.xaml'), 'klcWindowShell')
        names = {e.attrib.get(X + 'Name') for e in shell.iter() if X + 'Name' in e.attrib}
        self.assertEqual({'klcShell_Body', 'klcShell_Header', 'klcShell_Footer',
                          'klcHeader_logo', 'klcHeader_title', 'klcHeader_close',
                          'klcFooter_version', 'klcFooter_prototype', 'klcFooter_outreach'}, names)
        close = next(e for e in shell.iter(P + 'Button') if e.attrib.get(X + 'Name') == 'klcHeader_close')
        self.assertEqual('{StaticResource klcCloseButton}', close.attrib.get('Style'))
        self.assertEqual('{DynamicResource CloseLabel}', close.attrib.get('Content'))

    def test_disabled_states_use_the_disabled_brushes_without_stacking_opacity(self):
        for name in ('KLCodeFoundation.xaml', 'KLCodeComponents.xaml'):
            self.assertNotRegex(_read(name), r'Property="Opacity"\s+Value="0\.6"', name)


if __name__ == '__main__':
    unittest.main()
