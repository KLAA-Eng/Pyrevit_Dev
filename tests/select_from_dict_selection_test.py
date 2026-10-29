import ast
import os
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_PATH = os.path.join(PROJECT_ROOT, 'lib', 'GUI', 'SelectFromDict.py')


def _dialog_methods(source_path=SOURCE_PATH, class_name='SelectFromDict'):
    """Load the host-independent selection event methods from the GUI source."""
    with open(source_path, 'r', encoding='utf-8', errors='replace') as source_file:
        module = ast.parse(source_file.read(), source_path)
    dialog = next(node for node in module.body
                  if isinstance(node, ast.ClassDef) and node.name == class_name)
    methods = [node for node in dialog.body
               if isinstance(node, ast.FunctionDef)
               and node.name in ('UIe_ItemChecked', 'button_select', 'text_filter_updated',
                                 'generate_list_items', 'button_close', 'button_run')]
    namespace = {'List': _NetList, 'ListItem': _Item}
    exec(compile(ast.Module(body=methods, type_ignores=[]), source_path, 'exec'),
         namespace)
    return namespace


class _NetList(list):
    @classmethod
    def __class_getitem__(cls, item_type):
        return cls

    def Add(self, item):
        self.append(item)


class _Item(object):
    def __init__(self, name='Unnamed', element=None, checked=False):
        self.Name = name
        self.element = element
        self.IsChecked = checked


class _Dialog(object):
    def __init__(self, items, multiple=True):
        self.items = items
        self.SelectMultiple = multiple
        self.selected_items = []
        self.textbox_filter = type('Filter', (), {'Text': 'wood'})()
        self.closed = False

    def Close(self):
        self.closed = True


class SelectFromDictSelectionTests(unittest.TestCase):
    def test_explicit_empty_initial_selection_checks_no_rows(self):
        methods = _dialog_methods()
        dialog = _Dialog([])
        dialog.given_dict_items = {'A': 'a', 'B': 'b'}
        dialog.initial_checked_names = set()

        items = methods['generate_list_items'](dialog)

        self.assertEqual(['A', 'B'], [item.Name for item in items])
        self.assertFalse(any(item.IsChecked for item in items))

    def test_confirm_keeps_checked_items_hidden_by_a_filter(self):
        methods = _dialog_methods()
        dialog = _Dialog([
            _Item('Concrete', 'concrete', checked=True),
            _Item('Wood', 'wood', checked=True),
        ])

        methods['button_select'](dialog, None, None)

        self.assertTrue(dialog.closed)
        self.assertEqual(['concrete', 'wood'], dialog.selected_items)

    def test_single_selection_clears_hidden_checked_item(self):
        methods = _dialog_methods()
        dialog = _Dialog([
            _Item('Concrete', 'concrete', checked=True),
            _Item('Wood', 'wood'),
        ], multiple=False)
        sender = type('Sender', (), {
            'DataContext': dialog.items[1],
        })()

        methods['UIe_ItemChecked'](dialog, sender, None)

        self.assertFalse(dialog.items[0].IsChecked)
        self.assertTrue(dialog.items[1].IsChecked)

    def test_legacy_initial_selection_still_checks_first_sorted_item(self):
        methods = _dialog_methods()
        dialog = _Dialog([])
        dialog.given_dict_items = {'Wood': 'wood', 'Concrete': 'concrete'}
        dialog.initial_checked_names = None
        items = methods['generate_list_items'](dialog)
        self.assertEqual(['Concrete', 'Wood'], [item.Name for item in items])
        self.assertEqual([True, False], [item.IsChecked for item in items])

    def test_room_filter_retains_its_existing_hidden_item_uncheck_policy(self):
        path = os.path.join(PROJECT_ROOT, 'lib', 'GUI', 'Tools', 'CreateFromRooms.py')
        methods = _dialog_methods(path, 'CreateFromRooms')
        items = [_Item('Concrete', 'concrete', True), _Item('Wood', 'wood')]
        dialog = _Dialog(items)
        dialog.main_ListBox = type('ListBox', (), {'ItemsSource': items})()
        methods['text_filter_updated'](dialog, None, None)
        self.assertEqual([items[1]], dialog.main_ListBox.ItemsSource)
        self.assertFalse(items[0].IsChecked)
        dialog.main_ListBox.Items = dialog.main_ListBox.ItemsSource
        sender = type('Sender', (), {'DataContext': items[1]})()
        methods['UIe_ItemChecked'](dialog, sender, None)
        self.assertTrue(items[1].IsChecked)

    def test_room_cancel_closes_and_records_cancellation_without_exiting_the_host(self):
        path = os.path.join(PROJECT_ROOT, 'lib', 'GUI', 'Tools', 'CreateFromRooms.py')
        methods = _dialog_methods(path, 'CreateFromRooms')
        self.assertNotIn('sys', methods['button_close'].__code__.co_names)
        dialog = _Dialog([])
        dialog.cancelled = False
        methods['button_close'](dialog, None, None)
        self.assertTrue(dialog.closed)
        self.assertTrue(dialog.cancelled)

    def test_duplicate_action_closes_before_invoking_the_model_callback(self):
        path = os.path.join(PROJECT_ROOT, 'lib', 'GUI', 'DuplicateSheets.py')
        methods = _dialog_methods(path, 'DuplicateSheets')
        actions = []
        dialog = type('Dialog', (), {})()
        dialog.Close = lambda: actions.append('close')
        dialog._run_handler = lambda: actions.append('run')
        methods['button_run'](dialog, None, None)
        self.assertEqual(['close', 'run'], actions)


if __name__ == '__main__':
    unittest.main()
