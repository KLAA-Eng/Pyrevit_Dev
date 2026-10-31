"""Behavioral coverage of the Gallery's visible standalone catalog."""
from __future__ import unicode_literals

import os
import shutil
import tempfile
import unittest

from lib.ui_gallery.registry import gallery_entries, resolve_source, matching_entries


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class GalleryRegistryTests(unittest.TestCase):
    def test_action_choice_has_five_variants_and_seven_states_in_one_row(self):
        rows = gallery_entries(ROOT, {})
        action = next(row for row in rows if row['id'] == 'dialog-actions')
        self.assertEqual(['Commands', 'Commands + Details', 'Commands + Checkbox',
                          'Full Content', 'Standard Buttons'],
                         [variant['label'] for variant in action['variants']])
        self.assertEqual(['Normal', 'Empty', 'Warning', 'Error', 'Success', 'Disabled', 'Long content'],
                         action['states'])
        matches = matching_entries(rows, 'Commands + Checkbox')
        self.assertEqual(['dialog-actions'], [row['id'] for row in matches])

    def test_shared_dialog_family_has_explicit_sources_and_supported_states(self):
        rows = [row for row in gallery_entries(ROOT, {}) if row['category'] == 'Shared dialog']
        self.assertEqual(6, len(rows))
        self.assertNotIn('dialog-confirmation', [row['id'] for row in rows])
        self.assertNotIn('dialog-parameters', [row['id'] for row in rows])
        self.assertEqual(6, len(set(row['source_path'] for row in rows)))
        for row in rows:
            self.assertTrue(row['can_launch'])
            self.assertEqual(7 if row['id'] in ('dialog-message', 'dialog-actions') else 5, len(row['states']))
            self.assertTrue(os.path.isfile(row['source_path']))
            self.assertIn('Existing tools retain', row['description'])

    def test_shared_families_keep_all_variants_and_search_returns_family_once(self):
        rows = gallery_entries(ROOT, {})
        selection = next(row for row in rows if row['id'] == 'dialog-selection')
        self.assertEqual(['Sheets', 'Revisions', 'Open Documents', 'List Single', 'List Multiple'],
                         [item['label'] for item in selection['variants']])
        self.assertNotIn('dialog-sheets', [row['id'] for row in rows])
        self.assertEqual([selection], matching_entries(rows, 'List Multiple'))
        self.assertEqual(5, len(selection['variants']))
        self.assertIn('pyrevit-select-list', [row['id'] for row in rows])
        self.assertIn('pyrevit-select-list-single', [row['id'] for row in rows])
        self.assertEqual(6, len(matching_entries(rows, 'Shared dialog')))

    def test_origins_distinguish_pyrevit_wrappers_from_native_dialogs(self):
        rows = dict((row['id'], row) for row in gallery_entries(ROOT, {}))
        self.assertEqual('Repository custom', rows['kla-select-from-dict']['origin'])
        self.assertEqual('pyRevit built-in', rows['pyrevit-select-list']['origin'])
        self.assertEqual('Revit/Windows native', rows['pyrevit-alert']['origin'])
        self.assertEqual('Revit/Windows native', rows['pyrevit-pick-file']['origin'])

    def test_future_windows_keep_reviewed_adapters_after_relocation(self):
        rows = gallery_entries(ROOT, {})
        expected = {
            'kla-create-from-rooms': 'lib/GUI/_future/KLC-CreateFromRooms.xaml',
            'kla-match-properties-recall': 'lib/GUI/_future/match/clipboard_window.xaml',
        }
        for identity, path in expected.items():
            row = next(item for item in rows if item['id'] == identity)
            self.assertEqual(path, row['relative_path'])
            self.assertTrue(row['can_launch'])
            self.assertTrue(os.path.isfile(row['source_path']))
            self.assertEqual([row], [item for item in rows if item['relative_path'] == path])

    def test_compiled_windows_remain_explicitly_deferred_without_states(self):
        rows = [row for row in gallery_entries(ROOT, {})
                if row['category'] == 'Compiled add-in']
        self.assertEqual(5, len(rows))
        for row in rows:
            self.assertFalse(row['can_launch'])
            self.assertEqual('Deferred', row['preview_status'])
            self.assertIn('future', row['unavailable_reason'].lower())
            self.assertEqual([], row['states'])

    def test_docked_surfaces_and_overlays_are_outside_standalone_scope(self):
        rows = gallery_entries(ROOT, {})
        self.assertNotIn('pyrevit-warning-bar', [row['id'] for row in rows])
        self.assertNotIn('pyrevit-show-balloon', [row['id'] for row in rows])
        self.assertFalse(any(row['relative_path'].endswith('pane_ui.xaml') for row in rows))

    def test_new_windows_are_accounted_for_without_becoming_executable(self):
        directory = tempfile.mkdtemp()
        try:
            folder = os.path.join(directory, 'KL&A Tools_dev.tab', 'Panel.panel', 'New.pushbutton')
            os.makedirs(folder)
            path = os.path.join(folder, 'Window.xaml')
            with open(path, 'w') as stream:
                stream.write('<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" Title="New window"/>')
            row = [row for row in gallery_entries(directory, {}) if row['title'] == 'New window'][0]
            self.assertFalse(row['can_launch'])
            self.assertEqual('Needs preview adapter', row['preview_status'])
            self.assertIn('Panel.panel/New.pushbutton/Window.xaml', row['relative_path'])
        finally:
            shutil.rmtree(directory)

    def test_resolves_both_tab_layouts_and_rejects_escape_paths(self):
        path = resolve_source(ROOT, 'KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml')
        self.assertTrue(os.path.isfile(path))
        self.assertIsNone(resolve_source(ROOT, '../outside.xaml'))
        self.assertIsNone(resolve_source(ROOT, 'C:/outside.xaml'))

    def test_search_includes_friendly_tool_names_and_paths(self):
        rows = [{'title': 'Shared selector', 'origin': 'Repository custom',
                 'callers': [{'title': 'Carbon GWP Pull', 'path': 'tools/carbon'}]},
                {'title': 'Other', 'origin': 'pyRevit built-in', 'callers': []}]
        self.assertEqual([rows[0]], matching_entries(rows, 'carbon'))
        self.assertEqual([rows[1]], matching_entries(rows, '', 'pyRevit built-in'))
        self.assertEqual([], matching_entries(rows, 'missing'))

    def test_preview_status_combines_with_origin_and_search(self):
        rows = [dict(title='Family Studio', origin='Repository custom', preview_status='Deferred'),
                dict(title='Shared selector', origin='Repository custom', preview_status='Interactive preview'),
                dict(title='Shared host list', origin='pyRevit built-in', preview_status='Interactive preview')]
        self.assertEqual([rows[0]], matching_entries(rows, preview='Deferred'))
        self.assertEqual([rows[1]], matching_entries(rows, 'shared', 'Repository custom', 'Interactive preview'))
        self.assertEqual([], matching_entries(rows, 'shared', preview='Deferred'))
        self.assertEqual(rows, matching_entries(rows, preview='All previews'))

    def test_only_renamed_options_review_remain_as_templates(self):
        rows = gallery_entries(ROOT, {})
        templates = [row for row in rows if row['category'] == 'Template']
        self.assertEqual(2, len(templates))
        self.assertEqual({'Template - ' + name for name in ('Options', 'Review')},
                         {row['title'] for row in templates})
        for row in templates:
            self.assertTrue(row['can_launch'])
            self.assertTrue(os.path.isfile(row['source_path']))
            self.assertEqual(5, len(row['states']))
        for old in ('lib/GUI/_templates/KLCodeFormTemplate.xaml',
                    'lib/GUI/_templates/KLCodeOptionsTemplate.xaml',
                    'lib/GUI/_templates/KLCodeReviewTemplate.xaml',
                    'lib/GUI/FindReplace.xaml', 'lib/GUI/FindReplace.py',
                    'lib/GUI/_templates/KLCodeMainTemplate.xaml',
                    'lib/GUI/_templates/KLCodeSelectionTemplate.xaml',
                    'lib/GUI/_templates/KLCodeMessageTemplate.xaml'):
            self.assertFalse(os.path.exists(os.path.join(ROOT, old)))

    def test_only_message_and_action_choice_add_warning_and_success_states(self):
        rows = dict((row['id'], row) for row in gallery_entries(ROOT, {}))
        self.assertEqual(['Normal', 'Empty', 'Warning', 'Error', 'Success', 'Disabled', 'Long content'],
                         rows['dialog-message']['states'])
        for row in rows.values():
            if row['id'] not in ('dialog-message', 'dialog-actions'):
                self.assertNotIn('Warning', row['states'])
                self.assertNotIn('Success', row['states'])

    def test_retired_rename_forms_are_absent_from_source_and_catalog(self):
        rows = gallery_entries(ROOT, {})
        for name in ('RenameViews.xaml', 'RenameSheets.xaml', 'RenameSheets.py'):
            self.assertFalse(os.path.exists(os.path.join(ROOT, 'lib', 'GUI', name)))
        self.assertFalse(any(row['id'].startswith('kla-legacy-rename-') for row in rows))
        self.assertTrue(any(row['id'] == 'kla-find-replace-views' for row in rows))
        self.assertTrue(any(row['id'] == 'kla-find-replace-sheets' for row in rows))


if __name__ == '__main__':
    unittest.main()
