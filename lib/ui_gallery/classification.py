"""Conservative XAML classification that never loads a XAML UI."""
from __future__ import unicode_literals

import re
from xml.etree import ElementTree


EVENT_ATTRIBUTES = set([
    'Click', 'Checked', 'Unchecked', 'SelectionChanged', 'TextChanged',
    'MouseDown', 'MouseUp', 'MouseMove', 'MouseEnter', 'MouseLeave',
    'KeyDown', 'KeyUp', 'Loaded', 'Closed', 'Closing', 'RequestNavigate',
    'Drop', 'DragEnter', 'DragLeave', 'PreviewMouseDown', 'PreviewKeyDown',
])


def classify_xaml(path):
    """Return display metadata and the reason a source can or cannot preview."""
    try:
        tree = ElementTree.parse(path)
    except (EnvironmentError, ElementTree.ParseError):
        return _result('Unknown', '', False, 'Malformed XAML')

    root = tree.getroot()
    root_kind = _local_name(root.tag)
    title = root.attrib.get('Title', '')
    if root_kind != 'Window':
        return _result(root_kind, title, False, 'Root is {}, not Window'.format(root_kind))

    text = _read_text(path)
    if text is None:
        return _result(root_kind, title, False, 'Unreadable XAML')
    if 'clr-namespace:' in text or 'x:Class=' in text:
        return _result(root_kind, title, False, 'Code namespace reference')
    if re.search(r'\{\s*Binding\b', text):
        return _result(root_kind, title, False, 'Binding expression')
    if re.search(r'\{\s*StaticResource\b', text):
        return _result(root_kind, title, False, 'StaticResource lookup')
    if re.search(r'\{\s*DynamicResource\b', text):
        return _result(root_kind, title, False, 'DynamicResource lookup')

    for element in tree.iter():
        if _local_name(element.tag) == 'ResourceDictionary' and 'Source' in element.attrib:
            return _result(root_kind, title, False, 'External resource dictionary')
        for attribute in element.attrib:
            attribute_name = _local_name(attribute)
            if attribute_name == 'Class':
                return _result(root_kind, title, False, 'Code namespace reference')
            if attribute_name in EVENT_ATTRIBUTES:
                return _result(root_kind, title, False,
                               'Event handler attribute: {}'.format(attribute_name))
    return _result(root_kind, title, True, 'Self-contained Window')


def _result(root_kind, title, is_previewable, reason):
    return {
        'root_kind': root_kind,
        'title': title,
        'is_previewable': is_previewable,
        'reason': reason,
    }


def _local_name(name):
    return name.rsplit('}', 1)[-1]


def _read_text(path):
    try:
        with open(path, 'rb') as source_file:
            return source_file.read().decode('utf-8-sig')
    except (EnvironmentError, UnicodeError):
        return None
