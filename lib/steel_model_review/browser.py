# -*- coding: utf-8 -*-
"""Modal findings browser; host navigation runs after the window closes."""

from pyrevit import forms

from steel_model_review.engine import CHECKS


class ReviewRow(object):
    """Expose plain result fields as readable WPF binding properties."""

    def __init__(self, row):
        self.row = row
        self.Severity = row['severity']
        self.Check = row['check']
        self.Member = row['member']
        self.End = str(row['end'])
        self.Level = row['level']
        self.Offset = ('{0:+.8f}'.format(row['value'])
                       if row['value'] is not None else '')
        self.Related = ', '.join(str(r['id']) for r in row['related'])
        self.Status = row['status']
        self.Reason = row['reason']


class ReviewWindow(forms.WPFWindow):
    """Display filtered findings and return an action to the command adapter.

    Args:
        xaml: Absolute path to the bundle's review.xaml.
        snapshot: Complete or explicitly cancelled review snapshot.
        stale: Whether relevant model or settings evidence has changed.
    """

    def __init__(self, xaml, snapshot, stale=False):
        forms.WPFWindow.__init__(self, xaml)
        self.action = None
        self.snapshot = snapshot
        self._ready = False
        rows = snapshot['rows']
        counts = dict((s, sum(1 for r in rows if r['severity'] == s))
                      for s in ('Critical', 'Warning', 'Not evaluated', 'Pass'))
        accepted = sum(1 for r in rows if r['status'] == 'Accepted exception')
        self.summary.Text = (
            '{0} | {1} | {2}\nCritical {3}  |  Warning {4}  |  '
            'Not evaluated {5}  |  Pass {6}  |  Accepted exceptions {7}'
            .format(snapshot['model'], snapshot['time'], snapshot['state'],
                    counts['Critical'], counts['Warning'], counts['Not evaluated'],
                    counts['Pass'], accepted))
        self.coverage_text.Text = snapshot['summary']
        self.stale_text.Text = (
            'STALE: model or settings changed. Rerun before accepting findings.'
            if stale else 'Read-only geometry review; no SDS2-ready certification.')
        self.accept_button.IsEnabled = not stale and snapshot['state'] == 'Complete'
        self.severity_filter.ItemsSource = ['Issues', 'All', 'Critical', 'Warning',
                                            'Not evaluated', 'Pass']
        self.check_filter.ItemsSource = ['All'] + list(CHECKS)
        self.level_filter.ItemsSource = ['All'] + sorted(set(r['level'] for r in rows))
        self.status_filter.ItemsSource = ['All', 'Open', 'Accepted exception']
        for control in (self.severity_filter, self.check_filter,
                        self.level_filter, self.status_filter):
            control.SelectedIndex = 0
            control.SelectionChanged += self._filter
        self.search_box.TextChanged += self._filter
        self.findings.SelectionChanged += self._detail
        for button, action in ((self.coverage_button, 'coverage'),
                               (self.grids_button, 'grids'),
                               (self.select_button, 'select'),
                               (self.accept_button, 'accept'),
                               (self.reopen_button, 'reopen'),
                               (self.rerun_button, 'rerun'),
                               (self.close_button, 'close')):
            button.Tag = action
            button.Click += self._action
        self._ready = True
        self._filter(None, None)

    def _filter(self, sender, event):
        """Refresh sorted rows when a reviewer changes any filter control."""
        if not self._ready:
            return
        severity = str(self.severity_filter.SelectedItem)
        check = str(self.check_filter.SelectedItem)
        level = str(self.level_filter.SelectedItem)
        status = str(self.status_filter.SelectedItem)
        search = self.search_box.Text.lower()
        output = []
        order = {'Critical': 0, 'Warning': 1, 'Not evaluated': 2, 'Pass': 3}
        for row in self.snapshot['rows']:
            if severity == 'Issues' and row['severity'] == 'Pass':
                continue
            if severity not in ('Issues', 'All') and row['severity'] != severity:
                continue
            if check != 'All' and row['check'] != check:
                continue
            if level != 'All' and row['level'] != level:
                continue
            if status != 'All' and row['status'] != status:
                continue
            related = ' '.join(str(r['id']) for r in row['related'])
            if search not in ('{0} {1} {2}'.format(row['member'], row['reason'],
                                                 related)).lower():
                continue
            output.append(ReviewRow(row))
        output.sort(key=lambda r: (order[r.Severity], r.Check, r.Member, r.End))
        self.findings.ItemsSource = output

    def _detail(self, sender, event):
        """Show the selected finding's complete reason and exception text."""
        selected = self.findings.SelectedItem
        if selected:
            row = selected.row
            self.detail.Text = ('{0} | {1} | End {2}\n{3}\nRelated: {4}\n'
                                'Measured offset: {5} in\nException: {6}'
                                .format(selected.Check, selected.Member,
                                        selected.End, selected.Reason,
                                        selected.Related, selected.Offset,
                                        row['exception']))

    def _action(self, sender, event):
        """Close the modal window and return the requested workflow action."""
        action = str(sender.Tag)
        selected = self.findings.SelectedItem
        if action in ('select', 'accept', 'reopen', 'grids') and not selected:
            forms.alert('Select a finding first.', title='Model Checker')
            return
        self.action = (action, selected.row if selected else None)
        self.Close()
