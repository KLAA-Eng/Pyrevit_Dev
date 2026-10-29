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

    def test_every_token_the_dictionaries_name_exists(self):
        import re
        tokens = lint.read(PROJECT_ROOT, 'lib/GUI/Resources/KLCodeFoundationTokens.xaml')
        palette = lint.read(PROJECT_ROOT, 'lib/GUI/Resources/KLCode_palette.xaml')
        primitives = lint.read(PROJECT_ROOT, 'lib/GUI/Resources/KLCodeSharedPrimitives.xaml')
        icons = lint.read(PROJECT_ROOT, 'lib/_icons/gui/KLCodeIcons.xaml')
        defined = set(re.findall(r'x:Key="([^"]+)"', tokens + palette + primitives + icons))
        for path in lint.STRICT:
            text = lint.read(PROJECT_ROOT, path)
            defined |= set(re.findall(r'x:Key="([^"]+)"', text))
            used = set(re.findall(r'\{StaticResource ([^}]+)\}', text))
            self.assertEqual(set(), used - defined, path)


if __name__ == '__main__':
    unittest.main()
