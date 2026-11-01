"""Caller identity must survive shared chrome without accessing a Revit model.

The version vectors are shared with the C# adapter's tests through
lib/GUI/window_metadata_vectors.json; the footer destinations and the Close label
are data in lib/GUI/Resources/KLCodeTokens.xaml, read by the shell in both hosts.
Since the 2026-10-31 shell rework the footer captions are literal Runs in the shell.
"""
import json
import os
import sys
import unittest
from xml.etree import ElementTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib'))

from GUI.window_metadata import WindowMetadata

P = '{http://schemas.microsoft.com/winfx/2006/xaml/presentation}'
X = '{http://schemas.microsoft.com/winfx/2006/xaml}'
SYS = '{clr-namespace:System;assembly=System}'


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

    def test_chrome_data_holds_both_footer_destinations_and_the_close_label(self):
        chrome = ElementTree.parse(os.path.join(ROOT, 'lib', 'GUI', 'Resources', 'KLCodeTokens.xaml')).getroot()
        entries = {node.attrib[X + 'Key']: (node.tag, (node.text or '').strip()) for node in chrome if X + 'Key' in node.attrib}
        self.assertEqual(SYS + 'Uri', entries['klcPrototypeUri'][0])
        self.assertEqual(SYS + 'Uri', entries['klcOutreachUri'][0])
        self.assertEqual('https://forms.cloud.microsoft/r/HjuggSZqyU', entries['klcPrototypeUri'][1])
        self.assertTrue(entries['klcOutreachUri'][1].startswith('https://forms.microsoft.com/Pages/ResponsePage.aspx?'))
        self.assertEqual('Close', entries['CloseLabel'][1])
        # 2026-10-31: only Close is still a DynamicResource label; the footer captions are literal in the shell.
        self.assertEqual(set(), {'PrototypeLabel', 'OutreachLabel'} & set(entries))
        with open(os.path.join(ROOT, 'lib', 'GUI', 'Resources', 'KLCodeFoundation.xaml'), encoding='utf-8') as stream:
            foundation = stream.read()
        for reference in ('{DynamicResource CloseLabel}', '{StaticResource klcPrototypeUri}',
                          '{StaticResource klcOutreachUri}', 'Source="KLCodeTokens.xaml"'):
            self.assertIn(reference, foundation, reference)
        for removed in ('PrototypeLabel', 'OutreachLabel'):
            self.assertNotIn(removed, foundation, removed)
        shell = ElementTree.fromstring(foundation)
        links = {node.attrib[X + 'Name']: (node.attrib.get('NavigateUri'), node.find(P + 'Run').attrib.get('Text'))
                 for node in shell.iter(P + 'Hyperlink') if X + 'Name' in node.attrib}
        self.assertEqual({'klcFooter_prototype': ('{StaticResource klcPrototypeUri}', 'Prototype'),
                          'klcFooter_outreach': ('{StaticResource klcOutreachUri}', 'Outreach')}, links)


if __name__ == '__main__':
    unittest.main()
