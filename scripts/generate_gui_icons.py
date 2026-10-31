"""Generate framework-native GUI artwork from the attributed sources.

One output, deterministic (``--check`` fails when it is stale): ``lib/GUI/Resources/klIcons.xaml``, a
geometry-only leaf dictionary with no brushes, holding

* one ``klicon<Role>`` GeometryGroup per role, drawn by the foundation's ``KlaGuiIcon`` presenter, and
* the KLCode logo (``klcLogo*``): the slash and letter geometry from ``lib/_logos/klcLogo.svg``, the SVG
  group's scale and offset as one transform, and the view-box canvas, drawn by the shared primitives'
  ``klcLogo`` DataTemplate.

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
LOGO_SVG = ROOT / 'lib' / '_logos' / 'klcLogo.svg'
ICONS_XAML = ROOT / 'lib' / 'GUI' / 'Resources' / 'klIcons.xaml'
WPF = 'http://schemas.microsoft.com/winfx/2006/xaml/presentation'
XAML = 'http://schemas.microsoft.com/winfx/2006/xaml'
SYS = 'clr-namespace:System;assembly=mscorlib'
SVG = 'http://www.w3.org/2000/svg'
# The logo's outlines may sit inside one scale-and-offset group; anything else (rotation, skew) is refused.
LOGO_TOLERANCE = 2.0

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
    ET.register_namespace('sys', SYS)


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
    """lib/GUI/Resources/klIcons.xaml: one GeometryGroup per role, then the KLCode logo resources."""
    _register()
    root = ET.Element('{' + WPF + '}ResourceDictionary')
    for role, parts in role_parts():
        group = element(root, 'GeometryGroup', {'{' + XAML + '}Key': 'klicon' + role})
        for name, attrs, filled in parts:
            element(group, name, attrs)
    _append_logo(root)
    return _serialise(root, '<!-- Generated by scripts/generate_gui_icons.py: GUI icon geometry (klicon<Role>) and the KLCode logo (klcLogo*) from klcLogo.svg. Edit the SVG sources and manifest, not this file. -->')


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


def _matrix(transform):
    """(a, d, e, f) of an axis-aligned SVG transform: matrix(a,0,0,d,e,f), translate(e[,f]) or scale(a[,d])."""
    if not transform:
        return (1.0, 1.0, 0.0, 0.0)
    m = re.match(r'^\s*matrix\(([^)]*)\)\s*$', transform)
    if m:
        a, b, c, d, e, f = [float(v) for v in re.split(r'[\s,]+', m.group(1).strip())]
        if abs(b) > 1e-9 or abs(c) > 1e-9 or a <= 0 or d <= 0:
            raise ValueError('The logo group transform must be a positive scale and offset only: ' + transform)
        return (a, d, e, f)
    m = re.match(r'^\s*translate\(([^)]*)\)\s*$', transform)
    if m:
        v = [float(x) for x in re.split(r'[\s,]+', m.group(1).strip())]
        return (1.0, 1.0, v[0], v[1] if len(v) > 1 else 0.0)
    m = re.match(r'^\s*scale\(([^)]*)\)\s*$', transform)
    if m:
        v = [float(x) for x in re.split(r'[\s,]+', m.group(1).strip())]
        return (v[0], v[1] if len(v) > 1 else v[0], 0.0, 0.0)
    raise ValueError('Unsupported logo transform: ' + transform)


def _append_logo(root):
    """The KLCode logo: the two SVG outlines, the group's transform as one MatrixTransform, the view-box canvas."""
    svg = ET.parse(LOGO_SVG).getroot()
    box = [float(v) for v in re.split(r'[\s,]+', svg.attrib['viewBox'].strip())]
    if box[0] or box[1]:
        raise ValueError('The logo view box must start at 0,0.')
    w, h = box[2], box[3]
    parents = dict((child, parent) for parent in svg.iter() for child in parent)
    paths = list(svg.iter('{' + SVG + '}path'))
    if len(paths) != 2:
        raise ValueError('The logo SVG must hold exactly two paths (slash, letters); found %d' % len(paths))
    transforms = []
    for path in paths:
        # Compose the path's own transform with each enclosing group's, innermost first.
        a, d, e, f, node = 1.0, 1.0, 0.0, 0.0, path
        while node is not None and node is not svg:
            ga, gd, ge, gf = _matrix(node.attrib.get('transform', ''))
            a, d, e, f = ga * a, gd * d, ga * e + ge, gd * f + gf
            node = parents.get(node)
        transforms.append((a, d, e, f))
    if len(set(transforms)) != 1:
        raise ValueError('Both logo paths must share one transform.')
    a, d, e, f = transforms[0]
    for path in paths:
        pts = path_points(path.attrib['d'])
        xs, ys = [a * p[0] + e for p in pts], [d * p[1] + f for p in pts]
        if min(xs) < -LOGO_TOLERANCE or max(xs) > w + LOGO_TOLERANCE or min(ys) < -LOGO_TOLERANCE or max(ys) > h + LOGO_TOLERANCE:
            raise ValueError('Logo geometry leaves the view box: x %.2f..%.2f y %.2f..%.2f' % (min(xs), max(xs), min(ys), max(ys)))
    for key, path in (('klcLogoSlash', paths[0]), ('klcLogoLetters', paths[1])):
        element(root, 'PathGeometry', {'{' + XAML + '}Key': key, 'Figures': path.attrib['d']})
    element(root, 'MatrixTransform', {'{' + XAML + '}Key': 'klcLogoTransform',
                                      'Matrix': ','.join('%.10g' % v for v in (a, 0, 0, d, e, f))})
    for key, value in (('klcLogoCanvasWidth', w), ('klcLogoCanvasHeight', h)):
        node = ET.SubElement(root, '{' + SYS + '}Double', {'{' + XAML + '}Key': key})
        node.text = '%g' % value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if resources need regeneration.')
    args = parser.parse_args()
    outputs = [(ICONS_XAML, generate_icons())]
    stale = [str(path.relative_to(ROOT)) for path, text in outputs if not path.exists() or path.read_text(encoding='utf-8') != text]
    if args.check:
        if stale:
            raise SystemExit('GUI artwork resources are stale (%s); run scripts/generate_gui_icons.py.' % ', '.join(stale))
    else:
        for path, text in outputs:
            path.write_text(text, encoding='utf-8')
    print('{} approved GUI icon roles and the KLCode logo verified.'.format(len(ROLES)))


if __name__ == '__main__':
    main()
