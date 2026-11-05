"""Lazy WPF rename request adapter, independent of current host/model context."""
from __future__ import unicode_literals

import os

from .models import DialogResult
from .rename_models import RenameState

_WINDOW_TYPE = None
# RenameDialog.xaml spells out both groups; one field uses the primary group only.
GROUPS = ('primary', 'secondary')
RULES = ('find', 'replace', 'prefix', 'suffix')


def _window_type():
    global _WINDOW_TYPE
    if _WINDOW_TYPE is not None:
        return _WINDOW_TYPE
    try:
        import wpf
    except ImportError:
        from pyrevit.framework import wpf
    from System import IntPtr
    from System.Windows import Window, WindowStartupLocation, Visibility
    from System.Windows.Automation import AutomationProperties
    from System.Windows.Controls import Button
    from System.Windows.Input import Key, Keyboard
    from System.Windows.Interop import WindowInteropHelper
    from GUI.window_chrome import load_window, fit_window_height

    class RenameWindow(Window):
        def __init__(self, title, state, version, owner, navigate):
            self.state = state
            self.result = DialogResult()
            self._ready = False
            load_window(self, os.path.join(os.path.dirname(__file__), 'RenameDialog.xaml'),
                        title, version=version, navigate=navigate, close_handler=self.cancel)
            if owner is not None:
                if isinstance(owner, Window):
                    self.Owner = owner
                else:
                    WindowInteropHelper(self).Owner = owner if isinstance(owner, IntPtr) else IntPtr(owner)
                self.WindowStartupLocation = WindowStartupLocation.CenterOwner
            self.slots = list(zip(GROUPS, state.fields))
            for slot, field in self.slots:
                self.heading(slot).Text = field.Label
                for name in RULES:
                    text = self.rule_input(slot, name)
                    text.Text = getattr(field, name.capitalize())
                    # The Find/Replace captions repeat per group, so each input names its field.
                    AutomationProperties.SetName(text, '{0} {1}'.format(field.Label, name))
            if len(self.slots) == 1:
                self.group_secondary.Visibility = Visibility.Collapsed
            if state.case_field is None:
                self.case_actions.Visibility = Visibility.Collapsed
            self._ready = True
            self.fit_height()
            self.Loaded += self.focus_input
            self.PreviewKeyDown += self.key_down

        def heading(self, slot):
            return getattr(self, 'heading_' + slot)

        def rule_input(self, slot, name):
            return getattr(self, 'input_{0}_{1}'.format(slot, name))

        def focus_input(self, sender, args):
            self.fit_height()
            if not self.window_body.Focus():
                self.Focus()

        def fit_height(self):
            # Release the previous minimum so clearing feedback can shrink again.
            self.MinHeight = 0
            self.MinHeight = fit_window_height(self)

        def feedback(self, text):
            # klcTextBoxFeedback collapses itself while Text is empty.
            self.validation_text.Text = text or ''
            self.fit_height()

        def text_changed(self, sender, args):
            if self._ready and self.validation_text.Text:
                self.feedback(None)

        def sync_fields(self):
            for slot, field in self.slots:
                for name in RULES:
                    setattr(field, name.capitalize(), self.rule_input(slot, name).Text)

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

        def case_clicked(self, operation):
            if not self.window_body.IsEnabled or not self.case_actions.IsEnabled:
                return
            self.result = self.state.case_result(self.state.case_field.Key, operation)
            self.Close()

        def case_upper(self, sender, args):
            self.case_clicked('upper')

        def case_lower(self, sender, args):
            self.case_clicked('lower')

        def key_down(self, sender, args):
            # Enter submits from the fields. A focused button keeps its own Enter
            # (Uppercase/Lowercase act; OK is IsDefault), so one key never does two things.
            if args.Key == Key.Enter and not isinstance(Keyboard.FocusedElement, Button):
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
