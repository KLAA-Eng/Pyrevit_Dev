from __future__ import print_function

import os
import unittest
from xml.etree import ElementTree


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WINDOW_XAML_PATHS = (
    'lib/GUI/SelectFromDict.xaml',
    'lib/GUI/CustomAlert.xaml',
    'lib/GUI/Tools/CreateFromRooms.xaml',
    'lib/match/clipboard_window.xaml',
    'KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml',
)

ALL_WINDOW_XAML_PATHS = WINDOW_XAML_PATHS + (
    'lib/GUI/FindReplace.xaml',
    'lib/GUI/RenameViews.xaml',
    'lib/GUI/RenameSheets.xaml',
    'lib/GUI/DuplicateSheets.xaml',
    'KL&A Tools.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml',
    'KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/Script.xaml',
    'KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/Script.xaml',
    'KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml',
    'KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml',
)

# The UI Gallery and its static preview fixture are DevSandbox tooling, not
# user-facing KL&A custom windows. The main template itself is the source
# visual authority rather than an additional production window.
KL_A_TEMPLATE_WINDOW_XAML_PATHS = (
    'lib/GUI/SelectFromDict.xaml',
    'lib/GUI/CustomAlert.xaml',
    'lib/GUI/FindReplace.xaml',
    'lib/GUI/RenameViews.xaml',
    'lib/GUI/RenameSheets.xaml',
    'lib/GUI/DuplicateSheets.xaml',
    'lib/GUI/Tools/CreateFromRooms.xaml',
    'lib/match/clipboard_window.xaml',
    'KL&A Tools.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml',
    'KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/Script.xaml',
    'KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/Script.xaml',
    'KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml',
)


class WindowBackgroundTests(unittest.TestCase):
    def test_all_documented_windows_use_kl_charcoal(self):
        for relative_path in ALL_WINDOW_XAML_PATHS:
            xaml_path = os.path.join(PROJECT_ROOT, relative_path)
            root = ElementTree.parse(xaml_path).getroot()

            self.assertEqual('#1A252B', root.attrib.get('Background'), relative_path)

    def test_branded_window_bodies_use_solid_kl_charcoal(self):
        for relative_path in WINDOW_XAML_PATHS:
            xaml_path = os.path.join(PROJECT_ROOT, relative_path)
            with open(xaml_path, 'r', encoding='utf-8') as xaml_file:
                xaml = xaml_file.read()

            self.assertIn('<Grid Background="#1A252B">', xaml, relative_path)
            self.assertNotIn('<LinearGradientBrush', xaml, relative_path)

    def test_editor_and_gallery_use_branded_chrome(self):
        target_paths = (
            'KL&A Tools.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml',
            'KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml',
        )

        for relative_path in target_paths:
            xaml_path = os.path.join(PROJECT_ROOT, relative_path)
            root = ElementTree.parse(xaml_path).getroot()
            with open(xaml_path, 'r', encoding='utf-8') as xaml_file:
                xaml = xaml_file.read()

            self.assertEqual('None', root.attrib.get('WindowStyle'), relative_path)
            self.assertEqual('True', root.attrib.get('AllowsTransparency'), relative_path)
            self.assertIn('MouseDown="header_drag"', xaml, relative_path)
            self.assertIn('x:Name="main_title"', xaml, relative_path)
            self.assertNotIn('#F5F5F5', xaml, relative_path)
            self.assertNotIn('#E8E8E8', xaml, relative_path)
            self.assertNotIn('Foreground="Red"', xaml, relative_path)

    def test_command_windows_keep_pyrevit_wpf_loader(self):
        script_paths = (
            'KL&A Tools.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py',
            'KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py',
        )

        for relative_path in script_paths:
            script_path = os.path.join(PROJECT_ROOT, relative_path)
            with open(script_path, 'r', encoding='utf-8') as script_file:
                script = script_file.read()

            self.assertIn('forms.WPFWindow', script, relative_path)
            self.assertNotIn('from WPF_Base import my_WPF', script, relative_path)

    def test_view_range_comboboxes_use_dark_template(self):
        relative_path = 'KL&A Tools.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml'
        xaml_path = os.path.join(PROJECT_ROOT, relative_path)
        with open(xaml_path, 'r', encoding='utf-8') as xaml_file:
            xaml = xaml_file.read()

        self.assertIn('x:Key="ComboBoxToggleButton"', xaml)
        self.assertIn('x:Key="ViewRangeComboBox"', xaml)
        self.assertIn('x:Key="ViewRangeComboBoxItem"', xaml)
        self.assertIn('Style="{StaticResource ViewRangeComboBox}"', xaml)
        self.assertIn('ItemContainerStyle="{StaticResource ViewRangeComboBoxItem}"', xaml)
        self.assertIn('DropDownBorder', xaml)
        self.assertIn('SelectionBoxItem', xaml)

    def test_kl_a_custom_windows_use_the_template_header_treatment(self):
        for relative_path in KL_A_TEMPLATE_WINDOW_XAML_PATHS:
            xaml_path = os.path.join(PROJECT_ROOT, relative_path)
            with open(xaml_path, 'r', encoding='utf-8') as xaml_file:
                xaml = xaml_file.read()

            root = ElementTree.parse(xaml_path).getroot()
            self.assertEqual('None', root.attrib.get('WindowStyle'), relative_path)
            self.assertEqual('#1A252B', root.attrib.get('Background'), relative_path)
            self.assertIn('MouseDown="header_drag"', xaml, relative_path)
            self.assertIn('RowDefinition Height="24"', xaml, relative_path)
            if relative_path.endswith('ViewRange.pushbutton/MainWindow.xaml'):
                self.assertIn('x:Name="wordmark_host"', xaml, relative_path)
            else:
                self.assertIn('ContentTemplate="{StaticResource KLCodeWordmark}"', xaml,
                              relative_path)
            self.assertIn('Width="70" Height="12" Margin="8,0,0,0"', xaml,
                          relative_path)
            self.assertIn('Grid.ColumnSpan="3"', xaml, relative_path)
            self.assertIn('Style="{StaticResource KLCodeCloseButton}"', xaml,
                          relative_path)

    def test_view_range_loads_the_shared_wordmark_at_runtime(self):
        script_path = os.path.join(
            PROJECT_ROOT,
            'KL&A Tools.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py',
        )
        with open(script_path, 'r', encoding='utf-8') as script_file:
            script = script_file.read()

        self.assertIn('wordmark_host.ContentTemplate = self._shared_wordmark_template()', script)
        self.assertIn("return styles['KLCodeWordmark']", script)

    def test_shared_dictionary_exposes_template_control_styles(self):
        styles_path = os.path.join(PROJECT_ROOT, 'lib/GUI/Resources/WPF_styles.xaml')
        with open(styles_path, 'r', encoding='utf-8') as styles_file:
            styles = styles_file.read()

        self.assertIn('x:Key="KLCodeWordmark"', styles)
        self.assertIn('x:Key="KLCodeCloseButton"', styles)
        self.assertIn('x:Key="KLCodeActionButton"', styles)
        self.assertIn('x:Key="KLCodeFilterTextBox"', styles)
        self.assertIn('Background="{StaticResource text_green}"', styles)
        self.assertIn('<Viewbox Width="70" Height="12"', styles)

    def test_search_windows_use_the_template_icon_and_filter_shell(self):
        search_windows = (
            'lib/GUI/SelectFromDict.xaml',
            'lib/GUI/Tools/CreateFromRooms.xaml',
            'KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml',
        )
        for relative_path in search_windows:
            xaml_path = os.path.join(PROJECT_ROOT, relative_path)
            with open(xaml_path, 'r', encoding='utf-8') as xaml_file:
                xaml = xaml_file.read()

            self.assertIn('search_16px_light.png', xaml, relative_path)
            self.assertIn('Style="{StaticResource KLCodeFilterTextBox}"', xaml,
                          relative_path)
            self.assertIn('CornerRadius="6"', xaml, relative_path)


if __name__ == '__main__':
    unittest.main()
