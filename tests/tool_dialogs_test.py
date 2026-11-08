"""Tool-facing result and cancellation contracts for standard dialogs."""
from __future__ import unicode_literals

import os
import sys
import types
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_ROOT = os.environ.get('KLC_TOOL_DIALOGS_SOURCE_ROOT', PROJECT_ROOT)
sys.path.insert(0, os.path.join(SOURCE_ROOT, 'lib'))
import GUI
GUI.__path__.insert(0, os.path.join(PROJECT_ROOT, 'lib', 'GUI'))
from GUI import dialogs, tool_dialogs
from GUI.dialogs.models import DialogResult


class ToolDialogTests(unittest.TestCase):
    def setUp(self):
        self.original_owner = tool_dialogs._owner
        tool_dialogs._owner = lambda owner: owner if owner is not None else 12345
        self.originals = {}
        self.calls = []
        self.result = DialogResult('ok')
        for name in ('show_message', 'choose_action', 'ask_text'):
            self.originals[name] = getattr(dialogs, name)

            def factory(*args, **kwargs):
                self.calls.append((args, kwargs))
                return self.result

            setattr(dialogs, name, factory)

    def tearDown(self):
        tool_dialogs._owner = self.original_owner
        for name, value in self.originals.items():
            setattr(dialogs, name, value)

    def test_notice_preserves_content_and_warning(self):
        self.assertTrue(tool_dialogs.alert('Summary', title='Tool', sub_msg='Body',
                                          expanded='Details', warn_icon=True))
        args, options = self.calls[0]
        self.assertEqual(('Tool', 'Summary\n\nBody'), args)
        self.assertEqual('warning', options['severity'])
        self.assertEqual('Details', options['details'])

    def test_notice_close_returns_false(self):
        self.result = DialogResult('cancel')
        self.assertFalse(tool_dialogs.alert('Notice', title='Tool'))

    def test_notice_exit_happens_even_after_ok(self):
        with self.assertRaises(SystemExit):
            tool_dialogs.alert('Stop', title='Tool', exitscript=True)

    def test_yes_no_accepts_yes_and_declines_no(self):
        self.result = DialogResult('accept', {'kind': 'button', 'key': 'yes'})
        self.assertTrue(tool_dialogs.alert('Write?', title='Tool', ok=False, yes=True, no=True))
        args, options = self.calls[-1]
        self.assertEqual(('yes', 'no'), options['buttons'])
        self.result = DialogResult('accept', {'kind': 'button', 'key': 'no'})
        self.assertFalse(tool_dialogs.alert('Write?', title='Tool', ok=False, yes=True, no=True))

    def test_yes_no_close_is_false_and_exit_flag_is_respected(self):
        self.result = DialogResult('close')
        self.assertFalse(tool_dialogs.alert('Write?', title='Tool', ok=False, yes=True, no=True))
        with self.assertRaises(SystemExit):
            tool_dialogs.alert('Write?', title='Tool', ok=False, yes=True, no=True, exitscript=True)

    def test_yes_overrides_default_ok_and_positive_does_not_exit(self):
        self.result = DialogResult('accept', {'kind': 'button', 'key': 'yes'})
        self.assertTrue(tool_dialogs.alert('Use?', title='Tool', yes=True, no=True, exitscript=True))
        self.assertEqual(('yes', 'no'), self.calls[-1][1]['buttons'])

    def test_owner_and_version_are_forwarded_without_model_work(self):
        owner = object()
        tool_dialogs.alert('Notice', title='Tool', warn_icon=False, owner=owner, version='v1.0')
        options = self.calls[-1][1]
        self.assertIs(owner, options['owner'])
        self.assertEqual('v1.0', options['version'])
        self.assertEqual('information', options['severity'])

    def test_menu_returns_original_action_and_cancel_is_a_standard_button(self):
        self.result = DialogResult('accept', {'kind': 'command', 'key': 'Unhide'})
        self.assertEqual('Unhide', tool_dialogs.choose(['Hide', 'Unhide', 'Cancel'], 'Tool', 'Choose'))
        args, options = self.calls[-1]
        self.assertEqual(['Hide', 'Unhide'], [row.Key for row in args[1]])
        self.assertEqual(('cancel',), options['buttons'])
        self.result = DialogResult('cancel')
        self.assertIsNone(tool_dialogs.choose(['Hide', 'Unhide'], 'Tool', 'Choose'))

    def test_blank_text_is_accepted_but_cancel_is_none(self):
        self.result = DialogResult('accept', '')
        self.assertEqual('', tool_dialogs.ask_text(default='', prompt='Subject', title='Tool'))
        self.assertFalse(self.calls[-1][1]['required'])
        self.result = DialogResult('cancel')
        self.assertIsNone(tool_dialogs.ask_text(default='', prompt='Subject', title='Tool'))


@unittest.skipUnless(os.environ.get('KLC_TOOL_DIALOGS_WPF') == '1', 'Requires WPF/IronPython')
class ToolDialogWpfTests(unittest.TestCase):
    def setUp(self):
        self.originals = {}
        self.windows = []
        self.interaction = None
        for name in ('create_message', 'create_choice', 'create_text_prompt'):
            original = getattr(dialogs, name)
            self.originals[name] = original

            # Bind each original factory separately in Python 2's shared loop scope.
            def bind(original_factory):
                return lambda *args, **kwargs: self._create(original_factory, args, kwargs)

            setattr(dialogs, name, bind(original))

    def _create(self, factory, args, kwargs):
        from System.Windows import WindowStartupLocation
        window = factory(*args, **kwargs)
        window.WindowStartupLocation = WindowStartupLocation.Manual
        window.Left = -10000
        window.Top = -10000
        self.windows.append(window)
        window.Loaded += lambda sender, event: self.interaction(window)
        return window

    def tearDown(self):
        for name, original in self.originals.items():
            setattr(dialogs, name, original)
        for window in self.windows:
            window.Close()

    def test_actual_message_accepts(self):
        self.interaction = lambda window: window.accept_message(None, None)
        self.assertTrue(tool_dialogs.alert('Notice', title='Tool', owner=0))

    def test_actual_yes_no_returns_distinct_booleans(self):
        self.interaction = lambda window: window.action_clicked(window.common_buttons['no'], None)
        self.assertFalse(tool_dialogs.alert('Write?', title='Tool', yes=True, no=True, owner=0))
        self.interaction = lambda window: window.action_clicked(window.common_buttons['yes'], None)
        self.assertTrue(tool_dialogs.alert('Write?', title='Tool', yes=True, no=True, owner=0))

    def test_actual_menu_returns_exact_command(self):
        self.interaction = lambda window: window.action_clicked(window.command_buttons['Unhide'], None)
        self.assertEqual('Unhide', tool_dialogs.choose(['Hide', 'Unhide', 'Cancel'], 'Tool', owner=0))

    def test_actual_text_preserves_blank_value(self):
        self.interaction = lambda window: window.accept_text()
        self.assertEqual('', tool_dialogs.ask_text(title='Tool', prompt='Subject', owner=0))


class HostMetadataTests(unittest.TestCase):
    def test_host_owner_and_title_are_resolved_only_on_demand(self):
        originals = dict((name, sys.modules.get(name)) for name in ('pyrevit', 'pyrevit.api'))
        host = types.ModuleType('pyrevit')
        api = types.ModuleType('pyrevit.api')
        host.EXEC_PARAMS = type('Params', (), {'command_name': 'Caller Tool'})()
        api.AdWindows = type('Windows', (), {
            'ComponentManager': type('Manager', (), {'ApplicationWindow': 9876})()})()
        sys.modules['pyrevit'] = host
        sys.modules['pyrevit.api'] = api
        try:
            self.assertEqual(9876, tool_dialogs._owner(None))
            self.assertEqual('Caller Tool', tool_dialogs._title(None))
            explicit = object()
            self.assertIs(explicit, tool_dialogs._owner(explicit))
            self.assertEqual('Explicit', tool_dialogs._title('Explicit'))
        finally:
            for name, value in originals.items():
                if value is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = value


if __name__ == '__main__':
    unittest.main()
