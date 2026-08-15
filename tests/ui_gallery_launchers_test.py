from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.ui_gallery.launchers import gallery_launchers, launcher_by_id


class UiGalleryLaunchersTests(unittest.TestCase):
    def test_catalogs_supported_seeded_dialog_launchers(self):
        launchers = gallery_launchers()
        launcher_ids = [launcher['id'] for launcher in launchers]

        self.assertEqual(sorted(launcher_ids), launcher_ids)
        self.assertEqual(len(launcher_ids), len(set(launcher_ids)))
        self.assertIn('pyrevit-select-list', launcher_ids)
        self.assertIn('pyrevit-command-switch', launcher_ids)
        self.assertIn('kla-select-from-dict', launcher_ids)
        self.assertIn('kla-custom-alert', launcher_ids)
        self.assertIn('kla-find-replace', launcher_ids)
        self.assertIn('kla-steel-psf', launcher_ids)
        self.assertTrue(all(launcher['uses_seed_data'] for launcher in launchers))

    def test_returns_a_copy_and_looks_up_by_id(self):
        launchers = gallery_launchers()
        launchers[0]['title'] = 'Changed by caller'

        self.assertNotEqual('Changed by caller', gallery_launchers()[0]['title'])
        self.assertEqual('pyrevit-select-list', launcher_by_id('pyrevit-select-list')['id'])
        self.assertIsNone(launcher_by_id('not-a-launcher'))


if __name__ == '__main__':
    unittest.main()
