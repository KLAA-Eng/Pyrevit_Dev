"""Actual text origins and shared dialog action spacing; isolated WPF probe."""
from GUI.dialogs import (SelectionItem, RenameField, create_selection, create_rename,
                         create_message, create_text_prompt)
from System.Windows import Size, Rect, Point
from System.Windows.Controls import TextBlock


def input_layout(window):
    for unused in range(3):
        window.Content.Measure(Size(window.Width, window.Height))
        window.Content.Arrange(Rect(0, 0, window.Width, window.Height))
        settle_layout(window.Content)


def text_origin(control, parent):
    return control.TranslatePoint(Point(control.GetRectFromCharacterIndex(0).X, 0), parent).X


def validate_input_alignment():
    windows = []
    try:
        selection = create_selection('Input alignment', [SelectionItem('a', 'Alpha', groups=('Group A',))])
        windows.append(selection)
        selection.filter_text.Text = 'Alpha'
        input_layout(selection)
        group_text = next(node for node in visual_children(selection.group_filter)
                          if isinstance(node, TextBlock) and node.Text == 'All Items')
        search_x = text_origin(selection.filter_text, selection.window_body)
        group_x = group_text.TranslatePoint(Point(0, 0), selection.window_body).X
        print('Selection text origins: search {}, group {}; input inset {}.'.format(
            search_x, group_x, text_origin(selection.filter_text, selection.filter_text)))
        assert abs(search_x - group_x) < 0.1, 'Search text must align with Group text'
        assert abs(text_origin(selection.filter_text, selection.filter_text) - 8) < 0.1
        if output_directory:
            render_content(selection, os.path.join(output_directory, 'selection-search-alignment.png'), selection.Width, selection.Height)
        rename = create_rename('Input alignment', [RenameField('name', 'Name', find='Alpha')])
        windows.append(rename)
        input_layout(rename)
        field = rename.field_controls[0].find_text
        assert abs(text_origin(field, field) - 8) < 0.1, 'Rename must share the corrected input inset'
        message = create_message('Action spacing', 'Message body.')
        prompt = create_text_prompt('Action spacing', 'Enter text.', default='Alpha')
        windows.extend([message, prompt])
        for window in (message, prompt):
            input_layout(window)
        assert prompt.accept_button.Style == message.action_one.Style
        assert (prompt.accept_button.ActualWidth, prompt.accept_button.ActualHeight) == (104, 28)
        assert (message.action_one.ActualWidth, message.action_one.ActualHeight) == (104, 28)
        message_bottom = message.message_banner.TranslatePoint(Point(0, message.message_banner.ActualHeight), message.window_body).Y
        prompt_bottom = prompt.input_text.TranslatePoint(Point(0, prompt.input_text.ActualHeight), prompt.window_body).Y
        assert abs(message.action_one.TranslatePoint(Point(0, 0), message.window_body).Y - message_bottom - 8) < 0.1
        assert abs(prompt.accept_button.TranslatePoint(Point(0, 0), prompt.window_body).Y - prompt_bottom - 8) < 0.1
        details = create_message('Action spacing', 'Message body.', details='Diagnostic details.')
        windows.append(details)
        details.message_expander.IsExpanded = True
        input_layout(details)
        details_bottom = details.message_expander.TranslatePoint(Point(0, details.message_expander.ActualHeight), details.window_body).Y
        assert abs(details.action_one.TranslatePoint(Point(0, 0), details.window_body).Y - details_bottom - 8) < 0.1
        print('Input alignment: 8-unit Search/Group/Rename text origins; shared 104x28 OK and 8-unit action gaps passed.')
    finally:
        for window in windows:
            window.Close()


validate_input_alignment()
