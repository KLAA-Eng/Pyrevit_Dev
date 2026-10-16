# -*- coding: utf-8 -*-
"""Modal findings browser; host navigation runs after the window closes."""

from pyrevit import forms

from steel_model_review.engine import CHECKS
from steel_model_review.reporting import CHECK_LABELS, evidence_text, filtered_rows


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
        self.relationships = dict((r['relationship_id'], r)
                                  for r in snapshot.get('relationships', []))
        self.members = dict((m['uid'], m) for m in snapshot.get('members', []))
        rows = snapshot['rows']
        counts = dict((s, sum(1 for r in rows if r['severity'] == s))
                      for s in ('Critical', 'Warning', 'Not evaluated', 'Pass', 'Error', 'Information'))
        accepted = sum(1 for r in rows if r['status'] == 'Accepted exception')
        self.summary.Text = (
            '{0} | {1} | {2}\nCritical {3}  |  Warning {4}  |  '
            'Not evaluated {5}  |  Pass {6}  |  Accepted exceptions {7}  |  '
            'Error {8}  |  Information {9}'
            .format(snapshot['model'], snapshot['time'], snapshot['state'],
                    counts['Critical'], counts['Warning'], counts['Not evaluated'],
                    counts['Pass'], accepted, counts['Error'], counts['Information']))
        self.coverage_text.Text = snapshot['summary']
        self.stale_text.Text = (
            'STALE: model or settings changed. Rerun before accepting findings.'
            if stale else 'Read-only geometry review; no SDS2-ready certification.')
        self.accept_button.IsEnabled = not stale and snapshot['state'] == 'Complete'
        self.severity_filter.ItemsSource = ['Review', 'All', 'Critical', 'Error', 'Warning',
                                            'Not evaluated', 'Information', 'Pass']
        self.check_filter.ItemsSource = ['All'] + [CHECK_LABELS[c] for c in CHECKS]
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
        output = filtered_rows(self.snapshot['rows'], severity, check, level,
                               status, self.search_box.Text)
        self.detail.Text = ''
        self.findings.ItemsSource = output
        self.result_count.Text = ('Showing {0} of {1} results'.format(
            len(output), len(self.snapshot['rows'])) if output else
            'No results match these filters ({0} total results).'.format(
                len(self.snapshot['rows'])))

    def _detail(self, sender, event):
        """Show the selected finding's complete reason and exception text."""
        selected = self.findings.SelectedItem
        if selected:
            row = selected.row
            end = ' | End {0}'.format(selected.End) if selected.End else ''
            measurement = ('{0}: {1} in'.format(selected.Measurement,
                                               selected.Offset)
                           if selected.Offset else 'Measurement unavailable')
            self.detail.Text = ('{0} | {1}{2}\n{3}\nRelated: {4}\n'
                                '{5}\nException: {6}'
                                .format(selected.Check, selected.Member, end,
                                        selected.Reason, selected.Related or 'None',
                                        measurement, row['exception'] or 'None'))
            relation = self.relationships.get(row.get('relationship_id'))
            self.detail.Text += '\n' + evidence_text(relation, self.members.get(row['uid'], {}))
        else:
            self.detail.Text = ''

    def _action(self, sender, event):
        """Close the modal window and return the requested workflow action."""
        action = str(sender.Tag)
        selected = self.findings.SelectedItem
        if action in ('select', 'accept', 'reopen', 'grids') and not selected:
            forms.alert('Select a finding first.', title='Model Checker')
            return
        self.action = (action, selected.row if selected else None)
        self.Close()
