"""Lazy bare-WPF floating chooser. No commands run and no model is queried."""
from __future__ import unicode_literals

import os

from .models import DialogResult
from .switch_models import CommandSwitch, SwitchState

_WINDOW_TYPE = None


def _window_type():
    global _WINDOW_TYPE
    if _WINDOW_TYPE is not None:
        return _WINDOW_TYPE
    try:
        import wpf
    except ImportError:
        from pyrevit.framework import wpf
    from System import Action, IntPtr
    from System.Windows import (Window, Visibility, Size, WindowStartupLocation,
                                FrameworkElement, DependencyObject)
    from System.Windows.Automation import AutomationProperties
    from System.Windows.Controls import Button, TextBox
    from System.Windows.Controls.Primitives import ToggleButton
    from System.Windows.Input import Key, MouseButtonState
    from System.Windows.Interop import WindowInteropHelper
    from System.Windows.Media import VisualTreeHelper
    from System.Windows.Threading import DispatcherPriority
    from GUI.window_chrome import shared_resources
    from GUI.window_metadata import WindowMetadata

    class CommandSwitchWindow(Window):
        def __init__(self, title, state, prompt, version, owner):
            self.state = state
            self.result = DialogResult()
            self.metadata = WindowMetadata(title, version)
            self._ready = False
            self._closed = False
            self._fit_scheduled = False
            self._command_buttons = {}
            self._toggle_buttons = {}
            resource_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                         'Resources', 'KLCodeCommandSwitch.xaml')
            self.Resources.MergedDictionaries.Add(shared_resources(resource_path))
            wpf.LoadComponent(self, os.path.join(os.path.dirname(__file__), 'CommandSwitchDialog.xaml'))
            self.Title = self.metadata.Title
            self.prompt_label.Content = prompt
            if owner is not None:
                if isinstance(owner, Window):
                    self.Owner = owner
                else:
                    WindowInteropHelper(self).Owner = owner if isinstance(owner, IntPtr) else IntPtr(owner)
                self.WindowStartupLocation = WindowStartupLocation.CenterOwner
            for row in state.switches:
                toggle = ToggleButton()
                toggle.Style = self.FindResource('KlaCommandToggle')
                toggle.Content = row.Label
                toggle.Tag = row.Key
                toggle.IsChecked = row.IsChecked
                toggle.IsEnabled = row.CanToggle
                toggle.MaxWidth = self.Width - 64
                AutomationProperties.SetName(toggle, row.Label)
                toggle.Click += self.switch_clicked
                self._toggle_buttons[row.Key] = toggle
                self.toggles_panel.Children.Add(toggle)
            for row in state.choices:
                button = Button()
                button.Style = self.FindResource('KlaCommandButton')
                button.Content = row.Label
                button.Tag = row.Key
                button.IsEnabled = row.CanSelect
                button.MaxWidth = self.Width - 64
                if row.Description:
                    button.ToolTip = row.Description
                AutomationProperties.SetName(button, row.Label)
                AutomationProperties.SetHelpText(button, row.Description)
                button.Click += self.command_clicked
                self._command_buttons[row.Key] = button
                self.commands_panel.Children.Add(button)
            self.toggles_panel.Visibility = Visibility.Visible if state.switches else Visibility.Collapsed
            self._ready = True
            self.refresh()
            self.Loaded += self.loaded
            self.Closed += self.closed

        def loaded(self, sender, args):
            # Start on the neutral panel. Typing routes into search explicitly,
            # while Tab can still reach it without an initial selected field.
            if not self.window_body.Focus():
                self.Focus()
            self.fit_height()

        def closed(self, sender, args):
            self._closed = True

        def fit_height(self):
            """The fixed-width floating panel fits content, with bounded overflow."""
            from math import ceil
            self._fit_scheduled = False
            if self._closed:
                return
            # Bound the measure as well as Window.Height. An infinite measure
            # after a layout callback can leave the ScrollViewer arranged at
            # its full content height until another parent layout occurs.
            self.Content.Measure(Size(self.Width, self.MaxHeight))
            self.Height = max(self.MinHeight, min(self.MaxHeight,
                              ceil(self.Content.DesiredSize.Height)))

        def queue_fit(self):
            if not self._fit_scheduled and not self._closed:
                self._fit_scheduled = True
                self.Dispatcher.BeginInvoke(DispatcherPriority.Loaded, Action(self.fit_height))

        def command_panel_size_changed(self, sender, args):
            if not self._ready or not args.WidthChanged:
                return
            # A pill may wrap its own label when it is longer than the panel.
            # Updating after arrangement also supports narrow offscreen QA renders.
            maximum = max(1, sender.ActualWidth - 8)
            for control in sender.Children:
                control.MaxWidth = maximum
            self.queue_fit()

        def refresh(self):
            visible = set(row.Key for row in self.state.visible_choices)
            for key, button in self._command_buttons.items():
                button.Visibility = Visibility.Visible if key in visible else Visibility.Collapsed
            self.empty_text.Text = 'No matching commands.' if self.state.choices else 'No commands available.'
            self.empty_text.Visibility = Visibility.Collapsed if visible else Visibility.Visible
            self.search_hint.Visibility = Visibility.Collapsed if self.search_text.Text else Visibility.Visible
            self.fit_height()

        def filter_changed(self, sender, args):
            if self._ready:
                self.state.query = self.search_text.Text
                self.refresh()

        def switch_clicked(self, sender, args):
            if sender.IsEnabled:
                sender.IsChecked = self.state.set_switch(sender.Tag, sender.IsChecked == True)

        def command_clicked(self, sender, args):
            # Eligibility and visibility are checked even for programmatic dispatch.
            key = sender.Tag
            if sender.IsEnabled and self.state.enter_choice(focused_key=key) is not None:
                self.result = self.state.result_for(key)
                self.Close()

        def cancel(self, sender=None, args=None):
            self.result = DialogResult()
            self.Close()

        def on_key_down(self, sender, args):
            if args.Key == Key.Escape:
                args.Handled = True
                if self.search_text.Text:
                    self.search_text.Clear()
                else:
                    self.cancel()
            elif args.Key == Key.Enter:
                args.Handled = True
                focused = next((key for key, button in self._command_buttons.items()
                                if button.IsKeyboardFocusWithin), None)
                key = self.state.enter_choice(focused_key=focused,
                                              search_focused=self.search_text.IsKeyboardFocusWithin)
                if key is not None:
                    self.command_clicked(self._command_buttons[key], args)

        def on_text_input(self, sender, args):
            text = args.Text
            if (self.search_text.IsKeyboardFocusWithin or not text
                    or not text.strip() or any(ord(character) < 32 for character in text)):
                return
            # Printable typing from a command/toggle moves into search; Tab and
            # Space retain their normal traversal/activation behavior.
            self.search_text.Focus()
            start = self.search_text.SelectionStart
            self.search_text.SelectedText = text
            self.search_text.CaretIndex = start + len(text)
            self.search_text.SelectionLength = 0
            args.Handled = True

        def drag_window(self, sender, args):
            if args.LeftButton != MouseButtonState.Pressed:
                return
            current = args.OriginalSource
            while isinstance(current, DependencyObject):
                if isinstance(current, (Button, ToggleButton, TextBox)):
                    return
                if current == sender:
                    self.DragMove()
                    args.Handled = True
                    return
                if isinstance(current, FrameworkElement) and current.Parent is not None:
                    current = current.Parent
                else:
                    current = VisualTreeHelper.GetParent(current)

    _WINDOW_TYPE = CommandSwitchWindow
    return _WINDOW_TYPE


def create_command_switch(title, choices, switches=(), prompt='Choose a Command',
                          version=None, owner=None, navigate=None):
    """Construct only; caller may ShowDialog and then inspect window.result.

    ``version`` is retained as metadata without a footer. ``navigate`` is accepted
    for the common dialog-factory signature; this window has no navigation links.
    """
    state = SwitchState(choices, switches)
    return _window_type()(title, state, prompt, version, owner)
