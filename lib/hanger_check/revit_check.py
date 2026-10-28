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
ZOOM_MARGIN_FT = 3.0
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
    # Only framing and hangers (family instances) are colored by the check.
    return [e.Id for e in DB.FilteredElementCollector(doc, view.Id).OfClass(DB.FamilyInstance)
            if _is_check_color(view.GetElementOverrides(e.Id))]


def _outline_ids(doc, view):
    """Detail lines drawn by the check (line styles named LINE_STYLE_PREFIX...)."""
    ids = []
    for curve in DB.FilteredElementCollector(doc, view.Id).OfClass(DB.CurveElement):
        style = curve.LineStyle
        if style is not None and style.Name.startswith(LINE_STYLE_PREFIX):
            ids.append(curve.Id)
    return ids


def _reset(doc, view, element_ids, outline_ids):
    for element_id in element_ids:
        view.SetElementOverrides(element_id, DB.OverrideGraphicSettings())
    for outline_id in outline_ids:
        doc.Delete(outline_id)


def has_highlights(doc, view):
    return bool(_highlighted_ids(doc, view) or _outline_ids(doc, view))


def clear_highlights(doc, view, transaction):
    """Reset check colors and delete hexagon outlines in one view. Returns the count cleared."""
    highlighted, outlines = _highlighted_ids(doc, view), _outline_ids(doc, view)
    if highlighted or outlines:
        with transaction('Clear hanger check highlights', doc=doc):
            _reset(doc, view, highlighted, outlines)
        forget_view(doc, view)
    return len(highlighted) + len(outlines)


def _views_slot(doc):
    return 'KLA.HangerCheck.Views|' + doc.PathName + '|' + doc.Title


def _colored_view_ids(doc):
    from System import AppDomain
    text = AppDomain.CurrentDomain.GetData(_views_slot(doc)) or ''
    return [int(v) for v in str(text).split(',') if v]


def _set_colored_view_ids(doc, view_ids):
    from System import AppDomain
    AppDomain.CurrentDomain.SetData(_views_slot(doc), ','.join(str(v) for v in sorted(view_ids)))


def remember_view(doc, view):
    """Record a view the check colored (kept in the AppDomain across runs), so
    closing the report clears just those views instead of scanning the model."""
    _set_colored_view_ids(doc, set(_colored_view_ids(doc)) | {id_value(view.Id)})


def forget_view(doc, view):
    _set_colored_view_ids(doc, set(_colored_view_ids(doc)) - {id_value(view.Id)})


def clear_checked_views(doc, transaction):
    """Clear the highlights in every view the check has colored this session
    (views on sheets show those same views). Returns (elements cleared, views)."""
    if doc is None or not doc.IsValidObject:
        return 0, 0
    found = []
    for view_id in _colored_view_ids(doc):
        view = doc.GetElement(DB.ElementId(view_id))
        if isinstance(view, DB.View):
            ids, outlines = _highlighted_ids(doc, view), _outline_ids(doc, view)
            if ids or outlines:
                found.append((view, ids, outlines))
    if found:
        with transaction('Clear hanger check highlights', doc=doc):
            for view, ids, outlines in found:
                _reset(doc, view, ids, outlines)
    _set_colored_view_ids(doc, [])
    return sum(len(ids) + len(outlines) for _view, ids, outlines in found), len(found)


RUN_SLOT = 'KLA.HangerCheck.Run'


def start_run():
    """Mark a new Check Hanger Locations run; returns its token. Kept in the
    AppDomain so it survives pyRevit's per-run engines."""
    from System import AppDomain, Guid
    token = str(Guid.NewGuid())
    AppDomain.CurrentDomain.SetData(RUN_SLOT, token)
    return token


def is_current_run(token):
    from System import AppDomain
    return AppDomain.CurrentDomain.GetData(RUN_SLOT) == token


def clear_when_closed(window, doc, token, transaction):
    """When the report window closes, clear the views the check colored unless
    a newer run has started. The clear runs later in Revit's API context."""
    from pyrevit.revit.events import execute_in_revit_context

    def on_closed(sender, args):
        if is_current_run(token):
            execute_in_revit_context(clear_checked_views, doc, transaction)

    window.Closed += on_closed


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
    remember_view(doc, view)
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


def _zoom_points(element, view, targets):
    """Points to frame for one element: a hanger's insertion point plus its
    framing joint when known; a member's location line; else its bounding box
    in the view."""
    location = element.Location
    if isinstance(location, DB.LocationPoint):
        target = targets.get(id_value(element.Id))
        return [location.Point] + ([DB.XYZ(*target)] if target is not None else [])
    if isinstance(location, DB.LocationCurve):
        return [location.Curve.GetEndPoint(0), location.Curve.GetEndPoint(1)]
    box = element.get_BoundingBox(view)
    return [box.Min, box.Max]


def _sheet_viewports(doc, sheet):
    """(viewport, its view) for every viewport placed on the sheet."""
    viewports = [doc.GetElement(i) for i in sheet.GetAllViewports()]
    return [(vp, doc.GetElement(vp.ViewId)) for vp in viewports]


def _to_sheet(viewport, view, points):
    """Model points -> sheet points through the viewport, else None (Revit 2022+)."""
    try:
        transforms = view.GetModelToProjectionTransforms()
        to_sheet = viewport.GetProjectionToSheetTransform()
    except Exception:
        return None
    if not transforms:
        return None
    to_projection = transforms[0].GetModelToProjectionTransform()
    return [to_sheet.OfPoint(to_projection.OfPoint(p)) for p in points]


def _inside(outline, point):
    return (outline.MinimumPoint.X <= point.X <= outline.MaximumPoint.X
            and outline.MinimumPoint.Y <= point.Y <= outline.MaximumPoint.Y)


def view_showing(doc, view, element):
    """(viewport, model view) where the element shows: the view itself, or on a
    sheet the first viewport whose view shows it, else (None, None)."""
    if not isinstance(view, DB.ViewSheet):
        return None, view if element.get_BoundingBox(view) is not None else None
    for viewport, model_view in _sheet_viewports(doc, view):
        if element.get_BoundingBox(model_view) is not None:
            return viewport, model_view
    return None, None


def _sheet_frame(doc, sheet, element, targets):
    """(sheet points, margin) for an element on a sheet, else None. Sheet
    elements frame by their own box; model elements through the viewport that
    shows them, preferring one whose outline contains the mapped points."""
    if element.OwnerViewId == sheet.Id:
        box = element.get_BoundingBox(sheet)
        return ([box.Min, box.Max], 0.0) if box is not None else None
    fallback = None
    for viewport, model_view in _sheet_viewports(doc, sheet):
        if element.get_BoundingBox(model_view) is None:
            continue
        mapped = _to_sheet(viewport, model_view,
                           _zoom_points(element, model_view, targets))
        if mapped is None:
            continue
        frame = (mapped, ZOOM_MARGIN_FT / max(model_view.Scale, 1))
        outline = viewport.GetBoxOutline()
        if all(_inside(outline, p) for p in mapped):
            return frame
        fallback = fallback or frame
    return fallback


def zoom_to(uidoc, view, elements, targets=None):
    """Select the elements and zoom the active view to them with
    ZoomAndCenterRectangle (pyRevit forum "Zoom / Go to element"), plus a
    ZOOM_MARGIN_FT margin so the framing around a hanger stays in view.
    targets: {hanger id: (x, y, z)} framing joints from check_hangers.
    On a sheet, model elements are framed through the viewport that shows
    them, with the margin at the viewport's scale. Elements not visible in the
    view (or any viewport on the sheet) are skipped and returned. Nothing
    zooms when none are visible."""
    targets = targets or {}
    doc = uidoc.Document
    ui_view = next((v for v in uidoc.GetOpenUIViews() if v.ViewId == view.Id), None)
    frames, hidden = [], []
    for element in elements:
        if isinstance(view, DB.ViewSheet):
            frame = _sheet_frame(doc, view, element, targets)
        elif element.get_BoundingBox(view) is not None:
            frame = (_zoom_points(element, view, targets), ZOOM_MARGIN_FT)
        else:
            frame = None
        if frame is None:
            hidden.append(element)
        else:
            frames.append(frame)
    if ui_view is None or not frames:
        return list(elements)
    try:
        uidoc.Selection.SetElementIds(List[DB.ElementId]([e.Id for e in elements]))
    except Exception:
        pass
    low = DB.XYZ(min(p.X - m for pts, m in frames for p in pts),
                 min(p.Y - m for pts, m in frames for p in pts),
                 min(p.Z for pts, m in frames for p in pts))
    high = DB.XYZ(max(p.X + m for pts, m in frames for p in pts),
                  max(p.Y + m for pts, m in frames for p in pts),
                  max(p.Z for pts, m in frames for p in pts))
    ui_view.ZoomAndCenterRectangle(low, high)
    return hidden


def joint_targets(results):
    """{hanger id: framing joint} for check_hangers results that found one."""
    return dict((i, r['joint']) for i, r in results.items() if r.get('joint') is not None)


def hanger_joints(doc, view, hangers):
    """{hanger id: framing joint} for hangers, each checked in the view that
    shows it (on a sheet, its viewport's view)."""
    groups = {}
    for hanger in hangers:
        model_view = view_showing(doc, view, hanger)[1]
        if model_view is not None:
            groups.setdefault(id_value(model_view.Id), (model_view, []))[1].append(hanger)
    joints = {}
    for model_view, group in groups.values():
        joints.update(joint_targets(check_hangers(doc, model_view, group, {})))
    return joints


def _ribbon_ids(items, suffix, found):
    for item in items:
        item_id = getattr(item, 'Id', None) or ''
        if item_id.endswith(suffix):
            found.append(item_id)
        children = getattr(item, 'Items', None)
        if children is not None:
            _ribbon_ids(children, suffix, found)


def ribbon_control_id(button_name, near_id=None):
    """The Revit ribbon's own control id for a pyRevit button bundle name, read
    from the loaded ribbon (pyRevit's report button links silently do nothing
    when the id is wrong). Prefers a match in the same pulldown as near_id."""
    try:
        from pyrevit.api import AdWindows
        tabs = AdWindows.ComponentManager.Ribbon.Tabs
    except Exception:
        return None
    found = []
    for tab in tabs:
        for panel in tab.Panels:
            _ribbon_ids(panel.Source.Items, '%' + button_name, found)
    if near_id and '%' in near_id:
        prefix = near_id.rsplit('%', 1)[0] + '%'
        for item_id in found:
            if item_id.startswith(prefix):
                return item_id
    return found[0] if found else None
