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

from GUI.dialogs import RenameField, create_rename, sheet_fields, view_fields
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
    layouts = (('views', view_fields, 384), ('sheets', sheet_fields, 712),
               ('generic', lambda: [RenameField('mark', 'Mark')], 384))
    for layout, preset, width in layouts:
        for state in ('Normal', 'Empty', 'Error', 'Disabled', 'Long content'):
            fields = preset()
            for field in fields:
                field.Find = 'A' if state != 'Empty' else ''
                field.Prefix = 'Long literal prefix value ' * 8 if state == 'Long content' else ''
            window = create_rename('Rename Contract', fields, version='v0.1', navigate=lambda uri: None)
            assert callable(rename_dialogs.rename), 'The public modal helper must survive lazy adapter loading'
            window.window_body.IsEnabled = state != 'Disabled'
            last = window.slots[-1][0]
            if state == 'Error':
                window.rule_input(last, 'find').Text = ''
                window.rule_input(last, 'replace').Text = 'Needs find text'
                rename_click(window.accept_button)
            rename_layout(window)
            assert window.Width == window.MinWidth == width
            assert window._kla_chrome.header.ActualHeight == window._kla_chrome.footer.ActualHeight == 24
            assert window.result.is_cancelled and window.result.value is None
            assert window.accept_button.IsDefault
            assert window.window_body.IsEnabled == (state != 'Disabled')
            assert window.validation_text.Visibility == (Visibility.Visible if state == 'Error' else Visibility.Collapsed)
            assert window.Height == window.MinHeight
            assert window.group_secondary.Visibility == (Visibility.Visible if len(fields) == 2 else Visibility.Collapsed)
            assert window.case_actions.Visibility == Visibility.Visible, 'Every preset has one case field'
            body = window._kla_chrome.body.Margin
            header_bottom = window._kla_chrome.header.TranslatePoint(Point(0, window._kla_chrome.header.ActualHeight), window.Content).Y
            previous = None
            for slot, field in window.slots:
                group = getattr(window, 'group_' + slot)
                position = group.TranslatePoint(Point(0, 0), window.Content)
                assert position.X >= 0 and position.X + group.ActualWidth <= width
                if previous is not None:
                    assert position.Y == previous.Y and position.X > previous.X, 'Groups must remain horizontal'
                previous = position
                assert window.heading(slot).Text == field.Label
                assert abs(window.heading(slot).TranslatePoint(Point(0, 0), window.Content).Y - header_bottom - body.Top) < 0.1
                for name in ('find', 'replace', 'prefix', 'suffix'):
                    control = window.rule_input(slot, name)
                    point = control.TranslatePoint(Point(0, 0), window.Content)
                    assert control.ActualWidth == 240 and control.ActualHeight == 24
                    assert point.X + control.ActualWidth <= width - body.Right
                    assert AutomationProperties.GetName(control) == '{0} {1}'.format(field.Label, name)
            gap = window.lower_button.TranslatePoint(Point(0, 0), window.case_actions).X - window.upper_button.TranslatePoint(Point(window.upper_button.ActualWidth, 0), window.case_actions).X
            assert abs(gap - 8) < 0.1, 'Case actions use the standard 8-unit pair gap'
            footer_y = window._kla_chrome.footer.TranslatePoint(Point(0, 0), window.Content).Y
            button_bottom = window.accept_button.TranslatePoint(Point(0, window.accept_button.ActualHeight), window.Content).Y
            assert abs(footer_y - button_bottom - body.Bottom) < 0.1, (layout, state, window.Height, button_bottom, footer_y)
            if output:
                rename_capture(window, os.path.join(output, 'rename-{0}-{1}.png'.format(layout, state.lower().replace(' ', '-'))))
            window.Close()

    originals = [RenameField('number', 'Sheet Number', allow_case=False), RenameField('name', 'Sheet Name')]
    window = create_rename('Long headings', [
        RenameField('first', 'Very long caller supplied property name for a Revit family parameter'),
        RenameField('second', 'Second property', allow_case=False)])
    rename_layout(window)
    assert window.heading_primary.ActualHeight > 24, 'Long caller headings wrap within their group'
    for slot in ('primary', 'secondary'):
        group = getattr(window, 'group_' + slot)
        right = group.TranslatePoint(Point(group.ActualWidth, 0), window.Content).X
        assert right <= window.Width - 16, 'Long headings cannot push the second group offscreen'
    window.Close()
    window = create_rename('No case actions', [RenameField('name', 'Name', allow_case=False)])
    rename_layout(window)
    assert window.case_actions.Visibility == Visibility.Collapsed
    no_case_height = window.Height
    window.Close()
    window = create_rename('Case actions', [RenameField('name', 'Name')])
    rename_layout(window)
    assert window.Height - no_case_height == 36, 'Omitted case actions must not reserve their old height'
    window.Close()
    window = create_rename('Rules', originals)
    baseline_height = window.MinHeight
    window.input_secondary_replace.Text = 'invalid without find'
    rename_click(window.accept_button)
    assert window.result.is_cancelled and window.validation_text.Text.startswith('Sheet Name:')
    assert window.MinHeight > baseline_height
    window.input_secondary_find.Text = 'A'
    assert window.MinHeight == baseline_height, 'Clearing feedback must restore the fitted minimum without growth drift'
    window.input_secondary_prefix.Text = 'PRE-'
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
    assert window.result.is_cancelled and window.validation_text.Text == 'Enter at least one rename rule.'
    window.input_primary_suffix.Text = '-A'
    rename_click(window.accept_button)
    assert window.result.value['operation'] == 'rename'
    window = create_rename('Disabled actions', [RenameField('name', 'Name')])
    window.window_body.IsEnabled = False
    event = EnterArgs()
    window.key_down(window, event)
    assert event.Handled and window.result.is_cancelled
    rename_click(window.accept_button)
    rename_click(window.upper_button)
    assert window.result.is_cancelled and window.result.value is None
    window.Close()
    for operation in ('upper', 'lower'):
        window = create_rename('Case', originals)
        window.input_primary_replace.Text = 'invalid other group'
        window.input_secondary_replace.Text = 'invalid target group'
        rename_click(getattr(window, operation + '_button'))
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
    print('Rename WPF: 15 layouts (Views/Sheets/Generic x five states), widths, named unclipped inputs, validation, request snapshots, Enter/click, separate case actions and cancellation passed.')


validate_rename_dialogs()
