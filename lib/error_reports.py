# -*- coding: utf-8 -*-
"""Error reports that KL&A tools write when something unexpected fails.

Each incident is one small JSON file named by its report id (for example
``PDFO-20261029-1432-7F3A``), so concurrent writers never share a file and a
user can quote the id with their feedback. Reports always go to a local
folder; ``SHARED_REPORTS_FOLDER`` can later name a shared folder that also
receives a copy when it is reachable.

This module is host-independent (it runs under IronPython and CPython);
``error_reports_revit`` gathers the Revit context and shows the id.
"""

import datetime
import json
import os
import re
import tempfile
import uuid


REPORT_VERSION = 1
# Set to a folder every user can write to (for example a UNC path) to also
# collect reports centrally. Empty keeps reports on each computer only.
SHARED_REPORTS_FOLDER = ''
LOG_TAIL_LINES = 40
_CLOUD_PREFIX = re.compile(r'^(?:\{[0-9A-Fa-f-]+\})+')
_FRAME = re.compile(r'File "([^"]+)", line (\d+), in (\S+)')


def local_reports_folder(environ=None):
    environ = os.environ if environ is None else environ
    base = environ.get('LOCALAPPDATA') or tempfile.gettempdir()
    return os.path.join(base, 'KLA Tools', 'Error Reports')


def make_report_id(tool_code, now=None, suffix=None):
    """Return an id like PDFO-20261029-1432-7F3A (tool, date, time, random)."""
    now = now or datetime.datetime.now()
    suffix = suffix or uuid.uuid4().hex[:4]
    return '{}-{:%Y%m%d-%H%M}-{}'.format(tool_code.upper(), now, suffix.upper())


def model_name(path_or_title):
    """Return a model's file name without its folder (or cloud ids)."""
    if not path_or_title:
        return ''
    name = re.split(r'[\\/]', path_or_title.strip())[-1]
    return _CLOUD_PREFIX.sub('', name)


def read_log_tail(path, lines=LOG_TAIL_LINES):
    """Return the last lines of a text log, or [] if it cannot be read."""
    if not path:
        return []
    try:
        with open(path, 'r') as log_file:
            return [line.rstrip('\r\n') for line in log_file.readlines()[-lines:]]
    except (IOError, OSError):
        return []


def build_report(report_id, tool, action, error_type, error_message, traceback_text,
                 context=None, log_tail=None, now=None):
    """Return the report dictionary.

    tool: {'id', 'name', 'version'}. context: environment facts such as
    extension_version, revit_version, revit_build, pyrevit_version, user,
    and model. Unknown context keys are kept as given.
    """
    now = now or datetime.datetime.now()
    report = {
        'report_version': REPORT_VERSION,
        'id': report_id,
        'created': now.strftime('%Y-%m-%dT%H:%M:%S'),
        'tool': dict(tool),
        'action': action or '',
        'error': {
            'type': error_type or '',
            'message': error_message or '',
            'traceback': traceback_text or '',
        },
        'context': dict(context or {}),
        'log_tail': list(log_tail or []),
    }
    report['signature'] = error_signature(report)
    return report


def error_signature(report):
    """Return a grouping key: tool, error type, and the innermost code frame.

    Reports with the same signature are the same bug seen again; the message
    is left out because it often contains element ids or paths.
    """
    frames = _FRAME.findall(report.get('error', {}).get('traceback', ''))
    where = ''
    if frames:
        path, line, function = frames[-1]
        where = '{}:{} {}'.format(os.path.basename(path.replace('\\', '/')), line, function)
    return '{} | {} | {}'.format(report.get('tool', {}).get('id', ''),
                                 report.get('error', {}).get('type', ''), where)


def write_report(report, folders):
    """Write the report as <id>.json into each reachable folder.

    Returns the paths written. Never raises: an error report must not cause
    a second error.
    """
    written = []
    for folder in folders:
        if not folder:
            continue
        try:
            if not os.path.isdir(folder):
                os.makedirs(folder)
            path = os.path.join(folder, report['id'] + '.json')
            with open(path, 'w') as report_file:
                json.dump(report, report_file, indent=2, sort_keys=True)
            written.append(path)
        except Exception:
            continue
    return written


def report_folders(environ=None):
    return [local_reports_folder(environ), SHARED_REPORTS_FOLDER]


def load_reports(paths):
    """Load report files, skipping anything that is not a readable report."""
    reports = []
    for path in paths:
        try:
            with open(path, 'r') as report_file:
                report = json.load(report_file)
        except (IOError, OSError, ValueError):
            continue
        if isinstance(report, dict) and 'id' in report and 'error' in report:
            report.setdefault('signature', error_signature(report))
            reports.append(report)
    return reports


def summarize(reports):
    """Group reports by signature, most frequent first.

    Returns dicts with signature, count, first and last created times,
    report ids, users, tool versions, and the latest message.
    """
    groups = {}
    for report in sorted(reports, key=lambda item: item.get('created', '')):
        group = groups.setdefault(report['signature'], {
            'signature': report['signature'], 'count': 0, 'first': report.get('created', ''),
            'last': '', 'ids': [], 'users': set(), 'versions': set(), 'message': '',
            'actions': set(),
        })
        group['count'] += 1
        group['last'] = report.get('created', '')
        group['ids'].append(report['id'])
        group['users'].add(report.get('context', {}).get('user', ''))
        group['versions'].add(report.get('tool', {}).get('version', ''))
        group['actions'].add(report.get('action', ''))
        group['message'] = report.get('error', {}).get('message', '')
    result = []
    for group in groups.values():
        for key in ('users', 'versions', 'actions'):
            group[key] = sorted(value for value in group[key] if value)
        result.append(group)
    return sorted(result, key=lambda group: (-group['count'], group['signature']))
