"""Lazy bare-WPF chooser adapter; distinct from the public command_switch helper."""
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
                                SystemParameters)
    from System.Windows.Automation import AutomationProperties
    from System.Windows.Controls import Button, ContextMenu
    from System.Windows.Controls.Primitives import ToggleButton
    from System.Windows.Input import (Key, Mouse, MouseButton, MouseButtonState,
                                      CaptureMode, MouseEventHandler)
    from System.Windows.Interop import WindowInteropHelper
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
            self._drag_origin = None
            self._dragged = False
            self._moving = False
            self._capture_pending = False
            self._context_menu_open = False
            self._context_menu = None
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
            self.Closing += self.closing
            self.Closed += self.closed
            self.Deactivated += self.deactivated
            self.Activated += self.activated
            self.ContextMenuClosing += self.context_closed
            self.AddHandler(Mouse.LostMouseCaptureEvent,
                            MouseEventHandler(self.capture_lost), True)

        def loaded(self, sender, args):
            # Start on the neutral panel. Typing routes into search explicitly,
            # while Tab can still reach it without an initial selected field.
            if not self.window_body.Focus():
                self.Focus()
            self.fit_height()
            self.capture_pointer()

        def closing(self, sender, args):
            # Closing a modal window deactivates it before Closed is raised.
            # Guard that event against a recursive cancel/Close call.
            self._closed = True

        def closed(self, sender, args):
            self._closed = True
            if self._context_menu is not None:
                self._context_menu.IsOpen = False
            if self.IsMouseCaptureWithin:
                Mouse.Capture(None)

        def deactivated(self, sender, args):
            if self.IsVisible and not self._closed:
                self.cancel()

        def activated(self, sender, args):
            self.capture_pointer()

        def context_closed(self, sender, args):
            if self._context_menu is not None:
                self._context_menu.Closed -= self.context_closed
                self._context_menu = None
            self._context_menu_open = False
            self.capture_lost(sender, args)

        def capture_pointer(self):
            """Popup-like outside clicks also work against a disabled modal owner."""
            self._capture_pending = False
            captured = Mouse.Captured
            if (isinstance(captured, ContextMenu) and captured.PlacementTarget is not None
                    and Window.GetWindow(captured.PlacementTarget) == self):
                # Context menus live in a separate popup tree. Let that popup
                # own capture until it closes, including programmatic menus.
                if self._context_menu != captured:
                    self._context_menu = captured
                    captured.Closed += self.context_closed
                self._context_menu_open = True
                return
            if (self.IsVisible and self.IsActive and not self._closed
                    and not self._moving and not self._context_menu_open
                    and not self.IsMouseCaptureWithin):
                Mouse.Capture(self, CaptureMode.SubTree)

        def capture_lost(self, sender, args):
            # Buttons and text editing temporarily capture their own mouse.
            # Re-arm after their release, without stealing a descendant capture.
            if not self._capture_pending and not self._closed and not self._moving:
                self._capture_pending = True
                self.Dispatcher.BeginInvoke(DispatcherPriority.Input,
                                            Action(self.capture_pointer))

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
            if self._dragged:
                sender.IsChecked = next(row.IsChecked for row in self.state.switches
                                        if row.Key == sender.Tag)
                return
            if sender.IsEnabled:
                sender.IsChecked = self.state.set_switch(sender.Tag, sender.IsChecked == True)

        def command_clicked(self, sender, args):
            # Eligibility and visibility are checked even for programmatic dispatch.
            key = sender.Tag
            if (not self._dragged and sender.IsEnabled
                    and self.state.enter_choice(focused_key=key) is not None):
                self.result = self.state.result_for(key)
                self.Close()

        def cancel(self, sender=None, args=None):
            self.result = DialogResult()
            self.Close()

        def on_key_down(self, sender, args):
            if self._closed:
                return
            self._dragged = False
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

        def pointer_down(self, sender, args):
            if self._closed or self._context_menu_open:
                return
            point = args.GetPosition(self)
            # The Window is 16 larger than the visible panel on every side; a
            # click in that transparent margin is outside.
            panel = args.GetPosition(self.switch_panel)
            if not (0 <= panel.X <= self.switch_panel.ActualWidth
                    and 0 <= panel.Y <= self.switch_panel.ActualHeight):
                args.Handled = True
                self.cancel()
                return
            if args.ChangedButton != MouseButton.Left:
                return
            self._drag_origin = point
            self._dragged = False

        def pointer_move(self, sender, args):
            if self._drag_origin is None or self._moving:
                return
            if args.LeftButton != MouseButtonState.Pressed:
                self._drag_origin = None
                return
            point = args.GetPosition(self)
            if (abs(point.X - self._drag_origin.X) < SystemParameters.MinimumHorizontalDragDistance
                    and abs(point.Y - self._drag_origin.Y) < SystemParameters.MinimumVerticalDragDistance):
                return
            self._dragged = True
            self._moving = True
            self._drag_origin = None
            args.Handled = True
            try:
                # Release a button/text selection capture before the native move
                # loop, so finishing a drag never invokes the underlying action.
                Mouse.Capture(None)
                self.DragMove()
            finally:
                self._moving = False
                self.capture_pointer()

        def pointer_up(self, sender, args):
            self._drag_origin = None
            if self._dragged:
                args.Handled = True
            self.capture_lost(sender, args)

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
