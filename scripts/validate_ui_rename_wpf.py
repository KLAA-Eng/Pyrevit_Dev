# -*- coding: utf-8 -*-
"""Real WPF rename probe; run in the installed IronPython WPF bootstrap.

Needs only lib on sys.path, the installed WPF assemblies, and optionally
output_directory. It also runs via execfile from the full Gallery probe.
No Revit/pyRevit stand-in or model/document is required.
"""
from __future__ import print_function

import os
import wpf
import clr

clr.AddReference('WindowsBase')
clr.AddReference('PresentationCore')
clr.AddReference('PresentationFramework')

from System import Action
from System.Windows import Size, Rect, Point, RoutedEventArgs, Visibility
from System.Windows.Automation import AutomationProperties
from System.Windows.Controls.Primitives import ButtonBase
from System.Windows.Input import Key
from System.Windows.Threading import Dispatcher, DispatcherFrame, DispatcherPriority

from GUI.dialogs import RenameField, create_rename
import GUI.dialogs as rename_dialogs


def rename_layout(window):
    window.Content.Measure(Size(window.Width, window.Height))
    window.Content.Arrange(Rect(0, 0, window.Width, window.Height))
    window.Content.UpdateLayout()
    frame = DispatcherFrame()
    Dispatcher.CurrentDispatcher.BeginInvoke(DispatcherPriority.Background,
        Action(lambda: setattr(frame, 'Continue', False)))
    Dispatcher.PushFrame(frame)
    window.Content.UpdateLayout()
    return window


def rename_click(button):
    button.RaiseEvent(RoutedEventArgs(ButtonBase.ClickEvent))


def rename_capture(window, path):
    from System.Windows.Media import PixelFormats
    from System.Windows.Media.Imaging import RenderTargetBitmap, PngBitmapEncoder, BitmapFrame
    from System.IO import FileStream, FileMode
    bitmap = RenderTargetBitmap(int(window.Width), int(window.Height), 96, 96, PixelFormats.Pbgra32)
    bitmap.Render(window.Content)
    encoder = PngBitmapEncoder()
    encoder.Frames.Add(BitmapFrame.Create(bitmap))
    stream = FileStream(path, FileMode.Create)
    try:
        encoder.Save(stream)
    finally:
        stream.Dispose()


def validate_rename_dialogs():
    output = globals().get('output_directory', '')
    if output and not os.path.isdir(output):
        os.makedirs(output)
    for count, width in ((1, 384), (2, 712), (3, 1040)):
        for state in ('Normal', 'Empty', 'Error', 'Disabled', 'Long content'):
            fields = [RenameField('field-{0}'.format(i), 'Naming Group {0}'.format(i + 1),
                       find='A' if state != 'Empty' else '',
                       prefix='Long literal prefix value ' * 8 if state == 'Long content' else '',
                       allow_case=i != 1) for i in range(count)]
            window = create_rename('Rename Contract', fields, version='v0.1', navigate=lambda uri: None)
            assert callable(rename_dialogs.rename), 'The public modal helper must survive lazy adapter loading'
            window.window_body.IsEnabled = state != 'Disabled'
            if state == 'Error':
                window.field_controls[-1].find_text.Text = ''
                window.field_controls[-1].replace_text.Text = 'Needs find text'
                rename_click(window.accept_button)
            rename_layout(window)
            assert window.Width == window.MinWidth == width
            assert window._kla_chrome.header.ActualHeight == window._kla_chrome.footer.ActualHeight == 24
            assert window.result.is_cancelled and window.result.value is None
            assert window.accept_button.IsDefault
            assert window.rename_scroll.ScrollableWidth == 0
            assert window.window_body.IsEnabled == (state != 'Disabled')
            assert window.validation_text.Visibility == (Visibility.Visible if state == 'Error' else Visibility.Collapsed)
            assert window.Height == window.MinHeight
            assert window.rename_scroll.ScrollableHeight == 0, 'The minimum height must fit inline feedback and Rename'
            previous = None
            for index, controls in enumerate(window.field_controls):
                position = controls.container.TranslatePoint(Point(0, 0), window.Content)
                assert controls.case_actions.Visibility == (Visibility.Collapsed if index == 1 else Visibility.Visible)
                assert position.X >= 0 and position.X + controls.container.ActualWidth <= width
                if previous is not None:
                    assert position.Y == previous.Y and position.X > previous.X, 'Groups must remain horizontal'
                previous = position
                for name in ('find', 'replace', 'prefix', 'suffix'):
                    control = getattr(controls, name + '_text')
                    point = control.TranslatePoint(Point(0, 0), window.Content)
                    assert control.ActualWidth == 240 and control.ActualHeight == 24
                    assert point.X + control.ActualWidth <= width - 16
                    assert AutomationProperties.GetAutomationId(control) == 'rename_{0}_{1}'.format(index, name)
                input_right = controls.find_text.TranslatePoint(Point(controls.find_text.ActualWidth, 0), controls.naming_group).X
                assert abs(controls.naming_group.ActualWidth - input_right - 9) < 0.1, 'Section hugs the input with an 8-unit inset plus its border'
                assert controls.find_text.TranslatePoint(Point(0, 0), controls.naming_group).X == 65, 'Compact labels use a 52-unit column'
                if controls.case_actions.Visibility == Visibility.Visible:
                    gap = controls.lower_button.TranslatePoint(Point(0, 0), controls.case_actions).X - controls.upper_button.TranslatePoint(Point(controls.upper_button.ActualWidth, 0), controls.case_actions).X
                    assert abs(gap - 8) < 0.1, 'Case actions use the standard 8-unit pair gap'
            footer_y = window._kla_chrome.footer.TranslatePoint(Point(0, 0), window.Content).Y
            button_bottom = window.accept_button.TranslatePoint(Point(0, window.accept_button.ActualHeight), window.Content).Y
            assert button_bottom <= footer_y, (count, state, window.Height, button_bottom, footer_y)
            if output:
                rename_capture(window, os.path.join(output, 'rename-{0}-{1}.png'.format(count, state.lower().replace(' ', '-'))))
            window.Close()

    originals = [RenameField('number', 'Sheet Number', allow_case=False), RenameField('name', 'Sheet Name')]
    window = create_rename('Rules', originals)
    window.field_controls[1].replace_text.Text = 'invalid without find'
    rename_click(window.accept_button)
    assert window.result.is_cancelled and window.validation_text.Text.startswith('Sheet Name:')
    assert window.MinHeight > 313
    window.field_controls[1].find_text.Text = 'A'
    assert window.MinHeight == 313, 'Clearing feedback must restore the original minimum without growth drift'
    window.field_controls[1].prefix_text.Text = 'PRE-'
    class EnterArgs(object):
        Key = Key.Enter
        Handled = False
    event = EnterArgs()
    window.key_down(window, event)
    assert event.Handled and window.result.action == 'accept'
    assert window.result.value == {'operation': 'rename', 'fields': {
        'number': {'find': '', 'replace': '', 'prefix': '', 'suffix': ''},
        'name': {'find': 'A', 'replace': 'invalid without find', 'prefix': 'PRE-', 'suffix': ''}}}
    assert originals[1].Find == originals[1].Replace == originals[1].Prefix == ''
    window = create_rename('Accept click', [RenameField('name', 'Name')])
    rename_click(window.accept_button)
    assert window.result.value['operation'] == 'rename'
    window = create_rename('Disabled actions', [RenameField('name', 'Name')])
    window.window_body.IsEnabled = False
    event = EnterArgs()
    window.key_down(window, event)
    assert event.Handled and window.result.is_cancelled
    rename_click(window.accept_button)
    rename_click(window.field_controls[0].upper_button)
    assert window.result.is_cancelled and window.result.value is None
    window.Close()
    for operation in ('upper', 'lower'):
        window = create_rename('Case', originals)
        window.field_controls[0].replace_text.Text = 'invalid other group'
        window.field_controls[1].replace_text.Text = 'invalid target group'
        rename_click(getattr(window.field_controls[1], operation + '_button'))
        assert window.result.value == {'operation': operation, 'field': 'name'}
        assert originals[1].Replace == ''
    for action in ('close', 'escape', 'native-close'):
        window = create_rename('Cancel', originals)
        if action == 'close':
            rename_click(window._kla_chrome.close_button)
        elif action == 'escape':
            class EscapeArgs(object):
                Key = Key.Escape
                Handled = False
            event = EscapeArgs()
            window._kla_chrome._key(window, event)
            assert event.Handled
        else:
            window.Close()
        assert window.result.is_cancelled and window.result.value is None
    print('Rename WPF: 15 horizontal layouts (1/2/3 groups x five states), widths, unclipped inputs, validation, request snapshots, Enter/click, separate case actions and cancellation passed.')


validate_rename_dialogs()
