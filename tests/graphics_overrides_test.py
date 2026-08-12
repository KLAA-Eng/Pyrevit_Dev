from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.graphics.overrides import create_red_projection_override


class FakeColor(object):
    def __init__(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue


class FakeSettings(object):
    def __init__(self):
        self.projection_line_color = None

    def SetProjectionLineColor(self, color):
        self.projection_line_color = color


class FakeDB(object):
    Color = FakeColor
    OverrideGraphicSettings = FakeSettings


class CreateRedProjectionOverrideTests(unittest.TestCase):
    def test_creates_fresh_settings_with_a_red_projection_line(self):
        first = create_red_projection_override(FakeDB)
        second = create_red_projection_override(FakeDB)

        self.assertIsNot(first, second)
        self.assertEqual((255, 0, 0), (
            first.projection_line_color.red,
            first.projection_line_color.green,
            first.projection_line_color.blue,
        ))
        self.assertEqual((255, 0, 0), (
            second.projection_line_color.red,
            second.projection_line_color.green,
            second.projection_line_color.blue,
        ))


if __name__ == '__main__':
    unittest.main()
