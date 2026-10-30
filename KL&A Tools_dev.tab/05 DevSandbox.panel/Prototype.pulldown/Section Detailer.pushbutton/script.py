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

from section_detailer.matching import (
    LIBRARY_ROOT,
    VIEW_SECTION,
    VIEW_SIDE,
    WOOD,
    best_per_family,
    find_catalog_type,
    match_key,
    member_spec,
    parse_type_catalog,
    pick_library_file,
    rank_candidates,
)
from section_detailer.view_geometry import (
    END_ON,
    IN_PLANE,
    bounds_center,
    classify_member,
    clip_segment,
    crosses_plane,
    extent_along,
    ply_offsets,
    rotation_in_view,
    side_segment,
    to_view,
    unit_2d,
    width_direction,
)


COMMAND_TITLE = 'Section Detailer'
OVERLAY_MARKER = 'Section Detailer'
MINIMUM_REVIT_VERSION = 2023
MEMBER_CATEGORIES = ('OST_StructuralFraming', 'OST_StructuralColumns')
PLY_PARAMETERS = ('Plies', 'Number of Plies', 'Ply Count')
FACE_TOLERANCE = 1e-4
SHOW_WIDTH_ALIGNMENT = 0.7

CUT = 'cut'
BEYOND = 'beyond'
ALONG = 'along'

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

    def to_view(self, point):
        return to_view(_xyz(point), self.origin, self.right, self.up)

    def in_view(self, vector):
        return (sum(a * b for a, b in zip(vector, self.right)),
                sum(a * b for a, b in zip(vector, self.up)))

    def to_model(self, uv):
        return (view.Origin + view.RightDirection * uv[0] + view.UpDirection * uv[1])


# Collection and geometry

def _prior_overlay():
    collector = (DB.FilteredElementCollector(doc, view.Id)
                 .OfCategory(DB.BuiltInCategory.OST_DetailComponents)
                 .WhereElementIsNotElementType())
    return [element for element in collector if _comments(element) == OVERLAY_MARKER]


def _visible_members():
    categories = List[DB.BuiltInCategory](
        [getattr(DB.BuiltInCategory, name) for name in MEMBER_CATEGORIES])
    return list(DB.FilteredElementCollector(doc, view.Id)
                .WherePasses(DB.ElementMulticategoryFilter(categories))
                .WhereElementIsNotElementType()
                .OfClass(DB.FamilyInstance))


def _is_column(member):
    return member.Category.Id == DB.ElementId(DB.BuiltInCategory.OST_StructuralColumns)


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


def _ply_count(member):
    for element in (member, member.Symbol):
        for name in PLY_PARAMETERS:
            parameter = element.LookupParameter(name)
            if parameter and parameter.StorageType == DB.StorageType.Integer:
                if parameter.AsInteger() > 0:
                    return parameter.AsInteger()
    return None


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


def _cut_outline(element, frame):
    """Return view-plane points of the member's cut face on the section plane."""
    plane = frame.plane
    points = []
    for solid in _solids(element):
        try:
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
            for loop in face.EdgeLoops:
                points.extend(_edge_points(loop, frame))
    return points


def _projected_outline(element, frame):
    """Return view-plane points of the member's whole outline."""
    points = []
    for solid in _solids(element):
        points.extend(_edge_points(solid.Edges, frame))
    return points


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
        if kind not in (END_ON, IN_PLANE):
            skipped.append((member, type_name, 'Oblique to the section'))
            continue
        depth = _depth_direction(member)
        show_width = abs(sum(a * b for a, b in zip(depth, frame.direction))) > SHOW_WIDTH_ALIGNMENT
        view_kind = VIEW_SECTION if kind == END_ON else VIEW_SIDE
        spec = member_spec(type_name, symbol.FamilyName, view_kind, show_width)
        if spec is None:
            skipped.append((member, type_name, 'Not a supported steel or wood type'))
            continue
        if spec['kind'] == WOOD:
            spec['plies'] = _ply_count(member) or spec['plies']

        if kind == IN_PLANE:
            status, outline = ALONG, _projected_outline(member, frame)
        elif crosses_plane(axis[0], axis[1], frame.origin, frame.direction):
            status, outline = CUT, _cut_outline(member, frame)
        else:
            status, outline = BEYOND, _projected_outline(member, frame)
        if not outline:
            skipped.append((member, type_name, 'Could not read the member outline'))
            continue
        jobs.append({
            'member': member,
            'type_name': type_name,
            'spec': spec,
            'status': status,
            'outline': outline,
            'axis_2d': frame.in_view(direction),
            'depth': depth,
        })
    return jobs, skipped


# Matching and loading

def _spec_key(spec):
    return spec['kind'], tuple(spec['bases']), spec['target']


def _loaded_detail_types():
    collector = (DB.FilteredElementCollector(doc)
                 .OfClass(DB.FamilySymbol)
                 .OfCategory(DB.BuiltInCategory.OST_DetailComponents))
    return dict(((symbol.FamilyName, _type_name(symbol)), symbol) for symbol in collector)


def _rank(spec, loaded):
    return rank_candidates(spec['target'], loaded.keys(), bases=spec['bases'],
                           key=match_key(spec['kind']),
                           family_only=spec['kind'] == WOOD)


class Library(object):
    """Reads KLAA library folders once per run."""

    def __init__(self):
        self._listings = {}

    def files(self, folder):
        if folder not in self._listings:
            path = os.path.join(LIBRARY_ROOT, folder)
            self._listings[folder] = os.listdir(path) if os.path.isdir(path) else None
        return self._listings[folder]

    def source(self, spec):
        """Return ``(rfa_path, catalog_type)`` for a spec, else a reason."""
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


def _load_from_library(sources):
    with revit.Transaction('Section Detailer: load detail types', doc=doc):
        for path, type_name in sorted(set(sources.values())):
            doc.LoadFamilySymbol(path, type_name)


def _choose(target, choices):
    labels = ['{} : {}'.format(family, type_name) for family, type_name in choices]
    picked = forms.CommandSwitchWindow.show(
        labels, message='Detail component for {}'.format(target))
    if picked is None:
        return None
    return choices[labels.index(picked)]


def _resolve_types(specs):
    """Return spec key -> FamilySymbol, plus spec key -> skip reason."""
    loaded = _loaded_detail_types()
    library = Library()
    reasons = {}
    sources = {}
    for key, spec in sorted(specs.items()):
        if _rank(spec, loaded):
            continue
        source, reason = library.source(spec)
        if source:
            sources[key] = source
        else:
            reasons[key] = reason

    if sources:
        names = sorted(set('{}  ({})'.format(type_name, os.path.basename(path))
                           for path, type_name in sources.values()))
        message = 'Load {} detail type(s) from the KLAA library?\n\n{}'.format(
            len(names), '\n'.join(names))
        if forms.alert(message, title=COMMAND_TITLE, yes=True, no=True):
            _load_from_library(sources)
            loaded = _loaded_detail_types()
        else:
            for key in sources:
                reasons[key] = 'Not loaded (declined)'

    chosen = {}
    for key, spec in sorted(specs.items()):
        if key in reasons:
            continue
        choices = best_per_family(_rank(spec, loaded))
        if not choices:
            reasons[key] = 'Library load did not add the type'
            continue
        pick = choices[0] if len(choices) == 1 else _choose(spec['target'], choices)
        if pick is None:
            reasons[key] = 'Skipped at type choice'
        else:
            chosen[key] = loaded[pick]
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


def _place_profile(job, symbol, frame):
    """Place section components on an end-on member, one per wood ply."""
    depth_2d = unit_2d(frame.in_view(job['depth'])) or (0.0, 1.0)
    across = width_direction(depth_2d)
    center = bounds_center(job['outline'])
    plies = job['spec']['plies'] if job['spec']['kind'] == WOOD else 1
    low, high = extent_along(job['outline'], across)
    angle = rotation_in_view(job['depth'], frame.right, frame.up)
    placed = []
    for offset in ply_offsets(plies, (high - low) / plies):
        point = frame.to_model((center[0] + across[0] * offset,
                                center[1] + across[1] * offset))
        instance = doc.Create.NewFamilyInstance(point, symbol, view)
        _rotate(instance, point, angle)
        placed.append(_finish(instance))
    return placed


def _place_side(job, symbol, frame):
    """Place a side component along an in-plane member, trimmed to the crop."""
    depth_2d = unit_2d(frame.in_view(job['depth']))
    segment = side_segment(job['outline'], job['axis_2d'], depth_2d)
    segment = segment and clip_segment(segment[0], segment[1], frame.crop)
    if not segment:
        return None
    start, end = frame.to_model(segment[0]), frame.to_model(segment[1])
    if start.DistanceTo(end) < doc.Application.ShortCurveTolerance:
        return None
    line = DB.Line.CreateBound(start, end)
    if symbol.Family.FamilyPlacementType == DB.FamilyPlacementType.CurveBasedDetail:
        return [_finish(doc.Create.NewFamilyInstance(line, symbol, view))]
    middle = line.Evaluate(0.5, True)
    instance = doc.Create.NewFamilyInstance(middle, symbol, view)
    du, dv = segment[1][0] - segment[0][0], segment[1][1] - segment[0][1]
    _rotate(instance, middle, math.atan2(dv, du))
    length = instance.LookupParameter('Length')
    if length and not length.IsReadOnly:
        length.Set(line.Length)
    return [_finish(instance)]


def _report(placed, skipped):
    output.print_md('## Section Detailer: {}'.format(view.Name))
    counts = ', '.join('{} {}'.format(len(placed.get(status, [])), label)
                       for status, label in ((CUT, 'cut'), (BEYOND, 'beyond the cut'),
                                             (ALONG, 'along the section')))
    output.print_md('Placed detail components: {}.'.format(counts))
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
            message='{} Section Detailer component(s) already in this view.'.format(len(prior)))
        if choice is None:
            script.exit()
        replace = choice == 'Replace'

    frame = ViewFrame(view)
    jobs, skipped = _survey(_visible_members(), frame)
    placed = {}
    if not jobs:
        _report(placed, skipped)
        return

    group = DB.TransactionGroup(doc, COMMAND_TITLE)
    group.Start()
    try:
        specs = dict((_spec_key(job['spec']), job['spec']) for job in jobs)
        chosen, reasons = _resolve_types(specs)
        with revit.Transaction('Section Detailer: place components', doc=doc):
            if replace:
                for element in prior:
                    doc.Delete(element.Id)
            for job in jobs:
                key = _spec_key(job['spec'])
                if key not in chosen:
                    skipped.append((job['member'], job['type_name'],
                                    reasons.get(key, 'No type')))
                    continue
                symbol = chosen[key]
                _activate(symbol)
                if job['status'] == ALONG:
                    instances = _place_side(job, symbol, frame)
                else:
                    instances = _place_profile(job, symbol, frame)
                if not instances:
                    skipped.append((job['member'], job['type_name'], 'Outside the crop region'))
                    continue
                placed.setdefault(job['status'], []).extend(instances)
        group.Assimilate()
    except Exception:
        if group.HasStarted():
            group.RollBack()
        raise

    _report(placed, skipped)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        forms.alert('Section Detailer failed; no changes were kept.\n\n{}'.format(
            traceback.format_exc()), title=COMMAND_TITLE, warn_icon=True)
