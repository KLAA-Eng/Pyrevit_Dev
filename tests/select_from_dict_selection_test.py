import ast
import os
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_PATH = os.path.join(PROJECT_ROOT, 'lib', 'GUI', 'SelectFromDict.py')


def _dialog_methods():
    """Load the host-independent selection event methods from the GUI source."""
    with open(SOURCE_PATH, 'r', encoding='utf-8', errors='replace') as source_file:
        module = ast.parse(source_file.read(), SOURCE_PATH)
    dialog = next(node for node in module.body
                  if isinstance(node, ast.ClassDef) and node.name == 'SelectFromDict')
    methods = [node for node in dialog.body
               if isinstance(node, ast.FunctionDef)
               and node.name in ('UIe_ItemChecked', 'button_select')]
    namespace = {}
    exec(compile(ast.Module(body=methods, type_ignores=[]), SOURCE_PATH, 'exec'),
         namespace)
    return namespace


class _Item(object):
    def __init__(self, name, element, checked=False):
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
            'Content': type('Content', (), {'Text': 'Wood'})(),
        })()

        methods['UIe_ItemChecked'](dialog, sender, None)

        self.assertFalse(dialog.items[0].IsChecked)
        self.assertTrue(dialog.items[1].IsChecked)


if __name__ == '__main__':
    unittest.main()
