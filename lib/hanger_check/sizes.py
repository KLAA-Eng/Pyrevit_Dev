"""Compare a hanger's Header/Joist text with the framing member it is attached to.

Hanger values come from the Smart Hanger schedule, for example
'6 3/4x15 GLB', '(3)14" LVL', '11 7/8" TJI 360', '(2)LVL OR PACKOUT' or
'WF BEAM'. Sizes are parsed into plies, width, depth (inches), material and
I-joist series, then compared with the member's 'Family: Type' label, falling
back to its width/depth parameters.

Joist vs supported member is strict:
  * Depth must agree within SIZE_TOL_IN whenever both are known; nominal sawn
    lumber (2x10) also matches its actual size (1 1/2 x 9 1/4).
  * Members are modeled as one element the full width of all plies: plies x
    1 3/4" for LVL/LSL, plies x 1 1/2" for sawn lumber. The hanger width
    (explicit, or its plies x ply width) must equal the member's full width,
    and a type name giving plies must agree with the hanger's plies and with
    its own modeled width.
  * Material and I-joist series must agree when both are named.
Header vs supporting member is loose: the Header may list alternatives
('LVL OR 2x8'), and only material, depth and steel/wall kind are compared.
A comparison without enough information is left undecided, never a mismatch.
"""

from __future__ import division

import re


SIZE_TOL_IN = 0.125
PLY_WIDTH_IN = 1.75
SAWN_PLY_WIDTH_IN = 1.5
MIN_NAME_DEPTH_IN = 3.0          # smaller lone numbers in a type name are grades or marks
PLY_MATERIALS = ('LVL', 'LSL')
MATERIALS = (
    ('GLB', ('GLB', 'GLULAM', 'GLU-LAM')),
    ('LVL', ('LVL', 'MICROLLAM')),
    ('PSL', ('PSL', 'PARALLAM')),
    ('LSL', ('LSL', 'TIMBERSTRAND')),
    ('TJI', ('TJI',)),
)

MISMATCH_SUPPORTED = 'Supported member mismatch'
MISMATCH_SUPPORTING = 'Supporting member mismatch'
MISMATCH_BOTH = 'Both mismatch'

KIND_STEEL = 'steel'
KIND_WALL = 'wall'
KIND_COLUMN = 'column'
DETAIL_KINDS = (KIND_WALL, KIND_COLUMN)

MOUNT_TOP_FLANGE = 'Top flange mounted'
MOUNT_WEB_PACKOUT = 'Face mounted - needs web packout'
MOUNT_WALL = 'Wall - ledger or plate'
MOUNT_COLUMN = 'Column - see detail'
NO_FASTENER = ('', 'N/A', 'NA', 'NONE', 'NO')

_PLY = re.compile(r'\(\s*(\d+)\s*\)|(\d+)\s*-?\s*PLY\b', re.I)
_SERIES = re.compile(r'\b(TJI|NI|BCI|LPI)\s*-?\s*(\d+)\b', re.I)
# Numbers glued to letters or underscores (15SE, 2.0E, KLAA_15) are codes, not sizes.
_NUMBER = re.compile(r'(?<![A-Za-z_\d.])(?:(\d+)\s*[- ]\s*(\d+)\s*/\s*(\d+)|(\d+)\s*/\s*(\d+)'
                     r'|(\d+(?:\.\d+)?))(?![A-Za-z_\d.])')
_ALTERNATIVES = re.compile(r'\bOR\b', re.I)
_SAWN_WORDS = re.compile(r'\b(DIMENSION|LUMBER|SAWN|DF|SPF|HF|SYP)\b')
_STEEL_SHAPE = re.compile(r'(^|[^A-Z])W\s*\d+(\.\d+)?\s*X\s*\d+')
_STEEL_WORDS = re.compile(r'\bWF\b|WIDE\s*-?\s*FLANGE|\bSTEEL\b')
_WALL_WORDS = re.compile(r'\b(PLATE|LEDGER|LEDGE|WALL|CONCRETE|CMU|MASONRY)\b')
_COLUMN_WORDS = re.compile(r'\b(COLUMN|POST)\b')


def _material(text):
    upper = text.upper()
    for key, words in MATERIALS:
        for word in words:
            if re.search(r'(^|[^A-Z])' + re.escape(word) + r'([^A-Z]|$)', upper):
                return key
    return None


def _numbers(text):
    values = []
    for match in _NUMBER.finditer(text):
        whole, num, den, frac_num, frac_den, plain = match.groups()
        if whole is not None:
            values.append(int(whole) + int(num) / int(den))
        elif frac_num is not None:
            values.append(int(frac_num) / int(frac_den))
        else:
            values.append(float(plain))
    return values


def parse_size(text):
    """Return {'plies', 'width', 'depth', 'material', 'series'} (inches) parsed from text."""
    size = {'plies': None, 'width': None, 'depth': None, 'material': None, 'series': None}
    if not text:
        return size
    text = text.replace(u'\u00d7', 'x').replace('"', ' ').replace("''", ' ')
    size['material'] = _material(text)
    series = _SERIES.search(text)
    if series:
        size['series'] = '%s %s' % (series.group(1).upper(), series.group(2))
    text = _SERIES.sub(' ', text)
    ply = _PLY.search(text)
    if ply:
        size['plies'] = int(ply.group(1) or ply.group(2))
        text = text[:ply.start()] + ' ' + text[ply.end():]
    sides = re.split(r'(?<=[\d\s])[xX](?=[\s\d])', text, maxsplit=1)
    if len(sides) == 2:
        width, depth = _numbers(sides[0]), _numbers(sides[1])
        size['width'] = width[-1] if width else None
        size['depth'] = depth[0] if depth else None
    else:
        numbers = _numbers(text)
        size['depth'] = max(numbers) if numbers else None
    return size


def parse_member(label):
    """parse_size for a 'Family: Type' label: sizes and plies come from the type
    name only (family names such as Framing_KLAA_15SE are not sizes); material
    and series may come from either."""
    if not label or ':' not in label:
        return parse_size(label)
    size = parse_size(label.split(':', 1)[1])
    whole = parse_size(label)
    size['material'] = size['material'] or whole['material']
    size['series'] = size['series'] or whole['series']
    return size


def _is_nominal(size):
    """Sawn lumber written nominally, such as 2x10: whole inches and no material."""
    return (size['material'] is None and size['depth'] is not None
            and size['depth'] == int(size['depth']) and size['depth'] >= 4
            and (size['width'] is None or size['width'] == int(size['width'])))


def _actual(nominal):
    return nominal - (0.5 if nominal <= 6 else 0.75)


def _ply_width(material, sawn):
    """Width of one ply: 1 3/4" for LVL/LSL, 1 1/2" for sawn lumber, else None."""
    if material in PLY_MATERIALS:
        return PLY_WIDTH_IN
    if material is None and sawn:
        return SAWN_PLY_WIDTH_IN
    return None


def _hanger_widths(size, ply_width):
    plies = size['plies'] or 1
    if size['width'] is not None:
        widths = [size['width'] * plies]
        if _is_nominal(size):
            widths.append(_actual(size['width']) * plies)
        return widths
    if size['plies'] and ply_width:
        return [size['plies'] * ply_width]
    return []


def _member_depth(member, member_depth_in):
    """(depth, source). The type name wins; a depth parameter is used only when
    the name gives none, or only a grade/mark number such as GL-1 or 2.0E."""
    if member['depth'] is not None and (member['width'] is not None
                                        or member['depth'] >= MIN_NAME_DEPTH_IN):
        return member['depth'], 'type name'
    if member_depth_in is not None:
        return member_depth_in, 'depth parameter'
    return member['depth'], 'type name'


def _member_width(member, member_width_in, ply_width):
    """Full modeled width. A width parameter is the full width of all plies; a
    'W x D' type name with plies may give one ply (1 3/4, or nominal 2) or the
    full width."""
    if member['width'] is None:
        return member_width_in
    width, plies = member['width'], member['plies']
    if plies and ply_width and (_close(width, ply_width)
                                or (_is_nominal(member) and _close(_actual(width), ply_width))):
        return ply_width * plies
    return width


def _close(a, b):
    return abs(a - b) <= SIZE_TOL_IN


def format_inches(value):
    """Inches to the nearest 1/16 as text, e.g. 11.875 -> '11 7/8"'."""
    sixteenths = int(round(value * 16))
    whole, rest = divmod(sixteenths, 16)
    if not rest:
        return '%d"' % whole
    den = 16
    while rest % 2 == 0:
        rest, den = rest // 2, den // 2
    return ('%d %d/%d"' % (whole, rest, den)) if whole else ('%d/%d"' % (rest, den))


def compare_size(hanger_text, member_label, member_width_in=None, member_depth_in=None,
                 strict=True):
    """(True | False | None, reason) for a hanger Header/Joist value vs one member.

    strict also checks width, plies and I-joist series. A True result may carry
    a reason worth noting (for example an unconfirmed material).
    """
    hanger = parse_size(hanger_text)
    member = parse_member(member_label)
    depth, depth_source = _member_depth(member, member_depth_in)
    sawn = _is_nominal(hanger) or _is_nominal(member) or bool(_SAWN_WORDS.search(
        (member_label or '').upper()))
    ply_width = _ply_width(member['material'] or hanger['material'], sawn)
    member_width = _member_width(member, member_width_in, ply_width)
    problems, notes, details = [], [], []
    if hanger['material'] and member['material'] and hanger['material'] != member['material']:
        problems.append('material')
    if strict and hanger['series'] and member['series'] and hanger['series'] != member['series']:
        problems.append('series')
    nominal = _is_nominal(hanger)
    depth_known = hanger['depth'] is not None and depth is not None
    if depth_known and not (_close(hanger['depth'], depth)
                            or (nominal and _close(_actual(hanger['depth']), depth))):
        problems.append('depth')
        details.append('depth %s vs %s from %s' % (
            format_inches(hanger['depth']), format_inches(depth), depth_source))
    if strict and hanger['plies'] and member['plies'] and hanger['plies'] != member['plies']:
        problems.append('plies')
        details.append('(%d) vs (%d)' % (hanger['plies'], member['plies']))
    if strict and member['plies'] and ply_width and member_width is not None and not _close(
            member_width, member['plies'] * ply_width):
        problems.append('member width')
        details.append('type (%d) needs %s, modeled %s' % (
            member['plies'], format_inches(member['plies'] * ply_width),
            format_inches(member_width)))
    widths = _hanger_widths(hanger, ply_width)
    if strict and member_width is not None and widths and not any(
            _close(w, member_width) for w in widths):
        problems.append('width')
        nearest = min(widths, key=lambda w: abs(w - member_width))
        details.append('width %s vs %s' % (format_inches(nearest), format_inches(member_width)))
    if problems:
        reason = '%s differs' % '/'.join(problems)
        return False, '%s (hanger vs member: %s)' % (reason, ', '.join(details)) if details else reason
    if not depth_known:
        if not strict and hanger['material'] and member['material']:
            return True, ''
        return None, 'size not compared'
    if strict and hanger['material'] and not member['material']:
        notes.append('material %s not confirmed' % hanger['material'])
    return True, '; '.join(notes)


def support_kind(header_text, member_label=None):
    """KIND_STEEL, KIND_WALL, KIND_COLUMN or None from the Header and supporting member."""
    member = (member_label or '').upper()
    header = (header_text or '').upper()
    if _STEEL_SHAPE.search(member) or _STEEL_WORDS.search(member):
        return KIND_STEEL
    if _STEEL_SHAPE.search(header) or _STEEL_WORDS.search(header):
        return KIND_STEEL
    if _WALL_WORDS.search(header):
        return KIND_WALL
    if _COLUMN_WORDS.search(header):
        return KIND_COLUMN
    return None


def compare_supporting(header_text, member_label, member_width_in=None, member_depth_in=None):
    """Loose (True | False | None, reason) for a Header value vs the supporting member.

    Each 'OR' alternative is tried; any match passes, and a mismatch needs every
    alternative to disagree. Wall and column alternatives are not compared.
    """
    if not header_text:
        return None, 'size not compared'
    member_steel = support_kind(None, member_label) == KIND_STEEL
    outcomes, reasons = [], []
    for alternative in _ALTERNATIVES.split(header_text):
        kind = support_kind(alternative)
        if kind in DETAIL_KINDS:
            ok, reason = None, 'wall or column support'
        elif kind == KIND_STEEL:
            ok, reason = (True, '') if member_steel else (False, 'steel beam expected')
        elif member_steel:                           # wood packout on a steel beam
            ok, reason = None, 'wood alternative on steel'
        else:
            ok, reason = compare_size(alternative, member_label, member_width_in,
                                      member_depth_in, strict=False)
        outcomes.append(ok)
        reasons.append(reason)
    if True in outcomes:
        return True, ''
    if outcomes and all(ok is False for ok in outcomes):
        return False, '; '.join(r for r in reasons if r)
    return None, 'size not compared'


def has_top_flange(fastener_text):
    """True when the Fastener-TF value lists fasteners rather than '--' or blank."""
    text = (fastener_text or '').strip().upper()
    return text.strip('-_ ') != '' and text not in NO_FASTENER


def mounting_label(kind, fastener_tf):
    """How the hanger mounts: top flange, face mount on steel, or wall/column detail."""
    if kind == KIND_STEEL:
        return MOUNT_TOP_FLANGE if has_top_flange(fastener_tf) else MOUNT_WEB_PACKOUT
    if has_top_flange(fastener_tf):
        return MOUNT_TOP_FLANGE
    if kind == KIND_WALL:
        return MOUNT_WALL
    if kind == KIND_COLUMN:
        return MOUNT_COLUMN
    return ''


def mismatch_label(supported_ok, supporting_ok):
    """Blank, or which member disagrees with the hanger's Joist/Header values."""
    if supported_ok is False and supporting_ok is False:
        return MISMATCH_BOTH
    if supported_ok is False:
        return MISMATCH_SUPPORTED
    if supporting_ok is False:
        return MISMATCH_SUPPORTING
    return ''
