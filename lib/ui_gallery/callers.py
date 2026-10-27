"""Source-backed Gallery callers without importing or executing command code.

Python imports, called functions, and constructed classes are followed. Class
handlers are possible UI callbacks, so constructing a class includes its methods.
This is a conservative static inventory, not proof that a runtime branch ran.
Dynamic imports/getattr and invalid Python sources may require explicit metadata.
"""
from __future__ import unicode_literals

import ast
import io
import os
import re
from xml.etree import ElementTree


_API_NAMES = set([
    'alert', 'ask_for_string', 'ask_for_color', 'pick_file', 'pick_folder',
    'SelectFromList', 'CommandSwitchWindow', 'ProgressBar', 'WarningBar',
    'select_open_docs', 'select_parameters', 'select_revisions', 'select_sheets',
    'select_views', 'show_balloon', 'ask_for_one_item', 'ask_for_number_slider',
])
_BUNDLE_SUFFIXES = ('.pushbutton', '.smartbutton', '.invokebutton')
_XAML_NAMESPACE = 'http://schemas.microsoft.com/winfx/2006/xaml/presentation'
try:
    _STRING_TYPES = (basestring,)
except NameError:
    _STRING_TYPES = (str,)


def canonical_path(path):
    """Use the stable release-tab alias for source/caller identities."""
    value = path.replace('\\', '/')
    prefix = 'KL&A Tools_dev.tab/'
    return 'KL&A Tools.tab/' + value[len(prefix):] if value.startswith(prefix) else value


def _read(path):
    try:
        with io.open(path, 'r', encoding='utf-8-sig') as stream:
            return stream.read()
    except (EnvironmentError, UnicodeError):
        return ''


def _literal(node):
    if hasattr(ast, 'Str') and isinstance(node, ast.Str):
        return node.s
    if hasattr(ast, 'Constant') and isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, _STRING_TYPES) else None
    return None


def _dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted(node.value)
        return parent + '.' + node.attr if parent else ''
    return ''


def _body_nodes(body):
    """Walk one scope, excluding nested function/class bodies."""
    pending = list(body)
    while pending:
        node = pending.pop()
        yield node
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Lambda)):
            pending.extend(ast.iter_child_nodes(node))


class _Scope(object):
    def __init__(self, name, node, body):
        self.name = name
        self.node = node
        self.nodes = list(_body_nodes(body))
        self.imports = {}
        self.assignments = {}
        for item in self.nodes:
            if isinstance(item, ast.Import):
                for alias in item.names:
                    self.imports[alias.asname or alias.name.split('.')[0]] = (
                        alias.name if alias.asname else alias.name.split('.')[0])
            elif isinstance(item, ast.ImportFrom) and item.module:
                for alias in item.names:
                    if alias.name != '*':
                        self.imports[alias.asname or alias.name] = item.module + '.' + alias.name
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        self.assignments[target.id] = item.value


class _Source(object):
    def __init__(self, path, relative_path, text):
        self.path = path
        self.relative_path = relative_path
        self.scopes = {}
        try:
            # Python 2 rejects a Unicode source carrying an encoding cookie.
            tree = ast.parse(text.encode('utf-8'))
        except (SyntaxError, ValueError, TypeError, UnicodeError):
            return
        self._collect('', tree, tree.body)

    def _collect(self, name, node, body):
        self.scopes[name] = _Scope(name, node, body)
        for item in _body_nodes(body):
            if isinstance(item, (ast.FunctionDef, ast.ClassDef)):
                child = name + '.' + item.name if name else item.name
                self._collect(child, item, item.body)


class _Inventory(object):
    def __init__(self, root):
        self.root = os.path.realpath(root)
        self.sources = {}
        self.modules = {}
        self.windows = {}
        self.tools = []
        self.cs_files = []
        for directory, subdirectories, filenames in os.walk(self.root):
            subdirectories[:] = sorted(name for name in subdirectories
                                       if name not in ('.git', '.agents', '.codex', '.klcode',
                                                       'bin', 'obj', '__pycache__')
                                       and not os.path.islink(os.path.join(directory, name)))
            relative_dir = os.path.relpath(directory, self.root).replace(os.sep, '/')
            if any(part.startswith('_') for part in relative_dir.split('/')
                   if part != '__init__.py'):
                # Hidden ribbon templates are not active tools. Library files
                # beginning with underscores are still indexed below.
                if relative_dir.startswith(('KL&A Tools.tab/', 'KL&A Tools_dev.tab/')):
                    subdirectories[:] = []
                    continue
            for filename in sorted(filenames):
                path = os.path.join(directory, filename)
                relative = os.path.relpath(path, self.root).replace(os.sep, '/')
                if os.path.islink(path):
                    continue
                if filename.endswith('.xaml'):
                    try:
                        if ElementTree.parse(path).getroot().tag == '{' + _XAML_NAMESPACE + '}Window':
                            self.windows[os.path.normcase(os.path.normpath(path))] = canonical_path(relative)
                    except (EnvironmentError, ElementTree.ParseError):
                        pass
                elif filename.endswith('.py') and (
                        relative.startswith('lib/') or '.tab/' in relative):
                    source = _Source(path, canonical_path(relative), _read(path))
                    self.sources[path] = source
                    if relative.startswith('lib/'):
                        module = relative[4:-3].replace('/', '.')
                        if module.endswith('.__init__'):
                            module = module[:-9]
                        self.modules[module] = path
                elif filename.endswith('.cs') and relative.startswith('src/'):
                    self.cs_files.append((relative, _read(path)))
            if directory.endswith(_BUNDLE_SUFFIXES) and '.tab/' in relative_dir:
                script = os.path.join(directory, 'script.py')
                bundle_text = _read(os.path.join(directory, 'bundle.yaml'))
                self.tools.append((directory, script, bundle_text))

    def module_path(self, name):
        if name in self.modules:
            return self.modules[name]
        # Legacy GUI code uses bare sibling imports after adding GUI to sys.path.
        suffix = '.' + name
        matches = [path for key, path in self.modules.items() if key.endswith(suffix)]
        return matches[0] if len(matches) == 1 else None

    def resolve(self, source, scope, name, seen=None):
        """Return (source path, scope) for local symbols, or an external name."""
        seen = set() if seen is None else seen
        marker = (source.path, scope.name, name)
        if marker in seen:
            return name
        seen.add(marker)
        parts = name.split('.')
        head = parts[0]
        if head == 'self' and '.' in scope.name:
            name = scope.name.rsplit('.', 1)[0] + '.' + '.'.join(parts[1:])
            if name in source.scopes:
                return (source.path, name)
        if name in source.scopes:
            return (source.path, name)
        for current in (scope, source.scopes.get('')):
            if current and head in current.imports:
                full = current.imports[head]
                if len(parts) > 1:
                    full += '.' + '.'.join(parts[1:])
                return self.resolve_external(full, seen)
            if current and head in current.assignments:
                value = current.assignments[head]
                if isinstance(value, ast.Call):
                    replacement = _dotted(value.func)
                    if replacement and replacement.split('.')[0] != head:
                        suffix = '.' + '.'.join(parts[1:]) if len(parts) > 1 else ''
                        return self.resolve(source, current, replacement + suffix, seen)
        # A class method explicitly named as Class.__init__ can be inherited.
        if len(parts) > 1 and parts[0] in source.scopes:
            class_scope = source.scopes[parts[0]]
            if isinstance(class_scope.node, ast.ClassDef):
                for base in class_scope.node.bases:
                    resolved = self.resolve(source, class_scope, _dotted(base), seen)
                    if isinstance(resolved, tuple):
                        other = self.sources[resolved[0]]
                        method = resolved[1] + '.' + '.'.join(parts[1:])
                        if method in other.scopes:
                            return (other.path, method)
        return name

    def resolve_external(self, full, seen):
        parts = full.split('.')
        for count in range(len(parts), 0, -1):
            path = self.module_path('.'.join(parts[:count]))
            if path:
                source = self.sources[path]
                if '' not in source.scopes:
                    return full
                symbol = '.'.join(parts[count:])
                if not symbol:
                    return (path, '')
                return self.resolve(source, source.scopes[''], symbol, seen)
        return full

    def value(self, source, scope, node, seen=None):
        seen = set() if seen is None else seen
        value = _literal(node)
        if value is not None:
            return value
        if isinstance(node, ast.Name):
            if node.id == '__file__':
                return source.path
            if node.id in seen:
                return None
            seen.add(node.id)
            expression = scope.assignments.get(node.id)
            if expression is None:
                expression = source.scopes[''].assignments.get(node.id)
            return self.value(source, scope, expression, seen) if expression is not None else None
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self.value(source, scope, node.left, set(seen))
            right = self.value(source, scope, node.right, set(seen))
            return left + right if left is not None and right is not None else None
        if isinstance(node, ast.Call):
            name = _dotted(node.func).split('.')[-1]
            values = [self.value(source, scope, arg, set(seen)) for arg in node.args]
            if not values or any(value is None for value in values):
                return None
            if name == 'join':
                return os.path.join(*values)
            if name == 'dirname':
                return os.path.dirname(values[0])
            if name in ('abspath', 'realpath', 'normpath'):
                return os.path.normpath(values[0])
        return None

    def window_key(self, source, value):
        if not value or not value.lower().endswith('.xaml'):
            return None
        paths = [value, os.path.join(os.path.dirname(source.path), value)]
        for path in paths:
            key = os.path.normcase(os.path.normpath(path))
            if key in self.windows:
                return self.windows[key]
        return None

    def class_methods(self, source, scope, seen=None):
        """Collect possible callbacks, respecting subclass method overrides."""
        seen = set() if seen is None else seen
        marker = (source.path, scope.name)
        if marker in seen:
            return {}
        seen.add(marker)
        prefix = scope.name + '.'
        methods = dict((name[len(prefix):], (source.path, name))
                       for name in source.scopes
                       if name.startswith(prefix) and name.count('.') == scope.name.count('.') + 1)
        for base in scope.node.bases:
            resolved = self.resolve(source, scope, _dotted(base))
            if not isinstance(resolved, tuple):
                continue
            other = self.sources[resolved[0]]
            parent = other.scopes.get(resolved[1])
            if parent is not None and isinstance(parent.node, ast.ClassDef):
                for name, method in self.class_methods(other, parent, seen).items():
                    if name not in methods:
                        methods[name] = method
        return methods

    def trace(self, script):
        """Find possible UI calls reachable from a command entry point."""
        result = {}
        queue = [(script, '')]
        visited = set()
        while queue:
            path, scope_name = queue.pop()
            if (path, scope_name) in visited or path not in self.sources:
                continue
            visited.add((path, scope_name))
            source = self.sources[path]
            scope = source.scopes.get(scope_name)
            if scope is None:
                continue
            if isinstance(scope.node, ast.ClassDef):
                queue.extend(self.class_methods(source, scope).values())
            for node in scope.nodes:
                if not isinstance(node, ast.Call):
                    continue
                name = _dotted(node.func)
                resolved = self.resolve(source, scope, name)
                constructor = False
                if isinstance(resolved, tuple):
                    queue.append(resolved)
                    target = self.sources[resolved[0]].scopes.get(resolved[1])
                    constructor = target is not None and isinstance(target.node, ast.ClassDef)
                else:
                    api = _api_key(resolved)
                    if api:
                        result.setdefault(api, set()).add(source.relative_path)
                if constructor or name.endswith(('LoadComponent', 'WPFWindow.__init__', 'WPFWindow')):
                    for arg in node.args:
                        key = self.window_key(source, self.value(source, scope, arg))
                        if key:
                            result.setdefault(key, set()).add(source.relative_path)
        # Include the traversed source path as evidence of shared-helper routing.
        evidence = set(self.sources[path].relative_path for path, name in visited
                       if path in self.sources)
        for key in result:
            result[key].update(evidence)
        return result


def _api_key(name):
    if name.startswith('pyrevit.forms.'):
        member = name[len('pyrevit.forms.'):].split('.')[0]
        return 'pyrevit:' + member if member in _API_NAMES else None
    for member in ('TaskDialog', 'OpenFileDialog', 'SaveFileDialog', 'FolderBrowserDialog'):
        if name.endswith('.' + member) or name.endswith('.' + member + '.Show'):
            return 'native:' + member
    return None


def _tool_title(script_text, bundle_text, folder):
    match = re.search(r'^__title__\s*=\s*([\'"])(.*?)\1', script_text, re.MULTILINE)
    if match:
        return match.group(2).replace('\\n', ' ').strip()
    match = re.search(r'^title:[ \t]*(?:\r?\n[ \t]+en_us:[ \t]*)?([^\r\n]+)', bundle_text, re.MULTILINE)
    if match:
        return match.group(1).strip().strip('\'"')
    return os.path.basename(folder).rsplit('.', 1)[0].replace('_', ' ')


def _compiled_keys(inventory, bundle_text):
    """Match compiled command declarations to their assembly-owned views.

    Compiled commands have no Python entry point. Their assembly identity owns
    the view family; alert use is confirmed by a source reference to KlaAlertWindow.
    """
    match = re.search(r'^assembly:\s*(\S+)', bundle_text, re.MULTILINE)
    if not match:
        return {}
    assembly = match.group(1).strip('\'"')
    if (assembly.startswith('KLCode.FamilyStudio.Revit') and
            re.search(r'^command_class:\s*FamilyStudioCommand\s*$', bundle_text, re.MULTILINE)):
        prefix = 'src/KLCode.FamilyStudio/Revit/'
    elif (assembly.startswith('KLA.ModelStartupImporter.Revit') and
          re.search(r'^command_class:\s*StartupImportCommand\s*$', bundle_text, re.MULTILINE)):
        prefix = 'src/KLA.ModelStartupImporter/'
    else:
        return {}
    keys = dict((key, set()) for key in inventory.windows.values() if key.startswith(prefix))
    evidence = set(path for path, text in inventory.cs_files
                   if path.startswith(prefix) and 'KlaAlertWindow' in text)
    if evidence:
        alert = 'src/KLCode.Wpf/Views/KlaAlertWindow.xaml'
        if alert in inventory.windows.values():
            keys[alert] = evidence
    for member in ('TaskDialog', 'OpenFileDialog', 'SaveFileDialog', 'FolderBrowserDialog'):
        native_evidence = set(path for path, text in inventory.cs_files
                              if path.startswith(prefix) and re.search(
                                  r'\b(?:new\s+)?' + member + r'\s*(?:\(|\.|\{)', text))
        if native_evidence:
            keys['native:' + member] = native_evidence
    return keys


def discover_callers(extension_root):
    """Return deterministic static callers keyed by canonical window/API identity.

    Values contain ``title``, canonical bundle ``path``, ``via`` source evidence,
    and ``confidence='static'``. Hidden ribbon template directories are excluded.
    Invalid/unreadable sources are skipped, not executed or guessed. Callbacks
    and conditional branches represent possible callers, not observed runtime use.
    """
    if not extension_root or not os.path.isdir(extension_root):
        return {}
    inventory = _Inventory(extension_root)
    result = {}
    for folder, script, bundle_text in inventory.tools:
        script_text = _read(script)
        title = _tool_title(script_text, bundle_text, folder)
        tool_path = canonical_path(os.path.relpath(folder, inventory.root))
        targets = _compiled_keys(inventory, bundle_text)
        for filename in ('script.py', 'config.py'):
            entry = os.path.join(folder, filename)
            if entry in inventory.sources:
                for key, evidence in inventory.trace(entry).items():
                    targets.setdefault(key, set()).update(evidence)
        for key, evidence in targets.items():
            result.setdefault(key, []).append({
                'title': title, 'path': tool_path, 'via': sorted(evidence),
                'confidence': 'static',
            })
    for rows in result.values():
        rows.sort(key=lambda row: (row['title'].lower(), row['path'].lower()))
    return result


def callers_for(launcher, caller_index):
    """Return independent caller rows for an existing launcher dictionary."""
    key = launcher.get('caller_key') or launcher.get('relative_path') or ''
    rows = caller_index.get(canonical_path(key), [])
    return [dict(row, via=list(row.get('via', []))) for row in rows]
