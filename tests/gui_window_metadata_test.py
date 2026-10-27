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
        self.assertEqual('Version: v1.3', metadata.VersionText)

    def test_missing_version_is_omitted_instead_of_invented(self):
        for version in (None, '', '   '):
            self.assertEqual('', WindowMetadata('Shared alert', version).VersionText)

    def test_metadata_strips_outer_whitespace_and_preserves_full_title(self):
        title = 'A long window title that should remain available to automation'
        metadata = WindowMetadata('  ' + title + '  ', ' v0.5 ')
        self.assertEqual(title, metadata.Title)
        self.assertEqual('Version: v0.5', metadata.VersionText)

    def test_shared_footer_destinations_are_actual_existing_forms(self):
        metadata = WindowMetadata('Preview')
        self.assertEqual('https://forms.cloud.microsoft/r/HjuggSZqyU', metadata.PrototypeUri)
        self.assertTrue(metadata.OutreachUri.startswith('https://forms.microsoft.com/Pages/ResponsePage.aspx?'))


if __name__ == '__main__':
    unittest.main()
