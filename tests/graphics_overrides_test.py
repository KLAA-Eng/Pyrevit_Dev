from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.graphics.overrides import (
    create_red_projection_override,
    override_has_existing_graphics,
    override_has_red_line,
)


class FakeColor(object):
    def __init__(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue
        self.Red = red
        self.Green = green
        self.Blue = blue
        self.IsValid = True


class InvalidColor(object):
    IsValid = False


class FakeSettings(object):
    def __init__(self):
        self.projection_line_color = None

    def SetProjectionLineColor(self, color):
        self.projection_line_color = color


class FakeDB(object):
    Color = FakeColor
    OverrideGraphicSettings = FakeSettings

    class ElementId(object):
        InvalidElementId = -1

    class ViewDetailLevel(object):
        Undefined = 'Undefined'


class RaisingOverrideSettings(object):
    @property
    def ProjectionLineColor(self):
        raise SystemError('Object reference not set to an instance of an object.')

    @property
    def CutLineColor(self):
        return InvalidColor()


class LineColorOverrideSettings(object):
    ProjectionLinePatternId = -1
    CutLinePatternId = -1
    SurfaceForegroundPatternId = -1
    SurfaceBackgroundPatternId = -1
    CutForegroundPatternId = -1
    CutBackgroundPatternId = -1
    ProjectionLineWeight = -1
    CutLineWeight = -1
    DetailLevel = 'Undefined'
    Halftone = False
    Transparency = 0

    def __init__(self, projection_color=None, cut_color=None):
        self.ProjectionLineColor = projection_color or InvalidColor()
        self.CutLineColor = cut_color or InvalidColor()
        self.SurfaceForegroundPatternColor = InvalidColor()
        self.SurfaceBackgroundPatternColor = InvalidColor()
        self.CutForegroundPatternColor = InvalidColor()
        self.CutBackgroundPatternColor = InvalidColor()


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

    def test_unreadable_or_unset_override_color_is_not_red_or_existing(self):
        settings = RaisingOverrideSettings()

        self.assertFalse(override_has_red_line(settings))
        self.assertFalse(override_has_existing_graphics(settings, FakeDB))

    def test_detects_red_projection_or_cut_line_override(self):
        red_projection = LineColorOverrideSettings(projection_color=FakeColor(255, 0, 0))
        red_cut = LineColorOverrideSettings(cut_color=FakeColor(255, 0, 0))

        self.assertTrue(override_has_red_line(red_projection))
        self.assertTrue(override_has_red_line(red_cut))

    def test_detects_non_red_existing_override_for_preservation(self):
        settings = LineColorOverrideSettings(projection_color=FakeColor(0, 0, 255))

        self.assertFalse(override_has_red_line(settings))
        self.assertTrue(override_has_existing_graphics(settings, FakeDB))


if __name__ == '__main__':
    unittest.main()
