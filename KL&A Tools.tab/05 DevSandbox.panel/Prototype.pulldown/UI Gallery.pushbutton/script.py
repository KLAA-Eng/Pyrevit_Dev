# -*- coding: utf-8 -*-
"""Safely catalog XAML UI sources without executing their commands."""
from __future__ import print_function

import os
import sys

from pyrevit import forms


def _extension_root(path):
    current = os.path.abspath(path)
    while True:
        if current.lower().endswith('.extension'):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return os.path.abspath(path)
        current = parent


EXTENSION_ROOT = _extension_root(__file__)
LIB_DIR = os.path.join(EXTENSION_ROOT, 'lib')
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from ui_gallery.catalog import catalog_xaml_sources
from ui_gallery.preview import can_preview


XAML_PATH = os.path.join(os.path.dirname(__file__), 'Gallery.xaml')
FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'PreviewFixture.xaml')


class GalleryRow(object):
    def __init__(self, entry):
        self.Entry = entry
        self.RelativePath = entry['relative_path']
        self.RootKind = entry['root_kind']
        self.Title = entry['title'] or '(untitled)'
        self.PreviewStatus = 'Enabled' if entry['is_previewable'] else 'Metadata only'
        self.Reason = entry['reason']


class Gallery(forms.WPFWindow):
    def __init__(self):
        forms.WPFWindow.__init__(self, XAML_PATH)
        self._rows = [GalleryRow(entry) for entry in catalog_xaml_sources(EXTENSION_ROOT)]
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

    def inspect_source(self, sender, args):
        row = self.EntriesGrid.SelectedItem
        if row:
            forms.alert(row.Entry['path'], title='Catalogued XAML source')

    def preview_source(self, sender, args):
        row = self.EntriesGrid.SelectedItem
        if row and can_preview(row.Entry, FIXTURE_PATH):
            forms.WPFWindow(FIXTURE_PATH).ShowDialog()

    def close_window(self, sender, args):
        self.Close()

    def _matches(self, row, query):
        if not query:
            return True
        values = (row.RelativePath, row.RootKind, row.Title, row.PreviewStatus, row.Reason)
        return any(query in value.lower() for value in values)

    def _update_actions(self):
        row = self.EntriesGrid.SelectedItem
        self.InspectButton.IsEnabled = row is not None
        self.PreviewButton.IsEnabled = bool(row and can_preview(row.Entry, FIXTURE_PATH))


if __name__ == '__main__':
    Gallery().ShowDialog()
