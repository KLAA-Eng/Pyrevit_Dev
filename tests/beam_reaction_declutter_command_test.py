from __future__ import print_function

import importlib.util
import os
import sys
import types
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMAND_PATH = os.path.join(
    PROJECT_ROOT,
    'KL&A Tools_dev.tab',
    '05 DevSandbox.panel',
    'Prototype.pulldown',
    'Beam Reaction Declutter.pushbutton',
    'script.py',
)


def load_command_module():
    """Load the command while replacing host-only pyRevit modules."""
    pyrevit = types.ModuleType('pyrevit')
    pyrevit.DB = object()
    pyrevit.forms = object()
    pyrevit.revit = object()
    pyrevit.script = object()
    gui = types.ModuleType('GUI')
    gui_forms = types.ModuleType('GUI.forms')
    gui_forms.select_from_dict = lambda *args, **kwargs: []

    old_modules = {
        name: sys.modules.get(name)
        for name in ('pyrevit', 'GUI', 'GUI.forms')
    }
    sys.modules['pyrevit'] = pyrevit
    sys.modules['GUI'] = gui
    sys.modules['GUI.forms'] = gui_forms
    library_path = os.path.join(PROJECT_ROOT, 'lib')
    sys.path.insert(0, library_path)
    try:
        spec = importlib.util.spec_from_file_location(
            'beam_reaction_declutter_command_test_module', COMMAND_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, previous in old_modules.items():
            if previous is None:
                del sys.modules[name]
            else:
                sys.modules[name] = previous
        sys.path.remove(library_path)


class FakeApplication(object):
    def __init__(self, version_number):
        self.VersionNumber = version_number


class FakeDocument(object):
    def __init__(self, version_number):
        self.Application = FakeApplication(version_number)


class FakeView(object):
    def __init__(self, template=False, allows_overrides=True):
        self.IsTemplate = template
        self.allows_overrides = allows_overrides
        self.Name = 'Level 1'
        self.Id = FakeElementId(42)

    def AreGraphicsOverridesAllowed(self):
        return self.allows_overrides


class FakeElementId(object):
    def __init__(self, value):
        self.Value = value


class FakeCollector(list):
    def OfClass(self, unused_class):
        return self


class FakeDB(object):
    ViewPlan = object()

    def __init__(self, views):
        self.views = views

    def FilteredElementCollector(self, unused_document):
        return FakeCollector(self.views)


class FakeColor(object):
    def __init__(self, red, green, blue):
        self.Red = red
        self.Green = green
        self.Blue = blue


class FakeOverride(object):
    def __init__(self, color):
        self.ProjectionLineColor = color


class BeamReactionDeclutterCommandTests(unittest.TestCase):
    def test_requires_revit_2024_or_newer(self):
        command = load_command_module()

        self.assertTrue(command._is_supported_revit_version(FakeDocument('2024')))
        self.assertTrue(command._is_supported_revit_version(FakeDocument('2026')))
        self.assertFalse(command._is_supported_revit_version(FakeDocument('2023')))
        self.assertFalse(command._is_supported_revit_version(FakeDocument('unknown')))

    def test_eligible_plan_views_excludes_templates_and_unsupported_views(self):
        command = load_command_module()
        expected = FakeView()
        command.DB = FakeDB([expected, FakeView(template=True), FakeView(False, False)])

        self.assertEqual([expected], command._eligible_plan_views(object()))

    def test_cancelled_view_selection_returns_an_empty_scope(self):
        command = load_command_module()
        command._eligible_plan_views = lambda document: [FakeView()]
        command.select_from_dict = lambda *args, **kwargs: []

        self.assertEqual([], command._select_plan_views(object()))

    def test_reset_recognizes_only_the_exact_source_marker(self):
        command = load_command_module()

        self.assertTrue(command._source_marker_override(FakeOverride(FakeColor(254, 0, 0))))
        self.assertFalse(command._source_marker_override(FakeOverride(FakeColor(255, 0, 0))))
        self.assertFalse(command._source_marker_override(FakeOverride(FakeColor(254, 1, 0))))


if __name__ == '__main__':
    unittest.main()
