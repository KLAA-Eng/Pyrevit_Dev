"""Revit API adapter shared by the hanger check commands.

Elements are tracked in an {int id: element} dict so reports and overrides
reuse the real ElementIds. Highlights are always rebuilt for every hanger
visible in the view: existing check colors and hexagon outlines are cleared
first, so hangers that were fixed since the last run lose their highlight.

In plan views framing is taken from what the view shows and compared in plan,
ignoring the hanger's height (the Dynamo graph projected onto the level).
The hanger's hexagon is found in its plan linework; its flat sides along the
text locate the supported member, and highlights trace it with heavy colored
detail lines, so the hanger text keeps its own color.
"""

from System.Collections.Generic import List

from pyrevit import DB

from .classify import (
    DEFAULT_HANGER_FAMILY,
    ROLE_BOTH,
    ROLE_SUPPORTED,
    ROLE_SUPPORTING,
    SEARCH_RADIUS_FT,
    STATUS_REVIEW_DETAILS,
    VERTICAL_REACH_FT,
    apply_review,
    classify_hanger,
    flag_shared_ends,
    is_problem,
    matches_family,
    member_roles,
    slope_label,
)
from .outline import find_hexagons, flat_side_offsets, loop_segments
from .sizes import (
    DETAIL_KINDS,
    compare_size,
    compare_supporting,
    member_width,
    mismatch_label,
    mounting_label,
    support_kind,
)


PROBLEM_KEY = 'problem'
DETAILS_KEY = 'details'
COLORS = {
    ROLE_SUPPORTED: (0, 102, 255),
    ROLE_SUPPORTING: (255, 128, 0),
    ROLE_BOTH: (153, 51, 255),
    PROBLEM_KEY: (230, 0, 0),
    DETAILS_KEY: (0, 160, 160),
}
LEGACY_COLORS = ((0, 67, 255), (255, 255, 0), (0, 176, 80), (206, 1, 1))
MEMBER_LINE_WEIGHT = 6
HEXAGON_LINE_WEIGHT = 10
LINE_STYLE_PREFIX = 'KLA Hanger Check - '
LINE_STYLES = {PROBLEM_KEY: 'Problem', DETAILS_KEY: 'Review details'}
PLAN_Z_REACH_FT = 10000.0
HANGER_FIELDS = ('Designation', 'Header', 'Joist')
TOP_FLANGE_FIELD = 'Fastener-TF'
WIDTH_PARAMS = ('b', 'Width', 'B', 'Beam Width', 'Nominal Width')
DEPTH_PARAMS = ('d', 'Depth', 'h', 'Height', 'Beam Depth', 'Nominal Depth')


def id_value(element_id):
    return element_id.Value if hasattr(element_id, 'Value') else element_id.IntegerValue


def _xyz(point):
    return (point.X, point.Y, point.Z)


def type_name(doc, element):
    element_type = doc.GetElement(element.GetTypeId())
    param = element_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM) if element_type else None
    return (param.AsString() if param else None) or '-'


def member_label(doc, element):
    """'Family: Type' for a framing member."""
    family = element.Symbol.FamilyName if isinstance(element, DB.FamilyInstance) else ''
    return '%s: %s' % (family, type_name(doc, element)) if family else type_name(doc, element)


def _text_param(sources, name):
    for source in sources:
        param = source.LookupParameter(name) if source is not None else None
        if param is not None and param.HasValue:
            value = param.AsString() if param.StorageType == DB.StorageType.String \
                else param.AsValueString()
            if value and value.strip():
                return value.strip()
    return None


def hanger_values(doc, hanger):
    """{Type, Designation, Header, Joist, Fastener-TF}: the hanger's type name, then
    schedule values from the instance, then its type."""
    sources = (hanger, doc.GetElement(hanger.GetTypeId()))
    values = dict((name, _text_param(sources, name))
                  for name in HANGER_FIELDS + (TOP_FLANGE_FIELD,))
    values['Type'] = type_name(doc, hanger)
    return values


def hanger_info(values):
    return '; '.join('%s: %s' % (name, values.get(name) or '-')
                     for name in ('Type',) + HANGER_FIELDS)


def _length_in(doc, element, names):
    sources = (element, doc.GetElement(element.GetTypeId()))
    for name in names:
        for source in sources:
            param = source.LookupParameter(name) if source is not None else None
            if (param is not None and param.HasValue
                    and param.StorageType == DB.StorageType.Double and param.AsDouble() > 0):
                return param.AsDouble() * 12.0
    return None


def _compare_member(doc, hanger_text, element, compare):
    if element is None or not hanger_text:
        return None, None
    return compare(hanger_text, member_label(doc, element),
                   _length_in(doc, element, WIDTH_PARAMS),
                   _length_in(doc, element, DEPTH_PARAMS))


def is_hanger(element):
    return (isinstance(element, DB.FamilyInstance)
            and isinstance(element.Location, DB.LocationPoint)
            and matches_family(element.Symbol.FamilyName, DEFAULT_HANGER_FAMILY))


def hangers_in_view(doc, view):
    collector = DB.FilteredElementCollector(doc, view.Id).OfClass(DB.FamilyInstance)
    return [e for e in collector if is_hanger(e)]


def selected_hangers(uidoc):
    doc = uidoc.Document
    return [e for e in (doc.GetElement(i) for i in uidoc.Selection.GetElementIds())
            if e is not None and is_hanger(e)]


def text_direction(hanger):
    """Plan direction of the hanger text: the family's local X axis."""
    basis = hanger.GetTransform().BasisX
    return (basis.X, basis.Y)


def is_plan(view):
    return isinstance(view, DB.ViewPlan)


def framing_near(doc, view, point, elements):
    """Framing near the hanger: in plan views, at any height the view shows."""
    plan = is_plan(view)
    reach = PLAN_Z_REACH_FT if plan else VERTICAL_REACH_FT
    low = DB.XYZ(point.X - SEARCH_RADIUS_FT, point.Y - SEARCH_RADIUS_FT, point.Z - reach)
    high = DB.XYZ(point.X + SEARCH_RADIUS_FT, point.Y + SEARCH_RADIUS_FT, point.Z + reach)
    collector = (DB.FilteredElementCollector(doc, view.Id) if plan
                 else DB.FilteredElementCollector(doc))
    collector = (collector
                 .OfCategory(DB.BuiltInCategory.OST_StructuralFraming)
                 .WhereElementIsNotElementType()
                 .WherePasses(DB.BoundingBoxIntersectsFilter(DB.Outline(low, high))))
    members = []
    for framing in collector:
        if isinstance(framing.Location, DB.LocationCurve):
            curve = framing.Location.Curve
            elements[id_value(framing.Id)] = framing
            width_in = member_width(member_label(doc, framing),
                                    _length_in(doc, framing, WIDTH_PARAMS))
            members.append({'id': id_value(framing.Id),
                            'start': _xyz(curve.GetEndPoint(0)),
                            'end': _xyz(curve.GetEndPoint(1)),
                            'half_width': width_in / 24.0 if width_in else 0.0})
    return members


def check_hangers(doc, view, hangers, elements):
    """Classify each hanger. Returns {hanger id: result}; fills elements."""
    results = {}
    for hanger in hangers:
        point = hanger.Location.Point
        elements[id_value(hanger.Id)] = hanger
        xyz = (point.X, point.Y, None) if is_plan(view) else _xyz(point)
        hexagon = _hexagon(hanger, view)
        flat_sides = (flat_side_offsets(hexagon, text_direction(hanger), (point.X, point.Y))
                      if hexagon else None)
        result = classify_hanger(xyz, framing_near(doc, view, point, elements),
                                 text_direction(hanger), flat_sides)
        result['hexagon'] = hexagon
        results[id_value(hanger.Id)] = result
    flag_shared_ends(results)
    for hanger_id, result in results.items():
        _add_size_check(doc, result, hanger_values(doc, elements[hanger_id]), elements)
    return results


def _add_size_check(doc, result, values, elements):
    """Joist vs supported member (strict), Header vs supporting member (loose)."""
    result['hanger_values'] = values
    checks = []
    for field, key, compare in (('Joist', 'supported', compare_size),
                                ('Header', 'supporting', compare_supporting)):
        member = elements.get(result[key]) if result[key] is not None else None
        ok, reason = _compare_member(doc, values.get(field), member, compare)
        checks.append(ok)
        if ok is False:
            result['notes'].append('%s "%s" vs %s: %s' % (
                field, values[field], member_label(doc, member), reason))
        elif ok is None and member is not None and values.get(field):
            result['notes'].append('%s "%s" not compared: %s' % (field, values[field], reason))
        elif ok and reason:
            result['notes'].append('%s: %s' % (field, reason))
    supporting = elements.get(result['supporting']) if result['supporting'] is not None else None
    kind = support_kind(values.get('Header'),
                        member_label(doc, supporting) if supporting is not None else None)
    result['mounting'] = mounting_label(kind, values.get(TOP_FLANGE_FIELD))
    supported = elements.get(result['supported']) if result['supported'] is not None else None
    result['supported_slope'] = member_slope(supported)
    apply_review(result, mismatch_label(checks[0], checks[1]), kind in DETAIL_KINDS)


def _solid_fill_id(doc):
    for pattern in DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement):
        if pattern.GetFillPattern().IsSolidFill:
            return pattern.Id
    return None


def _member_override(rgb, solid_fill_id):
    color = DB.Color(*rgb)
    settings = DB.OverrideGraphicSettings()
    settings.SetProjectionLineColor(color)
    settings.SetProjectionLineWeight(MEMBER_LINE_WEIGHT)
    settings.SetCutLineColor(color)
    if solid_fill_id is not None:
        settings.SetSurfaceForegroundPatternId(solid_fill_id)
        settings.SetSurfaceForegroundPatternColor(color)
    return settings


def _hanger_override(key):
    """Fallback when no hexagon is found: halftoned colored lines only."""
    settings = DB.OverrideGraphicSettings()
    settings.SetProjectionLineColor(DB.Color(*COLORS[key]))
    settings.SetHalftone(True)
    return settings


def _is_check_color(settings):
    try:
        color = settings.ProjectionLineColor
        rgb = (color.Red, color.Green, color.Blue)
        return color.IsValid and (rgb in COLORS.values() or rgb in LEGACY_COLORS)
    except Exception:
        return False


def _highlighted_ids(doc, view):
    return [e.Id for e in DB.FilteredElementCollector(doc, view.Id).WhereElementIsNotElementType()
            if _is_check_color(view.GetElementOverrides(e.Id))]


def _outline_ids(doc, view):
    """Detail lines drawn by the check (line styles named LINE_STYLE_PREFIX...)."""
    ids = []
    for curve in DB.FilteredElementCollector(doc, view.Id).OfClass(DB.CurveElement):
        style = curve.LineStyle
        if style is not None and style.Name.startswith(LINE_STYLE_PREFIX):
            ids.append(curve.Id)
    return ids


def has_highlights(doc, view):
    return bool(_highlighted_ids(doc, view) or _outline_ids(doc, view))


def _reset(doc, view, element_ids, outline_ids):
    for element_id in element_ids:
        view.SetElementOverrides(element_id, DB.OverrideGraphicSettings())
    for outline_id in outline_ids:
        doc.Delete(outline_id)


def clear_highlights(doc, view, transaction):
    """Reset check colors and delete hexagon outlines. Returns the count cleared."""
    highlighted, outlines = _highlighted_ids(doc, view), _outline_ids(doc, view)
    with transaction('Clear hanger check highlights', doc=doc):
        _reset(doc, view, highlighted, outlines)
    return len(highlighted) + len(outlines)


def _line_style(doc, key):
    """Projection GraphicsStyle of the check's line style, created on first use."""
    categories = doc.Settings.Categories
    lines = categories.get_Item(DB.BuiltInCategory.OST_Lines)
    name = LINE_STYLE_PREFIX + LINE_STYLES[key]
    if lines.SubCategories.Contains(name):
        sub = lines.SubCategories.get_Item(name)
    else:
        sub = categories.NewSubcategory(lines, name)
    sub.LineColor = DB.Color(*COLORS[key])
    sub.SetLineWeight(HEXAGON_LINE_WEIGHT, DB.GraphicsStyleType.Projection)
    return sub.GetGraphicsStyle(DB.GraphicsStyleType.Projection)


def _plan_segments(element, view):
    """Plan line pieces of the element's geometry as seen in the view."""
    options = DB.Options()
    options.View = view
    segments = []

    def add(curve):
        if isinstance(curve, DB.Line):
            p, q = curve.GetEndPoint(0), curve.GetEndPoint(1)
            segments.append(((p.X, p.Y), (q.X, q.Y)))

    def walk(geometry):
        for item in geometry:
            if isinstance(item, DB.GeometryInstance):
                walk(item.GetInstanceGeometry())
            elif isinstance(item, DB.Line):
                add(item)
            elif isinstance(item, DB.PolyLine):
                points = list(item.GetCoordinates())
                for p, q in zip(points, points[1:]):
                    segments.append(((p.X, p.Y), (q.X, q.Y)))
            elif isinstance(item, DB.Solid):
                for edge in item.Edges:
                    add(edge.AsCurve())

    geometry = element.get_Geometry(options)
    if geometry is not None:
        walk(geometry)
    return segments


def _plan_z(view):
    level = view.GenLevel if is_plan(view) else None
    return level.Elevation if level is not None else view.Origin.Z


def _hexagon(hanger, view):
    """The hanger's hexagon (6 plan points) from its linework in the view, else None."""
    hexagons = find_hexagons(_plan_segments(hanger, view))
    return hexagons[0] if hexagons else None


def _trace_hexagon(doc, view, hexagon, style):
    """Draw detail lines over the hanger's hexagon. False when there is none."""
    if not hexagon:
        return False
    z = _plan_z(view)
    try:
        for (x1, y1), (x2, y2) in loop_segments(hexagon):
            curve = doc.Create.NewDetailCurve(
                view, DB.Line.CreateBound(DB.XYZ(x1, y1, z), DB.XYZ(x2, y2, z)))
            curve.LineStyle = style
    except Exception:
        return False
    return True


def _hanger_key(result):
    if is_problem(result):
        return PROBLEM_KEY
    if result['status'] == STATUS_REVIEW_DETAILS:
        return DETAILS_KEY
    return None


def refresh_highlights(doc, view, results, elements, transaction):
    """Clear old check colors, then color members by role and outline hangers to review."""
    solid_fill_id = _solid_fill_id(doc)
    highlighted, outlines = _highlighted_ids(doc, view), _outline_ids(doc, view)
    with transaction('Refresh hanger check highlights', doc=doc):
        _reset(doc, view, highlighted, outlines)
        for member_id, role in member_roles(results).items():
            view.SetElementOverrides(elements[member_id].Id,
                                     _member_override(COLORS[role], solid_fill_id))
        styles = {}
        for hanger_id, result in results.items():
            key = _hanger_key(result)
            if key is None:
                continue
            if key not in styles:
                styles[key] = _line_style(doc, key)
            hanger = elements[hanger_id]
            if not _trace_hexagon(doc, view, result.get('hexagon'), styles[key]):
                view.SetElementOverrides(hanger.Id, _hanger_override(key))


def member_slope(element):
    """'Flat' or 'Sloped r:12 (a deg)' from a framing member's location line, else '-'."""
    if element is None or not isinstance(element.Location, DB.LocationCurve):
        return '-'
    curve = element.Location.Curve
    return slope_label(_xyz(curve.GetEndPoint(0)), _xyz(curve.GetEndPoint(1)))


def zoom_to(uidoc, view, elements):
    """Select the elements and zoom the active view to their bounding boxes in
    that view (ZoomAndCenterRectangle, as in the pyRevit forum "Zoom / Go to
    element" solution). Returns the elements not visible in the view; nothing
    zooms when none are visible or the view is not open."""
    ui_view = next((v for v in uidoc.GetOpenUIViews() if v.ViewId == view.Id), None)
    boxes, hidden = [], []
    for element in elements:
        box = element.get_BoundingBox(view)
        if box is None:
            hidden.append(element)
        else:
            boxes.append(box)
    if ui_view is None or not boxes:
        return list(elements)
    uidoc.Selection.SetElementIds(List[DB.ElementId]([e.Id for e in elements]))
    low = DB.XYZ(min(b.Min.X for b in boxes), min(b.Min.Y for b in boxes),
                 min(b.Min.Z for b in boxes))
    high = DB.XYZ(max(b.Max.X for b in boxes), max(b.Max.Y for b in boxes),
                  max(b.Max.Z for b in boxes))
    ui_view.ZoomAndCenterRectangle(low, high)
    return hidden
