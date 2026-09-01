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
    'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml',
)

ALL_WINDOW_XAML_PATHS = WINDOW_XAML_PATHS + (
    'lib/GUI/FindReplace.xaml',
    'lib/GUI/RenameViews.xaml',
    'lib/GUI/RenameSheets.xaml',
    'lib/GUI/DuplicateSheets.xaml',
    'KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml',
    'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/Script.xaml',
    'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/Script.xaml',
    'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml',
    'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml',
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
            with open(xaml_path, 'r') as xaml_file:
                xaml = xaml_file.read()

            self.assertIn('<Grid Background="#1A252B">', xaml, relative_path)
            self.assertNotIn('<LinearGradientBrush', xaml, relative_path)

    def test_editor_and_gallery_use_branded_chrome(self):
        target_paths = (
            'KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml',
            'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml',
        )

        for relative_path in target_paths:
            xaml_path = os.path.join(PROJECT_ROOT, relative_path)
            root = ElementTree.parse(xaml_path).getroot()
            with open(xaml_path, 'r') as xaml_file:
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
            'KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py',
            'KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py',
        )

        for relative_path in script_paths:
            script_path = os.path.join(PROJECT_ROOT, relative_path)
            with open(script_path, 'r') as script_file:
                script = script_file.read()

            self.assertIn('forms.WPFWindow', script, relative_path)
            self.assertNotIn('from WPF_Base import my_WPF', script, relative_path)


if __name__ == '__main__':
    unittest.main()
