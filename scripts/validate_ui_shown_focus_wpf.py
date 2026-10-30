"""Opt-in owned-window focus acceptance, without Revit or injected user input."""
from GUI.dialogs import create_command_switch, create_selection, ActionChoice, SelectionItem
from System.Windows.Input import FocusManager
from System.Windows.Automation.Peers import UIElementAutomationPeer
from System.Windows.Controls import CheckBox


def validate_shown_focus():
    window = create_command_switch('KLCode initial focus fixture', [ActionChoice('first', 'First Command')])
    try:
        window.Show()
        window.Activate()
        settle_layout(window.Content)
        peer = UIElementAutomationPeer.CreatePeerForElement(window.search_text)
        assert peer.GetName() == 'Filter commands' and str(peer.GetAutomationControlType()) == 'Edit'
        assert FocusManager.GetFocusedElement(window) == window.window_body
        assert not window.search_text.IsKeyboardFocusWithin and window.search_text.SelectionLength == 0
        button = window._command_buttons['first']
        button.Focus()
        settle_layout(window.Content)
        assert button.IsKeyboardFocused
        assert button.BorderBrush == window.FindResource('KlaAccentBrush')
        assert button.Template.FindName('FocusMark', button) is None
        print('Shown Command Switch: UIA Edit/Filter commands, neutral initial focus, unselected search and no white button focus marks passed.')
    finally:
        window.Close()

    window = create_selection('KLCode checkbox focus fixture', [SelectionItem('row', 'Example row')])
    try:
        window.Show()
        window.Activate()
        settle_layout(window.Content)
        check = next(control for control in descendants(window.items_list) if isinstance(control, CheckBox))
        check.Focus()
        settle_layout(window.Content)
        assert check.IsKeyboardFocused
        assert check.Template.FindName('CheckBorder', check).BorderBrush == window.FindResource('KlaBorderBrush')
        print('Shown selector: focused checkbox retains the green square border without a white override.')
    finally:
        window.Close()
    print('Two owned fictional windows closed. No Revit, user documents or system-wide input injection used.')


validate_shown_focus()
