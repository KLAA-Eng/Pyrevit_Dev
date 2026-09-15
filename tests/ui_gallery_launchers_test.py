from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.ui_gallery.launchers import gallery_launchers, launcher_by_id
from lib.ui_gallery.catalog import catalog_xaml_sources


class UiGalleryLaunchersTests(unittest.TestCase):
    def test_catalogs_supported_dialog_launchers(self):
        launchers = gallery_launchers()
        launcher_ids = [launcher['id'] for launcher in launchers]

        self.assertEqual(sorted(launcher_ids), launcher_ids)
        self.assertEqual(len(launcher_ids), len(set(launcher_ids)))
        self.assertIn('pyrevit-select-list', launcher_ids)
        self.assertIn('pyrevit-command-switch', launcher_ids)
        self.assertIn('kla-select-from-dict', launcher_ids)
        self.assertIn('kla-main-template', launcher_ids)
        self.assertIn('kla-custom-alert', launcher_ids)
        self.assertIn('kla-find-replace', launcher_ids)
        self.assertIn('kla-steel-psf', launcher_ids)
        self.assertIn('kla-find-replace-views', launcher_ids)
        self.assertIn('kla-find-replace-sheets', launcher_ids)
        self.assertIn('kla-duplicate-sheets', launcher_ids)
        self.assertIn('kla-view-range', launcher_ids)
        self.assertIn('pyrevit-ask-for-color', launcher_ids)
        self.assertIn('pyrevit-pick-file', launcher_ids)
        self.assertIn('pyrevit-pick-folder', launcher_ids)
        self.assertIn('pyrevit-progress-bar', launcher_ids)
        self.assertIn('pyrevit-show-balloon', launcher_ids)
        self.assertIn('pyrevit-select-open-docs', launcher_ids)
        self.assertIn('pyrevit-select-parameters', launcher_ids)
        self.assertIn('pyrevit-select-revisions', launcher_ids)
        self.assertIn('pyrevit-select-sheets', launcher_ids)
        self.assertIn('pyrevit-select-views', launcher_ids)
        self.assertIn('pyrevit-warning-bar', launcher_ids)
        self.assertTrue(all('relative_path' in launcher for launcher in launchers))
        self.assertTrue(all('called_by' in launcher for launcher in launchers))
        self.assertTrue(all('can_launch' in launcher for launcher in launchers))
        self.assertTrue(all('sample_data_label' in launcher for launcher in launchers))
        self.assertTrue(all(launcher['called_by'] for launcher in launchers))

    def test_seeded_claim_only_applies_to_seeded_previews(self):
        launchers = gallery_launchers()
        by_id = dict((launcher['id'], launcher) for launcher in launchers)

        self.assertTrue(by_id['kla-duplicate-sheets']['uses_seed_data'])
        self.assertEqual('Seeded sample data', by_id['kla-duplicate-sheets']['sample_data_label'])
        self.assertFalse(by_id['ui-gallery-preview-fixture']['uses_seed_data'])
        self.assertEqual('Static fixture', by_id['ui-gallery-preview-fixture']['sample_data_label'])
        self.assertFalse(by_id['pyrevit-select-views']['uses_seed_data'])
        self.assertFalse(by_id['pyrevit-select-views']['can_launch'])
        self.assertEqual('Host/model data required',
                         by_id['pyrevit-select-views']['sample_data_label'])

    def test_all_repo_window_xaml_files_are_accounted_for(self):
        launchers = gallery_launchers()
        launcher_paths = set(
            launcher['relative_path']
            for launcher in launchers
            if launcher['relative_path']
        )
        window_paths = set(
            entry['relative_path']
            for entry in catalog_xaml_sources(PROJECT_ROOT)
            if entry['root_kind'] == 'Window'
        )

        self.assertEqual(sorted(window_paths), sorted(launcher_paths))

    def test_non_window_xaml_files_stay_catalog_only(self):
        entries = catalog_xaml_sources(PROJECT_ROOT)
        non_window_paths = set(
            entry['relative_path']
            for entry in entries
            if entry['root_kind'] in ('Page', 'UserControl', 'ResourceDictionary')
        )
        launcher_paths = set(
            launcher['relative_path']
            for launcher in gallery_launchers()
            if launcher['relative_path']
        )

        self.assertFalse(non_window_paths.intersection(launcher_paths))

    def test_returns_a_copy_and_looks_up_by_id(self):
        launchers = gallery_launchers()
        launchers[0]['title'] = 'Changed by caller'

        self.assertNotEqual('Changed by caller', gallery_launchers()[0]['title'])
        self.assertEqual('pyrevit-select-list', launcher_by_id('pyrevit-select-list')['id'])
        self.assertIsNone(launcher_by_id('not-a-launcher'))


if __name__ == '__main__':
    unittest.main()
