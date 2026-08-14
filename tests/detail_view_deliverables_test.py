from __future__ import unicode_literals

import copy
import os
import shutil
import sys
import tempfile
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.detail_view_deliverables import (
    build_deliverable_plan, has_export_failures, is_direct_child_path)


class BuildDeliverablePlanTests(unittest.TestCase):
    def setUp(self):
        self.destination = tempfile.mkdtemp()
        self.folder = {
            'view_id': 42,
            'folder_name': '1 - Wall Detail',
            'path': os.path.join(self.destination, '1 - Wall Detail'),
        }

    def tearDown(self):
        shutil.rmtree(self.destination)

    def test_builds_fixed_direct_child_artifacts(self):
        result = build_deliverable_plan(self.destination, [self.folder])

        self.assertEqual([], result['errors'])
        item = result['items'][0]
        self.assertEqual(42, item['view_id'])
        self.assertEqual(
            {
                'pdf': os.path.join(self.folder['path'], 'detail.pdf'),
                'jpeg': os.path.join(self.folder['path'], 'detail.jpg'),
                'html': os.path.join(self.folder['path'], 'index.html'),
            },
            item['artifacts'],
        )

    def test_rejects_tampered_folder_outside_destination(self):
        outside = dict(self.folder, path=os.path.dirname(self.destination))

        result = build_deliverable_plan(self.destination, [outside])

        self.assertEqual([], result['items'])
        self.assertEqual(['View 42 folder is outside the destination.'], result['errors'])

    def test_rejects_existing_artifacts_before_returning_any_plan(self):
        existing = os.path.join(self.folder['path'], 'detail.pdf')

        result = build_deliverable_plan(
            self.destination, [self.folder], existing_paths=[existing])

        self.assertEqual([], result['items'])
        self.assertEqual(
            ['Destination already contains "detail.pdf" for view 42.'],
            result['errors'],
        )

    def test_does_not_mutate_folder_plan_records(self):
        folders = [self.folder]
        original = copy.deepcopy(folders)

        build_deliverable_plan(self.destination, folders)

        self.assertEqual(original, folders)

    def test_detects_a_partial_export_without_inspecting_folder_names(self):
        successful = {'folder_name': '1 - Detail', 'pdf': 'Created',
                      'jpeg': 'Created', 'html': 'Created'}
        failed = dict(successful, jpeg='Failed: access denied')

        self.assertFalse(has_export_failures([successful]))
        self.assertTrue(has_export_failures([failed]))

    def test_accepts_only_generated_files_directly_inside_the_work_item_folder(self):
        generated = os.path.join(self.folder['path'], 'detail - Wall Detail.jpg')

        self.assertTrue(is_direct_child_path(self.folder['path'], generated))
        self.assertFalse(is_direct_child_path(
            self.folder['path'], os.path.join(self.folder['path'], '..', 'detail.jpg')))


if __name__ == '__main__':
    unittest.main()
