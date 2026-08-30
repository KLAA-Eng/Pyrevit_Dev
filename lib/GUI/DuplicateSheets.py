# -*- coding: utf-8 -*-
import os

from GUI.forms import my_WPF

from clr import AddReference
AddReference("System")
from System.Diagnostics.Process import Start
from System.Windows.Window import DragMove
from System.Windows.Input import MouseButtonState
import wpf


class DuplicateSheets(my_WPF):
    """Shared presentation for the Duplicate Sheets command."""

    def __init__(self, title, run_handler, duplicate_option_handler):
        self._run_handler = run_handler
        self._duplicate_option_handler = duplicate_option_handler
        self.add_wpf_resource()
        wpf.LoadComponent(self, os.path.join(os.path.dirname(__file__), 'DuplicateSheets.xaml'))
        self.main_title.Text = title

    def button_close(self, sender, e):
        self.Close()

    def Hyperlink_RequestNavigate(self, sender, e):
        Start(e.Uri.AbsoluteUri)

    def header_drag(self, sender, e):
        if e.LeftButton == MouseButtonState.Pressed:
            DragMove(self)

    def radiobutton_duplicate_option(self, sender, e):
        self._duplicate_option_handler(sender)

    def button_run(self, sender, e):
        self.Close()
        self._run_handler()
