"""Opt-in WPF shell loader with no import-time pyRevit or document dependency.

The caller owns data, showing the window, accept/cancel semantics, modeless
lifetime, and Revit operations. This module shares only presentation.
"""
from __future__ import unicode_literals

import os

from GUI.window_metadata import WindowMetadata

COMPONENTS_XAML = os.path.join(os.path.dirname(__file__), 'Resources', 'KLCodeComponents.xaml')
_DICTIONARIES = {}


def shared_resources(xaml_path=COMPONENTS_XAML):
    """One parsed ResourceDictionary per process for the shared chain.

    Every window merges the same instance (WPF allows a dictionary in several
    MergedDictionaries), so the foundation, tokens and icons parse once instead
    of once per window; Recall's content control shares it with its window.
    """
    from System import Uri
    from System.Windows import ResourceDictionary

    if xaml_path not in _DICTIONARIES:
        resources = ResourceDictionary()
        resources.Source = Uri(xaml_path)
        _DICTIONARIES[xaml_path] = resources
    return _DICTIONARIES[xaml_path]


def load_window(window, xaml_path, title, version=None, navigate=None, close_handler=None):
    """Load a body with shared chrome; do not show it or change DataContext.

    ``navigate`` receives an absolute URI; Gallery supplies a local simulation.
    Ordinary callers omit it to use the same OS navigation as legacy windows.
    """
    import wpf

    window.Resources.MergedDictionaries.Add(shared_resources())
    host_loader = getattr(window, 'load_xaml', None)
    if callable(host_loader):
        host_loader(xaml_path)
    else:
        wpf.LoadComponent(window, xaml_path)
    chrome = WindowChrome(window, WindowMetadata(title, version), navigate, close_handler)
    window._kla_chrome = chrome
    return chrome


def fit_window_height(window):
    """Fit a chromeless shared-shell window within caller height limits.

    Call after content, expansion or width changes. A bounded window with a
    star-row ScrollViewer keeps long content accessible once MaxHeight is hit.
    """
    from math import ceil
    from System.Windows import Size

    window.Content.Measure(Size(window.Width, float('inf')))
    height = max(window.MinHeight, min(window.MaxHeight, ceil(window.Content.DesiredSize.Height)))
    window.Height = height
    return height


class WindowChrome(object):
    """Bind KlaWindowShell named parts without workflow inheritance."""
    def __init__(self, window, metadata, navigate, close_handler=None):
        self.window = window
        self.navigate = navigate
        self.close_handler = close_handler
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
        window.PreviewKeyDown += self._key
        self.header.MouseLeftButtonDown += self._drag
        self.prototype.RequestNavigate += self._navigate
        self.outreach.RequestNavigate += self._navigate

    def _close(self, sender, args):
        if self.close_handler is not None:
            self.close_handler(sender, args)
        else:
            self.window.Close()

    def hide_footer(self):
        """Omit this window's footer and row without changing the shared template."""
        from System.Windows import GridLength, Visibility

        self.footer.Visibility = Visibility.Collapsed
        self.shell.Template.FindName('PART_FooterRow', self.shell).Height = GridLength(0)

    def _key(self, sender, args):
        """Escape follows the same close policy as the header Close button."""
        from System.Windows.Input import Key
        if args.Key == Key.Escape:
            args.Handled = True
            self._close(sender, args)

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
