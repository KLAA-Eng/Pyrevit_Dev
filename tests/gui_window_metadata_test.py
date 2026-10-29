"""Caller identity must survive shared chrome without accessing a Revit model."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib'))

from GUI.window_metadata import WindowMetadata


class WindowMetadataTests(unittest.TestCase):
    def test_footer_uses_the_calling_tools_pure_version(self):
        metadata = WindowMetadata('Find and replace views', 'v1.3')
        self.assertEqual('Find and replace views', metadata.Title)
        self.assertEqual('v1.3', metadata.VersionText)

    def test_missing_version_is_omitted_instead_of_invented(self):
        for version in (None, '', '   '):
            self.assertEqual('', WindowMetadata('Shared alert', version).VersionText)

    def test_legacy_display_prefixes_are_normalized_without_changing_tool_versions(self):
        for source in ('Version: 1.2', 'version= 1.2', 'Version 1.2', '1.2', 'v1.2'):
            self.assertEqual('v1.2', WindowMetadata('Caller', source).VersionText)
        self.assertEqual('v1.0.Source', WindowMetadata('Imported', 'v1.0.Source').VersionText)

    def test_tool_names_and_placeholders_never_become_a_version(self):
        for source in ('Core Tools', 'DevSandbox Prototype', 'Version: _', '__version__', 'v'):
            self.assertEqual('', WindowMetadata('Caller', source).VersionText, source)

    def test_metadata_strips_outer_whitespace_and_preserves_full_title(self):
        title = 'A long window title that should remain available to automation'
        metadata = WindowMetadata('  ' + title + '  ', ' v0.5 ')
        self.assertEqual(title, metadata.Title)
        self.assertEqual('v0.5', metadata.VersionText)

    def test_shared_footer_destinations_are_actual_existing_forms(self):
        metadata = WindowMetadata('Preview')
        self.assertEqual('https://forms.cloud.microsoft/r/HjuggSZqyU', metadata.PrototypeUri)
        self.assertTrue(metadata.OutreachUri.startswith('https://forms.microsoft.com/Pages/ResponsePage.aspx?'))


if __name__ == '__main__':
    unittest.main()
