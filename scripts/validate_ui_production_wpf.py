# -*- coding: utf-8 -*-
"""Opt-in production-XAML checks inside the isolated Gallery WPF probe.

This constructs real WPF layouts with Gallery-owned fictional data/handlers.
No Window is shown; Revit ownership, model operations, live keyboard/pointer
input, monitor/DPI and assistive-technology acceptance are separate host checks.
"""
from __future__ import print_function

import math

from System import Uri
from System.Windows import Window, Size, Rect, Point, ResourceDictionary, ResizeMode, TextWrapping
from System.Windows.Automation import AutomationProperties
from System.Windows.Controls import (Button, ContentControl, Image, Label,
                                     ScrollViewer, StackPanel, TextBlock,
                                     TextBox, WrapPanel)
from System.Windows.Media import Brushes, DrawingImage, Geometry
from System.Windows.Media.Imaging import BitmapSource
from System.Windows.Shapes import Path


PRODUCTION_IDS = (
    'kla-select-from-dict', 'kla-create-from-rooms', 'kla-custom-alert',
    'kla-duplicate-sheets', 'kla-find-replace-views', 'kla-find-replace-sheets',
    'kla-match-properties-recall', 'kla-steel-psf', 'kla-view-range')
ICON_ROLES = ('Search', 'TextFilter', 'Regex', 'ClearSearch', 'ReadElement',
              'ReadViewFilters', 'FilterElement', 'PickElement',
              'RectangleSelection', 'CurrentSelection', 'ListView', 'GridView',
              'Favorite', 'Information', 'Warning', 'Error', 'Success')
FOOTER_ACTIONS = {
    'kla-select-from-dict': 'button_main',
    'kla-create-from-rooms': 'button_main',
    'kla-duplicate-sheets': 'primary_action',
    'kla-steel-psf': 'button_main',
}


def production_layout(window, width=None, height=None):
    width = float(window.Width if width is None else width)
    height = float(window.Height if height is None else height)
    assert not math.isnan(width) and not math.isnan(height), 'Preview must fit auto-sized windows before validation.'
    assert width > 0 and height > 0 and not math.isinf(width) and not math.isinf(height)
    shell = window.window_shell
    shell.Measure(Size(width, height))
    shell.Arrange(Rect(0, 0, width, height))
    settle_layout(shell)
    return width, height


def assert_scrolls(viewer, shell, context):
    assert viewer.ViewportHeight > 0, context + ': no viewport'
    assert viewer.ScrollableHeight > 0, context + ': content should overflow'
    viewer.ScrollToEnd()
    settle_layout(shell)
    assert viewer.VerticalOffset > 0, context + ': end is not reachable'


def assert_recall_captions(window, locale):
    recall = window.content_host.Content
    count = 0
    for button in descendants(recall):
        if not isinstance(button, Button) or not isinstance(button.Content, StackPanel):
            continue
        if button.Visibility.ToString() != 'Visible':
            continue
        border = button.Template.FindName('ButtonBorder', button)
        available = button.ActualWidth - border.Padding.Left - border.Padding.Right - border.BorderThickness.Left - border.BorderThickness.Right
        assert button.Content.DesiredSize.Width <= available + 0.1, (locale, button.Name, 'icon/text clipped', button.Content.DesiredSize.Width, available)
        position = button.TranslatePoint(Point(0, 0), window.window_body)
        assert position.X >= -0.1 and position.X + button.ActualWidth <= window.window_body.ActualWidth + 0.1, (locale, button.Name, 'button exceeds body')
        assert button.ActualWidth == window.FindResource('KlaIconTextButtonWidth') and button.ActualHeight == window.FindResource('KlaCompactHeight'), (locale, button.Name, 'icon/text role')
        count += 1
    assert count == 4, (locale, count)
    last = recall.pasteSelBtn.TranslatePoint(Point(0, recall.pasteSelBtn.ActualHeight), window.window_shell).Y
    footer = window._kla_chrome.footer.TranslatePoint(Point(0, 0), window.window_shell).Y
    assert abs(footer - last - 8) < 0.1, (locale, 'paste/footer gap', footer - last)


def validate_production_windows():
    count = 0
    for identity in PRODUCTION_IDS:
        entry = next(row for row in entries if row['id'] == identity)
        assert len(entry['states']) == 5, identity
        for state in entry['states']:
            window = create_custom(repo_root, dict(entry, tool_version=namespace['__version__']), state)
            try:
                width, height = production_layout(window)
                shell, chrome = window.window_shell, window._kla_chrome
                token = window.FindResource
                chrome_row, inset = token('KlaChromeRow').Value, token('KlaBodyInset')
                assert chrome.header.ActualHeight == chrome.footer.ActualHeight == chrome_row, (identity, state)
                origin = window.window_body.TranslatePoint(Point(0, 0), shell)
                assert abs(origin.X - inset.Left) < 0.1 and abs(origin.Y - (chrome_row + inset.Top)) < 0.1, (identity, state, origin)
                assert abs(window.window_body.ActualWidth - (width - inset.Left - inset.Right)) < 1, (identity, state)
                assert window.window_body.ActualHeight > 0, (identity, state)
                assert window.window_body.IsEnabled == (state != 'Disabled'), (identity, state)
                assert chrome.close_button.IsEnabled, (identity, state)
                assert chrome.title.ToolTip is None
                assert chrome.version.Text == namespace['__version__'], (identity, state)

                for control in descendants(window.window_body):
                    if isinstance(control, Image):
                        assert control.Source is not None and not isinstance(control.Source, BitmapSource), (identity, 'raster icon')
                    if isinstance(control, TextBox) and (control.Name.startswith(('input_', 'UI_view_', 'UI_sheet_'))
                            or control.Name in ('textbox_filter', 'UI_offset', 'search_tb',
                                                'topplane_input', 'cutplane_input', 'bottomplane_input', 'viewdepth_input')):
                        assert abs(control.ActualHeight - token('KlaCompactFieldHeight')) < 0.1, (identity, state, control.Name, control.ActualHeight)
                        assert control.ActualWidth > 20, (identity, state, control.Name)
                        if control.Name.startswith(('input_', 'UI_view_', 'UI_sheet_')):
                            assert abs(control.ActualWidth - token('KlaCompactFieldInputColumn').Value) < 0.1, (identity, state, control.Name, 'naming field width', control.ActualWidth)
                        assert AutomationProperties.GetName(control), (identity, control.Name, 'unnamed field')
                    if isinstance(control, Label) and control.Style == window.Resources['KlaFoundationPromptLabel']:
                        assert control.FontSize == token('KlaTitleFontSize'), (identity, state, 'prompt')

                if identity in FOOTER_ACTIONS:
                    action = getattr(window, FOOTER_ACTIONS[identity])
                    bottom = action.TranslatePoint(Point(0, action.ActualHeight), shell).Y
                    footer_top = chrome.footer.TranslatePoint(Point(0, 0), shell).Y
                    assert abs(footer_top - bottom - 8) < 1, (identity, state, 'action gap', footer_top - bottom)
                if identity in ('kla-find-replace-views', 'kla-find-replace-sheets') and state in ('Normal', 'Disabled'):
                    action = window.UI_main_button
                    bottom = action.TranslatePoint(Point(0, action.ActualHeight), shell).Y
                    footer_top = chrome.footer.TranslatePoint(Point(0, 0), shell).Y
                    assert abs(footer_top - bottom - 8) < 1, (identity, state, 'compact rename action gap', footer_top - bottom)
                if state == 'Empty' and hasattr(window, 'main_ListBox'):
                    assert window.main_ListBox.Items.Count == 0, identity
                if state == 'Long content' and hasattr(window, 'main_ListBox'):
                    viewers = [part for part in descendants(window.main_ListBox) if isinstance(part, ScrollViewer)]
                    assert any(part.ScrollableHeight > 0 for part in viewers), (identity, 'long checked list has no scroll range')
                if identity == 'kla-match-properties-recall':
                    recall = window.content_host.Content
                    assert str(recall.Background) == '#FF1A252B', 'Standalone Recall must not use the docked white surface.'
                    assert_recall_captions(window, 'en_us/' + state)
                    if state == 'Empty':
                        assert recall.paramListView.Items.Count == 0
                    if state == 'Long content':
                        viewers = [part for part in descendants(recall.paramListView) if isinstance(part, ScrollViewer)]
                        assert any(part.ScrollableHeight > 0 for part in viewers), 'Recall long list has no scroll range.'
                if identity == 'kla-view-range' and state == 'Long content':
                    assert window.view_message_scroll.ActualHeight <= 96
                    assert_scrolls(window.view_message_scroll, shell, 'View Range long instructions')
                if identity == 'kla-view-range':
                    for cell in descendants(window.grid_main):
                        if isinstance(cell, TextBlock) and cell.Style == window.Resources['ViewRangeTableCell']:
                            assert cell.TextWrapping == TextWrapping.NoWrap
                            assert cell.ActualHeight <= 32, (identity, state, 'table cell exceeds its row', cell.ActualHeight)
                    for prefix, expected in (('topplane', '#FF00FF00'), ('cutplane', '#FFFF0000'),
                                             ('bottomplane', '#FF0000FF'), ('viewdepth', '#FFFF7F00')):
                        assert str(getattr(window.DataContext, prefix + '_brush')) == expected, (identity, prefix, 'plane color')
                    for prefix in ('topplane', 'bottomplane', 'viewdepth'):
                        combo = getattr(window, prefix + '_level_combo')
                        expected_name = combo.SelectedItem.Name
                        shown = [part.Text for part in descendants(combo) if isinstance(part, TextBlock)]
                        assert expected_name in shown, (identity, state, prefix, 'selected level name not displayed', shown)
                if identity in ('kla-find-replace-views', 'kla-find-replace-sheets') and state == 'Long content':
                    assert window.result_details.VerticalScrollBarVisibility.ToString() == 'Auto'
                    assert window.result_details.ActualHeight > 0

                if output_directory:
                    filename = 'production-' + identity + '-' + state.lower().replace(' ', '-') + '.png'
                    render_content(window, os.path.join(output_directory, filename), width, height)

                if identity == 'kla-match-properties-recall' and state == 'Normal':
                    for locale in ('de_de', 'ko', 'en_us'):
                        strings = ResourceDictionary()
                        strings.Source = Uri(os.path.join(repo_root, 'lib', 'match', 'clipboard_ui.ResourceDictionary.' + locale + '.xaml'))
                        recall.Resources.MergedDictionaries.Add(strings)
                        production_layout(window)
                        assert_recall_captions(window, locale)
                        if output_directory and locale != 'en_us':
                            render_content(window, os.path.join(output_directory, 'production-recall-' + locale + '.png'), width, height)
                    print('Standalone Recall: English/German/Korean visible icon/text captions fit128x28; three-paste row stays within448-wide shell and8-unit footer gap.')

                if identity == 'kla-custom-alert' and state == 'Long content':
                    # Force a real overflow even if the ordinary long fixture fits at this font/DPI.
                    window.message_text.Text = '\n'.join('Stress message line {:03d}: this must remain reachable.'.format(i) for i in range(120))
                    width, height = production_layout(window, width, 400)
                    assert_scrolls(window.alert_scroll, shell, 'Alert bounded long message')
                    if output_directory:
                        render_content(window, os.path.join(output_directory, 'production-alert-stress-end.png'), width, height)
                if state == 'Normal' and window.ResizeMode != ResizeMode.NoResize and window.MinWidth > 0 and window.MinHeight > 0:
                    min_width, min_height = production_layout(window, window.MinWidth, window.MinHeight)
                    assert window.window_body.ActualHeight > 0
                    assert chrome.close_button.IsEnabled
                    if output_directory:
                        render_content(window, os.path.join(output_directory, 'production-' + identity + '-minimum.png'), min_width, min_height)
                count += 1
            finally:
                window.Close()
    print('Production Python: {} real-XAML state layouts; shared chrome, body/field geometry, caller version, vector icons, empty/long bounds and alert stress scrolling passed.'.format(count))


def validate_gui_icons():
    resources = ResourceDictionary()
    resources.Source = Uri(os.path.join(repo_root, 'lib', 'GUI', 'Resources', 'KLCodeComponents.xaml'))
    owner = Window()
    owner.Resources.MergedDictionaries.Add(resources)
    owner.Foreground = Brushes.Orange
    panel = WrapPanel()
    panel.ItemWidth, panel.ItemHeight = 140, 56
    panel.Background = resources['header_background']
    owner.Content = panel
    presenters = []
    try:
        for role in ICON_ROLES:
            geometry = resources['Kla' + role + 'Geometry']
            image = resources['KlaIcon' + role]
            assert isinstance(geometry, Geometry) and not geometry.Bounds.IsEmpty, role
            assert isinstance(image, DrawingImage), role
            assert image.Width == image.Height == 24, (role, image.Width, image.Height)
            block = StackPanel()
            icon = ContentControl()
            icon.Style = resources['KlaGuiIcon']
            icon.Content = geometry
            block.Children.Add(icon)
            label = TextBlock()
            label.Text, label.Width = role, 132
            label.TextWrapping = TextWrapping.Wrap
            label.Foreground = resources['text_white']
            block.Children.Add(label)
            panel.Children.Add(block)
            presenters.append(icon)
        panel.Measure(Size(700, 224))
        panel.Arrange(Rect(0, 0, 700, 224))
        settle_layout(panel)
        for icon in presenters:
            assert icon.ActualWidth == icon.ActualHeight == 16
            path = next(part for part in descendants(icon) if isinstance(part, Path))
            assert str(path.Stroke) == str(owner.Foreground)
            assert path.StrokeThickness == 1.5
            icon.IsEnabled = False
            settle_layout(panel)
            assert str(path.Stroke) == str(resources['KlaDisabledTextBrush'])
            icon.IsEnabled = True
        owner.Foreground = resources['text_white']
        settle_layout(panel)
        if output_directory:
            render_content(owner, os.path.join(output_directory, 'gui-icons-17-native.png'), 700, 224)
        print('GUI icons: all17 geometry/DrawingImage resources load at24-unit bounds;16-unit presenters inherit foreground and show disabled stroke at1.5 thickness.')
    finally:
        owner.Close()


validate_production_windows()
validate_gui_icons()
