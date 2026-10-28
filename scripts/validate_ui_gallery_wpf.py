# -*- coding: utf-8 -*-
"""Isolated WPF probe launched by validate_ui_gallery_wpf.ps1, not by pyRevit.

The pyRevit boundary is a small loader/alert stand-in; WPF, IronPython,
resources, bindings, and custom preview event handlers are real. This does not
prove pyRevit/Revit integration or native-dialog behavior.
"""
from __future__ import print_function

import os
import sys
import types
import wpf
from System import Uri
from System.Windows import Window, Size, Rect
from System.Windows.Media import PixelFormats
from System.Windows.Media.Imaging import RenderTargetBitmap, PngBitmapEncoder, BitmapFrame
from System.IO import FileStream, FileMode


alerts = []


class LoaderWindow(Window):
    def __init__(self, path):
        wpf.LoadComponent(self, path)


forms = types.ModuleType('forms')
forms.WPFWindow = LoaderWindow
forms.alert = lambda *args, **kwargs: alerts.append((args, kwargs))
pyrevit = types.ModuleType('pyrevit')
pyrevit.forms = forms
sys.modules['pyrevit'] = pyrevit

from ui_gallery.registry import gallery_entries
from ui_gallery.windows import create_custom
from ui_gallery.scenarios import STATES


def render_content(window, filename, width, height):
    content = window.Content
    content.Measure(Size(width, height))
    content.Arrange(Rect(0, 0, width, height))
    content.UpdateLayout()
    bitmap = RenderTargetBitmap(int(width), int(height), 96, 96, PixelFormats.Pbgra32)
    bitmap.Render(content)
    encoder = PngBitmapEncoder()
    encoder.Frames.Add(BitmapFrame.Create(bitmap))
    stream = FileStream(filename, FileMode.Create)
    try:
        encoder.Save(stream)
    finally:
        stream.Dispose()


entries = gallery_entries(repo_root)
command_path = os.path.join(repo_root, 'KL&A Tools_dev.tab', '05 DevSandbox.panel',
                            'Prototype.pulldown', 'UI Gallery.pushbutton', 'script.py')
namespace = {'__file__': command_path, '__name__': 'gallery_probe'}
execfile(command_path, namespace)
gallery = namespace['Gallery']()
assert len(gallery._entries) == len(entries)
gallery.FilterBox.Text = 'carbon'
assert gallery.EntriesGrid.Items.Count > 0
assert all('Carbon GWP Pull' in row.UsedBy for row in gallery.EntriesGrid.Items)
gallery.FilterBox.Text = 'no_such_gallery_tool_4927'
assert gallery.EntriesGrid.Items.Count == 0
assert not gallery.LaunchButton.IsEnabled
gallery.FilterBox.Text = ''
gallery.OriginFilter.SelectedItem = 'pyRevit built-in'
assert all(row.Origin == 'pyRevit built-in' for row in gallery.EntriesGrid.Items)
gallery.OriginFilter.SelectedItem = 'All origins'
gallery.PreviewFilter.SelectedItem = 'Deferred'
assert gallery.EntriesGrid.Items.Count == 5
assert all(row.PreviewStatus == 'Deferred' for row in gallery.EntriesGrid.Items)
assert not gallery.LaunchButton.IsEnabled
gallery.OriginFilter.SelectedItem = 'pyRevit built-in'
assert gallery.EntriesGrid.Items.Count == 0
assert not gallery.LaunchButton.IsEnabled
gallery.OriginFilter.SelectedItem = 'All origins'
gallery.FilterBox.Text = 'FamilyStudioWindow.xaml'
assert gallery.EntriesGrid.Items.Count == 1
assert gallery.EntriesGrid.Items[0].Entry['id'] == 'kla-family-studio'
gallery.FilterBox.Text = ''
if output_directory:
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)
    render_content(gallery, os.path.join(output_directory, 'gallery-deferred.png'), 1060, 706)
gallery.PreviewFilter.SelectedItem = 'Interactive preview'
assert all(row.CanLaunch for row in gallery.EntriesGrid.Items)
gallery.PreviewFilter.SelectedItem = 'All previews'
assert gallery.EntriesGrid.Items.Count == len(entries)

deferred = next(row for row in gallery.EntriesGrid.Items if row.Entry['id'] == 'kla-family-studio')
gallery.EntriesGrid.SelectedItem = deferred
assert not gallery.LaunchButton.IsEnabled
assert gallery.StateSelector.Items.Count == 0

if output_directory:
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)
    gallery.EntriesGrid.SelectedItem = next(row for row in gallery.EntriesGrid.Items
                                            if row.Entry['id'] == 'kla-select-from-dict')
    render_content(gallery, os.path.join(output_directory, 'gallery-1060.png'), 1060, 706)
    render_content(gallery, os.path.join(output_directory, 'gallery-900.png'), 900, 586)

count = 0
for entry in entries:
    if entry['origin'] != 'Repository custom' or not entry['can_launch'] or entry['id'] == 'ui-gallery':
        continue
    for state in entry['states']:
        window = create_custom(repo_root, entry, state)
        count += 1
        if hasattr(window, 'main_ListBox'):
            window.button_select_all(None, None)
            window.button_select_none(None, None)
            assert not any(item.IsChecked for item in window._items)
        if output_directory and state == 'Normal' and entry['id'] in ('kla-match-properties-recall', 'kla-find-replace-views'):
            render_content(window, os.path.join(output_directory, entry['id'] + '.png'),
                           420 if 'recall' in entry['id'] else 350, 500)
        window.Close()
gallery.Close()
execfile(os.path.join(repo_root, 'scripts', 'validate_ui_foundation_wpf.py'))
print('IronPython {}: {} catalog entries; {} real-WPF custom/state constructions; Gallery filters/deferred selection passed.'.format(sys.version.split()[0], len(entries), count))
print('No window was shown. Native dialogs and pyRevit/Revit integration remain host checks.')
