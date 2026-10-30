"""Match modeled steel shapes to KL&A detail component families and types.

The pyRevit command reads type names, file names, and type catalogs from Revit
and the KLAA library, then uses these rules to decide what to place. Nothing
here imports Revit so the rules can be tested in CPython.
"""

import re


LIBRARY_ROOT = (r'J:\Standards\910 Revit Support\KLAA Library'
                r'\KLAA Detail Components')
METALS_FOLDER = 'Div 05 - Metals'

VIEW_SECTION = 'Section'
VIEW_SIDE = 'Side'

# Longest prefixes first so WT is not read as W, HP as H, and so on.
_SHAPE_PREFIXES = ('PIPE', 'HSS', 'HP', 'WT', 'MC', 'W', 'C', 'L')

_FAMILY_SHAPES = {
    'W': 'WideFlange',
    'HSS_RECT': 'HSS',
    'HSS_ROUND': 'HSS_Round',
    'L': 'Angle',
    'C': 'Channel',
    'MC': 'Channel',
    'WT': 'WT',
    'HP': 'HP',
    'PIPE': 'Pipe',
}

_LIBRARY_FILE = re.compile(
    r'^(?P<base>.+?)_KLAA_(?P<revision>\d+)?DC\.rfa$', re.IGNORECASE)
_DECIMAL = re.compile(r'^\d*\.\d+$|^\d+\.\d*$')


def _normalize_token(token):
    """Drop insignificant decimal zeros so 20.000 and 20 compare equal."""
    if not _DECIMAL.match(token):
        return token
    trimmed = token.rstrip('0').rstrip('.')
    if trimmed.startswith('.'):
        trimmed = '0' + trimmed
    return trimmed or '0'


def normalize_designation(name):
    """Return a comparison key for an AISC designation.

    Revit framing types (``W12X26``), KLAA catalogs (``W12x26``), and hand-typed
    names (``W 12x26``) all reduce to ``W12X26``. Round HSS walls such as
    ``0.500`` and ``0.5`` compare equal.
    """
    if not name:
        return ''
    text = re.sub(r'\s+', '', name).upper()
    match = re.match(r'^([A-Z]+)(.*)$', text)
    if not match:
        return text
    prefix, rest = match.groups()
    return prefix + 'X'.join(_normalize_token(part) for part in rest.split('X'))


def shape_key(designation):
    """Return the KLAA shape key for a designation, or None when unsupported."""
    key = normalize_designation(designation)
    for prefix in _SHAPE_PREFIXES:
        if not key.startswith(prefix):
            continue
        rest = key[len(prefix):]
        if not rest or not rest[0].isdigit():
            continue
        if prefix == 'HSS':
            return 'HSS_ROUND' if rest.count('X') == 1 else 'HSS_RECT'
        return prefix
    return None


def family_base(shape, view_kind=VIEW_SECTION):
    """Return the KLAA family name stem for a shape key and view kind."""
    name = _FAMILY_SHAPES.get(shape)
    if name is None:
        return None
    return '5_{}_{}'.format(name, view_kind)


def parse_library_filename(filename):
    """Return ``(base, revision)`` for a KLAA ``.rfa`` name, else None.

    Revit backups (``name.0001.rfa``) are not library families. An undated
    family (``_KLAA_DC``) has revision 0.
    """
    match = _LIBRARY_FILE.match(filename or '')
    if not match or re.search(r'\.\d{4}\.rfa$', filename, re.IGNORECASE):
        return None
    revision = match.group('revision')
    return match.group('base'), int(revision) if revision else 0


def pick_library_file(filenames, base):
    """Return the newest library file whose stem is ``base``, else None."""
    best = None
    best_revision = -1
    for filename in filenames:
        parsed = parse_library_filename(filename)
        if parsed is None or parsed[0].lower() != base.lower():
            continue
        if parsed[1] > best_revision:
            best, best_revision = filename, parsed[1]
    return best


def family_matches_base(family_name, base):
    """Return True when a loaded family name is a revision of ``base``."""
    parsed = parse_library_filename((family_name or '') + '.rfa')
    return parsed is not None and parsed[0].lower() == base.lower()


def parse_type_catalog(text):
    """Return type names from a Revit type catalog, in file order."""
    names = []
    lines = (text or '').splitlines()
    for line in lines[1:]:
        name = line.split(',', 1)[0].strip()
        if name:
            names.append(name)
    return names


def find_catalog_type(type_names, designation):
    """Return the catalog spelling of ``designation``, else None."""
    key = normalize_designation(designation)
    for name in type_names:
        if normalize_designation(name) == key:
            return name
    return None


def rank_candidates(designation, candidates, base=None, preferred_families=()):
    """Return loaded ``(family, type)`` pairs that match ``designation``.

    Only exact designation matches are returned. Families from a reference
    detail rank first, then revisions of the KLAA ``base`` family, then the
    rest; ties keep a stable alphabetical order.
    """
    key = normalize_designation(designation)
    preferred = set(name.lower() for name in preferred_families)

    def order(candidate):
        family = candidate[0]
        if family.lower() in preferred:
            rank = 0
        elif base and family_matches_base(family, base):
            rank = 1
        else:
            rank = 2
        return rank, family.lower(), candidate[1].lower()

    matches = [candidate for candidate in candidates
               if normalize_designation(candidate[1]) == key]
    return sorted(set(matches), key=order)
