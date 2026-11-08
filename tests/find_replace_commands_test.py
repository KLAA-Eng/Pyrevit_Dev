"""The real command adapters map shared fields to model targets and host owner."""
import importlib.util
import os
import sys
import types
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))


class View(object):
    pass


class ViewSheet(View):
    pass


class Collector(object):
    def __init__(self, doc):
        self.doc = doc

    def OfClass(self, kind):
        return self

    def ToElements(self):
        return self.doc.elements


def load_command(folder):
    db = types.ModuleType('Autodesk.Revit.DB')
    db.BuiltInCategory = object()
    db.FilteredElementCollector = Collector
    db.View = View
    db.ViewSheet = ViewSheet
    api = types.ModuleType('pyrevit.api')
    api.AdWindows = type('AdWindows', (), {'ComponentManager':
        type('Manager', (), {'ApplicationWindow': 42})()})()
    tools = types.ModuleType('GUI.tool_dialogs')
    selection = types.ModuleType('Snippets._selection')
    selection.select_from_dict = lambda *args, **kwargs: []
    selection.get_selected_sheets = lambda **kwargs: kwargs['given_uidoc'].Document.elements
    batch = types.ModuleType('find_replace.revit_batch')
    batch.apply_batch = lambda *args: None
    modules = {'Autodesk': types.ModuleType('Autodesk'),
               'Autodesk.Revit': types.ModuleType('Autodesk.Revit'),
               'Autodesk.Revit.DB': db, 'pyrevit': types.ModuleType('pyrevit'),
               'pyrevit.api': api, 'GUI.tool_dialogs': tools,
               'Snippets': types.ModuleType('Snippets'), 'Snippets._selection': selection,
               'find_replace.revit_batch': batch}
    path = os.path.join(ROOT, 'KL&A Tools_dev.tab', '03 Core Tools.panel',
                        'Rename.pulldown', folder, 'script.py')
    spec = importlib.util.spec_from_file_location('rename_command_under_test', path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


class CommandTests(unittest.TestCase):
    def element(self):
        element = ViewSheet()
        element.Name, element.SheetNumber = 'Plan', 'A1'
        element.Id = type('Id', (), {'IntegerValue': 1})()
        return element

    def test_views_adapter_passes_name_group_and_native_owner(self):
        command = load_command('FindReplace - Views.pushbutton')
        element = self.element()
        command.selected_views = lambda uidoc: [element]
        def run(title, version, items, fields, plan, execute, **options):
            self.assertEqual(['name'], [field.Key for field in fields])
            self.assertEqual(42, options['owner'])
            request = dict(operation='upper', field='name')
            self.assertEqual([('Name', 'PLAN')], plan(items, request)[0]['changes'])
            return 'finished'
        command.run = run
        uidoc = type('UIDoc', (), {'Document': object()})()
        self.assertEqual('finished', command.main(uidoc))

    def test_sheets_adapter_maps_number_and_name_with_atomic_changes(self):
        command = load_command('FindReplace_Sheets.pushbutton')
        element = self.element()
        doc = type('Doc', (), {'elements': [element]})()
        def run(title, version, items, fields, plan, execute, **options):
            self.assertEqual(['number', 'name'], [field.Key for field in fields])
            self.assertEqual([False, True], [field.AllowCase for field in fields])
            self.assertEqual(42, options['owner'])
            self.assertIs(command.update_project_browser, options['after_change'])
            request = dict(operation='rename', fields={
                'number': dict(find='A', replace='B', prefix='', suffix=''),
                'name': dict(find='', replace='', prefix='New ', suffix='')})
            self.assertEqual([('Name', 'New Plan'), ('SheetNumber', 'B1')],
                             plan(items, request)[0]['changes'])
            return 'finished'
        command.run = run
        self.assertEqual('finished', command.main(type('UIDoc', (), {'Document': doc})()))


if __name__ == '__main__':
    unittest.main()
