# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Section\nDetailer"
__version__ = "v0.0"

import math
import os
import traceback

from pyrevit import DB, forms, revit, script
from System.Collections.Generic import List
from System.IO import File

from section_detailer.annotations import (
    BREAK_FAMILY,
    BREAK_TYPE,
    CONCRETE_REGION,
    EARTH_FOLDER,
    ELEVATION_FAMILY,
    ELEVATION_PATH,
    ELEVATION_TYPE,
    GRID_FAMILY,
    GRID_TYPE,
    PLATE_THICKNESS,
    SHEATHING_FAMILY,
    SOIL_FAMILY,
    STEEL_LABEL,
    break_segment,
    crop_crossings,
    floor_label,
    inset_rect,
    is_concrete,
    lowest_bottoms,
    merge_crossings,
    plate_centers,
    sheathing_layer,
    stud_layer,
    unique_tops,
    visible_top,
)
from section_detailer.matching import (
    LIBRARY_ROOT,
    STEEL,
    VIEW_SECTION,
    VIEW_SIDE,
    WOOD,
    WOOD_FOLDER,
    best_per_family,
    choose_wood_stack,
    family_matches_base,
    find_catalog_type,
    format_inches,
    match_key,
    member_spec,
    parse_catalog_sizes,
    parse_type_catalog,
    pick_library_file,
    rank_candidates,
    wood_family_bases,
)
from section_detailer.outline import (
    OUTLINE_STYLE,
    boundary_segments,
    join_collinear,
)
from section_detailer.view_geometry import (
    END_ON,
    IN_PLANE,
    OBLIQUE,
    bounds_center,
    classify_member,
    clip_polygon,
    clip_segment,
    crosses_plane,
    extent_along,
    line_plane_point,
    member_size,
    offset_down,
    ply_offsets,
    rotation_in_view,
    side_segment,
    signed_area,
    to_view,
    top_edges,
    unit_2d,
    width_direction,
)


COMMAND_TITLE = 'Section Detailer'
OVERLAY_MARKER = 'Section Detailer'
MINIMUM_REVIT_VERSION = 2023
MEMBER_CATEGORIES = ('OST_StructuralFraming', 'OST_StructuralColumns')
OVERLAY_CATEGORIES = ('OST_DetailComponents', 'OST_GenericAnnotation', 'OST_Lines')
# Elevation_KLAA labels: the description sits above the line ("Text Top"),
# the elevation below it ("Text Bottom"), with per-side copies for each type.
ELEVATION_TEXT_PARAMETERS = ('Description', 'Text Top', 'text right top', 'text left top')
ELEVATION_BLANK_PARAMETERS = ('Elevation', 'Text Bottom', 'text right bottom',
                              'text left bottom')
GRID_LABEL_PARAMETERS = ('Grid', 'Grid Label', 'Grid Number', 'Label', 'Text', 'Name')
SOIL_TYPE = '4" SOIL'
SHEATHING_THICKNESS_PARAMETERS = ('Thickness', 'Sheathing Thickness', 'Depth')
FACE_TOLERANCE = 1e-4
SHOW_WIDTH_ALIGNMENT = 0.7
MOVE_TOLERANCE = 1e-6
# Sheathing on joists, or plies against each other, share one break line.
BREAK_MERGE_TOLERANCE = 0.5 / 12.0
FLOOR_TOP_TOLERANCE = 0.125 / 12.0
# Paper-space gap between an element's end and its elevation symbol, in feet.
ELEVATION_GAP = 0.5 / 12.0
# Flip if the break family masks the inside of the crop instead of the outside.
BREAK_MASKS_RIGHT = True
# Half-thickness of the slab around the cut plane used to find linked elements.
LINK_SEARCH_DEPTH = 0.01

CUT = 'cut'
BEYOND = 'beyond'
ALONG = 'along'
PLATE = 'plate'

doc = revit.doc
view = doc.ActiveView
output = script.get_output()


def _stop(message):
    forms.alert(message, title=COMMAND_TITLE, warn_icon=True)
    script.exit()


def _xyz(vector):
    return (vector.X, vector.Y, vector.Z)


def _type_name(element):
    parameter = element.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
    return parameter.AsString() if parameter else None


def _comments(element):
    parameter = element.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    return parameter.AsString() if parameter else None


def _set_comments(element, value):
    parameter = element.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if parameter and not parameter.IsReadOnly:
        parameter.Set(value)


def _is_supported_revit_version():
    try:
        return int(doc.Application.VersionNumber) >= MINIMUM_REVIT_VERSION
    except Exception:
        return False


def _category_filter(names):
    categories = List[DB.BuiltInCategory](
        [getattr(DB.BuiltInCategory, name) for name in names])
    return DB.ElementMulticategoryFilter(categories)


class ViewFrame(object):
    """The active view's plane, axes, and crop in view coordinates."""

    def __init__(self, section):
        self.origin = _xyz(section.Origin)
        self.right = _xyz(section.RightDirection)
        self.up = _xyz(section.UpDirection)
        self.direction = _xyz(section.ViewDirection)
        self.plane = DB.Plane.CreateByNormalAndOrigin(section.ViewDirection, section.Origin)
        self.crop = None
        if section.CropBoxActive:
            box = section.CropBox
            corners = [self.to_view(box.Transform.OfPoint(point))
                       for point in (box.Min, box.Max)]
            self.crop = (min(c[0] for c in corners), min(c[1] for c in corners),
                         max(c[0] for c in corners), max(c[1] for c in corners))
        # Members stop, and break lines sit, just inside the crop.
        self.trim = inset_rect(self.crop)

    def to_view(self, point):
        return to_view(_xyz(point), self.origin, self.right, self.up)

    def in_view(self, vector):
        return (sum(a * b for a, b in zip(vector, self.right)),
                sum(a * b for a, b in zip(vector, self.up)))

    def to_model(self, uv):
        return view.Origin + view.RightDirection * uv[0] + view.UpDirection * uv[1]

    def offset(self, du, dv):
        return view.RightDirection * du + view.UpDirection * dv


# Collection and geometry

def _prior_overlay():
    collector = (DB.FilteredElementCollector(doc, view.Id)
                 .WherePasses(_category_filter(OVERLAY_CATEGORIES))
                 .WhereElementIsNotElementType())
    return [element for element in collector if _comments(element) == OVERLAY_MARKER]


def _visible_members():
    return list(DB.FilteredElementCollector(doc, view.Id)
                .WherePasses(_category_filter(MEMBER_CATEGORIES))
                .WhereElementIsNotElementType()
                .OfClass(DB.FamilyInstance))


def _visible_floors():
    return list(DB.FilteredElementCollector(doc, view.Id)
                .OfCategory(DB.BuiltInCategory.OST_Floors)
                .WhereElementIsNotElementType()
                .OfClass(DB.Floor))


def _visible_foundations():
    return list(DB.FilteredElementCollector(doc, view.Id)
                .OfCategory(DB.BuiltInCategory.OST_StructuralFoundation)
                .WhereElementIsNotElementType())


def _visible_grids():
    return list(DB.FilteredElementCollector(doc, view.Id).OfClass(DB.Grid))


def _visible_roofs():
    return list(DB.FilteredElementCollector(doc, view.Id)
                .OfCategory(DB.BuiltInCategory.OST_Roofs)
                .WhereElementIsNotElementType()
                .OfClass(DB.RoofBase))


def _visible_walls():
    return list(DB.FilteredElementCollector(doc, view.Id)
                .OfCategory(DB.BuiltInCategory.OST_Walls)
                .WhereElementIsNotElementType()
                .OfClass(DB.Wall))


def _is_column(member):
    return member.Category.Id == DB.ElementId(DB.BuiltInCategory.OST_StructuralColumns)


def _is_wood(member):
    try:
        return member.StructuralMaterialType == DB.Structure.StructuralMaterialType.Wood
    except Exception:
        return False


def _member_axis(member):
    """Return the member's axis endpoints, or None for unsupported locations."""
    location = member.Location
    if isinstance(location, DB.LocationCurve):
        curve = location.Curve
        if not isinstance(curve, DB.Line):
            return None
        return _xyz(curve.GetEndPoint(0)), _xyz(curve.GetEndPoint(1))
    if isinstance(location, DB.LocationPoint):
        point = _xyz(location.Point)
        return point, (point[0], point[1], point[2] + 1.0)
    return None


def _depth_direction(member):
    """Return the member's section-depth direction in model coordinates.

    Framing depth is the instance Z axis; a column's depth is taken as its
    Y axis. Both are assumptions to confirm in live testing.
    """
    transform = member.GetTransform()
    return _xyz(transform.BasisY if _is_column(member) else transform.BasisZ)


def _solids(element):
    options = DB.Options()
    options.DetailLevel = DB.ViewDetailLevel.Fine
    pending = list(element.get_Geometry(options) or [])
    while pending:
        item = pending.pop()
        if isinstance(item, DB.Solid) and item.Volume > 0:
            yield item
        elif isinstance(item, DB.GeometryInstance):
            pending.extend(item.GetInstanceGeometry())


def _edge_points(edges, frame):
    points = []
    for edge in edges:
        for point in edge.Tessellate():
            points.append(frame.to_view(point))
    return points


def _cut_faces(element, frame, transform=None):
    """Yield the element's faces on the section plane.

    ``transform`` places a linked element in host coordinates.
    """
    plane = frame.plane
    for solid in _solids(element):
        try:
            if transform is not None:
                solid = DB.SolidUtils.CreateTransformed(solid, transform)
            piece = DB.BooleanOperationsUtils.CutWithHalfSpace(solid, plane)
        except Exception:
            continue
        if piece is None:
            continue
        for face in piece.Faces:
            if not isinstance(face, DB.PlanarFace):
                continue
            if abs(face.FaceNormal.DotProduct(plane.Normal)) < 1 - FACE_TOLERANCE:
                continue
            if abs((face.Origin - plane.Origin).DotProduct(plane.Normal)) > FACE_TOLERANCE:
                continue
            yield face


def _cut_outline(element, frame):
    """Return view-plane points of the element's cut face on the section plane."""
    points = []
    for face in _cut_faces(element, frame):
        for loop in face.EdgeLoops:
            points.extend(_edge_points(loop, frame))
    return points


def _cut_regions(element, frame, transform=None):
    """Return one region of ordered view-plane loops per cut face."""
    regions = []
    for face in _cut_faces(element, frame, transform):
        loops = []
        for loop in face.EdgeLoops:
            points = []
            for edge in loop:
                curve = edge.AsCurveFollowingFace(face)
                points.extend(frame.to_view(point) for point in list(curve.Tessellate())[:-1])
            if len(points) >= 3:
                loops.append(points)
        if loops:
            regions.append(loops)
    return regions


def _projected_outline(element, frame):
    """Return view-plane points of the element's whole outline."""
    points = []
    for solid in _solids(element):
        points.extend(_edge_points(solid.Edges, frame))
    return points


def _member_size(member, direction, depth):
    """Return the member's ``(depth, width)`` in feet, square to its axis."""
    points = []
    for solid in _solids(member):
        for edge in solid.Edges:
            points.extend(_xyz(point) for point in edge.Tessellate())
    return member_size(points, direction, depth)


def _wood_target(outline, size, axis_2d, status, show_width):
    """Return the modeled ``(seen depth, width, seen_width)`` in inches.

    End-on and oblique members use the member's own size; a member seen
    from its side gives only the depth across its length (its width when
    seen on its flat).
    """
    if status == ALONG:
        axis = unit_2d(axis_2d)
        low, high = extent_along(outline, (-axis[1], axis[0]))
        return round((high - low) * 12.0, 3), None, show_width
    depth, width = size
    return round(depth * 12.0, 3), round(width * 12.0, 3), False


def _target_text(spec):
    if spec['kind'] != WOOD:
        return spec['target']
    depth, width, _ = spec['target']
    if width is None:
        return '{} {} deep'.format(spec['material'], format_inches(depth))
    return '{} {}x{}'.format(spec['material'], format_inches(width), format_inches(depth))


def _survey(members, frame):
    """Classify members into placement jobs and skip records."""
    jobs = []
    skipped = []
    for member in members:
        symbol = member.Symbol
        type_name = _type_name(symbol)
        axis = _member_axis(member)
        if axis is None:
            skipped.append((member, type_name, 'Curved or unsupported location'))
            continue
        direction = tuple(b - a for a, b in zip(axis[0], axis[1]))
        kind = classify_member(direction, frame.direction)
        cut = crosses_plane(axis[0], axis[1], frame.origin, frame.direction)
        if kind == OBLIQUE and not cut:
            skipped.append((member, type_name, 'Oblique to the section and not cut'))
            continue
        depth = _depth_direction(member)
        show_width = abs(sum(a * b for a, b in zip(depth, frame.direction))) > SHOW_WIDTH_ALIGNMENT
        view_kind = VIEW_SIDE if kind == IN_PLANE else VIEW_SECTION
        spec = member_spec(type_name, symbol.FamilyName, view_kind, show_width,
                           wood=_is_wood(member))
        if spec is None:
            skipped.append((member, type_name, 'Not a supported steel or wood type'))
            continue

        if kind == IN_PLANE:
            status, outline = ALONG, _projected_outline(member, frame)
        elif cut:
            status, outline = CUT, _cut_outline(member, frame)
        else:
            status, outline = BEYOND, _projected_outline(member, frame)
        if not outline:
            skipped.append((member, type_name, 'Could not read the member outline'))
            continue
        size = None if kind == IN_PLANE else _member_size(member, direction, depth)
        if kind != IN_PLANE and size is None:
            skipped.append((member, type_name, 'Could not read the member size'))
            continue
        axis_2d = frame.in_view(direction)
        if spec['kind'] == WOOD:
            spec['target'] = _wood_target(outline, size, axis_2d, status, show_width)
        jobs.append({
            'member': member,
            'type_name': type_name,
            'spec': spec,
            'status': status,
            'outline': outline,
            'axis_2d': axis_2d,
            'depth': depth,
            'size': size,
        })
    return jobs, skipped


def _type_layers(element_type):
    """Return ``(material name, thickness, is_structure)`` for each layer.

    Floor layers run top down; wall layers run from the exterior in.
    """
    layers = []
    try:
        structure = element_type.GetCompoundStructure()
        for layer in structure.GetLayers() if structure else []:
            material = doc.GetElement(layer.MaterialId)
            layers.append((material.Name if material is not None else '', layer.Width,
                           layer.Function == DB.MaterialFunctionAssignment.Structure))
    except Exception:
        pass
    return layers


def _floor_layers(floor):
    """Return ``(material name, thickness)`` for each layer, top down."""
    return [layer[:2] for layer in _type_layers(floor.FloorType)]


def _survey_floors(floors, frame):
    """Return cut floor outlines, visible floor tops, and sheathing lines."""
    outlines = []
    tops = []
    sheathing = []
    for floor in floors:
        outline = _cut_outline(floor, frame)
        if not outline:
            continue
        outlines.append(outline)
        type_name = _type_name(floor.FloorType)
        layers = _floor_layers(floor)
        top = visible_top(outline, floor_label(type_name, [name for name, _ in layers]),
                          frame.trim)
        if top:
            tops.append(top)
        layer = sheathing_layer(type_name, layers)
        if layer:
            below, thickness = layer
            v = max(point[1] for point in outline) - below - thickness / 2.0
            us = [point[0] for point in outline]
            segment = clip_segment((min(us), v), (max(us), v), frame.trim)
            if segment:
                sheathing.append((segment, thickness))
    return outlines, unique_tops(tops, FLOOR_TOP_TOLERANCE), sheathing


def _survey_roofs(roofs, frame):
    """Return ``(segment, thickness)`` sheathing lines for cut roofs.

    The sheathing follows each up-facing edge of the cut face, sloped or
    flat, set down square to it by the layers above the sheathing.
    """
    sheathing = []
    for roof in roofs:
        roof_type = doc.GetElement(roof.GetTypeId())
        layer = sheathing_layer(_type_name(roof_type),
                                [layer[:2] for layer in _type_layers(roof_type)])
        if layer is None:
            continue
        below, thickness = layer
        for loops in _cut_regions(roof, frame):
            outer = max(loops, key=lambda loop: abs(signed_area(loop)))
            for edge in join_collinear(top_edges(outer)):
                if edge[0][0] > edge[1][0]:
                    edge = (edge[1], edge[0])
                edge = offset_down(edge, below + thickness / 2.0)
                segment = edge and clip_segment(edge[0], edge[1], frame.trim)
                if segment:
                    sheathing.append((segment, thickness))
    return sheathing


def _clipped_region(loops, frame):
    """Return the region's loops clipped to the crop, without loops left empty."""
    return [loop for loop in (clip_polygon(loop, frame.trim) for loop in loops) if loop]


def _survey_concrete(foundations, walls, frame):
    """Return clipped cut regions of footings and concrete walls, and footing outlines."""
    regions = []
    footings = []
    for foundation in foundations:
        for loops in _cut_regions(foundation, frame):
            footings.append([point for loop in loops for point in loop])
            regions.append(_clipped_region(loops, frame))
    for wall in walls:
        wall_type = wall.WallType
        if wall_type.Kind != DB.WallKind.Basic \
                or not is_concrete(_type_name(wall_type), _type_layers(wall_type)):
            continue
        for loops in _cut_regions(wall, frame):
            regions.append(_clipped_region(loops, frame))
    return [region for region in regions if region], footings


def _soil_lines(footings, frame):
    """Return view-plane segments along the bottom of the lowest footings."""
    lines = []
    for low, high, bottom in lowest_bottoms(footings, FLOOR_TOP_TOLERANCE):
        segment = clip_segment((low, bottom), (high, bottom), frame.trim)
        if segment:
            lines.append(segment)
    return lines


def _grid_positions(grids, frame):
    """Return ``(u, label)`` where straight grids cross the section plane in the crop."""
    positions = []
    for grid in grids:
        curve = grid.Curve
        if not isinstance(curve, DB.Line):
            continue
        point = line_plane_point(_xyz(curve.GetEndPoint(0)), _xyz(curve.GetEndPoint(1)),
                                 frame.origin, frame.direction)
        if point is None:
            continue
        u = to_view(point, frame.origin, frame.right, frame.up)[0]
        if frame.trim is None or frame.trim[0] <= u <= frame.trim[2]:
            positions.append((u, grid.Name))
    return positions


def _plate_spec(stud_width):
    """Return the wood spec for a 2x plate laid flat across ``stud_width`` feet."""
    return {
        'kind': WOOD,
        'target': (round(stud_width * 12.0, 3), round(PLATE_THICKNESS * 12.0, 3), False),
        'bases': wood_family_bases('Sawn', VIEW_SECTION)[:1],
        'folder': WOOD_FOLDER,
        'material': 'Sawn',
    }


def _survey_walls(walls, frame):
    """Return plate jobs for wood walls cut square by the section.

    Each job holds the view-plane centers of the wall's double top plate
    and single bottom plate, centered on the stud layer.
    """
    jobs = []
    skipped = []
    for wall in walls:
        wall_type = wall.WallType
        if wall_type.Kind != DB.WallKind.Basic:
            continue
        type_name = _type_name(wall_type)
        layer = stud_layer(type_name, _type_layers(wall_type))
        if layer is None:
            continue
        location = wall.Location
        curve = location.Curve if isinstance(location, DB.LocationCurve) else None
        if not isinstance(curve, DB.Line):
            skipped.append((wall, type_name, 'Curved wall; no plates'))
            continue
        start, end = _xyz(curve.GetEndPoint(0)), _xyz(curve.GetEndPoint(1))
        direction = tuple(b - a for a, b in zip(start, end))
        if classify_member(direction, frame.direction) != END_ON \
                or not crosses_plane(start, end, frame.origin, frame.direction):
            continue
        outline = _cut_outline(wall, frame)
        if not outline:
            continue
        offset, thickness = layer
        sign = 1.0 if frame.in_view(_xyz(wall.Orientation))[0] >= 0 else -1.0
        us = [point[0] for point in outline]
        exterior = max(us) if sign > 0 else min(us)
        u = exterior - sign * (offset + thickness / 2.0)
        vs = [point[1] for point in outline]
        centers = plate_centers(min(vs), max(vs), u, frame.trim)
        if not centers:
            continue
        jobs.append({
            'member': wall,
            'type_name': type_name,
            'spec': _plate_spec(thickness),
            'status': PLATE,
            'centers': centers,
        })
    return jobs, skipped


def _steel_tops(jobs, frame):
    """Return one top-of-steel elevation per height, for steel cut or along."""
    tops = [visible_top(job['outline'], STEEL_LABEL, frame.trim) for job in jobs
            if job['spec']['kind'] == STEEL and job['status'] in (CUT, ALONG)]
    return unique_tops([top for top in tops if top], FLOOR_TOP_TOLERANCE)


def _break_crossings(jobs, floor_outlines, frame):
    crossings = []
    for job in jobs:
        if job['status'] == ALONG:
            crossings.extend(crop_crossings(job['outline'], job['axis_2d'], frame.trim))
    for outline in floor_outlines:
        crossings.extend(crop_crossings(outline, (1.0, 0.0), frame.trim))
    return merge_crossings(crossings, BREAK_MERGE_TOLERANCE)


# Linked architectural model

def _link_label(link):
    return '{}  [{}]'.format(link.Name, link.Id.IntegerValue)


def _outline_links():
    """Return the visible loaded links to outline, asking when there are several."""
    links = [link for link in DB.FilteredElementCollector(doc, view.Id)
             .OfClass(DB.RevitLinkInstance)
             if link.GetLinkDocument() is not None]
    if len(links) <= 1:
        return links
    labels = dict((_link_label(link), link) for link in links)
    picked = forms.SelectFromList.show(
        sorted(labels), title='Linked models to outline', multiselect=True,
        button_name='Outline')
    return [labels[label] for label in picked or []]


def _link_filter(transform, frame):
    """Return a filter for linked elements near the cut plane inside the crop."""
    if frame.crop is None:
        return None
    inverse = transform.Inverse
    points = []
    for u in (frame.crop[0], frame.crop[2]):
        for v in (frame.crop[1], frame.crop[3]):
            for depth in (-LINK_SEARCH_DEPTH, LINK_SEARCH_DEPTH):
                points.append(inverse.OfPoint(
                    frame.to_model((u, v)) + view.ViewDirection * depth))
    low = DB.XYZ(min(p.X for p in points), min(p.Y for p in points), min(p.Z for p in points))
    high = DB.XYZ(max(p.X for p in points), max(p.Y for p in points), max(p.Z for p in points))
    return DB.BoundingBoxIntersectsFilter(DB.Outline(low, high))


def _link_regions(link, frame):
    """Return the cut regions of a linked model's elements on the section plane."""
    transform = link.GetTotalTransform()
    collector = DB.FilteredElementCollector(link.GetLinkDocument()).WhereElementIsNotElementType()
    box_filter = _link_filter(transform, frame)
    if box_filter is not None:
        collector = collector.WherePasses(box_filter)
    regions = []
    for element in collector:
        category = element.Category
        if category is None or category.CategoryType != DB.CategoryType.Model:
            continue
        regions.extend(_cut_regions(element, frame, transform))
    return regions


def _outline_style():
    """Return the outline line style, asking when S-OBJ4 is not in the project."""
    lines = doc.Settings.Categories.get_Item(DB.BuiltInCategory.OST_Lines)
    styles = dict((category.Name, category) for category in lines.SubCategories)
    name = OUTLINE_STYLE if OUTLINE_STYLE in styles else forms.SelectFromList.show(
        sorted(styles), title='{} not found: line style for the outline'.format(OUTLINE_STYLE),
        button_name='Use style')
    if not name:
        return None
    return styles[name].GetGraphicsStyle(DB.GraphicsStyleType.Projection)


# Matching and loading

def _spec_key(spec):
    return spec['kind'], tuple(spec['bases']), spec['target']


def _loaded_symbols(category):
    return list(DB.FilteredElementCollector(doc)
                .OfClass(DB.FamilySymbol)
                .OfCategory(category))


def _loaded_detail_types():
    return dict(((symbol.FamilyName, _type_name(symbol)), symbol)
                for symbol in _loaded_symbols(DB.BuiltInCategory.OST_DetailComponents))


def _find_symbol(category, family_test, type_name):
    """Return the named type of a matching family, else its first type."""
    symbols = [symbol for symbol in _loaded_symbols(category) if family_test(symbol.FamilyName)]
    for symbol in symbols:
        if (_type_name(symbol) or '').lower() == type_name.lower():
            return symbol
    return symbols[0] if symbols else None


def _break_symbol():
    return _find_symbol(DB.BuiltInCategory.OST_DetailComponents,
                        lambda name: family_matches_base(name, BREAK_FAMILY), BREAK_TYPE)


def _elevation_symbol():
    return _find_symbol(DB.BuiltInCategory.OST_GenericAnnotation,
                        lambda name: name.lower().startswith(ELEVATION_FAMILY.lower()),
                        ELEVATION_TYPE)


def _soil_symbol():
    return _find_symbol(DB.BuiltInCategory.OST_DetailComponents,
                        lambda name: family_matches_base(name, SOIL_FAMILY), SOIL_TYPE)


def _grid_symbol():
    return _find_symbol(DB.BuiltInCategory.OST_DetailComponents,
                        lambda name: family_matches_base(name, GRID_FAMILY), GRID_TYPE)


def _concrete_region_type():
    """Return the concrete filled region type, asking when none is named concrete."""
    types = list(DB.FilteredElementCollector(doc).OfClass(DB.FilledRegionType))
    named = dict((DB.Element.Name.GetValue(item), item) for item in types)
    for name in sorted(named, key=len):
        if CONCRETE_REGION.lower() in name.lower():
            return named[name]
    if not named:
        return None
    picked = forms.SelectFromList.show(
        sorted(named), title='No "{}" filled region type; pick one for concrete'.format(
            CONCRETE_REGION), button_name='Use type')
    return named.get(picked) if picked else None


def _sheathing_symbol(thickness):
    """Return the sheathing type named for ``thickness`` (feet), else the first."""
    symbols = [symbol for symbol in _loaded_symbols(DB.BuiltInCategory.OST_DetailComponents)
               if family_matches_base(symbol.FamilyName, SHEATHING_FAMILY)]
    text = format_inches(thickness * 12.0)
    for symbol in symbols:
        if text in (_type_name(symbol) or ''):
            return symbol
    return symbols[0] if symbols else None


def _symbol_size(symbol):
    """Return a wood type's ``(width, depth)`` in inches, else None."""
    values = []
    for name in ('Width', 'Depth'):
        parameter = symbol.LookupParameter(name)
        if parameter is None or parameter.StorageType != DB.StorageType.Double:
            return None
        values.append(parameter.AsDouble() * 12.0)
    return tuple(values)


def _rank(spec, loaded):
    return rank_candidates(spec['target'], loaded.keys(), bases=spec['bases'],
                           key=match_key(spec['kind']))


class Library(object):
    """Reads KLAA library folders and wood catalogs once per run."""

    def __init__(self):
        self._listings = {}
        self._sizes = {}

    def files(self, folder):
        if folder not in self._listings:
            path = os.path.join(LIBRARY_ROOT, folder)
            self._listings[folder] = os.listdir(path) if os.path.isdir(path) else None
        return self._listings[folder]

    def source(self, spec):
        """Return ``(rfa_path, catalog_type)`` for a steel spec, else a reason."""
        folder = os.path.join(LIBRARY_ROOT, spec['folder'])
        filenames = self.files(spec['folder'])
        if filenames is None:
            return None, 'KLAA library not reachable: {}'.format(folder)
        for base in spec['bases']:
            filename = pick_library_file(filenames, base)
            if filename is None:
                continue
            path = os.path.join(folder, filename)
            catalog = os.path.splitext(path)[0] + '.txt'
            if not os.path.isfile(catalog):
                continue
            names = parse_type_catalog(File.ReadAllText(catalog))
            type_name = find_catalog_type(names, spec['target'], key=match_key(spec['kind']))
            if type_name:
                return (path, type_name), None
        return None, '{} not found in {}'.format(spec['target'], ', '.join(spec['bases']))

    def catalog_sizes(self, folder, base):
        """Return ``(rfa_path, [(name, width, depth)])`` for a wood family."""
        if (folder, base) not in self._sizes:
            filename = pick_library_file(self.files(folder) or [], base)
            path = filename and os.path.join(LIBRARY_ROOT, folder, filename)
            catalog = path and os.path.splitext(path)[0] + '.txt'
            sizes = []
            if catalog and os.path.isfile(catalog):
                sizes = parse_catalog_sizes(File.ReadAllText(catalog))
            self._sizes[(folder, base)] = (path, sizes)
        return self._sizes[(folder, base)]

    def family_path(self, base, folder=''):
        """Return the newest library family for ``base`` in ``folder``, else None."""
        filenames = self.files(folder)
        filename = filenames and pick_library_file(filenames, base)
        return os.path.join(LIBRARY_ROOT, folder, filename) if filename else None


def _wood_pick(spec, loaded, library):
    """Return ``(base, type_name, plies, rfa_path)`` for a wood spec, else None.

    Loaded types and the library catalog of each family compete on size;
    ``rfa_path`` is None when the chosen type is already loaded.
    """
    depth, width, seen_width = spec['target']
    for base in spec['bases']:
        symbols = dict((type_name, symbol) for (family, type_name), symbol in loaded.items()
                       if family_matches_base(family, base))
        sizes = []
        for type_name, symbol in symbols.items():
            size = _symbol_size(symbol)
            if size:
                sizes.append((type_name,) + size)
        path, catalog = library.catalog_sizes(spec['folder'], base)
        sizes.extend(size for size in catalog if size[0] not in symbols)
        pick = choose_wood_stack(sizes, depth, width, spec['material'], seen_width)
        if pick:
            type_name, plies = pick
            return base, type_name, plies, None if type_name in symbols else path
    return None


def _wood_symbol(base, type_name, loaded):
    for (family, name), symbol in loaded.items():
        if name == type_name and family_matches_base(family, base):
            return symbol
    return None


def _choose(target, choices):
    labels = ['{} : {}'.format(family, type_name) for family, type_name in choices]
    picked = forms.CommandSwitchWindow.show(
        labels, message='Detail component for {}'.format(target))
    if picked is None:
        return None
    return choices[labels.index(picked)]


def _resolve_types(specs, families):
    """Load what is missing, then return spec key -> (FamilySymbol, plies) and reasons.

    ``families`` are whole families (break line, elevation symbol, sheathing)
    to load when absent, as ``(label, path)`` pairs; they share the one load
    prompt.
    """
    loaded = _loaded_detail_types()
    library = Library()
    reasons = {}
    sources = {}
    wood = {}
    ordered = sorted(specs.items(), key=lambda item: str(item[0]))
    for key, spec in ordered:
        if spec['kind'] == WOOD:
            pick = _wood_pick(spec, loaded, library)
            if pick is None:
                reasons[key] = 'No {} type in {}'.format(_target_text(spec),
                                                         ', '.join(spec['bases']))
                continue
            wood[key] = pick
            if pick[3]:
                sources[key] = (pick[3], pick[1])
            continue
        if _rank(spec, loaded):
            continue
        source, reason = library.source(spec)
        if source:
            sources[key] = source
        else:
            reasons[key] = reason

    families = [(label, path) for label, path in families if path and os.path.isfile(path)]
    if sources or families:
        names = sorted(set('{}  ({})'.format(type_name, os.path.basename(path))
                           for path, type_name in sources.values()))
        names.extend(label for label, _ in families)
        message = 'Load {} item(s) from the KLAA library?\n\n{}'.format(
            len(names), '\n'.join(names))
        if forms.alert(message, title=COMMAND_TITLE, yes=True, no=True):
            with revit.Transaction('Section Detailer: load from library', doc=doc):
                for path, type_name in sorted(set(sources.values())):
                    doc.LoadFamilySymbol(path, type_name)
                for _, path in families:
                    doc.LoadFamily(path)
            loaded = _loaded_detail_types()
        else:
            for key in sources:
                reasons[key] = 'Not loaded (declined)'

    chosen = {}
    for key, spec in ordered:
        if key in reasons:
            continue
        if key in wood:
            base, type_name, plies, _ = wood[key]
            symbol = _wood_symbol(base, type_name, loaded)
            if symbol is None:
                reasons[key] = 'Library load did not add {}'.format(type_name)
            else:
                chosen[key] = (symbol, plies)
            continue
        choices = best_per_family(_rank(spec, loaded))
        if not choices:
            reasons[key] = 'Library load did not add the type'
            continue
        pick = choices[0] if len(choices) == 1 else _choose(spec['target'], choices)
        if pick is None:
            reasons[key] = 'Skipped at type choice'
        else:
            chosen[key] = (loaded[pick], 1)
    return chosen, reasons


# Placement

def _activate(symbol):
    if not symbol.IsActive:
        symbol.Activate()
        doc.Regenerate()


def _finish(instance):
    _set_comments(instance, OVERLAY_MARKER)
    return instance


def _rotate(instance, point, angle):
    if angle:
        axis = DB.Line.CreateBound(point, point + view.ViewDirection)
        DB.ElementTransformUtils.RotateElement(doc, instance.Id, axis, angle)


def _view_bounds(instance, frame):
    """Return the instance's bounding box corners as view-plane points, else None."""
    doc.Regenerate()
    box = instance.get_BoundingBox(view)
    if box is None:
        return None
    return [frame.to_view(DB.XYZ(x, y, z))
            for x in (box.Min.X, box.Max.X)
            for y in (box.Min.Y, box.Max.Y)
            for z in (box.Min.Z, box.Max.Z)]


def _is_invisible(item):
    style = doc.GetElement(item.GraphicsStyleId)
    return style is not None and 'invisible' in style.Name.lower()


def _drawn_points(instance, frame):
    """Return view-plane points of the instance's visible lines and solids.

    The bounding box also counts invisible lines and other hidden content,
    which pushed off-center families such as HSS off target.
    """
    doc.Regenerate()
    options = DB.Options()
    options.View = view
    points = []
    pending = list(instance.get_Geometry(options) or [])
    while pending:
        item = pending.pop()
        if isinstance(item, DB.GeometryInstance):
            pending.extend(item.GetInstanceGeometry())
        elif isinstance(item, DB.Curve) and not _is_invisible(item):
            points.extend(frame.to_view(point) for point in item.Tessellate())
        elif isinstance(item, DB.Solid) and not _is_invisible(item):
            points.extend(_edge_points(item.Edges, frame))
    return points or _view_bounds(instance, frame)


def _move(instance, du, dv, frame):
    if math.hypot(du, dv) > MOVE_TOLERANCE:
        DB.ElementTransformUtils.MoveElement(doc, instance.Id, frame.offset(du, dv))


def _align_center(instance, target, frame, across=None):
    """Move the instance so its drawn center lands on ``target``.

    Families do not all insert at their center (HSS, for one), so placement
    is corrected from the drawn lines. With ``across`` the move is limited
    to that direction, keeping a side component's length where it was.
    """
    points = _drawn_points(instance, frame)
    if not points:
        return
    center = bounds_center(points)
    du, dv = target[0] - center[0], target[1] - center[1]
    if across is not None:
        amount = du * across[0] + dv * across[1]
        du, dv = amount * across[0], amount * across[1]
    _move(instance, du, dv, frame)


def _set_length(instance, names, value):
    for name in names:
        parameter = instance.LookupParameter(name)
        if parameter and parameter.StorageType == DB.StorageType.Double \
                and not parameter.IsReadOnly:
            parameter.Set(value)
            return


def _place_profile(job, symbol, plies, frame):
    """Place section components on an end-on or oblique member, one per wood ply.

    Plies are spaced by the member's own width, so an oblique member's
    stretched cut face does not spread them apart.
    """
    depth_2d = unit_2d(frame.in_view(job['depth'])) or (0.0, 1.0)
    across = width_direction(depth_2d)
    center = bounds_center(job['outline'])
    angle = rotation_in_view(job['depth'], frame.right, frame.up)
    placed = []
    for offset in ply_offsets(plies, job['size'][1] / plies):
        target = (center[0] + across[0] * offset, center[1] + across[1] * offset)
        point = frame.to_model(target)
        instance = doc.Create.NewFamilyInstance(point, symbol, view)
        _rotate(instance, point, angle)
        _align_center(instance, target, frame)
        placed.append(_finish(instance))
    return placed


def _place_plates(job, symbol, frame):
    """Place a 2x section component laid flat at each wall plate center."""
    placed = []
    for target in job['centers']:
        point = frame.to_model(target)
        instance = doc.Create.NewFamilyInstance(point, symbol, view)
        # Turn the family's depth (up) to run across the wall.
        _rotate(instance, point, -math.pi / 2.0)
        _align_center(instance, target, frame)
        placed.append(_finish(instance))
    return placed


def _place_on_segment(symbol, segment, frame, thickness=None):
    """Place a line-like component on a view-plane segment, centered across it."""
    start, end = frame.to_model(segment[0]), frame.to_model(segment[1])
    if start.DistanceTo(end) < doc.Application.ShortCurveTolerance:
        return None
    line = DB.Line.CreateBound(start, end)
    du, dv = segment[1][0] - segment[0][0], segment[1][1] - segment[0][1]
    middle_uv = ((segment[0][0] + segment[1][0]) / 2.0, (segment[0][1] + segment[1][1]) / 2.0)
    across = unit_2d((-dv, du))
    if symbol.Family.FamilyPlacementType == DB.FamilyPlacementType.CurveBasedDetail:
        instance = doc.Create.NewFamilyInstance(line, symbol, view)
    else:
        middle = line.Evaluate(0.5, True)
        instance = doc.Create.NewFamilyInstance(middle, symbol, view)
        _rotate(instance, middle, math.atan2(dv, du))
        _set_length(instance, ('Length',), line.Length)
    if thickness is not None:
        _set_length(instance, SHEATHING_THICKNESS_PARAMETERS, thickness)
    _align_center(instance, middle_uv, frame, across)
    return _finish(instance)


def _place_side(job, symbol, frame):
    """Place a side component along an in-plane member for its visible length."""
    depth_2d = unit_2d(frame.in_view(job['depth']))
    segment = side_segment(job['outline'], job['axis_2d'], depth_2d)
    segment = segment and clip_segment(segment[0], segment[1], frame.trim)
    if not segment:
        return None
    instance = _place_on_segment(symbol, segment, frame)
    return [instance] if instance else None


def _place_sheathing(sheathing, frame, notes):
    placed = []
    missing = False
    for segment, thickness in sheathing:
        symbol = _sheathing_symbol(thickness)
        if symbol is None:
            missing = True
            continue
        _activate(symbol)
        instance = _place_on_segment(symbol, segment, frame, thickness)
        if instance:
            placed.append(instance)
    if missing:
        notes.append('No {} family; floor sheathing was not placed.'.format(SHEATHING_FAMILY))
    return placed


def _place_breaks(crossings, symbol, frame):
    placed = []
    for edge, low, high in crossings:
        start, end = break_segment(edge, low, high, frame.trim, BREAK_MASKS_RIGHT)
        line = DB.Line.CreateBound(frame.to_model(start), frame.to_model(end))
        if symbol.Family.FamilyPlacementType == DB.FamilyPlacementType.CurveBasedDetail:
            placed.append(_finish(doc.Create.NewFamilyInstance(line, symbol, view)))
    return placed


def _set_text(instance, names, text):
    """Set each writable text parameter in ``names``; return the names set."""
    written = []
    for name in names:
        parameter = instance.LookupParameter(name)
        if parameter and parameter.StorageType == DB.StorageType.String \
                and not parameter.IsReadOnly:
            parameter.Set(text)
            written.append(name)
    return written


def _set_label(instance, text):
    """Write the ``T/`` text in the description and blank the elevation.

    Returns the description parameters written; empty when none was found.
    There is no fallback to other text parameters, which once put the
    description in the elevation slot.
    """
    _set_text(instance, ELEVATION_BLANK_PARAMETERS, '')
    return _set_text(instance, ELEVATION_TEXT_PARAMETERS, text)


def _place_elevations(tops, symbol, frame):
    """Place an elevation symbol at each top, outside the break lines.

    With a crop the symbols line up just past its right edge, beyond the
    break lines; without one each starts just past its element's end.
    """
    gap = ELEVATION_GAP * view.Scale
    placed = []
    unlabeled = []
    for top, right, label in tops:
        start = (frame.crop[2] if frame.crop else right) + gap
        instance = doc.Create.NewFamilyInstance(frame.to_model((start, top)), symbol, view)
        if not _set_label(instance, label):
            unlabeled.append(label)
        bounds = _view_bounds(instance, frame)
        if bounds:
            _move(instance, start - min(point[0] for point in bounds), 0.0, frame)
        _set_comments(instance, OVERLAY_MARKER)
        placed.append(instance)
    return placed, unlabeled


def _curve_loop(points):
    """Return a CurveLoop through view-plane points, dropping too-short edges."""
    shortest = doc.Application.ShortCurveTolerance
    corners = []
    for point in points:
        if not corners or corners[-1].DistanceTo(point) >= shortest:
            corners.append(point)
    if len(corners) > 1 and corners[-1].DistanceTo(corners[0]) < shortest:
        corners.pop()
    if len(corners) < 3:
        return None
    loop = DB.CurveLoop()
    for start, end in zip(corners, corners[1:] + corners[:1]):
        loop.Append(DB.Line.CreateBound(start, end))
    return loop


def _place_regions(regions, region_type, frame, notes):
    """Fill each concrete cut region with the filled region type."""
    placed = []
    failed = 0
    for region in regions:
        loops = List[DB.CurveLoop]()
        for loop in region:
            curve_loop = _curve_loop([frame.to_model(point) for point in loop])
            if curve_loop is not None:
                loops.Add(curve_loop)
        if loops.Count == 0:
            continue
        try:
            placed.append(_finish(DB.FilledRegion.Create(doc, region_type.Id, view.Id, loops)))
        except Exception:
            failed += 1
    if failed:
        notes.append('{} concrete region(s) had an invalid outline and were not filled.'.format(
            failed))
    return placed


def _place_soil(lines, symbol, frame):
    """Place soil components just below each lowest footing bottom."""
    parameter = symbol.LookupParameter('Width')
    depth = parameter.AsDouble() if parameter and \
        parameter.StorageType == DB.StorageType.Double else 4.0 / 12.0
    placed = []
    for (u0, v0), (u1, v1) in lines:
        instance = _place_on_segment(symbol, ((u0, v0 - depth / 2.0), (u1, v1 - depth / 2.0)),
                                     frame)
        if instance:
            placed.append(instance)
    return placed


def _place_grids(positions, symbol, frame, notes):
    """Place a vertical grid component at each grid, labeled with its name."""
    placed = []
    unlabeled = []
    low, high = frame.trim[1], frame.trim[3]
    for u, name in positions:
        if symbol.Family.FamilyPlacementType == DB.FamilyPlacementType.CurveBasedDetail:
            line = DB.Line.CreateBound(frame.to_model((u, low)), frame.to_model((u, high)))
            instance = doc.Create.NewFamilyInstance(line, symbol, view)
        else:
            instance = doc.Create.NewFamilyInstance(frame.to_model((u, high)), symbol, view)
        if not any(_set_text(instance, (label,), name) for label in GRID_LABEL_PARAMETERS):
            unlabeled.append(name)
        placed.append(_finish(instance))
    if unlabeled:
        notes.append('Could not find a label parameter on the grid component for: {}.'.format(
            ', '.join(unlabeled)))
    return placed


def _draw_outline(segments, style, frame):
    """Draw halftoned detail lines along the outline, clipped to the crop."""
    overrides = DB.OverrideGraphicSettings()
    overrides.SetHalftone(True)
    placed = []
    for start, end in segments:
        clipped = clip_segment(start, end, frame.crop)
        if not clipped:
            continue
        a, b = frame.to_model(clipped[0]), frame.to_model(clipped[1])
        if a.DistanceTo(b) < doc.Application.ShortCurveTolerance:
            continue
        curve = doc.Create.NewDetailCurve(view, DB.Line.CreateBound(a, b))
        curve.LineStyle = style
        view.SetElementOverrides(curve.Id, overrides)
        placed.append(_finish(curve))
    return placed


def _report(placed, skipped, notes):
    output.print_md('## Section Detailer: {}'.format(view.Name))
    counts = ', '.join('{} {}'.format(len(placed.get(status, [])), label)
                       for status, label in ((CUT, 'cut'), (BEYOND, 'beyond the cut'),
                                             (ALONG, 'along the section'),
                                             (PLATE, 'wall plates'),
                                             ('sheathing', 'sheathing'),
                                             ('concrete', 'concrete regions'),
                                             ('soil', 'soil'),
                                             ('grid', 'grids'),
                                             ('break', 'break lines'),
                                             ('elevation', 'elevation symbols'),
                                             ('outline', 'outline lines')))
    output.print_md('Placed: {}.'.format(counts))
    for note in notes:
        output.print_md('- {}'.format(note))
    if skipped:
        output.print_table(
            [[output.linkify(member.Id), type_name or '-', reason]
             for member, type_name, reason in skipped],
            columns=['Member', 'Type', 'Not placed because'])


def main():
    if not _is_supported_revit_version():
        _stop('Section Detailer requires Revit {} or later.'.format(MINIMUM_REVIT_VERSION))
    if not isinstance(view, DB.ViewSection) or view.IsTemplate:
        _stop('Open a section view first.')

    prior = _prior_overlay()
    replace = False
    if prior:
        choice = forms.CommandSwitchWindow.show(
            ['Replace', 'Add'],
            message='{} Section Detailer item(s) already in this view.'.format(len(prior)))
        if choice is None:
            script.exit()
        replace = choice == 'Replace'

    frame = ViewFrame(view)
    jobs, skipped = _survey(_visible_members(), frame)
    walls = _visible_walls()
    plate_jobs, wall_skipped = _survey_walls(walls, frame)
    skipped.extend(wall_skipped)
    concrete, footings = _survey_concrete(_visible_foundations(), walls, frame)
    soil = _soil_lines(footings, frame)
    grids = _grid_positions(_visible_grids(), frame)
    floor_outlines, floor_tops, sheathing = _survey_floors(_visible_floors(), frame)
    sheathing.extend(_survey_roofs(_visible_roofs(), frame))
    tops = floor_tops + _steel_tops(jobs, frame)
    crossings = _break_crossings(jobs, floor_outlines, frame)
    regions = []
    for link in _outline_links():
        regions.extend(_link_regions(link, frame))
    segments = join_collinear(boundary_segments(regions)) if regions else []
    style = _outline_style() if segments else None
    placed = {}
    notes = []
    if grids and frame.trim is None:
        notes.append('The view has no crop region; grid components were not placed.')
        grids = []
    if not (jobs or plate_jobs or tops or sheathing or segments or concrete or soil or grids):
        _report(placed, skipped, notes)
        return
    if segments and style is None:
        notes.append('No line style chosen; the linked model outline was not drawn.')
    region_type = _concrete_region_type() if concrete else None
    if concrete and region_type is None:
        notes.append('No filled region type chosen; concrete was not filled.')

    families = []
    library = Library()
    if crossings and _break_symbol() is None:
        families.append(('{} family'.format(BREAK_FAMILY), library.family_path(BREAK_FAMILY)))
    if tops and _elevation_symbol() is None:
        families.append((os.path.basename(ELEVATION_PATH), ELEVATION_PATH))
    if sheathing and _sheathing_symbol(0.0) is None:
        families.append(('{} family'.format(SHEATHING_FAMILY),
                         library.family_path(SHEATHING_FAMILY, WOOD_FOLDER)))
    if soil and _soil_symbol() is None:
        families.append(('{} family'.format(SOIL_FAMILY),
                         library.family_path(SOIL_FAMILY, EARTH_FOLDER)))
    if grids and _grid_symbol() is None:
        families.append(('{} family'.format(GRID_FAMILY), library.family_path(GRID_FAMILY)))

    group = DB.TransactionGroup(doc, COMMAND_TITLE)
    group.Start()
    try:
        specs = dict((_spec_key(job['spec']), job['spec']) for job in jobs + plate_jobs)
        chosen, reasons = _resolve_types(specs, families)
        with revit.Transaction('Section Detailer: place components', doc=doc):
            if replace:
                for element in prior:
                    doc.Delete(element.Id)
            for job in jobs + plate_jobs:
                key = _spec_key(job['spec'])
                if key not in chosen:
                    skipped.append((job['member'], job['type_name'],
                                    reasons.get(key, 'No type')))
                    continue
                symbol, plies = chosen[key]
                _activate(symbol)
                if job['status'] == ALONG:
                    instances = _place_side(job, symbol, frame)
                elif job['status'] == PLATE:
                    instances = _place_plates(job, symbol, frame)
                else:
                    instances = _place_profile(job, symbol, plies, frame)
                if not instances:
                    skipped.append((job['member'], job['type_name'], 'Outside the crop region'))
                    continue
                placed.setdefault(job['status'], []).extend(instances)

            if sheathing:
                placed['sheathing'] = _place_sheathing(sheathing, frame, notes)
            if concrete and region_type is not None:
                placed['concrete'] = _place_regions(concrete, region_type, frame, notes)
            if soil:
                symbol = _soil_symbol()
                if symbol is None:
                    notes.append('No {} family; soil was not placed.'.format(SOIL_FAMILY))
                else:
                    _activate(symbol)
                    placed['soil'] = _place_soil(soil, symbol, frame)
            if grids:
                symbol = _grid_symbol()
                if symbol is None:
                    notes.append('No {} family; grids were not placed.'.format(GRID_FAMILY))
                else:
                    _activate(symbol)
                    placed['grid'] = _place_grids(grids, symbol, frame, notes)
            if crossings:
                symbol = _break_symbol()
                if symbol is None:
                    notes.append('No {} family; break lines were not placed.'.format(BREAK_FAMILY))
                else:
                    _activate(symbol)
                    placed['break'] = _place_breaks(crossings, symbol, frame)
            if tops:
                symbol = _elevation_symbol()
                if symbol is None:
                    notes.append('No {} family; elevation symbols were not placed.'.format(
                        ELEVATION_FAMILY))
                else:
                    _activate(symbol)
                    placed['elevation'], unlabeled = _place_elevations(tops, symbol, frame)
                    if unlabeled:
                        notes.append('Could not find a description parameter ({}) for '
                                     'elevation labels: {}.'.format(
                                         ', '.join(ELEVATION_TEXT_PARAMETERS),
                                         ', '.join(sorted(set(unlabeled)))))
            if segments and style is not None:
                placed['outline'] = _draw_outline(segments, style, frame)
        group.Assimilate()
    except Exception:
        if group.HasStarted():
            group.RollBack()
        raise

    _report(placed, skipped, notes)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        forms.alert('Section Detailer failed; no changes were kept.\n\n{}'.format(
            traceback.format_exc()), title=COMMAND_TITLE, warn_icon=True)
