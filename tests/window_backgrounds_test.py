from __future__ import print_function

import os
import unittest

from repo_paths import TAB_NAME
from xml.etree import ElementTree


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WINDOW_XAML_PATHS = (
    'lib/GUI/SelectFromDict.xaml',
    'lib/GUI/CustomAlert.xaml',
    'lib/GUI/Tools/CreateFromRooms.xaml',
    'lib/match/clipboard_window.xaml',
    TAB_NAME + '/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml',
)

ALL_WINDOW_XAML_PATHS = WINDOW_XAML_PATHS + (
    'lib/GUI/DuplicateSheets.xaml',
    TAB_NAME + '/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml',
    TAB_NAME + '/03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton/Script.xaml',
    TAB_NAME + '/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton/Script.xaml',
    TAB_NAME + '/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml',
    TAB_NAME + '/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml',
)

# The UI Gallery and its static preview fixture are DevSandbox tooling, not
# user-facing KL&A custom windows. The main template itself is the source
# visual authority rather than an additional production window.
KL_A_TEMPLATE_WINDOW_XAML_PATHS = (
    'lib/GUI/SelectFromDict.xaml',
    'lib/GUI/CustomAlert.xaml',
    'lib/GUI/DuplicateSheets.xaml',
    'lib/GUI/Tools/CreateFromRooms.xaml',
    'lib/match/clipboard_window.xaml',
    TAB_NAME + '/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml',
    TAB_NAME + '/03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton/Script.xaml',
    TAB_NAME + '/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton/Script.xaml',
    TAB_NAME + '/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml',
)


class WindowBackgroundTests(unittest.TestCase):
    def test_all_documented_windows_use_kl_charcoal(self):
        for relative_path in ALL_WINDOW_XAML_PATHS:
            xaml_path = os.path.join(PROJECT_ROOT, relative_path)
            root = ElementTree.parse(xaml_path).getroot()

            if relative_path in KL_A_TEMPLATE_WINDOW_XAML_PATHS:
                self.assertEqual('{StaticResource KlaFoundationWindow}', root.attrib.get('Style'), relative_path)
            else:
                self.assertEqual('#1A252B', root.attrib.get('Background'), relative_path)

    def test_branded_window_bodies_use_solid_kl_charcoal(self):
        for relative_path in WINDOW_XAML_PATHS:
            xaml_path = os.path.join(PROJECT_ROOT, relative_path)
            with open(xaml_path, 'r', encoding='utf-8') as xaml_file:
                xaml = xaml_file.read()

            self.assertIn('x:Name="window_body"', xaml, relative_path)
            self.assertIn('Style="{StaticResource KlaWindowShell}"', xaml, relative_path)
            self.assertNotIn('<LinearGradientBrush', xaml, relative_path)

    def test_editor_and_gallery_use_branded_chrome(self):
        target_paths = (
            TAB_NAME + '/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml',
            TAB_NAME + '/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml',
        )

        for relative_path in target_paths:
            xaml_path = os.path.join(PROJECT_ROOT, relative_path)
            root = ElementTree.parse(xaml_path).getroot()
            with open(xaml_path, 'r', encoding='utf-8') as xaml_file:
                xaml = xaml_file.read()

            if relative_path in KL_A_TEMPLATE_WINDOW_XAML_PATHS:
                self.assertEqual('{StaticResource KlaFoundationWindow}', root.attrib.get('Style'), relative_path)
                self.assertIn('Style="{StaticResource KlaWindowShell}"', xaml)
            else:
                self.assertEqual('None', root.attrib.get('WindowStyle'), relative_path)
                self.assertEqual('True', root.attrib.get('AllowsTransparency'), relative_path)
                self.assertIn('MouseDown="header_drag"', xaml, relative_path)
                self.assertIn('x:Name="main_title"', xaml, relative_path)
            self.assertNotIn('#F5F5F5', xaml, relative_path)
            self.assertNotIn('#E8E8E8', xaml, relative_path)
            self.assertNotIn('Foreground="Red"', xaml, relative_path)

    def test_command_windows_keep_pyrevit_wpf_loader(self):
        script_paths = (
            TAB_NAME + '/03 Core Tools.panel/ViewRange.pushbutton/script.py',
            TAB_NAME + '/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py',
        )

        for relative_path in script_paths:
            script_path = os.path.join(PROJECT_ROOT, relative_path)
            with open(script_path, 'r', encoding='utf-8') as script_file:
                script = script_file.read()

            self.assertIn('forms.WPFWindow', script, relative_path)
            self.assertNotIn('from WPF_Base import my_WPF', script, relative_path)

    def test_view_range_comboboxes_use_dark_template(self):
        relative_path = TAB_NAME + '/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml'
        xaml_path = os.path.join(PROJECT_ROOT, relative_path)
        with open(xaml_path, 'r', encoding='utf-8') as xaml_file:
            xaml = xaml_file.read()

        self.assertIn('Style="{StaticResource KlaCompactComboBox}"', xaml)
        with open(os.path.join(PROJECT_ROOT, 'lib/GUI/Resources/KLCodeComponents.xaml'), encoding='utf-8') as stream:
            shared = stream.read()
        self.assertIn('x:Key="KlaCompactComboBox"', shared)
        self.assertIn('BasedOn="{StaticResource KlaComboBox}"', shared)
        self.assertIn('ItemContainerStyle', shared)
        self.assertIn('DropDownBorder', shared)
        self.assertIn('SelectionBoxItem', shared)
        self.assertIn('x:Name="PART_Popup"', shared)

    def test_kl_a_custom_windows_use_the_template_header_treatment(self):
        for relative_path in KL_A_TEMPLATE_WINDOW_XAML_PATHS:
            xaml_path = os.path.join(PROJECT_ROOT, relative_path)
            with open(xaml_path, 'r', encoding='utf-8') as xaml_file:
                xaml = xaml_file.read()

            root = ElementTree.parse(xaml_path).getroot()
            self.assertEqual('{StaticResource KlaFoundationWindow}', root.attrib.get('Style'), relative_path)
            self.assertIn('x:Name="window_shell"', xaml, relative_path)
            self.assertIn('Style="{StaticResource KlaWindowShell}"', xaml, relative_path)
            self.assertNotIn('x:Name="main_title"', xaml, relative_path)
        with open(os.path.join(PROJECT_ROOT, 'lib/GUI/Resources/KLCodeFoundation.xaml'), encoding='utf-8') as stream:
            shell = stream.read()
        self.assertIn('Width="{StaticResource KlaWordmarkWidth}" Height="{StaticResource KlaWordmarkHeight}"', shell)
        self.assertIn('ContentTemplate="{StaticResource KLCodeWordmark}"', shell)
        self.assertIn('Height="{StaticResource KlaChromeRow}"', shell)
        self.assertIn('Style="{StaticResource KlaFoundationCloseButton}"', shell)

    def test_view_range_loads_the_shared_wordmark_at_runtime(self):
        script_path = os.path.join(
            PROJECT_ROOT,
            TAB_NAME + '/03 Core Tools.panel/ViewRange.pushbutton/script.py',
        )
        with open(script_path, 'r', encoding='utf-8') as script_file:
            script = script_file.read()

        self.assertIn('from GUI.window_chrome import load_window', script)
        self.assertIn('load_window(self,', script)
        with open(os.path.join(PROJECT_ROOT, 'lib/GUI/window_chrome.py'), encoding='utf-8') as stream:
            adapter = stream.read()
        self.assertIn('host_loader(xaml_path)', adapter)

    def test_search_windows_use_the_template_icon_and_filter_shell(self):
        search_windows = (
            'lib/GUI/SelectFromDict.xaml',
            'lib/GUI/Tools/CreateFromRooms.xaml',
            TAB_NAME + '/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml',
        )
        for relative_path in search_windows:
            xaml_path = os.path.join(PROJECT_ROOT, relative_path)
            with open(xaml_path, 'r', encoding='utf-8') as xaml_file:
                xaml = xaml_file.read()

            self.assertIn('Source="{StaticResource KlaIconSearch}"', xaml, relative_path)
            self.assertIn('Style="{StaticResource KlaFoundationFilter}"', xaml,
                          relative_path)
            self.assertNotIn('search_16px_light.png', xaml, relative_path)


if __name__ == '__main__':
    unittest.main()
