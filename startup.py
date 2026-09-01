"""Prepare managed DevSandbox dependencies for pyRevit Invoke Buttons."""
from __future__ import print_function

import os

from pyrevit import HOST_APP
from System import Environment
from System.IO import File
from System.Reflection import Assembly


def _load_dependency(relative_path):
    """Load one managed assembly without locking its package file."""
    assembly_path = os.path.join(os.path.dirname(__file__), relative_path)
    if not File.Exists(assembly_path):
        print("DevSandbox dependency is missing: {}".format(assembly_path))
        return

    try:
        Assembly.Load(File.ReadAllBytes(assembly_path))
    except Exception as error:
        print("Could not preload {}: {}".format(relative_path, error))


if HOST_APP.version in ("2024", "2025", "2026"):
    # Invoke Button loads the command assembly from bytes. Revit provides its
    # own API assemblies, but managed companions in each package must be loaded
    # into the AppDomain before the command resolves them.
    # The 2024 host uses .NET Framework assemblies with a `_2024` identity;
    # newer hosts use the .NET 8 assemblies without that suffix.
    _compiled_wpf_assembly = "KLCode.Wpf_2024.dll"
    _startup_importer_ui_assembly = "KLA.ModelStartupImporter.UI_2024.dll"
    if HOST_APP.version != "2024":
        _compiled_wpf_assembly = "KLCode.Wpf.dll"
        _startup_importer_ui_assembly = "KLA.ModelStartupImporter.UI.dll"

    _family_studio_bin = os.path.join(
        os.path.dirname(__file__), "KL&A Tools_dev.tab", "05 DevSandbox.panel",
        "Family Studio.invokebutton", "bin")
    _family_studio_data_root = os.path.join(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "KLCode", "FamilyStudio")
    if not os.path.isdir(_family_studio_data_root):
        os.makedirs(_family_studio_data_root)
    Environment.SetEnvironmentVariable(
        "KLCODE_FAMILY_STUDIO_DATABASE",
        os.path.join(_family_studio_data_root, "family_studio-devsandbox.sqlite"))
    if File.Exists(os.path.join(_family_studio_bin, "e_sqlite3.dll")):
        Environment.SetEnvironmentVariable(
            "KLCODE_FAMILY_STUDIO_NATIVE_SQLITE",
            os.path.join(_family_studio_bin, "e_sqlite3.dll"))
        current_path = Environment.GetEnvironmentVariable("PATH") or ""
        Environment.SetEnvironmentVariable(
            "PATH", _family_studio_bin + os.pathsep + current_path)

    for _dependency in (
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Startup Importer.invokebutton", "bin",
                _compiled_wpf_assembly),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Startup Importer.invokebutton", "bin",
                _startup_importer_ui_assembly),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Startup Importer.invokebutton", "bin",
                "KLA.ModelStartupImporter.Core.dll"),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Startup Importer.invokebutton", "bin",
                "DocumentFormat.OpenXml.Framework.dll"),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Startup Importer.invokebutton", "bin",
                "DocumentFormat.OpenXml.dll"),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Family Studio.invokebutton", "bin",
                "KLCode.FamilyStudio.Core.dll"),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Family Studio.invokebutton", "bin",
                "Microsoft.Bcl.AsyncInterfaces.dll"),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Family Studio.invokebutton", "bin",
                "System.Buffers.dll"),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Family Studio.invokebutton", "bin",
                "System.Memory.dll"),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Family Studio.invokebutton", "bin",
                "System.Numerics.Vectors.dll"),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Family Studio.invokebutton", "bin",
                "System.Runtime.CompilerServices.Unsafe.dll"),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Family Studio.invokebutton", "bin",
                "System.Threading.Tasks.Extensions.dll"),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Family Studio.invokebutton", "bin",
                "System.ValueTuple.dll"),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Family Studio.invokebutton", "bin",
                "SQLitePCLRaw.core.dll"),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Family Studio.invokebutton", "bin",
                "SQLitePCLRaw.provider.e_sqlite3.dll"),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Family Studio.invokebutton", "bin",
                "Microsoft.Data.Sqlite.dll"),
            os.path.join(
                "KL&A Tools_dev.tab", "05 DevSandbox.panel",
                "Family Studio.invokebutton", "bin",
                "KLCode.FamilyStudio.Database.dll"),
    ):
        _load_dependency(_dependency)
