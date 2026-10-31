"""Lazy WPF factories. No Revit queries, transactions or script termination."""
from __future__ import unicode_literals

import os

from .models import DialogResult, SelectionGroup, SelectionState, validate_text

_TYPES = None


def _window_types():
    global _TYPES
    if _TYPES is not None:
        return _TYPES
    try:
        import wpf
    except ImportError:
        # pyRevit knows the installed engine's assembly prefix/path. Load only
        # its framework bootstrap, rather than GUI.forms or a document-bound form.
        from pyrevit.framework import wpf
    from System import IntPtr
    from System import Action
    from System.Windows import Window, Visibility
    from System.Windows.Interop import WindowInteropHelper
    from System.Windows.Automation import AutomationProperties
    from System.Windows.Controls import Button, CheckBox, ComboBox
    from System.Windows.Controls.Primitives import ToggleButton
    from System.Windows.Documents import Hyperlink
    from System.Windows.Media import VisualTreeHelper
    from System.Windows.Input import Key, Keyboard
    from System.Windows.Threading import DispatcherPriority
    from GUI.window_chrome import load_window, fit_window_height

    class DialogWindow(Window):
        def initialize(self, filename, title, version, owner, navigate):
            self.result = DialogResult()
            self._ready = False
            load_window(self, os.path.join(os.path.dirname(__file__), filename), title,
                        version=version, navigate=navigate, close_handler=self.cancel)
            if owner is not None:
                if isinstance(owner, Window):
                    self.Owner = owner
                else:
                    WindowInteropHelper(self).Owner = owner if isinstance(owner, IntPtr) else IntPtr(owner)
                from System.Windows import WindowStartupLocation
                self.WindowStartupLocation = WindowStartupLocation.CenterOwner

        def finish(self, action, value=None):
            self.result = DialogResult(action, value)
            self.Close()

        def cancel(self, sender=None, args=None):
            self.finish('cancel')

        def feedback(self, text):
            self.validation_text.Text = text or ''
            self.validation_text.Visibility = Visibility.Visible if text else Visibility.Collapsed

    class MessageWindow(DialogWindow):
        def __init__(self, title, message, severity, details,
                     version, owner, navigate):
            self.initialize('MessageDialog.xaml', title, version, owner, navigate)
            self._kla_chrome.hide_footer()
            # Keep the caller title for task switching/accessibility; the
            # message chrome intentionally has an empty center title area.
            self._kla_chrome.title.Visibility = Visibility.Collapsed
            roles = {'information': ('Information', 'KlaInformationGeometry', 'KlaInfoBrush'),
                     'warning': ('Warning', 'KlaWarningGeometry', 'KlaWarningBrush'),
                     'error': ('Error', 'KlaMessageErrorGeometry', 'KlaErrorBrush'),
                     'success': ('Success', 'KlaMessageSuccessGeometry', 'KlaReadyBrush')}
            heading, icon, brush = roles[severity]
            self.message_heading.Text = heading
            self.message_icon.Content = self.FindResource(icon)
            AutomationProperties.SetName(self.message_icon, heading)
            severity_brush = self.FindResource(brush)
            self.message_banner.BorderBrush = severity_brush
            self.message_icon.Foreground = severity_brush
            self.message_heading.Foreground = severity_brush
            self.message_body.Text = message
            self.message_details.Text = details
            self.message_expander.Visibility = Visibility.Visible if details else Visibility.Collapsed
            self.action_one.Content = 'OK'
            self._details_open = False
            self._details_growth = 0
            self._details_pending = False
            self._collapsed_min_height = self.MinHeight
            self._ready = True
            fit_window_height(self)
            self._collapsed_details_height = self.message_expander.DesiredSize.Height
            self.Closed += self.stop_layout

        def stop_layout(self, sender, args):
            self._ready = False

        def accept_message(self, sender, args):
            self.finish('ok')

        def details_changed(self, sender, args):
            if self._ready and not self._details_pending:
                # Expanded is raised before the template has made its content
                # visible. Measure after that transition, preserving manual size.
                self._details_pending = True
                self.Dispatcher.BeginInvoke(DispatcherPriority.Loaded, Action(self.resize_details))

        def resize_details(self):
            from System.Windows import Size

            self._details_pending = False
            if not self._ready:
                return
            expanded = bool(self.message_expander.IsExpanded)
            if expanded == self._details_open:
                return
            if expanded:
                self.message_expander.Measure(Size(max(1, self.message_expander.ActualWidth), float('inf')))
                extra = max(0, self.message_expander.DesiredSize.Height - self._collapsed_details_height)
                previous = self.Height
                self.MinHeight = min(self.MaxHeight, self._collapsed_min_height + extra)
                self.Height = min(self.MaxHeight, max(self.MinHeight, previous + extra))
                self._details_growth = self.Height - previous
            else:
                self.MinHeight = self._collapsed_min_height
                self.Height = max(self.MinHeight, min(self.MaxHeight, self.Height - self._details_growth))
                self._details_growth = 0
            self._details_open = expanded

    class SelectionWindow(DialogWindow):
        def __init__(self, title, items, multiple, groups, prompt, required, all_label,
                     version, owner, navigate):
            self.state = SelectionState(items, multiple, groups)
            self.required = required
            self.initialize('SelectionDialog.xaml', title, version, owner, navigate)
            self.prompt_label.Content = prompt
            self.group_filter.ItemsSource = [SelectionGroup(None, all_label)] + self.state.groups
            self.group_filter.SelectedIndex = 0
            self.group_row.Visibility = Visibility.Visible if self.state.groups else Visibility.Collapsed
            self.batch_actions.Visibility = Visibility.Visible if multiple else Visibility.Collapsed
            self._ready = True
            self.refresh()
            self.feedback(None)
            self.Loaded += self.focus_filter
            self.PreviewKeyDown += self.block_enter

        def block_enter(self, sender, args):
            # The list and filter accept only through Select; a focused button,
            # the group dropdown and the footer links keep their own Enter.
            if args.Key == Key.Enter and not isinstance(Keyboard.FocusedElement, (Button, ComboBox, Hyperlink)):
                args.Handled = True

        def focus_filter(self, sender, args):
            self.window_body.Focus()

        def refresh(self):
            self._ready = False
            self.items_list.ItemsSource = None
            self.items_list.ItemsSource = self.state.visible_items
            self._ready = True

        def feedback(self, text):
            from System.Windows import GridLength, Thickness

            DialogWindow.feedback(self, text)
            self.batch_actions.Margin = self.FindResource('KlaStackGap') if text else Thickness(0)
            self.secondary_gap.Height = self.FindResource('KlaGridSpace8') if text or self.state.multiple else GridLength(0)

        def update_checks(self, parent=None):
            # Pull changed checks into realized controls without rebuilding the list:
            # Space/Tab retain keyboard focus and scrolling stays where the user left it.
            parent = self.items_list if parent is None else parent
            for index in range(VisualTreeHelper.GetChildrenCount(parent)):
                child = VisualTreeHelper.GetChild(parent, index)
                if isinstance(child, CheckBox):
                    binding = child.GetBindingExpression(ToggleButton.IsCheckedProperty)
                    if binding is not None:
                        binding.UpdateTarget()
                self.update_checks(child)

        def filter_changed(self, sender, args):
            if not self._ready:
                return
            self.state.query = self.filter_text.Text
            group = self.group_filter.SelectedItem
            self.state.group = group.Key if group is not None else None
            self.refresh()

        def item_checked(self, sender, args):
            if self._ready:
                self.state.set_checked(sender.DataContext.Key, sender.IsChecked == True)
                self.update_checks()
                self.feedback(None)

        def check_all(self, sender, args):
            self.state.set_visible_checked(True)
            self.update_checks()
            self.feedback(None)

        def check_none(self, sender, args):
            self.state.set_visible_checked(False)
            self.update_checks()

        def accept_selection(self, sender=None, args=None):
            values = self.state.selected_values
            if self.required and not values:
                self.feedback('Select at least one item.' if self.state.multiple else 'Select an item.')
                return
            self.finish('accept', values if self.state.multiple else (values[0] if values else None))

    class TextWindow(DialogWindow):
        def __init__(self, title, prompt, default, required, validator, version, owner, navigate):
            self.required = required
            self.validator = validator
            self.initialize('TextPromptDialog.xaml', title, version, owner, navigate)
            self._kla_chrome.hide_footer()
            self._kla_chrome.title.Visibility = Visibility.Collapsed
            from System.Windows.Automation import AutomationProperties
            AutomationProperties.SetName(self.input_text, prompt or 'Text value')
            self.input_text.Text = default
            self._fitted_height = None
            self._ready = True
            self.Loaded += self.focus_input
            self.Closed += self.stop_layout
            self.fit_prompt(initial=True)

        def stop_layout(self, sender, args):
            self._ready = False

        def fit_prompt(self, initial=False):
            from math import ceil
            from System.Windows import Size

            if not self._ready:
                return
            inset = self.FindResource('KlaBodyInset')
            bounds = Size(max(1, self.Width - inset.Left - inset.Right), float('inf'))
            self.prompt_fields.Measure(bounds)
            self.prompt_actions.Measure(bounds)
            desired = (self.FindResource('KlaChromeRow').Value + inset.Top + inset.Bottom
                       + self.prompt_fields.DesiredSize.Height + self.prompt_actions.DesiredSize.Height)
            minimum = min(self.MaxHeight, ceil(desired))
            self.MinHeight = minimum
            # Follow the content until the user resizes with the grip; a resized
            # window keeps its height unless the content no longer fits.
            if (initial or self._fitted_height is None or self.Height < minimum
                    or abs(self.Height - self._fitted_height) < 0.5):
                self.Height = minimum
                self._fitted_height = minimum

        def feedback(self, text):
            DialogWindow.feedback(self, text)
            # Let visibility/template changes settle before measuring raw fields;
            # a constrained ScrollViewer reports viewport size instead of content.
            self.Dispatcher.BeginInvoke(DispatcherPriority.Loaded, Action(self.fit_prompt))

        def focus_input(self, sender, args):
            self.fit_prompt(initial=True)
            if not self.window_body.Focus():
                self.Focus()

        def text_changed(self, sender, args):
            if self._ready:
                self.feedback(None)

        def accept_text(self, sender=None, args=None):
            value = self.input_text.Text
            error = validate_text(value, self.required, self.validator)
            if error:
                self.feedback(error)
                self.input_text.Focus()
                return
            self.finish('accept', value)

    _TYPES = (MessageWindow, SelectionWindow, TextWindow)
    return _TYPES


def create_message(title, message, severity='information', details='',
                   version=None, owner=None, navigate=None):
    if severity not in ('information', 'warning', 'error', 'success'):
        raise ValueError('Unknown message severity.')
    return _window_types()[0](title, message, severity, details,
                              version, owner, navigate)


def create_selection(title, items, multiple=True, groups=None, prompt='Select Items',
                     required=True, all_label='All Items', version=None, owner=None, navigate=None):
    return _window_types()[1](title, items, multiple, groups, prompt, required, all_label, version, owner, navigate)


def create_choice(title, choices, **options):
    from .choice_window import create_choice as factory
    return factory(title, choices, **options)


def create_text_prompt(title, prompt, default='', required=False, validator=None,
                       version=None, owner=None, navigate=None):
    return _window_types()[2](title, prompt, default, required, validator, version, owner, navigate)
