"""Real-resource focus contracts; invoked by the installed IronPython WPF probe.

No window is shown. This verifies style/template isolation, not physical
keyboard-versus-pointer focus routing, which remains a live acceptance check.
"""
import wpf
from System.Windows import Window, Size, Rect
from System.Windows.Controls import Button, CheckBox, RadioButton, Control
from System.Windows.Controls.Primitives import ToggleButton
from GUI.window_chrome import shared_resources


def validate_keyboard_focus_resources():
    import os

    host = Window()
    host.Resources.MergedDictionaries.Add(shared_resources())
    host.Resources.MergedDictionaries.Add(shared_resources(os.path.join(
        repo_root, 'lib', 'GUI', 'Resources', 'KLCodeCommandSwitch.xaml')))
    focus_style = host.FindResource('KlaKeyboardFocusVisual')
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
        assert control.FocusVisualStyle == focus_style, role
        assert control.Template.FindName('FocusMark', control) is None, role
        assert control.Template.FindName('ToggleFocus', control) is None, role
        if isinstance(control, CheckBox):
            square = control.Template.FindName('CheckBorder', control)
            assert square.BorderBrush == host.FindResource('KlaBorderBrush'), role
            control.IsChecked = True
            assert square.BorderBrush == host.FindResource('KlaBorderBrush'), role
            assert control.Template.FindName('CheckMark', control).Visibility.ToString() == 'Visible', role

    # Instantiate the adorner template separately: it is decorative and never
    # joins the button/checkbox content tree or changes its layout dimensions.
    adorner = Control()
    adorner.Style = focus_style
    adorner.Measure(Size(104, 28))
    adorner.Arrange(Rect(0, 0, 104, 28))
    adorner.ApplyTemplate()
    assert not adorner.Focusable and not adorner.IsHitTestVisible
    assert host.FindResource('KlaKeyboardFocusBrush').Color.ToString() == '#FF91C8A6'
    assert host.FindResource('KlaFocusBrush').Color.ToString() == '#FFE5E4E2', 'Input/dropdown focus stays unchanged'
    host.Close()
    print('Shared focus: {} actual style/template roles retain keyboard focus, omit click-focus marks and preserve checkbox state/input focus roles.'.format(len(roles)))


validate_keyboard_focus_resources()
