import unittest

from lib.carbon_gwp import revit_chart


class _Disposable(object):
    def Dispose(self):
        pass


class _Rectangle(object):
    def __init__(self, *values):
        self.values = values


class _RectangleF(_Rectangle):
    pass


class _Bitmap(_Disposable):
    def __init__(self, *values):
        self.values = values

    def SetResolution(self, *values):
        pass

    def Save(self, *values):
        pass


class _Graphics(_Disposable):
    def Clear(self, *values):
        pass

    def FillPie(self, brush, rectangle, start_angle, sweep_angle):
        if not isinstance(rectangle, _Rectangle) or isinstance(rectangle, _RectangleF):
            raise TypeError('expected Rectangle, got RectangleF')

    def FillEllipse(self, *values):
        pass

    def FillRectangle(self, *values):
        pass

    def DrawLine(self, *values):
        pass

    def DrawString(self, *values):
        pass


class _GraphicsFactory(object):
    @staticmethod
    def FromImage(bitmap):
        return _Graphics()


class _Color(object):
    White = 'white'

    @staticmethod
    def FromArgb(*values):
        return values


class _ColorTranslator(object):
    @staticmethod
    def FromHtml(value):
        return value


class _Font(_Disposable):
    def __init__(self, *values):
        pass


class _SolidBrush(_Disposable):
    def __init__(self, *values):
        pass


class _Pen(_Disposable):
    def __init__(self, *values):
        pass


class _StringFormat(_Disposable):
    pass


class _Point(object):
    def __init__(self, x, y, z=0.0):
        self.X = x
        self.Y = y
        self.Z = z


class _Box(object):
    def __init__(self, minimum, maximum):
        self.Min = minimum
        self.Max = maximum


class _PointDb(object):
    XYZ = staticmethod(_Point)


def _strict_drawing_api():
    return {
        'Bitmap': _Bitmap,
        'Color': _Color,
        'ColorTranslator': _ColorTranslator,
        'Font': _Font,
        'FontStyle': type('FontStyle', (), {'Bold': 'bold', 'Regular': 'regular'}),
        'Graphics': _GraphicsFactory,
        'GraphicsUnit': type('GraphicsUnit', (), {'Pixel': 'pixel'}),
        'Pen': _Pen,
        'Rectangle': _Rectangle,
        'RectangleF': _RectangleF,
        'SolidBrush': _SolidBrush,
        'StringAlignment': type('StringAlignment', (), {
            'Center': 'center', 'Near': 'near', 'Far': 'far'}),
        'StringFormat': _StringFormat,
        'ImageFormat': type('ImageFormat', (), {'Png': 'png'}),
        'SmoothingMode': type('SmoothingMode', (), {'AntiAlias': 'antialias'}),
        'TextRenderingHint': type('TextRenderingHint', (), {'AntiAliasGridFit': 'gridfit'}),
    }


class CarbonGwpRevitChartTests(unittest.TestCase):
    def test_renderer_passes_an_integer_rectangle_to_fill_pie(self):
        original_loader = revit_chart._load_drawing_api
        revit_chart._load_drawing_api = _strict_drawing_api
        try:
            revit_chart.render_chart_png([
                {
                    'display_label': 'Concrete Floor',
                    'value': 100.0,
                    'color': '#4E79A7',
                },
            ], 'ignored.png')
        finally:
            revit_chart._load_drawing_api = original_loader

    def test_chart_anchor_points_use_titleblock_and_gwp_image_corners(self):
        box = _Box(_Point(1.0, 2.0), _Point(4.0, 5.0))

        top_left = revit_chart._box_top_left(box, _PointDb)
        top_right = revit_chart._box_top_right(box, _PointDb)
        bottom_left = revit_chart._box_bottom_left(box, _PointDb)

        self.assertEqual((1.0, 5.0, 0.0), (top_left.X, top_left.Y, top_left.Z))
        self.assertEqual((4.0, 5.0, 0.0), (top_right.X, top_right.Y, top_right.Z))
        self.assertEqual((1.0, 2.0, 0.0), (bottom_left.X, bottom_left.Y, bottom_left.Z))


if __name__ == '__main__':
    unittest.main()
