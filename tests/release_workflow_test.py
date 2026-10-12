"""Regression checks for release identity, provenance, and completed evidence."""

import ast
import json
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

from repo_paths import ROOT, TAB_NAME, find_tab

sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import generate_build_info as generator
import release_check as checker


class ReleaseWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.payload = {'version': '0.0.11', 'channel': 'dev', 'release_date': '2026-10-05'}
        self.build = checker.build_values(generator.render_build_info(self.payload, 'a' * 40, '2026-10-05'))
        self.changelog = '## Unreleased\nDevelopment 0.0.11\n## 0.0.10 - 2026-10-05\n**Channel:** Beta\n**Tag:** `v0.0.10-beta`\n'
        self.readme = 'v0.0.11-dev; latest published v0.0.10-beta'
        self.row = ['0.0.10', '74eccba', '10.05.2026', '0.0.10',
                    'annotated v0.0.10-beta; https://github.com/KLAA-Eng/Pyrevit_Dev/releases/tag/v0.0.10-beta',
                    'Squash-style release']
        self.ledger = {'0.0.10': self.row}

    def errors(self, **changes):
        values = dict(payload=self.payload, build=self.build, changelog=self.changelog,
                      readme=self.readme, ledger=self.ledger, tabs=['KL&A Tools_dev.tab'])
        values.update(changes)
        return checker.identity_errors(**values)

    def test_both_layouts_resolve_and_ambiguous_layout_fails(self):
        for name in ('KL&A Tools_dev.tab', 'KL&A Tools.tab'):
            with tempfile.TemporaryDirectory() as root:
                with self.assertRaises(ValueError):
                    find_tab(root)
                os.mkdir(os.path.join(root, name))
                self.assertEqual(name, find_tab(root))
                other = 'KL&A Tools.tab' if name.endswith('_dev.tab') else 'KL&A Tools_dev.tab'
                os.mkdir(os.path.join(root, other))
                with self.assertRaises(ValueError):
                    find_tab(root)

    def test_valid_dev_and_beta_identities(self):
        self.assertEqual([], self.errors())
        payload = dict(self.payload, version='0.0.10', channel='beta')
        build = checker.build_values(generator.render_build_info(payload, 'a' * 40, '2026-10-05'))
        self.assertEqual([], self.errors(payload=payload, build=build, tabs=['KL&A Tools.tab']))

    def test_stale_metadata_and_wrong_layout_are_rejected(self):
        errors = self.errors(build=dict(self.build, VERSION='0.0.10', GIT_TAG='v0.0.11-dev'),
                             tabs=['KL&A Tools.tab'])
        for fragment in ('VERSION must match', 'ambiguous', 'active ribbon'):
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_dev_cannot_be_a_changelog_release(self):
        errors = self.errors(changelog=self.changelog + '## 0.0.11 - 2026-10-05\n')
        self.assertTrue(any('dev identity' in error for error in errors))

    def test_latest_release_must_be_in_ledger(self):
        self.assertTrue(any('missing from the delivery ledger' in error for error in self.errors(ledger={})))

    def test_published_history_cannot_be_removed_during_dev_preparation(self):
        errors = self.errors(changelog='## Unreleased\nDevelopment 0.0.11\n', ledger={})
        self.assertTrue(any('published release history' in error for error in errors))

    def test_dev_preparation_requires_resolved_published_delivery(self):
        pending = list(self.row)
        pending[1] = 'Pending merge'
        self.assertTrue(any('must be resolved' in error for error in
                            self.errors(ledger={'0.0.10': pending})))

    def test_invalid_version_channel_and_calendar_date_are_rejected(self):
        for change in ({'version': '0.0.11-dev'}, {'channel': 'release'}, {'release_date': '2026-02-30'}):
            with self.assertRaises(ValueError):
                generator.validate_payload(dict(self.payload, **change))

    def test_generated_identity_never_uses_an_existing_tag(self):
        with tempfile.TemporaryDirectory() as root:
            version_path = os.path.join(root, 'version.json')
            build_path = os.path.join(root, 'build_info.py')
            with open(version_path, 'w', encoding='utf-8') as stream:
                json.dump(self.payload, stream)
            with mock.patch.object(generator, 'VERSION_PATH', version_path), \
                    mock.patch.object(generator, 'BUILD_INFO_PATH', build_path), \
                    mock.patch.object(generator, 'run_git', return_value='a' * 40) as run_git:
                self.assertEqual(0, generator.main())
                run_git.assert_called_once_with(['rev-parse', 'HEAD'])
            with open(build_path, encoding='utf-8') as stream:
                values = checker.build_values(stream.read())
            self.assertEqual('v0.0.11-dev', values['VERSION_LABEL'])
            self.assertEqual('a' * 40, values['METADATA_SOURCE_SHA'])
            self.assertNotIn('GIT_TAG', values)

    def test_build_reader_does_not_execute_code(self):
        with self.assertRaises(ValueError):
            checker.build_values('import os\n')
        with self.assertRaises(ValueError):
            checker.build_values('VERSION = "1"\nVERSION = "2"\n')

    def git_evidence(self, *args):
        if args[0] == 'cat-file':
            return 'tag'
        if args[0] == 'rev-parse':
            return 'b' * 40
        if args[0] == 'show':
            return json.dumps(dict(self.payload, version='0.0.10', channel='beta'))
        self.fail('unexpected Git call ' + repr(args))

    def test_completed_delivery_matches_annotated_tag_and_release_identity(self):
        self.assertEqual([], checker.delivery_errors('0.0.10', self.ledger, self.git_evidence))

    def test_delivery_identifier_cannot_reference_another_release(self):
        wrong = list(self.row)
        wrong[3] = '0.0.9'
        self.assertTrue(any('requested delivery' in error for error in
                            checker.delivery_errors('0.0.10', {'0.0.10': wrong}, self.git_evidence)))
        wrong[0] = '0.0.9'
        self.assertTrue(checker.delivery_errors('0.0.10', {'0.0.10': wrong}, self.git_evidence))

    def test_pending_delivery_and_lightweight_tag_are_rejected(self):
        pending = list(self.row)
        pending[1] = 'Pending merge'
        self.assertTrue(checker.delivery_errors('0.0.10', {'0.0.10': pending}, self.git_evidence))
        def lightweight(*args):
            return 'commit' if args[0] == 'cat-file' else self.git_evidence(*args)
        self.assertTrue(any('annotated' in error for error in
                            checker.delivery_errors('0.0.10', self.ledger, lightweight)))

    def test_wrong_peeled_commit_and_tagged_channel_are_rejected(self):
        def wrong_commit(*args):
            if args[0] == 'rev-parse' and args[1].startswith('refs/tags/'):
                return 'c' * 40
            return self.git_evidence(*args)
        self.assertTrue(any('peel' in error for error in
                            checker.delivery_errors('0.0.10', self.ledger, wrong_commit)))
        def wrong_channel(*args):
            if args[0] == 'show':
                return json.dumps(dict(self.payload, version='0.0.10', channel='dev'))
            return self.git_evidence(*args)
        self.assertTrue(any('version/channel' in error for error in
                            checker.delivery_errors('0.0.10', self.ledger, wrong_channel)))

    def test_about_labels_display_identity_and_generation_provenance(self):
        path = os.path.join(ROOT, TAB_NAME, '04 Outreach.panel', 'About KL&A Tools.pushbutton', 'script.py')
        with open(path, encoding='utf-8') as stream:
            tree = ast.parse(stream.read())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        alert = mock.Mock()
        namespace = {'__revit__': types.SimpleNamespace(Application=types.SimpleNamespace(VersionName='fixture')),
                     'forms': types.SimpleNamespace(alert=alert), 'build_info': types.SimpleNamespace(**self.build),
                     'EXTENSION_ROOT': 'fixture.extension', 'get_pyrevit_version': lambda: 'fixture',
                     'get_revit_build': lambda: 'fixture'}
        exec(compile(ast.Module(body=[main], type_ignores=[]), path, 'exec'), namespace)
        namespace['main']()
        text = alert.call_args[0][0]
        self.assertIn('Version identity: v0.0.11-dev', text)
        self.assertIn('Metadata source commit: ' + 'a' * 40, text)
        self.assertNotIn('Git Tag:', text)
        self.assertNotIn('Git SHA:', text)


if __name__ == '__main__':
    unittest.main()
