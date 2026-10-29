# -*- coding: utf-8 -*-
"""Reusable modal alert window for KL&A pyRevit commands."""
from __future__ import print_function

import os

from WPF_Base import my_WPF  # not GUI.forms: that module imports the Revit-bound SelectFromDict at load time
from GUI.window_chrome import load_window, fit_window_height


PATH_SCRIPT = os.path.dirname(__file__)
class CustomAlert(my_WPF):
    """Display a styled informational or warning message."""
    def __init__(self, message, title='KL&A Tools', is_warning=False):
        load_window(self, os.path.join(PATH_SCRIPT, 'CustomAlert.xaml'),
                    title or 'KL&A Tools')
        self.message_text.Text = message or ''
        self._set_alert_style(is_warning)
        fit_window_height(self)
        self.ShowDialog()

    def _set_alert_style(self, is_warning):
        if is_warning:
            self.alert_heading.Text = 'Warning'
            self.alert_icon.Content = self.Resources['KlaWarningGeometry']
            self.alert_banner.BorderBrush = self.Resources['KlaWarningBrush']
            return
        self.alert_heading.Text = 'Information'
        self.alert_icon.Content = self.Resources['KlaInformationGeometry']
        self.alert_banner.BorderBrush = self.Resources['KlaInfoBrush']

def show_alert(message, title='KL&A Tools', is_warning=False):
    """Show a modal custom alert and return after the user dismisses it."""
    CustomAlert(message, title=title, is_warning=is_warning)
