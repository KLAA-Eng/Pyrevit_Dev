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


class CustomAlertIntegrationTests(unittest.TestCase):
    def test_steel_psf_uses_the_reusable_custom_alert(self):
        with open(STEEL_PSF_SCRIPT, 'r') as script_file:
            source = script_file.read()

        self.assertIn('from GUI.CustomAlert import show_alert', source)
        self.assertNotIn('forms.alert(', source)
        self.assertTrue(os.path.isfile(os.path.join(GUI_DIR, 'CustomAlert.py')))
        self.assertTrue(os.path.isfile(os.path.join(GUI_DIR, 'CustomAlert.xaml')))


if __name__ == '__main__':
    unittest.main()
