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
    width = width or window.Width
    height = height or window.Height
    window.Content.Measure(Size(width, height))
    window.Content.Arrange(Rect(0, 0, width, height))
    window.Content.UpdateLayout()
    settle_layout(window.Content)
    chrome = window._kla_chrome
    assert chrome.header.ActualHeight == chrome.footer.ActualHeight == 24
    assert str(chrome.version.Foreground) == '#FF808080'
    assert str(chrome.prototype.Foreground) == '#FF407058'
    actions = [control for control in descendants(window.window_body)
               if isinstance(control, Button) and control.Visibility == Visibility.Visible
               and control.ActualHeight > 0]
    for button in actions:
        position = button.TranslatePoint(Point(0, 0), window.Content)
        assert position.X >= 0 and position.X + button.ActualWidth <= width, (window.Title, button.Content, position.X, width)
        assert position.Y + button.ActualHeight <= chrome.footer.TranslatePoint(Point(0, 0), window.Content).Y, (window.Title, button.Content)
    return window


def click(button):
    button.RaiseEvent(RoutedEventArgs(ButtonBase.ClickEvent))


def validate_shared_dialogs():
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
                assert window.accept_button.IsDefault
            if hasattr(window, 'message_expander'):
                assert not window.message_expander.IsExpanded
            if output_directory and state in ('Normal', 'Error', 'Long content'):
                render_content(window, os.path.join(output_directory, identity + '-' + state.replace(' ', '-').lower() + '.png'), window.Width, window.Height)
            # Validate the smallest supported layout too, including long content.
            dialog_layout(window, window.MinWidth, window.MinHeight)
            if output_directory and state == 'Normal':
                render_content(window, os.path.join(output_directory, identity + '-minimum.png'), window.MinWidth, window.MinHeight)
            window.Close()
            count += 1

    for action in ('ok', 'yes', 'no', 'retry', 'cancel'):
        window = create_message('Result contract', 'Fictional content', buttons=(action,))
        click(window.action_one)
        assert window.result.action == action
    for severity in ('information', 'warning', 'error', 'success'):
        window = create_message('Severity', 'Fictional content', severity=severity)
        dialog_layout(window)
        assert window.message_heading.Text.lower() == severity
        window.Close()
    window = create_message('Confirmation', 'Continue?', buttons=('yes', 'no', 'cancel'))
    assert window.action_three.IsDefault and not window.action_one.IsDefault
    click(window.action_two)
    assert window.result.action == 'no' and not window.result.is_cancelled

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
    print('Shared dialogs: {} normal/minimum state layouts; explicit actions, severities, cancellation handlers, selection identity/groups/filtering/disabled rows, single selection, action eligibility and text validation passed.'.format(count))


validate_shared_dialogs()
