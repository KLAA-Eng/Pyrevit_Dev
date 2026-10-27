"""Opt-in WPF shell loader with no import-time pyRevit or document dependency.

The caller owns data, showing the window, accept/cancel semantics, modeless
lifetime, and Revit operations. This module shares only presentation.
"""
from __future__ import unicode_literals

import os

from GUI.window_metadata import WindowMetadata


def load_window(window, xaml_path, title, version=None, navigate=None):
    """Load a body with shared chrome; do not show it or change DataContext.

    ``navigate`` receives an absolute URI; Gallery supplies a local simulation.
    Ordinary callers omit it to use the same OS navigation as legacy windows.
    """
    import wpf
    from System import Uri
    from System.Windows import ResourceDictionary

    resources = ResourceDictionary()
    resources.Source = Uri(os.path.join(os.path.dirname(__file__), 'Resources',
                                       'KLCodeFoundation.xaml'))
    window.Resources.MergedDictionaries.Add(resources)
    wpf.LoadComponent(window, xaml_path)
    chrome = WindowChrome(window, WindowMetadata(title, version), navigate)
    window._kla_chrome = chrome
    return chrome


class WindowChrome(object):
    """Bind KlaWindowShell named parts without workflow inheritance."""
    def __init__(self, window, metadata, navigate):
        self.window = window
        self.navigate = navigate
        self.shell = window.window_shell
        self.shell.Tag = metadata
        window.Title = metadata.Title
        self.shell.ApplyTemplate()
        template = self.shell.Template
        self.header = template.FindName('PART_Header', self.shell)
        self.title = template.FindName('PART_Title', self.shell)
        self.close_button = template.FindName('PART_Close', self.shell)
        self.body = template.FindName('PART_Body', self.shell)
        self.footer = template.FindName('PART_Footer', self.shell)
        self.version = template.FindName('PART_Version', self.shell)
        self.prototype = template.FindName('PART_Prototype', self.shell)
        self.outreach = template.FindName('PART_Outreach', self.shell)
        self.close_button.Click += self._close
        self.header.MouseLeftButtonDown += self._drag
        self.prototype.RequestNavigate += self._navigate
        self.outreach.RequestNavigate += self._navigate

    def _close(self, sender, args):
        self.window.Close()

    def _drag(self, sender, args):
        from System.Windows.Input import MouseButtonState
        if args.LeftButton == MouseButtonState.Pressed:
            self.window.DragMove()
            args.Handled = True

    def _navigate(self, sender, args):
        args.Handled = True
        uri = args.Uri.AbsoluteUri
        if self.navigate is not None:
            self.navigate(uri)
        else:
            from System.Diagnostics.Process import Start
            Start(uri)
