"""Real-resource focus contracts; invoked by the installed IronPython WPF probe.

No window is shown. This verifies style/template isolation, not physical
keyboard-versus-pointer focus routing, which remains a live acceptance check.
"""
import wpf
from System.Windows import Window
from System.Windows.Controls import Button, CheckBox, RadioButton
from System.Windows.Controls.Primitives import ToggleButton
from GUI.window_chrome import shared_resources


def validate_keyboard_focus_resources():
    import os

    host = Window()
    host.Resources.MergedDictionaries.Add(shared_resources())
    host.Resources.MergedDictionaries.Add(shared_resources(os.path.join(
        repo_root, 'lib', 'GUI', 'Resources', 'KLCodeCommandSwitch.xaml')))
    roles = [(Button, name) for name in ('KlaButton', 'KlaButtonPrimary',
             'KlaButtonSecondary', 'KlaLinkButton', 'KlaGhostButton',
             'KlaIconButton', 'KlaIconTextButton', 'KlaButtonClose', 'KlaCommandButton')]
    roles += [(CheckBox, 'KlaCheck'), (CheckBox, 'KlaDialogCheck'),
              (RadioButton, 'KlaRadioButton'), (RadioButton, 'KlaSegmentButton'),
              (ToggleButton, 'KlaToggle'), (ToggleButton, 'KlaCommandToggle')]
    for control_type, role in roles:
        control = control_type()
        control.Style = host.FindResource(role)
        control.Content = 'Focus fixture'
        control.ApplyTemplate()
        assert control.Focusable and control.IsTabStop, role
        assert control.FocusVisualStyle is None, role
        assert control.Template.FindName('FocusMark', control) is None, role
        assert control.Template.FindName('ToggleFocus', control) is None, role
        if isinstance(control, CheckBox):
            square = control.Template.FindName('CheckBorder', control)
            assert square.BorderBrush == host.FindResource('KlaBorderBrush'), role
            control.IsChecked = True
            assert square.BorderBrush == host.FindResource('KlaBorderBrush'), role
            assert control.Template.FindName('CheckMark', control).Visibility.ToString() == 'Visible', role

    assert host.FindResource('KlaFocusBrush').Color.ToString() == '#FFE5E4E2', 'Input/dropdown focus stays unchanged'
    host.Close()
    print('Shared focus: {} actual style roles retain keyboard operation with no focus adorners; checked state and input focus roles preserved.'.format(len(roles)))


validate_keyboard_focus_resources()
