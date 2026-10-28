# -*- coding: utf-8 -*-
"""Minimal PDF text extraction with page positions.

Reads one page's text as positioned words using only the standard library, so
it runs under pyRevit's IronPython 2.7 and CPython alike. It supports what
drawing PDFs use: FlateDecode streams, object streams, incremental updates,
simple and Type0 fonts with ToUnicode maps, and form XObjects. Encrypted PDFs,
Type3 glyph shapes, and text drawn as vector outlines are not readable.

Positions are in PDF user space (points, y up), mapped to the displayed page
by ``page_to_unit`` so callers can scale them to any raster size.
"""

import math
import re
import zlib


# -- Objects -------------------------------------------------------------------

class Name(object):
    __slots__ = ('value',)

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, Name) and other.value == self.value

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return '/' + self.value


class Ref(object):
    __slots__ = ('num', 'gen')

    def __init__(self, num, gen):
        self.num = num
        self.gen = gen


class Stream(object):
    def __init__(self, info, raw):
        self.info = info
        self.raw = raw


class Operator(object):
    __slots__ = ('value',)

    def __init__(self, value):
        self.value = value


class PdfError(Exception):
    """The PDF cannot be read for text."""


_WHITESPACE = b' \t\r\n\x0c\x00'
_DELIMITERS = b'()<>[]{}/%'
_NUMBER = re.compile(br'[+-]?(?:\d+\.?\d*|\.\d+)')
_REGULAR = re.compile(br'[^ \t\r\n\x0c\x00()<>\[\]{}/%]+')
_OBJ_HEADER = re.compile(br'(\d+)\s+(\d+)\s+obj\b')
_HEX_DIGITS = re.compile(br'[^0-9A-Fa-f]')
_ESCAPES = {b'n': b'\n', b'r': b'\r', b't': b'\t', b'b': b'\b', b'f': b'\x0c',
            b'(': b'(', b')': b')', b'\\': b'\\'}


def _char(data, index):
    return data[index:index + 1]


class Lexer(object):
    """Tokenizer for PDF objects and content streams."""

    def __init__(self, data, pos=0):
        self.data = data
        self.pos = pos

    def skip_space(self):
        data, size = self.data, len(self.data)
        while self.pos < size:
            char = _char(data, self.pos)
            if char in _WHITESPACE:
                self.pos += 1
            elif char == b'%':
                end = data.find(b'\n', self.pos)
                self.pos = size if end < 0 else end + 1
            else:
                break

    def _literal_string(self):
        data = self.data
        self.pos += 1
        depth, out = 1, []
        while self.pos < len(data):
            char = _char(data, self.pos)
            if char == b'\\':
                nxt = _char(data, self.pos + 1)
                if nxt in _ESCAPES:
                    out.append(_ESCAPES[nxt])
                    self.pos += 2
                elif nxt.isdigit():
                    digits = re.match(br'[0-7]{1,3}', data[self.pos + 1:self.pos + 4]).group(0)
                    out.append(bytearray([int(digits, 8) & 0xFF]))
                    self.pos += 1 + len(digits)
                elif nxt in (b'\r', b'\n'):
                    self.pos += 2
                    if nxt == b'\r' and _char(data, self.pos) == b'\n':
                        self.pos += 1
                else:
                    out.append(nxt)
                    self.pos += 2
                continue
            if char == b'(':
                depth += 1
            elif char == b')':
                depth -= 1
                if depth == 0:
                    self.pos += 1
                    break
            out.append(char)
            self.pos += 1
        return bytes(b''.join(bytes(part) for part in out))

    def _hex_string(self):
        end = self.data.find(b'>', self.pos)
        digits = _HEX_DIGITS.sub(b'', self.data[self.pos + 1:end])
        self.pos = end + 1
        if len(digits) % 2:
            digits += b'0'
        return bytes(bytearray(int(digits[i:i + 2], 16) for i in range(0, len(digits), 2)))

    def token(self):
        """Return the next raw token, or None at the end."""
        self.skip_space()
        data = self.data
        if self.pos >= len(data):
            return None
        char = _char(data, self.pos)
        if char == b'(':
            return ('str', self._literal_string())
        if char == b'<':
            if _char(data, self.pos + 1) == b'<':
                self.pos += 2
                return ('<<', None)
            return ('str', self._hex_string())
        if char == b'>' and _char(data, self.pos + 1) == b'>':
            self.pos += 2
            return ('>>', None)
        if char in (b'[', b']', b'{', b'}'):
            self.pos += 1
            return (char.decode('latin-1'), None)
        if char == b'/':
            match = _REGULAR.match(data, self.pos + 1)
            self.pos = match.end() if match else self.pos + 1
            raw = match.group(0) if match else b''
            raw = re.sub(br'#([0-9A-Fa-f]{2})', lambda m: bytes(bytearray([int(m.group(1), 16)])), raw)
            return ('name', Name(raw.decode('latin-1')))
        match = _REGULAR.match(data, self.pos)
        if not match:
            self.pos += 1
            return self.token()
        self.pos = match.end()
        word = match.group(0)
        if _NUMBER.match(word) and _NUMBER.match(word).end() == len(word):
            return ('num', float(word) if b'.' in word else int(word))
        return ('op', word.decode('latin-1'))

    def parse(self, tok=None):
        """Parse one object (with N G R references) from the token stream."""
        tok = tok or self.token()
        if tok is None:
            return None
        kind, value = tok
        if kind == 'num' and isinstance(value, int):
            mark = self.pos
            second = self.token()
            if second and second[0] == 'num' and isinstance(second[1], int):
                third = self.token()
                if third == ('op', 'R'):
                    return Ref(value, second[1])
            self.pos = mark
            return value
        if kind in ('num', 'str', 'name'):
            return value
        if kind == '[':
            items = []
            while True:
                tok = self.token()
                if tok is None or tok[0] == ']':
                    return items
                items.append(self.parse(tok))
        if kind == '<<':
            result = {}
            while True:
                tok = self.token()
                if tok is None or tok[0] == '>>':
                    return result
                if tok[0] == 'name':
                    result[tok[1].value] = self.parse()
        if kind == 'op':
            if value == 'true':
                return True
            if value == 'false':
                return False
            if value == 'null':
                return None
            return Operator(value)
        return None


def _decode_stream(stream, resolve):
    filters = resolve(stream.info.get('Filter'))
    if filters is None:
        filters = []
    elif not isinstance(filters, list):
        filters = [filters]
    data = stream.raw
    for name in filters:
        name = resolve(name)
        name = name.value if isinstance(name, Name) else name
        if name in ('FlateDecode', 'Fl'):
            try:
                data = zlib.decompress(data)
            except zlib.error:
                data = zlib.decompressobj().decompress(data)
        else:
            raise PdfError('Unsupported stream filter {}.'.format(name))
    return data


class Document(object):
    """Lazy object table for an unencrypted PDF file."""

    def __init__(self, data):
        if b'/Encrypt' in data[-4096:] or re.search(br'/Encrypt\s', data):
            raise PdfError('Encrypted PDFs cannot be read for text.')
        self.data = data
        self.offsets = {}
        for match in _OBJ_HEADER.finditer(data):
            # Later definitions (incremental updates) replace earlier ones.
            self.offsets[int(match.group(1))] = match.end()
        self.cache = {}
        self.object_streams = None

    def resolve(self, value):
        seen = 0
        while isinstance(value, Ref):
            value = self.get(value.num)
            seen += 1
            if seen > 32:
                return None
        return value

    def get(self, num):
        if num in self.cache:
            return self.cache[num]
        value = None
        if num in self.offsets:
            value = self._parse_at(self.offsets[num])
        else:
            value = self._from_object_streams(num)
        self.cache[num] = value
        return value

    def _parse_at(self, offset):
        lexer = Lexer(self.data, offset)
        value = lexer.parse()
        if isinstance(value, dict):
            mark = lexer.pos
            tok = lexer.token()
            if tok == ('op', 'stream'):
                start = lexer.pos
                if self.data[start:start + 2] == b'\r\n':
                    start += 2
                elif self.data[start:start + 1] in (b'\r', b'\n'):
                    start += 1
                length = self.resolve(value.get('Length'))
                end = start + length if isinstance(length, int) else -1
                if end < 0 or self.data[end:end + 20].strip()[:9] != b'endstream':
                    end = self.data.find(b'endstream', start)
                    while end > start and self.data[end - 1:end] in (b'\r', b'\n'):
                        end -= 1
                return Stream(value, self.data[start:end])
            lexer.pos = mark
        return value

    def stream_data(self, stream):
        return _decode_stream(stream, self.resolve)

    def _from_object_streams(self, num):
        if self.object_streams is None:
            self.object_streams = {}
            for other in list(self.offsets):
                obj = self.get(other)
                if isinstance(obj, Stream) and self.resolve(obj.info.get('Type')) == Name('ObjStm'):
                    try:
                        body = self.stream_data(obj)
                    except Exception:
                        continue
                    first = self.resolve(obj.info.get('First')) or 0
                    count = self.resolve(obj.info.get('N')) or 0
                    header = Lexer(body)
                    pairs = []
                    for _ in range(count):
                        number = header.token()
                        offset = header.token()
                        if not number or not offset:
                            break
                        pairs.append((number[1], offset[1]))
                    for number, offset in pairs:
                        if number not in self.offsets:
                            self.object_streams[number] = (body, first + offset)
        if num in self.object_streams:
            body, offset = self.object_streams[num]
            return Lexer(body, offset).parse()
        return None

    def pages(self):
        """Return page dictionaries in order, with inherited attributes filled in."""
        catalog = None
        for match in re.finditer(br'/Root\s+(\d+)\s+(\d+)\s+R', self.data):
            catalog = self.get(int(match.group(1)))
        if not isinstance(catalog, dict):
            for num in self.offsets:
                obj = self.get(num)
                if isinstance(obj, dict) and obj.get('Type') == Name('Catalog'):
                    catalog = obj
        if not isinstance(catalog, dict):
            raise PdfError('PDF has no page catalog.')
        pages = []
        self._walk(self.resolve(catalog.get('Pages')), {}, pages, 0)
        return pages

    def _walk(self, node, inherited, pages, depth):
        if not isinstance(node, dict) or depth > 64:
            return
        attrs = dict(inherited)
        for key in ('Resources', 'MediaBox', 'CropBox', 'Rotate'):
            if key in node:
                attrs[key] = node[key]
        kids = self.resolve(node.get('Kids'))
        if isinstance(kids, list):
            for kid in kids:
                self._walk(self.resolve(kid), attrs, pages, depth + 1)
        else:
            page = dict(node)
            page.update((key, value) for key, value in attrs.items() if key not in node)
            pages.append(page)


# -- Fonts -----------------------------------------------------------------------

def _hex_int(raw):
    return int(re.sub(br'[^0-9A-Fa-f]', b'', raw) or b'0', 16)


def _utf16(raw):
    digits = re.sub(br'[^0-9A-Fa-f]', b'', raw)
    data = bytes(bytearray(int(digits[i:i + 2], 16) for i in range(0, len(digits) - 1, 2)))
    try:
        return data.decode('utf-16-be')
    except UnicodeDecodeError:
        return u''


def parse_cmap(data):
    """Return {code: unicode text} from a ToUnicode CMap stream."""
    mapping = {}
    for block in re.findall(br'beginbfchar(.*?)endbfchar', data, re.S):
        for src, dst in re.findall(br'<([0-9A-Fa-f\s]+)>\s*<([0-9A-Fa-f\s]*)>', block):
            mapping[_hex_int(src)] = _utf16(dst)
    for block in re.findall(br'beginbfrange(.*?)endbfrange', data, re.S):
        for lo, hi, rest in re.findall(br'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<[0-9A-Fa-f\s]*>|\[[^\]]*\])', block):
            lo, hi = _hex_int(lo), _hex_int(hi)
            if rest.startswith(b'['):
                for offset, dst in enumerate(re.findall(br'<([0-9A-Fa-f\s]*)>', rest)):
                    mapping[lo + offset] = _utf16(dst)
            else:
                base = _utf16(rest[1:-1])
                if not base:
                    continue
                for code in range(lo, min(hi, lo + 0xFFFF) + 1):
                    mapping[code] = base[:-1] + (u'%c' % (ord(base[-1]) + code - lo))
    return mapping


class Font(object):
    def __init__(self, doc, info):
        resolve = doc.resolve
        info = resolve(info) or {}
        subtype = resolve(info.get('Subtype'))
        self.two_byte = subtype == Name('Type0')
        self.to_unicode = {}
        cmap = resolve(info.get('ToUnicode'))
        if isinstance(cmap, Stream):
            try:
                self.to_unicode = parse_cmap(doc.stream_data(cmap))
            except Exception:
                self.to_unicode = {}
        self.widths = {}
        self.default_width = 0.5
        if self.two_byte:
            descendants = resolve(info.get('DescendantFonts')) or [{}]
            cid_font = resolve(descendants[0]) or {}
            self.default_width = (resolve(cid_font.get('DW')) or 1000) / 1000.0
            entries = resolve(cid_font.get('W')) or []
            index = 0
            while index < len(entries):
                first = resolve(entries[index])
                nxt = resolve(entries[index + 1]) if index + 1 < len(entries) else None
                if isinstance(nxt, list):
                    for offset, width in enumerate(nxt):
                        self.widths[first + offset] = resolve(width) / 1000.0
                    index += 2
                else:
                    last = nxt
                    width = resolve(entries[index + 2]) if index + 2 < len(entries) else 1000
                    for code in range(first, (last or first) + 1):
                        self.widths[code] = width / 1000.0
                    index += 3
        else:
            first = resolve(info.get('FirstChar')) or 0
            for offset, width in enumerate(resolve(info.get('Widths')) or []):
                self.widths[first + offset] = (resolve(width) or 0) / 1000.0
            descriptor = resolve(info.get('FontDescriptor')) or {}
            missing = resolve(descriptor.get('MissingWidth'))
            if missing:
                self.default_width = missing / 1000.0

    def codes(self, data):
        raw = bytearray(data)
        if self.two_byte:
            return [raw[i] << 8 | raw[i + 1] for i in range(0, len(raw) - 1, 2)]
        return list(raw)

    def text(self, code):
        if code in self.to_unicode:
            return self.to_unicode[code]
        return u'%c' % code if 32 <= code < 127 else u''

    def width(self, code):
        return self.widths.get(code, self.default_width)


# -- Content interpretation --------------------------------------------------------

def _multiply(m, n):
    a, b, c, d, e, f = m
    a2, b2, c2, d2, e2, f2 = n
    return (a * a2 + b * c2, a * b2 + b * d2,
            c * a2 + d * c2, c * b2 + d * d2,
            e * a2 + f * c2 + e2, e * b2 + f * d2 + f2)


IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


class Glyph(object):
    __slots__ = ('text', 'x', 'y', 'ux', 'uy', 'advance', 'size')

    def __init__(self, text, x, y, ux, uy, advance, size):
        self.text = text
        self.x, self.y = x, y
        self.ux, self.uy = ux, uy
        self.advance = advance
        self.size = size


class _TextState(object):
    def __init__(self):
        self.char_space = 0.0
        self.word_space = 0.0
        self.scale = 1.0
        self.leading = 0.0
        self.font = None
        self.size = 0.0
        self.rise = 0.0


def _number(value):
    return float(value) if isinstance(value, (int, float)) else 0.0


class _Interpreter(object):
    def __init__(self, doc, glyphs):
        self.doc = doc
        self.glyphs = glyphs
        self.font_cache = {}

    def run(self, data, resources, ctm, depth=0):
        if depth > 8:
            return
        resolve = self.doc.resolve
        resources = resolve(resources) or {}
        fonts = resolve(resources.get('Font')) or {}
        xobjects = resolve(resources.get('XObject')) or {}
        state = _TextState()
        stack = []
        tm = tlm = IDENTITY
        lexer = Lexer(data)
        operands = []
        while True:
            tok = lexer.token()
            if tok is None:
                break
            if tok[0] != 'op':
                operands.append(lexer.parse(tok))
                continue
            op = tok[1]
            if op == 'BI':
                end = data.find(b'EI', lexer.pos)
                while end >= 0 and data[end + 2:end + 3] not in _WHITESPACE + b'':
                    end = data.find(b'EI', end + 2)
                lexer.pos = len(data) if end < 0 else end + 2
            elif op in ('true', 'false', 'null'):
                operands.append(None)
                continue
            elif op == 'q':
                stack.append((ctm, state.__dict__.copy()))
            elif op == 'Q':
                if stack:
                    ctm, saved = stack.pop()
                    state.__dict__.update(saved)
            elif op == 'cm' and len(operands) >= 6:
                ctm = _multiply(tuple(_number(v) for v in operands[-6:]), ctm)
            elif op == 'BT':
                tm = tlm = IDENTITY
            elif op == 'Tf' and len(operands) >= 2:
                name = operands[-2]
                key = name.value if isinstance(name, Name) else None
                if key not in self.font_cache:
                    self.font_cache[key] = Font(self.doc, fonts.get(key)) if key in fonts else None
                state.font = self.font_cache[key]
                state.size = _number(operands[-1])
            elif op == 'Tc' and operands:
                state.char_space = _number(operands[-1])
            elif op == 'Tw' and operands:
                state.word_space = _number(operands[-1])
            elif op == 'Tz' and operands:
                state.scale = _number(operands[-1]) / 100.0
            elif op == 'TL' and operands:
                state.leading = _number(operands[-1])
            elif op == 'Ts' and operands:
                state.rise = _number(operands[-1])
            elif op in ('Td', 'TD') and len(operands) >= 2:
                tx, ty = _number(operands[-2]), _number(operands[-1])
                if op == 'TD':
                    state.leading = -ty
                tm = tlm = _multiply((1.0, 0.0, 0.0, 1.0, tx, ty), tlm)
            elif op == 'Tm' and len(operands) >= 6:
                tm = tlm = tuple(_number(v) for v in operands[-6:])
            elif op == 'T*':
                tm = tlm = _multiply((1.0, 0.0, 0.0, 1.0, 0.0, -state.leading), tlm)
            elif op in ('Tj', "'", '"', 'TJ') and operands:
                if op in ("'", '"'):
                    if op == '"' and len(operands) >= 3:
                        state.word_space = _number(operands[-3])
                        state.char_space = _number(operands[-2])
                    tm = tlm = _multiply((1.0, 0.0, 0.0, 1.0, 0.0, -state.leading), tlm)
                items = operands[-1] if op == 'TJ' else [operands[-1]]
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, bytes):
                            tm = self._show(item, state, tm, ctm)
                        elif isinstance(item, (int, float)):
                            shift = -item / 1000.0 * state.size * state.scale
                            tm = _multiply((1.0, 0.0, 0.0, 1.0, shift, 0.0), tm)
            elif op == 'Do' and operands:
                name = operands[-1]
                xobject = resolve(xobjects.get(name.value)) if isinstance(name, Name) else None
                if isinstance(xobject, Stream) and resolve(xobject.info.get('Subtype')) == Name('Form'):
                    matrix = resolve(xobject.info.get('Matrix')) or list(IDENTITY)
                    try:
                        body = self.doc.stream_data(xobject)
                    except PdfError:
                        body = b''
                    self.run(body, xobject.info.get('Resources') or resources,
                             _multiply(tuple(_number(resolve(v)) for v in matrix), ctm), depth + 1)
            operands = []

    def _show(self, data, state, tm, ctm):
        font = state.font
        if font is None or state.size == 0:
            return tm
        for code in font.codes(data):
            trm = _multiply(tm, ctm)
            ux, uy = trm[0], trm[1]
            length = math.hypot(ux, uy) or 1.0
            size = abs(state.size) * math.hypot(trm[2], trm[3])
            origin_x = trm[4] + trm[2] * state.rise
            origin_y = trm[5] + trm[3] * state.rise
            width = font.width(code) * state.size + state.char_space
            if not font.two_byte and code == 32:
                width += state.word_space
            width *= state.scale
            advance = width * length
            text = font.text(code)
            if text:
                self.glyphs.append(Glyph(text, origin_x, origin_y, ux / length, uy / length,
                                         advance, size))
            tm = _multiply((1.0, 0.0, 0.0, 1.0, width, 0.0), tm)
        return tm


# -- Words ---------------------------------------------------------------------------

class Word(object):
    """Text run in page space: start point, unit direction, length, glyph height."""

    def __init__(self, glyphs):
        self.glyphs = glyphs
        # Map each character back to its glyph; a ToUnicode entry may yield several.
        self.char_glyph = []
        for index, glyph in enumerate(glyphs):
            self.char_glyph.extend([index] * len(glyph.text))
        self.text = u''.join(glyph.text for glyph in glyphs)
        first, last = glyphs[0], glyphs[-1]
        self.x, self.y = first.x, first.y
        self.ux, self.uy = first.ux, first.uy
        self.size = max(glyph.size for glyph in glyphs)
        self.length = ((last.x - first.x) * self.ux + (last.y - first.y) * self.uy) + last.advance

    def span(self, start, end):
        """Return the Word for characters start:end of this word's text."""
        return Word(self.glyphs[self.char_glyph[start]:self.char_glyph[end - 1] + 1])

    def center(self):
        # Midpoint along the baseline, raised half the glyph height.
        half = self.length / 2.0
        lift = self.size * 0.35
        return (self.x + self.ux * half - self.uy * lift,
                self.y + self.uy * half + self.ux * lift)

    def __repr__(self):
        return 'Word({!r}, {:.1f}, {:.1f})'.format(self.text, self.x, self.y)


def _direction_groups(glyphs, tolerance_degrees):
    """Group glyphs whose text directions are within tolerance of each other."""
    ordered = sorted(glyphs, key=lambda glyph: math.atan2(glyph.uy, glyph.ux))
    groups, last_angle = [], None
    for glyph in ordered:
        angle = math.degrees(math.atan2(glyph.uy, glyph.ux))
        if last_angle is None or angle - last_angle > tolerance_degrees:
            groups.append([])
        groups[-1].append(glyph)
        last_angle = angle
    return groups


def group_words(glyphs, gap_ratio=0.3, line_ratio=0.3, angle_tolerance=3.0):
    """Join glyphs that continue each other along one baseline into words.

    Glyphs are grouped by direction (within angle_tolerance degrees, since
    drawing exports wobble slightly) and baseline, so drawing order does not
    matter; a gap wider than gap_ratio of the glyph height starts a new word.
    """
    words = []
    for members in _direction_groups(glyphs, angle_tolerance):
        ux = sum(glyph.ux for glyph in members) / len(members)
        uy = sum(glyph.uy for glyph in members) / len(members)
        norm = math.hypot(ux, uy) or 1.0
        ux, uy = ux / norm, uy / norm
        # Along-baseline and across-baseline coordinates for this direction.
        def along(glyph):
            return glyph.x * ux + glyph.y * uy

        def across(glyph):
            return -glyph.x * uy + glyph.y * ux

        members.sort(key=lambda glyph: (round(across(glyph), 1), along(glyph)))
        lines = []
        for glyph in sorted(members, key=across):
            for line in lines:
                if abs(across(glyph) - line[0]) <= line_ratio * max(glyph.size, 0.1):
                    line[1].append(glyph)
                    break
            else:
                lines.append([across(glyph), [glyph]])
        for _, line in lines:
            line.sort(key=along)
            current = []
            for glyph in line:
                if current:
                    previous = current[-1]
                    gap = along(glyph) - (along(previous) + previous.advance)
                    overlap_same = abs(along(glyph) - along(previous)) < 0.01 and glyph.text == previous.text
                    if overlap_same:
                        continue
                    if gap > gap_ratio * max(glyph.size, 0.1) or gap < -0.6 * max(glyph.size, 0.1):
                        _flush(current, words)
                        current = []
                if glyph.text.strip():
                    current.append(glyph)
                elif current:
                    _flush(current, words)
                    current = []
            _flush(current, words)
    return words


def _flush(glyphs, words):
    if glyphs:
        word = Word(glyphs)
        if word.text.strip():
            words.append(word)


# -- Public API ------------------------------------------------------------------------

class PageText(object):
    def __init__(self, words, box, rotate):
        self.words = words
        self.box = box
        self.rotate = rotate

    def page_to_unit(self, x, y):
        """Map a page-space point to (u, v) in 0-1 of the displayed page, v down."""
        x0, y0, x1, y1 = self.box
        u = (x - x0) / (x1 - x0)
        v = (y1 - y) / (y1 - y0)
        rotate = self.rotate % 360
        if rotate == 90:
            return (1.0 - v, u)
        if rotate == 180:
            return (1.0 - u, 1.0 - v)
        if rotate == 270:
            return (v, 1.0 - u)
        return (u, v)

    def display_size(self):
        """Return the displayed page size in points (after /Rotate)."""
        width = self.box[2] - self.box[0]
        height = self.box[3] - self.box[1]
        if self.rotate % 180 == 90:
            return (height, width)
        return (width, height)


def _box(value, resolve):
    value = resolve(value)
    if isinstance(value, list) and len(value) == 4:
        x0, y0, x1, y1 = [_number(resolve(item)) for item in value]
        return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
    return None


def read_page_text(data, page_number=1):
    """Return the PageText for a 1-based page of a PDF given as bytes."""
    doc = Document(data)
    pages = doc.pages()
    if not 1 <= page_number <= len(pages):
        raise PdfError('The PDF has {} page(s); page {} does not exist.'.format(len(pages), page_number))
    page = pages[page_number - 1]
    resolve = doc.resolve
    box = _box(page.get('CropBox'), resolve) or _box(page.get('MediaBox'), resolve) or (0.0, 0.0, 612.0, 792.0)
    rotate = int(_number(resolve(page.get('Rotate')) or 0))
    contents = resolve(page.get('Contents'))
    streams = contents if isinstance(contents, list) else [contents]
    body = b'\n'.join(doc.stream_data(resolve(item)) for item in streams
                      if isinstance(resolve(item), Stream))
    glyphs = []
    _Interpreter(doc, glyphs).run(body, page.get('Resources'), IDENTITY)
    return PageText(group_words(glyphs), box, rotate)


def read_pdf_page_text(path, page_number=1):
    with open(path, 'rb') as pdf_file:
        return read_page_text(pdf_file.read(), page_number)
