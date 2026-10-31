"""Opt-in owned-window focus acceptance, without Revit or injected user input."""
from GUI.dialogs import (create_command_switch, create_selection, ActionChoice, SelectionItem,
                         create_rename, RenameField, create_text_prompt)
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
        assert button.FocusVisualStyle is None
        assert button.BorderBrush == window.FindResource('KlaAccentBrush')
        assert button.Template.FindName('FocusMark', button) is None
        print('Shown Command Switch: neutral initial focus and focused command without any focus adorner passed.')
    finally:
        window.Close()

    window = create_selection('KLCode checkbox focus fixture', [SelectionItem('row', 'Example row')])
    try:
        window.Show()
        window.Activate()
        settle_layout(window.Content)
        assert FocusManager.GetFocusedElement(window) == window.window_body
        assert not window.filter_text.IsKeyboardFocusWithin and window.filter_text.SelectionLength == 0
        check = next(control for control in descendants(window.items_list) if isinstance(control, CheckBox))
        check.Focus()
        settle_layout(window.Content)
        assert check.IsKeyboardFocused
        assert check.FocusVisualStyle is None
        assert check.Template.FindName('CheckBorder', check).BorderBrush == window.FindResource('KlaBorderBrush')
        print('Shown selector: neutral initial focus, no search selection, and focused checkbox without adorner passed.')
    finally:
        window.Close()
    window = create_rename('KLCode Rename focus fixture', [RenameField('name', 'Name')])
    try:
        window.Show()
        window.Activate()
        settle_layout(window.Content)
        assert FocusManager.GetFocusedElement(window) == window.window_body
        for controls in window.field_controls:
            for name in ('find', 'replace', 'prefix', 'suffix'):
                field = getattr(controls, name + '_text')
                assert not field.IsKeyboardFocusWithin and field.SelectionLength == 0
                assert field.Text == ''
        if output_directory:
            render_content(window, os.path.join(output_directory, 'rename-shown-neutral.png'), window.Width, window.Height)
        print('Shown Rename: neutral initial focus, four empty unselected fields and no initial input caret passed.')
    finally:
        window.Close()
    window = create_text_prompt('KLCode Text focus fixture', 'Optional text')
    try:
        window.Show()
        window.Activate()
        settle_layout(window.Content)
        assert FocusManager.GetFocusedElement(window) == window.window_body
        assert not window.input_text.IsKeyboardFocusWithin and window.input_text.SelectionLength == 0
        assert window.input_placeholder.Visibility == Visibility.Visible
        assert window._kla_chrome.title.Visibility == Visibility.Collapsed
        assert window.input_placeholder.Foreground == window.FindResource('KlaPlaceholderBrush')
        window.input_text.Focus()
        settle_layout(window.Content)
        assert window.input_placeholder.Visibility == Visibility.Collapsed, 'Focus hides the empty watermark'
        window.input_text.Text = 'Caller text'
        window.input_text.SelectAll()
        window.window_body.Focus()
        settle_layout(window.Content)
        assert window.input_placeholder.Visibility == Visibility.Collapsed, 'Nonempty text never shows the watermark'
        window.input_text.Clear()
        settle_layout(window.Content)
        assert window.input_placeholder.Visibility == Visibility.Visible, 'Empty unfocused field restores the watermark'
        if output_directory:
            render_content(window, os.path.join(output_directory, 'text-entry-shown-neutral.png'), window.Width, window.Height)
        print('Shown Text Entry: neutral initial focus, blank center title, gray watermark hidden on focus and restored on empty blur passed.')
    finally:
        window.Close()
    print('Four owned fictional windows closed. No Revit, user documents or system-wide input injection used.')


validate_shown_focus()
