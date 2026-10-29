"""Generate framework-native GUI icon resources from the attributed SVG sources.

This development script runs under CPython; generated WPF resources require no
SVG renderer or Python dependency in command paths. Source geometry stays local.
"""
from pathlib import Path
import argparse
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'lib' / '_icons' / 'gui'
WPF = 'http://schemas.microsoft.com/winfx/2006/xaml/presentation'
XAML = 'http://schemas.microsoft.com/winfx/2006/xaml'

ROLES = {
    'Search': 'search', 'TextFilter': 'list-filter', 'Regex': 'regex',
    'ClearSearch': 'x', 'ReadElement': 'tags', 'ReadViewFilters': 'eye',
    'FilterElement': 'funnel', 'PickElement': 'mouse-pointer-2',
    'RectangleSelection': 'scan', 'CurrentSelection': 'check-check',
    'ListView': 'list', 'GridView': 'layout-grid', 'Favorite': 'star',
    'Information': 'info', 'Warning': 'triangle-alert', 'Error': 'circle-x',
    'Success': 'circle-check',
}


def element(parent, name, attributes=None):
    return ET.SubElement(parent, '{' + WPF + '}' + name, attributes or {})


def geometry(svg):
    """Translate the supported local Lucide primitives without changing bounds."""
    name = svg.tag.rsplit('}', 1)[-1]
    attrs = svg.attrib
    if 'transform' in attrs:
        raise ValueError('Transforms require an explicit converter implementation.')
    if name == 'path':
        return 'PathGeometry', {'Figures': attrs['d']}
    if name == 'circle':
        return 'EllipseGeometry', {'Center': attrs['cx'] + ',' + attrs['cy'],
                                   'RadiusX': attrs['r'], 'RadiusY': attrs['r']}
    if name == 'rect':
        return 'RectangleGeometry', {'Rect': ','.join(attrs[key] for key in ('x', 'y', 'width', 'height')),
                                     'RadiusX': attrs.get('rx', '0'), 'RadiusY': attrs.get('ry', attrs.get('rx', '0'))}
    if name == 'line':
        return 'LineGeometry', {'StartPoint': attrs['x1'] + ',' + attrs['y1'],
                               'EndPoint': attrs['x2'] + ',' + attrs['y2']}
    if name == 'polyline':
        return 'PathGeometry', {'Figures': 'M' + attrs['points']}
    raise ValueError('Unsupported SVG primitive: ' + name)


def generate():
    manifest = json.loads((ASSETS / 'source.json').read_text(encoding='utf-8'))
    ET.register_namespace('', WPF)
    ET.register_namespace('x', XAML)
    root = ET.Element('{' + WPF + '}ResourceDictionary')
    element(root, 'SolidColorBrush', {'{' + XAML + '}Key': 'KlaGuiIconBrush', 'Color': manifest['foreground']})
    element(root, 'SolidColorBrush', {'{' + XAML + '}Key': 'KlaGuiIconDisabledBrush', 'Color': manifest['disabled_foreground']})
    element(root, 'Pen', {'{' + XAML + '}Key': 'KlaGuiIconPen',
                              'Brush': '{StaticResource KlaGuiIconBrush}', 'Thickness': str(manifest['stroke_width']),
                              'StartLineCap': 'Round', 'EndLineCap': 'Round', 'LineJoin': 'Round'})
    for role, source in sorted(ROLES.items()):
        svg = ET.parse(ASSETS / 'svg' / (source + '.svg')).getroot()
        if svg.attrib.get('viewBox') != '0 0 24 24':
            raise ValueError('Unexpected icon view box: ' + source)
        group = element(root, 'GeometryGroup', {'{' + XAML + '}Key': 'Kla' + role + 'Geometry'})
        parts = []
        for child in svg:
            name, attrs = geometry(child)
            element(group, name, attrs)
            parts.append((name, attrs, child.attrib.get('fill') == 'currentColor'))
        image = element(root, 'DrawingImage', {'{' + XAML + '}Key': 'KlaIcon' + role})
        drawing = element(element(image, 'DrawingImage.Drawing'), 'DrawingGroup')
        bounds = element(drawing, 'GeometryDrawing', {'Brush': 'Transparent'})
        element(element(bounds, 'GeometryDrawing.Geometry'), 'RectangleGeometry', {'Rect': '0,0,24,24'})
        for name, attrs, filled in parts:
            part = element(drawing, 'GeometryDrawing', {'Pen': '{StaticResource KlaGuiIconPen}'})
            if filled:
                part.set('Brush', '{StaticResource KlaGuiIconBrush}')
            element(element(part, 'GeometryDrawing.Geometry'), name, attrs)
    style = element(root, 'Style', {'{' + XAML + '}Key': 'KlaGuiIcon', 'TargetType': 'ContentControl'})
    for key, value in [('Width', '16'), ('Height', '16'), ('Focusable', 'False'), ('IsHitTestVisible', 'False')]:
        element(style, 'Setter', {'Property': key, 'Value': value})
    setter = element(style, 'Setter', {'Property': 'Template'})
    template = element(element(setter, 'Setter.Value'), 'ControlTemplate', {'TargetType': 'ContentControl'})
    canvas = element(element(template, 'Viewbox', {'Stretch': 'Uniform'}), 'Canvas', {'Width': '24', 'Height': '24'})
    element(canvas, 'Path', {'Data': '{TemplateBinding Content}', 'Stroke': '{TemplateBinding Foreground}',
                             'StrokeThickness': str(manifest['stroke_width']), 'StrokeStartLineCap': 'Round',
                             'StrokeEndLineCap': 'Round', 'StrokeLineJoin': 'Round'})
    triggers = element(style, 'Style.Triggers')
    disabled = element(triggers, 'Trigger', {'Property': 'IsEnabled', 'Value': 'False'})
    element(disabled, 'Setter', {'Property': 'Foreground', 'Value': '{StaticResource KlaGuiIconDisabledBrush}'})
    ET.indent(root, space='    ')
    return '<!-- Generated by scripts/generate_gui_icons.py; edit SVG sources/manifest, not this file. -->\n' + ET.tostring(root, encoding='unicode') + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if resources need regeneration.')
    args = parser.parse_args()
    target = ASSETS / 'KLCodeIcons.xaml'
    output = generate()
    if args.check:
        if not target.exists() or target.read_text(encoding='utf-8') != output:
            raise SystemExit('GUI icon resources are stale; run scripts/generate_gui_icons.py.')
    else:
        target.write_text(output, encoding='utf-8')
    print('{} approved GUI icon roles verified.'.format(len(ROLES)))


if __name__ == '__main__':
    main()
