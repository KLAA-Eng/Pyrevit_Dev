"""Host-independent fictional states and validation for reference windows."""
from __future__ import unicode_literals

from .scenarios import parse_offset, selection_items, validate_state

TEMPLATE_FILES = {
    'template-options': 'KLC-OptionsTemp.xaml',
    'template-review': 'KLC-ReviewTemp.xaml',
}


def option_data(state):
    validate_state(state)
    return dict(category='' if state == 'Empty' else 'Structural',
                offset={'Empty': '', 'Error': 'not a number', 'Long content': '123456789.5'}.get(state, '150'),
                path='' if state == 'Empty' else 'C:\\Sample Library\\' +
                ('Coordination\\' * 12 if state == 'Long content' else '') + 'Example.rfa')


def validate_options(category, offset):
    if not category:
        return 'Choose a sample category.'
    try:
        parse_offset(offset)
    except ValueError as error:
        return str(error)
    return ''


class ReviewRow(object):
    def __init__(self, name, status, detail, checked=False):
        self.Name = name
        self.Status = status
        self.Detail = detail
        self.IsChecked = checked
        self.CanUse = status != 'Blocked'


def review_rows(state):
    validate_state(state)
    rows = [ReviewRow(item.Name, ('Ready', 'Warning', 'Blocked')[index % 3],
                      'Fictional item. ' + ('Review the naming and destination. ' * 12 if state == 'Long content'
                                           else 'No production operation will run.'), index == 0)
            for index, item in enumerate(selection_items(state))]
    if state == 'Error' and rows:
        rows[0].Status = 'Blocked'
        rows[0].CanUse = False
    return rows


def review_outcome(rows):
    chosen = [row for row in rows if row.IsChecked]
    if not chosen:
        return 'Select at least one sample item.'
    if any(row.Status == 'Blocked' for row in chosen):
        return 'Cannot apply: a checked sample item is blocked. Clear the filter and use Check All to select eligible items only.'
    return '{} checked sample item(s); {} warning(s). No import or model change was performed.'.format(
        len(chosen), sum(row.Status == 'Warning' for row in chosen))
