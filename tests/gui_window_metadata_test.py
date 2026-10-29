"""Caller identity must survive shared chrome without accessing a Revit model.

The version vectors are shared with the C# adapter's tests through
lib/GUI/window_metadata_vectors.json; the footer destinations and labels are
data in lib/GUI/Resources/KLCodeChrome.xaml, read by the shell in both hosts.
"""
import json
import os
import sys
import unittest
from xml.etree import ElementTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))

from GUI.window_metadata import WindowMetadata

X = '{http://schemas.microsoft.com/winfx/2006/xaml}'
SYS = '{clr-namespace:System;assembly=mscorlib}'


def vectors(family):
    with open(os.path.join(ROOT, 'lib', 'GUI', 'window_metadata_vectors.json'), encoding='utf-8') as stream:
        return json.load(stream)[family]


class WindowMetadataTests(unittest.TestCase):
    def test_version_text_matches_the_shared_vectors(self):
        for vector in vectors('version'):
            self.assertEqual(vector['expected'], WindowMetadata('Caller', vector['input']).VersionText, repr(vector['input']))

    def test_title_is_trimmed_and_never_invents_a_version(self):
        for vector in vectors('title'):
            metadata = WindowMetadata(vector['input'])
            self.assertEqual(vector['expected'], metadata.Title, repr(vector['input']))
            self.assertEqual('', metadata.VersionText)

    def test_metadata_carries_identity_only(self):
        metadata = WindowMetadata('Find and replace views', 'v1.3')
        self.assertEqual({'Title', 'VersionText'}, set(vars(metadata)))

    def test_chrome_data_holds_both_footer_destinations_and_the_default_labels(self):
        chrome = ElementTree.parse(os.path.join(ROOT, 'lib', 'GUI', 'Resources', 'KLCodeChrome.xaml')).getroot()
        entries = {node.attrib[X + 'Key']: (node.tag, (node.text or '').strip()) for node in chrome}
        self.assertEqual(SYS + 'Uri', entries['KlaPrototypeUri'][0])
        self.assertEqual(SYS + 'Uri', entries['KlaOutreachUri'][0])
        self.assertEqual('https://forms.cloud.microsoft/r/HjuggSZqyU', entries['KlaPrototypeUri'][1])
        self.assertTrue(entries['KlaOutreachUri'][1].startswith('https://forms.microsoft.com/Pages/ResponsePage.aspx?'))
        self.assertEqual({'Close', 'Prototype', 'Outreach'}, {entries[k][1] for k in ('CloseLabel', 'PrototypeLabel', 'OutreachLabel')})
        with open(os.path.join(ROOT, 'lib', 'GUI', 'Resources', 'KLCodeFoundation.xaml'), encoding='utf-8') as stream:
            foundation = stream.read()
        for reference in ('{DynamicResource CloseLabel}', '{DynamicResource PrototypeLabel}', '{DynamicResource OutreachLabel}',
                          '{StaticResource KlaPrototypeUri}', '{StaticResource KlaOutreachUri}', 'Source="KLCodeChrome.xaml"'):
            self.assertIn(reference, foundation, reference)


if __name__ == '__main__':
    unittest.main()
