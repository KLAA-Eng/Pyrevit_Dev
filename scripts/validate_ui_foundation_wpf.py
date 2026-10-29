# -*- coding: utf-8 -*-
"""Reference-shell checks, run inside validate_ui_gallery_wpf.py's real WPF host."""
from __future__ import print_function

from System import Uri
from System.Windows import Point, RoutedEventArgs, Size, Rect, FlowDirection
from System.Windows.Controls.Primitives import ButtonBase
from System.Windows.Controls import TextBlock, CheckBox
from System.Windows.Controls.Primitives import ScrollBar
from System.Windows.Media import (VisualTreeHelper, FormattedText, Typeface,
                                  DrawingVisual, VisualBrush, PixelFormats)
from System.Windows.Media.Imaging import RenderTargetBitmap, PngBitmapEncoder, BitmapFrame
from System.IO import FileStream, FileMode
from System.Globalization import CultureInfo
from System.Windows.Documents import Hyperlink
from System.Windows.Navigation import RequestNavigateEventArgs

def descendants(parent):
    for index in range(VisualTreeHelper.GetChildrenCount(parent)):
        child = VisualTreeHelper.GetChild(parent, index)
        yield child
        for nested in descendants(child):
            yield nested


def render_close_detail(button, filename):
    """Render the actual control at 4x density without changing its layout."""
    visual = DrawingVisual()
    context = visual.RenderOpen()
    context.DrawRectangle(VisualBrush(button), None, Rect(0, 0, 60, 18))
    context.Close()
    bitmap = RenderTargetBitmap(240, 72, 384, 384, PixelFormats.Pbgra32)
    bitmap.Render(visual)
    encoder = PngBitmapEncoder()
    encoder.Frames.Add(BitmapFrame.Create(bitmap))
    stream = FileStream(filename, FileMode.Create)
    try:
        encoder.Save(stream)
    finally:
        stream.Dispose()


def validate_foundation(root, entries, tool_version, output_directory, render):
    rooms_entry = next(entry for entry in entries if entry['id'] == 'kla-create-from-rooms')
    rooms = create_custom(root, rooms_entry, 'Normal')
    rooms.Content.Measure(Size(400, 406))
    rooms.Content.Arrange(Rect(0, 0, 400, 406))
    rooms.Content.UpdateLayout()
    room_row = rooms.main_ListBox.ItemContainerGenerator.ContainerFromIndex(0)
    room_check = next(item for item in descendants(room_row) if isinstance(item, CheckBox))
    room_text = next(item for item in descendants(room_check) if isinstance(item, TextBlock))
    room_row_height = room_row.ActualHeight
    room_text_gap = room_text.TranslatePoint(Point(0, 0), room_check).X - 16
    room_filter_height = rooms.textbox_filter.ActualHeight
    print('Create from rooms: search {} high at y={}; row {} high, padding {}; checkbox text gap {}.'.format(
        rooms.textbox_filter.ActualHeight, rooms.textbox_filter.TranslatePoint(Point(0, 0), rooms.Content).Y,
        room_row.ActualHeight, room_row.Padding,
        room_text.TranslatePoint(Point(0, 0), room_check).X - 16))
    if output_directory:
        render(rooms, os.path.join(output_directory, 'create-from-rooms-reference.png'), 400, 406)
    rooms.Close()
    selection_entry = next(entry for entry in entries if entry['id'] == 'kla-select-from-dict')
    selection = create_custom(root, selection_entry, 'Normal')
    selection.Content.Measure(Size(432, 576))
    selection.Content.Arrange(Rect(0, 0, 432, 576))
    selection.Content.UpdateLayout()
    native_row = selection.main_ListBox.ItemContainerGenerator.ContainerFromIndex(0)
    native_row_template = native_row.Template
    prompt_font_size = selection.text_label.FontSize
    assert prompt_font_size == 14
    if output_directory:
        render(selection, os.path.join(output_directory, 'list-selection-reference.png'), 432, 576)
    selection.Close()
    template = next(entry for entry in entries if entry['id'] == 'template-selection')
    for state in template['states']:
        window = create_custom(root, dict(template, tool_version=tool_version), state)
        shell = window.window_shell
        shell.Measure(Size(432, 576))
        shell.Arrange(Rect(0, 0, 432, 576))
        shell.UpdateLayout()
        chrome = window._kla_chrome
        if state == 'Normal':
            row = window.main_ListBox.ItemContainerGenerator.ContainerFromIndex(0)
            check = next(item for item in descendants(row) if isinstance(item, CheckBox))
            text = next(item for item in descendants(check) if isinstance(item, TextBlock))
            bars = [item for item in descendants(window.main_ListBox) if isinstance(item, ScrollBar)]
            assert row.ActualHeight == room_row_height
            assert row.Template == native_row_template
            assert window.text_label.Content == 'Select Elements:'
            label = next(part for part in descendants(chrome.close_button) if isinstance(part, TextBlock))
            glyphs = FormattedText(label.Text, CultureInfo.InvariantCulture, FlowDirection.LeftToRight,
                                   Typeface(label.FontFamily, label.FontStyle, label.FontWeight, label.FontStretch),
                                   label.FontSize, label.Foreground).BuildGeometry(Point(0, 0)).Bounds
            origin = label.TranslatePoint(Point(0, 0), chrome.close_button)
            center_x = origin.X + glyphs.X + glyphs.Width / 2
            center_y = origin.Y + glyphs.Y + glyphs.Height / 2
            assert abs(center_x - chrome.close_button.ActualWidth / 2) < 0.25
            assert abs(center_y - chrome.close_button.ActualHeight / 2) < 0.25
            print('Close visible-text center: {:.2f}, {:.2f}; button center: 30, 9.'.format(center_x, center_y))
            if output_directory:
                render_close_detail(chrome.close_button, os.path.join(output_directory, 'close-control-4x.png'))
            assert text.TranslatePoint(Point(0, 0), check).X - token('KlaGridSpace16').Value == room_text_gap
            print('Main template: search {} high at y={}; row {} high, padding {}; checkbox text gap {}; list {} x {}; text width {}; scrollbars {}.'.format(
                window.textbox_filter.ActualHeight, window.textbox_filter.TranslatePoint(Point(0, 0), shell).Y,
                row.ActualHeight, row.Padding, text.TranslatePoint(Point(0, 0), check).X - 16,
                window.main_ListBox.ActualWidth, window.main_ListBox.ActualHeight, text.ActualWidth,
                [(str(bar.Orientation), bar.ActualWidth) for bar in bars]))
        token = window.FindResource
        chrome_row, inset, pair_gap = token('KlaChromeRow').Value, token('KlaBodyInset'), token('KlaPairGap').Right
        assert chrome.header.ActualHeight == chrome.footer.ActualHeight == chrome_row
        assert chrome.title.Text == shell.Tag.Title
        assert chrome.title.ToolTip is None and window.ToolTip is None
        assert chrome.version.Text == tool_version
        assert str(chrome.version.Foreground) == str(token('KlaTextMutedBrush'))
        assert str(chrome.prototype.Foreground) == str(token('KlaAccentHoverBrush'))
        assert str(chrome.outreach.Foreground) == str(token('KlaAccentHoverBrush'))
        assert window.textbox_filter.ActualHeight == room_filter_height
        assert window.textbox_filter.FontSize == token('KlaTitleFontSize')
        assert window.textbox_filter.TranslatePoint(Point(0, 0), shell).Y == chrome_row + inset.Top
        assert window.text_label.FontSize == prompt_font_size
        window.button_main.ApplyTemplate()
        assert window.button_main.Template.FindName('ButtonBorder', window.button_main).BorderBrush.Color.A == 0
        assert str(window.FontFamily) == 'Segoe UI'
        assert window.FontSize == token('KlaBodyFontSize') and chrome.title.FontSize == token('KlaTitleFontSize')
        assert window.button_main.ActualWidth == token('KlaMainButtonWidth') and window.button_main.ActualHeight == token('KlaControlHeight')
        buttons = list(window.UI_Buttons_all_none.Children)
        assert all(button.ActualWidth == token('KlaButtonWidth') and button.ActualHeight == token('KlaCompactHeight') for button in buttons)
        body_origin = window.window_body.TranslatePoint(Point(0, 0), shell)
        assert body_origin.X == inset.Left and body_origin.Y == chrome_row + inset.Top
        first = buttons[0].TranslatePoint(Point(0, 0), shell)
        second = buttons[1].TranslatePoint(Point(0, 0), shell)
        main = window.button_main.TranslatePoint(Point(0, 0), shell)
        assert second.X - first.X - token('KlaButtonWidth') == pair_gap
        assert main.X == first.X and main.Y - first.Y - token('KlaCompactHeight') == token('KlaGridSpace8').Value
        assert chrome.footer.TranslatePoint(Point(0, 0), shell).Y - main.Y - token('KlaControlHeight') == inset.Bottom
        assert window.window_body.IsEnabled == (state != 'Disabled')
        assert chrome.close_button.IsEnabled
        if state == 'Long content':
            check = next(item for item in descendants(window.main_ListBox) if isinstance(item, CheckBox))
            text = next(item for item in descendants(check) if isinstance(item, TextBlock))
            bar = next(item for item in descendants(window.main_ListBox)
                       if isinstance(item, ScrollBar) and str(item.Orientation) == 'Vertical')
            gap = (bar.TranslatePoint(Point(0, 0), window.main_ListBox).X
                   - text.TranslatePoint(Point(0, 0), window.main_ListBox).X - text.ActualWidth)
            assert 0 <= gap <= 8, gap
            print('Long-content text-to-scrollbar layout clearance: {}.'.format(gap))
        if state == 'Disabled':
            labels = [element for element in descendants(window.main_ListBox)
                      if isinstance(element, TextBlock) and element.Text]
            assert labels and all(str(label.Foreground) == str(token('KlaDisabledTextBrush')) for label in labels)
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
        navigation = RequestNavigateEventArgs(chrome.prototype.NavigateUri, '')
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
