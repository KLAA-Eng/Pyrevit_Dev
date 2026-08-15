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
        self.Description = launcher['description']
        self.SampleData = 'Seeded sample data'


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
        if row:
            self._launch(row.Launcher['id'])

    def close_window(self, sender, args):
        self.Close()

    def _matches(self, row, query):
        if not query:
            return True
        values = (row.Category, row.Title, row.Description, row.SampleData)
        return any(query in value.lower() for value in values)

    def _update_actions(self):
        self.LaunchButton.IsEnabled = self.EntriesGrid.SelectedItem is not None

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
        elif launcher_id == 'kla-find-replace':
            self._launch_find_replace_preview()
        elif launcher_id == 'kla-select-from-dict':
            from SelectFromDict import select_from_dict
            select_from_dict(dict((name, name) for name in sample_names),
                             title='KL&A sample selection',
                             label='Select fictional drawing types:',
                             button_name='Use selection',
                             version='UI Gallery')
        elif launcher_id == 'kla-steel-psf':
            self._launch_steel_psf_preview()
        else:
            raise ValueError('Unsupported gallery launcher: {}'.format(launcher_id))

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
