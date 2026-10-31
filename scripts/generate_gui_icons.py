"""Generate framework-native GUI artwork from the attributed sources.

Two outputs, both deterministic (``--check`` fails when either is stale):

* ``lib/_icons/gui/klIcons.xaml`` — geometry only (one ``klicon<Role>`` GeometryGroup per role). A leaf
  dictionary with no brushes; windows draw it through the foundation's ``KlaGuiIcon`` presenter, the only icon form.
* ``lib/_logos/KLCodeWordmark.xaml`` — the KLCode wordmark's slash and letter geometry from
  ``lib/_logos/KLCode_text_1024x256px.svg``, with its drawing offset, for the shared primitives' DataTemplate.

This development script runs under CPython; generated WPF resources require no SVG renderer or Python
dependency in command paths. Source geometry stays local.
"""
from pathlib import Path
import argparse
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'lib' / '_icons' / 'gui'
WORDMARK_SVG = ROOT / 'lib' / '_logos' / 'KLCode_text_1024x256px.svg'
WORDMARK_XAML = ROOT / 'lib' / '_logos' / 'KLCodeWordmark.xaml'
WPF = 'http://schemas.microsoft.com/winfx/2006/xaml/presentation'
XAML = 'http://schemas.microsoft.com/winfx/2006/xaml'
SVG = 'http://www.w3.org/2000/svg'
# The wordmark's bounding box in the SVG's 1024x256 view box (x, y, width, height).
# Apply its origin offset to the Path's RenderTransform, preserving the old WPF rasterization.
WORDMARK_BOUNDS = (32, 64, 961, 138)

ROLES = {
    # Shared dialogs: Selection (Search, Group), Message and Action Choice severity icons,
    # and the shared Details toggle. InfoAlert and WarnAlert also serve CustomAlert and the compiled alert.
    'Search': 'search', 'Group': 'layers-2',
    'InfoAlert': 'info', 'WarnAlert': 'triangle-alert',
    # ErrorAlert also serves the compiled alert and Startup Importer blocking issues (circle-x retired 2026-10-31);
    # SuccessAlert also draws the recall window's current-selection action (FutureCurrentSelection merged 2026-10-31).
    'ErrorAlert': 'octagon-alert', 'SuccessAlert': 'check-check',
    'ChevRight': 'chevron-right', 'ChevDown': 'chevron-down',
    # Other live windows: compiled Family Studio (List, Grid, Fav).
    'List': 'list', 'Grid': 'layout-grid', 'Fav': 'star',
    # Future: used only by the Match recall window in lib/GUI/_future/match, which no tool opens.
    'FutureFilterList': 'list-filter', 'FutureRegex': 'regex', 'FutureClearSearch': 'x',
    'FutureTags': 'tags', 'FutureRead': 'eye', 'FutureFilterFunnel': 'funnel',
    'FuturePointer': 'mouse-pointer-2', 'FutureRectSelect': 'scan',
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


def _register():
    ET.register_namespace('', WPF)
    ET.register_namespace('x', XAML)


def _serialise(root, comment):
    ET.indent(root, space='    ')
    return comment + '\n' + ET.tostring(root, encoding='unicode') + '\n'


def role_parts():
    """[(role, [(geometry name, attrs, filled)])] in role order, read from the approved SVG sources."""
    result = []
    for role, source in sorted(ROLES.items()):
        svg = ET.parse(ASSETS / 'svg' / (source + '.svg')).getroot()
        if svg.attrib.get('viewBox') != '0 0 24 24':
            raise ValueError('Unexpected icon view box: ' + source)
        parts = []
        for child in svg:
            name, attrs = geometry(child)
            parts.append((name, attrs, child.attrib.get('fill') == 'currentColor'))
        result.append((role, parts))
    return result


def generate_icons():
    """lib/_icons/gui/klIcons.xaml: one GeometryGroup per role and nothing else."""
    _register()
    root = ET.Element('{' + WPF + '}ResourceDictionary')
    for role, parts in role_parts():
        group = element(root, 'GeometryGroup', {'{' + XAML + '}Key': 'klicon' + role})
        for name, attrs, filled in parts:
            element(group, name, attrs)
    return _serialise(root, '<!-- Generated by scripts/generate_gui_icons.py; geometry only. Edit the SVG sources and manifest, not this file. -->')


_NUM = re.compile(r'-?\d*\.?\d+(?:e-?\d+)?')


def path_points(d):
    """Every absolute point a path touches (end points and curve controls) — enough to sanity-check its bounds."""
    tokens = re.findall(r'[MLHVCSQTAZmlhvcsqtaz]|' + _NUM.pattern, d)
    points, x, y, start, i, cmd = [], 0.0, 0.0, (0.0, 0.0), 0, None
    counts = {'M': 2, 'L': 2, 'H': 1, 'V': 1, 'C': 6, 'S': 4, 'Q': 4, 'T': 2, 'A': 7, 'Z': 0}
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]; i += 1
            if cmd.upper() == 'Z':
                x, y = start; continue
        rel, c = cmd.islower(), cmd.upper()
        args = [float(t) for t in tokens[i:i + counts[c]]]; i += counts[c]
        if c == 'H':
            x = x + args[0] if rel else args[0]
        elif c == 'V':
            y = y + args[0] if rel else args[0]
        elif c == 'A':
            x, y = (x + args[5], y + args[6]) if rel else (args[5], args[6])
        else:
            pairs = [(args[k], args[k + 1]) for k in range(0, len(args), 2)]
            for px, py in pairs:
                ax, ay = (x + px, y + py) if rel else (px, py)
                points.append((ax, ay))
            x, y = points[-1]
            if c == 'M':
                start = (x, y); cmd = 'l' if rel else 'L'
            continue
        points.append((x, y))
    return points


def generate_wordmark():
    """Generate the SVG geometry and the Path drawing offset separately."""
    _register()
    svg = ET.parse(WORDMARK_SVG).getroot()
    paths = list(svg.iter('{' + SVG + '}path'))
    if len(paths) != 2:
        raise ValueError('The wordmark SVG must hold exactly two paths (slash, letters); found %d' % len(paths))
    for group in svg.iter('{' + SVG + '}g'):
        m = re.match(r'matrix\(([-\d.e]+),0,0,([-\d.e]+),([-\d.e]+),([-\d.e]+)\)', group.attrib.get('transform', 'matrix(1,0,0,1,0,0)'))
        if not m or abs(float(m.group(1)) - 1) > 1e-4 or abs(float(m.group(2)) - 1) > 1e-4:
            raise ValueError('The wordmark group transform must be (near-)identity scale.')
    x0, y0, w, h = WORDMARK_BOUNDS
    for path in paths:
        pts = path_points(path.attrib['d'])
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if min(xs) < x0 - 1 or max(xs) > x0 + w + 1 or min(ys) < y0 - 1 or max(ys) > y0 + h + 1:
            raise ValueError('Wordmark geometry leaves WORDMARK_BOUNDS: x %s..%s y %s..%s' % (min(xs), max(xs), min(ys), max(ys)))
    root = ET.Element('{' + WPF + '}ResourceDictionary')
    for key, path in (('KlaWordmarkSlashGeometry', paths[0]), ('KlaWordmarkLettersGeometry', paths[1])):
        element(root, 'PathGeometry', {'{' + XAML + '}Key': key, 'Figures': path.attrib['d']})
    element(root, 'TranslateTransform', {'{' + XAML + '}Key': 'KlaWordmarkOrigin', 'X': str(-x0), 'Y': str(-y0)})
    sysns = 'clr-namespace:System;assembly=mscorlib'
    for key, value in (('KlaWordmarkCanvasWidth', w), ('KlaWordmarkCanvasHeight', h)):
        node = ET.SubElement(root, '{' + sysns + '}Double', {'{' + XAML + '}Key': key})
        node.text = str(value)
    ET.register_namespace('sys', sysns)
    return _serialise(root, '<!-- Generated by scripts/generate_gui_icons.py from KLCode_text_1024x256px.svg; geometry and drawing offset. Edit the SVG, not this file. -->')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if resources need regeneration.')
    args = parser.parse_args()
    outputs = [(ASSETS / 'klIcons.xaml', generate_icons()), (WORDMARK_XAML, generate_wordmark())]
    stale = [str(path.relative_to(ROOT)) for path, text in outputs if not path.exists() or path.read_text(encoding='utf-8') != text]
    if args.check:
        if stale:
            raise SystemExit('GUI artwork resources are stale (%s); run scripts/generate_gui_icons.py.' % ', '.join(stale))
    else:
        for path, text in outputs:
            path.write_text(text, encoding='utf-8')
    print('{} approved GUI icon roles and the wordmark verified.'.format(len(ROLES)))


if __name__ == '__main__':
    main()
