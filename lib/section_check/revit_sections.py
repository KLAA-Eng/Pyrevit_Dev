"""Revit API adapter for Check Section References.

For each reference section marker in a plan view, the model elements cut at
the marker are compared with the referenced detail: the elements cut by a live
referenced section (elsewhere in the model), or the component names and notes
of a referenced drafting view. Nothing in the model changes.

Cuts are read inside a window: a vertical rectangle on the cut plane, extruded
CUT_BAND_FT to each side, intersected with walls, floors, framing, columns,
foundations, and roofs by solid. A live reference uses its crop box width and
height; the marker's window takes that width and the same height above and
below the plan's level as the crop has above and below its nearest level, so
both windows frame the same part of the condition. A drafting reference uses
the marker length (clamped) and DEFAULT_BELOW_FT / DEFAULT_ABOVE_FT.
"""

from System.Collections.Generic import List

from pyrevit import DB

from .conditions import (
    COLUMN,
    FLOOR,
    FOUNDATION,
    FRAMING,
    ROOF,
    VERTICAL,
    WALL,
    condition,
    detail_content,
    orientation,
)
from .markers import assign_notes, closest_on_segment, cut_line, right_of, unit
from .score import compare_detail, compare_sections


CUT_BAND_FT = 1.0
DEFAULT_BELOW_FT = 4.0
DEFAULT_ABOVE_FT = 4.0
MIN_WIDTH_FT, MAX_WIDTH_FT = 4.0, 12.0
NOTE_REACH_IN = 0.75
GROUPS = (
    (DB.BuiltInCategory.OST_Walls, WALL),
    (DB.BuiltInCategory.OST_Floors, FLOOR),
    (DB.BuiltInCategory.OST_StructuralFraming, FRAMING),
    (DB.BuiltInCategory.OST_StructuralColumns, COLUMN),
    (DB.BuiltInCategory.OST_Columns, COLUMN),
    (DB.BuiltInCategory.OST_StructuralFoundation, FOUNDATION),
    (DB.BuiltInCategory.OST_Roofs, ROOF),
)
KIND_SECTION, KIND_DRAFTING, KIND_OTHER = 'Section', 'Drafting', 'Not compared'


def id_value(element_id):
    return element_id.Value if hasattr(element_id, 'Value') else element_id.IntegerValue


def _type_name(doc, element):
    element_type = doc.GetElement(element.GetTypeId())
    param = element_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM) if element_type else None
    return (param.AsString() if param else None) or '-'


def element_label(doc, element):
    """'Family: Type' for family instances, else the type name."""
    family = element.Symbol.FamilyName if isinstance(element, DB.FamilyInstance) else ''
    name = _type_name(doc, element)
    return '%s: %s' % (family, name) if family else name


def _plan(point):
    return (point.X, point.Y)


def reference_markers(doc, view):
    """[(marker element, referenced view or None)] for the view's reference sections."""
    markers = []
    for marker_id in view.GetReferenceSections():
        marker = doc.GetElement(marker_id)
        try:
            referenced = doc.GetElement(DB.ReferenceableViewUtils.GetReferencedViewId(doc, marker_id))
        except Exception:
            referenced = None
        if marker is not None:
            markers.append((marker, referenced))
    return markers


def other_marker_count(doc, view, markers):
    """Section, callout, and elevation markers in the view that are not references."""
    viewers = (DB.FilteredElementCollector(doc, view.Id)
               .OfCategory(DB.BuiltInCategory.OST_Viewers).WhereElementIsNotElementType())
    return max(0, viewers.GetElementCount() - len(markers))


def _walk(geometry, segments, points):
    for item in geometry or ():
        if isinstance(item, DB.GeometryInstance):
            _walk(item.GetInstanceGeometry(), segments, points)
        elif isinstance(item, DB.Line):
            segments.append((_plan(item.GetEndPoint(0)), _plan(item.GetEndPoint(1))))
        elif isinstance(item, DB.Curve):
            points.extend(_plan(p) for p in item.Tessellate())
        elif isinstance(item, DB.PolyLine):
            points.extend(_plan(p) for p in item.GetCoordinates())


def marker_line(marker, view):
    """cut_line() of the marker as drawn in the view; without drawn lines, the
    long axis of its box in the view with an unknown look direction."""
    options = DB.Options()
    options.View = view
    segments, points = [], []
    try:
        _walk(marker.get_Geometry(options), segments, points)
    except Exception:
        pass
    line = cut_line(segments, points)
    if line is not None:
        return line
    box = marker.get_BoundingBox(view)
    if box is None:
        return None
    low, high = _plan(box.Min), _plan(box.Max)
    mid_x, mid_y = (low[0] + high[0]) / 2.0, (low[1] + high[1]) / 2.0
    if high[0] - low[0] >= high[1] - low[1]:
        return {'start': (low[0], mid_y), 'end': (high[0], mid_y), 'look': None}
    return {'start': (mid_x, low[1]), 'end': (mid_x, high[1]), 'look': None}


def marker_notes(doc, view, lines):
    """assign_notes() for the view's text notes and the markers' cut lines."""
    notes = []
    for note in DB.FilteredElementCollector(doc, view.Id).OfClass(DB.TextNote):
        box = note.get_BoundingBox(view)
        if box is not None:
            notes.append((note.Text, _plan(box.Min), _plan(box.Max)))
    reach = NOTE_REACH_IN / 12.0 * max(view.Scale, 1)
    return assign_notes(dict((key, (line['start'], line['end'])) for key, line in lines.items()),
                        notes, reach)


def _levels(doc):
    return sorted(level.ProjectElevation for level in
                  DB.FilteredElementCollector(doc).OfClass(DB.Level))


def section_window(doc, section):
    """Window of a live section from its crop box: {'center' (x, y), 'right',
    'look', 'width', 'below', 'above', 'anchor'} with below/above relative to
    the anchor, the level nearest the crop's middle; None for views that are
    not vertical."""
    crop = section.CropBox
    transform = crop.Transform
    if abs(section.ViewDirection.Z) > 0.1:
        return None
    middle = transform.OfPoint(DB.XYZ((crop.Min.X + crop.Max.X) / 2.0,
                                      (crop.Min.Y + crop.Max.Y) / 2.0, crop.Max.Z))
    half_height = (crop.Max.Y - crop.Min.Y) / 2.0
    levels = _levels(doc)
    anchor = min(levels, key=lambda z: abs(z - middle.Z)) if levels else middle.Z
    look = unit((-section.ViewDirection.X, -section.ViewDirection.Y))
    return {'center': _plan(middle), 'right': right_of(look), 'look': look,
            'width': crop.Max.X - crop.Min.X,
            'below': middle.Z - half_height - anchor, 'above': middle.Z + half_height - anchor,
            'anchor': anchor}


def marker_window(view, line, width=None, below=DEFAULT_BELOW_FT, above=DEFAULT_ABOVE_FT):
    """Window at a marker on the plan's level. Without a known look direction
    the left-hand normal of the cut line stands in (hand then not checked)."""
    start, end = line['start'], line['end']
    direction = unit((end[0] - start[0], end[1] - start[1])) or (1.0, 0.0)
    look = line['look'] or (-direction[1], direction[0])
    if width is None:
        length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
        width = max(MIN_WIDTH_FT, min(MAX_WIDTH_FT, length))
    level = view.GenLevel
    anchor = level.ProjectElevation if level is not None else 0.0
    return {'center': ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0),
            'right': right_of(look), 'look': look, 'width': width,
            'below': below, 'above': above, 'anchor': anchor}


def _window_solid(window):
    center, right, look, anchor = (window['center'], window['right'], window['look'],
                                   window['anchor'])
    r = DB.XYZ(right[0], right[1], 0.0) * (window['width'] / 2.0)
    l = DB.XYZ(look[0], look[1], 0.0)
    base = DB.XYZ(center[0], center[1], 0.0) - l * CUT_BAND_FT
    low = DB.XYZ(0.0, 0.0, anchor + window['below'])
    high = DB.XYZ(0.0, 0.0, anchor + window['above'])
    corners = [base - r + low, base + r + low, base + r + high, base - r + high]
    curves = List[DB.Curve]([DB.Line.CreateBound(corners[i], corners[(i + 1) % 4])
                             for i in range(4)])
    loops = List[DB.CurveLoop]([DB.CurveLoop.Create(curves)])
    return DB.GeometryCreationUtilities.CreateExtrusionGeometry(loops, l, 2.0 * CUT_BAND_FT)


def _group(element):
    category = element.Category
    if category is None:
        return None
    for built_in, group in GROUPS:
        if id_value(category.Id) == int(built_in):
            return group
    return None


def _condition(doc, element, group, window):
    center, right = window['center'], window['right']
    location = element.Location
    orient, point = None, None
    if isinstance(location, DB.LocationCurve):
        start, end = location.Curve.GetEndPoint(0), location.Curve.GetEndPoint(1)
        orient = orientation((end.X - start.X, end.Y - start.Y), right)
        point = closest_on_segment(center, _plan(start), _plan(end))
    elif isinstance(location, DB.LocationPoint):
        point = _plan(location.Point)
    if group == COLUMN:
        orient = VERTICAL
    offset = None
    if point is not None:
        offset = (point[0] - center[0]) * right[0] + (point[1] - center[1]) * right[1]
    return condition(group, element_label(doc, element), orient, offset)


def cut_conditions(doc, window):
    """Conditions for the model elements inside the window."""
    solid = _window_solid(window)
    box = solid.GetBoundingBox()
    corners = [box.Transform.OfPoint(box.Min), box.Transform.OfPoint(box.Max)]
    outline = DB.Outline(DB.XYZ(*[min(getattr(p, k) for p in corners) for k in 'XYZ']),
                         DB.XYZ(*[max(getattr(p, k) for p in corners) for k in 'XYZ']))
    categories = List[DB.BuiltInCategory]([built_in for built_in, _group in GROUPS])
    collector = (DB.FilteredElementCollector(doc)
                 .WherePasses(DB.ElementMulticategoryFilter(categories))
                 .WhereElementIsNotElementType()
                 .WherePasses(DB.BoundingBoxIntersectsFilter(outline))
                 .WherePasses(DB.ElementIntersectsSolidFilter(solid)))
    conditions = []
    for element in collector:
        group = _group(element)
        if group is not None:
            conditions.append(_condition(doc, element, group, window))
    return sorted(conditions, key=lambda c: (c['group'], c['label']))


def drafting_content(doc, drafting):
    """detail_content() of a drafting view's detail components, filled regions,
    and text notes."""
    labels = [element_label(doc, e) for e in DB.FilteredElementCollector(doc, drafting.Id)
              .OfCategory(DB.BuiltInCategory.OST_DetailComponents)
              .WhereElementIsNotElementType()]
    for region in DB.FilteredElementCollector(doc, drafting.Id).OfClass(DB.FilledRegion):
        region_type = doc.GetElement(region.GetTypeId())
        if region_type is not None:
            labels.append(DB.Element.Name.GetValue(region_type))
    texts = [n.Text for n in DB.FilteredElementCollector(doc, drafting.Id).OfClass(DB.TextNote)]
    return detail_content(labels, texts)


def _view_param(view, built_in):
    param = view.get_Parameter(built_in)
    value = param.AsString() if param is not None and param.HasValue else None
    return value or None


def reference_label(view):
    """'View name (detail/sheet)', or the name alone when not on a sheet."""
    if view is None:
        return 'Missing referenced view'
    detail = _view_param(view, DB.BuiltInParameter.VIEWPORT_DETAIL_NUMBER)
    sheet = _view_param(view, DB.BuiltInParameter.VIEWPORT_SHEET_NUMBER)
    placed = ' (%s/%s)' % (detail, sheet) if detail and sheet else ' (not on a sheet)'
    return view.Name + placed


def _check_marker(doc, view, marker, referenced, line, flags, section_cache):
    result = {'marker': marker, 'reference': reference_label(referenced),
              'flags': flags, 'here': [], 'ref': [], 'kind': KIND_OTHER}
    if line is None:
        result.update(percent=None, rating="Can't tell", notes=['Marker line not found'])
        return result
    if isinstance(referenced, DB.ViewDrafting):
        result['here'] = cut_conditions(doc, marker_window(view, line))
        result['kind'] = KIND_DRAFTING
        result.update(compare_detail(result['here'], drafting_content(doc, referenced),
                                     flags['sim'], flags['oh']))
        return result
    ref_window = section_window(doc, referenced) if isinstance(referenced, DB.ViewSection) else None
    if ref_window is None:
        result.update(percent=None, rating="Can't tell",
                      notes=['Referenced view is not a section or drafting view'])
        return result
    key = id_value(referenced.Id)
    if key not in section_cache:
        section_cache[key] = cut_conditions(doc, ref_window)
    window = marker_window(view, line, ref_window['width'],
                           ref_window['below'], ref_window['above'])
    result['here'] = cut_conditions(doc, window)
    result['ref'] = section_cache[key]
    result['kind'] = KIND_SECTION
    result.update(compare_sections(result['here'], result['ref'], flags['sim'], flags['oh'],
                                   hand_known=line['look'] is not None))
    return result


def check_markers(doc, view):
    """Results for every reference section in the plan view, each a dict with
    marker, reference, kind, flags (sim, oh, texts), here and ref conditions,
    percent, rating, and notes. A section referenced by several markers is
    cut once."""
    markers = reference_markers(doc, view)
    lines = dict((id_value(m.Id), marker_line(m, view)) for m, _r in markers)
    flags = marker_notes(doc, view, dict((k, v) for k, v in lines.items() if v is not None))
    empty = {'sim': False, 'oh': False, 'texts': []}
    section_cache = {}
    return [_check_marker(doc, view, marker, referenced, lines[id_value(marker.Id)],
                          flags.get(id_value(marker.Id), empty), section_cache)
            for marker, referenced in markers]
