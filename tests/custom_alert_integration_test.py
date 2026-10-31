from __future__ import print_function

import os
import importlib.util
import sys
import types
import unittest
from unittest.mock import patch

from repo_paths import TAB_NAME


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUI_DIR = os.path.join(PROJECT_ROOT, 'lib', 'GUI')
STEEL_PSF_SCRIPT = os.path.join(
    PROJECT_ROOT,
    TAB_NAME,
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


class CustomAlertPresentationTests(unittest.TestCase):
    def load_adapter(self):
        actions = []
        def module(**values):
            boundary = types.ModuleType('boundary')
            boundary.__dict__.update(values)
            return boundary
        class Window(object):
            def add_wpf_resource(self):
                pass
            def ShowDialog(self):
                actions.append('show')
        def controls(window):
            for name in ('main_title', 'message_text', 'alert_heading', 'alert_icon', 'alert_banner'):
                setattr(window, name, types.SimpleNamespace())
            window.Resources = dict((key, key) for key in (
                'klgeoWarnAlert', 'klgeoInfoAlert', 'KlaWarningBrush', 'KlaInfoBrush'))
        def load(window, path, title, version=None):
            controls(window)
            window.Title = title
            window.version = version
            window._kla_chrome = module(hide_footer=lambda: actions.append('hide footer'))
            actions.append('load')
        def fit(window):
            self.assertTrue(hasattr(window.alert_icon, 'Content'))
            actions.append('fit')
        def legacy_load(window, path):
            controls(window)
            actions.append('legacy load')
        host = {
            'WPF_Base': module(my_WPF=Window),
            'GUI.window_chrome': module(load_window=load, fit_window_height=fit),
            'System.Windows.Media': module(Brushes=module(Goldenrod='warning', MediumSeaGreen='information')),
            'System.Windows.Automation': module(AutomationProperties=module(SetName=lambda element, name: setattr(element, 'automation_name', name))),
            'wpf': module(LoadComponent=legacy_load),
        }
        path = os.path.join(GUI_DIR, 'CustomAlert.py')
        spec = importlib.util.spec_from_file_location('custom_alert_adapter_under_test', path)
        adapter = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, host):
            spec.loader.exec_module(adapter)
        return adapter, actions

    def test_warning_sets_shared_icon_and_border_before_fitting_and_showing(self):
        adapter, actions = self.load_adapter()
        window = adapter.CustomAlert('Review this warning.', title='Caller title', is_warning=True)
        self.assertEqual('Warning', window.alert_icon.automation_name)
        self.assertEqual(['load', 'hide footer', 'fit', 'show'], actions)
        self.assertEqual('Caller title', window.Title)
        self.assertIsNone(window.version)
        self.assertEqual('Review this warning.', window.message_text.Text)
        self.assertEqual('Warning', window.alert_heading.Text)
        self.assertEqual('klgeoWarnAlert', window.alert_icon.Content)
        self.assertEqual('KlaWarningBrush', window.alert_banner.BorderBrush)

    def test_information_keeps_empty_input_fallback_and_public_wrapper(self):
        adapter, actions = self.load_adapter()
        window = adapter.CustomAlert(None, title=None)
        self.assertEqual(['load', 'hide footer', 'fit', 'show'], actions)
        self.assertEqual('KL&A Tools', window.Title)
        self.assertEqual('', window.message_text.Text)
        self.assertEqual('Information', window.alert_heading.Text)
        self.assertEqual('klgeoInfoAlert', window.alert_icon.Content)
        self.assertEqual('KlaInfoBrush', window.alert_banner.BorderBrush)
        with patch.object(adapter, 'CustomAlert') as constructor:
            self.assertIsNone(adapter.show_alert('Message', 'Tool', True))
            constructor.assert_called_once_with('Message', title='Tool', is_warning=True)


if __name__ == '__main__':
    unittest.main()
