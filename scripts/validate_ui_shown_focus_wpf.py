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
        # The visible prompt Label names the search box; it carries no AutomationProperties.Name of its own.
        assert peer.GetName() == 'Choose a Command' and str(peer.GetAutomationControlType()) == 'Edit'
        hint = window.search_text.Template.FindName('Watermark', window.search_text)
        assert hint.Text == 'Type to filter' and hint.Visibility == Visibility.Visible
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
        assert check.Template.FindName('CheckBorder', check).BorderBrush == window.FindResource('klcBorderColor')
        print('Shown selector: neutral initial focus, no search selection, and focused checkbox without adorner passed.')
    finally:
        window.Close()
    window = create_rename('KLCode Rename focus fixture', [RenameField('name', 'Name')])
    try:
        window.Show()
        window.Activate()
        settle_layout(window.Content)
        assert FocusManager.GetFocusedElement(window) == window.window_body
        for slot, unused in window.slots:
            for name in ('find', 'replace', 'prefix', 'suffix'):
                field = window.rule_input(slot, name)
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
        watermark = window.input_text.Template.FindName('Watermark', window.input_text)
        assert watermark.Visibility == Visibility.Visible
        assert window._kla_chrome.title.Visibility == Visibility.Collapsed
        assert watermark.Foreground == window.FindResource('klcTextColorWaterMark')
        window.input_text.Focus()
        settle_layout(window.Content)
        assert watermark.Visibility == Visibility.Visible, 'An empty field keeps its watermark while focused'
        window.input_text.Text = 'Caller text'
        window.input_text.SelectAll()
        window.window_body.Focus()
        settle_layout(window.Content)
        assert watermark.Visibility == Visibility.Collapsed, 'Nonempty text never shows the watermark'
        window.input_text.Clear()
        settle_layout(window.Content)
        assert watermark.Visibility == Visibility.Visible, 'An emptied field restores the watermark'
        if output_directory:
            render_content(window, os.path.join(output_directory, 'text-entry-shown-neutral.png'), window.Width, window.Height)
        print('Shown Text Entry: neutral initial focus, blank center title, gray watermark shown while empty, focused or not, and hidden by text passed.')
    finally:
        window.Close()
    print('Four owned fictional windows closed. No Revit, user documents or system-wide input injection used.')


validate_shown_focus()
