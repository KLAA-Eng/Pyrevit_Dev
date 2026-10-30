"""Break lines, elevation symbols, and sheathing for a detailed section.

Positions are ``(u, v)`` view-plane coordinates in feet, and crop rectangles
are ``(min_u, min_v, max_u, max_v)``, matching ``view_geometry``.
"""

import math
import re


BREAK_FAMILY = '00_Break_Line_Pick'
BREAK_TYPE = 'Break Line small'
ELEVATION_FAMILY = 'Elevation_KLAA'
ELEVATION_TYPE = 'Right Elevation'
ELEVATION_PATH = (r'J:\Standards\910 Revit Support\KLAA Library'
                  r'\KLAA Annotations\Symbols\Elevation_KLAA_17SY.rfa')

# Break lines sit this far inside the crop so their jag is not clipped.
BREAK_INSET = 0.25
# Members within this angle of an edge's normal get a break at that edge.
BREAK_ANGLE = math.radians(15)

LEFT = 'left'
RIGHT = 'right'
BOTTOM = 'bottom'
TOP = 'top'

_OUTWARD = {LEFT: (-1.0, 0.0), RIGHT: (1.0, 0.0), BOTTOM: (0.0, -1.0), TOP: (0.0, 1.0)}

STEEL_LABEL = 'T/STEEL'
SHEATHING_FAMILY = '6_Sheathing_Ply_Section'

# Wall plates: 2x lumber laid flat, a double top plate and a single bottom plate.
PLATE_THICKNESS = 1.5 / 12.0
TOP_PLATES = 2
BOTTOM_PLATES = 1

_SHEATHING = re.compile(r'SHEATH|PLYWOOD|\bPLY\b|OSB|SUBFLOOR')
_STUDS = re.compile(r'STUD|WOOD|LUMBER|TIMBER|\bSPF\b|\bDF\b|DOUGLAS|\bHF\b|\bSYP\b|\b2X\d')
_WOOD_FLOOR = re.compile(r'SHEATH|PLY|OSB|WOOD|SUBFLOOR|T&G|DECKING')
_CONCRETE_FLOOR = re.compile(r'CONC|SLAB|TOPPING|GYP')


def inset_rect(rect, inset=BREAK_INSET):
    """Return the crop rectangle shrunk on every side, or None."""
    if rect is None:
        return None
    return rect[0] + inset, rect[1] + inset, rect[2] - inset, rect[3] - inset


def crop_crossings(outline, axis_2d, rect):
    """Return ``(edge, low, high)`` where a member runs out through ``rect``.

    Only members roughly normal to an edge get a break there: horizontal
    members at the left and right edges, vertical members at the top and
    bottom. ``low``-``high`` is the member's extent along that edge.
    """
    if rect is None or not outline:
        return []
    length = math.hypot(axis_2d[0], axis_2d[1])
    if length == 0:
        return []
    us = [point[0] for point in outline]
    vs = [point[1] for point in outline]
    limit = math.cos(BREAK_ANGLE)
    crossings = []
    if abs(axis_2d[0]) / length >= limit:
        if min(us) < rect[0] < max(us):
            crossings.append((LEFT, min(vs), max(vs)))
        if min(us) < rect[2] < max(us):
            crossings.append((RIGHT, min(vs), max(vs)))
    elif abs(axis_2d[1]) / length >= limit:
        if min(vs) < rect[1] < max(vs):
            crossings.append((BOTTOM, min(us), max(us)))
        if min(vs) < rect[3] < max(vs):
            crossings.append((TOP, min(us), max(us)))
    return crossings


def merge_crossings(crossings, tolerance):
    """Merge touching or overlapping crossings on the same edge.

    A floor's sheathing and the joists below it share one break line.
    Returns ``(edge, low, high)`` sorted by edge and position.
    """
    merged = []
    for edge, low, high in sorted(crossings):
        if merged and merged[-1][0] == edge and low <= merged[-1][2] + tolerance:
            merged[-1] = (edge, merged[-1][1], max(merged[-1][2], high))
        else:
            merged.append((edge, low, high))
    return merged


def break_segment(edge, low, high, rect, outside_on_right=True):
    """Return the break line ``(start, end)`` for a merged crossing.

    The line sits on the inset crop edge. Its direction is chosen so the
    outside of the crop is on its right (or left), which is the side a
    line-based break family masks.
    """
    nu, nv = _OUTWARD[edge]
    if not outside_on_right:
        nu, nv = -nu, -nv
    direction = (-nv, nu)
    if edge in (LEFT, RIGHT):
        u = rect[0] if edge == LEFT else rect[2]
        start, end = (u, low), (u, high)
        along = direction[1]
    else:
        v = rect[1] if edge == BOTTOM else rect[3]
        start, end = (low, v), (high, v)
        along = direction[0]
    return (start, end) if along > 0 else (end, start)


def floor_label(type_name, material_names=()):
    """Return the elevation text for the top of a floor."""
    words = ' '.join([type_name or ''] + list(material_names)).upper()
    if _WOOD_FLOOR.search(words):
        return 'T/SHEATHING'
    if _CONCRETE_FLOOR.search(words):
        return 'T/SLAB'
    return 'T/FLOOR'


def unique_tops(tops, tolerance):
    """Keep one ``(v, right_u, label)`` per elevation, rightmost end first.

    Floors whose tops are within ``tolerance`` share one symbol, placed past
    the rightmost of them.
    """
    groups = []
    for top in sorted(tops):
        if groups and top[0] - groups[-1][0][0] <= tolerance:
            groups[-1].append(top)
        else:
            groups.append([top])
    return [max(group, key=lambda item: item[1]) for group in groups]


def visible_top(outline, label, rect):
    """Return ``(v, right_u, label)`` for an element's top, else None.

    The top must show inside ``rect`` (the trimmed crop) and the element must
    overlap it across; the symbol then starts at the element's right end, or
    the crop's right edge when the element runs past it.
    """
    if not outline:
        return None
    us = [point[0] for point in outline]
    top = max(point[1] for point in outline)
    right = max(us)
    if rect is not None:
        if not rect[1] <= top <= rect[3] or right <= rect[0] or min(us) >= rect[2]:
            return None
        right = min(right, rect[2])
    return top, right, label


def sheathing_layer(type_name, layers):
    """Return ``(depth_below_top, thickness)`` of a floor's sheathing, else None.

    ``layers`` are ``(material_name, thickness)`` from the top down. The first
    plywood, OSB, or sheathing layer is used; a single-layer floor whose type
    name says sheathing is sheathing throughout.
    """
    below = 0.0
    for material, thickness in layers:
        if thickness > 0 and _SHEATHING.search((material or '').upper()):
            return below, thickness
        below += thickness
    if len(layers) == 1 and _SHEATHING.search((type_name or '').upper()):
        return 0.0, layers[0][1]
    return None


def stud_layer(type_name, layers):
    """Return ``(depth_from_exterior, thickness)`` of a wood wall's studs, else None.

    ``layers`` are ``(material_name, thickness, is_structure)`` from the
    exterior in. The thickest wood or stud layer that is not sheathing is
    used. When no material says wood but the type name does, the thickest
    structure layer is used, then a single-layer wall's whole width.
    """
    def thickest(test):
        best = None
        offset = 0.0
        for layer in layers:
            if layer[1] > 0 and test(layer) and (best is None or layer[1] > best[1]):
                best = (offset, layer[1])
            offset += layer[1]
        return best

    def is_studs(layer):
        material = (layer[0] or '').upper()
        return bool(_STUDS.search(material)) and not _SHEATHING.search(material)

    found = thickest(is_studs)
    if found or not _STUDS.search((type_name or '').upper()):
        return found
    found = thickest(lambda layer: layer[2])
    if found is None and len(layers) == 1:
        found = thickest(lambda layer: True)
    return found


def plate_centers(bottom, top, u, rect, plate=PLATE_THICKNESS,
                  top_plates=TOP_PLATES, bottom_plates=BOTTOM_PLATES):
    """Return view-plane centers of a wall's top and bottom plates.

    Plates stack down from ``top`` and up from ``bottom`` at ``u``; plates
    whose center falls outside ``rect`` are left out, and a wall too short
    for all of them gets none.
    """
    if top - bottom < plate * (top_plates + bottom_plates):
        return []
    centers = [(u, top - plate * (index + 0.5)) for index in range(top_plates)]
    centers.extend((u, bottom + plate * (index + 0.5)) for index in range(bottom_plates))
    if rect is None:
        return centers
    return [center for center in centers
            if rect[0] <= center[0] <= rect[2] and rect[1] <= center[1] <= rect[3]]
