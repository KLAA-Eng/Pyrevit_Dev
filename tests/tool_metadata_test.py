"""Regression coverage for the independent command metadata contract."""

import importlib.util
import os
import tempfile
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_SPEC = importlib.util.spec_from_file_location(
    'check_tool_metadata', os.path.join(ROOT, 'scripts', 'check_tool_metadata.py'))
checker = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(checker)

BUNDLE = '''title: Example
author: KL&A
tooltip: |
  Version: v1.2.EFTools
  Date: 08.13.2026
  Description:
  Describe the task.
  How-to:
  -> Click the button.
  Last update:
  - Recorded source baseline.
'''
SCRIPT = '__title__ = "Example"\n__version__ = "v1.2.EFTools"\n'
SPEC = '''# Example
| Field | Value |
| --- | --- |
| Tool version | `v1.2.EFTools` |
| Status/origin | Unchanged EFTools import. |
| Tool ID | example-command |
| Path aliases | `Example.pushbutton` |
| Version inputs | `bundle.yaml`; `script.py` |
## Tool version history
| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| `v1.2.EFTools` | `0.0.1.beta` | 08.13.2026 | Source baseline. | abc1234 |
'''


class ToolMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = os.path.join(self.temporary.name, 'Example.pushbutton')
        os.makedirs(self.path)

    def validate(self, bundle=BUNDLE, script=SCRIPT, spec=SPEC):
        for name, text in (('bundle.yaml', bundle), ('script.py', script), ('SPEC.md', spec)):
            if text is not None:
                with open(os.path.join(self.path, name), 'w', encoding='utf-8') as stream:
                    stream.write(text)
        return checker.validate_bundle(self.path)

    def test_source_versions_and_scriptless_commands_are_supported(self):
        self.assertEqual([], self.validate())
        os.remove(os.path.join(self.path, 'script.py'))
        self.assertEqual([], self.validate(script=None))

    def test_maintained_and_devsandbox_versions_are_supported(self):
        for version in ('v1.0', 'v0.3', 'v2.10', 'v1.0.pyRevit'):
            self.assertEqual([], self.validate(
                BUNDLE.replace('v1.2.EFTools', version),
                SCRIPT.replace('v1.2.EFTools', version),
                SPEC.replace('v1.2.EFTools', version)))

    def test_title_mismatch_is_detected(self):
        self.assertTrue(any('title' in error for error in
                            self.validate(script=SCRIPT.replace('Example', 'Different'))))

    def test_localized_and_literal_titles_are_supported(self):
        localized = BUNDLE.replace('title: Example', 'title:\n  fr_fr: Exemple\n  en_us: Example')
        self.assertEqual([], self.validate(bundle=localized))
        literal = BUNDLE.replace('title: Example', 'title: |-\n  Example\n  Command')
        self.assertEqual([], self.validate(bundle=literal,
                         script=SCRIPT.replace('Example', 'Example\\nCommand')))

    def test_version_labels_and_expressions_are_rejected(self):
        for value in ('Version: v1.2.EFTools', '1.2', 'v1.2.3', 'v1.0-beta'):
            errors = self.validate(script=SCRIPT.replace('v1.2.EFTools', value))
            self.assertTrue(any('pure' in error for error in errors), value)
        errors = self.validate(script=SCRIPT.replace('"v1.2.EFTools"', '"v1.2" + ".EFTools"'))
        self.assertTrue(any('literal' in error for error in errors))

    def test_forbidden_script_metadata_and_missing_bundle_author_are_detected(self):
        errors = self.validate(bundle=BUNDLE.replace('author: KL&A\n', ''),
                               script=SCRIPT + '__author__ = "KL&A"\n__doc__ = "Help"\n')
        self.assertTrue(any('__author__' in error for error in errors))
        self.assertTrue(any('__doc__' in error for error in errors))
        self.assertIn('bundle requires author', errors)

    def test_module_docstrings_are_rejected_even_when_empty_or_parenthesized(self):
        for docstring in ('"""Command help."""\n', '""""""\n',
                          '("Command "\n "help.")\n'):
            errors = self.validate(script='# -*- coding: utf-8 -*-\n' + docstring + SCRIPT)
            self.assertTrue(any('module docstring' in error for error in errors), docstring)

    def test_function_and_class_docstrings_remain_allowed(self):
        source = SCRIPT + '''
def run_command():
    """Run the command with documented behavior."""
    return None

class CommandState(object):
    """Keep command-specific state."""

    def reset(self):
        """Reset the current state."""
        return None
'''
        self.assertEqual([], self.validate(script=source))

    def test_tooltip_mismatch_missing_sections_and_author_line_are_detected(self):
        changed = BUNDLE.replace('Version: v1.2.EFTools', 'Version: v1.1.EFTools')
        changed = changed.replace('08.13.2026', '31.02.2026').replace('How-to:', 'Instructions:')
        changed = changed.replace('  - Recorded source baseline.', '  Author: KL&A')
        errors = self.validate(bundle=changed)
        for fragment in ('Version line', 'Date', 'How-to', 'bullet', 'Author line'):
            self.assertTrue(any(fragment in error for error in errors), fragment)

    def test_spec_contract_and_current_version_row_are_required(self):
        errors = self.validate(spec=SPEC.replace('Status/origin', 'Origin').replace('Git evidence', 'Evidence'))
        self.assertTrue(any('Status/origin' in error for error in errors))
        self.assertTrue(any('Git evidence' in error for error in errors))
        errors = self.validate(spec=SPEC.replace('| abc1234 |', '| |'))
        self.assertTrue(any('complete row' in error for error in errors))

    def test_delivery_ledger_reference_and_date_are_required(self):
        errors = self.validate(spec=SPEC.replace('`0.0.1.beta`', '`0.0.99`'))
        self.assertTrue(any('delivery ledger' in error for error in errors))
        errors = self.validate(spec=SPEC.replace('08.13.2026', '08.14.2026'))
        self.assertTrue(any('match its Main delivery date' in error for error in errors))

    def test_planned_versions_require_matching_unreleased_status(self):
        planned_bundle = BUNDLE.replace('v1.2.EFTools', 'v1.3').replace(
            'Date: 08.13.2026', 'Date: 10.02.2026\n  Status: Unreleased')
        planned_script = SCRIPT.replace('v1.2.EFTools', 'v1.3')
        planned_spec = SPEC.replace('v1.2.EFTools', 'v1.3').replace(
            '`0.0.1.beta` | 08.13.2026', 'Unreleased | 10.02.2026')
        self.assertEqual([], self.validate(planned_bundle, planned_script, planned_spec))
        errors = self.validate(planned_bundle.replace('  Status: Unreleased\n', ''),
                               planned_script, planned_spec)
        self.assertTrue(any('Status: Unreleased' in error for error in errors))

    def test_existing_labeled_identity_bullets_are_supported(self):
        spec = SPEC.replace('| Tool version | `v1.2.EFTools` |',
                            '- **Tool version:** `v1.2.EFTools` (upstream baseline)')
        spec = spec.replace('| Status/origin | Unchanged EFTools import. |',
                            '- **Status/origin:** Unchanged EFTools import.')
        self.assertEqual([], self.validate(spec=spec))

    def test_visibility_excludes_underscore_templates_but_includes_devsandbox(self):
        for relative in ('05 DevSandbox.panel/Example.pushbutton',
                         '05 DevSandbox.panel/_Templates/Hidden.pushbutton',
                         '02 Production.panel/_Hidden.pushbutton'):
            os.makedirs(os.path.join(self.temporary.name, 'KL&A Tools_dev.tab', relative))
        bundles = list(checker.visible_bundles(self.temporary.name))
        self.assertEqual(1, len(bundles))
        self.assertIn('05 DevSandbox.panel', bundles[0])

    def test_canonical_hidden_template_conforms(self):
        path = os.path.join(ROOT, 'KL&A Tools.tab', '05 DevSandbox.panel',
                            '_Templates', '_Template.pushbutton')
        self.assertEqual([], checker.validate_bundle(path))


if __name__ == '__main__':
    unittest.main()
