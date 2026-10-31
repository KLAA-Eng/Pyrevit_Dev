"""Lazy WPF rename request adapter, independent of current host/model context."""
from __future__ import unicode_literals

import os

from .models import DialogResult
from .rename_models import RenameState

_WINDOW_TYPE = None


class FieldControls(object):
    """Readable control handles for each caller-defined naming group."""
    pass


def _window_type():
    global _WINDOW_TYPE
    if _WINDOW_TYPE is not None:
        return _WINDOW_TYPE
    try:
        import wpf
    except ImportError:
        from pyrevit.framework import wpf
    from System import IntPtr
    from System.Windows import (Window, WindowStartupLocation, Visibility, Size,
                                Thickness, GridLength, GridUnitType, HorizontalAlignment)
    from System.Windows.Automation import AutomationProperties
    from System.Windows.Controls import (Grid, StackPanel, Label, TextBox,
                                         Border, Button, ItemsControl,
                                         ColumnDefinition, Orientation)
    from System.Windows.Input import Key
    from System.Windows.Interop import WindowInteropHelper
    from GUI.window_chrome import load_window

    class RenameWindow(Window):
        def __init__(self, title, state, version, owner, navigate):
            self.state = state
            self.result = DialogResult()
            self._ready = False
            self.field_controls = []
            self.field_containers = []
            load_window(self, os.path.join(os.path.dirname(__file__), 'RenameDialog.xaml'),
                        title, version=version, navigate=navigate, close_handler=self.cancel)
            self._baseline_min_height = self.MinHeight
            self.Width = self.MinWidth = 384 + 328 * (len(state.fields) - 1)
            if owner is not None:
                if isinstance(owner, Window):
                    self.Owner = owner
                else:
                    WindowInteropHelper(self).Owner = owner if isinstance(owner, IntPtr) else IntPtr(owner)
                self.WindowStartupLocation = WindowStartupLocation.CenterOwner
            for index, field in enumerate(state.fields):
                self.add_field(index, field)
            self._ready = True
            self.fit_height()
            self.Loaded += self.focus_input
            self.PreviewKeyDown += self.key_down

        def add_field(self, index, field):
            column = ColumnDefinition()
            column.Width = GridLength(1, GridUnitType.Star)
            self.fields_panel.ColumnDefinitions.Add(column)
            controls = FieldControls()
            controls.field = field
            controls.container = StackPanel()
            controls.container.Margin = Thickness(0, 0, 8 if index < len(self.state.fields) - 1 else 0, 0)
            Grid.SetColumn(controls.container, index)
            controls.container.Name = 'rename_field_{0}'.format(index)
            AutomationProperties.SetAutomationId(controls.container, controls.container.Name)
            controls.label = Label()
            controls.label.Style = self.FindResource('KlaPromptLabel')
            controls.label.Content = field.Label
            controls.label.Margin = Thickness(0, 0, 0, 8)
            controls.container.Children.Add(controls.label)
            controls.naming_group = Border()
            controls.naming_group.Style = self.FindResource('KlaSection')
            controls.naming_group.HorizontalAlignment = HorizontalAlignment.Left
            controls.naming_group.Padding = Thickness(12, 12, 8, 12)
            rows = ItemsControl()
            rows.Style = self.FindResource('KlaRenameFieldRows')
            for row, name in enumerate(('find', 'replace', 'prefix', 'suffix')):
                text = TextBox()
                text.Style = self.FindResource('KlaInputCompact')
                text.Text = getattr(field, name.capitalize())
                text.Name = 'rename_{0}_{1}'.format(index, name)
                AutomationProperties.SetAutomationId(text, text.Name)
                AutomationProperties.SetName(text, '{0} {1}'.format(field.Label, name))
                Grid.SetRow(text, row * 2)
                Grid.SetColumn(text, 1)
                text.TextChanged += self.text_changed
                label = Label()
                label.Style = self.FindResource('KlaCompactFieldLabel')
                label.Content = name.capitalize() + ':'
                label.Target = text
                Grid.SetRow(label, row * 2)
                rows.Items.Add(label)
                rows.Items.Add(text)
                setattr(controls, name + '_text', text)
            controls.naming_group.Child = rows
            controls.container.Children.Add(controls.naming_group)
            controls.case_actions = StackPanel()
            controls.case_actions.Orientation = Orientation.Horizontal
            controls.case_actions.HorizontalAlignment = HorizontalAlignment.Center
            controls.case_actions.Margin = self.FindResource('KlaActionTopGap')
            controls.case_actions.Visibility = Visibility.Visible if field.AllowCase else Visibility.Collapsed
            for operation, caption in (('upper', 'Uppercase'), ('lower', 'Lowercase')):
                button = Button()
                button.Style = self.FindResource('KlaButtonSecondary')
                button.Content = caption
                button.Tag = (field.Key, operation)
                button.Name = 'rename_{0}_{1}'.format(index, operation)
                AutomationProperties.SetAutomationId(button, button.Name)
                AutomationProperties.SetName(button, '{0} {1}'.format(field.Label, caption))
                if operation == 'upper':
                    button.Margin = self.FindResource('KlaPairGap')
                button.Click += self.case_clicked
                controls.case_actions.Children.Add(button)
                setattr(controls, operation + '_button', button)
            controls.container.Children.Add(controls.case_actions)
            self.fields_panel.Children.Add(controls.container)
            self.field_controls.append(controls)
            self.field_containers.append(controls.container)

        def focus_input(self, sender, args):
            self.fit_height()
            if not self.window_body.Focus():
                self.Focus()

        def fit_height(self):
            from math import ceil
            inset = self.FindResource('KlaBodyInset')
            bounds = Size(max(1, self.Width - inset.Left - inset.Right), float('inf'))
            height = 2 * self.FindResource('KlaChromeRow').Value + inset.Top + inset.Bottom
            for control in (self.fields_panel, self.validation_text, self.accept_button):
                control.Measure(bounds)
                height += control.DesiredSize.Height
            self.MinHeight = min(self.MaxHeight, max(self._baseline_min_height, ceil(height)))
            self.Height = self.MinHeight

        def feedback(self, text):
            self.validation_text.Text = text or ''
            self.validation_text.Visibility = Visibility.Visible if text else Visibility.Collapsed
            self.fit_height()

        def text_changed(self, sender, args):
            if self._ready:
                self.feedback(None)

        def sync_fields(self):
            for controls in self.field_controls:
                for name in ('find', 'replace', 'prefix', 'suffix'):
                    setattr(controls.field, name.capitalize(), getattr(controls, name + '_text').Text)

        def accept_rename(self, sender=None, args=None):
            if not self.window_body.IsEnabled or not self.accept_button.IsEnabled:
                return
            self.sync_fields()
            try:
                result = self.state.rename_result()
            except ValueError as error:
                self.feedback(error.args[0])
                return
            self.result = result
            self.Close()

        def case_clicked(self, sender, args):
            if not self.window_body.IsEnabled or not sender.IsEnabled:
                return
            key, operation = sender.Tag
            self.result = self.state.case_result(key, operation)
            self.Close()

        def key_down(self, sender, args):
            if args.Key == Key.Enter:
                args.Handled = True
                self.accept_rename()

        def cancel(self, sender=None, args=None):
            self.result = DialogResult()
            self.Close()

    _WINDOW_TYPE = RenameWindow
    return _WINDOW_TYPE


def create_rename(title, fields, version=None, owner=None, navigate=None):
    """Construct without showing; reject bad groups before loading WPF."""
    state = RenameState(fields)
    return _window_type()(title, state, version, owner, navigate)
