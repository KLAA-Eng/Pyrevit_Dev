"""Compare a hanger's Header/Joist text with the framing member it is attached to.

Hanger values come from the Smart Hanger schedule, for example
'6 3/4x15 GLB', '(3)14" LVL', '(2)9 1/2" LVL' or '(2)2x10'. Sizes are parsed
into plies, width, depth (inches) and material, then compared with the
member's 'Family: Type' label, falling back to its width/depth parameters.

  * Depth must agree within SIZE_TOL_IN whenever both are known.
  * Width is checked when the hanger gives one (explicitly, or as plies of
    1 3/4" LVL/LSL); a member modeled as a single ply also matches.
  * Material is checked only when both name a known material.
A comparison without a hanger depth or member depth is left undecided.
"""

from __future__ import division

import re


SIZE_TOL_IN = 0.125
PLY_WIDTH_IN = 1.75
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

_PLY = re.compile(r'\(\s*(\d+)\s*\)|(\d+)\s*-?\s*PLY\b', re.I)
_SERIES = re.compile(r'\b(TJI|NI|BCI|LPI)\s*-?\s*\d+\b', re.I)
_NUMBER = re.compile(r'(\d+)\s*[- ]\s*(\d+)\s*/\s*(\d+)|(\d+)\s*/\s*(\d+)|(\d+(?:\.\d+)?)')


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
    """Return {'plies', 'width', 'depth', 'material'} (inches) parsed from text."""
    size = {'plies': None, 'width': None, 'depth': None, 'material': None}
    if not text:
        return size
    text = text.replace(u'×', 'x').replace('"', ' ').replace("''", ' ')
    size['material'] = _material(text)
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


def _hanger_width(size):
    if size['width'] is not None:
        return size['width'] * (size['plies'] or 1)
    if size['plies'] and size['material'] in PLY_MATERIALS:
        return size['plies'] * PLY_WIDTH_IN
    return None


def _close(a, b):
    return abs(a - b) <= SIZE_TOL_IN


def compare_size(hanger_text, member_label, member_width_in=None, member_depth_in=None):
    """(True | False | None, reason) for a hanger Header/Joist value vs one member."""
    hanger = parse_size(hanger_text)
    member = parse_size(member_label)
    if member['width'] is not None:                  # 'W x D' in the type name
        width, depth = member['width'], member['depth']
    else:                                            # grades/marks make lone numbers unreliable
        width = member_width_in
        depth = member_depth_in if member_depth_in is not None else member['depth']
    if member['plies'] and width is not None:
        width *= member['plies']
    if hanger['depth'] is None or depth is None:
        return None, 'size not compared'
    problems = []
    if not _close(hanger['depth'], depth):
        problems.append('depth')
    hanger_width = _hanger_width(hanger)
    if hanger_width is not None and width is not None and not (
            _close(hanger_width, width)
            or (hanger['plies'] and _close(hanger_width, width * hanger['plies']))):
        problems.append('width')
    if hanger['material'] and member['material'] and hanger['material'] != member['material']:
        problems.append('material')
    if problems:
        return False, '%s differs' % '/'.join(problems)
    return True, ''


def mismatch_label(supported_ok, supporting_ok):
    """Blank, or which member disagrees with the hanger's Joist/Header values."""
    if supported_ok is False and supporting_ok is False:
        return MISMATCH_BOTH
    if supported_ok is False:
        return MISMATCH_SUPPORTED
    if supporting_ok is False:
        return MISMATCH_SUPPORTING
    return ''
