"""Read-only host facts for joins, offsets, work planes and column sections.

The DB namespace is passed explicitly to keep the host boundary mockable.
All returned values are JSON-compatible; no live references escape extraction.
"""


LENGTH_PARAMETERS = (
    'STRUCTURAL_BEAM_END0_ELEVATION', 'STRUCTURAL_BEAM_END1_ELEVATION',
    'Z_OFFSET_VALUE', 'START_Z_OFFSET_VALUE', 'END_Z_OFFSET_VALUE',
    'Y_OFFSET_VALUE', 'START_Y_OFFSET_VALUE', 'END_Y_OFFSET_VALUE',
    'START_JOIN_CUTBACK', 'END_JOIN_CUTBACK', 'START_EXTENSION', 'END_EXTENSION',
)
ENUM_PARAMETERS = ('YZ_JUSTIFICATION', 'Z_JUSTIFICATION',
                   'START_Z_JUSTIFICATION', 'END_Z_JUSTIFICATION')


def identity(element):
    """Return navigation and stable identity for a source or external target."""
    return {'uid': element.UniqueId, 'id': int(element.Id.Value)}


def parameters(element, db):
    """Preserve absent versus failed versus zero-valued beam parameter facts."""
    values = {}
    for key in LENGTH_PARAMETERS + ENUM_PARAMETERS + ('STRUCTURAL_BEND_DIR_ANGLE',):
        try:
            token = getattr(db.BuiltInParameter, key, None)
            parameter = element.get_Parameter(token) if token is not None else None
            if parameter is None or not parameter.HasValue:
                values[key] = {'state': 'Missing'}
            elif key in ENUM_PARAMETERS:
                values[key] = {'state': 'Value', 'value': parameter.AsInteger()}
            else:
                values[key] = {'state': 'Value', 'value': parameter.AsDouble() *
                               (12.0 if key in LENGTH_PARAMETERS else 1.0),
                               'units': 'in' if key in LENGTH_PARAMETERS else 'rad'}
        except Exception as error:
            values[key] = {'state': 'Unavailable', 'reason': str(error)}
    return values


def joins(element, db):
    """Read both indexed end joins; empty lists and failed queries stay distinct."""
    result = {}
    for end in (0, 1):
        facts = {'state': 'Read', 'participants': [], 'allowed': None, 'errors': []}
        try:
            participants = list(element.Location.get_ElementsAtJoin(end))
            facts['raw_participant_ids'] = [int(p.Id.Value) for p in participants]
            unique = dict((p.UniqueId, identity(p)) for p in participants
                          if p.UniqueId != element.UniqueId)
            facts['participants'] = [unique[k] for k in sorted(unique)]
        except Exception as error:
            facts.update(state='Unavailable')
            facts['errors'].append('ElementsAtJoin: {0}'.format(error))
        try:
            facts['allowed'] = bool(db.Structure.StructuralFramingUtils.IsJoinAllowedAtEnd(element, end))
        except Exception as error:
            facts['errors'].append('Join permission: {0}'.format(error))
        try:
            reference = db.Structure.StructuralFramingUtils.GetEndReference(element, end)
            facts['end_reference'] = {'state': 'Read', 'target_id': int(reference.ElementId.Value),
                'reference': reference.ConvertToStableRepresentation(element.Document)}
        except Exception as error:
            facts['end_reference'] = {'state': 'Unavailable', 'reason': str(error)}
        result[str(end)] = facts
    return result


def bottom_attachment(element, db):
    """Resolve an actual referenced floor/roof underside, never coplanarity alone."""
    facts = {'state': 'Unresolved', 'evidence_source': 'FamilyInstance.HostFace'}
    try:
        reference = element.HostFace
        facts['work_plane'] = None
        token = getattr(db.BuiltInParameter, 'SKETCH_PLANE_PARAM', None)
        parameter = element.get_Parameter(token) if token is not None else None
        if parameter is not None and parameter.HasValue:
            try:
                storage = str(parameter.StorageType)
                if storage == 'ElementId':
                    plane_id = parameter.AsElementId()
                    plane = element.Document.GetElement(plane_id)
                    facts['work_plane'] = {'id': int(plane_id.Value),
                                          'name': plane.Name if plane else ''}
                elif storage == 'String':
                    facts['work_plane'] = parameter.AsString()
                else:
                    facts['work_plane'] = parameter.AsValueString()
            except Exception as error:
                facts['work_plane_error'] = str(error)
        if reference is None:
            facts.update(state='No Bottom-face Attachment Found',
                         reason='No underlying host-face reference was returned; '
                                'a work-plane name or matching elevation is not attachment proof.')
            return facts
        linked_id = getattr(reference, 'LinkedElementId', None)
        if linked_id is not None and int(linked_id.Value) >= 0:
            facts['reason'] = 'Linked host-face targets are excluded from this host-model review.'
            return facts
        # HostFace can reference geometry underlying a face-based work plane.
        target = element.Document.GetElement(reference.ElementId)
        if target is None:
            facts['reason'] = 'The work-plane face target could not be resolved.'
            return facts
        facts['host'] = identity(target)
        facts['host']['name'] = target.Name
        facts['reference'] = reference.ConvertToStableRepresentation(element.Document)
        if not isinstance(target, (db.Floor, db.RoofBase)):
            facts.update(state='Other Work Plane', reason='Referenced face belongs to a different host category.')
            return facts
        bottoms = db.HostObjectUtils.GetBottomFaces(target)
        facts['bottom_references'] = [r.ConvertToStableRepresentation(element.Document) for r in bottoms]
        if facts['reference'] not in facts['bottom_references']:
            facts.update(state='Other Work Plane', reason='Referenced floor/roof face is not a bottom face.')
            return facts
        facts.update(state='Floor Bottom Work Plane' if isinstance(target, db.Floor) else
                     'Roof Bottom Work Plane', reason='Beam host/work-plane face reference matches '
                     'a bottom face of the identified floor/roof. Severity policy pending.')
    except Exception as error:
        facts.update(state='Unresolved', reason='Bottom-face reference lookup failed: {0}'.format(error))
    return facts


def column_section(element, faces, db):
    """Recognize actual I-section web planes by paired face spacing and metadata.

    Ambiguous or missing section metadata leaves the face type unresolved rather
    than assuming family-local X/Y have a particular flange/web meaning.
    """
    facts = {'shape': 'Unknown', 'web_planes': [], 'web_normals': []}
    try:
        facts['shape'] = str(element.Symbol.Family.StructuralSectionShape)
        if facts['shape'] not in ('IWideFlange', 'IParallelFlange', 'ISlopedFlange',
                                  'IWelded', 'GeneralI'):
            return facts
        parameter = element.Symbol.get_Parameter(db.BuiltInParameter.STRUCTURAL_SECTION_ISHAPE_WEBTHICKNESS)
        if parameter is None or not parameter.HasValue:
            return facts
        thickness = parameter.AsDouble() * 12.0
        facts['web_thickness'] = thickness
        normals, planes = [], []
        vertical = [face for face in faces if abs(face[0][2]) <= 1e-8]
        for i, a in enumerate(vertical):
            for b in vertical[i + 1:]:
                if abs(sum(a[0][j] * b[0][j] for j in range(3))) < 0.999999:
                    continue
                gap = abs(sum(a[0][j] * (b[1][j] - a[1][j]) for j in range(3)))
                if thickness > 0 and abs(gap - thickness) <= 1e-6:
                    normals.append(a[0])
                    planes.extend([(a[0], a[1]), (b[0], b[1])])
        if normals and all(abs(sum(normals[0][j] * n[j] for j in range(3))) > 0.999999
                           for n in normals):
            facts.update(web_normals=[normals[0]], web_planes=planes)
        else:
            facts['reason'] = 'Web-plane geometry is missing or ambiguous.'
    except Exception as error:
        facts['reason'] = 'Section-face classification unavailable: {0}'.format(error)
    return facts
