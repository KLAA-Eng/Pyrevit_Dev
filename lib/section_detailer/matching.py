"""Match modeled steel and wood members to KL&A detail component types.

The pyRevit command reads type names, file names, and type catalogs from Revit
and the KLAA library, then uses these rules to decide what to place. Nothing
here imports Revit so the rules can be tested in CPython.
"""

import re


LIBRARY_ROOT = (r'J:\Standards\910 Revit Support\KLAA Library'
                r'\KLAA Detail Components')
METALS_FOLDER = 'Div 05 - Metals'
WOOD_FOLDER = 'Div 06 - Wood and Plastic'

VIEW_SECTION = 'Section'
VIEW_SIDE = 'Side'

STEEL = 'steel'
WOOD = 'wood'

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

# Sawn lumber tries dimension lumber first, then heavy timber sizes.
_WOOD_FAMILIES = {
    'Sawn': ('6_Lumber_Dimension', '6_HeavyTimber'),
    'LVL': ('6_Lumber_LVL',),
    'PSL': ('6_Lumber_PSL',),
    'LSL': ('6_Lumber_LSL',),
    'Glulam': ('6_GluLaminatedBeam',),
}
_WOOD_MATERIALS = (
    ('Glulam', re.compile(r'GLULAM|GLU-?LAM|\bGLB\b')),
    ('LVL', re.compile(r'\bLVL')),
    ('PSL', re.compile(r'\bPSL')),
    ('LSL', re.compile(r'\bLSL')),
)

# Stacked materials are drawn as plies of this width (in), side by side.
_STACK_PLIES = {'LVL': 1.75, 'Sawn': 1.5}
# Modeled and catalog wood sizes agree within this many inches.
WOOD_TOLERANCE = 1.0 / 16
_WOOD_WORDS = re.compile(r'WOOD|LUMBER|TIMBER|\bSPF\b|\bDF\b|DOUGLAS|\bHF\b|\bSYP\b')

_LIBRARY_FILE = re.compile(
    r'^(?P<base>.+?)_KLAA_(?P<revision>\d+)?DC\.rfa$', re.IGNORECASE)
_DECIMAL = re.compile(r'^\d*\.\d+$|^\d+\.\d*$')
_NUMBER = r'\d+(?:\.\d+|[ -]\d+/\d+|/\d+)?|\.\d+'
_WOOD_SIZE = re.compile(
    r'(?<![A-Za-z\d./])(' + _NUMBER + r')\s*[xX]\s*(' + _NUMBER + r')')



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


def side_designation(designation, show_width=False):
    """Return the designation a ``Side`` family uses for a steel shape.

    KLAA rectangular HSS side types are named by the face seen and the wall,
    ``HSS6x1/4``; the seen face is the depth unless ``show_width`` is set.
    Other shapes keep their full designation.
    """
    if shape_key(designation) != 'HSS_RECT':
        return designation
    parts = normalize_designation(designation)[3:].split('X')
    return 'HSS{}X{}'.format(parts[1] if show_width else parts[0], parts[2])


# Wood

def parse_number(text):
    """Return inches from ``1 3/4``, ``1-3/4``, ``3/4``, ``1.75``, or None."""
    text = (text or '').strip()
    match = re.match(r'^(\d+)[ -](\d+)/(\d+)$', text)
    if match:
        whole, top, bottom = (int(value) for value in match.groups())
        return whole + float(top) / bottom
    match = re.match(r'^(\d+)/(\d+)$', text)
    if match:
        return float(match.group(1)) / int(match.group(2))
    try:
        return float(text)
    except ValueError:
        return None


def wood_size_key(name):
    """Return a ``(width, depth)`` key from the first ``AxB`` size in a name.

    ``2x10``, ``PT 2x10``, ``2x10 WBx``, and ``1 3/4x11 7/8`` all yield
    numeric keys; steel designations such as ``W12x26`` yield None.
    """
    match = _WOOD_SIZE.search(name or '')
    if not match:
        return None
    width, depth = parse_number(match.group(1)), parse_number(match.group(2))
    if width is None or depth is None:
        return None
    return round(width, 4), round(depth, 4)


def format_inches(value):
    """Return inches as lumber-style text to 1/16: 11.875 -> ``11 7/8``."""
    sixteenths = int(round(value * 16))
    whole, remainder = divmod(sixteenths, 16)
    if not remainder:
        return str(whole)
    bottom = 16
    while remainder % 2 == 0:
        remainder //= 2
        bottom //= 2
    fraction = '{}/{}'.format(remainder, bottom)
    return '{} {}'.format(whole, fraction) if whole else fraction


def wood_material(type_name, family_name=''):
    """Return Sawn, LVL, PSL, LSL, or Glulam from the type and family names."""
    words = '{} {}'.format(type_name or '', family_name or '').upper()
    for name, pattern in _WOOD_MATERIALS:
        if pattern.search(words):
            return name
    return 'Sawn'


def is_wood_name(type_name, family_name=''):
    """Return True when the names read as a wood member."""
    words = '{} {}'.format(type_name or '', family_name or '').upper()
    if wood_size_key(type_name) is not None or _WOOD_WORDS.search(words):
        return True
    return any(pattern.search(words) for _, pattern in _WOOD_MATERIALS)


def parse_catalog_sizes(text):
    """Return ``(name, width, depth)`` in inches from a wood type catalog.

    KLAA wood catalogs carry ``Width`` and ``Depth`` length columns, in
    either order. Rows without both values are skipped.
    """
    lines = (text or '').splitlines()
    if not lines:
        return []
    columns = {}
    for index, header in enumerate(lines[0].split(',')):
        parts = header.split('##')
        if parts[0].strip() in ('Width', 'Depth'):
            unit = parts[2].strip().lower() if len(parts) > 2 else 'inches'
            columns[parts[0].strip()] = (index, 12.0 if unit == 'feet' else 1.0)
    if len(columns) < 2:
        return []
    sizes = []
    for line in lines[1:]:
        cells = line.split(',')
        name = cells[0].strip()
        values = []
        for key in ('Width', 'Depth'):
            index, scale = columns[key]
            value = parse_number(cells[index]) if index < len(cells) else None
            values.append(None if value is None else value * scale)
        if name and None not in values:
            sizes.append((name, values[0], values[1]))
    return sizes


def choose_wood_stack(sizes, depth, width=None, material='Sawn', seen_width=False,
                      tolerance=WOOD_TOLERANCE):
    """Return ``(type_name, plies)`` that builds a wood member, else None.

    ``sizes`` are ``(name, width, depth)`` in inches from one family. The
    type's depth must match the member's. With ``width`` (a member seen
    end-on), a whole number of the type side by side must make up the
    width: LVL and sawn lumber prefer their 1 3/4 in and 1 1/2 in plies,
    other materials the fewest pieces. Without ``width`` (a member seen from
    its side) one piece is used. ``seen_width`` matches the type's width
    instead of its depth, for a member seen on its flat.
    """
    ply = _STACK_PLIES.get(material)
    best = None
    for name, type_width, type_depth in sizes:
        seen = type_width if seen_width else type_depth
        if abs(seen - depth) > tolerance or type_width <= 0:
            continue
        plies = 1
        if width is not None:
            plies = int(round(width / type_width))
            if plies < 1 or abs(plies * type_width - width) > tolerance:
                continue
        stacked = 0 if ply and abs(type_width - ply) <= tolerance else 1
        rank = (stacked, plies, len(name), name)
        if best is None or rank < best[0]:
            best = (rank, (name, plies))
    return best[1] if best else None


def wood_family_bases(material, view_kind=VIEW_SECTION):
    """Return KLAA wood family stems to try, in order, for a material."""
    return ['{}_{}'.format(stem, view_kind)
            for stem in _WOOD_FAMILIES.get(material, ())]


def member_spec(type_name, family_name='', view_kind=VIEW_SECTION, show_width=False,
                wood=False):
    """Return what to look for when detailing a member, else None.

    The dict holds ``kind`` (steel or wood), ``target`` (the type name to
    match), ``bases`` (KLAA family stems in preference order), and
    ``folder`` (library subfolder). Wood is matched by modeled size, so its
    ``target`` is left for the caller to fill and ``material`` is added.
    ``wood`` marks a member whose structural material is wood.
    """
    if shape_key(type_name):
        designation = normalize_designation(type_name)
        if view_kind == VIEW_SIDE:
            designation = side_designation(designation, show_width)
        return {
            'kind': STEEL,
            'target': designation,
            'bases': [family_base(shape_key(type_name), view_kind)],
            'folder': METALS_FOLDER,
        }
    if not (wood or is_wood_name(type_name, family_name)):
        return None
    material = wood_material(type_name, family_name)
    return {
        'kind': WOOD,
        'target': None,
        'bases': wood_family_bases(material, view_kind),
        'folder': WOOD_FOLDER,
        'material': material,
    }


def match_key(kind):
    """Return the name comparison function for a member kind."""
    return wood_size_key if kind == WOOD else normalize_designation


# Library files

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


def find_catalog_type(type_names, designation, key=normalize_designation):
    """Return the catalog spelling of ``designation``, else None.

    When several names share a size (``2x10`` and ``PT 2x10``), the plainest
    (shortest) name wins.
    """
    want = key(designation)
    if not want:
        return None
    matches = [name for name in type_names if key(name) == want]
    if not matches:
        return None
    return min(matches, key=len)


def rank_candidates(target, candidates, bases=(), preferred_families=(),
                    key=normalize_designation, family_only=False):
    """Return loaded ``(family, type)`` pairs that match ``target``.

    Families from a reference detail rank first, then revisions of the KLAA
    ``bases`` in order, then the rest; within a family the plainest name
    comes first. With ``family_only`` (used for wood, where sizes repeat
    across materials) other KLAA families never match, and office families
    match only on an identical name.
    """
    want = key(target)
    if not want:
        return []
    if isinstance(bases, str):
        bases = (bases,)
    preferred = set(name.lower() for name in preferred_families)
    exact = normalize_designation(target)

    def family_rank(family):
        if family.lower() in preferred:
            return 0
        for index, base in enumerate(bases):
            if base and family_matches_base(family, base):
                return 1 + index
        return None

    ranked = []
    for family, type_name in set(candidates):
        if key(type_name) != want:
            continue
        rank = family_rank(family)
        if rank is None:
            if family_only and (normalize_designation(type_name) != exact or
                                parse_library_filename(family + '.rfa')):
                continue
            rank = 1 + len(bases)
        ranked.append((rank, len(type_name), family.lower(), type_name.lower(),
                       (family, type_name)))
    return [item[-1] for item in sorted(ranked)]


def best_per_family(ranked):
    """Keep the first ranked type of each family.

    The user is asked to choose only between families; within a family the
    plainest name (``2x10`` over ``PT 2x10``) is used.
    """
    seen = set()
    result = []
    for family, type_name in ranked:
        if family.lower() not in seen:
            seen.add(family.lower())
            result.append((family, type_name))
    return result
