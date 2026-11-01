"""Owner decisions on the Command Switch look (2026-10-31): no panel shadow, no toggle hover fill."""
import os
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = '{http://schemas.microsoft.com/winfx/2006/xaml/presentation}'
X = '{http://schemas.microsoft.com/winfx/2006/xaml}'


def parse(relative):
    return ET.parse(os.path.join(ROOT, relative)).getroot()


class CommandSwitchLookTests(unittest.TestCase):
    def test_panel_has_no_shadow_and_no_outline(self):
        window = parse('lib/GUI/dialogs/CommandSwitchDialog.xaml')
        self.assertEqual([], [node for node in window.iter() if node.tag.endswith('Effect')])
        panel = next(node for node in window.iter() if node.attrib.get(X + 'Name') == 'switch_panel')
        self.assertEqual('0', panel.attrib.get('BorderThickness'))

    def test_toggle_pill_has_no_hover_trigger_but_command_pill_keeps_one(self):
        styles = {}
        for name in ('KLCodeFoundation.xaml', 'KLCodeComponents.xaml'):
            styles.update((node.attrib.get(X + 'Key'), node)
                          for node in parse('lib/GUI/Resources/' + name).iter(P + 'Style'))

        def hover(style):
            # Follow BasedOn: the command pill takes its hover from the klcFdnButton template.
            found = []
            while style is not None:
                found += [node for node in style.iter(P + 'Trigger') if node.attrib.get('Property') == 'IsMouseOver']
                base = re.match(r'\{StaticResource (\S+)\}$', style.attrib.get('BasedOn', ''))
                style = styles[base.group(1)] if base else None
            return found
        self.assertEqual([], hover(styles['KlaCommandToggle']))
        self.assertEqual(1, len(hover(styles['KlaCommandButton'])))


if __name__ == '__main__':
    unittest.main()
