# -*- coding: utf-8 -*-
"""Reusable modal alert window for KL&A pyRevit commands."""
from __future__ import print_function

import os

from WPF_Base import my_WPF
from System.Windows.Media import Brushes
import wpf


PATH_SCRIPT = os.path.dirname(__file__)
class CustomAlert(my_WPF):
    """Display a styled informational or warning message."""
    def __init__(self, message, title='KL&A Tools', is_warning=False):
        self.add_wpf_resource()
        wpf.LoadComponent(self, os.path.join(PATH_SCRIPT, 'CustomAlert.xaml'))
        self.main_title.Text = title or 'KL&A Tools'
        self.message_text.Text = message or ''
        self._set_alert_style(is_warning)
        self.ShowDialog()

    def _set_alert_style(self, is_warning):
        if is_warning:
            self.alert_heading.Text = 'Warning'
            self.alert_icon.Text = '!'
            self.alert_icon.Foreground = Brushes.Goldenrod
            return
        self.alert_heading.Text = 'Information'
        self.alert_icon.Text = 'i'
        self.alert_icon.Foreground = Brushes.MediumSeaGreen

    def button_ok(self, sender, event):
        self.Close()


def show_alert(message, title='KL&A Tools', is_warning=False):
    """Show a modal custom alert and return after the user dismisses it."""
    CustomAlert(message, title=title, is_warning=is_warning)
