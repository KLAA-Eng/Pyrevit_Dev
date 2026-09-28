from __future__ import print_function

import os
import re
import ast
import shutil
import tempfile
import unittest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _tab_folder_name in ("KL&A Tools_dev.tab", "KL&A Tools.tab"):
    _candidate_panel_root = os.path.join(
        REPO_ROOT, _tab_folder_name, "05 DevSandbox.panel"
    )
    if os.path.isdir(_candidate_panel_root):
        PANEL_ROOT = _candidate_panel_root
        break
else:
    raise RuntimeError("No KL&A Tools ribbon tab was found in the extension.")
PROTOTYPE_ROOT = os.path.join(PANEL_ROOT, "Prototype.pulldown")


def _read_text(path):
    with open(path, "r") as stream:
        return stream.read()


def _metadata_value(bundle_text, key):
    match = re.search(r"^{}:\s*(.+?)\s*$".format(key), bundle_text, re.MULTILINE)
    return match.group(1) if match else ""


def _load_devsandbox_root_resolver(startup_path, extension_root):
    source_tree = ast.parse(_read_text(startup_path), startup_path)
    resolver_nodes = []
    for node in source_tree.body:
        if isinstance(node, ast.Assign):
            if any(getattr(target, "id", None) == "_TAB_FOLDER_NAMES"
                   for target in node.targets):
                resolver_nodes.append(node)
        elif (isinstance(node, ast.FunctionDef) and
              node.name == "_devsandbox_root"):
            resolver_nodes.append(node)

    namespace = {"__file__": os.path.join(extension_root, "startup.py"), "os": os}
    exec(compile(ast.Module(body=resolver_nodes, type_ignores=[]),
                 startup_path, "exec"), namespace)
    return namespace["_devsandbox_root"]()


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

        self.assertIn(
            '_TAB_FOLDER_NAMES = ("KL&A Tools_dev.tab", "KL&A Tools.tab")',
            startup_text,
        )
        self.assertIn("def _devsandbox_root():", startup_text)
        self.assertIn("_devsandbox_bundle_root = _devsandbox_root()", startup_text)
        self.assertEqual(1, startup_text.count('"KL&A Tools_dev.tab"'))

    def test_startup_resolves_the_release_tab_folder(self):
        temporary_extension_root = tempfile.mkdtemp()
        try:
            expected_root = os.path.join(
                temporary_extension_root, "KL&A Tools.tab",
                "05 DevSandbox.panel", "Prototype.pulldown")
            os.makedirs(expected_root)

            resolved_root = _load_devsandbox_root_resolver(
                os.path.join(REPO_ROOT, "startup.py"),
                temporary_extension_root)

            self.assertEqual(expected_root, resolved_root)
        finally:
            shutil.rmtree(temporary_extension_root)

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
