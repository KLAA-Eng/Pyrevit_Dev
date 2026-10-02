import sys
import types
import unittest

from lib import excel_com


class DirectWorkbooks(object):
    def __init__(self):
        self.open_calls = []
        self.add_calls = 0

    def Open(self, path, **options):
        self.open_calls.append((path, options))
        return 'opened workbook'

    def Add(self):
        self.add_calls += 1
        return 'new workbook'


class FakeExcel(object):
    def __init__(self, workbooks):
        self.Workbooks = workbooks
        self.quit_calls = 0

    def Quit(self):
        self.quit_calls += 1


class FakeWorkbook(object):
    def __init__(self, fail_close=False):
        self.close_calls = []
        self.fail_close = fail_close

    def Close(self, save_changes):
        self.close_calls.append(save_changes)
        if self.fail_close:
            raise RuntimeError('close failed')


class RawCom(object):
    """Raw IDispatch-shaped fake with intentionally misleading attributes."""
    def __init__(self, name):
        self.name = name
        self.Close = False
        self.Save = False

    def GetType(self):
        return type('RawComType', (), {'FullName': 'System.__ComObject'})()


class ExcelComTests(unittest.TestCase):
    def setUp(self):
        self.original_invoke_member = excel_com._invoke_member
        self.original_get_property = excel_com._get_property
        self.original_set_property = excel_com._set_property
        self.original_missing_value = excel_com._missing_value
        self.original_disable_macros = excel_com._disable_automation_macros
        self.original_restore_macros = excel_com._restore_automation_macros

    def tearDown(self):
        excel_com._invoke_member = self.original_invoke_member
        excel_com._get_property = self.original_get_property
        excel_com._set_property = self.original_set_property
        excel_com._missing_value = self.original_missing_value
        excel_com._disable_automation_macros = self.original_disable_macros
        excel_com._restore_automation_macros = self.original_restore_macros

    def test_explicit_operations_use_direct_pia_objects(self):
        class ItemCollection(object):
            Count = 2
            def __getitem__(self, index):
                return 'item-{}'.format(index)

        class Direct(object):
            Name = 'before'
            def Save(self):
                return 'saved'

        target = Direct()
        collection = ItemCollection()
        self.assertEqual('before', excel_com.get_property(target, 'Name'))
        excel_com.set_property(target, 'Name', 'after')
        self.assertEqual('after', target.Name)
        self.assertEqual('saved', excel_com.call_method(target, 'Save'))
        self.assertEqual('item-2', excel_com.get_item(collection, 2))
        self.assertEqual(2, excel_com.collection_count(collection))

    def test_explicit_operations_use_idispatch_for_every_raw_member(self):
        workbook = RawCom('workbook')
        worksheets = RawCom('worksheets')
        worksheet = RawCom('worksheet')
        calls = []

        def get_property(target, name, arguments=None):
            calls.append(('get', target.name, name, list(arguments or [])))
            values = {
                ('workbook', 'Worksheets'): worksheets,
                ('workbook', 'Range'): worksheet,
                ('worksheets', 'Item'): worksheet,
                ('worksheet', 'Name'): 'DYN Out - Steel',
            }
            return values[(target.name, name)]

        excel_com._get_property = get_property
        excel_com._set_property = lambda target, name, value: calls.append(
            ('set', target.name, name, value))
        excel_com._invoke_member = lambda target, name, arguments: calls.append(
            ('call', target.name, name, list(arguments))) or 'called'

        self.assertIs(worksheets, excel_com.get_property(workbook, 'Worksheets'))
        self.assertIs(worksheet, excel_com.get_item(worksheets, 1))
        self.assertEqual('DYN Out - Steel', excel_com.get_property(worksheet, 'Name'))
        excel_com.set_property(worksheet, 'Name', 'DYN Out - Concrete')
        self.assertEqual('called', excel_com.call_method(workbook, 'Save'))
        self.assertIs(worksheet, excel_com.get_indexed_property(
            workbook, 'Range', 'A1'))
        self.assertIn(('get', 'worksheets', 'Item', [1]), calls)
        self.assertIn(('set', 'worksheet', 'Name', 'DYN Out - Concrete'), calls)
        self.assertIn(('call', 'workbook', 'Save', []), calls)

    def test_range_uses_idispatch_property_get_not_method_in_raw_mode(self):
        worksheet = RawCom('worksheet')
        calls = []
        excel_com._get_property = lambda target, name, arguments=None: calls.append(
            (target, name, list(arguments or []))) or 'range'
        excel_com._invoke_member = lambda *_args: self.fail(
            'Range must not be invoked as a raw COM method')

        value = excel_com.range_at(worksheet, 'A1:B2')

        self.assertEqual('range', value)
        self.assertEqual([(worksheet, 'Range', ['A1:B2'])], calls)

    def test_raw_collection_item_falls_back_to_idispatch_method(self):
        collection = RawCom('queries')
        excel_com._get_property = lambda *_args: (_ for _ in ()).throw(
            RuntimeError('property route rejected'))
        calls = []
        excel_com._invoke_member = lambda target, name, arguments: calls.append(
            (target, name, list(arguments))) or 'query table'

        value = excel_com.get_item(collection, 1)

        self.assertEqual('query table', value)
        self.assertEqual([(collection, 'Item', [1])], calls)

    def test_raw_excel_shape_helpers_use_explicit_optional_arguments(self):
        workbook = RawCom('workbook')
        worksheet = RawCom('worksheet')
        collections = {
            ('worksheet', 'ListObjects'): RawCom('listobjects'),
            ('worksheet', 'UsedRange'): RawCom('usedrange'),
            ('workbook', 'PivotCaches'): RawCom('pivotcaches'),
            ('worksheet', 'ChartObjects'): RawCom('chartobjects'),
        }
        calls = []
        excel_com._missing_value = lambda: 'MISSING'
        def get_property(target, name, arguments=None):
            if (target.name, name) == ('usedrange', 'Address'):
                self.assertEqual(
                    ['MISSING', 'MISSING', 'MISSING', True, 'MISSING'],
                    list(arguments))
                return "'[Smoke]Facade Query'!$A$1:$B$3"
            return collections[(target.name, name)]
        excel_com._get_property = get_property
        excel_com._invoke_member = lambda target, name, arguments: calls.append(
            (target.name, name, list(arguments))) or target

        excel_com.add_list_object(worksheet)
        excel_com.create_pivot_cache(workbook, collections[('worksheet', 'UsedRange')])
        excel_com.add_chart_object(worksheet, 20, 20, 300, 160)

        self.assertIn(
            ('listobjects', 'Add', [1, collections[('worksheet', 'UsedRange')],
                                    'MISSING', 1, 'MISSING']), calls)
        self.assertIn(
            ('pivotcaches', 'Create', [1, "'[Smoke]Facade Query'!$A$1:$B$3",
                                      'MISSING']), calls)
        self.assertIn(
            ('chartobjects', 'Add', [20.0, 20.0, 300.0, 160.0]), calls)

    def test_open_and_add_dispatch_raw_workbooks_without_python_member_access(self):
        workbooks = RawCom('workbooks')
        excel = FakeExcel(workbooks)
        calls = []
        excel_com._missing_value = lambda: 'MISSING'
        excel_com._disable_automation_macros = lambda _excel: 'previous'
        restored = []
        excel_com._restore_automation_macros = lambda _excel, value: restored.append(value)
        excel_com._invoke_member = lambda target, name, arguments: calls.append(
            (target, name, list(arguments))) or name

        self.assertEqual('Open', excel_com.open_workbook(excel, 'book.xlsx', 3, True))
        self.assertEqual('Add', excel_com.add_workbook(excel))
        self.assertEqual('Open', calls[0][1])
        self.assertEqual(['book.xlsx', 3, True], calls[0][2][:3])
        self.assertEqual('Add', calls[1][1])
        self.assertEqual(['MISSING'], calls[1][2])
        self.assertEqual(['previous'], restored)

    def test_close_uses_idispatch_even_when_raw_close_looks_boolean(self):
        workbook = RawCom('workbook')
        excel = FakeExcel(DirectWorkbooks())
        calls = []
        excel_com._invoke_member = lambda target, name, arguments: calls.append(
            (target, name, list(arguments)))

        excel_com.close_excel_application(excel, workbook)

        self.assertEqual([(workbook, 'Close', [False])], calls)
        self.assertEqual(1, excel.quit_calls)

    def test_cleanup_preserves_primary_error_when_requested(self):
        excel = FakeExcel(DirectWorkbooks())
        workbook = FakeWorkbook(fail_close=True)

        errors = excel_com.close_excel_application(excel, workbook, suppress_errors=True)

        self.assertEqual(1, excel.quit_calls)
        self.assertEqual(1, len(errors))
        self.assertIn('Workbook.Close', errors[0])

    def test_idispatch_invocation_converts_python_arguments_to_dotnet_array(self):
        class ArrayFactory(object):
            def __getitem__(self, item_type):
                return lambda values: ('dotnet-array', item_type, list(values))

        captured = []
        class TargetType(object):
            def InvokeMember(self, member, flags, binder, target, arguments):
                captured.append((member, flags, binder, target, arguments))
                return 'reflection result'
        class Target(object):
            def GetType(self):
                return TargetType()

        fake_system = types.ModuleType('System')
        fake_system.Array = ArrayFactory()
        fake_system.Object = 'System.Object'
        fake_reflection = types.ModuleType('System.Reflection')
        fake_reflection.BindingFlags = type('BindingFlags', (), {
            'InvokeMethod': 1, 'Public': 2, 'Instance': 4,
            'OptionalParamBinding': 8,
        })
        old_system = sys.modules.get('System')
        old_reflection = sys.modules.get('System.Reflection')
        sys.modules['System'] = fake_system
        sys.modules['System.Reflection'] = fake_reflection
        try:
            result = excel_com._invoke_member(Target(), 'Open', ['file.xlsx', 3])
        finally:
            if old_system is None:
                del sys.modules['System']
            else:
                sys.modules['System'] = old_system
            if old_reflection is None:
                del sys.modules['System.Reflection']
            else:
                sys.modules['System.Reflection'] = old_reflection

        self.assertEqual('reflection result', result)
        self.assertEqual(('dotnet-array', 'System.Object', ['file.xlsx', 3]), captured[0][4])

    def test_idispatch_property_set_uses_only_set_property_flag(self):
        class ArrayFactory(object):
            def __getitem__(self, item_type):
                return lambda values: ('dotnet-array', item_type, list(values))

        captured = []
        class TargetType(object):
            def InvokeMember(self, member, flags, binder, target, arguments):
                captured.append((member, flags, arguments))
        class Target(object):
            def GetType(self):
                return TargetType()

        fake_system = types.ModuleType('System')
        fake_system.Array = ArrayFactory()
        fake_system.Object = 'System.Object'
        fake_reflection = types.ModuleType('System.Reflection')
        fake_reflection.BindingFlags = type('BindingFlags', (), {
            'SetProperty': 1, 'PutDispProperty': 2, 'Public': 4, 'Instance': 8,
        })
        old_system = sys.modules.get('System')
        old_reflection = sys.modules.get('System.Reflection')
        sys.modules['System'] = fake_system
        sys.modules['System.Reflection'] = fake_reflection
        try:
            excel_com._set_property(Target(), 'Name', 'Facade Data')
        finally:
            if old_system is None:
                del sys.modules['System']
            else:
                sys.modules['System'] = old_system
            if old_reflection is None:
                del sys.modules['System.Reflection']
            else:
                sys.modules['System.Reflection'] = old_reflection

        self.assertEqual('Name', captured[0][0])
        self.assertEqual(13, captured[0][1])
        self.assertEqual(('dotnet-array', 'System.Object', ['Facade Data']), captured[0][2])


if __name__ == '__main__':
    unittest.main()
