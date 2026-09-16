from __future__ import print_function

import os
import re
import unittest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL_ROOT = os.path.join(
    REPO_ROOT, "KL&A Tools_dev.tab", "05 DevSandbox.panel"
)
PROTOTYPE_ROOT = os.path.join(PANEL_ROOT, "Prototype.pulldown")


def _read_text(path):
    with open(path, "r") as stream:
        return stream.read()


def _metadata_value(bundle_text, key):
    match = re.search(r"^{}:\s*(.+?)\s*$".format(key), bundle_text, re.MULTILINE)
    return match.group(1) if match else ""


class CompiledCommandBundlesTest(unittest.TestCase):
    def test_compiled_commands_are_exposed_in_dev_sandbox(self):
        panel_metadata = _read_text(os.path.join(PANEL_ROOT, "bundle.yaml"))
        prototype_metadata = _read_text(
            os.path.join(PROTOTYPE_ROOT, "bundle.yaml")
        )
        self.assertIn("  - Prototype", panel_metadata)

        command_classes = {
            "Startup Importer": "StartupImportCommand",
            "Family Studio": "FamilyStudioCommand",
        }

        for command_name, command_class in command_classes.items():
            bundle_root = os.path.join(
                PROTOTYPE_ROOT, command_name + ".invokebutton"
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
            self.assertIn("  - " + command_name, prototype_metadata)

    def test_startup_preloads_dependencies_from_prototype_pulldown(self):
        startup_path = os.path.join(REPO_ROOT, "startup.py")
        startup_text = _read_text(startup_path)

        self.assertNotIn(
            '"05 DevSandbox.panel",\n                "Startup Importer.invokebutton"',
            startup_text,
        )
        self.assertNotIn(
            '"05 DevSandbox.panel",\n                "Family Studio.invokebutton"',
            startup_text,
        )
        self.assertGreaterEqual(
            startup_text.count('"Prototype.pulldown"'),
            18,
        )

    def test_compiled_package_outputs_target_prototype_pulldown(self):
        source_paths = (
            os.path.join(
                REPO_ROOT, "src", "KLA.ModelStartupImporter",
                "KLA.ModelStartupImporter.Packaging.proj",
            ),
            os.path.join(
                REPO_ROOT, "src", "KLA.ModelStartupImporter",
                "KLA.ModelStartupImporter.Revit",
                "KLA.ModelStartupImporter.Revit.csproj",
            ),
            os.path.join(
                REPO_ROOT, "src", "KLCode.FamilyStudio", "Revit",
                "KLCode.FamilyStudio.Revit",
                "KLCode.FamilyStudio.Revit.csproj",
            ),
        )

        for source_path in source_paths:
            self.assertIn("Prototype.pulldown", _read_text(source_path))

    def test_startup_preloads_host_specific_compiled_dependencies(self):
        startup_path = os.path.join(REPO_ROOT, "startup.py")
        startup_text = _read_text(startup_path)

        self.assertIn('_compiled_wpf_assembly = "KLCode.Wpf_2024.dll"', startup_text)
        self.assertIn('_startup_importer_ui_assembly = "KLA.ModelStartupImporter.UI_2024.dll"', startup_text)
        self.assertIn('_compiled_wpf_assembly = "KLCode.Wpf.dll"', startup_text)
        self.assertIn('_startup_importer_ui_assembly = "KLA.ModelStartupImporter.UI.dll"', startup_text)
        self.assertLess(
            startup_text.index("_compiled_wpf_assembly),"),
            startup_text.index("_startup_importer_ui_assembly),"),
        )


if __name__ == "__main__":
    unittest.main()
