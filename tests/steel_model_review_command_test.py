"""Verify failure diagnostics without requiring a running Revit document."""

import ast
import contextlib
import io
import os
import sys
import traceback
import types
import unittest
from unittest import mock


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMAND = os.path.join(
    ROOT, 'KL&A Tools_dev.tab', '05 DevSandbox.panel', 'Model Review.pulldown',
    'Model Checker.pushbutton', 'script.py')


def diagnostic_functions():
    with io.open(COMMAND, encoding='utf-8') as stream:
        tree = ast.parse(stream.read(), COMMAND)
    names = ('_stage', '_report_failure', 'run_command')
    tree.body = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    output = mock.Mock()
    logger = mock.Mock()
    alert = mock.Mock()
    scope = {'sys': sys, 'traceback': traceback, '__title__': 'Model Checker',
             'RUN_STAGE': 'Starting Model Checker',
             'script': types.SimpleNamespace(get_output=lambda: output,
                                             get_logger=lambda: logger),
             'forms': types.SimpleNamespace(alert=alert)}
    exec(compile(tree, COMMAND, 'exec'), scope)
    return scope, output, logger, alert


class CommandDiagnosticsTests(unittest.TestCase):
    def test_dialog_contains_original_traceback_and_stage(self):
        scope, output, logger, alert = diagnostic_functions()
        scope['_stage']('Choosing the export phase')
        details = 'Traceback (most recent call last):\nValueError: phase failure\n'
        scope['_report_failure'](details)
        message = alert.call_args[0][0]
        expanded = alert.call_args[1]['expanded']
        self.assertIn('Choosing the export phase', message)
        self.assertIn('ValueError: phase failure', message)
        self.assertIn(details, expanded)
        self.assertIn(sys.version, expanded)

    def test_output_renderer_receives_full_diagnostics_directly(self):
        scope, output, logger, alert = diagnostic_functions()
        scope['_report_failure']('RuntimeError: geometry failed')
        output.print_code.assert_called_once()
        self.assertIn('RuntimeError: geometry failed', output.print_code.call_args[0][0])

    def test_logger_failure_cannot_hide_dialog(self):
        scope, output, logger, alert = diagnostic_functions()
        logger.error.side_effect = RuntimeError('Logger unavailable')
        scope['_report_failure']('ValueError: original failure')
        alert.assert_called_once()
        self.assertIn('original failure', alert.call_args[1]['expanded'])

    def test_output_failure_falls_back_to_stdout_and_dialog(self):
        scope, output, logger, alert = diagnostic_functions()
        output.print_md.side_effect = RuntimeError('Renderer unavailable')
        text = io.StringIO()
        with contextlib.redirect_stdout(text):
            scope['_report_failure']('ValueError: original failure')
        self.assertIn('original failure', text.getvalue())
        self.assertIn('original failure', alert.call_args[1]['expanded'])

    def test_entry_point_preserves_failure_before_reporting(self):
        scope, output, logger, alert = diagnostic_functions()
        def fail():
            scope['_stage']('Opening the findings browser')
            raise RuntimeError('WPF binding failed')
        scope['main'] = fail
        scope['run_command']()
        self.assertIn('RuntimeError: WPF binding failed',
                      alert.call_args[1]['expanded'])
        self.assertIn('Opening the findings browser', alert.call_args[0][0])

    def test_successful_command_does_not_report_failure(self):
        scope, output, logger, alert = diagnostic_functions()
        scope['main'] = mock.Mock()
        scope['run_command']()
        alert.assert_not_called()


if __name__ == '__main__':
    unittest.main()
