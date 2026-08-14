from __future__ import print_function

import copy
import os
import shutil
import sys
import tempfile
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.detail_view_folders import build_folder_plan, create_folder_paths


class BuildFolderPlanTests(unittest.TestCase):
    def setUp(self):
        self.destination = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.destination)

    def test_builds_sorted_direct_child_folders_from_detail_number_and_view_name(self):
        views = [
            {'detail_number': '2', 'view_name': 'Wall Section', 'view_id': 2},
            {'detail_number': '1', 'view_name': 'Plan Detail', 'view_id': 1},
        ]

        result = build_folder_plan(self.destination, views)

        self.assertEqual([], result['errors'])
        self.assertEqual(
            ['1 - Plan Detail', '2 - Wall Section'],
            [item['folder_name'] for item in result['folders']],
        )
        self.assertTrue(all(
            os.path.dirname(item['path']) == os.path.abspath(self.destination)
            for item in result['folders']
        ))

    def test_uses_unplaced_label_when_detail_number_is_missing(self):
        result = build_folder_plan(self.destination, [
            {'detail_number': None, 'view_name': 'Typical Detail', 'view_id': 1},
        ])

        self.assertEqual([], result['errors'])
        self.assertEqual('Unplaced - Typical Detail', result['folders'][0]['folder_name'])

    def test_sanitizes_windows_unsafe_characters_and_trailing_periods(self):
        result = build_folder_plan(self.destination, [
            {'detail_number': '1/A?', 'view_name': 'Wall: Detail.', 'view_id': 1},
        ])

        self.assertEqual([], result['errors'])
        self.assertEqual('1_A_ - Wall_ Detail', result['folders'][0]['folder_name'])

    def test_rejects_missing_view_name_without_returning_a_partial_plan(self):
        result = build_folder_plan(self.destination, [
            {'detail_number': '1', 'view_name': 'Valid', 'view_id': 1},
            {'detail_number': '2', 'view_name': '   ', 'view_id': 2},
        ])

        self.assertEqual([], result['folders'])
        self.assertEqual(['View 2 has no usable name.'], result['errors'])

    def test_rejects_folder_names_longer_than_the_windows_component_limit(self):
        result = build_folder_plan(self.destination, [
            {'detail_number': '1', 'view_name': 'A' * 300, 'view_id': 1},
        ])

        self.assertEqual([], result['folders'])
        self.assertEqual(['View 1 folder name exceeds 255 characters.'], result['errors'])

    def test_rejects_case_insensitive_sanitized_name_collisions(self):
        result = build_folder_plan(self.destination, [
            {'detail_number': '1', 'view_name': 'Wall: Detail', 'view_id': 1},
            {'detail_number': '1', 'view_name': 'wall? detail', 'view_id': 2},
        ])

        self.assertEqual([], result['folders'])
        self.assertEqual(
            ['Multiple views resolve to the folder "1 - Wall_ Detail".'],
            result['errors'],
        )

    def test_rejects_existing_destination_folder_before_returning_plan(self):
        existing_path = os.path.join(self.destination, '1 - Existing')
        result = build_folder_plan(
            self.destination,
            [{'detail_number': '1', 'view_name': 'Existing', 'view_id': 1}],
            existing_paths=[existing_path],
        )

        self.assertEqual([], result['folders'])
        self.assertEqual(
            ['Destination already contains "1 - Existing".'],
            result['errors'],
        )

    def test_constrains_malicious_view_name_to_a_direct_child_folder(self):
        result = build_folder_plan(self.destination, [
            {'detail_number': '1', 'view_name': '../Outside', 'view_id': 1},
        ])

        self.assertEqual([], result['errors'])
        self.assertEqual('1 - _Outside', result['folders'][0]['folder_name'])
        self.assertEqual(
            os.path.abspath(self.destination),
            os.path.dirname(result['folders'][0]['path']),
        )

    def test_does_not_mutate_view_records(self):
        views = [{'detail_number': '1', 'view_name': 'Detail', 'view_id': 1}]
        original = copy.deepcopy(views)

        build_folder_plan(self.destination, views)

        self.assertEqual(original, views)

    def test_creates_each_preflighted_folder(self):
        plan = build_folder_plan(self.destination, [
            {'detail_number': '1', 'view_name': 'One', 'view_id': 1},
            {'detail_number': '2', 'view_name': 'Two', 'view_id': 2},
        ])

        result = create_folder_paths(self.destination, plan['folders'])

        self.assertEqual(['1 - One', '2 - Two'], result['created'])
        self.assertEqual([], result['errors'])
        self.assertTrue(os.path.isdir(os.path.join(self.destination, '1 - One')))
        self.assertTrue(os.path.isdir(os.path.join(self.destination, '2 - Two')))

    def test_stops_after_a_creation_failure_and_reports_prior_folders(self):
        plan = build_folder_plan(self.destination, [
            {'detail_number': '1', 'view_name': 'One', 'view_id': 1},
            {'detail_number': '2', 'view_name': 'Two', 'view_id': 2},
        ])
        created_paths = []

        def make_directory(path):
            if path.endswith('2 - Two'):
                raise OSError('simulated failure')
            created_paths.append(path)

        result = create_folder_paths(
            self.destination, plan['folders'], make_directory=make_directory)

        self.assertEqual(['1 - One'], result['created'])
        self.assertEqual(
            [{'folder_name': '2 - Two', 'reason': 'Could not create folder.'}],
            result['errors'],
        )
        self.assertEqual(1, len(created_paths))

    def test_rejects_a_tampered_path_outside_the_destination_before_creation(self):
        attempted_paths = []
        outside_path = os.path.join(os.path.dirname(self.destination), 'outside')

        result = create_folder_paths(
            self.destination,
            [{'folder_name': 'Outside', 'path': outside_path}],
            make_directory=attempted_paths.append,
        )

        self.assertEqual([], result['created'])
        self.assertEqual(
            [{'folder_name': 'Outside', 'reason': 'Folder plan is outside the destination.'}],
            result['errors'],
        )
        self.assertEqual([], attempted_paths)


if __name__ == '__main__':
    unittest.main()
