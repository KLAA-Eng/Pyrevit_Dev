"""Shared input-mode focus contracts without loading WPF or Revit."""
import os
import unittest
from xml.etree import ElementTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NS = '{http://schemas.microsoft.com/winfx/2006/xaml/presentation}'
KEY = '{http://schemas.microsoft.com/winfx/2006/xaml}Key'


class FocusVisualTests(unittest.TestCase):
    def setUp(self):
        self.styles = {}
        self.button_styles = []
        for name in ('KLCodeFoundation.xaml', 'KLCodeComponents.xaml', 'KLCodeCommandSwitch.xaml'):
            root = ElementTree.parse(os.path.join(ROOT, 'lib', 'GUI', 'Resources', name))
            for style in root.findall(NS + 'Style'):
                identity = style.get(KEY)
                if identity:
                    self.styles[identity] = style
                if style.get('TargetType') in ('Button', 'CheckBox', 'RadioButton', 'ToggleButton'):
                    self.button_styles.append((identity or style.get('TargetType'), style))

    def value(self, style, prop):
        for setter in style.findall(NS + 'Setter'):
            if setter.get('Property') == prop:
                return setter.get('Value')
        parent = style.get('BasedOn')
        return self.value(self.styles[parent[len('{StaticResource '):-1]], prop) if parent else None

    def test_every_button_family_keeps_keyboard_focus_without_pointer_focus_marks(self):
        self.assertGreater(len(self.button_styles), 15)
        for name, style in self.button_styles:
            self.assertEqual('{StaticResource KlaKeyboardFocusVisual}', self.value(style, 'FocusVisualStyle'), name)
            self.assertNotEqual('False', self.value(style, 'Focusable'), name)
            self.assertFalse(any(trigger.get('Property') in ('IsKeyboardFocused', 'IsKeyboardFocusWithin')
                                 for trigger in style.iter(NS + 'Trigger')), name)

    def test_focus_decoration_cannot_capture_input_or_reflow_control_content(self):
        visual = self.styles['KlaKeyboardFocusVisual']
        self.assertEqual('False', self.value(visual, 'IsHitTestVisible'))
        self.assertEqual('False', self.value(visual, 'Focusable'))
        self.assertIsNotNone(visual.find('.//' + NS + 'ControlTemplate'))
        for name, style in self.button_styles:
            names = [element.get('{http://schemas.microsoft.com/winfx/2006/xaml}Name') for element in style.iter()]
            self.assertNotIn('FocusMark', names, name)
            self.assertNotIn('ToggleFocus', names, name)

    def test_text_and_group_input_focus_remains_visible(self):
        for name in ('KlaFoundationInput', 'KlaComboBox'):
            triggers = list(self.styles[name].iter(NS + 'Trigger'))
            self.assertTrue(any(trigger.get('Property') == 'IsKeyboardFocusWithin' for trigger in triggers), name)


if __name__ == '__main__':
    unittest.main()
