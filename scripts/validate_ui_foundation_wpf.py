# -*- coding: utf-8 -*-
"""Reference-shell checks, run inside validate_ui_gallery_wpf.py's real WPF host."""
from __future__ import print_function

from System import Uri
from System.Windows import Point, RoutedEventArgs, Size, Rect, FlowDirection
from System.Windows.Controls.Primitives import ButtonBase
from System.Windows.Controls import TextBlock, CheckBox
from System.Windows.Controls.Primitives import ScrollBar
from System.Windows.Media import (Color, VisualTreeHelper, FormattedText, Typeface,
                                  DrawingVisual, VisualBrush, PixelFormats)
from System.Windows.Media.Imaging import RenderTargetBitmap, PngBitmapEncoder, BitmapFrame
from System.IO import FileStream, FileMode
from System.Globalization import CultureInfo
from System.Windows.Documents import Hyperlink
from System.Windows.Navigation import RequestNavigateEventArgs
from GUI.dialogs import SelectionItem, create_selection

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
    """Exercise the actual shared selector rather than a duplicate template."""
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
        room_filter_height, rooms.textbox_filter.TranslatePoint(Point(0, 0), rooms.Content).Y,
        room_row_height, room_row.Padding, room_text_gap))
    if output_directory:
        render(rooms, os.path.join(output_directory, 'create-from-rooms-reference.png'), 400, 406)
    rooms.Close()

    selection_entry = next(entry for entry in entries if entry['id'] == 'kla-select-from-dict')
    reference = create_custom(root, selection_entry, 'Normal')
    reference.Content.Measure(Size(432, 576))
    reference.Content.Arrange(Rect(0, 0, 432, 576))
    reference.Content.UpdateLayout()
    native_row_template = reference.main_ListBox.ItemContainerGenerator.ContainerFromIndex(0).Template
    prompt_font_size = reference.text_label.FontSize
    assert prompt_font_size == 14
    if output_directory:
        render(reference, os.path.join(output_directory, 'list-selection-reference.png'), 432, 576)
    reference.Close()

    states = ('Normal', 'Empty', 'Error', 'Disabled', 'Long content')
    for state in states:
        labels = ['Sample view {}'.format(index + 1) for index in range(4)]
        if state == 'Long content':
            labels = ['A deliberately long selectable label ' * 12] + labels * 12
        source_rows = [] if state == 'Empty' else [
            SelectionItem('sample-{}'.format(index), label, 'payload-{}'.format(index))
            for index, label in enumerate(labels)]
        navigated = []
        title = 'Shared selector foundation' + (' - Long project context ' * 12 if state == 'Long content' else '')
        window = create_selection(title, source_rows, prompt='Select Elements:',
                                  version=tool_version, navigate=lambda uri: navigated.append(uri))
        if state == 'Error':
            window.accept_selection()
        window.window_body.IsEnabled = state != 'Disabled'
        shell = window.window_shell
        shell.Measure(Size(432, 576))
        shell.Arrange(Rect(0, 0, 432, 576))
        shell.UpdateLayout()
        settle_layout(shell)
        chrome = window._kla_chrome
        token = window.FindResource
        if state == 'Normal':
            row = window.items_list.ItemContainerGenerator.ContainerFromIndex(0)
            check = next(item for item in descendants(row) if isinstance(item, CheckBox))
            text = next(item for item in descendants(check) if isinstance(item, TextBlock) and item.Text)
            bars = [item for item in descendants(window.items_list) if isinstance(item, ScrollBar)]
            description = next(item for item in descendants(check) if isinstance(item, TextBlock) and not item.Text)
            # The real shared row has a label plus a description TextBlock;
            # preserve its actual composition instead of substituting a
            # single-label template just to match the production reference.
            assert row.ActualHeight == room_row_height + description.ActualHeight, (row.ActualHeight, room_row_height, description.ActualHeight)
            assert row.Template == native_row_template
            assert window.prompt_label.Content == 'Select Elements:'
            label = next(part for part in descendants(chrome.close_button) if isinstance(part, TextBlock))
            glyphs = FormattedText(label.Text, CultureInfo.InvariantCulture, FlowDirection.LeftToRight,
                                   Typeface(label.FontFamily, label.FontStyle, label.FontWeight, label.FontStretch),
                                   label.FontSize, label.Foreground).BuildGeometry(Point(0, 0)).Bounds
            origin = label.TranslatePoint(Point(0, 0), chrome.close_button)
            center_x = origin.X + glyphs.X + glyphs.Width / 2
            center_y = origin.Y + glyphs.Y + glyphs.Height / 2
            assert abs(center_x - chrome.close_button.ActualWidth / 2) < 0.25, 'Close horizontal center: {}'.format(center_x)
            assert abs(center_y - chrome.close_button.ActualHeight / 2) < 0.25, 'Close vertical center: {}'.format(center_y)
            print('Close visible-text center: {:.2f}, {:.2f}; button center: 30, 9.'.format(center_x, center_y))
            if output_directory:
                render_close_detail(chrome.close_button, os.path.join(output_directory, 'close-control-4x.png'))
            assert text.TranslatePoint(Point(0, 0), check).X - token('KlaGridSpace16').Value == room_text_gap
            print('Shared selector: search {} high at y={}; row {} high, padding {}; checkbox text gap {}; list {} x {}; text width {}; scrollbars {}.'.format(
                window.filter_text.ActualHeight, window.filter_text.TranslatePoint(Point(0, 0), shell).Y,
                row.ActualHeight, row.Padding, text.TranslatePoint(Point(0, 0), check).X - 16,
                window.items_list.ActualWidth, window.items_list.ActualHeight, text.ActualWidth,
                [(str(bar.Orientation), bar.ActualWidth) for bar in bars]))
        chrome_row, inset, pair_gap = token('KlaChromeRow').Value, token('KlaBodyInset'), token('KlaPairGap').Right
        assert chrome.header.ActualHeight == chrome.footer.ActualHeight == chrome_row
        assert chrome.title.Text == shell.Tag.Title
        assert chrome.title.ToolTip is None and window.ToolTip is None
        assert chrome.version.Text == tool_version
        assert chrome.version.Foreground.Color == Color.FromRgb(128, 128, 128)
        assert chrome.prototype.Foreground.Color == Color.FromRgb(64, 112, 88)
        assert chrome.outreach.Foreground.Color == Color.FromRgb(64, 112, 88)
        assert window.filter_text.ActualHeight == room_filter_height
        assert window.filter_text.FontSize == token('KlaTitleFontSize')
        assert window.filter_text.TranslatePoint(Point(0, 0), shell).Y == chrome_row + inset.Top
        assert window.prompt_label.FontSize == prompt_font_size
        window.accept_button.ApplyTemplate()
        assert window.accept_button.Template.FindName('ButtonBorder', window.accept_button).BorderBrush.Color.A == 0
        assert not window.accept_button.IsDefault
        assert str(window.FontFamily) == 'Segoe UI'
        assert window.FontSize == token('KlaBodyFontSize') and chrome.title.FontSize == token('KlaTitleFontSize')
        assert window.accept_button.ActualWidth == token('KlaMainButtonWidth') and window.accept_button.ActualHeight == token('KlaControlHeight')
        buttons = list(window.batch_actions.Children)
        assert all(button.ActualWidth == token('KlaButtonWidth') and button.ActualHeight == token('KlaCompactHeight') for button in buttons)
        assert all(button.Background == token('KlaComponentSurfaceBrush') for button in buttons)
        body_origin = window.window_body.TranslatePoint(Point(0, 0), shell)
        assert body_origin.X == inset.Left and body_origin.Y == chrome_row + inset.Top
        first = buttons[0].TranslatePoint(Point(0, 0), shell)
        second = buttons[1].TranslatePoint(Point(0, 0), shell)
        main = window.accept_button.TranslatePoint(Point(0, 0), shell)
        assert second.X - first.X - token('KlaButtonWidth') == pair_gap
        assert main.X == first.X and main.Y - first.Y - token('KlaCompactHeight') == token('KlaGridSpace8').Value
        assert chrome.footer.TranslatePoint(Point(0, 0), shell).Y - main.Y - token('KlaControlHeight') == inset.Bottom
        assert window.window_body.IsEnabled == (state != 'Disabled') and chrome.close_button.IsEnabled
        if state == 'Long content':
            check = next(item for item in descendants(window.items_list) if isinstance(item, CheckBox))
            text = next(item for item in descendants(check) if isinstance(item, TextBlock) and item.Text)
            bar = next(item for item in descendants(window.items_list)
                       if isinstance(item, ScrollBar) and str(item.Orientation) == 'Vertical')
            gap = (bar.TranslatePoint(Point(0, 0), window.items_list).X
                   - text.TranslatePoint(Point(0, 0), window.items_list).X - text.ActualWidth)
            assert 0 <= gap <= 8, gap
            assert bar.Maximum > bar.Minimum, 'Long fixture must actually overflow'
            print('Long-content text-to-scrollbar layout clearance: {}.'.format(gap))
        if state == 'Disabled':
            labels = [element for element in descendants(window.items_list)
                      if isinstance(element, TextBlock) and element.Text]
            assert labels and all(str(label.Foreground) == str(token('KlaDisabledTextBrush')) for label in labels)
        if output_directory:
            render(window, os.path.join(output_directory, 'shared-selector-foundation-' + state.lower().replace(' ', '-') + '.png'), 432, 576)

        navigation = RequestNavigateEventArgs(chrome.prototype.NavigateUri, '')
        navigation.RoutedEvent = Hyperlink.RequestNavigateEvent
        chrome.prototype.RaiseEvent(navigation)
        assert navigation.Handled and navigated == [chrome.prototype.NavigateUri.AbsoluteUri]
        closed = []
        window.Closed += lambda sender, args: closed.append(True)
        if state != 'Disabled':
            if state == 'Error':
                window.accept_button.RaiseEvent(RoutedEventArgs(ButtonBase.ClickEvent))
                assert window.result.is_cancelled and window.validation_text.Text
            window.filter_text.Text = 'no_matching_sample_591'
            assert window.items_list.Items.Count == 0
            window.filter_text.Text = ''
            window.check_none(None, None)
            assert not any(item.IsChecked for item in window.state.items)
            window.check_all(None, None)
            assert all(item.IsChecked for item in window.state.items)
            assert not any(item.IsChecked for item in source_rows), 'Caller check state stays unchanged'
            window.accept_button.RaiseEvent(RoutedEventArgs(ButtonBase.ClickEvent))
            if source_rows:
                assert window.result.action == 'accept'
                assert window.result.value == [row.Value for row in source_rows]
                assert closed
            else:
                assert window.result.is_cancelled and window.validation_text.Text
        if not closed:
            chrome.close_button.RaiseEvent(RoutedEventArgs(ButtonBase.ClickEvent))
            assert closed and window.result.is_cancelled

    # Unknown caller version must not leave placeholder footer text.
    window = create_selection('Unknown caller version', [SelectionItem('one', 'One', 1)])
    window.window_shell.Measure(Size(432, 576))
    window.window_shell.Arrange(Rect(0, 0, 432, 576))
    assert window._kla_chrome.version.Text == ''
    window.Close()
    print('Foundation: five shared-selector states, real shell/Close/native-row geometry, caller identity, checked results/navigation and cancellation passed.')


validate_foundation(repo_root, entries, namespace['__version__'], output_directory, render_content)
