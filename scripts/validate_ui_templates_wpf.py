# -*- coding: utf-8 -*-
"""Real WPF template-family layout/actions; invoked inside the Gallery probe."""
from __future__ import print_function

from ui_gallery.template_data import TEMPLATE_FILES
from System.Windows import Thickness
from System.Windows.Controls import CheckBox, Label, Border, DataGridCell


def validate_review_cells(window):
    for index in range(min(4, window.review_grid.Items.Count)):
        item = window.review_grid.Items[index]
        row = window.review_grid.ItemContainerGenerator.ContainerFromIndex(index)
        content = window.review_grid.Columns[2].GetCellContent(row)
        chip = next(control for control in descendants(content)
                    if isinstance(control, Border) and isinstance(control.Child, TextBlock)
                    and control.Child.Text == item.Status)
        cell = VisualTreeHelper.GetParent(chip)
        while not isinstance(cell, DataGridCell):
            cell = VisualTreeHelper.GetParent(cell)
        center = chip.TranslatePoint(Point(chip.ActualWidth / 2, chip.ActualHeight / 2), cell)
        assert abs(center.X - cell.ActualWidth / 2) < 1, (item.Status, center.X, cell.ActualWidth)
        assert abs(center.Y - cell.ActualHeight / 2) < 1, (item.Status, center.Y, cell.ActualHeight)
        check_content = window.review_grid.Columns[0].GetCellContent(row)
        check = next(control for control in descendants(check_content) if isinstance(control, CheckBox))
        assert check.IsEnabled == (window.preview_state != 'Disabled' and item.CanUse)


def validate_template_family():
    count = 0
    for identity in sorted(TEMPLATE_FILES):
        entry = next(row for row in entries if row['id'] == identity)
        for state in entry['states']:
            window = create_custom(repo_root, dict(entry, tool_version=namespace['__version__']), state)
            width, height = window.Width, window.Height
            shell = window.window_shell
            shell.Measure(Size(width, height))
            shell.Arrange(Rect(0, 0, width, height))
            shell.UpdateLayout()
            settle_layout(shell)
            token = window.FindResource
            assert window._kla_chrome.header.ActualHeight == window._kla_chrome.footer.ActualHeight == token('KlaChromeRow').Value
            assert window._kla_chrome.title.ToolTip is None
            assert window.window_body.IsEnabled == (state != 'Disabled')
            if identity == 'template-form':
                assert window.form_prompt.Style == window.Resources['KlaFoundationPromptLabel']
                assert window.form_prompt.FontSize == token('KlaTitleFontSize') and str(window.form_prompt.FontWeight) == 'Normal'
                fields = [getattr(window, 'input_' + name) for name in ('find', 'replace', 'prefix', 'suffix')]
                assert not hasattr(window, 'preview_lines')
                assert window.naming_group.Padding == token('KlaSectionPadding')
                for field in fields:
                    assert field.ActualWidth == token('KlaCompactFieldInputColumn').Value and field.ActualHeight == token('KlaCompactFieldHeight'), (state, field.Name, field.ActualWidth, field.ActualHeight)
                    label = next(control for control in descendants(window.naming_group)
                                 if isinstance(control, Label) and control.Target == field)
                    assert label.ActualWidth == token('KlaCompactFieldLabelColumn').Value and str(label.VerticalContentAlignment) == 'Center'
                    assert label.Content.endswith(':')
                for previous, following in zip(fields, fields[1:]):
                    gap = following.TranslatePoint(Point(0, 0), shell).Y - previous.TranslatePoint(Point(0, previous.ActualHeight), shell).Y
                    assert gap == token('KlaGridSpace8').Value, gap
            if identity == 'template-options':
                assert window.options_fields.ColumnDefinitions[0].ActualWidth == token('KlaCompactFieldLabelColumn').Value
                assert isinstance(window.option_include_existing, CheckBox)
                assert window.option_include_existing.Content == 'Include Existing'
                assert not hasattr(window, 'option_toggle')
                for field in (window.option_category, window.option_offset, window.option_path):
                    assert field.ActualHeight == token('KlaCompactFieldHeight'), (state, field.Name, field.ActualHeight)
                for prompt in (window.options_prompt, window.output_prompt):
                    assert prompt.Style == window.Resources['KlaFoundationPromptLabel']
                    assert prompt.FontSize == token('KlaTitleFontSize') and str(prompt.FontWeight) == 'Normal'
            if identity == 'template-options' and state == 'Disabled':
                for widget in (window.option_category, window.scope_selected, window.option_include_existing):
                    labels = [item for item in descendants(widget) if isinstance(item, TextBlock) and item.Text]
                    assert labels and all(str(label.Foreground) == '#FFA6B0AD' for label in labels), (widget.Name, [(label.Text, str(label.Foreground)) for label in labels])
            if identity == 'template-review':
                validate_review_cells(window)
            if hasattr(window, 'primary_action'):
                button = window.primary_action
                bottom = button.TranslatePoint(Point(0, button.ActualHeight), shell).Y
                footer = window._kla_chrome.footer.TranslatePoint(Point(0, 0), shell).Y
                assert abs(footer - bottom - 8) < 1, (identity, state, footer - bottom)
            if output_directory:
                render_content(window, os.path.join(output_directory, identity + '-' + state.lower().replace(' ', '-') + '.png'), width, height)
            if state == 'Normal':
                if identity == 'template-form':
                    window.input_find.Text = ''
                    window.input_replace.Text = 'Invalid'
                    window.apply_form(None, None)
                    assert 'Find' in window.form_feedback.Text
                    window.reset_form(None, None)
                    window.input_prefix.Text = 'QA-'
                    window.apply_form(None, None)
                    assert window.input_prefix.Text == 'QA-'
                    assert window.form_feedback.Text == 'Rules accepted for 4 sample names. No elements were renamed.'
                elif identity == 'template-options':
                    window.option_offset.Text = 'invalid'
                    window.apply_options(None, None)
                    assert 'offset' in window.options_feedback.Text.lower()
                    window.option_offset.Text = '-12.5'
                    window.scope_all.IsChecked = True
                    window.option_include_existing.IsChecked = False
                    window.apply_options(None, None)
                    assert 'All Available Items' in window.options_feedback.Text
                    assert 'include existing False' in window.options_feedback.Text
                    window.option_include_existing.IsChecked = True
                    window.apply_options(None, None)
                    assert 'include existing True' in window.options_feedback.Text
                    window.browse_sample(None, None)
                    assert 'Alternate Example' in window.option_path.Text
                elif identity == 'template-review':
                    row = window.review_grid.ItemContainerGenerator.ContainerFromIndex(0)
                    check = next(control for control in descendants(row) if isinstance(control, CheckBox))
                    check.IsChecked = False
                    assert not window._review_rows[0].IsChecked
                    assert '0 checked' in window.review_summary.Text
                    window.review_grid.SelectedItem = window._review_rows[3]
                    assert window._review_rows[3].Name in window.review_detail.Text
                    assert not window._review_rows[3].IsChecked
                    window.review_search.Text = window._review_rows[0].Name
                    window.review_check_all(None, None)
                    assert [row.IsChecked for row in window._review_rows] == [True, False, False, False]
                    window.review_search.Text = 'no_sample_match_593'
                    assert window.review_grid.Items.Count == 0
                    window.review_check_all(None, None)
                    assert [row.IsChecked for row in window._review_rows] == [True, False, False, False]
                    if output_directory:
                        window.review_search.Text = window._review_rows[0].Name
                        render_content(window, os.path.join(output_directory, 'template-review-filtered.png'), width, height)
                        assert window.review_grid.ItemContainerGenerator.ContainerFromIndex(0) is not None
                    window.review_search.Text = ''
                    window.review_check_all(None, None)
                    assert not any(row.IsChecked and not row.CanUse for row in window._review_rows)
                    window.apply_review(None, None)
                    assert 'No import' in window.preview_result
                shell.Measure(Size(window.MinWidth, window.MinHeight))
                shell.Arrange(Rect(0, 0, window.MinWidth, window.MinHeight))
                shell.UpdateLayout()
                if output_directory:
                    render_content(window, os.path.join(output_directory, identity + '-minimum.png'), window.MinWidth, window.MinHeight)
            window.Close()
            count += 1
    print('Template family: {} state layouts, normal-state interactions, and minimum-size renders passed.'.format(count))


validate_template_family()
