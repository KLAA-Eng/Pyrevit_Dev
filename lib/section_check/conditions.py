"""Describe what a section cuts as comparable conditions.

A condition is one modeled element: its group (Wall, Floor, Framing, Column,
Foundation, Roof), its 'Family: Type' label, the sizes and materials read from
that label, its orientation to the cut, and the side of the cut it sits on.
Drafting details have no model elements, so their component names and note
text are read into the same groups, sizes, and materials.
"""

from __future__ import division

import re


WALL, FLOOR, FRAMING, COLUMN, FOUNDATION, ROOF = (
    'Wall', 'Floor', 'Framing', 'Column', 'Foundation', 'Roof')
CUT, ALONG, SKEW, VERTICAL = 'cut', 'along', 'skew', 'vertical'
LEFT, CENTER, RIGHT = 'L', 'C', 'R'
CENTER_BAND_FT = 1.0
ALONG_COSINE = 0.866   # within 30 deg of the cut line
CUT_COSINE = 0.5       # within 30 deg of the view direction

STEEL_SHAPE = re.compile(
    r'(?<![A-Z0-9])(W|WT|HSS|MC|C|L)\s?(\d+(?:\.\d+)?)\s?X\s?(\d+(?:\.\d+|/\d+)?)'
    r'(?:\s?X\s?(\d+(?:\.\d+|/\d+)?))?(?![A-Z0-9])')
LUMBER = re.compile(r'(?<![A-Z0-9./])(\d{1,2})\s?X\s?(\d{1,2})(?![A-Z0-9./])')
INCHES = re.compile(r'(?<![A-Z0-9./])(\d+(?:\.\d+)?(?:[\s-]\d+/\d+)?)\s?(?:"|IN\b|INCH)')
MATERIALS = {
    'CMU': 'CMU', 'MASONRY': 'CMU', 'BLOCK': 'CMU',
    'CONC': 'CONC', 'CONCRETE': 'CONC', 'SOG': 'CONC',
    'LVL': 'LVL', 'GLB': 'GLB', 'GLULAM': 'GLB', 'PSL': 'PSL', 'LSL': 'LSL',
    'TJI': 'TJI', 'CLT': 'CLT', 'STUD': 'STUD', 'STUDS': 'STUD',
    'STEEL': 'STEEL', 'STL': 'STEEL', 'MTL': 'STEEL', 'METAL': 'STEEL',
    'WOOD': 'WOOD', 'TIMBER': 'WOOD', 'DF': 'WOOD', 'BRICK': 'BRICK', 'DECK': 'DECK',
}
GROUP_WORDS = {
    WALL: ('WALL', 'WALLS', 'CMU', 'MASONRY', 'STUD', 'STUDS', 'PARAPET', 'SHEARWALL'),
    FLOOR: ('SLAB', 'DECK', 'SOG', 'TOPPING', 'FLOOR', 'SHEATHING', 'DIAPHRAGM'),
    FRAMING: ('BEAM', 'JOIST', 'JST', 'JOISTS', 'GIRDER', 'HEADER', 'HDR', 'LEDGER',
              'TJI', 'LVL', 'GLB', 'PSL', 'RAFTER', 'TRUSS', 'PURLIN', 'BLOCKING'),
    COLUMN: ('COLUMN', 'COL', 'POST', 'HSS'),
    FOUNDATION: ('FOOTING', 'FTG', 'PILE', 'PIER', 'CAISSON', 'FOUNDATION', 'STEMWALL'),
    ROOF: ('ROOF',),
}


def _clean(text):
    text = (text or '').upper()
    for quote in (u'″', u'”', u'“', "''"):
        text = text.replace(quote, '"')
    return text.replace(u' ', ' ').replace(u' ', ' ')


def read_label(text):
    """(sizes, materials) sets from a type name or note text."""
    text = _clean(text)
    sizes, materials = set(), set()
    for match in STEEL_SHAPE.finditer(text):
        sizes.add('X'.join(p for p in (match.group(1) + match.group(2),
                                       match.group(3), match.group(4)) if p))
        materials.add('STEEL')
    text = STEEL_SHAPE.sub(' ', text)
    for match in LUMBER.finditer(text):
        sizes.add('%sX%s' % match.groups())
        materials.add('WOOD')
    text = LUMBER.sub(' ', text)
    for match in INCHES.finditer(text):
        sizes.add(re.sub(r'[\s-]+', '-', match.group(1)) + 'IN')
    for word in re.findall(r'[A-Z]+', text):
        if word in MATERIALS:
            materials.add(MATERIALS[word])
    return sizes, materials


def orientation(direction, right):
    """'along' the cut line, 'cut' (running into the view), or 'skew' for a
    plan direction; None for a vertical or unknown direction."""
    if direction is None:
        return None
    length = (direction[0] ** 2 + direction[1] ** 2) ** 0.5
    if length < 1e-6:
        return None
    cosine = abs(direction[0] * right[0] + direction[1] * right[1]) / length
    if cosine >= ALONG_COSINE:
        return ALONG
    return CUT if cosine <= CUT_COSINE else SKEW


def side(offset, band=CENTER_BAND_FT):
    """'L', 'C', or 'R' for an offset (feet) to the viewer's right; None if unknown."""
    if offset is None:
        return None
    if abs(offset) <= band:
        return CENTER
    return RIGHT if offset > 0 else LEFT


def condition(group, label, orient=None, offset=None):
    sizes, materials = read_label(label)
    return {'group': group, 'label': label, 'sizes': sizes, 'materials': materials,
            'orient': orient, 'side': side(offset)}


def mirrored(conditions):
    """The conditions seen opposite hand: left and right swapped."""
    swap = {LEFT: RIGHT, RIGHT: LEFT}
    return [dict(c, side=swap.get(c['side'], c['side'])) for c in conditions]


def detail_content(labels, texts):
    """{'groups', 'sizes', 'materials'} named by a drafting detail's component
    and region type names (labels) and its note texts."""
    groups, sizes, materials = set(), set(), set()
    for text in list(labels) + list(texts):
        found_sizes, found_materials = read_label(text)
        sizes |= found_sizes
        materials |= found_materials
        words = set(re.findall(r'[A-Z]+', _clean(text)))
        for group, keys in GROUP_WORDS.items():
            if words.intersection(keys):
                groups.add(group)
        if any(s[0] == 'W' and s[1:2].isdigit() for s in found_sizes):
            groups.add(FRAMING)
    return {'groups': groups, 'sizes': sizes, 'materials': materials}


def describe(cond):
    extras = [v for v in (cond['orient'], cond['side']) if v]
    return '%s %s%s' % (cond['group'], cond['label'],
                        ' (%s)' % ', '.join(extras) if extras else '')
