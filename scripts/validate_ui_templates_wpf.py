# -*- coding: utf-8 -*-
"""Real WPF template-family layout/actions; invoked inside the Gallery probe."""
from __future__ import print_function

from ui_gallery.template_data import TEMPLATE_FILES
from System.Windows import Thickness
from System.Windows.Controls import CheckBox, Label


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
            assert window._kla_chrome.header.ActualHeight == window._kla_chrome.footer.ActualHeight == 24
            assert window._kla_chrome.title.ToolTip is None
            assert window.window_body.IsEnabled == (state != 'Disabled')
            if identity == 'template-form':
                fields = [getattr(window, 'input_' + name) for name in ('find', 'replace', 'prefix', 'suffix')]
                assert not hasattr(window, 'preview_lines')
                assert window.naming_group.Padding == Thickness(12)
                for field in fields:
                    assert field.ActualWidth == 240 and field.ActualHeight == 24, (state, field.Name, field.ActualWidth, field.ActualHeight)
                    label = next(control for control in window.naming_group.Child.Children
                                 if isinstance(control, Label) and control.Target == field)
                    assert label.ActualWidth == 60 and str(label.VerticalContentAlignment) == 'Center'
                    assert label.Content.endswith(':')
                for previous, following in zip(fields, fields[1:]):
                    gap = following.TranslatePoint(Point(0, 0), shell).Y - previous.TranslatePoint(Point(0, previous.ActualHeight), shell).Y
                    assert gap == 8, gap
            if identity == 'template-options' and state == 'Disabled':
                for widget in (window.option_category, window.scope_selected, window.option_toggle):
                    labels = [item for item in descendants(widget) if isinstance(item, TextBlock) and item.Text]
                    assert labels and all(str(label.Foreground) == '#FFA6B0AD' for label in labels), (widget.Name, [(label.Text, str(label.Foreground)) for label in labels])
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
                elif identity == 'template-message':
                    window.message_severity.SelectedItem = 'Warning'
                    assert 'Warning' in window.message_heading.Text
                    window.message_expander.IsExpanded = True
                elif identity == 'template-options':
                    window.option_offset.Text = 'invalid'
                    window.apply_options(None, None)
                    assert 'offset' in window.options_feedback.Text.lower()
                    window.option_offset.Text = '-12.5'
                    window.scope_all.IsChecked = True
                    window.apply_options(None, None)
                    assert 'All Available Items' in window.options_feedback.Text
                    window.browse_sample(None, None)
                    assert 'Alternate Example' in window.option_path.Text
                elif identity == 'template-review':
                    row = window.review_grid.ItemContainerGenerator.ContainerFromIndex(0)
                    check = next(control for control in descendants(row) if isinstance(control, CheckBox))
                    check.IsChecked = False
                    assert not window._review_rows[0].IsChecked
                    assert '0 checked' in window.review_summary.Text
                    window.review_search.Text = 'no_sample_match_593'
                    assert window.review_grid.Items.Count == 0
                    window.review_search.Text = ''
                    window.review_check_all(None, None)
                    assert not any(row.IsChecked and not row.CanUse for row in window._review_rows)
                    window.apply_review(None, None)
                    assert 'No import' in window.preview_result
                if identity != 'template-selection':
                    shell.Measure(Size(window.MinWidth, window.MinHeight))
                    shell.Arrange(Rect(0, 0, window.MinWidth, window.MinHeight))
                    shell.UpdateLayout()
                    if output_directory:
                        render_content(window, os.path.join(output_directory, identity + '-minimum.png'), window.MinWidth, window.MinHeight)
            window.Close()
            count += 1
    print('Template family: {} state layouts, normal-state interactions, and minimum-size renders passed.'.format(count))


validate_template_family()
