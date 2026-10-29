"""Contracts for safe real-XAML preview adapters without a Revit dependency."""
import ast
import os
import sys
import types
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))

from ui_gallery import windows


class Control(object):
    def __init__(self):
        self.Text = ''
        self.Content = ''
        self.ItemsSource = []
        self.Children = []
        self.IsEnabled = True
        self.IsChecked = False
        self.SelectedItem = None

    def ScrollIntoView(self, item):
        self.scrolled_item = item


class Resources(dict):
    def __init__(self):
        self.MergedDictionaries = self

    def Add(self, value):
        pass

    def __getitem__(self, key):
        return object()


class HostControl(Control):
    def __new__(cls, *args, **kwargs):
        instance = object.__new__(cls)
        instance.Resources = Resources()
        instance.Content = Control()
        return instance

    def __init__(self):
        self.Resources = Resources()

    def ShowDialog(self):
        pass

    def Close(self):
        self.closed = True


def host_modules(alerts):
    """Small host fake executes adapters against actual XAML-named controls."""
    def module(**values):
        result = types.ModuleType('fixture')
        result.__dict__.update(values)
        return result

    def load(control, path):
        root = ElementTree.parse(path).getroot()
        control.Height = float(root.attrib.get('Height', 400))
        control.MinHeight = float(root.attrib.get('MinHeight', 0))
        for element in root.iter():
            name = element.attrib.get('{http://schemas.microsoft.com/winfx/2006/xaml}Name')
            if name:
                widget = Control()
                widget.Text = element.attrib.get('Text', '')
                setattr(control, name, widget)

    def load_shell(control, path, title, version=None, navigate=None):
        # The shared shell's real resource/template/event bindings run in the WPF probe.
        load(control, path)
        control.Title = title

    class Bitmap(object):
        def BeginInit(self):
            pass

        def EndInit(self):
            pass

        def Freeze(self):
            pass

    brushes = module(**dict((key, key) for key in (
        'Goldenrod', 'MediumSeaGreen', 'DodgerBlue', 'Orange', 'SeaGreen', 'MediumPurple')))
    return {
        'GUI.window_chrome': module(load_window=load_shell, fit_window_height=lambda window: window.Height),
        'pyrevit': module(forms=module(alert=lambda *a, **k: alerts.append((a, k)))),
        'wpf': module(LoadComponent=load),
        'System': module(Uri=lambda *a: a, UriKind=module(Absolute='absolute')),
        'System.Windows': module(ResourceDictionary=Resources,
                                  Visibility=module(Visible='visible', Collapsed='collapsed'),
                                  Window=HostControl),
        'System.Windows.Controls': module(Grid=module(GetRow=lambda child: 1),
                                           UserControl=HostControl),
        'System.Windows.Input': module(MouseButtonState=module(Pressed='pressed')),
        'System.Windows.Media': module(Brushes=brushes,
                                       Color=module(FromRgb=lambda *rgb: rgb),
                                       SolidColorBrush=lambda color: color),
        'System.Windows.Media.Imaging': module(BitmapImage=Bitmap,
                                                BitmapCacheOption=module(OnLoad='load'),
                                                BitmapCreateOptions=module(IgnoreImageCache='ignore')),
    }


class GalleryWindowTests(unittest.TestCase):
    def test_compiled_windows_fail_before_loading_any_host_modules(self):
        for identifier in windows.DEFERRED_IDS:
            with self.assertRaises(ValueError) as caught:
                windows.launch_custom(ROOT, {'id': identifier})
            self.assertIn('deferred', str(caught.exception).lower())

    def test_path_alias_resolves_development_and_release_tabs(self):
        path = windows.source_path(ROOT, 'KL&A Tools.tab/03 Core Tools.panel/'
                                  'ViewRange.pushbutton/MainWindow.xaml')
        self.assertTrue(os.path.isfile(path))
        with self.assertRaises(ValueError):
            windows.source_path(ROOT, '../outside.xaml')

    def test_adapter_has_handlers_for_every_allowed_source(self):
        with open(os.path.join(ROOT, 'lib', 'ui_gallery', 'windows.py'),
                  encoding='utf-8') as stream:
            tree = ast.parse(stream.read())
        with open(os.path.join(ROOT, 'lib', 'ui_gallery', 'templates.py'), encoding='utf-8') as stream:
            tree.body.extend(ast.parse(stream.read()).body)
        methods = {node.name for node in ast.walk(tree)
                   if isinstance(node, ast.FunctionDef)}
        events = {'Click', 'Checked', 'Unchecked', 'MouseDown', 'TextChanged',
                  'PreviewTextInput', 'RequestNavigate', 'Expanded', 'Collapsed', 'SizeChanged'}
        for relative in list(windows.SOURCES.values()) + ['lib/match/clipboard_content.xaml']:
            path = windows.source_path(ROOT, relative)
            if not os.path.isfile(path):
                continue
            for element in ElementTree.parse(path).iter():
                for name, value in element.attrib.items():
                    if name in events:
                        self.assertIn(value, methods, '{}: {}'.format(relative, value))

    def test_adapters_do_not_import_production_commands_or_clipboard(self):
        with open(os.path.join(ROOT, 'lib', 'ui_gallery', 'windows.py'),
                  encoding='utf-8') as stream:
            tree = ast.parse(stream.read())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or '')
        self.assertNotIn('match.clipboard', imports)
        self.assertNotIn('GUI.SelectFromDict', imports)
        self.assertFalse(any('steel_weight' in name or 'revit_batch' in name
                             for name in imports))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        names = [node.func.attr for node in calls if isinstance(node.func, ast.Attribute)]
        self.assertNotIn('load_source', names)
        self.assertNotIn('Start', names)

    def test_all_existing_adapters_construct_with_each_state_using_named_xaml_controls(self):
        from ui_gallery.scenarios import STATES
        alerts = []
        with patch.dict(sys.modules, host_modules(alerts)):
            for identifier, relative in windows.SOURCES.items():
                if not os.path.isfile(windows.source_path(ROOT, relative)):
                    continue
                for state in STATES:
                    preview = windows.create_custom(ROOT, {'id': identifier, 'title': identifier}, state)
                    self.assertEqual(state, preview.preview_state)
        self.assertEqual([], alerts)

    def test_selection_and_exports_are_local_simulations(self):
        alerts = []
        with patch.dict(sys.modules, host_modules(alerts)):
            preview = windows.create_custom(ROOT, {'id': 'kla-steel-psf'}, 'Normal')
            preview.button_select_none(None, None)
            self.assertFalse(any(row.IsChecked for row in preview._items))
            preview.textbox_filter.Text = 'Foundation'
            preview.text_filter_updated(None, None)
            preview.button_select_all(None, None)
            self.assertEqual(1, sum(row.IsChecked for row in preview._items))
            preview.button_initialize_csv(None, None)
            self.assertIn('No folder picker or file write', preview.preview_result)

    def test_sheet_case_action_preserves_numbers_and_rename_validates_both_groups(self):
        with patch.dict(sys.modules, host_modules([])):
            preview = windows.create_custom(ROOT, {'id': 'kla-find-replace-sheets'})
            original_numbers = list(preview._sample_numbers)
            preview.button_uppercase(None, None)
            self.assertEqual(original_numbers, preview._sample_numbers)
            original_names = list(preview._sample_names)
            preview.input_sheet_number_find.Text = ''
            preview.input_sheet_number_replace.Text = 'invalid'
            preview.button_run(None, None)
            self.assertEqual(original_names, preview._sample_names)
            self.assertEqual(original_numbers, preview._sample_numbers)
            self.assertIn('validation failed', preview.result_summary.Text)

    def test_recall_retains_shell_and_uses_safe_real_content_adapter(self):
        alerts = []
        with patch.dict(sys.modules, host_modules(alerts)):
            preview = windows.create_custom(ROOT, {'id': 'kla-match-properties-recall'})
            content = preview.content_host.Content
            self.assertIsNot(preview.Content, content)
            self.assertEqual('PreviewRecallContent', type(content).__name__)
            content.search_tb.Text = 'Existing'
            content.search_changed(None, None)
            self.assertEqual(1, len(content.paramListView.ItemsSource))
            content.paste_single(None, None)
            self.assertEqual(1, len(alerts))

    def test_duplicate_simulation_uses_entered_names_numbers_and_options(self):
        with patch.dict(sys.modules, host_modules([])):
            preview = windows.create_custom(ROOT, {'id': 'kla-duplicate-sheets'})
            preview.UI_sheet_name_prefix.Text = 'Changed - '
            preview.UI_sheet_number_prefix.Text = 'New-'
            preview.UI_checkbox_views.IsChecked = True
            preview.button_run(None, None)
            self.assertIn('Changed - ', preview.preview_result)
            self.assertIn('New-S101', preview.preview_result)
            self.assertIn('Included: views', preview.preview_result)

    def test_rename_family_states_seed_visible_empty_invalid_and_long_fields(self):
        groups = {
            'template-form': 'input_',
            'kla-find-replace-views': 'input_',
            'kla-find-replace-sheets': 'input_sheet_name_',
            'kla-duplicate-sheets': 'UI_sheet_name_',
        }
        with patch.dict(sys.modules, host_modules([])):
            for identifier, prefix in groups.items():
                empty = windows.create_custom(ROOT, {'id': identifier}, 'Empty')
                self.assertEqual('', getattr(empty, prefix + 'find').Text, identifier)
                self.assertEqual('', getattr(empty, prefix + 'replace').Text, identifier)
                error = windows.create_custom(ROOT, {'id': identifier}, 'Error')
                self.assertEqual('', getattr(error, prefix + 'find').Text, identifier)
                self.assertNotEqual('', getattr(error, prefix + 'replace').Text, identifier)
                long = windows.create_custom(ROOT, {'id': identifier}, 'Long content')
                self.assertGreater(len(getattr(long, prefix + 'prefix').Text), 100, identifier)

    def test_duplicate_error_state_rejects_the_seeded_invalid_naming_fields(self):
        alerts = []
        with patch.dict(sys.modules, host_modules(alerts)):
            preview = windows.create_custom(ROOT, {'id': 'kla-duplicate-sheets'}, 'Error')
            preview.button_run(None, None)
            self.assertIn('Enter Find text', preview.preview_result)
            self.assertTrue(alerts[-1][1]['warn_icon'])

    def test_duplicate_checks_view_title_and_number_naming_requests(self):
        with patch.dict(sys.modules, host_modules([])):
            for prefix in ('UI_view_', 'UI_sheet_name_', 'UI_sheet_number_'):
                preview = windows.create_custom(ROOT, {'id': 'kla-duplicate-sheets'})
                getattr(preview, prefix + 'find').Text = ''
                getattr(preview, prefix + 'replace').Text = 'Invalid without Find'
                preview.button_run(None, None)
                self.assertIn('Enter Find text', preview.preview_result, prefix)


if __name__ == '__main__':
    unittest.main()
