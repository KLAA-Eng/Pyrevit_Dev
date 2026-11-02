"""The shared dictionaries name tokens, never numbers; the scale lint sees the consumer drift."""
import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'scripts'))
import check_ui_scale as lint  # noqa: E402


class TokenScaleTests(unittest.TestCase):
    def test_foundation_and_components_carry_no_numeric_layout_literals(self):
        for path in lint.STRICT:
            self.assertEqual([], lint.strict_violations(lint.read(PROJECT_ROOT, path)), path)

    def test_lint_recognises_attribute_and_setter_literals(self):
        text = ('<Border Margin="0,0,0,7" Padding="8,4"/>\n'
                '<Setter Property="CornerRadius" Value="5"/>\n'
                '<Setter Property="Padding" Value="0"/>\n'
                '<Border Width="{StaticResource KlaCheckSize}"/>\n')
        self.assertEqual([(1, 'Margin', '0,0,0,7'), (1, 'Padding', '8,4'), (2, 'CornerRadius', '5')],
                         lint.strict_violations(text))
        self.assertEqual([(1, 'Margin', '0,0,0,7')], lint.off_scale(text))

    def test_lint_allows_size_literals_only_in_the_sized_icon_styles(self):
        text = ('<Style x:Key="klaIcon24" TargetType="ContentControl">\n'
                '    <Setter Property="Width" Value="24" />\n'
                '    <Setter Property="Margin" Value="4" />\n'
                '</Style>\n'
                '<Style x:Key="KlaIcon" TargetType="ContentControl">\n'
                '    <Setter Property="Width" Value="24" />\n'
                '</Style>\n')
        self.assertEqual([(3, 'Margin', '4'), (6, 'Width', '24')], lint.strict_violations(text))

    def test_every_token_the_dictionaries_name_exists(self):
        import re
        tokens = lint.read(PROJECT_ROOT, 'lib/GUI/Resources/KLCodeTokens.xaml')
        icons = lint.read(PROJECT_ROOT, 'lib/GUI/Resources/klIcons.xaml')
        defined = set(re.findall(r'x:Key="([^"]+)"', tokens + icons))
        for path in lint.STRICT:
            text = lint.read(PROJECT_ROOT, path)
            defined |= set(re.findall(r'x:Key="([^"]+)"', text))
            used = set(re.findall(r'\{StaticResource ([^}]+)\}', text))
            self.assertEqual(set(), used - defined, path)


if __name__ == '__main__':
    unittest.main()
