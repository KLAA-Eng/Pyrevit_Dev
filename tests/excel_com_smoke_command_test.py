import os
import unittest


ROOT = os.path.dirname(os.path.dirname(__file__))
PULLDOWN = os.path.join(
    ROOT, 'KL&A Tools.tab', '05 DevSandbox.panel', 'Prototype.pulldown')
COMMAND = os.path.join(PULLDOWN, 'Excel COM Smoke Test.pushbutton')


class ExcelComSmokeCommandTests(unittest.TestCase):
    def test_smoke_command_is_registered_and_has_required_artifacts(self):
        with open(os.path.join(PULLDOWN, 'bundle.yaml'), 'r') as stream:
            layout = stream.read()
        self.assertIn('- Excel COM Smoke Test', layout)
        for filename in ('bundle.yaml', 'script.py', 'SPEC.md'):
            self.assertTrue(os.path.isfile(os.path.join(COMMAND, filename)))

    def test_smoke_script_uses_only_public_explicit_excel_facade(self):
        with open(os.path.join(COMMAND, 'script.py'), 'r') as stream:
            source = stream.read()
        compile(source, os.path.join(COMMAND, 'script.py'), 'exec')
        self.assertIn('from excel_com import (', source)
        self.assertIn('get_property', source)
        self.assertIn('set_property', source)
        self.assertIn('call_method', source)
        self.assertIn('get_item', source)
        self.assertNotIn('_wrap_com', source)
        self.assertNotIn('_ExcelComProxy', source)
        self.assertIn('SMOKE_ROOT_NAME', source)
        self.assertIn('_is_owned_path', source)
        self.assertIn('_error_detail', source)
        self.assertIn("'Facade Table'", source)


if __name__ == '__main__':
    unittest.main()
