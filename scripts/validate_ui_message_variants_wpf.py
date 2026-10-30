# -*- coding: utf-8 -*-
"""Real installed-IronPython/WPF Message contracts; execfile after the probe bootstrap.

The PowerShell runner supplies the installed WPF runtime and library path.
These fixtures own their windows and never attach to Revit.
"""
from __future__ import print_function

import wpf
from System import Action
from System.Windows import Size, Rect, Point, Visibility, RoutedEventArgs
from System.Windows.Controls import ScrollViewer
from System.Windows.Controls.Primitives import ButtonBase
from System.Windows.Automation.Peers import ToggleButtonAutomationPeer, PatternInterface
from System.Windows.Media import VisualTreeHelper
from System.Windows.Threading import Dispatcher, DispatcherFrame, DispatcherPriority
from GUI.dialogs import create_message


def message_descendants(root):
    for index in range(VisualTreeHelper.GetChildrenCount(root)):
        child = VisualTreeHelper.GetChild(root, index)
        yield child
        for descendant in message_descendants(child):
            yield descendant


def message_layout(window):
    for unused in range(3):
        window.Content.Measure(Size(window.Width, window.Height))
        window.Content.Arrange(Rect(0, 0, window.Width, window.Height))
        window.Content.UpdateLayout()
        frame = DispatcherFrame()
        Dispatcher.CurrentDispatcher.BeginInvoke(DispatcherPriority.Background,
            Action(lambda: setattr(frame, 'Continue', False)))
        Dispatcher.PushFrame(frame)
    window.Content.UpdateLayout()


def validate_message_variants():
    roles = {'information': ('KlaInformationGeometry', 'KlaInfoBrush'),
             'warning': ('KlaWarningGeometry', 'KlaWarningBrush'),
             'error': ('KlaMessageErrorGeometry', 'KlaErrorBrush'),
             'success': ('KlaMessageSuccessGeometry', 'KlaReadyBrush')}
    count = 0
    for severity, (geometry, brush) in sorted(roles.items()):
        for with_details in (False, True):
            window = create_message('Message variants', 'First line of the message.\nSecond line.',
                                    severity=severity, details='First diagnostic line.\nSecond line.' if with_details else '')
            try:
                message_layout(window)
                assert window.message_heading.FontSize == 18
                assert str(window.message_heading.FontWeight) == 'SemiBold'
                assert str(window.message_heading.FontFamily) == 'Segoe UI'
                assert window.message_icon.ActualWidth == window.message_icon.ActualHeight == 24
                assert window.message_icon.Content == window.FindResource(geometry)
                expected_brush = window.FindResource(brush)
                assert window.message_banner.BorderBrush == expected_brush
                assert window.message_icon.Foreground == window.message_heading.Foreground == expected_brush
                assert window.message_body.FontSize == window.message_details.FontSize == 12
                assert window.message_expander.Visibility == (Visibility.Visible if with_details else Visibility.Collapsed)
                assert not window.message_expander.IsExpanded
                assert window.action_one.Content == 'OK' and window.action_one.IsDefault
                initial_height, initial_body = window.Height, window.message_banner.ActualHeight
                if with_details:
                    header = window.message_expander.Template.FindName('DetailsToggle', window.message_expander)
                    icon = header.Template.FindName('DetailsChevron', header)
                    assert icon.ActualWidth == icon.ActualHeight == 16
                    assert icon.Content == window.FindResource('KlaChevronRightGeometry')
                    peer = ToggleButtonAutomationPeer(header)
                    assert peer.GetName() == 'Details'
                    peer.GetPattern(PatternInterface.Toggle).Toggle()
                    message_layout(window)
                    assert window.message_expander.IsExpanded
                    assert icon.Content == window.FindResource('KlaChevronDownGeometry')
                    assert window.Height > initial_height
                    assert window.message_banner.ActualHeight >= initial_body - 1
                    body_left = window.message_body.TranslatePoint(Point(0, 0), window.window_body).X
                    detail_origin = window.message_details.TranslatePoint(Point(0, 0), window.window_body).X
                    character = window.message_details.GetRectFromCharacterIndex(0)
                    assert abs(detail_origin + character.Left - body_left) < 0.1, (body_left, detail_origin + character.Left)
                    # TextBoxView exposes the padded text viewport; prove both edges,
                    # rather than comparing outer TextBox rectangles.
                    text_view = next(node for node in message_descendants(window.message_details)
                                     if node.GetType().Name == 'TextBoxView')
                    detail_right = text_view.TranslatePoint(Point(text_view.ActualWidth, 0), window.window_body).X
                    body_right = body_left + window.message_body.ActualWidth
                    assert abs(detail_right - body_right) < 0.1, (body_right, detail_right)
                    assert window.message_details.IsReadOnly
                    window.message_details.Select(0, 5)
                    assert window.message_details.SelectedText == 'First'
                    for unused in range(3):
                        window.message_expander.IsExpanded = False
                        message_layout(window)
                        assert window.Height == initial_height
                        assert icon.Content == window.FindResource('KlaChevronRightGeometry')
                        window.message_expander.IsExpanded = True
                        message_layout(window)
                        assert window.message_banner.ActualHeight >= initial_body - 1
                    window.Height = 500
                    for width in (480, 640):
                        window.Width = width
                        message_layout(window)
                        assert window.Height == 500
                count += 1
            finally:
                window.Close()
    window = create_message('Long Message', ('Long body text. ' * 60 + '\n') * 60,
                            details='Diagnostic line.\n' * 60)
    try:
        window.message_expander.IsExpanded = True
        message_layout(window)
        assert window.Height == window.MaxHeight == 640
        assert any(node.ScrollableHeight > 0 for node in message_descendants(window.message_banner)
                   if isinstance(node, ScrollViewer))
        assert any(node.ScrollableHeight > 0 for node in message_descendants(window.message_details)
                   if isinstance(node, ScrollViewer))
    finally:
        window.Close()
    window = create_message('Result', 'OK result')
    window.action_one.RaiseEvent(RoutedEventArgs(ButtonBase.ClickEvent))
    assert window.result.action == 'ok'
    print('Message variants: %d severity/details combinations; glyph edges, toggle, copy selection, sizing, cap and scroll contracts passed.' % count)


validate_message_variants()
