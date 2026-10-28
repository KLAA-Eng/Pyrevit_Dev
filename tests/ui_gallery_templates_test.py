"""Reference-window interactions at a fake WPF boundary; real rendering has its own probe."""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib'))
from ui_gallery.windows import create_custom
from ui_gallery_windows_test import host_modules, ROOT


class TemplateInteractionTests(unittest.TestCase):
    def preview(self, kind, state='Normal'):
        return create_custom(ROOT, dict(id='template-' + kind, title='Template - ' + kind), state)

    def test_form_validation_and_reset_leave_sample_names_unchanged(self):
        with patch.dict(sys.modules, host_modules([])):
            window = self.preview('form')
            names = [row.Name for row in window._items]
            window.input_find.Text = ''
            window.input_replace.Text = 'Replacement'
            window.apply_form(None, None)
            self.assertIn('Find', window.preview_result)
            window.reset_form(None, None)
            window.input_prefix.Text = 'Reviewed-'
            window.apply_form(None, None)
            self.assertFalse(hasattr(window, 'preview_lines'))
            self.assertEqual('Reviewed-', window.input_prefix.Text)
            self.assertEqual('Rules accepted for 4 sample names. No elements were renamed.', window.preview_result)
            self.assertEqual(names, [row.Name for row in window._items])

    def test_options_validate_and_browse_only_changes_fictional_path(self):
        alerts = []
        with patch.dict(sys.modules, host_modules(alerts)):
            window = self.preview('options', 'Error')
            self.assertIn('offset', window.preview_result.lower())
            window.option_offset.Text = '-12.5'
            window.scope_selected.IsChecked = False
            window.option_include_existing.IsChecked = False
            window.apply_options(None, None)
            self.assertIn('All Available Items', window.preview_result)
            self.assertIn('include existing False', window.preview_result)
            window.browse_sample(None, None)
            self.assertIn('Alternate Example', window.option_path.Text)
        self.assertEqual([], alerts)

    def test_review_keeps_checks_across_filtering_and_excludes_blocked_rows(self):
        with patch.dict(sys.modules, host_modules([])):
            window = self.preview('review', 'Error')
            window.apply_review(None, None)
            self.assertIn('blocked', window.preview_result)
            window.review_check_all(None, None)
            self.assertFalse(any(row.IsChecked and not row.CanUse for row in window._review_rows))
            checked = sum(row.IsChecked for row in window._review_rows)
            window.review_search.Text = 'no_matching_sample'
            window.review_filter_changed(None, None)
            self.assertEqual([], window.review_grid.ItemsSource)
            self.assertIn('No Sample Item', window.review_detail.Text)
            window.apply_review(None, None)
            self.assertIn(str(checked), window.preview_result)
            window.review_search.Text = ''
            window.review_filter_changed(None, None)
            self.assertEqual(checked, sum(row.IsChecked for row in window._review_rows))

    def test_message_kind_change_and_disabled_body_keep_common_close_available(self):
        with patch.dict(sys.modules, host_modules([])):
            window = self.preview('message')
            window.message_severity.SelectedItem = 'Warning'
            window.message_kind_changed(None, None)
            self.assertIn('Warning', window.message_heading.Text)
            self.assertFalse(window.message_expander.IsExpanded)
            for state in ('Error', 'Long content'):
                message = self.preview('message', state)
                self.assertFalse(message.message_expander.IsExpanded)
            disabled = self.preview('message', 'Disabled')
            self.assertFalse(disabled.window_body.IsEnabled)
            disabled.dismiss_template(None, None)
            self.assertTrue(disabled.closed)

    def test_selection_checks_and_navigation_are_local(self):
        alerts = []
        with patch.dict(sys.modules, host_modules(alerts)):
            window = self.preview('selection')
            window.button_select_none(None, None)
            window.textbox_filter.Text = 'Foundation'
            window.text_filter_updated(None, None)
            window.button_select_all(None, None)
            self.assertEqual(1, sum(row.IsChecked for row in window._items))
            window.button_select(None, None)
            self.assertIn('1 fictional', window.preview_result)
            window._navigation('https://example.test')
            self.assertIn('simulated', window.preview_result)
        self.assertEqual(1, len(alerts))
