"""Exact view/sheet targets, independent of WPF and Revit transactions."""
from __future__ import unicode_literals

from find_replace.workflow import case_value, rename_value


def _target(current, request, field):
    if request['operation'] == 'rename':
        rules = request['fields'][field]
        return rename_value(current, rules['find'], rules['replace'],
                            rules['prefix'], rules['suffix'])
    return case_value(current, request['operation'])


def view_entries(views, request):
    entries = []
    for view in views:
        old = view.Name
        new = _target(old, request, 'name')
        entries.append(dict(element=view,
            label='{0} [{1}]'.format(old, view.Id.IntegerValue),
            changes=[('Name', new)] if new != old else []))
    return entries


def sheet_entries(sheets, request, all_sheets):
    entries = []
    for sheet in sheets:
        name, number = sheet.Name, sheet.SheetNumber
        new_name = _target(name, request, 'name')
        new_number = (_target(number, request, 'number')
                      if request['operation'] == 'rename' else number)
        changes = []
        if new_name != name:
            changes.append(('Name', new_name))
        if new_number != number:
            changes.append(('SheetNumber', new_number))
        entries.append(dict(element=sheet,
            label='{0} - {1} [{2}]'.format(number, name, sheet.Id.IntegerValue),
            changes=changes, number=new_number, number_changed=new_number != number))
    # Compare with the initial model state: swaps/occupied numbers and repeated
    # requested numbers must not become dependent on iteration order.
    occupied = dict((sheet.SheetNumber.lower(), sheet.Id.IntegerValue) for sheet in all_sheets)
    requested = {}
    for entry in entries:
        if entry['number_changed']:
            key = entry['number'].lower()
            requested[key] = requested.get(key, 0) + 1
    for entry in entries:
        if not entry['number_changed']:
            continue
        key = entry['number'].lower()
        holder = occupied.get(key)
        if holder is not None and holder != entry['element'].Id.IntegerValue:
            entry['issue'] = 'Sheet number is already in use'
        elif requested[key] > 1:
            entry['issue'] = 'Multiple selected sheets request this number'
    return entries
