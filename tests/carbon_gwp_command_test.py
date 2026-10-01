import importlib.util
import os
import sys
import tempfile
import types
import unittest


COMMAND_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'KL&A Tools.tab',
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
        self.open_arguments = []

    def Open(self, path, **kwargs):
        self.open_arguments.append((path, kwargs))
        return self.workbook

    def Add(self):
        return self.workbook


class FakeExcel(object):
    def __init__(self, workbook):
        self.Workbooks = FakeWorkbooks(workbook)
        self.quit_called = False
        self.async_calculation_count = 0
        self.full_rebuild_count = 0

    def CalculateUntilAsyncQueriesDone(self):
        self.async_calculation_count += 1

    def CalculateFullRebuild(self):
        self.full_rebuild_count += 1

    def Quit(self):
        self.quit_called = True


class FakeExportWorksheet(object):
    def __init__(self):
        self.UsedRange = type('UsedRange', (), {
            'Rows': type('Rows', (), {'Count': 4})(),
            'Columns': type('Columns', (), {'Count': 2})(),
            'Value2': (
                ('ConcreteGWP', 395259),
                ('MasonryGWP', 0),
                ('SteelGWP', 29935.354),
                ('WoodGWP', 7947.74),
            ),
        })()


class FakeExportWorkbook(FakeWorkbook):
    def __init__(self):
        FakeWorkbook.__init__(self)
        self.refresh_count = 0
        self.updated_links = []
        self.Worksheets = type('Worksheets', (), {
            'Item': lambda _self, _name: FakeExportWorksheet(),
        })()

    def RefreshAll(self):
        self.refresh_count += 1

    def LinkSources(self):
        return ('container.xlsx',)

    def UpdateLink(self, links):
        self.updated_links.append(links)


class FakeQueryTable(object):
    def __init__(self):
        self.BackgroundQuery = True
        self.Refreshing = False


class FakeQueryWorksheet(object):
    def __init__(self):
        self.QueryTables = [FakeQueryTable()]
        self.ListObjects = []


class FakeMaterialAccuracyWorksheet(object):
    def __init__(self, name, na_cells=None):
        self.Name = name
        self.na_cells = na_cells or []

    def Evaluate(self, formula):
        return formula[5:-1] in self.na_cells


class FakeWorksheets(object):
    def __init__(self, worksheets):
        self.worksheets = worksheets
        self.Count = len(worksheets)

    def __getitem__(self, index):
        return self.worksheets[index - 1]


class FakeForms(object):
    def __init__(self):
        self.alerts = []

    def alert(self, message, **kwargs):
        self.alerts.append((message, kwargs))


class FakeOutput(object):
    def __init__(self):
        self.markdown = []
        self.tables = []

    def print_md(self, text):
        self.markdown.append(text)

    def print_table(self, rows, columns):
        self.tables.append((rows, columns))


class CarbonGwpCommandTests(unittest.TestCase):
    def test_chart_png_paths_are_saved_beside_post_processing_workbook(self):
        command = load_command_module()
        workbook_path = os.path.join(r'C:\Projects\Carbon', 'Post-Processing.xlsx')

        self.assertEqual(
            os.path.join(r'C:\Projects\Carbon', 'Carbon GWP Summary.png'),
            command._chart_png_path(workbook_path, 'gwp'))
        self.assertEqual(
            os.path.join(
                r'C:\Projects\Carbon',
                'Carbon Material Volume Summary.png'),
            command._chart_png_path(workbook_path, 'volume'))
        with self.assertRaises(ValueError):
            command._chart_png_path(workbook_path, 'unsupported')

    def test_workbook_picker_titles_match_the_two_workbook_roles(self):
        command = load_command_module()

        self.assertEqual('Select Export Container',
                         command.EXPORT_WORKBOOK_PICKER_TITLE)
        self.assertEqual('Select Post-processing',
                         command.POST_PROCESSING_WORKBOOK_PICKER_TITLE)

    def test_local_model_folder_starts_first_workbook_picker(self):
        command = load_command_module()
        model_folder = tempfile.mkdtemp()
        try:
            document = type('Document', (), {
                'IsModelInCloud': False,
                'IsWorkshared': False,
                'PathName': os.path.join(model_folder, 'Project.rvt'),
            })()
            self.assertEqual(
                model_folder,
                command._model_workbook_folder(document, r'G:\_Carbon\fallback.xlsx'),
            )
        finally:
            os.rmdir(model_folder)

    def test_cloud_model_keeps_configured_folder_as_first_picker_fallback(self):
        command = load_command_module()
        cloud_folder = tempfile.mkdtemp()
        document = type('Document', (), {'IsModelInCloud': True})()
        original_cloud_folder = command.CLOUD_MODEL_WORKBOOK_FOLDER
        try:
            command.CLOUD_MODEL_WORKBOOK_FOLDER = cloud_folder
            self.assertEqual(
                cloud_folder,
                command._model_workbook_folder(document, r'G:\_Carbon\fallback.xlsx'),
            )
        finally:
            command.CLOUD_MODEL_WORKBOOK_FOLDER = original_cloud_folder
            os.rmdir(cloud_folder)

    def test_cloud_model_uses_local_profile_when_library_folder_is_unavailable(self):
        command = load_command_module()
        document = type('Document', (), {'IsModelInCloud': True})()
        original_cloud_folder = command.CLOUD_MODEL_WORKBOOK_FOLDER
        try:
            command.CLOUD_MODEL_WORKBOOK_FOLDER = r'J:\Not Available\Carbon GWP'
            expected = os.environ.get('USERPROFILE')
            if not expected or not os.path.isdir(expected):
                expected = os.environ.get('SystemDrive', 'C:') + os.sep
            self.assertEqual(
                expected,
                command._model_workbook_folder(document, r'G:\_Carbon\fallback.xlsx'),
            )
        finally:
            command.CLOUD_MODEL_WORKBOOK_FOLDER = original_cloud_folder

    def test_workshared_model_uses_central_model_folder(self):
        command = load_command_module()
        central_folder = tempfile.mkdtemp()
        original_db = command.DB
        try:
            central_path = os.path.join(central_folder, 'Central.rvt')
            command.DB = type('DB', (), {
                'ModelPathUtils': type('ModelPathUtils', (), {
                    'ConvertModelPathToUserVisiblePath': staticmethod(
                        lambda _path: central_path),
                }),
            })()
            document = type('Document', (), {
                'IsModelInCloud': False,
                'IsWorkshared': True,
                'GetWorksharingCentralModelPath': lambda _self: object(),
                'PathName': r'C:\Users\example\AppData\Local\Project_local.rvt',
            })()
            self.assertEqual(
                central_folder,
                command._model_workbook_folder(document, r'G:\_Carbon\fallback.xlsx'),
            )
        finally:
            command.DB = original_db
            os.rmdir(central_folder)

    def test_target_sheet_name_ignores_case(self):
        command = load_command_module()

        self.assertTrue(command._is_target_sheet_name('SYNC TO CENTRAL'))
        self.assertTrue(command._is_target_sheet_name('sync to central'))
        self.assertTrue(command._is_target_sheet_name('Sync To Central'))
        self.assertFalse(command._is_target_sheet_name('SYNC TO CENTRAL - COPY'))

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

    def test_export_read_updates_formula_links_before_charting_rows(self):
        command = load_command_module()
        workbook = FakeExportWorkbook()
        excel = FakeExcel(workbook)
        command._load_excel_application = lambda: excel
        command._worksheet_by_name = lambda _book, _name: FakeExportWorksheet()

        rows = command._read_export_rows('post-processing.xlsx')

        self.assertEqual(4, len(rows))
        self.assertEqual(1, workbook.refresh_count)
        self.assertEqual([('container.xlsx',)], workbook.updated_links)
        self.assertEqual(1, excel.async_calculation_count)
        self.assertEqual(1, excel.full_rebuild_count)
        self.assertEqual(
            {'UpdateLinks': 3, 'ReadOnly': True},
            excel.Workbooks.open_arguments[0][1],
        )

    def test_export_read_stops_when_refresh_fails(self):
        command = load_command_module()
        workbook = FakeExportWorkbook()
        excel = FakeExcel(workbook)
        command._load_excel_application = lambda: excel

        def fail_refresh():
            raise RuntimeError('refresh failed')

        workbook.RefreshAll = fail_refresh

        with self.assertRaises(RuntimeError):
            command._read_export_rows('post-processing.xlsx')

        self.assertEqual([False], workbook.close_arguments)
        self.assertTrue(excel.quit_called)

    def test_export_read_stops_when_link_update_fails(self):
        command = load_command_module()
        workbook = FakeExportWorkbook()
        excel = FakeExcel(workbook)
        command._load_excel_application = lambda: excel

        def fail_link_update(_links):
            raise RuntimeError('link update failed')

        workbook.UpdateLink = fail_link_update

        with self.assertRaises(RuntimeError):
            command._read_export_rows('post-processing.xlsx')

        self.assertEqual([False], workbook.close_arguments)
        self.assertTrue(excel.quit_called)

    def test_export_read_stops_when_async_calculation_fails(self):
        command = load_command_module()
        workbook = FakeExportWorkbook()
        excel = FakeExcel(workbook)
        command._load_excel_application = lambda: excel

        def fail_async_calculation():
            raise RuntimeError('async calculation failed')

        excel.CalculateUntilAsyncQueriesDone = fail_async_calculation

        with self.assertRaises(RuntimeError):
            command._read_export_rows('post-processing.xlsx')

        self.assertEqual([False], workbook.close_arguments)
        self.assertTrue(excel.quit_called)

    def test_query_refresh_is_made_foreground_without_saving_workbook(self):
        command = load_command_module()
        worksheet = FakeQueryWorksheet()
        workbook = type('Workbook', (), {
            'Connections': [],
            'Worksheets': [worksheet],
        })()

        command._make_query_refresh_foreground(workbook)

        self.assertFalse(worksheet.QueryTables[0].BackgroundQuery)
        self.assertFalse(command._query_refresh_is_running(workbook))

    def test_material_accuracy_check_lists_only_actual_excel_na_errors(self):
        command = load_command_module()
        worksheet = FakeMaterialAccuracyWorksheet(
            'post-processing', na_cells=['F46', 'F50'])
        workbook = type('Workbook', (), {
            'Worksheets': FakeWorksheets([worksheet]),
        })()

        result = command._material_accuracy_check(workbook)

        self.assertEqual('completed', result['status'])
        self.assertEqual(['F46', 'F50'], result['cells'])
        self.assertEqual('Post-Processing', result['sheet'])

    def test_material_accuracy_check_reports_unavailable_when_sheet_is_missing(self):
        command = load_command_module()
        workbook = type('Workbook', (), {
            'Worksheets': FakeWorksheets([
                FakeMaterialAccuracyWorksheet('Post-Processing v2'),
            ]),
        })()

        result = command._material_accuracy_check(workbook)

        self.assertEqual('unavailable', result['status'])
        self.assertIn('Worksheet not found', result['reason'])

    def test_material_accuracy_warning_confirms_chart_update_and_locations(self):
        command = load_command_module()
        fake_forms = FakeForms()
        command.forms = fake_forms

        command._show_material_accuracy_warning({
            'status': 'completed',
            'sheet': 'Post-Processing',
            'range': 'F41:F70',
            'cells': ['F46', 'F50'],
            'reason': '',
        })

        self.assertEqual(1, len(fake_forms.alerts))
        self.assertIn('chart update completed', fake_forms.alerts[0][0])
        self.assertIn('2 #N/A result(s)', fake_forms.alerts[0][0])
        self.assertIn('Post-Processing!F41:F70', fake_forms.alerts[0][0])

    def test_report_uses_project_facing_chart_and_skipped_row_columns(self):
        command = load_command_module()
        output = FakeOutput()
        chart_results = [{
            'name': 'Embodied Carbon',
            'unit': u'kgCO\u2082e',
            'total': 1250.0,
            'action': 'updated',
            'slices': [{
                'row': 1,
                'source_name': 'ConcreteGWP',
                'display_label': 'Concrete',
                'value': 1200.4,
            }],
            'skipped': [{
                'row': 2,
                'source_name': 'MasonryGWP',
                'display_label': 'Masonry',
                'reason': 'non-positive GWP value',
                'value': '0',
            }],
        }]

        command._print_report(output, {
            'export_workbook': 'container.xlsx',
            'post_processing_workbook': 'post.xlsx',
            'target_sheet': 'SYNC TO CENTRAL',
        }, [], chart_results)

        self.assertEqual(
            ['Row', 'Source', 'Material', u'kgCO\u2082e'],
            output.tables[0][1])
        self.assertEqual([[1, 'ConcreteGWP', 'Concrete', '1200.40']],
                         output.tables[0][0])
        self.assertEqual(['Row', 'Source', 'Material', 'Reason'],
                         output.tables[1][1])
        self.assertEqual(
            [[2, 'MasonryGWP', 'Masonry', 'non-positive GWP value']],
            output.tables[1][0])


if __name__ == '__main__':
    unittest.main()
