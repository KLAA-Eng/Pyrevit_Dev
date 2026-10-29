"""Summarize KL&A tool error reports for triage.

Reads report JSON files from folders, single files, or .zip archives (for
example a user's ``%LOCALAPPDATA%\\KLA Tools\\Error Reports`` folder sent in a
zip) and prints a Markdown summary that groups repeats of the same bug.

    python scripts/summarize_error_reports.py <folder|file.json|reports.zip>...
    python scripts/summarize_error_reports.py <paths>... --id PDFO-20261029-1432-7F3A

With no path, the current user's local report folder is read.
"""

import argparse
import json
import os
import sys
import zipfile


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lib.error_reports import error_signature, load_reports, local_reports_folder, summarize  # noqa: E402


def collect(paths):
    """Return reports from folders, JSON files, and zip archives."""
    files, reports = [], []
    for path in paths:
        if os.path.isdir(path):
            for folder, _, names in os.walk(path):
                files.extend(os.path.join(folder, name) for name in names if name.lower().endswith('.json'))
        elif path.lower().endswith('.zip'):
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    if not name.lower().endswith('.json'):
                        continue
                    try:
                        report = json.loads(archive.read(name).decode('utf-8'))
                    except ValueError:
                        continue
                    if isinstance(report, dict) and 'id' in report and 'error' in report:
                        report.setdefault('signature', error_signature(report))
                        reports.append(report)
        else:
            files.append(path)
    reports.extend(load_reports(files))
    unique = dict((report['id'], report) for report in reports)
    return list(unique.values())


def print_summary(reports, out):
    groups = summarize(reports)
    out.write('# Error report summary\n\n{} report(s), {} distinct problem(s).\n\n'.format(
        len(reports), len(groups)))
    for number, group in enumerate(groups, 1):
        out.write('## {}. {} ({}x)\n\n'.format(number, group['signature'], group['count']))
        out.write('- Latest message: {}\n'.format(group['message'] or '(none)'))
        out.write('- Seen: {} to {}\n'.format(group['first'], group['last']))
        out.write('- Actions: {}\n'.format(', '.join(group['actions']) or '(unknown)'))
        out.write('- Tool versions: {}\n'.format(', '.join(group['versions']) or '(unknown)'))
        out.write('- Users: {}\n'.format(', '.join(group['users']) or '(unknown)'))
        out.write('- Report ids: {}\n\n'.format(', '.join(group['ids'])))


def print_report(report, out):
    out.write('# Report {}\n\n'.format(report['id']))
    out.write('```json\n{}\n```\n'.format(json.dumps(report, indent=2, sort_keys=True)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('paths', nargs='*', help='report folders, .json files, or .zip archives')
    parser.add_argument('--id', help='print one full report by id')
    args = parser.parse_args(argv)
    paths = args.paths or [local_reports_folder()]
    missing = [path for path in paths if not os.path.exists(path)]
    if missing:
        sys.stderr.write('Not found: {}\n'.format(', '.join(missing)))
        return 1
    reports = collect(paths)
    if args.id:
        match = [report for report in reports if report['id'].upper() == args.id.upper()]
        if not match:
            sys.stderr.write('No report {} found.\n'.format(args.id))
            return 1
        print_report(match[0], sys.stdout)
        return 0
    print_summary(reports, sys.stdout)
    return 0


if __name__ == '__main__':
    sys.exit(main())
