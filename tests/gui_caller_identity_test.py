"""Every shared-shell caller passes its real tool identity, never a placeholder.

The footer renders only a pure ``vMAJOR.MINOR`` version; anything else becomes an
empty footer. This scan runs under CPython without a host and fails on the exact
call sites that would ship a blank footer or a literal ``__title__`` header.
"""
import ast
import io
import os
import re
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_ROOTS = ('lib', 'KL&A Tools_dev.tab', 'KL&A Tools.tab')
SKIP_PARTS = ('ui_gallery', '__pycache__')
SHELL_CALLS = ('select_from_dict', 'load_window', 'start', 'select_group_types',
               'select_attached_groups', 'get_selected_views', 'get_selected_sheets',
               'select_title_block')
VERSION_LITERAL = re.compile(r'^[vV]?\d+\.\d+')
PLACEHOLDER_TITLES = ('__title', '__title__', '')


def _python_sources():
    for root_name in SCAN_ROOTS:
        root = os.path.join(PROJECT_ROOT, root_name)
        for directory, folders, files in os.walk(root):
            folders[:] = [name for name in folders if name not in SKIP_PARTS]
            for name in files:
                if name.endswith('.py'):
                    yield os.path.join(directory, name)


def _read(path):
    with io.open(path, 'r', encoding='utf-8', errors='replace') as handle:
        return handle.read()


def _string(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _call_name(node):
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


class CallerIdentityScan(object):
    """Collect version/title arguments from shell calls and function defaults."""
    def __init__(self):
        self.problems = []

    def scan(self, path, source):
        relative = os.path.relpath(path, PROJECT_ROOT)
        try:
            tree = ast.parse(source, path)
        except SyntaxError:
            self._scan_text(relative, source)
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _call_name(node) in SHELL_CALLS:
                for keyword in node.keywords:
                    self._check(relative, node.lineno, keyword.arg, _string(keyword.value))
            elif isinstance(node, ast.FunctionDef):
                names = [arg.arg for arg in node.args.args]
                defaults = node.args.defaults
                for arg, default in zip(names[len(names) - len(defaults):], defaults):
                    self._check(relative, node.lineno, arg, _string(default))

    def _scan_text(self, relative, source):
        for number, line in enumerate(source.splitlines(), 1):
            for match in re.finditer(r"\b(version|title)\s*=\s*(['\"])(.*?)\2", line):
                self._check(relative, number, match.group(1), match.group(3))

    def _check(self, relative, line, name, value):
        if value is None:
            return
        if name == 'version' and not VERSION_LITERAL.match(value):
            self.problems.append('{}:{} version={!r} renders an empty footer'.format(relative, line, value))
        if name == 'title' and value.strip() in PLACEHOLDER_TITLES:
            self.problems.append('{}:{} title={!r} is a placeholder'.format(relative, line, value))


class CallerIdentityTests(unittest.TestCase):
    def test_no_shell_caller_passes_a_placeholder_title_or_a_non_version(self):
        scan = CallerIdentityScan()
        for path in _python_sources():
            scan.scan(path, _read(path))
        self.assertEqual([], scan.problems, '\n'.join(scan.problems))

    def test_scan_recognises_the_shapes_that_shipped_blank_footers(self):
        scan = CallerIdentityScan()
        scan.scan(os.path.join(PROJECT_ROOT, 'lib', 'sample.py'),
                  "def helper(title='__title__', version='Version 0.1'):\n"
                  "    select_from_dict({}, title=title, version='Core Tools')\n"
                  "    load_window(w, 'x.xaml', 'Tool', version=__version__)\n"
                  "    select_from_dict({}, title='Pick', version='v1.2')\n")
        self.assertEqual(3, len(scan.problems), scan.problems)

    def test_scan_falls_back_to_text_for_ironpython_only_syntax(self):
        scan = CallerIdentityScan()
        scan.scan(os.path.join(PROJECT_ROOT, 'lib', 'legacy.py'),
                  "print 'legacy'\nselect_from_dict(d, title='__title__', version='Version: _')\n")
        self.assertEqual(2, len(scan.problems), scan.problems)


if __name__ == '__main__':
    unittest.main()
