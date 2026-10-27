"""Exercise the built-in adapter contract without a Revit document."""
from __future__ import unicode_literals

import sys
import types
import unittest
from unittest.mock import patch

from lib.ui_gallery.builtin import launch_builtin, picker_names


class BuiltinPreviewTests(unittest.TestCase):
    def test_selector_states_have_empty_and_long_samples(self):
        self.assertEqual([], picker_names('pyrevit-select-sheets', 'Empty'))
        names = picker_names('pyrevit-select-sheets', 'Long content')
        self.assertEqual(45, len(names))
        self.assertTrue(all(len(name) > 100 for name in names))

    def test_model_picker_uses_only_shared_list_window_and_disables_actions(self):
        windows = []

        class ListWindow(object):
            def __init__(self, options, **kwargs):
                self.options = options
                self.kwargs = kwargs
                self.list_lb = types.SimpleNamespace(IsEnabled=True)
                self.select_b = types.SimpleNamespace(IsEnabled=True)
                self.shown = False
                windows.append(self)

            def ShowDialog(self):
                self.shown = True

        forms = types.SimpleNamespace(SelectFromList=ListWindow, XAML_FILES_DIR='installed/forms',
                                      TemplateListItem=lambda item, **kwargs: types.SimpleNamespace(item=item))
        utils = types.SimpleNamespace(load_ctrl_template=lambda path: 'installed parameter template')
        with patch.dict(sys.modules, {'pyrevit': types.SimpleNamespace(forms=forms),
                                     'pyrevit.forms': types.SimpleNamespace(utils=utils)}):
            result = launch_builtin(dict(id='pyrevit-select-parameters', title='Parameters',
                                         can_launch=True, states=['Disabled']), 'Disabled')
        self.assertTrue(windows[0].shown)
        self.assertFalse(windows[0].select_b.IsEnabled)
        self.assertFalse(windows[0].list_lb.IsEnabled)
        self.assertEqual('Mark [Instance]', windows[0].options['All Parameters'][0].item.name)
        self.assertEqual(2, len(windows[0].options['Instance Parameters']))
        self.assertEqual(1, len(windows[0].options['Type Parameters']))
        self.assertEqual('installed parameter template', windows[0].kwargs['item_template'])
        self.assertIn('discarded', result)

    def test_native_picker_result_is_not_read_or_opened(self):
        calls = []
        def choose_file(**kwargs):
            calls.append(kwargs)
            return object()
        forms = types.SimpleNamespace(pick_file=choose_file)
        with patch.dict(sys.modules, {'pyrevit': types.SimpleNamespace(forms=forms)}):
            result = launch_builtin(dict(id='pyrevit-pick-file', can_launch=True,
                                         states=['Normal']))
        self.assertEqual(1, len(calls))
        self.assertIn('discarded', result)

    def test_disabled_and_unsupported_states_are_rejected_before_host_import(self):
        for entry, state in [(dict(can_launch=False), 'Normal'),
                             (dict(can_launch=True, states=['Normal']), 'Error')]:
            with self.assertRaises(ValueError):
                launch_builtin(entry, state)


if __name__ == '__main__':
    unittest.main()
