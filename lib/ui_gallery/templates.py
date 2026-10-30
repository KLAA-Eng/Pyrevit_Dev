# -*- coding: utf-8 -*-
"""Interactive reference-window presenters; all data and outcomes are fictional."""
from __future__ import unicode_literals

from .scenarios import naming_values, rename_samples
from .template_data import TEMPLATE_FILES, form_names, option_data, review_rows, review_outcome, validate_options

TEMPLATE_IDS = frozenset(TEMPLATE_FILES)


def create_template(launcher, state, path):
    # Host imports occur only after windows.create_custom validates the source/state.
    from System.Windows import Window
    from GUI.window_chrome import load_window

    class TemplateWindow(Window):
        def __init__(self):
            self.preview_id = launcher['id']
            self.preview_state = state
            self.preview_result = ''
            self._ready = False
            self._refreshing = False
            title = launcher.get('title', 'Template - ' + self.preview_id.split('-')[1].title())
            if state == 'Long content':
                title += ' - Long Content And Deliberately Long Window Title'
            load_window(self, path, title, launcher.get('tool_version'), self._navigation)
            self._initialize()
            self._ready = True
            if state == 'Disabled':
                self.window_body.IsEnabled = False

        def _initialize(self):
            if self.preview_id == 'template-form':
                self._set_form(naming_values(self.preview_state))
                self.apply_form(None, None)
            elif self.preview_id == 'template-options':
                data = option_data(self.preview_state)
                self.option_category.ItemsSource = ['Structural', 'Architectural', 'Coordination']
                self.option_category.SelectedItem = data['category'] or None
                self.option_offset.Text = data['offset']
                self.option_path.Text = data['path']
                self.option_include_existing.IsChecked = True
                self.apply_options(None, None)
            else:
                self._review_rows = review_rows(self.preview_state)
                self._refresh_review()

        def _navigation(self, uri):
            self.preview_result = 'Footer navigation simulated; no external page opened.'

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

        def browse_sample(self, sender, args):
            self.option_path.Text = 'C:\\Sample Library\\Alternate Example.rfa'
            self.options_feedback.Text = 'Sample location changed. No file picker or file access was performed.'
            self.preview_result = self.options_feedback.Text

        def apply_options(self, sender, args):
            error = validate_options(self.option_category.SelectedItem, self.option_offset.Text)
            scope = 'Selected Items' if self.scope_selected.IsChecked else 'All Available Items'
            self.options_feedback.Text = error or 'Sample options applied: {}; offset {} mm; include existing {}. No files or model changed.'.format(
                scope, self.option_offset.Text, bool(self.option_include_existing.IsChecked))
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
            if self.review_grid.SelectedItem is not None:
                self.review_grid.ScrollIntoView(self.review_grid.SelectedItem)
            self.review_selection_changed(None, None)
            self._review_summary()

        def _review_summary(self):
            self.review_summary.Text = '{} of {} sample items shown; {} checked in total. Check All affects shown items.'.format(
                len(self.review_grid.ItemsSource or ()), len(self._review_rows),
                sum(row.IsChecked for row in self._review_rows))

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
            for row in self.review_grid.ItemsSource or ():
                row.IsChecked = row.CanUse
            self._refresh_review()

        def apply_review(self, sender, args):
            self.preview_result = review_outcome(self._review_rows)
            self.review_summary.Text = self.preview_result

    return TemplateWindow()
