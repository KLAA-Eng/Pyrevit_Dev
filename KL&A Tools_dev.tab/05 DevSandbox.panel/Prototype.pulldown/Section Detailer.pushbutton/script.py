# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Section\nDetailer"
__version__ = "v0.0"

import os
import traceback

from pyrevit import DB, forms, revit, script
from System.Collections.Generic import List
from System.IO import File

from section_detailer.matching import (
    LIBRARY_ROOT,
    METALS_FOLDER,
    VIEW_SECTION,
    family_base,
    find_catalog_type,
    normalize_designation,
    parse_type_catalog,
    pick_library_file,
    rank_candidates,
    shape_key,
)
from section_detailer.view_geometry import (
    CUT,
    IN_PLANE,
    bounds_center,
    classify_member,
    crosses_plane,
    rotation_in_view,
    to_view,
)


COMMAND_TITLE = 'Section Detailer'
OVERLAY_MARKER = 'Section Detailer'
MINIMUM_REVIT_VERSION = 2024
MEMBER_CATEGORIES = ('OST_StructuralFraming', 'OST_StructuralColumns')
FACE_TOLERANCE = 1e-4

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


# Collection

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


def _cut_profile_center(element, plane):
    """Return the view-plane center of the member's cut face, else None."""
    origin, right, up = _xyz(view.Origin), _xyz(view.RightDirection), _xyz(view.UpDirection)
    normal = plane.Normal
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
            if abs(face.FaceNormal.DotProduct(normal)) < 1 - FACE_TOLERANCE:
                continue
            if abs((face.Origin - plane.Origin).DotProduct(normal)) > FACE_TOLERANCE:
                continue
            for loop in face.EdgeLoops:
                for edge in loop:
                    for point in edge.Tessellate():
                        points.append(to_view(_xyz(point), origin, right, up))
    return bounds_center(points)


# Matching and loading

def _loaded_detail_types():
    collector = (DB.FilteredElementCollector(doc)
                 .OfClass(DB.FamilySymbol)
                 .OfCategory(DB.BuiltInCategory.OST_DetailComponents))
    return dict(((symbol.FamilyName, _type_name(symbol)), symbol) for symbol in collector)


def _library_source(designation):
    """Return ``(rfa_path, catalog_type)`` in the KLAA library, else a reason."""
    base = family_base(shape_key(designation), VIEW_SECTION)
    folder = os.path.join(LIBRARY_ROOT, METALS_FOLDER)
    if not os.path.isdir(folder):
        return None, 'KLAA library not reachable: {}'.format(folder)
    filename = pick_library_file(os.listdir(folder), base)
    if filename is None:
        return None, 'No {} family in the KLAA library'.format(base)
    path = os.path.join(folder, filename)
    catalog = os.path.splitext(path)[0] + '.txt'
    if not os.path.isfile(catalog):
        return None, 'No type catalog beside {}'.format(filename)
    type_name = find_catalog_type(parse_type_catalog(File.ReadAllText(catalog)), designation)
    if type_name is None:
        return None, '{} is not in the {} type catalog'.format(designation, filename)
    return (path, type_name), None


def _load_from_library(sources):
    loaded = []
    with revit.Transaction('Section Detailer: load detail types', doc=doc):
        for designation, (path, type_name) in sorted(sources.items()):
            result = doc.LoadFamilySymbol(path, type_name)
            ok = result[0] if isinstance(result, tuple) else result
            if ok:
                loaded.append(designation)
    return loaded


def _choose(designation, ranked):
    labels = ['{} : {}'.format(family, type_name) for family, type_name in ranked]
    picked = forms.CommandSwitchWindow.show(
        labels, message='Detail component for {}'.format(designation))
    if picked is None:
        return None
    return ranked[labels.index(picked)]


def _resolve_types(designations):
    """Return designation -> FamilySymbol, plus designation -> skip reason."""
    loaded = _loaded_detail_types()
    reasons = {}
    sources = {}
    for designation in designations:
        base = family_base(shape_key(designation), VIEW_SECTION)
        if base is None:
            reasons[designation] = 'Shape not supported yet'
        elif not rank_candidates(designation, loaded.keys(), base=base):
            source, reason = _library_source(designation)
            if source:
                sources[designation] = source
            else:
                reasons[designation] = reason

    if sources:
        message = 'Load {} detail type(s) from the KLAA library?\n\n{}'.format(
            len(sources), '\n'.join(sorted(sources)))
        if forms.alert(message, title=COMMAND_TITLE, yes=True, no=True):
            _load_from_library(sources)
            loaded = _loaded_detail_types()
        else:
            for designation in sources:
                reasons[designation] = 'Not loaded (declined)'

    chosen = {}
    for designation in designations:
        if designation in reasons:
            continue
        base = family_base(shape_key(designation), VIEW_SECTION)
        ranked = rank_candidates(designation, loaded.keys(), base=base)
        if not ranked:
            reasons[designation] = 'Library load did not add the type'
            continue
        pick = ranked[0] if len(ranked) == 1 else _choose(designation, ranked)
        if pick is None:
            reasons[designation] = 'Skipped at type choice'
        else:
            chosen[designation] = loaded[pick]
    return chosen, reasons


# Placement

def _place(symbol, center, depth):
    origin = view.Origin
    point = origin + view.RightDirection * center[0] + view.UpDirection * center[1]
    if not symbol.IsActive:
        symbol.Activate()
        doc.Regenerate()
    instance = doc.Create.NewFamilyInstance(point, symbol, view)
    angle = rotation_in_view(depth, _xyz(view.RightDirection), _xyz(view.UpDirection))
    if angle:
        axis = DB.Line.CreateBound(point, point + view.ViewDirection)
        DB.ElementTransformUtils.RotateElement(doc, instance.Id, axis, angle)
    _set_comments(instance, OVERLAY_MARKER)
    return instance


def _report(placed, skipped):
    output.print_md('## Section Detailer: {}'.format(view.Name))
    output.print_md('Placed **{}** detail component(s).'.format(len(placed)))
    if skipped:
        output.print_table(
            [[output.linkify(member.Id), designation or '-', reason]
             for member, designation, reason in skipped],
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

    plane = DB.Plane.CreateByNormalAndOrigin(view.ViewDirection, view.Origin)
    view_direction = _xyz(view.ViewDirection)
    origin = _xyz(view.Origin)

    targets = []
    skipped = []
    for member in _visible_members():
        designation = normalize_designation(_type_name(member.Symbol))
        axis = _member_axis(member)
        if axis is None:
            skipped.append((member, designation, 'Curved or unsupported location'))
            continue
        direction = tuple(b - a for a, b in zip(axis[0], axis[1]))
        kind = classify_member(direction, view_direction)
        if kind == IN_PLANE:
            skipped.append((member, designation, 'Runs along the section (later phase)'))
            continue
        if kind != CUT:
            skipped.append((member, designation, 'Oblique to the section'))
            continue
        if not crosses_plane(axis[0], axis[1], origin, view_direction):
            skipped.append((member, designation, 'Beyond the cut plane'))
            continue
        targets.append((member, designation))

    if not targets:
        _report([], skipped)
        return

    group = DB.TransactionGroup(doc, COMMAND_TITLE)
    group.Start()
    try:
        chosen, reasons = _resolve_types(sorted(set(d for _, d in targets)))
        placed = []
        with revit.Transaction('Section Detailer: place components', doc=doc):
            if replace:
                for element in prior:
                    doc.Delete(element.Id)
            for member, designation in targets:
                if designation not in chosen:
                    skipped.append((member, designation, reasons.get(designation, 'No type')))
                    continue
                center = _cut_profile_center(member, plane)
                if center is None:
                    skipped.append((member, designation, 'Could not read the cut profile'))
                    continue
                depth = _xyz(member.GetTransform().BasisZ)
                placed.append(_place(chosen[designation], center, depth))
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
