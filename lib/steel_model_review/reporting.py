"""Host-independent labels, measurements, and filtering for review results."""

CHECK_LABELS = {
    'SMR-01': 'SMR-01 - Beam endpoints',
    'SMR-02': 'SMR-02 - Vertical mismatches',
    'SMR-03': 'SMR-03 - Column grid alignment',
    'SMR-04': 'SMR-04 - Duplicates and overlaps',
}
SEVERITY_ORDER = {'Critical': 0, 'Warning': 1, 'Not evaluated': 2, 'Pass': 3}


def _element_label(name, element_id):
    """Include an ID once, including names already prefixed by extraction."""
    if name == str(element_id) or name.startswith('{0}:'.format(element_id)):
        return name
    return '{0} [{1}]'.format(name, element_id)


class ReviewRow(object):
    """Expose readable report fields without depending on WPF or Revit."""

    def __init__(self, row):
        self.row = row
        self.Severity = row['severity']
        self.Check = CHECK_LABELS.get(row['check'], row['check'])
        self.Member = _element_label(row['member'], row['id'])
        self.End = str(row['end'])
        self.Level = row['level']
        self.Value = row['value']
        self.Measurement = (row.get('measurement', 'Offset')
                            if self.Value is not None else 'Not measured')
        self.Offset = ('{0:+.8f}'.format(row['value'])
                       if row['value'] is not None else '')
        self.Related = ', '.join(_element_label(r.get('name', ''), r['id'])
                                 for r in row['related'])
        self.Status = row['status']
        self.Reason = row['reason']


def filtered_rows(rows, severity='Issues', check='All', level='All',
                  status='All', search=''):
    """Return sorted display rows matching the reviewer's visible filters.

    Search includes the member's ID and all related element names and IDs.
    Accepted findings retain their measured severity and remain searchable.
    """
    output = []
    search = search.strip().lower()
    for row in rows:
        if severity == 'Issues' and row['severity'] == 'Pass':
            continue
        if severity not in ('Issues', 'All') and row['severity'] != severity:
            continue
        if check != 'All' and CHECK_LABELS.get(row['check'], row['check']) != check:
            continue
        if level != 'All' and row['level'] != level:
            continue
        if status != 'All' and row['status'] != status:
            continue
        display = ReviewRow(row)
        if search not in ' '.join((display.Member, display.Related,
                                   display.Reason)).lower():
            continue
        output.append(display)
    output.sort(key=lambda r: (SEVERITY_ORDER[r.Severity], r.Check,
                               r.Member, r.End))
    return output
