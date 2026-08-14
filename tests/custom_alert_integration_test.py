from __future__ import print_function

import os
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUI_DIR = os.path.join(PROJECT_ROOT, 'lib', 'GUI')
STEEL_PSF_SCRIPT = os.path.join(
    PROJECT_ROOT,
    'KL&A Tools_dev.tab',
    '05 DevSandbox.panel',
    'Prototype.pulldown',
    'Steel PSF.pushbutton',
    'script.py')


class SteelPSFDefaultMessageTests(unittest.TestCase):
    def test_steel_psf_uses_default_pyrevit_alerts_for_messages(self):
        with open(STEEL_PSF_SCRIPT, 'r') as script_file:
            source = script_file.read()

        self.assertNotIn('from GUI.CustomAlert import show_alert', source)
        self.assertNotIn('from GUI.SteelPSFReport import show_steel_psf_report', source)
        self.assertIn('forms.alert(', source)
        self.assertIn('script.get_output()', source)


if __name__ == '__main__':
    unittest.main()
