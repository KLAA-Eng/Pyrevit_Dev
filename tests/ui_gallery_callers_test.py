"""Behavioral coverage for source-only Gallery caller discovery."""
from __future__ import unicode_literals

import io
import os
import shutil
import sys
import tempfile
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lib.ui_gallery.callers import discover_callers


class CallerDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def write(self, relative_path, text):
        path = os.path.join(self.root, relative_path)
        parent = os.path.dirname(path)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        with io.open(path, 'w', encoding='utf-8') as stream:
            stream.write(text)
        return path

    def tool(self, folder, source):
        path = 'KL&A Tools_dev.tab/Tools.panel/' + folder + '.pushbutton'
        self.write(path + '/script.py', source)
        return path.replace('KL&A Tools_dev.tab/', 'KL&A Tools.tab/')

    def test_follows_called_helper_and_reexport_without_unrelated_functions(self):
        self.write('lib/selectors.py',
                   'from pyrevit import forms\n'
                   'def choose():\n    return forms.SelectFromList.show(["one"])\n'
                   'def unused():\n    return forms.ask_for_string()\n')
        self.write('lib/public.py', 'from selectors import choose as pick\n')
        path = self.tool('Example', '__title__ = "Friendly Example"\n'
                         'from public import pick\npick()\n')
        self.tool('Other', '__title__ = "Other"\n'
                  'from selectors import unused\nvalue = 1\n')

        result = discover_callers(self.root)

        self.assertEqual(['Friendly Example'],
                         [row['title'] for row in result['pyrevit:SelectFromList']])
        self.assertEqual(path, result['pyrevit:SelectFromList'][0]['path'])
        self.assertNotIn('pyrevit:ask_for_string', result)

    def test_discovers_local_xaml_in_constructed_class_and_builtin_alias(self):
        folder = 'KL&A Tools_dev.tab/Tools.panel/Example.pushbutton'
        self.write(folder + '/Dialog.xaml',
                   '<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"/>')
        self.tool('Example',
                  'from pyrevit import forms as ui\n'
                  '__title__ = "Example"\n'
                  'class Dialog(ui.WPFWindow):\n'
                  '    def __init__(self):\n'
                  '        ui.WPFWindow.__init__(self, "Dialog.xaml")\n'
                  '    def close(self):\n'
                  '        ui.alert("Preview")\n'
                  'Dialog()\n')

        result = discover_callers(self.root)

        key = folder.replace('KL&A Tools_dev.tab/', 'KL&A Tools.tab/') + '/Dialog.xaml'
        self.assertEqual('Example', result[key][0]['title'])
        self.assertEqual('Example', result['pyrevit:alert'][0]['title'])

    def test_reexported_custom_function_resolves_shared_xaml_path(self):
        self.write('lib/GUI/Select.xaml',
                   '<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"/>')
        self.write('lib/GUI/selection.py',
                   'import os\nimport wpf\n'
                   'PATH = os.path.dirname(__file__)\n'
                   'def select():\n'
                   '    wpf.LoadComponent(None, os.path.join(PATH, "Select.xaml"))\n')
        self.write('lib/helpers.py', 'from GUI.selection import select\n'
                   'def sheets():\n    return select()\n')
        self.tool('Sheets', '__title__ = "Sheets"\n'
                  'from helpers import sheets\nsheets()\n')

        result = discover_callers(self.root)

        self.assertEqual('Sheets', result['lib/GUI/Select.xaml'][0]['title'])
        self.assertIn('lib/helpers.py', result['lib/GUI/Select.xaml'][0]['via'])

    def test_ignores_hidden_template_tools_and_comments(self):
        self.write('KL&A Tools_dev.tab/_Templates/Hidden.pushbutton/script.py',
                   'from pyrevit import forms\nforms.alert("hidden")\n')
        self.tool('Visible', '# forms.alert("comment")\n'
                  '__title__ = "Visible"\ntext = "forms.ask_for_string()"\n')
        self.assertEqual({}, discover_callers(self.root))

    def test_overridden_base_handler_does_not_add_retired_window(self):
        self.write('lib/Old.xaml', '<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"/>')
        self.write('lib/base.py', 'import wpf\n'
                   'class Base(object):\n'
                   '    def start(self):\n'
                   '        wpf.LoadComponent(self, "Old.xaml")\n')
        folder = 'KL&A Tools_dev.tab/Tools.panel/Current.pushbutton'
        self.write(folder + '/Current.xaml', '<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"/>')
        self.tool('Current', 'import wpf\nfrom base import Base\n'
                  'class Current(Base):\n'
                  '    def __init__(self):\n        self.start()\n'
                  '    def start(self):\n        wpf.LoadComponent(self, "Current.xaml")\n'
                  'Current()\n')

        result = discover_callers(self.root)

        self.assertNotIn('lib/Old.xaml', result)
        self.assertIn(folder.replace('KL&A Tools_dev.tab/', 'KL&A Tools.tab/') + '/Current.xaml', result)

    def test_constructor_supplied_xaml_and_native_dialog_are_discovered(self):
        folder = 'KL&A Tools_dev.tab/Tools.panel/Current.pushbutton'
        self.write(folder + '/Current.xaml', '<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"/>')
        self.tool('Current', 'import wpf\nfrom pyrevit import forms\n'
                  'from Autodesk.Revit.UI import TaskDialog as Prompt\n'
                  'class Current(forms.WPFWindow):\n'
                  '    def __init__(self, path):\n'
                  '        wpf.LoadComponent(self, path)\n'
                  'Current("Current.xaml").ShowDialog()\nPrompt("Review")\n')

        result = discover_callers(self.root)

        self.assertIn(folder.replace('KL&A Tools_dev.tab/', 'KL&A Tools.tab/') + '/Current.xaml', result)
        self.assertEqual('Current', result['native:TaskDialog'][0]['title'])

    def test_handles_invalid_root_and_unparseable_source_without_execution(self):
        self.assertEqual({}, discover_callers(os.path.join(self.root, 'missing')))
        self.tool('Broken', 'this is invalid Python :::\n')
        self.assertEqual({}, discover_callers(self.root))

    def test_configuration_entry_point_is_attributed_to_its_visible_tool(self):
        path = self.tool('Settings', '__title__ = "Settings Tool"\n')
        self.write(path.replace('KL&A Tools.tab/', 'KL&A Tools_dev.tab/') + '/config.py',
                   'from pyrevit import forms\nforms.ask_for_string()\n')
        result = discover_callers(self.root)
        self.assertEqual(['Settings Tool'],
                         [row['title'] for row in result['pyrevit:ask_for_string']])

    def test_callable_aliases_with_cycles_do_not_recurse_forever(self):
        self.tool('Aliases', 'a = b()\nb = a()\na.method()\n')
        self.assertEqual({}, discover_callers(self.root))

    def test_real_repo_includes_indirect_sheet_picker_and_compiled_consumers(self):
        result = discover_callers(PROJECT_ROOT)
        selection_titles = [row['title'] for row in result['lib/GUI/SelectFromDict.xaml']]
        self.assertIn('Duplicate Sheets', selection_titles)
        self.assertIn('Carbon GWP Pull', selection_titles)
        compiled = result['src/KLCode.Wpf/Views/KlaAlertWindow.xaml']
        self.assertEqual(['Family Studio', 'Startup Importer'],
                         sorted(row['title'] for row in compiled))
        native_titles = [row['title'] for row in result['native:OpenFileDialog']]
        self.assertIn('Family Studio', native_titles)
        self.assertIn('Startup Importer', native_titles)


if __name__ == '__main__':
    unittest.main()
