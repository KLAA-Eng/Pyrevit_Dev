# -*- coding: utf-8 -*-
import os

from GUI.forms import my_WPF
from GUI.window_chrome import load_window


class DuplicateSheets(my_WPF):
    """Shared presentation for the Duplicate Sheets command."""

    def __init__(self, title, run_handler, duplicate_option_handler, version=None):
        self._run_handler = run_handler
        self._duplicate_option_handler = duplicate_option_handler
        load_window(self, os.path.join(os.path.dirname(__file__), 'DuplicateSheets.xaml'),
                    title, version)

    def button_close(self, sender, e):
        self.Close()

    def radiobutton_duplicate_option(self, sender, e):
        self._duplicate_option_handler(sender)

    def button_run(self, sender, e):
        self.Close()
        self._run_handler()
