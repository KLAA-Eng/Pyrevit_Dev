from __future__ import print_function

import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.hanger_check.classify import STATUS_OK, is_problem
from lib.hanger_check.sizes import (
    MISMATCH_BOTH,
    MISMATCH_SUPPORTED,
    MISMATCH_SUPPORTING,
    compare_size,
    mismatch_label,
    parse_size,
)


class ParseSizeTest(unittest.TestCase):
    def test_hanger_key_formats(self):
        self.assertEqual(parse_size('6 3/4x15 GLB'),
                         {'plies': None, 'width': 6.75, 'depth': 15.0, 'material': 'GLB'})
        self.assertEqual(parse_size('(3)14" LVL'),
                         {'plies': 3, 'width': None, 'depth': 14.0, 'material': 'LVL'})
        self.assertEqual(parse_size('(2)9 1/2" LVL')['depth'], 9.5)
        self.assertEqual(parse_size('(2)2x10'),
                         {'plies': 2, 'width': 2.0, 'depth': 10.0, 'material': None})

    def test_revit_type_labels(self):
        self.assertEqual(parse_size('Glulam: 6 3/4" x 15"')['width'], 6.75)
        self.assertEqual(parse_size('LVL 2.0E: 1-3/4" x 11-7/8"')['depth'], 11.875)
        self.assertEqual(parse_size('TJI 210: 11 7/8"')['depth'], 11.875)


class CompareSizeTest(unittest.TestCase):
    def test_glulam_header_matches(self):
        self.assertEqual(compare_size('6 3/4x15 GLB', 'Glulam: 6 3/4" x 15"'), (True, ''))

    def test_glulam_header_wrong_depth(self):
        ok, reason = compare_size('6 3/4x15 GLB', 'Glulam: 6 3/4" x 13 1/2"')
        self.assertFalse(ok)
        self.assertEqual(reason, 'depth differs')

    def test_ply_lvl_matches_built_up_or_single_ply(self):
        self.assertTrue(compare_size('(3)14" LVL', 'LVL: 5 1/4" x 14"')[0])
        self.assertTrue(compare_size('(3)14" LVL', 'LVL: 1 3/4" x 14"')[0])
        self.assertFalse(compare_size('(3)14" LVL', 'LVL: 3 1/2" x 14"')[0])

    def test_material_mismatch(self):
        ok, reason = compare_size('(2)9 1/2" LVL', 'Parallam PSL: 3 1/2" x 9 1/2"')
        self.assertFalse(ok)
        self.assertEqual(reason, 'material differs')

    def test_parameters_used_when_label_has_no_size(self):
        self.assertTrue(compare_size('6 3/4x15 GLB', 'Glulam: GL-1', 6.75, 15.0)[0])
        self.assertFalse(compare_size('6 3/4x15 GLB', 'Glulam: GL-1', 6.75, 12.0)[0])

    def test_sawn_lumber_nominal(self):
        self.assertTrue(compare_size('(2)2x10', 'Dimension Lumber: 2x10')[0])

    def test_undecided_without_sizes(self):
        self.assertIsNone(compare_size('SEE PLAN', 'LVL: 1 3/4" x 14"')[0])
        self.assertIsNone(compare_size('(3)14" LVL', 'LVL: Custom')[0])


class MismatchLabelTest(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(mismatch_label(True, True), '')
        self.assertEqual(mismatch_label(None, None), '')
        self.assertEqual(mismatch_label(False, True), MISMATCH_SUPPORTED)
        self.assertEqual(mismatch_label(None, False), MISMATCH_SUPPORTING)
        self.assertEqual(mismatch_label(False, False), MISMATCH_BOTH)

    def test_mismatch_is_a_problem(self):
        result = {'status': STATUS_OK, 'mismatch': MISMATCH_SUPPORTED}
        self.assertTrue(is_problem(result))
        self.assertFalse(is_problem({'status': STATUS_OK, 'mismatch': ''}))


class SourceEncodingTest(unittest.TestCase):
    def test_sources_are_ascii_for_ironpython(self):
        # IronPython 2.7 refuses non-ASCII source without a coding line.
        folders = [os.path.join(PROJECT_ROOT, 'lib', 'hanger_check')]
        pulldown = os.path.join(PROJECT_ROOT, 'KL&A Tools_dev.tab', '05 DevSandbox.panel',
                                'Prototype.pulldown')
        folders += [os.path.join(pulldown, name) for name in
                    ('Check Hanger Locations.pushbutton', 'Hanger Highlights.pushbutton')]
        for folder in folders:
            for name in os.listdir(folder):
                if name.endswith('.py'):
                    with open(os.path.join(folder, name), 'rb') as stream:
                        data = stream.read()
                    self.assertFalse(any(byte > 127 for byte in bytearray(data)),
                                     '%s contains non-ASCII text' % name)


if __name__ == '__main__':
    unittest.main()
