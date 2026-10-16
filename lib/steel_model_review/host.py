# -*- coding: utf-8 -*-
"""Read-only Revit extraction boundary for Model Checker.

Geometry is normalized to world-coordinate inch tuples before rule evaluation.
Original family geometry avoids treating connection cutbacks as reference ends.
"""

from pyrevit import DB

from steel_model_review.engine import Cancelled, CHECKS, finding
from steel_model_review.geometry import distance


def id_value(element_id):
    """Return the 64-bit ElementId value used by Revit 2024 and later."""
    return int(element_id.Value)


def name(element):
    """Read a name without relying on engine-specific descriptor helpers.

    Args:
        element: Revit element or None. Derived element types can expose a
            write-only Name property in IronPython.

    Returns:
        The instance Name or type-name parameter, preserving Unicode text.
        None inputs return an empty string.

    Raises:
        AttributeError: Neither a readable Name nor type-name parameter exists.
    """
    if element is None:
        return ''
    try:
        return element.Name or ''
    except AttributeError:
        # Some IronPython contexts expose no GetValue on the base descriptor.
        # The built-in type-name parameter also handles hidden type getters.
        parameter = element.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
        if parameter is not None:
            return parameter.AsString() or ''
        raise


def point(xyz):
    """Convert a Revit XYZ in internal feet to a plain inch tuple."""
    return xyz.X * 12.0, xyz.Y * 12.0, xyz.Z * 12.0


def collect(document, category):
    """Collect all instances of a category, independent of view visibility."""
    return list(DB.FilteredElementCollector(document).OfCategory(category)
                .WhereElementIsNotElementType())


def _record(element, kind):
    level = element.Document.GetElement(element.LevelId)
    symbol = element.Document.GetElement(element.GetTypeId())
    return {'uid': element.UniqueId, 'id': id_value(element.Id),
            'name': '{0}: {1}'.format(id_value(element.Id), name(symbol)),
            'level': name(level), 'type': id_value(element.GetTypeId()),
            'kind': kind, 'version': str(element.VersionGuid)}


def in_scope(element, phase_id, options):
    """Return whether an element exists in the chosen phase and option scope."""
    option = element.DesignOption
    if option is not None and id_value(option.Id) not in options:
        return False
    if element.HasPhases():
        status = element.GetPhaseStatus(phase_id)
        if status not in (DB.ElementOnPhaseStatus.New,
                          DB.ElementOnPhaseStatus.Existing):
            return False
    return True


def classification(element, kind):
    """Return steel/concrete/other/unknown from structural material evidence."""
    if kind != 'wall':
        value = str(element.StructuralMaterialType)
        if value == 'Steel':
            return 'steel'
        if value not in ('Undefined', 'Generic', 'Other', 'Invalid'):
            return 'other'
        return 'unknown'
    compound = element.WallType.GetCompoundStructure()
    if compound is None:
        return 'unknown'
    index = compound.StructuralMaterialIndex
    if index < 0:
        return 'unknown'
    material = element.Document.GetElement(compound.GetMaterialId(index))
    if material is None:
        return 'unknown'
    asset_element = element.Document.GetElement(material.StructuralAssetId)
    if asset_element is None:
        return 'unknown'
    asset = asset_element.GetStructuralAsset()
    return 'concrete' if str(asset.StructuralAssetClass) == 'Concrete' else 'other'


def _solids(geometry):
    """Yield positive-volume solids in already transformed instance geometry."""
    for item in geometry:
        if isinstance(item, DB.Solid) and item.Volume > 1e-9:
            yield item
        elif isinstance(item, DB.GeometryInstance):
            for solid in _solids(item.GetInstanceGeometry()):
                yield solid


def _loops(face):
    """Extract exact straight-edge loops without tessellation error.

    Args:
        face: A planar Revit face in world coordinates.

    Returns:
        Inch-based vertex loops, or None when a boundary is curved/degenerate.
    """
    loops = []
    for loop in face.GetEdgesAsCurveLoops():
        vertices = []
        for curve in loop:
            if not isinstance(curve, DB.Line):
                return None
            vertices.append(point(curve.GetEndPoint(0)))
        if len(vertices) < 3:
            return None
        loops.append(vertices)
    return loops


def _geometry(element, kind):
    """Extract original section evidence without treating cutbacks as endpoints.

    Args:
        element: Revit family instance or concrete wall.
        kind: Normalized member category.

    Returns:
        Planar face records, unique edge vertices, and a single-solid flag.
        Multi-solid geometry retains vertices only for broad-phase extents.
    """
    options = DB.Options()
    options.DetailLevel = DB.ViewDetailLevel.Fine
    options.ComputeReferences = False
    options.IncludeNonVisibleObjects = False
    if kind == 'wall':
        geometry = element.get_Geometry(options)
    else:
        # Original geometry is symbol-local and must be transformed once.
        geometry = element.GetOriginalGeometry(options).GetTransformed(
            element.GetTransform())
    solids = list(_solids(geometry)) if geometry else []
    faces, vertices = [], []
    for solid in solids:
        for edge in solid.Edges:
            curve = edge.AsCurve()
            vertices.extend([point(curve.GetEndPoint(0)),
                             point(curve.GetEndPoint(1))])
        for face in solid.Faces:
            if not isinstance(face, DB.PlanarFace):
                continue
            loops = _loops(face)
            if loops:
                n = face.FaceNormal
                faces.append(((n.X, n.Y, n.Z), point(face.Origin), loops))
    # Multiple disjoint solids could include plates or other nested components.
    # Their combined top envelope does not establish the member section.
    reliable = len(solids) == 1
    return faces if reliable else [], sorted(set(vertices)), reliable


def _wall_sides(element):
    """Resolve finite rectangular wall bearing faces.

    Args:
        element: Concrete wall with accessible side faces.

    Returns:
        Two finite plan segments representing interior and exterior faces.

    Raises:
        ValueError: Faces are nonplanar, nonvertical, opened, or ambiguous.
    """
    segments = []
    for side in (DB.ShellLayerType.Interior, DB.ShellLayerType.Exterior):
        refs = DB.HostObjectUtils.GetSideFaces(element, side)
        for reference in refs:
            face = element.GetGeometryObjectFromReference(reference)
            if not isinstance(face, DB.PlanarFace) or abs(face.FaceNormal.Z) > 1e-8:
                raise ValueError('Wall bearing face is not vertical and planar.')
            loops = _loops(face)
            if not loops or len(loops) != 1:
                raise ValueError('Wall side has curved edges or openings.')
            # A rectangular face has one finite horizontal station interval.
            xy = sorted(set(p[:2] for p in loops[0]))
            if len(xy) != 2:
                raise ValueError('Wall face is not a simple bearing rectangle.')
            segments.append((xy[0], xy[1]))
    if len(segments) != 2:
        raise ValueError('Expected one interior and one exterior bearing face.')
    return segments


def extract(element, kind):
    """Normalize one supported element; reject unreliable reference geometry.

    Args:
        element: A Revit beam, vertical column, wall, or straight grid.
        kind: One of beam, column, wall, or grid.

    Returns:
        A dictionary of scalar identity and inch-based geometry records.

    Raises:
        ValueError: Reference geometry is unsupported or unavailable.
    """
    record = _record(element, kind)
    location = element.Location
    if kind == 'grid':
        curve = element.Curve
    elif isinstance(location, DB.LocationCurve):
        curve = location.Curve
    else:
        curve = None
    if curve is not None:
        if not isinstance(curve, DB.Line) or not curve.IsBound:
            raise ValueError('Only bounded straight reference curves are supported.')
        start, end = point(curve.GetEndPoint(0)), point(curve.GetEndPoint(1))
    elif kind == 'column' and isinstance(location, DB.LocationPoint):
        start = end = point(location.Point)
    else:
        raise ValueError('Reference location is unavailable.')
    if kind == 'grid':
        record.update(start=start, end=end, name=name(element))
        return record
    if kind == 'beam' and distance(start[:2], end[:2]) < 1e-6:
        raise ValueError('Vertical or zero-plan-length beam is unsupported.')
    if kind == 'column' and distance(start[:2], end[:2]) > 1e-6:
        raise ValueError('Sloping column is unsupported.')
    faces, vertices, reliable = _geometry(element, kind)
    box = element.get_BoundingBox(None)
    if box is None:
        raise ValueError('Finite geometry extent is unavailable.')
    # Bounds are broad-phase envelopes; section elevations use planar faces.
    corners = vertices + [point(box.Min), point(box.Max), start, end]
    low = tuple(min(p[i] for p in corners) for i in range(3))
    high = tuple(max(p[i] for p in corners) for i in range(3))
    if vertices:
        # Reference-level Z can differ from the placed member elevation.
        # Keep it in the plan index but do not enlarge physical vertical extent.
        low = low[:2] + (min(p[2] for p in vertices),)
        high = high[:2] + (max(p[2] for p in vertices),)
    if kind == 'column':
        if not reliable or not vertices:
            raise ValueError('Column original-solid extent is unreliable.')
        low = tuple(min(p[i] for p in vertices) for i in range(3))
        high = tuple(max(p[i] for p in vertices) for i in range(3))
        start, end = (start[0], start[1], low[2]), (start[0], start[1], high[2])
    record.update(start=start, end=end, faces=faces,
                  vertices=vertices if reliable else [], bounds=(low, high))
    if kind == 'wall':
        record['sides'] = _wall_sides(element)
    return record


def extract_model(document, elements, phase_id, options, overrides, checks,
                  progress):
    """Extract eligible scope with per-element coverage and failure records.

    Args:
        document: Active project document.
        elements: Sequence of element/kind pairs, collected document-wide.
        phase_id: Confirmed export phase ElementId.
        options: Included numeric option IDs.
        overrides: Type-ID to reviewed material classification mapping.
        checks: Enabled check IDs.
        progress: Callback taking completed and total extraction counts.

    Returns:
        Records, grids, coverage rows, and extraction review findings.

    Raises:
        Cancelled: Progress callback signals cancellation.
    """
    records, grids, coverage, rows = [], [], [], []
    applies = {'beam': ('SMR-01', 'SMR-02', 'SMR-04'),
               'column': ('SMR-03', 'SMR-04'), 'wall': ('SMR-01', 'SMR-02'),
               'grid': ('SMR-03',)}
    for number, (element, kind) in enumerate(elements):
        progress(number, len(elements))
        base = _record(element, kind)
        state, reason = 'Eligible', ''
        try:
            if not in_scope(element, phase_id, options):
                state, reason = 'Excluded', 'Outside chosen phase or option scope.'
            elif kind == 'beam' and str(element.StructuralType) != 'Beam':
                state, reason = 'Excluded', 'Braces and non-beam framing are outside scope.'
            else:
                material = overrides.get(base['type'])
                if kind != 'grid' and material is None:
                    material = classification(element, kind)
                expected = 'concrete' if kind == 'wall' else 'steel'
                if kind != 'grid' and material != expected:
                    state = 'Excluded' if material == 'other' else 'Unsupported'
                    reason = 'Material classification: {0}.'.format(material)
                else:
                    result = extract(element, kind)
                    (grids if kind == 'grid' else records).append(result)
        except ValueError as error:
            state, reason = 'Unsupported', str(error)
        except Exception as error:
            state, reason = 'Failed', '{0}: {1}'.format(type(error).__name__, error)
        if state != 'Eligible':
            for check in applies[kind]:
                if check in checks and state in ('Unsupported', 'Failed'):
                    rows.append(finding(check, base, reason, 'Not evaluated'))
        coverage.append((base['id'], kind, state, reason))
    return records, grids, coverage, rows
