# -*- coding: utf-8 -*-
"""Reference-shell checks, run inside validate_ui_gallery_wpf.py's real WPF host."""
from __future__ import print_function

from System import Uri
from System.Windows import Point, RoutedEventArgs, Size, Rect
from System.Windows.Controls.Primitives import ButtonBase
from System.Windows.Controls import TextBlock
from System.Windows.Media import VisualTreeHelper
from System.Windows.Documents import Hyperlink
from System.Windows.Navigation import RequestNavigateEventArgs

def descendants(parent):
    for index in range(VisualTreeHelper.GetChildrenCount(parent)):
        child = VisualTreeHelper.GetChild(parent, index)
        yield child
        for nested in descendants(child):
            yield nested


def validate_foundation(root, entries, tool_version, output_directory, render):
    template = next(entry for entry in entries if entry['id'] == 'kla-main-template')
    for state in template['states']:
        window = create_custom(root, dict(template, tool_version=tool_version), state)
        shell = window.window_shell
        shell.Measure(Size(432, 576))
        shell.Arrange(Rect(0, 0, 432, 576))
        shell.UpdateLayout()
        chrome = window._kla_chrome
        assert chrome.header.ActualHeight == chrome.footer.ActualHeight == 24
        assert chrome.title.Text == shell.Tag.Title
        assert chrome.title.ToolTip is None and window.ToolTip is None
        assert chrome.version.Text == 'Version: ' + tool_version
        assert str(window.FontFamily) == 'Segoe UI'
        assert window.FontSize == 12 and chrome.title.FontSize == 14
        assert window.button_main.ActualWidth == 216 and window.button_main.ActualHeight == 32
        buttons = list(window.UI_Buttons_all_none.Children)
        assert all(button.ActualWidth == 104 and button.ActualHeight == 28 for button in buttons)
        body_origin = window.window_body.TranslatePoint(Point(0, 0), shell)
        assert body_origin.X == 16 and body_origin.Y == 40
        first = buttons[0].TranslatePoint(Point(0, 0), shell)
        second = buttons[1].TranslatePoint(Point(0, 0), shell)
        main = window.button_main.TranslatePoint(Point(0, 0), shell)
        assert second.X - first.X - 104 == 8
        assert main.X == first.X and main.Y - first.Y - 28 == 8
        assert chrome.footer.TranslatePoint(Point(0, 0), shell).Y - main.Y - 32 == 16
        assert window.window_body.IsEnabled == (state != 'Disabled')
        assert chrome.close_button.IsEnabled
        if state == 'Disabled':
            labels = [element for element in descendants(window.main_ListBox)
                      if isinstance(element, TextBlock) and element.Text]
            assert labels and all(str(label.Foreground) == '#FFA6B0AD' for label in labels)
        if output_directory:
            render(window, os.path.join(output_directory, 'main-template-' + state.lower().replace(' ', '-') + '.png'), 432, 576)
        if state != 'Disabled':
            if state == 'Error':
                window.button_main.RaiseEvent(RoutedEventArgs(ButtonBase.ClickEvent))
                assert '0 fictional item(s) selected' in window.preview_result
            window.textbox_filter.Text = 'no_matching_sample_591'
            assert window.main_ListBox.Items.Count == 0
            window.textbox_filter.Text = ''
            window.button_select_none(None, None)
            assert not any(item.IsChecked for item in window._items)
            window.button_select_all(None, None)
            assert all(item.IsChecked for item in window._items)
            window.button_main.RaiseEvent(RoutedEventArgs(ButtonBase.ClickEvent))
            assert 'fictional item(s) selected' in window.preview_result
        navigation = RequestNavigateEventArgs(Uri(shell.Tag.PrototypeUri), '')
        navigation.RoutedEvent = Hyperlink.RequestNavigateEvent
        chrome.prototype.RaiseEvent(navigation)
        assert navigation.Handled and 'navigation simulated' in window.preview_result
        closed = []
        window.Closed += lambda sender, args: closed.append(True)
        chrome.close_button.RaiseEvent(RoutedEventArgs(ButtonBase.ClickEvent))
        assert closed

    # Unknown caller version must not leave placeholder footer text.
    window = create_custom(root, template, 'Normal')
    window.window_shell.Measure(Size(432, 576))
    window.window_shell.Arrange(Rect(0, 0, 432, 576))
    assert window._kla_chrome.version.Text == ''
    window.Close()
    print('Foundation: five states, real shell geometry/bindings, caller identity, simulated actions/navigation, and close event passed.')


validate_foundation(repo_root, entries, namespace['__version__'], output_directory, render_content)
