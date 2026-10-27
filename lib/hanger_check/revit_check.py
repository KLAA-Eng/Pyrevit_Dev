"""Revit API adapter shared by the hanger check commands.

Elements are tracked in an {int id: element} dict so reports and overrides
reuse the real ElementIds. Highlights are always rebuilt for every hanger
visible in the view: existing check colors are cleared first, so hangers that
were fixed since the last run lose their highlight.
"""

from pyrevit import DB

from .classify import (
    DEFAULT_HANGER_FAMILY,
    ROLE_BOTH,
    ROLE_SUPPORTED,
    ROLE_SUPPORTING,
    SEARCH_RADIUS_FT,
    STATUS_OK,
    VERTICAL_REACH_FT,
    classify_hanger,
    flag_shared_ends,
    matches_family,
    member_roles,
)


PROBLEM_KEY = 'problem'
COLORS = {
    ROLE_SUPPORTED: (0, 67, 255),
    ROLE_SUPPORTING: (255, 255, 0),
    ROLE_BOTH: (0, 176, 80),
    PROBLEM_KEY: (206, 1, 1),
}
ZOOM_MARGIN_FT = 4.0
INFO_BUILTINS = ('ALL_MODEL_MARK', 'ALL_MODEL_INSTANCE_COMMENTS')


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


def hanger_info(doc, hanger):
    """Hanger type name plus its non-empty text parameters, for comparing with the framing."""
    keep = set(getattr(DB.BuiltInParameter, name) for name in INFO_BUILTINS)
    values = {}
    for source in (hanger, doc.GetElement(hanger.GetTypeId())):
        if source is None:
            continue
        for param in source.Parameters:
            try:
                if param.StorageType != DB.StorageType.String or not param.HasValue:
                    continue
                builtin = getattr(param.Definition, 'BuiltInParameter',
                                  DB.BuiltInParameter.INVALID)
                if builtin != DB.BuiltInParameter.INVALID and builtin not in keep:
                    continue
                value = param.AsString()
                if value and value.strip():
                    values.setdefault(param.Definition.Name, value.strip())
            except Exception:
                continue
    parts = [type_name(doc, hanger)]
    parts.extend('%s: %s' % (name, values[name]) for name in sorted(values))
    return '; '.join(parts)


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


def framing_near(doc, point, elements):
    low = DB.XYZ(point.X - SEARCH_RADIUS_FT, point.Y - SEARCH_RADIUS_FT,
                 point.Z - VERTICAL_REACH_FT)
    high = DB.XYZ(point.X + SEARCH_RADIUS_FT, point.Y + SEARCH_RADIUS_FT,
                  point.Z + VERTICAL_REACH_FT)
    collector = (DB.FilteredElementCollector(doc)
                 .OfCategory(DB.BuiltInCategory.OST_StructuralFraming)
                 .WhereElementIsNotElementType()
                 .WherePasses(DB.BoundingBoxIntersectsFilter(DB.Outline(low, high))))
    members = []
    for framing in collector:
        if isinstance(framing.Location, DB.LocationCurve):
            curve = framing.Location.Curve
            elements[id_value(framing.Id)] = framing
            members.append({'id': id_value(framing.Id),
                            'start': _xyz(curve.GetEndPoint(0)),
                            'end': _xyz(curve.GetEndPoint(1))})
    return members


def check_hangers(doc, hangers, elements):
    """Classify each hanger. Returns {hanger id: result}; fills elements."""
    results = {}
    for hanger in hangers:
        point = hanger.Location.Point
        elements[id_value(hanger.Id)] = hanger
        results[id_value(hanger.Id)] = classify_hanger(
            _xyz(point), framing_near(doc, point, elements), text_direction(hanger))
    return flag_shared_ends(results)


def _solid_fill_id(doc):
    for pattern in DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement):
        if pattern.GetFillPattern().IsSolidFill:
            return pattern.Id
    return None


def _member_override(rgb, solid_fill_id):
    color = DB.Color(*rgb)
    settings = DB.OverrideGraphicSettings()
    settings.SetProjectionLineColor(color)
    settings.SetCutLineColor(color)
    if solid_fill_id is not None:
        settings.SetSurfaceForegroundPatternId(solid_fill_id)
        settings.SetSurfaceForegroundPatternColor(color)
    return settings


def _hanger_override():
    """Halftoned red lines only, so hanger text stays readable."""
    settings = DB.OverrideGraphicSettings()
    settings.SetProjectionLineColor(DB.Color(*COLORS[PROBLEM_KEY]))
    settings.SetHalftone(True)
    return settings


def _is_check_color(settings):
    try:
        color = settings.ProjectionLineColor
        return color.IsValid and (color.Red, color.Green, color.Blue) in COLORS.values()
    except Exception:
        return False


def _highlighted_ids(doc, view):
    return [e.Id for e in DB.FilteredElementCollector(doc, view.Id).WhereElementIsNotElementType()
            if _is_check_color(view.GetElementOverrides(e.Id))]


def has_highlights(doc, view):
    return bool(_highlighted_ids(doc, view))


def _reset(view, element_ids):
    for element_id in element_ids:
        view.SetElementOverrides(element_id, DB.OverrideGraphicSettings())


def clear_highlights(doc, view, transaction):
    """Reset overrides that use a hanger check color. Returns the count cleared."""
    highlighted = _highlighted_ids(doc, view)
    with transaction('Clear hanger check highlights', doc=doc):
        _reset(view, highlighted)
    return len(highlighted)


def refresh_highlights(doc, view, results, elements, transaction):
    """Clear old check colors, then color members by role and problem hangers."""
    solid_fill_id = _solid_fill_id(doc)
    highlighted = _highlighted_ids(doc, view)
    with transaction('Refresh hanger check highlights', doc=doc):
        _reset(view, highlighted)
        for member_id, role in member_roles(results).items():
            view.SetElementOverrides(elements[member_id].Id,
                                     _member_override(COLORS[role], solid_fill_id))
        for hanger_id, result in results.items():
            if result['status'] != STATUS_OK:
                view.SetElementOverrides(elements[hanger_id].Id, _hanger_override())


def zoom_to(uidoc, view, hangers):
    """Zoom the active view around the hangers' insertion points."""
    points = [h.Location.Point for h in hangers]
    if not points:
        return
    ui_views = [v for v in uidoc.GetOpenUIViews() if v.ViewId == view.Id]
    if not ui_views:
        return
    low = DB.XYZ(min(p.X for p in points) - ZOOM_MARGIN_FT,
                 min(p.Y for p in points) - ZOOM_MARGIN_FT, min(p.Z for p in points))
    high = DB.XYZ(max(p.X for p in points) + ZOOM_MARGIN_FT,
                  max(p.Y for p in points) + ZOOM_MARGIN_FT, max(p.Z for p in points))
    ui_views[0].ZoomAndCenterRectangle(low, high)
