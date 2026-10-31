"""Revit API collection for the ForteWEB Export prototype.

Behaviour
  * STOPS with ExportError (no file written) if anything selected is not a
    Structural Framing member or a Beam System.
  * ForteWEB member name = the beam's Comments parameter (falls back to the
    element Id, with a warning). Notes = Revit Id + type name.
  * A selected beam system exports one joist per distinct length, named from
    the beam system's Comments.
  * Joist SPACING is written only for members in a beam system.
  * Member kind:
      member of a beam system           -> joist
      Structural Usage = Joist          -> joist
      other framing that BEARS ON TOP   -> drop beam
      other framing that FRAMES INTO SIDE / hangers at its face -> flush beam
      nothing framing to it             -> compare top of beam to its level
  * End supports: hanger family -> hanger; framing with beam bottom at/above
    its top -> beam (bearing); other framing -> hanger; column / wall.
  * Clear span = distance between the inside faces of the two supports.
"""

from __future__ import division, print_function

import math

from .fourwf import build_4wf
from .workflow import (
    DEFAULT_HANGER_FAMILY,
    DEFAULT_TOLERANCE_IN,
    beam_kind,
    clear_span_in,
    fmt_ftin,
    median_spacing_in,
    plan_closest,
    structural_system,
    system_member_labels,
)


REPORT_HEADER = ['Name', 'Revit Id', 'Kind', 'Clear span', 'Spacing',
                 'Start support', 'End support', 'How kind was set']


class ExportError(Exception):
    """Raised for user-facing problems (bad selection, nothing exportable)."""


def element_id_value(element_id):
    """Return an ElementId's integer value across Revit 2024+ builds."""
    return element_id.Value if hasattr(element_id, 'Value') else element_id.IntegerValue


def is_exportable(element):
    """True for structural framing members with a location line, or beam systems."""
    from Autodesk.Revit.DB import (BeamSystem, BuiltInCategory, ElementId,
                                   FamilyInstance, LocationCurve)
    if isinstance(element, BeamSystem):
        return True
    return (isinstance(element, FamilyInstance) and element.Category is not None
            and element.Category.Id.Equals(ElementId(BuiltInCategory.OST_StructuralFraming))
            and isinstance(element.Location, LocationCurve))


def run_export(doc, ids, template, out_path, sys_override='auto',
               tol_in=DEFAULT_TOLERANCE_IN, hanger_name=DEFAULT_HANGER_FAMILY):
    """Export the selected element ids. Returns [file path, report rows, warnings]."""
    from Autodesk.Revit.DB import (BeamSystem, BoundingBoxIntersectsFilter,
                                   BuiltInCategory as BIC, BuiltInParameter as BIP,
                                   ElementId, ElementMulticategoryFilter, FamilyInstance,
                                   FilteredElementCollector, LocationCurve, LocationPoint,
                                   Outline, StorageType, Wall, XYZ)
    from Autodesk.Revit.DB.Structure import StructuralInstanceUsage
    from System.Collections.Generic import List

    tol = float(tol_in or DEFAULT_TOLERANCE_IN) / 12.0                 # feet
    hanger_name = hanger_name or DEFAULT_HANGER_FAMILY

    def eid(element):
        return element_id_value(element.Id)

    def is_cat(element, bic):
        return element.Category is not None and element.Category.Id.Equals(ElementId(bic))

    def bbox(element):
        return element.get_BoundingBox(None)

    def type_width_in(element, default=3.5):
        element_type = doc.GetElement(element.GetTypeId())
        for name in ('b', 'bf', 'Width', 'B', 'Beam Width', 'Nominal Width'):
            for source in (element, element_type):
                param = source.LookupParameter(name) if source else None
                if (param and param.HasValue and param.StorageType == StorageType.Double
                        and param.AsDouble() > 0):
                    return param.AsDouble() * 12.0, True
        return default, False

    def comments(element):
        param = element.get_Parameter(BIP.ALL_MODEL_INSTANCE_COMMENTS)
        return param.AsString() if param and param.AsString() else None

    def reference_level(element):
        param = element.get_Parameter(BIP.INSTANCE_REFERENCE_LEVEL_PARAM)
        return doc.GetElement(param.AsElementId()) if param else None

    # ---------- 1. selection + validation
    ids = list(ids)
    if not ids:
        raise ExportError('Nothing selected in Revit. Select structural framing members '
                          'or beam systems, then run the tool again.')
    beams, systems, bad = [], [], []
    for element_id in ids:
        element = doc.GetElement(element_id)
        if isinstance(element, BeamSystem):
            systems.append(element)
        elif is_exportable(element):
            beams.append(element)
        else:
            cat = element.Category.Name if element.Category else type(element).__name__
            bad.append('%s (Id %d)' % (cat, eid(element)))
    if bad:
        raise ExportError('Only Structural Framing members and Beam Systems can be exported. '
                          'Remove these from the selection: ' + ', '.join(bad))

    # ---------- 1b. beam systems -> joist spacing
    def system_spacing_in(beam_system):
        members = [doc.GetElement(i) for i in beam_system.GetBeamIds()]
        members = [m for m in members if m and isinstance(m.Location, LocationCurve)]
        if len(members) >= 2:
            curve = members[0].Location.Curve
            p0, p1 = curve.GetEndPoint(0), curve.GetEndPoint(1)
            length = math.hypot(p1.X - p0.X, p1.Y - p0.Y)
            if length > 1e-9:                  # a vertical first member has no plan normal
                nx, ny = -(p1.Y - p0.Y) / length, (p1.X - p0.X) / length    # plan normal
                offsets = []
                for member in members:
                    mid = member.Location.Curve.Evaluate(0.5, True)
                    offsets.append(mid.X * nx + mid.Y * ny)
                spacing = median_spacing_in(offsets)
                if spacing is not None:
                    return spacing, members
        try:                                   # 0-1 joists: fall back to the layout rule
            return round(beam_system.LayoutRule.Spacing * 12.0, 2), members
        except Exception:
            return None, members

    # every framing member -> (beam system, spacing)
    in_system = {}
    for beam_system in systems:
        spacing, members = system_spacing_in(beam_system)
        for member in members:
            in_system[eid(member)] = (beam_system, spacing)
    for beam in beams:
        if eid(beam) not in in_system:
            beam_system = BeamSystem.BeamBelongsTo(beam)
            if beam_system is not None:
                in_system[eid(beam)] = (beam_system, system_spacing_in(beam_system)[0])

    # a selected beam system exports one joist per distinct length (not every joist)
    picked, seen = [], set(eid(b) for b in beams)
    for beam_system in systems:
        groups = {}
        for member_id in beam_system.GetBeamIds():
            member = doc.GetElement(member_id)
            if (member is None or eid(member) in seen
                    or not isinstance(member.Location, LocationCurve)):
                continue
            seen.add(eid(member))
            groups.setdefault(round(member.Location.Curve.Length * 12.0), []).append(member)
        base = comments(beam_system) or 'Beam System %d' % eid(beam_system)
        for length, label in system_member_labels(base, groups.keys()):
            picked.append((groups[length][0], label, len(groups[length])))
    beams = [(b, None, 1) for b in beams] + picked

    cat_filter = ElementMulticategoryFilter(List[BIC]([
        BIC.OST_StructuralFraming, BIC.OST_StructuralColumns, BIC.OST_Walls]))

    def around(x0, y0, z0, x1, y1, z1):
        outline = Outline(XYZ(min(x0, x1), min(y0, y1), min(z0, z1)),
                          XYZ(max(x0, x1), max(y0, y1), max(z0, z1)))
        return BoundingBoxIntersectsFilter(outline)

    def hanger_near(p, r=0.75):
        """A hanger family whose insertion point is within r (ft, plan) of this beam end."""
        found = (FilteredElementCollector(doc).OfClass(FamilyInstance)
                 .WherePasses(around(p.X - r, p.Y - r, p.Z - 3, p.X + r, p.Y + r, p.Z + 1)))
        for candidate in found:
            if hanger_name.lower() not in (candidate.Symbol.FamilyName or '').lower():
                continue
            if isinstance(candidate.Location, LocationPoint):
                q = candidate.Location.Point
                if math.hypot(q.X - p.X, q.Y - p.Y) <= r:
                    return True
        return False

    def axis_plan(beam):
        curve = beam.Location.Curve
        p0, p1 = curve.GetEndPoint(0), curve.GetEndPoint(1)
        dx, dy = p1.X - p0.X, p1.Y - p0.Y
        length = math.hypot(dx, dy)
        return p0, p1, (dx / length, dy / length) if length else (1.0, 0.0), length

    def parallel(beam_a, beam_b):
        a1 = axis_plan(beam_a)[2]
        a2 = axis_plan(beam_b)[2]
        return abs(a1[0] * a2[0] + a1[1] * a2[1]) > 0.95

    # ---------- 2. support at one end
    def find_support(beam, p, p0, a):
        r = 1.0
        candidates = (FilteredElementCollector(doc).WherePasses(cat_filter)
                      .WhereElementIsNotElementType()
                      .WherePasses(around(p.X - r, p.Y - r, p.Z - 3, p.X + r, p.Y + r, p.Z + 0.5)))
        best = None
        for c in candidates:
            if c.Id.Equals(beam.Id):
                continue
            if is_cat(c, BIC.OST_StructuralColumns) and isinstance(c.Location, LocationPoint):
                q = c.Location.Point
                width, _ = type_width_in(c)
                qx, qy, dist = q.X, q.Y, math.hypot(p.X - q.X, p.Y - q.Y)
                kind = 'column'
            elif isinstance(c, Wall) and isinstance(c.Location, LocationCurve):
                wall_curve = c.Location.Curve
                a0, a1 = wall_curve.GetEndPoint(0), wall_curve.GetEndPoint(1)
                qx, qy, dist = plan_closest(p.X, p.Y, a0.X, a0.Y, a1.X, a1.Y)
                width, kind = c.Width * 12.0, 'wall'
            elif is_cat(c, BIC.OST_StructuralFraming) and isinstance(c.Location, LocationCurve):
                if parallel(beam, c):
                    continue
                framing_curve = c.Location.Curve
                a0, a1 = framing_curve.GetEndPoint(0), framing_curve.GetEndPoint(1)
                qx, qy, dist = plan_closest(p.X, p.Y, a0.X, a0.Y, a1.X, a1.Y)
                width, _ = type_width_in(c)
                on_top = bbox(beam).Min.Z >= bbox(c).Max.Z - tol
                kind = 'beam' if on_top else 'hanger'
            else:
                continue
            if dist > (width / 24.0) + 0.5:          # half width + 6"
                continue
            if best is None or dist < best['dist']:
                s = (qx - p0.X) * a[0] + (qy - p0.Y) * a[1]   # position along beam
                best = {'type': kind, 'width': round(width, 3), 'dist': dist, 's': s * 12.0,
                        'by': '%s %d' % (c.Category.Name, eid(c))}
        if hanger_near(p):
            if best is None:
                best = {'type': 'hanger', 'width': 3.5, 'dist': 0, 'by': 'hanger family',
                        's': ((p.X - p0.X) * a[0] + (p.Y - p0.Y) * a[1]) * 12.0}
            else:
                best['type'] = 'hanger'
        return best

    # ---------- 3. flush or dropped
    def flush_or_drop(beam):
        bb = bbox(beam)
        p0, p1, a, length = axis_plan(beam)
        r = 1.0
        found = (FilteredElementCollector(doc).OfCategory(BIC.OST_StructuralFraming)
                 .WhereElementIsNotElementType()
                 .WherePasses(around(bb.Min.X - r, bb.Min.Y - r, bb.Min.Z - 0.5,
                                     bb.Max.X + r, bb.Max.Y + r, bb.Max.Z + 3)))
        half_w = type_width_in(beam)[0] / 24.0
        top, drop, flush = bb.Max.Z, 0, 0
        for framing in found:
            if (framing.Id.Equals(beam.Id) or not isinstance(framing.Location, LocationCurve)
                    or parallel(beam, framing)):
                continue
            framing_curve = framing.Location.Curve
            for k in (0, 1):
                q = framing_curve.GetEndPoint(k)
                _, _, dist = plan_closest(q.X, q.Y, p0.X, p0.Y, p1.X, p1.Y)
                if dist <= half_w + 0.5:
                    if bbox(framing).Min.Z >= top - tol:
                        drop += 1
                    else:
                        flush += 1
        if drop or flush:
            return beam_kind(drop, flush)
        level = reference_level(beam)
        if level is None:
            return beam_kind(0, 0)
        return beam_kind(0, 0, (level.ProjectElevation - top) * 12.0, level.Name)

    # ---------- 4. build member list
    members, report, warnings = [], [list(REPORT_HEADER)], []
    for beam, label, count in beams:
        bid = eid(beam)
        name = label or comments(beam)
        if not name:
            name = 'Id %d' % bid
            warnings.append("Id %d: Comments is empty - named '%s'" % (bid, name))
        type_name = doc.GetElement(beam.GetTypeId()).get_Parameter(
            BIP.SYMBOL_NAME_PARAM).AsString()

        p0, p1, a, length = axis_plan(beam)
        if abs(p1.Z - p0.Z) > 0.05:
            warnings.append('%s: member is sloped - plan length used, set pitch in ForteWEB' % name)

        level = reference_level(beam)
        system = structural_system(level.Name if level is not None else None, sys_override)

        # ---- joist spacing: ONLY for members that belong to a beam system
        spacing = None
        if bid in in_system:
            beam_system, spacing = in_system[bid]
            member_type, how = 'joist', 'Beam System %d' % eid(beam_system)
            if spacing is None:
                warnings.append('%s: could not read beam system spacing - template spacing kept'
                                % name)
        elif beam.StructuralUsage == StructuralInstanceUsage.Joist:
            member_type, how = 'joist', 'Structural Usage = Joist'
            warnings.append('%s: joist is not in a beam system - template spacing kept' % name)
        else:
            member_type, how = flush_or_drop(beam)          # beams never get a spacing

        sups = []
        for k, p in ((0, p0), (1, p1)):
            support = find_support(beam, p, p0, a)
            if support is None:
                warnings.append('%s: no support found at %s end - template support used, '
                                'bearing at member end' % (name, 'start' if k == 0 else 'end'))
                support = {'type': None, 'width': 3.5, 'by': 'none',
                           's': 0.0 if k == 0 else length * 12.0}
            sups.append(support)

        clear = clear_span_in(sups[0], sups[1])
        if clear <= 0:
            warnings.append('%s: computed clear span <= 0 - check supports' % name)
            continue

        notes = 'Revit Id %d | %s' % (bid, type_name)
        if count > 1:
            notes += ' | %d joists at this length' % count
        members.append({'name': name, 'kind': '%s_%s' % (system, member_type),
                        'span_in': clear, 'notes': notes, 'supports': sups,
                        'spacing_in': spacing})
        report.append([name, bid, '%s %s' % (system, member_type), fmt_ftin(clear),
                       ('%.2f" o.c.' % spacing) if spacing else '-',
                       '%s %.2f" (%s)' % (sups[0]['type'], sups[0]['width'], sups[0]['by']),
                       '%s %.2f" (%s)' % (sups[1]['type'], sups[1]['width'], sups[1]['by']),
                       how])

    if not members:
        raise ExportError('No members could be exported:\n' + '\n'.join(warnings))
    path = build_4wf(template, out_path, members, warnings)
    return [path, report, warnings]
