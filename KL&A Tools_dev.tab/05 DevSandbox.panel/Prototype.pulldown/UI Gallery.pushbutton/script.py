# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = 'UI Gallery'
__version__ = 'v0.5'

import os
import sys
from pyrevit import forms
from System.Windows import Window


def _extension_root(path):
    current = os.path.dirname(os.path.abspath(path))
    while True:
        if current.lower().endswith('.extension') or os.path.isdir(os.path.join(current, 'lib')):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            raise ValueError('Could not locate the extension root.')
        current = parent


EXTENSION_ROOT = _extension_root(__file__)
LIB_DIR = os.path.join(EXTENSION_ROOT, 'lib')
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from ui_gallery.registry import ORIGINS, gallery_entries, matching_entries
from ui_gallery.builtin import launch_builtin
from ui_gallery.windows import launch_custom
from GUI.window_chrome import load_window

XAML_PATH = os.path.join(os.path.dirname(__file__), 'Gallery.xaml')


class CallerRow(object):
    def __init__(self, caller):
        self.Title = caller['title']
        self.Path = caller['path']
        self.Evidence = '\n'.join(caller.get('via', []))


class GalleryRow(object):
    def __init__(self, entry):
        self.Entry = entry
        self.Title = entry['title']
        self.Origin = entry['origin']
        self.PreviewStatus = entry['preview_status']
        self.Description = entry['description']
        self.RelativePath = entry.get('relative_path') or entry['called_by']
        self.CallerRows = [CallerRow(caller) for caller in entry['callers']]
        self.UsedBy = ', '.join(caller.Title for caller in self.CallerRows) or 'No current tool caller found'
        self.CanLaunch = entry['can_launch']
        self.Reason = entry['unavailable_reason']


class Gallery(forms.WPFWindow):
    def __init__(self):
        self._ready = False
        Window.__init__(self)
        load_window(self, XAML_PATH, __title__, __version__)
        self._entries = gallery_entries(EXTENSION_ROOT)
        self.OriginFilter.ItemsSource = ['All origins'] + list(ORIGINS)
        self.OriginFilter.SelectedIndex = 0
        self.PreviewFilter.ItemsSource = ['All previews'] + sorted(
            set(entry['preview_status'] for entry in self._entries))
        self.PreviewFilter.SelectedIndex = 0
        self._ready = True
        self._filter()

    def filter_changed(self, sender, args):
        if self._ready:
            self._filter()

    def origin_changed(self, sender, args):
        if self._ready:
            self._filter()

    def preview_changed(self, sender, args):
        if self._ready:
            self._filter()

    def _filter(self):
        previous = self.EntriesGrid.SelectedItem
        previous_id = previous.Entry['id'] if previous else None
        entries = matching_entries(self._entries, self.FilterBox.Text,
                                   self.OriginFilter.SelectedItem or 'All origins',
                                   self.PreviewFilter.SelectedItem or 'All previews')
        rows = [GalleryRow(entry) for entry in entries]
        self.EntriesGrid.ItemsSource = rows
        self.CountText.Text = '{} standalone entries; {} available; {} deferred'.format(
            len(rows), sum(row.CanLaunch for row in rows),
            sum(row.PreviewStatus == 'Deferred' for row in rows))
        self.EntriesGrid.SelectedItem = next(
            (row for row in rows if row.Entry['id'] == previous_id), rows[0] if rows else None)
        self._update_selection()

    def selection_changed(self, sender, args):
        if self._ready:
            self._update_selection()

    def _update_selection(self):
        row = self.EntriesGrid.SelectedItem
        self.DetailTitle.Text = row.Title if row else 'No matching windows'
        self.DetailDescription.Text = row.Description if row else 'Clear the filters to see the catalog.'
        self.SourceText.Text = row.RelativePath if row else ''
        self.CallersList.ItemsSource = row.CallerRows if row else []
        self.CallerSummary.Text = ('{} calling tools'.format(len(row.CallerRows)) if row and row.CallerRows
                                   else 'No current tool caller found; this may be a template or legacy preview.')
        self.AvailabilityText.Text = row.Reason if row else 'Select a window to preview.'
        self.StateSelector.ItemsSource = row.Entry['states'] if row else []
        self.StateSelector.SelectedIndex = 0 if row and row.Entry['states'] else -1
        self.StateSelector.IsEnabled = bool(row and row.CanLaunch)
        self.LaunchButton.IsEnabled = bool(row and row.CanLaunch)
        self.LastResult.Text = ''

    def launch_selected(self, sender, args):
        row = self.EntriesGrid.SelectedItem
        if not row or not row.CanLaunch:
            return
        state = self.StateSelector.SelectedItem or 'Normal'
        try:
            identity = row.Entry['id']
            if identity == 'ui-gallery':
                Gallery().ShowDialog()
                result = 'Gallery preview closed.'
            elif row.Origin == 'Repository custom':
                result = launch_custom(EXTENSION_ROOT, dict(row.Entry, tool_version=__version__), state)
            else:
                result = launch_builtin(row.Entry, state)
            self.LastResult.Text = result or 'Preview closed. No tool command was run.'
        except Exception as error:
            self.LastResult.Text = 'Preview could not open: {}'.format(error)


if __name__ == '__main__':
    Gallery().ShowDialog()
