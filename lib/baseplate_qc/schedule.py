# -*- coding: utf-8 -*-
"""Read the base plate schedule and anchor rod table from drafted text.

The schedules are drawn with one text note per cell, so the Revit command
passes each note as a cell dict: {'text', 'xmin', 'ymin', 'xmax', 'ymax'} in
view coordinates (feet). Rows are rebuilt from the cells' heights and columns
from the nearest header cell, so the readers work at any view scale.
"""

import re


SCHEDULE_TITLE = 'BASE PLATE SCHEDULE'

# Anchor rod diameter (in) -> edge distance "C" (in), from the KL&A anchor rod
# requirements table. Used when the drawing set has no readable table.
DEFAULT_EDGE_DISTANCES = {
    0.75: 1.5,
    0.875: 2.0,
    1.0: 2.5,
    1.25: 2.5,
    1.5: 2.5,
}

# Header text -> schedule field, checked in order (first match wins).
_BASE_PLATE_HEADERS = (
    ('mark', ('MARK',)),
    ('type', ('TYPE',)),
    ('length', ('DIM L', 'DIML', 'L')),
    ('width', ('DIM W', 'DIMW', 'W')),
    ('thickness', ('THICKNESS', 'THICK', 'THK')),
    ('rod_count', ('NUMBER', 'NO', 'QTY')),
    ('rod_size', ('SIZE', 'DIA')),
    ('embed', ('EMBED',)),
)

_MARK_RE = re.compile(r'^[A-Z]{1,4}\d+[A-Z]?$')
_FEET_INCHES_RE = re.compile(r"^(\d+(?:\.\d+)?)'\s*-?\s*(.*)$")
_MIXED_RE = re.compile(r'^(\d+)\s+(\d+)/(\d+)$')
_FRACTION_RE = re.compile(r'^(\d+)/(\d+)$')
_DECIMAL_RE = re.compile(r'^(?:\d+(?:\.\d*)?|\.\d+)$')


def normalize_text(text):
    """Upper-case text with runs of whitespace (including line breaks) as one space."""
    return ' '.join((text or '').upper().split())


def normalize_mark(text):
    """Return a mark like 'BP7' from 'bp 7', 'BP-7', or ' BP7 '."""
    return re.sub(r'[\s\-_.]', '', (text or '').upper())


def is_mark(text):
    return bool(_MARK_RE.match(normalize_mark(text)))


def parse_inches(text):
    """Return inches from schedule text such as 14", 1 1/4", 3/4"Ø, 1'-2", or 0.75.

    Diameter symbols, quotes, and a trailing '(IN)' are ignored. Returns None
    when the text is not a dimension.
    """
    if text is None:
        return None
    value = normalize_text(text)
    for token in ('%%C', u'Ø', u'ø', u'Φ', u'φ', u'ϕ', u'⌀', '(IN)', 'IN.', 'DIA'):
        value = value.replace(token, ' ')
    value = value.replace(u'″', '"').replace(u'′', "'").replace("''", '"')
    value = value.replace('"', ' ').strip()
    feet = 0.0
    match = _FEET_INCHES_RE.match(value)
    if match:
        feet = float(match.group(1))
        value = match.group(2).strip()
        if not value:
            return feet * 12.0
    value = ' '.join(value.replace('-', ' ').split())
    inches = _simple_inches(value)
    if inches is None:
        return None
    return feet * 12.0 + inches


def _simple_inches(value):
    match = _MIXED_RE.match(value)
    if match:
        whole, num, den = (int(group) for group in match.groups())
        return whole + float(num) / den if den else None
    match = _FRACTION_RE.match(value)
    if match:
        num, den = (int(group) for group in match.groups())
        return float(num) / den if den else None
    if _DECIMAL_RE.match(value):
        return float(value)
    return None


def parse_count(text):
    match = re.match(r'^\s*(\d+)', text or '')
    return int(match.group(1)) if match else None


def format_inches(value):
    """Return 1.25 as 1 1/4", to the nearest 1/16"."""
    if value is None:
        return '?'
    sixteenths = int(round(value * 16))
    whole, rem = divmod(sixteenths, 16)
    if rem == 0:
        return '{}"'.format(whole)
    den = 16
    while rem % 2 == 0:
        rem //= 2
        den //= 2
    if whole:
        return '{} {}/{}"'.format(whole, rem, den)
    return '{}/{}"'.format(rem, den)


# -- Cell geometry -------------------------------------------------------------

def split_lines(cells):
    """Return one cell per text line.

    Drafted ("dumb") schedules often hold a whole column in one note, one
    value per line. A note's lines share its height evenly, so each line gets
    the middle half of its slot: lines of different notes in the same table
    row overlap, and neighboring rows do not.
    """
    result = []
    for cell in cells:
        lines = re.split(r'\r\n|\r|\n', cell['text'] or '')
        while lines and not lines[-1].strip():
            lines.pop()  # Revit ends note text with a line break.
        if len(lines) <= 1:
            result.append(dict(cell, text=lines[0] if lines else ''))
            continue
        slot = (cell['ymax'] - cell['ymin']) / float(len(lines))
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            middle = cell['ymax'] - slot * (index + 0.5)
            result.append({'text': line, 'xmin': cell['xmin'], 'xmax': cell['xmax'],
                           'ymin': middle - slot / 4.0, 'ymax': middle + slot / 4.0})
    return result


def _center(cell):
    return ((cell['xmin'] + cell['xmax']) / 2.0, (cell['ymin'] + cell['ymax']) / 2.0)


def _overlaps_rows(cell, other):
    """True when two cells share part of their height (the same table row)."""
    return cell['ymin'] < other['ymax'] and other['ymin'] < cell['ymax']


def _row_cells(cells, header):
    return [cell for cell in cells if _overlaps_rows(cell, header)]


def _rows_below(cells, top, xmin, xmax):
    """Group cells below top (and within xmin..xmax by center) into rows, top first."""
    below = []
    for cell in cells:
        x, y = _center(cell)
        if y < top and xmin <= x <= xmax:
            below.append(cell)
    below.sort(key=lambda cell: -_center(cell)[1])
    rows = []
    for cell in below:
        if rows and any(_overlaps_rows(cell, other) for other in rows[-1]):
            rows[-1].append(cell)
        else:
            rows.append([cell])
    return rows


def _column_bounds(headers):
    """Return (xmin, xmax) covering header centers plus half a column each side."""
    centers = sorted(_center(cell)[0] for cell in headers)
    if len(centers) > 1:
        half = min(b - a for a, b in zip(centers, centers[1:])) / 2.0
    else:
        half = (headers[0]['xmax'] - headers[0]['xmin']) / 2.0
    return centers[0] - half, centers[-1] + half


def _assign(row, columns):
    """Map each cell in row to the nearest column (by center x); join shared cells."""
    values = {}

    def put(key, text):
        text = normalize_text(text)
        values[key] = (values[key] + ' ' + text) if key in values else text

    for cell in sorted(row, key=lambda item: _center(item)[0]):
        # A note spanning several columns holds the row's values separated by
        # tabs or runs of spaces; give them out left to right.
        spanned = sorted((item for item in columns if cell['xmin'] < item[1] < cell['xmax']),
                         key=lambda item: item[1])
        parts = [part for part in re.split(r'\t+|\s{2,}', (cell['text'] or '').strip()) if part]
        if len(spanned) > 1 and len(parts) == len(spanned):
            for (key, _), part in zip(spanned, parts):
                put(key, part)
            continue
        x = _center(cell)[0]
        put(min(columns, key=lambda item: abs(item[1] - x))[0], cell['text'])
    return values


def _header_field(text, table):
    for field, names in table:
        if text in names:
            return field
    return None


# -- Base plate schedule -----------------------------------------------------------

def read_base_plate_schedule(cells):
    """Return ({mark: entry}, [problems]) from the base plate schedule cells.

    Each entry is {'mark', 'type', 'length', 'width', 'thickness' (in),
    'rod_count', 'rod_diameter', 'embed' (in), 'row'} with None for unreadable
    fields. The header row is the row holding a cell reading exactly MARK
    alongside TYPE and a plate dimension.
    """
    cells = split_lines(cells)
    for mark_cell in (cell for cell in cells if normalize_text(cell['text']) == 'MARK'):
        mark_x = _center(mark_cell)[0]
        # Nearest first, so other text at the same height cannot claim a field.
        row = sorted(_row_cells(cells, mark_cell), key=lambda cell: abs(_center(cell)[0] - mark_x))
        columns = []
        headers = []
        for header in row:
            field = _header_field(normalize_text(header['text']), _BASE_PLATE_HEADERS)
            if field and field not in [name for name, _ in columns]:
                columns.append((field, _center(header)[0]))
                headers.append(header)
        names = [name for name, _ in columns]
        if 'type' not in names or 'length' not in names or 'width' not in names:
            continue
        xmin, xmax = _column_bounds(headers)
        top = min(header['ymin'] for header in headers)
        return _read_base_plate_rows(_rows_below(cells, top, xmin, xmax), columns)
    return {}, ['No base plate schedule header (MARK, TYPE, DIM L, DIM W) was found.']


def _read_base_plate_rows(rows, columns):
    entries = {}
    problems = []
    started = False
    for row in rows:
        values = _assign(row, columns)
        mark = values.get('mark', '')
        if not is_mark(mark):
            if started:
                break  # The table ended; text below belongs to notes or details.
            continue
        started = True
        mark = normalize_mark(mark)
        entry = {
            'mark': mark,
            'type': normalize_mark(values.get('type', '')) or None,
            'length': parse_inches(values.get('length')),
            'width': parse_inches(values.get('width')),
            'thickness': parse_inches(values.get('thickness')),
            'rod_count': parse_count(values.get('rod_count')),
            'rod_diameter': parse_inches(values.get('rod_size')),
            'embed': parse_inches(values.get('embed')),
            'row': values,
        }
        missing = [name for name in ('type', 'length', 'width', 'rod_diameter') if not entry[name]]
        if missing:
            problems.append('{}: could not read {}.'.format(mark, ', '.join(missing)))
        if mark in entries:
            problems.append('{}: listed more than once; the first row is used.'.format(mark))
            continue
        entries[mark] = entry
    if not entries:
        problems.append('The base plate schedule header was found but no rows were read.')
    return entries, problems


# -- Anchor rod requirements -------------------------------------------------------

def read_edge_distances(cells):
    """Return {rod diameter (in): edge distance "C" (in)} from the anchor rod table.

    The header row holds a cell starting ANCHOR ROD (the diameter column) and a
    cell containing EDGE DISTANCE. Returns {} when the table is not found.
    """
    cells = split_lines(cells)
    for edge_cell in (cell for cell in cells if 'EDGE' in normalize_text(cell['text'])):
        row = _row_cells(cells, edge_cell)
        rod_cell = next((cell for cell in row
                         if normalize_text(cell['text']).startswith('ANCHOR ROD')
                         and 'RODS' not in normalize_text(cell['text'])), None)
        if rod_cell is None:
            continue
        # The table's columns run from the rod column to the edge distance
        # column; other text at the same height is outside the table.
        left = min(rod_cell['xmin'], edge_cell['xmin'])
        right = max(rod_cell['xmax'], edge_cell['xmax'])
        headers = [cell for cell in row if left <= _center(cell)[0] <= right]
        columns = [('edge', _center(edge_cell)[0]), ('rod', _center(rod_cell)[0])]
        columns += [('other{}'.format(index), _center(cell)[0])
                    for index, cell in enumerate(headers) if cell not in (edge_cell, rod_cell)]
        xmin, xmax = _column_bounds(headers)
        top = min(cell['ymin'] for cell in headers)
        distances = {}
        for row in _rows_below(cells, top, xmin, xmax):
            values = _assign(row, columns)
            rod = parse_inches(values.get('rod'))
            edge = parse_inches(values.get('edge'))
            if rod is None or edge is None:
                if distances:
                    break
                continue
            distances[round(rod, 4)] = edge
        if distances:
            return distances
    return {}


def edge_distance(rod_diameter, table=None):
    """Return the edge distance for a rod diameter, or None when it is not listed."""
    if rod_diameter is None:
        return None
    for source in (table or {}, DEFAULT_EDGE_DISTANCES):
        for diameter, distance in source.items():
            if abs(diameter - rod_diameter) < 1e-3:
                return distance
    return None
