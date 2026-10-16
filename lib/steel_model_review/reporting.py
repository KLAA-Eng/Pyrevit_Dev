"""Host-independent labels, measurements, and filtering for review results."""

CHECK_LABELS = {
    'SMR-01': 'SMR-01 - Beam endpoints',
    'SMR-02': 'SMR-02 - Vertical mismatches',
    'SMR-03': 'SMR-03 - Column grid alignment',
    'SMR-04': 'SMR-04 - Duplicates and overlaps',
    'SMR-05': 'SMR-05 - Bottom-face work planes',
    'SMR-06': 'SMR-06 - Interior crossings',
}
SEVERITY_ORDER = {'Critical': 0, 'Error': 1, 'Warning': 2, 'Not evaluated': 3,
                  'Information': 4, 'Pass': 5}


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
        self.Category = row.get('category', '')
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
        if severity in ('Review', 'Issues') and row['severity'] == 'Pass':
            continue
        if severity not in ('Review', 'Issues', 'All') and row['severity'] != severity:
            continue
        if check != 'All' and CHECK_LABELS.get(row['check'], row['check']) != check:
            continue
        if level != 'All' and row['level'] != level:
            continue
        if status != 'All' and row['status'] != status:
            continue
        display = ReviewRow(row)
        if search not in ' '.join((display.Member, display.Related,
                                   display.Reason, display.Category)).lower():
            continue
        output.append(display)
    output.sort(key=lambda r: (SEVERITY_ORDER[r.Severity], r.Check,
                               r.Member, r.End))
    return output


def evidence_text(relation, member):
    """Explain source evidence in reviewer language without serializing internals."""
    details = []
    if relation:
        facts = relation['evidence']
        details.append('Relationship: {0}'.format(relation['category']))
        if facts.get('receiving_usage'):
            details.append('Receiving member Revit structural usage: {0}'.format(facts['receiving_usage']))
        for key, label, units in (('angle_degrees', 'Plan angle', 'degrees'),
                                  ('horizontal_miss', 'Horizontal miss', 'in'),
                                  ('vertical_gap', 'Vertical separation', 'in'),
                                  ('beam_bottom', 'Beam underside elevation', 'in'),
                                  ('beam_top', 'Beam top elevation', 'in'),
                                  ('column_bottom', 'Column lower extent', 'in'),
                                  ('column_top', 'Column upper extent', 'in'),
                                  ('bottom_clearance', 'Underside above column base (negative below)', 'in'),
                                  ('top_protrusion', 'Beam top above column top (negative within)', 'in'),
                                  ('local_column_top', 'Local column bearing elevation', 'in'),
                                  ('bearing_gap', 'Underside minus local column top', 'in')):
            if facts.get(key) is not None:
                details.append('{0}: {1:.8f} {2}'.format(label, facts[key], units))
        if facts.get('group_size', 0) > 1:
            details.append('Joint contains {0} actual relationships.'.format(facts['group_size']))
        join = facts.get('join')
        if join:
            participants = ', '.join(str(p['id']) for p in join.get('participants', []))
            details.append('Revit end-join query: {0}; returned elements: {1}.'.format(
                join.get('state', 'Unavailable'), participants or 'none returned'))
            allowed = join.get('allowed')
            details.append('Revit joining allowed: {0}.'.format(
                'Unknown' if allowed is None else 'Yes' if allowed else 'No'))
            details.extend(join.get('errors', []))
        work_plane = facts.get('work_plane')
        if work_plane:
            details.append('Bottom-face association: {0}'.format(work_plane['state']))
            plane = work_plane.get('work_plane')
            if plane:
                details.append('Work plane: {0}'.format(plane.get('name', plane.get('id'))
                                                       if isinstance(plane, dict) else plane))
            details.append(work_plane.get('reason', ''))
    parameters = member.get('raw_parameters', {})
    if parameters:
        details.append('Offsets/justification retained for SDS2 transfer investigation:')
        for key in sorted(parameters):
            item = parameters[key]
            label = key.replace('STRUCTURAL_BEAM_', '').replace('_', ' ').lower()
            if item['state'] == 'Value':
                details.append('{0}: {1} {2}'.format(label, item['value'], item.get('units', '')))
            elif item['state'] == 'Unavailable':
                details.append('{0}: unavailable ({1})'.format(label, item.get('reason', '')))
    return '\n'.join(details)
