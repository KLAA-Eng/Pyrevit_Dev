from __future__ import print_function

import datetime
import json
import os
import shutil
import sys
import tempfile
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from lib.error_reports import (
    build_report,
    error_signature,
    load_reports,
    local_reports_folder,
    make_report_id,
    model_name,
    read_log_tail,
    summarize,
    write_report,
)


TRACEBACK = '''Traceback (most recent call last):
  File "C:\\ext\\PDF Overlay.pushbutton\\script.py", line 890, in Execute
    action(uiapp)
  File "C:\\ext\\lib\\pdf_overlay\\members.py", line 212, in match_members
    raise ValueError('bad member 1234')
ValueError: bad member 1234
'''
TOOL = {'id': 'devsandbox.pdf-overlay', 'name': 'PDF Overlay', 'version': 'v0.0'}


def sample(report_id='PDFO-20261029-1432-7F3A', when=None, user='tleigh', tool=None, traceback=TRACEBACK):
    return build_report(report_id, tool or TOOL, 'Check Members', 'ValueError', 'bad member 1234',
                        traceback, {'user': user, 'model': 'Lodge.rvt'}, ['line one'],
                        when or datetime.datetime(2026, 10, 29, 14, 32, 5))


class ErrorReportTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.folder)

    def test_report_id_names_tool_time_and_suffix(self):
        when = datetime.datetime(2026, 10, 29, 14, 32)
        self.assertEqual('PDFO-20261029-1432-7F3A', make_report_id('pdfo', when, '7f3a'))
        self.assertRegex(make_report_id('PDFO'), r'^PDFO-\d{8}-\d{4}-[0-9A-F]{4}$')

    def test_model_name_drops_folders_and_cloud_ids(self):
        self.assertEqual('Lodge.rvt', model_name('C:\\Projects\\24343\\Lodge.rvt'))
        self.assertEqual('24343_Snake River Lodge_S24.rvt', model_name(
            'CLD:\\US\\{89751eb1-2c65}\\{1e4cea40-8c2e}24343_Snake River Lodge_S24.rvt'))
        self.assertEqual('', model_name(None))

    def test_report_holds_error_context_and_signature(self):
        report = sample()
        self.assertEqual('2026-10-29T14:32:05', report['created'])
        self.assertEqual('Check Members', report['action'])
        self.assertEqual('Lodge.rvt', report['context']['model'])
        self.assertEqual('devsandbox.pdf-overlay | ValueError | members.py:212 match_members',
                         report['signature'])

    def test_signature_ignores_message_details(self):
        other = sample(traceback=TRACEBACK.replace('1234', '9876'))
        self.assertEqual(error_signature(sample()), error_signature(other))
        self.assertEqual('devsandbox.pdf-overlay | ValueError | ',
                         sample(traceback='').get('signature'))

    def test_write_and_load_round_trip_and_skip_bad_folders(self):
        report = sample()
        blocked = os.path.join(self.folder, 'file-not-folder')
        open(blocked, 'w').close()
        written = write_report(report, [self.folder, '', blocked])
        self.assertEqual([os.path.join(self.folder, report['id'] + '.json')], written)
        junk = os.path.join(self.folder, 'junk.json')
        with open(junk, 'w') as junk_file:
            junk_file.write('{not json')
        loaded = load_reports(written + [junk, os.path.join(self.folder, 'missing.json')])
        self.assertEqual([report], loaded)

    def test_summarize_groups_repeats_most_frequent_first(self):
        reports = [
            sample('A', datetime.datetime(2026, 10, 29, 9, 0), 'ann'),
            sample('B', datetime.datetime(2026, 10, 29, 10, 0), 'bob'),
            sample('C', datetime.datetime(2026, 10, 28, 8, 0), 'ann',
                   traceback=TRACEBACK.replace('line 212', 'line 300')),
        ]
        groups = summarize(reports)
        self.assertEqual([2, 1], [group['count'] for group in groups])
        self.assertEqual(['A', 'B'], groups[0]['ids'])
        self.assertEqual(['ann', 'bob'], groups[0]['users'])
        self.assertEqual(('2026-10-29T09:00:00', '2026-10-29T10:00:00'),
                         (groups[0]['first'], groups[0]['last']))

    def test_log_tail_and_folder(self):
        log_path = os.path.join(self.folder, 'tool.log')
        with open(log_path, 'w') as log_file:
            log_file.write('\n'.join(str(number) for number in range(100)))
        self.assertEqual(['97', '98', '99'], read_log_tail(log_path, 3))
        self.assertEqual([], read_log_tail(os.path.join(self.folder, 'none.log')))
        self.assertEqual(os.path.join('C:\\L', 'KLA Tools', 'Error Reports'),
                         local_reports_folder({'LOCALAPPDATA': 'C:\\L'}))
        self.assertTrue(json.dumps(sample()))


class ReportExceptionTests(unittest.TestCase):
    """The host helper degrades to user name only when Revit is absent."""

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        lib_path = os.path.join(PROJECT_ROOT, 'lib')
        if lib_path not in sys.path:
            sys.path.insert(0, lib_path)
        import error_reports
        import error_reports_revit
        self.module = error_reports_revit
        self.original = error_reports_revit.report_folders
        error_reports_revit.report_folders = lambda: [self.folder]
        self.addCleanup(setattr, error_reports_revit, 'report_folders', self.original)
        self.load = error_reports.load_reports

    def tearDown(self):
        shutil.rmtree(self.folder)

    def test_report_exception_writes_the_handled_error(self):
        try:
            raise KeyError('pose')
        except KeyError:
            report_id, message = self.module.report_exception(TOOL, 'PDFO', 'Align')
        self.assertRegex(report_id, r'^PDFO-')
        self.assertIn(report_id, message)
        self.assertIn('Suggestions/Bugs Feedback', message)
        report = self.load([os.path.join(self.folder, report_id + '.json')])[0]
        self.assertEqual(('Align', 'KeyError'), (report['action'], report['error']['type']))
        self.assertIn("raise KeyError('pose')", report['error']['traceback'])
        self.assertIn('user', report['context'])

    def test_unwritable_folder_returns_a_message_not_an_error(self):
        self.module.report_folders = lambda: []
        try:
            raise ValueError('x')
        except ValueError:
            report_id, message = self.module.report_exception(TOOL, 'PDFO', 'Align')
        self.assertIsNone(report_id)
        self.assertEqual('The error report could not be saved.', message)


if __name__ == '__main__':
    unittest.main()
