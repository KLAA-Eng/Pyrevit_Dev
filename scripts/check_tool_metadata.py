"""Check visible command metadata without loading Revit or command scripts.

This CPython development check accepts the repository's scalar, en_us-localized,
and literal-block YAML metadata forms. It deliberately does not execute Python
or attempt to parse arbitrary YAML.
"""

import ast
import datetime
import io
import os
import re
import sys
import tokenize


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = re.compile(r'^v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:\.[A-Za-z][A-Za-z0-9_-]*)?$')
DATE_FORMAT = '%m.%d.%Y'
DELIVERY_LEDGER = os.path.join(ROOT, 'docs', 'tool-version-delivery-ledger.md')
COMMAND_SUFFIXES = ('.pushbutton', '.smartbutton', '.urlbutton', '.invokebutton',
                    '.linkbutton', '.content')


def read_text(path):
    """Read a UTF-8 repository file, accepting an optional byte-order mark."""
    with io.open(path, 'r', encoding='utf-8-sig') as stream:
        return stream.read()


def _scalar(value):
    """Decode the simple quoted or plain YAML strings used in bundle metadata."""
    value = value.strip()
    if value.startswith('"'):
        result = ast.literal_eval(value)
        if not isinstance(result, str):
            raise ValueError('metadata must be a string')
        return result
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value.startswith(('{', '[', '&', '*', '!', '>', '|')):
        raise ValueError('unsupported metadata YAML form: ' + value)
    return value


def bundle_value(source, key):
    """Return a scalar or English localized bundle field, retaining block lines."""
    lines = source.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r'^' + re.escape(key) + r':\s*(.*)$', line)
        if not match:
            continue
        value = match.group(1)
        indent = 0
        start = index + 1
        if not value:
            for child in range(start, len(lines)):
                if lines[child] and not lines[child][0].isspace():
                    break
                localized = re.match(r'^(\s+)en_us:\s*(.*)$', lines[child])
                if localized:
                    indent = len(localized.group(1))
                    value = localized.group(2)
                    start = child + 1
                    break
            else:
                return ''
            if not value:
                return ''
        if value in ('|', '|-', '|+', '>', '>-', '>+'):
            block = []
            for following in lines[start:]:
                if following.strip() and len(following) - len(following.lstrip()) <= indent:
                    break
                block.append(following)
            widths = [len(item) - len(item.lstrip()) for item in block if item.strip()]
            width = min(widths) if widths else 0
            values = [item[width:] if item.strip() else '' for item in block]
            if value.startswith('>'):
                return ' '.join(values).strip()
            return '\n'.join(values).rstrip()
        return _scalar(value)
    return ''


def script_metadata(source):
    """Inspect literal metadata and module documentation without importing code."""
    tree = ast.parse(source)
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    metadata = {}
    if ast.get_docstring(tree) is not None:
        metadata['__module_docstring__'] = True
    for index, token in enumerate(tokens[:-2]):
        if token.type != tokenize.NAME or token.string not in (
                '__title__', '__version__', '__author__', '__doc__'):
            continue
        if tokens[index + 1].string != '=':
            continue
        name = token.string
        if name in metadata:
            raise ValueError('duplicate metadata assignment: ' + name)
        literal = tokens[index + 2]
        if name in ('__author__', '__doc__'):
            metadata[name] = True
        elif literal.type == tokenize.STRING:
            following = tokens[index + 3]
            if following.type not in (tokenize.NEWLINE, tokenize.COMMENT, tokenize.ENDMARKER):
                raise ValueError(name + ' must be one literal string')
            metadata[name] = ast.literal_eval(literal.string)
        else:
            raise ValueError(name + ' must be one literal string')
    return metadata


def _table_rows(source):
    return [[cell.strip().strip('`') for cell in line.strip().strip('|').split('|')]
            for line in source.splitlines() if line.strip().startswith('|')]


def delivery_dates():
    """Return delivery identifier to mainline date from the canonical ledger."""
    rows = _table_rows(read_text(DELIVERY_LEDGER))
    header = ['main delivery', 'main commit', 'delivery date', 'extension version',
              'tag / release evidence', 'delivery form']
    for index, row in enumerate(rows):
        if [cell.lower() for cell in row] != header:
            continue
        dates = {}
        for candidate in rows[index + 1:]:
            if len(candidate) != 6:
                break
            if candidate[0] and candidate[0] != '---':
                dates[candidate[0]] = candidate[2]
        return dates
    raise ValueError('delivery ledger requires its Main delivery table')


def _valid_date(value):
    try:
        datetime.datetime.strptime(value, DATE_FORMAT)
        return True
    except ValueError:
        return False


def validate_bundle(path):
    """Return actionable errors for one command bundle's static metadata contract."""
    errors = []
    try:
        bundle = read_text(os.path.join(path, 'bundle.yaml'))
        spec = read_text(os.path.join(path, 'SPEC.md'))
        title = bundle_value(bundle, 'title')
        tooltip = bundle_value(bundle, 'tooltip')
        author = bundle_value(bundle, 'author')
        rows = _table_rows(spec)
        identity = {row[0].lower(): row[1] for row in rows if len(row) == 2}
        # Existing SPECs may use labeled identity bullets instead of a table.
        for line in spec.splitlines():
            field = re.match(r'^\s*-\s+(?:\*\*)?(Tool ID|Path aliases|Version inputs|Tool version|Status/origin):'
                             r'(?:\*\*)?\s*(.+)$', line, re.IGNORECASE)
            if field:
                value = field.group(2).strip()
                if field.group(1).lower() == 'tool version':
                    value = value.split()[0].strip('`')
                identity[field.group(1).lower()] = value
        version = identity.get('tool version', '')
        if not VERSION.fullmatch(version):
            errors.append('SPEC Tool version must be a pure vMAJOR.MINOR[.Source] string')
        if not identity.get('status/origin'):
            errors.append('SPEC requires a nonempty Status/origin identity field')
        for field in ('tool id', 'path aliases', 'version inputs'):
            if not identity.get(field):
                errors.append('SPEC requires a nonempty {} identity field'.format(field.title()))
        header = ['version', 'main delivery', 'date', 'meaningful change', 'git evidence']
        header_indexes = [index for index, row in enumerate(rows)
                          if [cell.lower() for cell in row] == header]
        if not header_indexes:
            errors.append('SPEC requires Version | Main delivery | Date | Meaningful change | Git evidence table')
            history = []
        else:
            history = [row for row in rows[header_indexes[0] + 1:]
                       if len(row) == 5 and row[0] != '---']
            current_rows = [row for row in history if row[0] == version and all(row)]
            if len(current_rows) != 1:
                errors.append('SPEC history requires one complete row for the current tool version')
            deliveries = delivery_dates()
            for row in history:
                if not all(row):
                    errors.append('SPEC history rows must be complete')
                    continue
                delivery, history_date = row[1], row[2]
                if not _valid_date(history_date):
                    errors.append('SPEC history Date must be a valid MM.DD.YYYY date')
                if delivery == 'Unreleased':
                    if row[0] != version:
                        errors.append('only the current tool version may be Unreleased')
                elif delivery not in deliveries:
                    errors.append('SPEC Main delivery must exist in the delivery ledger')
                elif history_date != deliveries[delivery]:
                    errors.append('SPEC history Date must match its Main delivery date')
        script_path = os.path.join(path, 'script.py')
        if os.path.isfile(script_path):
            metadata = script_metadata(read_text(script_path))
            if '__module_docstring__' in metadata:
                errors.append('remove script module docstring; it populates __doc__ '
                              'and bundle.yaml owns command help')
            for forbidden in ('__author__', '__doc__'):
                if forbidden in metadata:
                    errors.append('remove script ' + forbidden + '; bundle.yaml owns this metadata')
            if not isinstance(metadata.get('__version__'), str) or not VERSION.fullmatch(metadata['__version__']):
                errors.append('script __version__ must be a pure vMAJOR.MINOR[.Source] string')
            if metadata.get('__version__') != version:
                errors.append('script __version__ must match SPEC Tool version')
            if metadata.get('__title__') != title:
                errors.append('script __title__ must match bundle title (en_us if localized)')
        if not title:
            errors.append('bundle requires title')
        if not author.strip():
            errors.append('bundle requires author')
        tooltip_version = re.search(r'^Version\s*[:=]\s*(\S+)\s*$', tooltip, re.MULTILINE)
        if not tooltip_version or tooltip_version.group(1) != version:
            errors.append('tooltip Version line must match the tool version')
        date = re.search(r'^Date\s*[:=]\s*(\d{2}\.\d{2}\.\d{4})\s*$', tooltip, re.MULTILINE)
        if not date or not _valid_date(date.group(1)):
            errors.append('tooltip Date must be a valid MM.DD.YYYY date')
        status = re.search(r'^Status\s*[:=]\s*(.+?)\s*$', tooltip, re.MULTILINE)
        current_history = [row for row in history if row[0] == version]
        if current_history:
            current_delivery, current_date = current_history[0][1:3]
            if date and date.group(1) != current_date:
                errors.append('tooltip Date must match the current SPEC history row')
            if current_delivery == 'Unreleased':
                if not status or status.group(1) != 'Unreleased':
                    errors.append('tooltip requires Status: Unreleased for a planned version')
            elif status:
                errors.append('tooltip Status is allowed only for an Unreleased version')
        positions = []
        for label in ('Description', 'How-to', 'Last update'):
            section = re.search(r'^' + label + r':\s*$', tooltip, re.MULTILINE | re.IGNORECASE)
            if not section:
                errors.append('tooltip requires ' + label + ': section')
            else:
                positions.append(section.start())
                if label == 'Last update' and not re.search(r'^\s*-\s+\S', tooltip[section.end():], re.MULTILINE):
                    errors.append('tooltip Last update requires a bullet list')
        if positions != sorted(positions):
            errors.append('tooltip sections must be ordered Description, How-to, Last update')
        if re.search(r'^\s*Author\s*[:=]', tooltip, re.MULTILINE | re.IGNORECASE):
            errors.append('tooltip must not contain an Author line')
    except (OSError, ValueError, SyntaxError, tokenize.TokenError) as error:
        errors.append(str(error))
    return errors


def visible_bundles(root):
    """Yield visible commands from either development or release tab layout."""
    for name in ('KL&A Tools_dev.tab', 'KL&A Tools.tab'):
        tab = os.path.join(root, name)
        if not os.path.isdir(tab):
            continue
        for path, directories, _files in os.walk(tab):
            directories[:] = sorted(item for item in directories if not item.startswith('_'))
            if path.endswith(COMMAND_SUFFIXES):
                yield path
                directories[:] = []


def main(root=ROOT):
    """Print failures and return a shell-friendly result code."""
    bundles = list(visible_bundles(root))
    failures = 0
    for path in bundles:
        for error in validate_bundle(path):
            print('{}: {}'.format(os.path.relpath(path, root), error))
            failures += 1
    print('Checked {} visible command bundles; {} error(s).'.format(len(bundles), failures))
    return 1 if failures or not bundles else 0


if __name__ == '__main__':
    sys.exit(main())
