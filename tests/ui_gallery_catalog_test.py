from __future__ import print_function

import os
import sys
import tempfile
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.ui_gallery.catalog import catalog_xaml_sources
from lib.ui_gallery.preview import can_preview


WINDOW = '<Window Title="Safe preview" xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" />'


class UiGalleryCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.external_dir = tempfile.mkdtemp()

    def tearDown(self):
        for root, directories, filenames in os.walk(self.temp_dir, topdown=False):
            for filename in filenames:
                os.remove(os.path.join(root, filename))
            for directory in directories:
                os.rmdir(os.path.join(root, directory))
        os.rmdir(self.temp_dir)
        for root, directories, filenames in os.walk(self.external_dir, topdown=False):
            for filename in filenames:
                os.remove(os.path.join(root, filename))
            for directory in directories:
                os.rmdir(os.path.join(root, directory))
        os.rmdir(self.external_dir)

    def _write(self, relative_path, contents):
        path = os.path.join(self.temp_dir, relative_path)
        parent = os.path.dirname(path)
        if not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, 'w') as xaml_file:
            xaml_file.write(contents)
        return path

    def test_catalogs_sorted_relative_paths_and_blocks_unsafe_sources(self):
        self._write('z/Control.xaml', '<UserControl />')
        self._write('a/Safe.xaml', WINDOW)
        self._write('a/Event.xaml', '<Window Click="run" />')
        self._write('a/Binding.xaml', '<Window><TextBlock Text="{Binding Name}" /></Window>')
        self._write('a/Static.xaml', '<Window><TextBlock Foreground="{StaticResource Accent}" /></Window>')
        self._write('a/Dynamic.xaml', '<Window><TextBlock Foreground="{DynamicResource Accent}" /></Window>')
        self._write('a/Namespace.xaml', '<Window xmlns:local="clr-namespace:Example" />')
        self._write('a/Class.xaml', '<Window xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" x:Class="Example.Window" />')
        self._write('a/Dictionary.xaml', '<ResourceDictionary />')
        self._write('a/External.xaml', '<Window><ResourceDictionary Source="colors.xaml" /></Window>')
        self._write('a/Broken.xaml', '<Window')
        self._write('.git/Hidden.xaml', WINDOW)

        entries = catalog_xaml_sources(self.temp_dir)
        by_path = dict((entry['relative_path'], entry) for entry in entries)

        self.assertEqual(sorted(by_path), [entry['relative_path'] for entry in entries])
        self.assertNotIn('.git/Hidden.xaml', by_path)
        self.assertEqual('Window', by_path['a/Safe.xaml']['root_kind'])
        self.assertEqual('Safe preview', by_path['a/Safe.xaml']['title'])
        self.assertTrue(by_path['a/Safe.xaml']['is_previewable'])
        self.assertEqual('Event handler attribute: Click', by_path['a/Event.xaml']['reason'])
        self.assertEqual('Binding expression', by_path['a/Binding.xaml']['reason'])
        self.assertEqual('StaticResource lookup', by_path['a/Static.xaml']['reason'])
        self.assertEqual('DynamicResource lookup', by_path['a/Dynamic.xaml']['reason'])
        self.assertEqual('Code namespace reference', by_path['a/Namespace.xaml']['reason'])
        self.assertEqual('Code namespace reference', by_path['a/Class.xaml']['reason'])
        self.assertEqual('Root is ResourceDictionary, not Window', by_path['a/Dictionary.xaml']['reason'])
        self.assertEqual('External resource dictionary', by_path['a/External.xaml']['reason'])
        self.assertEqual('Malformed XAML', by_path['a/Broken.xaml']['reason'])
        self.assertEqual('Root is UserControl, not Window', by_path['z/Control.xaml']['reason'])

    def test_blocks_each_supported_event_handler_attribute(self):
        event_names = ('Click', 'MouseDown', 'RequestNavigate', 'TextChanged')
        for event_name in event_names:
            path = self._write('events/{}.xaml'.format(event_name),
                               '<Window {}="handler" />'.format(event_name))
            relative_path = os.path.relpath(path, self.temp_dir).replace(os.sep, '/')
            entry = [item for item in catalog_xaml_sources(self.temp_dir)
                     if item['relative_path'] == relative_path][0]
            self.assertEqual('Event handler attribute: {}'.format(event_name), entry['reason'])
            self.assertFalse(entry['is_previewable'])

    def test_invalid_root_and_paths_outside_root_return_an_empty_catalog(self):
        self.assertEqual([], catalog_xaml_sources(os.path.join(self.temp_dir, 'missing')))
        self.assertEqual([], catalog_xaml_sources(os.path.join(self.temp_dir, '..')))

    def test_skips_a_xaml_symlink_that_resolves_outside_the_catalog_root(self):
        external_path = os.path.join(self.external_dir, 'External.xaml')
        with open(external_path, 'w') as xaml_file:
            xaml_file.write(WINDOW)
        os.symlink(external_path, os.path.join(self.temp_dir, 'Escaped.xaml'))

        self.assertEqual([], catalog_xaml_sources(self.temp_dir))

    def test_preview_requires_the_exact_allowlisted_fixture(self):
        fixture_path = self._write('fixtures/PreviewFixture.xaml', WINDOW)
        entries = catalog_xaml_sources(self.temp_dir)
        safe_entry = [entry for entry in entries if entry['relative_path'] == 'fixtures/PreviewFixture.xaml'][0]
        other_path = self._write('other/Safe.xaml', WINDOW)
        other_entry = [entry for entry in catalog_xaml_sources(self.temp_dir)
                       if entry['relative_path'] == 'other/Safe.xaml'][0]

        self.assertTrue(can_preview(safe_entry, fixture_path))
        self.assertFalse(can_preview(other_entry, fixture_path))
        safe_entry['is_previewable'] = False
        self.assertFalse(can_preview(safe_entry, fixture_path))


if __name__ == '__main__':
    unittest.main()
