"""Lazy TaskDialog-shaped Action Choice adapter; no model operations or persistence."""
from __future__ import unicode_literals

import os

try:
    from urlparse import urlparse
    _TEXT_TYPES = (basestring,)
except ImportError:
    from urllib.parse import urlparse
    _TEXT_TYPES = (str,)

from .models import DialogResult
from .choice_models import ChoiceState

_WINDOW_TYPE = None
_SEVERITY_ROLES = {
    'information': ('KlaInformationGeometry', 'KlaInfoBrush'),
    'warning': ('KlaWarningGeometry', 'KlaWarningBrush'),
    'error': ('KlaMessageErrorGeometry', 'KlaErrorBrush'),
    'success': ('KlaMessageSuccessGeometry', 'KlaReadyBrush')}


def _window_type():
    global _WINDOW_TYPE
    if _WINDOW_TYPE is not None:
        return _WINDOW_TYPE
    try:
        import wpf
    except ImportError:
        from pyrevit.framework import wpf
    from math import ceil
    from System import Action, IntPtr, Uri
    from System.Windows import (Window, Visibility, Size, Thickness,
                                WindowStartupLocation)
    from System.Windows.Automation import AutomationProperties
    from System.Windows.Controls import Button, Grid, RowDefinition, ColumnDefinition
    from System.Windows import GridLength
    from System.Windows.Input import Key, Keyboard
    from System.Windows.Interop import WindowInteropHelper
    from System.Windows.Threading import DispatcherPriority
    from GUI.window_chrome import load_window

    class ChoiceWindow(Window):
        is_action_choice = True

        def __init__(self, title, state, prompt, content, severity, details,
                     help_text, help_uri, version, owner, navigate):
            self.state = state
            self.result = DialogResult()
            self.command_buttons = {}
            self.common_buttons = {}
            self._ready = False
            self._finishing = False
            self._details_open = False
            self._details_pending = False
            self._details_growth = 0
            self._navigate = navigate
            load_window(self, os.path.join(os.path.dirname(__file__), 'ActionChoiceDialog.xaml'),
                        title, version=version, navigate=navigate, close_handler=self.close_action)
            self._kla_chrome.hide_footer()
            # Escape/Cancel and chrome Close have distinct results here.
            self._kla_chrome.detach_escape()
            self.PreviewKeyDown += self.key_down
            self.Closing += self.closing
            self.Closed += self.closed
            self.Loaded += self.loaded
            self._kla_chrome.close_button.Visibility = Visibility.Visible if state.can_cancel else Visibility.Collapsed
            if owner is not None:
                if isinstance(owner, Window):
                    self.Owner = owner
                else:
                    WindowInteropHelper(self).Owner = owner if isinstance(owner, IntPtr) else IntPtr(owner)
                self.WindowStartupLocation = WindowStartupLocation.CenterOwner
            self.instruction_text.Text = prompt or ''
            self.instruction_panel.Visibility = Visibility.Visible if prompt or severity else Visibility.Collapsed
            self.body_text.Text = content or ''
            self.body_text.Visibility = Visibility.Visible if content else Visibility.Collapsed
            if severity:
                geometry, brush = _SEVERITY_ROLES[severity]
                self.severity_icon.Content = self.FindResource(geometry)
                self.severity_icon.Foreground = self.FindResource(brush)
                self.severity_icon.Visibility = Visibility.Visible
                self.instruction_text.Foreground = self.FindResource(brush)
            for row in state.choices:
                button = Button()
                button.Style = self.FindResource('ActionCommandLink')
                button.Content = row
                button.IsEnabled = row.CanSelect
                button.Tag = ('command', row.Key)
                button.Click += self.action_clicked
                AutomationProperties.SetName(button, row.Label)
                AutomationProperties.SetHelpText(button, row.Description)
                self.commands_panel.Children.Add(button)
                self.command_buttons[row.Key] = button
            self.commands_panel.Visibility = Visibility.Visible if state.choices else Visibility.Collapsed
            # Four standard actions fit at the supported minimum width. Extra
            # buttons use a right-aligned second row with the standard 8 gap.
            columns = min(4, len(state.buttons))
            for index in range(columns):
                column = ColumnDefinition()
                column.Width = GridLength(104)
                self.buttons_panel.ColumnDefinitions.Add(column)
                if index < columns - 1:
                    gap = ColumnDefinition()
                    gap.Width = GridLength(8)
                    self.buttons_panel.ColumnDefinitions.Add(gap)
            rows = (len(state.buttons) + 3) // 4
            for index in range(rows):
                self.buttons_panel.RowDefinitions.Add(RowDefinition())
                if index < rows - 1:
                    gap = RowDefinition()
                    gap.Height = GridLength(8)
                    self.buttons_panel.RowDefinitions.Add(gap)
            for index, name in enumerate(state.buttons):
                button = Button()
                button.Style = self.FindResource('KlaButton')
                button.Content = 'OK' if name == 'ok' else name.capitalize()
                button.Tag = ('button', name)
                row = index // 4
                in_row = min(4, len(state.buttons) - row * 4)
                Grid.SetRow(button, row * 2)
                Grid.SetColumn(button, (columns - in_row + index % 4) * 2)
                button.Click += self.action_clicked
                AutomationProperties.SetName(button, button.Content)
                self.buttons_panel.Children.Add(button)
                self.common_buttons[name] = button
            self.buttons_panel.Visibility = Visibility.Visible if state.buttons else Visibility.Collapsed
            self.option_check.Content = state.checkbox_text
            self.option_check.IsChecked = state.checked == True
            self.option_check.Visibility = Visibility.Visible if state.checkbox_text else Visibility.Collapsed
            self.option_scroll.Visibility = self.option_check.Visibility
            self.details_text.Text = details or ''
            self.details_expander.Visibility = Visibility.Visible if details else Visibility.Collapsed
            self.help_panel.Visibility = Visibility.Visible if help_text or help_uri else Visibility.Collapsed
            self.help_link_text.Visibility = Visibility.Visible if help_uri else Visibility.Collapsed
            self.help_plain_text.Visibility = Visibility.Collapsed if help_uri else Visibility.Visible
            self.help_plain_text.Text = help_text or ''
            self.help_caption.Text = help_text or help_uri or ''
            if help_uri:
                self.help_link.NavigateUri = Uri(help_uri)
            self.default_button = self.target_button(state.default)
            if self.default_button is not None:
                self.default_button.IsDefault = True
            self._ready = True
            self.fit_initial()
            self._collapsed_min_height = self.MinHeight
            self._collapsed_details_height = self.details_expander.DesiredSize.Height

        def target_button(self, target):
            if target is None:
                return None
            kind, key = target
            return (self.command_buttons if kind == 'command' else self.common_buttons).get(key)

        def fit_initial(self):
            inset = self._kla_chrome.body.Margin
            bounds = Size(max(1, self.Width - inset.Left - inset.Right), float('inf'))
            height = self.FindResource('KlaChromeRow').Value + inset.Top + inset.Bottom
            for control in (self.main_content, self.option_scroll, self.details_expander,
                            self.buttons_panel, self.help_panel):
                control.Measure(bounds)
                height += control.DesiredSize.Height
            self.MinHeight = min(self.MaxHeight, ceil(height))
            self.Height = self.MinHeight

        def loaded(self, sender, args):
            self.fit_initial()
            self._collapsed_min_height = self.MinHeight
            self._collapsed_details_height = self.details_expander.DesiredSize.Height
            target = self.default_button
            if target is None or not target.IsEnabled or not target.Focus():
                self.window_body.Focus()

        def sync_checkbox(self):
            if self.state.checkbox_text:
                self.state.checked = self.option_check.IsChecked == True

        def complete(self, result):
            if result is not None:
                self.result = result
                self._finishing = True
                self.Close()

        def action_clicked(self, sender, args):
            if not self.window_body.IsEnabled or not sender.IsEnabled:
                return
            self.sync_checkbox()
            kind, key = sender.Tag
            self.complete(self.state.choose(kind, key))

        def dismiss(self, reason):
            self.sync_checkbox()
            self.complete(self.state.dismiss(reason))

        def close_action(self, sender=None, args=None):
            self.dismiss('close')

        def cancel(self, sender=None, args=None):
            self.dismiss('cancel')

        def closing(self, sender, args):
            if self._finishing:
                return
            self.sync_checkbox()
            # The X, Escape and Alt+F4 apply the cancellation policy before this
            # point and never call Close. Any close that still arrives comes from
            # code, the owner or the system, and always proceeds as close.
            self.result = self.state.dismiss('close') or self.state.forced_close()

        def closed(self, sender, args):
            self._ready = False

        def key_down(self, sender, args):
            key = args.SystemKey if args.Key == Key.System else args.Key
            if key == Key.Escape:
                args.Handled = True
                self.cancel()
            elif key == Key.F4 and args.Key == Key.System:
                # Alt+F4 is a user dismissal, so it obeys the cancellation policy.
                if not self.state.can_cancel:
                    args.Handled = True
            elif key == Key.Space:
                # Preserve checkbox toggling and text scrolling, but never let
                # WPF ButtonBase turn Space into a command or common-button Click.
                focused = Keyboard.FocusedElement
                details_toggle = self.details_expander.Template.FindName('DetailsToggle', self.details_expander)
                if focused in list(self.command_buttons.values()) + list(self.common_buttons.values()) + [self._kla_chrome.close_button, details_toggle]:
                    args.Handled = True
            elif key == Key.Enter:
                args.Handled = True
                if not self.window_body.IsEnabled:
                    return
                focused = Keyboard.FocusedElement
                if focused in list(self.command_buttons.values()) + list(self.common_buttons.values()):
                    self.action_clicked(focused, args)
                elif focused == self._kla_chrome.close_button:
                    self.close_action()
                else:
                    details_toggle = self.details_expander.Template.FindName('DetailsToggle', self.details_expander)
                    if focused == details_toggle:
                        self.details_expander.IsExpanded = not self.details_expander.IsExpanded
                    elif focused == self.help_link:
                        self.navigate_help()
                    elif self.default_button is not None:
                        self.action_clicked(self.default_button, args)

        def details_changed(self, sender, args):
            if self._ready and not self._details_pending:
                self._details_pending = True
                self.Dispatcher.BeginInvoke(DispatcherPriority.Loaded, Action(self.resize_details))

        def resize_details(self):
            self._details_pending = False
            if not self._ready:
                return
            expanded = bool(self.details_expander.IsExpanded)
            if expanded == self._details_open:
                return
            if expanded:
                self.details_expander.Measure(Size(max(1, self.details_expander.ActualWidth), float('inf')))
                extra = max(0, self.details_expander.DesiredSize.Height - self._collapsed_details_height)
                previous = self.Height
                self.MinHeight = min(self.MaxHeight, self._collapsed_min_height + extra)
                self.Height = min(self.MaxHeight, max(self.MinHeight, previous + extra))
                self._details_growth = self.Height - previous
            else:
                self.MinHeight = self._collapsed_min_height
                self.Height = max(self.MinHeight, min(self.MaxHeight, self.Height - self._details_growth))
                self._details_growth = 0
            self._details_open = expanded

        def navigate_help(self):
            if self.help_link.NavigateUri is None:
                return
            uri = self.help_link.NavigateUri.AbsoluteUri
            if self._navigate is not None:
                self._navigate(uri)
            else:
                from System.Diagnostics.Process import Start
                Start(uri)

        def help_requested(self, sender, args):
            args.Handled = True
            self.navigate_help()

    _WINDOW_TYPE = ChoiceWindow
    return _WINDOW_TYPE


def create_choice(title, choices, prompt='Choose an Action', content='', buttons=('cancel',),
                  default=None, allow_cancel=True, severity=None, details='',
                  checkbox_text='', checkbox_checked=False, help_text='', help_uri=None,
                  version=None, owner=None, navigate=None):
    """Construct an opt-in action dialog; validate configuration before WPF loads."""
    if severity is not None and severity not in tuple(_SEVERITY_ROLES):
        raise ValueError('Unknown action severity.')
    if help_uri:
        try:
            if not isinstance(help_uri, _TEXT_TYPES) or any(char.isspace() for char in help_uri):
                raise ValueError()
            parsed = urlparse(help_uri)
            if parsed.scheme.lower() not in ('https', 'http') or not parsed.hostname:
                raise ValueError()
            parsed.port  # Reject a malformed port before any WPF imports.
        except (ValueError, AttributeError):
            raise ValueError('Action help URI must be an absolute HTTP or HTTPS URL.')
    state = ChoiceState(choices, buttons, default, allow_cancel, checkbox_text, checkbox_checked)
    return _window_type()(title, state, prompt, content, severity, details,
                          help_text, help_uri, version, owner, navigate)
