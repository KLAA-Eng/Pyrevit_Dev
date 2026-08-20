# -*- coding: utf-8 -*-
"""Launch safe, seeded previews of pyRevit and KL&A dialog families."""
from __future__ import print_function

import os
import sys

from pyrevit import forms


def _extension_root(path):
    current = os.path.dirname(os.path.abspath(path))
    while True:
        if current.lower().endswith('.extension'):
            return current
        if os.path.isdir(os.path.join(current, 'lib')):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return os.path.abspath(path)
        current = parent


EXTENSION_ROOT = _extension_root(__file__)
LIB_DIR = os.path.join(EXTENSION_ROOT, 'lib')
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from ui_gallery.launchers import gallery_launchers


XAML_PATH = os.path.join(os.path.dirname(__file__), 'Gallery.xaml')
GUI_LIB_DIR = os.path.join(LIB_DIR, 'GUI')
if GUI_LIB_DIR not in sys.path:
    sys.path.insert(0, GUI_LIB_DIR)


class GalleryRow(object):
    def __init__(self, launcher):
        self.Launcher = launcher
        self.Category = launcher['category']
        self.Title = launcher['title']
        self.RelativePath = launcher.get('relative_path') or 'pyRevit built-in'
        self.CalledBy = launcher.get('called_by') or ''
        self.Description = launcher['description']
        self.SampleData = 'Seeded sample data' if launcher.get('uses_seed_data') else 'Catalog only'
        self.CanLaunch = launcher.get('can_launch', True)


class PreviewListItem(object):
    def __init__(self, name, element=None, checked=False):
        self.Name = name
        self.element = element
        self.IsChecked = checked


class PreviewLevel(object):
    def __init__(self, name, id_value):
        self.Name = name
        self.IdValue = id_value


class ViewRangePreviewData(object):
    def __init__(self):
        from System.Windows.Media import Brushes
        self.message = 'Fictional preview data. Changes cannot modify the model.'
        self.unit_label = 'ft'
        self.available_levels = [PreviewLevel('Level 01 - Lobby', 1),
                                 PreviewLevel('Level 02 - Office', 2),
                                 PreviewLevel('Roof - Mechanical', 3)]
        self.can_modify_view = True
        self.warning_message = ''
        self.topplane_brush = Brushes.DodgerBlue
        self.cutplane_brush = Brushes.Orange
        self.bottomplane_brush = Brushes.SeaGreen
        self.viewdepth_brush = Brushes.MediumPurple
        self.topplane_elevation = "12' - 0\""
        self.cutplane_elevation = "4' - 0\""
        self.bottomplane_elevation = "0' - 0\""
        self.viewdepth_elevation = "-4' - 0\""
        self.topplane_new_value = "12' - 0\""
        self.cutplane_new_value = "4' - 0\""
        self.bottomplane_new_value = "0' - 0\""
        self.viewdepth_new_value = "-4' - 0\""
        self.topplane_level_id = 1
        self.bottomplane_level_id = 1
        self.viewdepth_level_id = 1
        self.cutplane_level_name = 'Level 01 - Lobby'


class Gallery(forms.WPFWindow):
    def __init__(self):
        forms.WPFWindow.__init__(self, XAML_PATH)
        self._rows = [GalleryRow(launcher) for launcher in gallery_launchers()]
        self._visible_rows = list(self._rows)
        self.EntriesGrid.ItemsSource = self._visible_rows
        self._update_actions()

    def filter_changed(self, sender, args):
        query = (self.FilterBox.Text or '').lower()
        self._visible_rows = [row for row in self._rows if self._matches(row, query)]
        self.EntriesGrid.ItemsSource = self._visible_rows
        self._update_actions()

    def selection_changed(self, sender, args):
        self._update_actions()

    def launch_selected(self, sender, args):
        row = self.EntriesGrid.SelectedItem
        if row and row.CanLaunch:
            self._launch(row.Launcher['id'])

    def close_window(self, sender, args):
        self.Close()

    def _matches(self, row, query):
        if not query:
            return True
        values = (row.Category, row.Title, row.Description, row.SampleData,
                  row.RelativePath, row.CalledBy)
        return any(query in value.lower() for value in values)

    def _update_actions(self):
        row = self.EntriesGrid.SelectedItem
        self.LaunchButton.IsEnabled = bool(row and row.CanLaunch)

    def _launch(self, launcher_id):
        try:
            self._launch_dialog(launcher_id)
        except Exception as error:
            forms.alert('Could not open this dialog preview.\n\n{}'.format(error),
                        title='UI Gallery')

    def _launch_dialog(self, launcher_id):
        sample_names = ['A101 - Floor Plan', 'A201 - Building Section',
                        'S101 - Foundation Plan', 'M101 - HVAC Plan']
        if launcher_id == 'pyrevit-alert':
            forms.alert('This is a safe gallery preview. No model data is changed.',
                        title='Sample pyRevit alert')
        elif launcher_id == 'pyrevit-ask-for-string':
            forms.ask_for_string(default='Sample project note',
                                 prompt='Enter a preview value:',
                                 title='Sample pyRevit text input')
        elif launcher_id == 'pyrevit-command-switch':
            forms.CommandSwitchWindow.show(
                ['Open sample report', 'Review sample warnings', 'Cancel preview'],
                message='Choose a safe gallery action')
        elif launcher_id == 'pyrevit-select-list':
            forms.SelectFromList.show(sample_names, multiselect=True,
                                      title='Sample pyRevit list selection',
                                      button_name='Select samples')
        elif launcher_id == 'pyrevit-select-list-single':
            forms.SelectFromList.show(sample_names, multiselect=False,
                                      title='Sample pyRevit list selection',
                                      button_name='Select sample')
        elif launcher_id == 'kla-custom-alert':
            from CustomAlert import show_alert
            show_alert('Preview data is fictional and cannot modify this model.',
                       title='KL&A Tools gallery preview')
        elif launcher_id == 'kla-create-from-rooms':
            self._launch_create_from_rooms_preview()
        elif launcher_id == 'kla-find-replace':
            self._launch_find_replace_preview()
        elif launcher_id == 'kla-find-replace-views':
            self._launch_find_replace_views_preview()
        elif launcher_id == 'kla-find-replace-views-proto':
            self._launch_find_replace_views_proto_preview()
        elif launcher_id == 'kla-find-replace-sheets':
            self._launch_find_replace_sheets_preview()
        elif launcher_id == 'kla-find-replace-sheets-proto':
            self._launch_find_replace_sheets_proto_preview()
        elif launcher_id == 'kla-duplicate-sheets':
            self._launch_duplicate_sheets_preview()
        elif launcher_id == 'kla-match-properties-recall':
            self._launch_match_properties_recall_preview()
        elif launcher_id == 'kla-select-from-dict':
            from SelectFromDict import select_from_dict
            select_from_dict(dict((name, name) for name in sample_names),
                             title='KL&A sample selection',
                             label='Select fictional drawing types:',
                             button_name='Use selection',
                             version='UI Gallery')
        elif launcher_id == 'kla-steel-psf':
            self._launch_steel_psf_preview()
        elif launcher_id == 'kla-view-range':
            self._launch_view_range_preview()
        elif launcher_id == 'ui-gallery':
            Gallery().ShowDialog()
        elif launcher_id == 'ui-gallery-preview-fixture':
            self._launch_static_preview(
                os.path.join(os.path.dirname(__file__), 'fixtures', 'PreviewFixture.xaml'),
                'UI Gallery preview fixture')
        else:
            raise ValueError('Unsupported gallery launcher: {}'.format(launcher_id))

    def _launch_create_from_rooms_preview(self):
        import wpf
        from GUI.forms import my_WPF

        xaml_path = os.path.join(
            EXTENSION_ROOT, 'lib', 'GUI', 'Tools', 'CreateFromRooms.xaml')

        class CreateFromRoomsPreview(my_WPF):
            def __init__(self):
                self.add_wpf_resource()
                wpf.LoadComponent(self, xaml_path)
                self.main_title.Text = 'Create From Rooms — gallery preview'
                self.text_label.Content = 'Select fictional room type:'
                self.button_main.Content = 'Close preview'
                self.footer_version.Text = 'UI Gallery — fictional data only'
                self.UI_offset.Text = '15'
                self._items = [
                    PreviewListItem('Office Area Boundary', 'office', True),
                    PreviewListItem('Conference Room Boundary', 'conference', False),
                    PreviewListItem('Storage Room Boundary', 'storage', False),
                ]
                self.main_ListBox.ItemsSource = self._items
                self.ShowDialog()

            def text_filter_updated(self, sender, args):
                query = (self.textbox_filter.Text or '').lower()
                if not query:
                    self.main_ListBox.ItemsSource = self._items
                    return
                self.main_ListBox.ItemsSource = [
                    item for item in self._items if query in item.Name.lower()
                ]

            def UIe_ItemChecked(self, sender, args):
                for item in self._items:
                    item.IsChecked = item.Name == sender.Content.Text
                self.main_ListBox.ItemsSource = list(self._items)

            def NumberValidationTextBox(self, sender, args):
                return None

            def button_run(self, sender, args):
                self.Close()

        CreateFromRoomsPreview()

    def _launch_find_replace_preview(self):
        import wpf
        from GUI.forms import my_WPF
        from FindReplace import PATH_SCRIPT

        class FindReplacePreview(my_WPF):
            def __init__(self):
                self.add_wpf_resource()
                wpf.LoadComponent(self, os.path.join(PATH_SCRIPT, 'FindReplace.xaml'))
                self.main_title.Text = 'Find and Replace — gallery preview'
                self.UI_label.Content = 'Fictional drawing name'
                self.UI_main_button.Content = 'Close preview'
                self.input_find.Text = 'Office'
                self.input_replace.Text = 'Studio'
                self.input_prefix.Text = 'Sample - '
                self.input_suffix.Text = ' - Review'
                self.ShowDialog()

            def button_run(self, sender, args):
                self.Close()

        FindReplacePreview()

    def _launch_find_replace_views_preview(self):
        self._launch_rename_preview(
            os.path.join(EXTENSION_ROOT, 'lib', 'Renaming', 'GUI_BaseRename.xaml'),
            'Find and Replace Views — gallery preview',
            {
                'input_find': 'Office',
                'input_replace': 'Studio',
                'input_prefix': 'Sample - ',
                'input_suffix': ' - Review',
            })

    def _launch_find_replace_views_proto_preview(self):
        self._launch_rename_preview(
            os.path.join(EXTENSION_ROOT, 'KL&A Tools_dev.tab', '05 DevSandbox.panel',
                         'Prototype.pulldown', 'FindReplace - Views-proto.pushbutton',
                         'Script.xaml'),
            'Find and Replace Views Prototype — gallery preview',
            {
                'input_find': 'Office',
                'input_replace': 'Studio',
                'input_prefix': 'Sample - ',
                'input_suffix': ' - Review',
            })

    def _launch_find_replace_sheets_preview(self):
        self._launch_rename_preview(
            os.path.join(EXTENSION_ROOT, 'KL&A Tools_dev.tab', '03 Core Tools.panel',
                         'Rename.pulldown', 'FindReplace_Sheets.pushbutton', 'Script.xaml'),
            'Find and Replace Sheets — gallery preview',
            {
                'input_sheet_number_find': 'A',
                'input_sheet_number_replace': 'S',
                'input_sheet_number_prefix': 'Sample-',
                'input_sheet_number_suffix': '-R1',
                'input_sheet_name_find': 'Office',
                'input_sheet_name_replace': 'Studio',
                'input_sheet_name_prefix': 'Sample - ',
                'input_sheet_name_suffix': ' - Review',
            })

    def _launch_find_replace_sheets_proto_preview(self):
        self._launch_rename_preview(
            os.path.join(EXTENSION_ROOT, 'KL&A Tools_dev.tab', '05 DevSandbox.panel',
                         'Prototype.pulldown', 'FindReplace_Sheets-proto.pushbutton',
                         'Script.xaml'),
            'Find and Replace Sheets Prototype — gallery preview',
            {
                'input_sheet_number_find': 'A',
                'input_sheet_number_replace': 'S',
                'input_sheet_number_prefix': 'Sample-',
                'input_sheet_number_suffix': '-R1',
                'input_sheet_name_find': 'Office',
                'input_sheet_name_replace': 'Studio',
                'input_sheet_name_prefix': 'Sample - ',
                'input_sheet_name_suffix': ' - Review',
            })

    def _launch_rename_preview(self, xaml_path, title, sample_values):
        import wpf
        from GUI.forms import my_WPF

        class RenamePreview(my_WPF):
            def __init__(self):
                self.add_wpf_resource()
                wpf.LoadComponent(self, xaml_path)
                self.Title = title
                self.main_title.Text = title
                self.footer_version.Text = 'UI Gallery — fictional data only'
                for control_name, value in sample_values.items():
                    getattr(self, control_name).Text = value
                self.ShowDialog()

            def button_run(self, sender, args):
                self.Close()

            def button_uppercase(self, sender, args):
                self.Close()

            def button_lowercase(self, sender, args):
                self.Close()

            def Hyperlink_RequestNavigate(self, sender, args):
                args.Handled = True

        RenamePreview()

    def _launch_duplicate_sheets_preview(self):
        xaml_path = os.path.join(
            EXTENSION_ROOT, 'KL&A Tools_dev.tab', '03 Core Tools.panel',
            'duplicate_sheets.pushbutton', 'Script.xaml')
        self._launch_static_preview(xaml_path,
                                    'Duplicate Sheets — gallery preview')

    def _launch_static_preview(self, xaml_path, title):
        class StaticPreview(forms.WPFWindow):
            def __init__(self):
                forms.WPFWindow.__init__(self, xaml_path)
                self.Title = title
                if hasattr(self, 'main_title'):
                    self.main_title.Text = title
                self.ShowDialog()

            def button_close(self, sender, args):
                self.Close()

            def button_run(self, sender, args):
                self.Close()

            def header_drag(self, sender, args):
                return None

            def radiobutton_duplicate_option(self, sender, args):
                return None

        StaticPreview()

    def _launch_match_properties_recall_preview(self):
        from System.Windows import Thickness
        from System.Windows.Controls import StackPanel, TextBlock, ListBox

        xaml_path = os.path.join(EXTENSION_ROOT, 'lib', 'match', 'clipboard_window.xaml')

        class MatchRecallPreview(forms.WPFWindow):
            def __init__(self):
                forms.WPFWindow.__init__(self, xaml_path)
                self.Title = 'Match Properties Recall — gallery preview'
                panel = StackPanel()
                panel.Margin = Thickness(12)
                heading = TextBlock()
                heading.Text = 'Fictional saved match parameters'
                heading.Margin = Thickness(0, 0, 0, 8)
                panel.Children.Add(heading)
                values = ListBox()
                values.ItemsSource = [
                    'Mark = A-101',
                    'Comments = Coordination review',
                    'Phase Created = Existing',
                    'Detail Level = Fine',
                ]
                panel.Children.Add(values)
                note = TextBlock()
                note.Text = 'Preview only. No Revit elements are read or changed.'
                note.Margin = Thickness(0, 8, 0, 0)
                panel.Children.Add(note)
                self.Content = panel
                self.ShowDialog()

        MatchRecallPreview()

    def _launch_view_range_preview(self):
        xaml_path = os.path.join(
            EXTENSION_ROOT, 'KL&A Tools_dev.tab', '03 Core Tools.panel',
            'ViewRange.pushbutton', 'MainWindow.xaml')

        class ViewRangePreview(forms.WPFWindow):
            def __init__(self):
                forms.WPFWindow.__init__(self, xaml_path)
                self.DataContext = ViewRangePreviewData()
                self.ShowDialog()

            def apply_changes_click(self, sender, args):
                self.warning.Text = 'Preview mode: no changes were applied.'

            def reset_values_click(self, sender, args):
                self.warning.Text = 'Preview values are already seeded.'

        ViewRangePreview()

    def _launch_steel_psf_preview(self):
        import imp
        command_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'Steel PSF.pushbutton', 'script.py')
        module = imp.load_source('ui_gallery_steel_psf', command_path)
        sample_levels = {
            'Level 01 - Lobby': 'sample-level-01',
            'Level 02 - Office': 'sample-level-02',
            'Roof - Mechanical': 'sample-level-roof',
        }
        module.SteelPsfDialog(sample_levels, title='Steel PSF — gallery preview')


if __name__ == '__main__':
    Gallery().ShowDialog()
