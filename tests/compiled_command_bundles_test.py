from __future__ import print_function

import os
import re
import unittest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL_ROOT = os.path.join(
    REPO_ROOT, "KL&A Tools_dev.tab", "05 DevSandbox.panel"
)


def _read_text(path):
    with open(path, "r") as stream:
        return stream.read()


def _metadata_value(bundle_text, key):
    match = re.search(r"^{}:\s*(.+?)\s*$".format(key), bundle_text, re.MULTILINE)
    return match.group(1) if match else ""


class CompiledCommandBundlesTest(unittest.TestCase):
    def test_compiled_commands_are_exposed_in_dev_sandbox(self):
        panel_metadata = _read_text(os.path.join(PANEL_ROOT, "bundle.yaml"))

        command_classes = {
            "Startup Importer": "StartupImportCommand",
            "Family Studio": "FamilyStudioCommand",
        }

        for command_name, command_class in command_classes.items():
            bundle_root = os.path.join(
                PANEL_ROOT, command_name + ".invokebutton"
            )
            bundle_metadata_path = os.path.join(bundle_root, "bundle.yaml")

            self.assertTrue(os.path.isdir(bundle_root), bundle_root)
            self.assertTrue(os.path.isfile(bundle_metadata_path), bundle_metadata_path)
            self.assertFalse(os.path.exists(os.path.join(bundle_root, "script.py")))

            bundle_metadata = _read_text(bundle_metadata_path)
            self.assertTrue(_metadata_value(bundle_metadata, "assembly"))
            self.assertEqual(
                command_class,
                _metadata_value(bundle_metadata, "command_class"),
            )
            self.assertIn("  - " + command_name, panel_metadata)


if __name__ == "__main__":
    unittest.main()
