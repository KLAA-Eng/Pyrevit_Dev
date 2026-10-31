"""Actual WPF Action Choice contracts; uses only owned fictional windows."""
from __future__ import print_function

import os
import wpf
from System import Action, Environment
from System.Windows import (Size, Rect, Point, Visibility, RoutedEventArgs,
                            PresentationSource)
from System.Windows.Automation.Peers import UIElementAutomationPeer
from System.Windows.Controls import ScrollViewer
from System.Windows.Controls.Primitives import ButtonBase
from System.Windows.Input import Keyboard, Key, KeyEventArgs, FocusManager
from System.Windows.Media import VisualTreeHelper, PixelFormats
from System.Windows.Media.Imaging import RenderTargetBitmap, PngBitmapEncoder, BitmapFrame
from System.Windows.Threading import Dispatcher, DispatcherFrame, DispatcherPriority
from System.IO import FileStream, FileMode
from GUI.dialogs import ActionChoice, create_choice


def action_settle(window):
    frame = DispatcherFrame()
    Dispatcher.CurrentDispatcher.BeginInvoke(DispatcherPriority.Background,
        Action(lambda: setattr(frame, 'Continue', False)))
    Dispatcher.PushFrame(frame)
    window.Content.UpdateLayout()


def action_layout(window):
    for unused in range(3):
        window.Content.Measure(Size(window.Width, window.Height))
        window.Content.Arrange(Rect(0, 0, window.Width, window.Height))
        action_settle(window)


def action_descendants(parent):
    for index in range(VisualTreeHelper.GetChildrenCount(parent)):
        child = VisualTreeHelper.GetChild(parent, index)
        yield child
        for descendant in action_descendants(child):
            yield descendant


def action_click(control):
    control.RaiseEvent(RoutedEventArgs(ButtonBase.ClickEvent))


def action_capture(window, name):
    output = globals().get('output_directory', '')
    if not output:
        return
    if not os.path.isdir(output):
        os.makedirs(output)
    bitmap = RenderTargetBitmap(int(window.Width), int(window.Height), 96, 96, PixelFormats.Pbgra32)
    bitmap.Render(window.Content)
    encoder = PngBitmapEncoder()
    encoder.Frames.Add(BitmapFrame.Create(bitmap))
    stream = FileStream(os.path.join(output, name + '.png'), FileMode.Create)
    try:
        encoder.Save(stream)
    finally:
        stream.Dispose()


class ActionKey(object):
    Handled = False
    SystemKey = getattr(Key, 'None')

    def __init__(self, key):
        self.Key = key


def validate_action_choice():
    choices = [ActionChoice('hide', 'Hide Notes', 'Hide the notes in the selected views.'),
               ActionChoice('unhide', 'Unhide Notes', 'Restore the notes in the selected views.'),
               ActionChoice('blocked', 'Unavailable action', enabled=False)]
    for severity in (None, 'information', 'warning', 'error', 'success'):
        window = create_choice('Action Contract', choices, prompt='What would you like to do?',
            content='Caller-provided explanation.', severity=severity,
            details='Diagnostic detail.\n' * 8, checkbox_text='Apply to related views',
            checkbox_checked=True, help_text='Tool documentation',
            help_uri='https://example.com/tool-help', navigate=lambda uri: None)
        try:
            action_layout(window)
            assert window.Title == 'Action Contract' and window._kla_chrome.title.Visibility == Visibility.Visible
            assert window._kla_chrome.footer.Visibility == Visibility.Collapsed and window._kla_chrome.footer.ActualHeight == 0
            assert window.instruction_text.FontSize == 22 and str(window.instruction_text.FontWeight) == 'SemiBold'
            assert len(window.command_buttons) == 3 and not window.command_buttons['blocked'].IsEnabled
            assert window.default_button == window.command_buttons['hide'] and window.default_button.IsDefault
            assert window.severity_icon.Visibility == (Visibility.Visible if severity else Visibility.Collapsed)
            if severity:
                assert window.severity_icon.Foreground == window.instruction_text.Foreground
            assert window.option_check.IsChecked and window.option_check.Visibility == Visibility.Visible
            assert window.details_text.IsReadOnly and not window.details_expander.IsExpanded
            assert window.help_link.NavigateUri.AbsoluteUri == 'https://example.com/tool-help'
            original_height = window.Height
            original_viewport = window.main_scroll.ActualHeight
            window.details_expander.IsExpanded = True
            action_layout(window)
            assert window.Height > original_height and window.main_scroll.ActualHeight >= original_viewport - 1
            for unused in range(3):
                window.details_expander.IsExpanded = False
                action_layout(window)
                assert window.Height == original_height, 'Details collapse must not accumulate size drift'
                window.details_expander.IsExpanded = True
                action_layout(window)
                assert window.main_scroll.ActualHeight >= original_viewport - 1
            window.Height = 600
            for width in (480, 640):
                window.Width = width
                action_layout(window)
                assert window.Height == 600, 'Manual width changes must not resize height'
            action_capture(window, 'action-choice-' + (severity or 'plain'))
        finally:
            window.Close()

    window = create_choice('Immediate action', choices, checkbox_text='Remember for this operation')
    window.option_check.IsChecked = True
    action_click(window.command_buttons['blocked'])
    assert window.result.is_cancelled
    action_click(window.command_buttons['unhide'])
    assert window.result.action == 'accept' and window.result.value == {'kind': 'command', 'key': 'unhide', 'checked': True}
    for name in ('ok', 'yes', 'no', 'retry', 'cancel', 'close'):
        window = create_choice('Standard result', [], buttons=(name,), checkbox_text='Caller setting', checkbox_checked=True)
        action_layout(window)
        button = window.common_buttons[name]
        assert button.ActualWidth == 104 and button.ActualHeight == 28
        action_click(button)
        assert window.result.value == {'kind': 'button', 'key': name, 'checked': True}
        assert window.result.action == (name if name in ('cancel', 'close') else 'accept')
    for reason in ('cancel', 'close'):
        window = create_choice('Dismissal', choices, buttons=(), checkbox_text='Keep setting')
        window.option_check.IsChecked = True
        if reason == 'cancel':
            event = ActionKey(Key.Escape)
            window.key_down(window, event)
            assert event.Handled
        else:
            action_click(window._kla_chrome.close_button)
        assert window.result.action == reason and window.result.value['checked']
    window = create_choice('Native Close', choices)
    window.Close()
    assert window.result.action == 'close' and window.result.value['key'] == 'close'
    window = create_choice('Disabled', choices)
    window.window_body.IsEnabled = False
    action_click(window.command_buttons['hide'])
    window.key_down(window, ActionKey(Key.Enter))
    assert window.result.is_cancelled
    window.Close()
    window = create_choice('Empty', [], prompt='', content='', buttons=())
    action_layout(window)
    assert list(window.common_buttons) == ['close']
    assert window.instruction_panel.Visibility == window.commands_panel.Visibility == window.option_check.Visibility == window.details_expander.Visibility == window.help_panel.Visibility == Visibility.Collapsed
    window.Close()
    window = create_choice('Cap', choices, content=('Long caller explanation. ' * 30 + '\n') * 60,
                           details='Diagnostic line.\n' * 70, buttons=('yes', 'no', 'cancel'))
    window.details_expander.IsExpanded = True
    action_layout(window)
    assert window.Height == window.MaxHeight == 640
    assert window.main_scroll.ScrollableHeight > 0
    assert any(control.ScrollableHeight > 0 for control in action_descendants(window.details_text) if isinstance(control, ScrollViewer))
    for button in window.common_buttons.values():
        bottom = button.TranslatePoint(Point(0, button.ActualHeight), window.Content).Y
        assert bottom <= window.Height - 8
    action_capture(window, 'action-choice-long-expanded')
    window.Close()
    window = create_choice('All standard buttons and long optional text', choices,
        content='Caller explanation. ' * 200,
        buttons=('ok', 'yes', 'no', 'retry', 'cancel', 'close'),
        checkbox_text='Long caller checkbox label. ' * 150,
        help_text='Long caller help explanation. ' * 150,
        details='Diagnostic line.\n' * 70)
    window.Width = window.MinWidth
    window.details_expander.IsExpanded = True
    action_layout(window)
    assert window.Height == 640 and window.main_scroll.ActualHeight > 80
    assert window.option_scroll.ScrollableHeight > 0 and window.help_panel.ScrollableHeight > 0
    first = window.common_buttons['ok'].TranslatePoint(Point(0, 0), window.buttons_panel)
    second_row = window.common_buttons['cancel'].TranslatePoint(Point(0, 0), window.buttons_panel)
    assert second_row.Y - first.Y == 36, 'Wrapped common-button rows use an 8-unit vertical gap'
    for button in window.common_buttons.values():
        pos = button.TranslatePoint(Point(0, 0), window.Content)
        assert pos.X >= 16 and pos.X + button.ActualWidth <= window.Width - 16
        assert pos.Y + button.ActualHeight <= window.Height - 8
    action_capture(window, 'action-choice-six-buttons-long-options')
    window.Close()
    navigations = []
    window = create_choice('Help callback', [], help_text='Help', help_uri='https://example.com/help', navigate=navigations.append)
    window.navigate_help()
    assert navigations == ['https://example.com/help'] and window.result.is_cancelled
    window.Close()
    print('Action Choice WPF: severity/content, immediate commands, standard results, checkbox snapshots, optional sections, Details growth/no drift, capped scroll, disabled actions, help callback and distinct cancellation passed.')


def action_routed_key(window, control, key):
    event = KeyEventArgs(Keyboard.PrimaryDevice, PresentationSource.FromVisual(window), Environment.TickCount, key)
    event.RoutedEvent = Keyboard.PreviewKeyDownEvent
    control.RaiseEvent(event)
    return event


def action_press(window, control, key):
    """Dispatch WPF preview/bubble down/up; no physical keyboard injection."""
    down = action_routed_key(window, control, key)
    if not down.Handled:
        event = KeyEventArgs(Keyboard.PrimaryDevice, PresentationSource.FromVisual(window), Environment.TickCount, key)
        event.RoutedEvent = Keyboard.KeyDownEvent
        control.RaiseEvent(event)
    up = KeyEventArgs(Keyboard.PrimaryDevice, PresentationSource.FromVisual(window), Environment.TickCount, key)
    up.RoutedEvent = Keyboard.PreviewKeyUpEvent
    control.RaiseEvent(up)
    if not up.Handled:
        event = KeyEventArgs(Keyboard.PrimaryDevice, PresentationSource.FromVisual(window), Environment.TickCount, key)
        event.RoutedEvent = Keyboard.KeyUpEvent
        control.RaiseEvent(event)
    return down


def validate_action_choice_shown():
    rows = [ActionChoice('first', 'First'), ActionChoice('second', 'Second')]
    window = create_choice('Action keyboard fixture', rows, default=('command', 'second'),
                           checkbox_text='Caller option', details='Details')
    try:
        window.Show()
        window.Activate()
        action_settle(window)
        second = window.command_buttons['second']
        assert FocusManager.GetFocusedElement(window) == second
        peer = UIElementAutomationPeer.CreatePeerForElement(second)
        assert peer.GetName() == 'Second' and str(peer.GetAutomationControlType()) == 'Button'
        assert action_press(window, second, Key.Space).Handled
        assert window.result.is_cancelled
        window.common_buttons['cancel'].Focus()
        assert action_press(window, window.common_buttons['cancel'], Key.Space).Handled
        assert window.result.is_cancelled
        window.option_check.Focus()
        assert not window.option_check.IsChecked
        assert not action_press(window, window.option_check, Key.Space).Handled
        assert window.option_check.IsChecked, 'WPF checkbox toggles from the routed Space key sequence'
        second.Focus()
        assert action_routed_key(window, second, Key.Enter).Handled
        assert window.result.action == 'accept' and window.result.value['key'] == 'second'
    finally:
        window.Close()
    window = create_choice('No dismissal fixture', rows, buttons=(), allow_cancel=False)
    try:
        window.Show()
        window.Activate()
        action_settle(window)
        assert window._kla_chrome.close_button.Visibility == Visibility.Collapsed
        assert action_routed_key(window, window.command_buttons['first'], Key.Escape).Handled
        assert window.IsVisible and window.result.action == 'cancel'
        window.close_action()
        assert window.IsVisible, 'Chrome Close obeys the cancellation policy'
        action_click(window.command_buttons['first'])
        assert not window.IsVisible and window.result.action == 'accept'
    finally:
        window._finishing = True
        window.Close()
    window = create_choice('Host close fixture', rows, buttons=(), allow_cancel=False)
    window.Show()
    action_settle(window)
    window.Close()
    assert not window.IsVisible and window.result.action == 'close', 'A close from code, the owner or Revit always proceeds'
    window = create_choice('Explicit Cancel fixture', rows, buttons=('cancel',), allow_cancel=False)
    window.Show()
    action_settle(window)
    assert window._kla_chrome.close_button.Visibility == Visibility.Visible
    action_routed_key(window, window.command_buttons['first'], Key.Escape)
    assert not window.IsVisible and window.result.action == 'cancel'
    print('Shown Action Choice: caller default focus/UIA, real routed Enter/Space policy, native blocked Close and explicit Cancel override passed. No global input or Revit used.')


validate_action_choice()
if globals().get('show_focus_probe', False):
    validate_action_choice_shown()
