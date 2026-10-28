# -*- coding: utf-8 -*-
"""Interactive reference-window presenters; all data and outcomes are fictional."""
from __future__ import unicode_literals

from .scenarios import filtered_items, naming_values, rename_samples, selection_items, set_checked
from .template_data import TEMPLATE_FILES, form_names, message_data, option_data, review_rows, review_outcome, validate_options

TEMPLATE_IDS = frozenset(TEMPLATE_FILES)


def create_template(launcher, state, path):
    # Host imports occur only after windows.create_custom validates the source/state.
    from System.Windows import Window
    from GUI.window_chrome import load_window, fit_window_height
    from pyrevit import forms

    class TemplateWindow(Window):
        def __init__(self):
            self.preview_id = launcher['id']
            self.preview_state = state
            self.preview_result = ''
            self._ready = False
            self._refreshing = False
            self._items = selection_items(state)
            self._visible = list(self._items)
            title = launcher.get('title', 'Template - ' + self.preview_id.split('-')[1].title())
            if state == 'Long content':
                title += ' - Long Content And Deliberately Long Window Title'
            load_window(self, path, title, launcher.get('tool_version'), self._navigation)
            self._initialize()
            self._ready = True
            if state == 'Disabled':
                self.window_body.IsEnabled = False

        def _initialize(self):
            if self.preview_id == 'template-selection':
                if self.preview_state == 'Empty':
                    self.text_label.Content = 'No Sample Items Available.'
                elif self.preview_state == 'Error':
                    self.text_label.Content = 'Sample Validation: Select an Item.'
                    set_checked(self._items, False)
                self._refresh_selection()
            elif self.preview_id == 'template-form':
                self._set_form(naming_values(self.preview_state))
                self.apply_form(None, None)
            elif self.preview_id == 'template-message':
                self._message_min_height = self.MinHeight
                self.message_severity.ItemsSource = ['Information', 'Warning', 'Error']
                self.message_severity.SelectedItem = message_data(self.preview_state)['kind']
                self.message_expander.IsExpanded = False
                self._message()
            elif self.preview_id == 'template-options':
                data = option_data(self.preview_state)
                self.option_category.ItemsSource = ['Structural', 'Architectural', 'Coordination']
                self.option_category.SelectedItem = data['category'] or None
                self.option_offset.Text = data['offset']
                self.option_path.Text = data['path']
                self.option_toggle.IsChecked = True
                self.apply_options(None, None)
            else:
                self._review_rows = review_rows(self.preview_state)
                self._refresh_review()

        def _navigation(self, uri):
            self.preview_result = 'Footer navigation simulated; no external page opened.'

        def dismiss_template(self, sender, args):
            self.Close()

        def _refresh_selection(self):
            self._visible, unused = filtered_items(self._items, self.textbox_filter.Text or '')
            self.main_ListBox.ItemsSource = None
            self.main_ListBox.ItemsSource = list(self._visible)

        def text_filter_updated(self, sender, args):
            if self._ready:
                self._refresh_selection()

        def UIe_ItemChecked(self, sender, args):
            pass  # Each sample's two-way binding owns its check state.

        def button_select_all(self, sender, args):
            set_checked(self._visible, True)
            self._refresh_selection()

        def button_select_none(self, sender, args):
            set_checked(self._visible, False)
            self._refresh_selection()

        def button_select(self, sender, args):
            count = sum(item.IsChecked for item in self._items)
            self.preview_result = '{} fictional item(s) selected.'.format(count)
            forms.alert(self.preview_result, title='Template Preview', warn_icon=count == 0)

        def _set_form(self, values):
            for name in ('find', 'replace', 'prefix', 'suffix'):
                getattr(self, 'input_' + name).Text = values[name]

        def reset_form(self, sender, args):
            self._set_form(naming_values('Normal'))
            self.apply_form(None, None)

        def apply_form(self, sender, args):
            names = form_names(self.preview_state)
            values = [getattr(self, 'input_' + name).Text for name in ('find', 'replace', 'prefix', 'suffix')]
            targets, error = rename_samples(names, *values)
            self.form_feedback.Text = error or ('Rules accepted for {} sample names. No elements were renamed.'.format(len(targets))
                                               if names else 'No Sample Names Available.')
            self.form_feedback.Foreground = self.Resources['KlaErrorBrush' if error else 'KlaMutedBrush']
            self.preview_result = self.form_feedback.Text

        def _message(self):
            data = message_data(self.preview_state, self.message_severity.SelectedItem)
            self.message_heading.Text = data['heading']
            self.message_body.Text = data['body']
            self.message_details.Text = data['details']
            brush = {'Information': 'KlaInfoBrush', 'Warning': 'KlaWarningBrush', 'Error': 'KlaErrorBrush'}[data['kind']]
            self.message_banner.BorderBrush = self.Resources[brush]
            self._fit_message()

        def _fit_message(self):
            if getattr(self, '_fitting_message', False):
                return
            self._fitting_message = True
            try:
                # Reserve the details pane at minimum size while preserving a message viewport.
                details = self.message_details
                extra = details.Height + details.Margin.Top + details.Margin.Bottom if self.message_expander.IsExpanded else 0
                self.MinHeight = self._message_min_height + extra
                fit_window_height(self)
            finally:
                self._fitting_message = False

        def message_details_changed(self, sender, args):
            if self._ready:
                # Expander raises its event before its template finishes changing visibility.
                from System import Action
                from System.Windows.Threading import DispatcherPriority
                self.Dispatcher.BeginInvoke(DispatcherPriority.Loaded, Action(self._fit_message))

        def message_window_size_changed(self, sender, args):
            if self._ready and args.WidthChanged:
                self._fit_message()

        def message_kind_changed(self, sender, args):
            if self._ready:
                self._message()

        def browse_sample(self, sender, args):
            self.option_path.Text = 'C:\\Sample Library\\Alternate Example.rfa'
            self.options_feedback.Text = 'Sample location changed. No file picker or file access was performed.'
            self.preview_result = self.options_feedback.Text

        def apply_options(self, sender, args):
            error = validate_options(self.option_category.SelectedItem, self.option_offset.Text)
            scope = 'Selected Items' if self.scope_selected.IsChecked else 'All Available Items'
            self.options_feedback.Text = error or 'Sample options applied: {}; offset {} mm; include existing {}. No files or model changed.'.format(
                scope, self.option_offset.Text, bool(self.option_toggle.IsChecked))
            self.options_feedback.Foreground = self.Resources['KlaErrorBrush' if error else 'KlaMutedBrush']
            self.preview_result = self.options_feedback.Text

        def _refresh_review(self):
            self._refreshing = True
            try:
                previous = self.review_grid.SelectedItem
                query = (self.review_search.Text or '').lower()
                rows = [row for row in self._review_rows if query in (row.Name + ' ' + row.Status + ' ' + row.Detail).lower()]
                self.review_grid.ItemsSource = None
                self.review_grid.ItemsSource = rows
                self.review_grid.SelectedItem = previous if previous in rows else (rows[0] if rows else None)
            finally:
                self._refreshing = False
            self.review_selection_changed(None, None)
            self._review_summary()

        def _review_summary(self):
            self.review_summary.Text = '{} sample items; {} checked across all filters.'.format(
                len(self._review_rows), sum(row.IsChecked for row in self._review_rows))

        def review_filter_changed(self, sender, args):
            if self._ready:
                self._refresh_review()

        def review_selection_changed(self, sender, args):
            if self._refreshing:
                return
            item = self.review_grid.SelectedItem
            self.review_detail.Text = '{}\n\nStatus: {}\n\n{}'.format(item.Name, item.Status, item.Detail) if item else 'No Sample Item Selected.'

        def review_checked_changed(self, sender, args):
            if self._ready and not self._refreshing:
                self._review_summary()

        def review_check_all(self, sender, args):
            for row in self._review_rows:
                row.IsChecked = row.CanUse
            self._refresh_review()

        def apply_review(self, sender, args):
            self.preview_result = review_outcome(self._review_rows)
            self.review_summary.Text = self.preview_result

    return TemplateWindow()
