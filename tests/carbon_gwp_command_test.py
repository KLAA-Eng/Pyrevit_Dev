import importlib.util
import os
import sys
import tempfile
import types
import unittest


COMMAND_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'KL&A Tools_dev.tab',
    '05 DevSandbox.panel',
    'Prototype.pulldown',
    'Carbon GWP Pull.pushbutton',
    'script.py',
)


def load_command_module():
    """Load the command with its host-only imports replaced by test doubles."""
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
    library_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
    sys.path.insert(0, library_path)
    try:
        spec = importlib.util.spec_from_file_location('carbon_gwp_command_test_module', COMMAND_PATH)
        module = importlib.util.module_from_spec(spec)
        module.__title__ = 'Carbon GWP Pull'
        spec.loader.exec_module(module)
        return module
    finally:
        for name, previous in old_modules.items():
            if previous is None:
                del sys.modules[name]
            else:
                sys.modules[name] = previous
        sys.path.remove(library_path)


class FakeWorkbook(object):
    def __init__(self):
        self.close_arguments = []
        self.save_count = 0
        self.save_as_paths = []

    def Close(self, save_changes):
        self.close_arguments.append(save_changes)

    def Save(self):
        self.save_count += 1

    def SaveAs(self, path):
        self.save_as_paths.append(path)


class FakeWorkbooks(object):
    def __init__(self, workbook):
        self.workbook = workbook

    def Open(self, path):
        return self.workbook

    def Add(self):
        return self.workbook


class FakeExcel(object):
    def __init__(self, workbook):
        self.Workbooks = FakeWorkbooks(workbook)
        self.quit_called = False

    def Quit(self):
        self.quit_called = True


class CarbonGwpCommandTests(unittest.TestCase):
    def test_failed_export_closes_without_saving_partial_workbook(self):
        command = load_command_module()
        workbook = FakeWorkbook()
        excel = FakeExcel(workbook)
        command._load_excel_application = lambda: excel
        command._schedule_table_grid = lambda schedule: (_ for _ in ()).throw(RuntimeError('read failure'))

        with tempfile.NamedTemporaryFile() as temporary_file:
            with self.assertRaises(RuntimeError):
                command._export_schedules_to_workbook(temporary_file.name, [object()])

        self.assertEqual([False], workbook.close_arguments)
        self.assertEqual(0, workbook.save_count)
        self.assertTrue(excel.quit_called)

    def test_failed_new_export_does_not_create_a_partial_workbook(self):
        command = load_command_module()
        workbook = FakeWorkbook()
        excel = FakeExcel(workbook)
        command._load_excel_application = lambda: excel
        command._schedule_table_grid = lambda schedule: (_ for _ in ()).throw(RuntimeError('read failure'))
        temporary_directory = tempfile.mkdtemp()
        workbook_path = os.path.join(temporary_directory, 'Carbon GWP Export.xlsx')

        try:
            with self.assertRaises(RuntimeError):
                command._export_schedules_to_workbook(workbook_path, [object()])
        finally:
            os.rmdir(temporary_directory)

        self.assertEqual([], workbook.save_as_paths)
        self.assertEqual([False], workbook.close_arguments)
        self.assertTrue(excel.quit_called)


if __name__ == '__main__':
    unittest.main()
