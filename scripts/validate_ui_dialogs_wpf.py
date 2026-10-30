# -*- coding: utf-8 -*-
"""Actual WPF dialog contracts, executed by validate_ui_gallery_wpf.ps1."""
from __future__ import print_function

from GUI.dialogs import (SelectionItem, ActionChoice, create_message, create_selection,
                         create_choice, create_text_prompt)
from ui_gallery.dialog_data import DIALOG_FILES
from System.Windows import Visibility
from System.Windows.Controls import Button
from System.Windows.Controls.Primitives import ToggleButton
from System.Windows.Input import Key


def dialog_layout(window, width=None, height=None):
    fixed_height = height is not None
    width = width or window.Width
    height = height or window.Height
    window.Content.Measure(Size(width, height))
    window.Content.Arrange(Rect(0, 0, width, height))
    window.Content.UpdateLayout()
    settle_layout(window.Content)
    if not fixed_height and height != window.Height:
        height = window.Height
        window.Content.Measure(Size(width, height))
        window.Content.Arrange(Rect(0, 0, width, height))
        window.Content.UpdateLayout()
        settle_layout(window.Content)
    if not hasattr(window, '_kla_chrome'):
        assert str(window.Background) == '#00FFFFFF' or window.Background.Color.A == 0
        assert window.MaxHeight == 500 and not hasattr(window, 'window_shell')
        assert not hasattr(window, 'close_button')
        assert window.window_body.Focusable and not window.search_text.IsKeyboardFocusWithin
        return window
    chrome = window._kla_chrome
    assert chrome.header.ActualHeight == 24
    assert chrome.footer.ActualHeight == (0 if hasattr(window, 'input_text') else 24)
    assert str(chrome.version.Foreground) == '#FF808080'
    assert str(chrome.prototype.Foreground) == '#FF407058'
    actions = [control for control in descendants(window.window_body)
               if isinstance(control, Button) and control.Visibility == Visibility.Visible
               and control.ActualHeight > 0]
    for button in actions:
        position = button.TranslatePoint(Point(0, 0), window.Content)
        assert position.X >= 0 and position.X + button.ActualWidth <= width, (window.Title, button.Content, position.X, width)
        bottom = height if hasattr(window, 'input_text') else chrome.footer.TranslatePoint(Point(0, 0), window.Content).Y
        assert position.Y + button.ActualHeight <= bottom, (window.Title, button.Content)
    return window


def click(button):
    button.RaiseEvent(RoutedEventArgs(ButtonBase.ClickEvent))


def validate_shared_dialogs():
    window = create_message('Sizing regression', 'Keep this message visible.', details='Diagnostic detail.\n' * 8)
    dialog_layout(window)
    original_height = window.Height
    original_message_height = window.message_banner.ActualHeight
    window.message_expander.IsExpanded = True
    dialog_layout(window)
    dialog_layout(window)  # Expansion is applied after WPF updates the Expander template.
    assert window.Height > original_height, 'Opening Details must grow the window'
    assert window.message_banner.ActualHeight >= original_message_height - 1, 'Details must preserve the message viewport'
    if output_directory:
        render_content(window, os.path.join(output_directory, 'dialog-message-details-expanded.png'), window.Width, window.Height)
    for unused in range(3):
        window.message_expander.IsExpanded = False
        dialog_layout(window)
        assert window.Height == original_height
        window.message_expander.IsExpanded = True
        dialog_layout(window)
        assert window.message_banner.ActualHeight >= original_message_height - 1
    window.Height = 500
    window.Width = 480
    dialog_layout(window)
    assert window.Height == 500, 'Width changes must preserve manual height'
    window.Width = 640
    dialog_layout(window)
    assert window.Height == 500
    window.Close()
    count = 0
    for identity in sorted(DIALOG_FILES):
        entry = next(row for row in entries if row['id'] == identity)
        assert len(entry['states']) == 5 and entry['can_launch']
        for state in entry['states']:
            window = create_custom(repo_root, dict(entry, tool_version=namespace['__version__']), state)
            dialog_layout(window)
            assert window.window_body.IsEnabled == (state != 'Disabled')
            assert window.result.is_cancelled
            if hasattr(window, 'accept_button'):
                assert window.accept_button.IsDefault == (not hasattr(window, 'items_list'))
            if hasattr(window, 'items_list'):
                assert not hasattr(window, 'summary_text'), 'Selector count/visibility summary must be absent'
                assert window.state.multiple == (identity != 'dialog-list-single')
                assert window.Width == 432 and window.Height == 576
                assert window.filter_text.ActualHeight == window.group_filter.Height == 24
                assert window.accept_button.ActualWidth == 216 and window.accept_button.ActualHeight == 32
                bottom = window.accept_button.TranslatePoint(Point(0, 32), window.Content).Y
                assert abs(window._kla_chrome.footer.TranslatePoint(Point(0, 0), window.Content).Y - bottom - 8) < 1
                if window.group_row.Visibility == Visibility.Visible:
                    search = window.filter_text.TranslatePoint(Point(0, 0), window.Content)
                    group = window.group_filter.TranslatePoint(Point(0, 0), window.Content)
                    assert abs(search.X - group.X) < 1 and group.Y - search.Y == 32
                    assert window.group_filter.ActualHeight == 24
                    assert window.group_icon.Content == window.FindResource('KlaGroupGeometry')
                if window.state.multiple:
                    batch = list(window.batch_actions.Children)
                    assert [button.Content for button in batch] == ['Select All', 'Select None']
                    first = batch[0].TranslatePoint(Point(0, 0), window.Content)
                    second = batch[1].TranslatePoint(Point(0, 0), window.Content)
                    main = window.accept_button.TranslatePoint(Point(0, 0), window.Content)
                    assert first.X == main.X and second.X - first.X == 112
                    assert main.Y - first.Y - batch[0].ActualHeight == 8
                    if state != 'Error':
                        list_bottom = window.items_list.TranslatePoint(Point(0, window.items_list.ActualHeight), window.Content).Y
                        assert first.Y - list_bottom == 8
                    if state != 'Disabled':
                        assert batch[0].Background == window.FindResource('KlaComponentSurfaceBrush')
                elif state != 'Error':
                    list_bottom = window.items_list.TranslatePoint(Point(0, window.items_list.ActualHeight), window.Content).Y
                    assert window.accept_button.TranslatePoint(Point(0, 0), window.Content).Y - list_bottom == 8
                if identity == 'dialog-sheets':
                    assert window.group_filter.Items[0].Label == 'All Sheets'
            if hasattr(window, 'message_expander'):
                assert not window.message_expander.IsExpanded
            if hasattr(window, 'input_text'):
                assert window.input_text.ActualHeight == 36 and window.input_text.FontSize == 24
                assert str(window.input_text.FontWeight) == 'Bold' and str(window.input_text.FontFamily) == 'Segoe UI'
                assert window._kla_chrome.footer.Visibility == Visibility.Collapsed
                buttons = [control for control in descendants(window.window_body) if isinstance(control, Button)]
                assert len(buttons) == 1 and buttons[0] == window.accept_button
                if state in ('Normal', 'Empty', 'Error'):
                    label_bottom = window.prompt_label.TranslatePoint(Point(0, window.prompt_label.ActualHeight), window.Content).Y
                    field_top = window.input_text.TranslatePoint(Point(0, 0), window.Content).Y
                    assert abs(field_top - label_bottom - 8) < 1
                    last = window.validation_text if state == 'Error' else window.input_text
                    field_bottom = last.TranslatePoint(Point(0, last.ActualHeight), window.Content).Y
                    button_top = window.accept_button.TranslatePoint(Point(0, 0), window.Content).Y
                    assert abs(button_top - field_bottom - 8) < 1, (state, button_top - field_bottom)
                if state == 'Error':
                    assert window.prompt_scroll.ScrollableHeight == 0, 'Validation must fit without clipping'
            if output_directory and state in ('Normal', 'Error', 'Long content'):
                render_content(window, os.path.join(output_directory, identity + '-' + state.replace(' ', '-').lower() + '.png'), window.Width, window.Height)
            # Validate the smallest supported layout too, including long content.
            if hasattr(window, '_kla_chrome'):
                dialog_layout(window, window.MinWidth, window.MinHeight)
            else:
                # The non-resizable floating switch fits height to its content.
                window.Width = window.MinWidth
                window.fit_height()
                dialog_layout(window)
            if output_directory and state == 'Normal':
                render_content(window, os.path.join(output_directory, identity + '-minimum.png'), window.MinWidth,
                               window.MinHeight if hasattr(window, '_kla_chrome') else window.Height)
            window.Close()
            count += 1

    window = create_message('Result contract', 'Fictional content')
    click(window.action_one)
    assert window.result.action == 'ok'
    for severity in ('information', 'warning', 'error', 'success'):
        window = create_message('Severity', 'Fictional content', severity=severity)
        dialog_layout(window)
        assert window.message_heading.Text.lower() == severity
        window.Close()
    window = create_message('Overflow', '\n\n'.join(['Long fictional message. ' * 6] * 70), details='Diagnostic text\n' * 50)
    window.message_expander.IsExpanded = True
    dialog_layout(window)
    assert window.Height == 640 and window.message_details.IsReadOnly
    scrolls = [control for control in descendants(window.message_banner)
               if isinstance(control, ScrollViewer)]
    assert any(control.ScrollableHeight > 0 for control in scrolls)
    if output_directory:
        render_content(window, os.path.join(output_directory, 'dialog-message-overflow.png'), window.Width, window.Height)
    window.Close()

    payload_a, payload_b = object(), object()
    rows = [SelectionItem('a', 'Same label', payload_a, groups=('First',)),
            SelectionItem('b', 'Same label', payload_b, groups=('Second',)),
            SelectionItem('blocked', 'Blocked', None, enabled=False)]
    window = create_selection('Selection contracts', rows)
    dialog_layout(window)
    checks = [control for control in descendants(window.items_list) if isinstance(control, CheckBox)]
    assert len(checks) == 3 and not checks[-1].IsEnabled
    assert any(isinstance(control, TextBlock) and control.Text == 'Same label'
               for control in descendants(checks[0])), 'Selection label must render, not UIElement.ToString'
    first_check = checks[0]
    first_check.SetCurrentValue(ToggleButton.IsCheckedProperty, True)
    click(first_check)
    assert window.state.selected_values == [payload_a]
    assert first_check in list(descendants(window.items_list)), 'Checking must retain control identity/focus'
    window.group_filter.SelectedIndex = 2
    window.check_all(None, None)
    assert window.state.selected_values == [payload_a, payload_b]
    window.check_none(None, None)
    assert window.state.selected_values == [payload_a]
    window.group_filter.SelectedIndex = 0
    window.filter_text.Text = 'Blocked'
    window.check_all(None, None)
    assert window.state.selected_values == [payload_a]
    assert not rows[0].IsChecked
    click(window.accept_button)
    assert window.result.action == 'accept' and window.result.value == [payload_a]

    window = create_selection('Single', rows, multiple=False)
    dialog_layout(window)
    assert not window.state.selected_values and window.batch_actions.Visibility == Visibility.Collapsed
    window.accept_selection()
    assert window.validation_text.Visibility == Visibility.Visible
    checks = [control for control in descendants(window.items_list) if isinstance(control, CheckBox)]
    for check in checks[:2]:
        check.SetCurrentValue(ToggleButton.IsCheckedProperty, True)
        click(check)
    assert not checks[0].IsChecked and checks[1].IsChecked
    click(window.accept_button)
    assert window.result.value is payload_b

    for factory in (lambda: create_message('Cancel', 'Text'),
                    lambda: create_selection('Cancel', rows),
                    lambda: create_choice('Cancel', [ActionChoice('x', 'X')]),
                    lambda: create_text_prompt('Cancel', 'Text')):
        window = factory()
        class EscapeArgs(object):
            Key = Key.Escape
            Handled = False
        event = EscapeArgs()
        window._kla_chrome._key(window, event)
        assert event.Handled and window.result.is_cancelled
        window = factory()
        click(window._kla_chrome.close_button)
        assert window.result.is_cancelled

    for multiple in (False, True):
        window = create_selection('Explicit Select', rows, multiple=multiple)
        window.state.set_checked('a', True)
        class EnterArgs(object):
            Key = Key.Enter
            Handled = False
        event = EnterArgs()
        window.block_enter(window, event)
        assert event.Handled and window.result.is_cancelled and not window.accept_button.IsDefault
        click(window.accept_button)
        assert window.result.action == 'accept'

    from GUI.dialogs import create_command_switch, CommandSwitch
    toggles = [CommandSwitch('details', 'Include Details'), CommandSwitch('preview', 'Preview Only', checked=True)]
    choices = [ActionChoice('first', 'First Command'), ActionChoice('second', 'Second Command'),
               ActionChoice('blocked', 'Unavailable', enabled=False)]
    window = create_command_switch('Switch contract', choices, switches=toggles)
    dialog_layout(window)
    window.search_text.Text = 'First'
    dialog_layout(window)
    assert window._command_buttons['second'].Visibility == Visibility.Collapsed
    assert all(control.Visibility == Visibility.Visible for control in window._toggle_buttons.values())
    toggle = window._toggle_buttons['details']
    toggle.IsChecked = True
    click(toggle)
    assert not toggles[0].IsChecked and window.state.switches[0].IsChecked
    click(window._command_buttons['blocked'])
    assert window.result.is_cancelled
    class EscapeArgs(object):
        Key = Key.Escape
        Handled = False
    window.on_key_down(window, EscapeArgs())
    assert window.search_text.Text == '' and window.result.is_cancelled
    click(window._command_buttons['first'])
    assert window.result.value == {'command': 'first', 'switches': {'details': True, 'preview': True}}
    window = create_command_switch('Cancel', choices, switches=toggles)
    window.on_key_down(window, EscapeArgs())
    assert window.result.is_cancelled
    window = create_command_switch('Close', choices)
    window.Close()
    assert window.result.is_cancelled

    window = create_choice('Actions', [ActionChoice('a', 'A'), ActionChoice('b', 'B', enabled=False)])
    dialog_layout(window)
    assert window.choices_list.SelectedItem is None and not window.accept_button.IsEnabled
    window.choices_list.SelectedIndex = 1
    assert not window.accept_button.IsEnabled
    window.accept_choice()
    assert window.result.is_cancelled
    window.choices_list.SelectedIndex = 0
    assert window.accept_button.IsEnabled
    click(window.accept_button)
    assert window.result.value == 'a'

    window = create_text_prompt('Blank', 'Optional value')
    click(window.accept_button)
    assert window.result.action == 'accept' and window.result.value == ''
    window = create_text_prompt('Validated', 'Required value', required=True,
        validator=lambda value: 'Use at least three characters.' if len(value.strip()) < 3 else None)
    click(window.accept_button)
    assert window.result.is_cancelled and window.validation_text.Text == 'Enter a value.'
    window.input_text.Text = 'x'
    click(window.accept_button)
    assert window.validation_text.Text == 'Use at least three characters.'
    window.input_text.Text = ' raw '
    click(window.accept_button)
    assert window.result.value == ' raw '
    print('Shared dialogs: {} normal/minimum state layouts; Message expansion/manual-size regression, large footerless Text, explicit Select, five presets, command/toggle/filter/result contracts and deferred Action choice regression passed.'.format(count))


validate_shared_dialogs()
