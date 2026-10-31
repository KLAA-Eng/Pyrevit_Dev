# -*- coding: utf-8 -*-
"""Gallery-only adapters over real repository XAML and fictional data.

Production command classes are deliberately not loaded: their event handlers
can modify models, files, or saved settings. WPF imports occur only after a
known preview source and state have been checked.
"""
from __future__ import unicode_literals

import os

from .template_data import TEMPLATE_FILES
from .dialog_data import DIALOG_FILES, DIALOG_FAMILIES, MESSAGE_STATES, ACTION_IDS, ACTION_STATES
from .variants import preview_launcher
from find_replace.layout import results_height  # host-free constants shared with the production dialog

from ui_gallery.scenarios import (PreviewItem, alert_message, filtered_items, naming_values,
                                  parse_offset, recall_items, rename_samples,
                                  selection_items, set_checked, validate_state)


DEFERRED_IDS = frozenset((
    'kla-compiled-alert', 'kla-family-studio',
    'kla-startup-importer-source-picker', 'kla-startup-importer-review',
    'kla-startup-importer-blocking-issues'))

SOURCES = {
    'kla-create-from-rooms': 'lib/GUI/_future/KLC-CreateFromRooms.xaml',
    'kla-custom-alert': 'lib/GUI/CustomAlert.xaml',
    'kla-duplicate-sheets': 'lib/GUI/DuplicateSheets.xaml',
    'kla-find-replace-views': 'KL&A Tools.tab/03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton/Script.xaml',
    'kla-find-replace-sheets': 'KL&A Tools.tab/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton/Script.xaml',
    'kla-match-properties-recall': 'lib/GUI/_future/match/clipboard_window.xaml',
    'kla-select-from-dict': 'lib/GUI/SelectFromDict.xaml',
    'kla-steel-psf': 'KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml',
    'kla-view-range': 'KL&A Tools.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml',
    'ui-gallery-preview-fixture': 'KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml',
}


SOURCES.update((identity, 'lib/GUI/_templates/' + filename) for identity, filename in TEMPLATE_FILES.items())
SOURCES.update((identity, 'lib/GUI/dialogs/' + filename) for identity, filename in DIALOG_FILES.items())

def source_path(extension_root, relative_path):
    """Resolve the stable tab alias without allowing paths outside the repo."""
    relative_path = relative_path.replace('\\', '/')
    if relative_path.startswith('KL&A Tools.tab/'):
        development = os.path.join(extension_root, 'KL&A Tools_dev.tab')
        if os.path.isdir(development):
            relative_path = 'KL&A Tools_dev.tab/' + relative_path[len('KL&A Tools.tab/'):]
    root = os.path.realpath(extension_root)
    path = os.path.realpath(os.path.join(root, relative_path))
    if not os.path.normcase(path).startswith(os.path.normcase(root + os.sep)):
        raise ValueError('Preview source must remain inside the extension.')
    return path


def supports(launcher_id):
    return launcher_id in SOURCES or any(identity == launcher_id for identity, unused, choices in DIALOG_FAMILIES)


def create_custom(extension_root, launcher, state='Normal'):
    """Construct an allowed preview without showing it (also supports host QA)."""
    if launcher.get('variants'):
        launcher = preview_launcher(launcher, launcher.get('variant_id'))
    identifier = launcher['id']
    if identifier in DEFERRED_IDS:
        raise ValueError('Compiled window previews are deferred; this entry stays disabled.')
    if identifier not in SOURCES:
        raise ValueError('No reviewed custom preview adapter: {}'.format(identifier))
    if identifier in ('dialog-message', 'dialog-message-plain'):
        validate_state(state, MESSAGE_STATES)
    elif identifier in ACTION_IDS:
        validate_state(state, ACTION_STATES)
    else:
        validate_state(state)
    path = source_path(extension_root, SOURCES[identifier])
    if not os.path.isfile(path):
        raise ValueError('This window source is not present in this checkout.')
    if identifier in TEMPLATE_FILES:
        from .templates import create_template
        return create_template(launcher, state, path)
    if identifier in DIALOG_FILES:
        from .dialogs import create_dialog
        return create_dialog(launcher, state)
    window_type = _window_type()
    return window_type(extension_root, launcher, state, path)


def launch_custom(extension_root, launcher, state='Normal'):
    """Show a real-XAML preview; all action results are local simulations."""
    if launcher.get('variants'):
        launcher = preview_launcher(launcher, launcher.get('variant_id'))
    window = create_custom(extension_root, launcher, state)
    window.ShowDialog()
    if launcher['id'] in DIALOG_FILES:
        return 'Fictional dialog result: {}.'.format(window.result.action)
    return window.preview_result


def _window_type():
    # Loading pyRevit forms initializes the IronPython WPF support module.
    from pyrevit import forms
    import wpf
    from System import Uri, UriKind
    from System.Windows import ResourceDictionary, Visibility, Window
    from System.Windows.Controls import Grid, UserControl
    from System.Windows.Input import MouseButtonState
    from System.Windows.Media import Brushes, Color, SolidColorBrush
    from GUI.window_chrome import load_window, fit_window_height

    def merge(control, path):
        resources = ResourceDictionary()
        resources.Source = Uri(path, UriKind.Absolute)
        control.Resources.MergedDictionaries.Add(resources)

    def refresh(control, items):
        control.ItemsSource = None
        control.ItemsSource = list(items)

    class PreviewRecallContent(UserControl):
        """Actual clipboard XAML with explicitly local search/load/paste handlers."""
        def __init__(self, owner):
            UserControl.__init__(self)
            self._owner = owner
            self._ready = False
            self._items = recall_items(owner.preview_state)
            self._visible = list(self._items)
            merge(self, os.path.join(owner.preview_root, 'lib', 'GUI', 'Resources', 'KLCodeComponents.xaml'))
            merge(self, os.path.join(owner.preview_root, 'lib', 'GUI', '_future', 'match',
                                    'clipboard_ui.ResourceDictionary.en_us.xaml'))
            wpf.LoadComponent(self, os.path.join(owner.preview_root, 'lib', 'GUI', '_future', 'match',
                                               'clipboard_recall_content.xaml'))
            self.loadViewFiltersBtn.Visibility = Visibility.Collapsed
            self.loadFilterElemBtn.Visibility = Visibility.Collapsed
            self.categoryFilterCheck.Visibility = Visibility.Collapsed
            self.categoryColumn.Width = 0
            self._ready = True
            self._refresh()
            if owner.preview_state == 'Error':
                self.regexToggle_b.IsChecked = True
                self.search_tb.Text = '['

        def _refresh(self):
            self._visible, error = filtered_items(
                self._items, self.search_tb.Text or '', bool(self.regexToggle_b.IsChecked))
            refresh(self.paramListView, self._visible)
            self.search_tb.ToolTip = error or 'Search fictional parameter names and values.'
            checked = any(item.IsSelected for item in self._items)
            for button in (self.pasteSingleBtn, self.pasteRectBtn, self.pasteSelBtn):
                button.IsEnabled = checked
            self.clrsearch_b.Visibility = (Visibility.Visible if self.search_tb.Text
                                           else Visibility.Collapsed)

        def search_changed(self, sender, args):
            if self._ready:
                self._refresh()

        def toggle_regex(self, sender, args):
            if self._ready:
                key = 'regexIcon' if self.regexToggle_b.IsChecked else 'filterIcon'
                self.regexToggle_b.Content = self.Resources[key]
                self._refresh()

        def clear_search(self, sender, args):
            self.search_tb.Text = ''

        def check_all(self, sender, args):
            self._check(True)

        def uncheck_all(self, sender, args):
            self._check(False)

        def toggle_all(self, sender, args):
            self._check(None)

        def _check(self, value):
            for item in self._visible:
                item.IsSelected = not item.IsSelected if value is None else value
            self._refresh()

        def checkbox_click(self, sender, args):
            if self._ready:
                self._refresh()

        def load_from_element(self, sender, args):
            self._items = recall_items('Normal')
            self.search_tb.Text = ''
            self._refresh()

        def load_from_view_filters(self, sender, args):
            self.load_from_element(sender, args)

        def load_from_filter_and_element(self, sender, args):
            self.load_from_element(sender, args)

        def _paste(self, label):
            count = sum(1 for item in self._items if item.IsSelected)
            self._owner._feedback('{}: {} fictional parameter(s) selected.'.format(label, count))

        def paste_single(self, sender, args):
            self._paste('Paste One')

        def paste_rectangle(self, sender, args):
            self._paste('Paste Box')

        def paste_selection(self, sender, args):
            self._paste('Paste Selection')

    class Level(object):
        def __init__(self, name, value):
            self.Name = name
            self.IdValue = value

    class ViewRangeData(object):
        def __init__(self, state):
            self.message = 'Fictional plan view. Changes affect the preview only.'
            self.unit_label = 'ft'
            self.available_levels = [Level('Level 01 - Lobby', 1),
                                     Level('Level 02 - Office', 2), Level('Roof', 3)]
            self.can_modify_view = state not in ('Empty', 'Disabled')
            self.warning_message = ('Sample: Top must be above the cut plane.'
                                    if state == 'Error' else '')
            if state == 'Long content':
                self.message = alert_message('Long content')
                self.available_levels[0].Name = selection_items('Long content')[0].Name
            self.cutplane_level_name = self.available_levels[0].Name
            for prefix, value, rgb in (('topplane', '12', (0, 255, 0)),
                                       ('cutplane', '4', (255, 0, 0)),
                                       ('bottomplane', '0', (0, 0, 255)),
                                       ('viewdepth', '-4', (255, 127, 0))):
                brush = SolidColorBrush(Color.FromRgb(*rgb))
                setattr(self, prefix + '_brush', brush)
                setattr(self, prefix + '_elevation', '-' if state == 'Empty' else value)
                setattr(self, prefix + '_new_value', '' if state == 'Empty' else value)
                setattr(self, prefix + '_level_id', 1)
            if state == 'Error':
                self.topplane_new_value = 'not a number'

    class PreviewWindow(Window):
        """One safe handler surface shared by explicitly allowlisted source windows."""
        def __init__(self, root, launcher, state, path):
            self.preview_root = root
            self.preview_id = launcher['id']
            self.preview_state = state
            self.preview_result = ''
            self._ready = False
            self._updating = False
            self._items = selection_items(state)
            self._visible = list(self._items)
            self._sample_names = [row.Name for row in selection_items(state)]
            self._sample_numbers = ['A{:03d}'.format(i + 101)
                                    for i in range(len(self._sample_names))]
            self._duplicate_option = 'Duplicate'
            title = '{} [Gallery: {}]'.format(launcher.get('title', 'Preview'), state)
            if self.preview_id == 'ui-gallery-preview-fixture':
                wpf.LoadComponent(self, path)
                self.Title = title
            else:
                load_window(self, path, title, launcher.get('tool_version'), self._preview_navigation)
                if self.preview_id == 'kla-custom-alert':
                    self._kla_chrome.hide_footer()
            if hasattr(self, 'main_title'):
                self.main_title.Text = launcher.get('title', 'Preview')
            if hasattr(self, 'footer_version'):
                self.footer_version.Text = 'Gallery - {}'.format(state)
            self._initialize()
            if self.preview_id in ('kla-custom-alert', 'kla-view-range'):
                fit_window_height(self)
            self._ready = True
            if hasattr(self, 'main_ListBox'):
                self._refresh_selection()
            if state == 'Disabled':
                self._disable_body()

        def _initialize(self):
            if hasattr(self, 'UI_offset'):
                self.UI_offset.Text = {'Error': 'not a number', 'Empty': '',
                                       'Long content': '12345678901234567890.125'}.get(self.preview_state, '15')
            for group in ('input_', 'input_sheet_name_', 'input_sheet_number_',
                          'UI_view_', 'UI_sheet_name_', 'UI_sheet_number_'):
                values = naming_values(self.preview_state, numbers='number' in group)
                for suffix in ('find', 'replace', 'prefix', 'suffix'):
                    name = group + suffix
                    if hasattr(self, name):
                        getattr(self, name).Text = values[suffix]
            if self.preview_id == 'kla-custom-alert':
                self.alert_heading.Text = 'Warning' if self.preview_state == 'Error' else 'Information'
                severity = 'Warning' if self.preview_state == 'Error' else 'Information'
                self.alert_icon.Content = self.Resources['Kla' + severity + 'Geometry']
                self.alert_banner.BorderBrush = self.Resources['KlaWarningBrush' if severity == 'Warning' else 'KlaInfoBrush']
                self.message_text.Text = alert_message(self.preview_state)
            elif self.preview_id == 'kla-match-properties-recall':
                self.content_host.Content = PreviewRecallContent(self)
            elif self.preview_id == 'kla-view-range':
                self.DataContext = ViewRangeData(self.preview_state)
            if hasattr(self, 'result_panel'):
                if self.preview_state == 'Error':
                    self._show_result('Sample: 1 skipped; 1 failed.',
                                      'A101: requested name already exists.\nA201: sample read-only item.')
                elif self.preview_state == 'Empty':
                    self._show_result('Sample: no items selected.', '')
                elif self.preview_state == 'Long content':
                    self._show_result('Sample: multiple items need attention.', alert_message('Long content'))

        def _disable_body(self):
            if hasattr(self, 'window_body'):
                self.window_body.IsEnabled = False
                return
            content = self.Content
            if hasattr(content, 'Child'):
                content = content.Child
            if hasattr(content, 'Children'):
                for child in content.Children:
                    if Grid.GetRow(child) > 0:
                        child.IsEnabled = False

        def _preview_navigation(self, uri):
            self.preview_result = 'Footer navigation simulated; no external page opened.'

        def _feedback(self, message, error=False):
            self.preview_result = message
            forms.alert('Preview simulation only.\n\n' + message,
                        title='UI Gallery preview', warn_icon=error)

        def _show_result(self, summary, details):
            self.preview_result = summary + ('\n' + details if details else '')
            if not hasattr(self, 'result_panel'):
                self._feedback(self.preview_result, bool(details))
                return
            self.result_panel.Visibility = Visibility.Visible
            self.result_summary.Text = summary
            self.result_details.Text = details
            self.result_details.Visibility = Visibility.Visible if details else Visibility.Collapsed
            self.Height = results_height(1, bool(details))

        def button_close(self, sender, args):
            self.Close()

        def header_drag(self, sender, args):
            if args.LeftButton == MouseButtonState.Pressed:
                self.DragMove()

        def Hyperlink_RequestNavigate(self, sender, args):
            args.Handled = True

        def text_filter_updated(self, sender, args):
            if self._ready and not self._updating:
                self._refresh_selection()

        def _refresh_selection(self):
            self._visible, unused = filtered_items(self._items, self.textbox_filter.Text or '')
            self._updating = True
            try:
                refresh(self.main_ListBox, self._visible)
            finally:
                self._updating = False

        def UIe_ItemChecked(self, sender, args):
            if not self._ready or self._updating:
                return
            if self.preview_id == 'kla-create-from-rooms':
                selected = sender.DataContext
                for item in self._items:
                    item.IsChecked = item is selected
                self._refresh_selection()

        def button_select_all(self, sender, args):
            set_checked(self._visible, True)
            self._refresh_selection()

        def button_select_none(self, sender, args):
            set_checked(self._visible, False)
            self._refresh_selection()

        def button_select(self, sender, args):
            count = sum(1 for item in self._items if item.IsChecked)
            self._feedback('{} fictional item(s) selected.'.format(count), count == 0)

        def button_initialize_csv(self, sender, args):
            self._feedback('Initialize CSV simulated. No folder picker or file write was performed.')

        def button_append_csv(self, sender, args):
            self._feedback('Append CSV simulated. No folder picker or file write was performed.')

        def NumberValidationTextBox(self, sender, args):
            # Allow complete invalid input so the preview can exercise validation.
            return None

        def radiobutton_duplicate_option(self, sender, args):
            self._duplicate_option = str(sender.Content)

        def button_run(self, sender, args):
            if self.preview_id == 'kla-create-from-rooms':
                try:
                    offset = parse_offset(self.UI_offset.Text)
                    selected = [item for item in self._items if item.IsChecked]
                    if not selected:
                        raise ValueError('Select a fictional type first.')
                except ValueError as error:
                    self._feedback(str(error), True)
                    return
                self._feedback('Create simulated for {} at offset {} cm.'.format(selected[0].Name, offset))
            elif self.preview_id == 'kla-duplicate-sheets':
                groups = (('UI_view_', self._sample_names),
                          ('UI_sheet_name_', self._sample_names),
                          ('UI_sheet_number_', self._sample_numbers))
                planned = []
                for prefix, names in groups:
                    values = [getattr(self, prefix + suffix).Text
                              for suffix in ('find', 'replace', 'prefix', 'suffix')]
                    targets, error = rename_samples(names, *values)
                    if error:
                        self._feedback(error, True)
                        return
                    planned.append(targets)
                options = [name.replace('UI_checkbox_', '').replace('_', ' ')
                           for name in ('UI_checkbox_views', 'UI_checkbox_legends',
                                        'UI_checkbox_schedules', 'UI_checkbox_images',
                                        'UI_checkbox_lines', 'UI_checkbox_text',
                                        'UI_checkbox_clouds', 'UI_checkbox_dwgs',
                                        'UI_checkbox_symbols', 'UI_checkbox_dimensions',
                                        'UI_checkbox_additional_revisions')
                           if getattr(self, name).IsChecked]
                details = ['{} - {}\n  View: {}'.format(number, title, view)
                           for view, title, number in zip(*planned)]
                self._feedback('Duplicate simulated for {} fictional sheets using {}.\n'
                               'Included: {}\n\n{}'.format(len(details), self._duplicate_option,
                                                        ', '.join(options) or 'No optional content',
                                                        '\n'.join(details)), not details)
            else:
                self._rename('Rename')

        def button_uppercase(self, sender, args):
            self._rename('Uppercase')

        def button_lowercase(self, sender, args):
            self._rename('Lowercase')

        def _rename(self, action):
            prefix = 'input_sheet_name_' if hasattr(self, 'input_sheet_name_find') else 'input_'
            values = [getattr(self, prefix + suffix).Text
                      for suffix in ('find', 'replace', 'prefix', 'suffix')]
            targets, error = rename_samples(self._sample_names, *values, action=action)
            if error:
                self._show_result('Sample validation failed.', error)
                return
            numbers = list(self._sample_numbers)
            if hasattr(self, 'input_sheet_number_find') and action == 'Rename':
                number_values = [getattr(self, 'input_sheet_number_' + suffix).Text
                                 for suffix in ('find', 'replace', 'prefix', 'suffix')]
                numbers, error = rename_samples(numbers, *number_values)
                if error:
                    self._show_result('Sample number validation failed.', error)
                    return
            changed = sum(1 for before, after in zip(self._sample_names, targets) if before != after)
            if numbers != self._sample_numbers:
                changed = len(targets)
            self._sample_names = targets
            self._sample_numbers = numbers
            details = targets
            if hasattr(self, 'input_sheet_number_find'):
                details = ['{} - {}'.format(number, name) for number, name in zip(numbers, targets)]
            self._show_result('Preview: {} fictional item(s) changed.'.format(changed), '\n'.join(details))

        def apply_changes_click(self, sender, args):
            data = self.DataContext
            try:
                prefixes = ('topplane', 'cutplane', 'bottomplane', 'viewdepth')
                offsets = [parse_offset(getattr(self, prefix + '_input').Text) for prefix in prefixes]
                levels = [getattr(self, prefix + '_level_combo').SelectedValue
                          if prefix != 'cutplane' else 1 for prefix in prefixes]
                elevations = [offset + 12 * ((level or 1) - 1)
                              for offset, level in zip(offsets, levels)]
                if elevations != sorted(elevations, reverse=True):
                    raise ValueError('Top must be above cut, bottom, and view depth.')
                updated = ViewRangeData('Normal')
                updated.available_levels = data.available_levels
                for prefix, offset, level, elevation in zip(prefixes, offsets, levels, elevations):
                    setattr(updated, prefix + '_new_value', str(offset))
                    setattr(updated, prefix + '_level_id', level or 1)
                    setattr(updated, prefix + '_elevation', str(elevation))
                self.DataContext = updated
                self.warning.Text = 'Preview: changes applied to fictional values only.'
            except ValueError as error:
                self.warning.Text = 'Preview: ' + str(error)
            self.preview_result = self.warning.Text

        def reset_values_click(self, sender, args):
            self.DataContext = ViewRangeData('Normal')
            self.warning.Text = ''

    return PreviewWindow
