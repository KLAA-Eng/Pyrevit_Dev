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
from System import Uri, Action
from System.Windows.Threading import Dispatcher, DispatcherFrame, DispatcherPriority
from System.Windows import Window, Size, Rect
from System.Windows.Media import PixelFormats, VisualTreeHelper
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
from ui_gallery.variants import preview_entries


def settle_layout(content):
    # DataGrid star-column sizing is queued at Render priority; finish it before capture.
    frame = DispatcherFrame()
    Dispatcher.CurrentDispatcher.BeginInvoke(DispatcherPriority.Background,
        Action(lambda: setattr(frame, 'Continue', False)))
    Dispatcher.PushFrame(frame)
    content.UpdateLayout()


def render_content(window, filename, width, height):
    content = window.Content
    content.Measure(Size(width, height))
    content.Arrange(Rect(0, 0, width, height))
    content.UpdateLayout()
    settle_layout(content)
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
adapter_entries = list(preview_entries(entries))
command_path = os.path.join(repo_root, 'KL&A Tools_dev.tab', '05 DevSandbox.panel',
                            'Prototype.pulldown', 'UI Gallery.pushbutton', 'script.py')
namespace = {'__file__': command_path, '__name__': 'gallery_probe'}
execfile(command_path, namespace)
gallery = namespace['Gallery']()
assert len(gallery._entries) == len(entries)
gallery.EntriesGrid.SelectedItem = next(row for row in gallery.EntriesGrid.Items
                                       if row.Entry['id'] == 'dialog-message')
assert list(gallery.StateSelector.Items) == ['Normal', 'Empty', 'Warning', 'Error', 'Success', 'Disabled', 'Long content']
assert [item.Label for item in gallery.VariantSelector.Items] == ['Without Details', 'With Details']
gallery.VariantSelector.SelectedIndex = 1
gallery.StateSelector.SelectedItem = 'Success'
gallery.FilterBox.Text = 'Revisions'
assert gallery.EntriesGrid.Items.Count > 0
selection_row = next(row for row in gallery.EntriesGrid.Items if row.Entry['id'] == 'dialog-selection')
gallery.EntriesGrid.SelectedItem = selection_row
assert gallery.VariantSelector.Items.Count == 5
gallery.VariantSelector.SelectedIndex = 2
gallery.StateSelector.SelectedItem = 'Long content'
gallery.FilterBox.Text = 'no_such_window_variant'
assert gallery.VariantSelector.Items.Count == 0
gallery.FilterBox.Text = ''
gallery.EntriesGrid.SelectedItem = next(row for row in gallery.EntriesGrid.Items if row.Entry['id'] == 'dialog-message')
assert gallery.VariantSelector.SelectedItem.Label == 'With Details'
assert gallery.StateSelector.SelectedItem == 'Success'
gallery.EntriesGrid.SelectedItem = next(row for row in gallery.EntriesGrid.Items if row.Entry['id'] == 'dialog-selection')
assert gallery.VariantSelector.SelectedItem.Label == 'Open Documents'
assert gallery.StateSelector.SelectedItem == 'Long content'
source_column = next(column for column in gallery.EntriesGrid.Columns if column.Header == 'Window source')
assert source_column.CanUserSort, 'Window source must support header sorting'
gallery.Content.Measure(Size(gallery.Width, gallery.Height))
gallery.Content.Arrange(Rect(0, 0, gallery.Width, gallery.Height))
settle_layout(gallery.Content)

# Invoke the real column header's UI Automation action, so default WPF sorting
# rather than an independent Python sort orders the actual displayed rows.
import clr
clr.AddReference('UIAutomationProvider')
from System.Windows.Automation.Peers import (DataGridColumnHeaderItemAutomationPeer,
    DataGridColumnHeadersPresenterAutomationPeer, PatternInterface)
from System.Windows.Automation.Provider import IInvokeProvider
from System.Windows.Controls.Primitives import DataGridColumnHeadersPresenter


def visual_children(parent):
    for index in range(VisualTreeHelper.GetChildrenCount(parent)):
        child = VisualTreeHelper.GetChild(parent, index)
        yield child
        for nested in visual_children(child):
            yield nested


source_presenter = next(control for control in visual_children(gallery.EntriesGrid)
                        if isinstance(control, DataGridColumnHeadersPresenter))
variant_column = next(column for column in gallery.EntriesGrid.Columns if column.Header == 'Variant')
for column, property_name in ((source_column, 'RelativePath'), (variant_column, 'VariantLabels')):
    assert column.CanUserSort
    peer = DataGridColumnHeaderItemAutomationPeer(column.Header, column,
        DataGridColumnHeadersPresenterAutomationPeer(source_presenter))
    invoke = peer.GetPattern(PatternInterface.Invoke)
    for direction in ('Ascending', 'Descending'):
        IInvokeProvider.Invoke(invoke)
        settle_layout(gallery.Content)
        assert str(column.SortDirection) == direction
        displayed = [getattr(row, property_name) for row in gallery.EntriesGrid.Items]
        assert len(displayed) == len(entries)
        from System.Globalization import CultureInfo
        comparer = CultureInfo.CurrentCulture.CompareInfo
        comparisons = [comparer.Compare(left, right) for left, right in zip(displayed, displayed[1:])]
        assert all(value <= 0 if direction == 'Ascending' else value >= 0 for value in comparisons), direction
print('Gallery Window source and Variant: actual header UIA actions sort ascending and descending; variant/state memory survives filters.')
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
assert gallery._kla_chrome.version.Text == namespace['__version__']

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
    gallery.FilterBox.Text = 'Shared dialog'
    assert gallery.EntriesGrid.Items.Count == 6
    gallery.EntriesGrid.SelectedItem = next(row for row in gallery.EntriesGrid.Items
                                            if row.Entry['id'] == 'dialog-message')
    gallery.VariantSelector.SelectedIndex = 1
    gallery.StateSelector.SelectedItem = 'Warning'
    render_content(gallery, os.path.join(output_directory, 'gallery-shared-variants.png'), 1060, 760)
    gallery.FilterBox.Text = ''

count = 0
for entry in adapter_entries:
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
                           window.Width, window.Height)
        window.Close()
gallery.Close()
execfile(os.path.join(repo_root, 'scripts', 'validate_ui_input_alignment_wpf.py'))
execfile(os.path.join(repo_root, 'scripts', 'validate_ui_foundation_wpf.py'))
execfile(os.path.join(repo_root, 'scripts', 'validate_ui_templates_wpf.py'))
execfile(os.path.join(repo_root, 'scripts', 'validate_ui_production_wpf.py'))
execfile(os.path.join(repo_root, 'scripts', 'validate_ui_dialogs_wpf.py'))
execfile(os.path.join(repo_root, 'scripts', 'validate_ui_message_variants_wpf.py'))
execfile(os.path.join(repo_root, 'scripts', 'validate_ui_rename_wpf.py'))
execfile(os.path.join(repo_root, 'scripts', 'validate_ui_focus_wpf.py'))
print('IronPython {}: {} catalog entries; {} real-WPF custom/state constructions; Gallery filters/deferred selection passed.'.format(sys.version.split()[0], len(entries), count))
if show_focus_probe:
    execfile(os.path.join(repo_root, 'scripts', 'validate_ui_shown_focus_wpf.py'))
else:
    print('No window was shown. Native dialogs and pyRevit/Revit integration remain host checks.')
