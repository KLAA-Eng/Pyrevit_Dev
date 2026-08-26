# KL&A Model Startup Importer

This source-level DevSandbox MVP contains deterministic, host-independent parsing and import-plan logic plus a thin Revit preflight command. It deliberately does not modify a Revit model yet: the catalog file contract, seed RVT path, Extensible Storage schema, and update/rebuild behavior require owner decisions and Windows/Revit validation.

## Local host-independent gates

```shell
dotnet restore KLA.ModelStartupImporter.Tests/KLA.ModelStartupImporter.Tests.csproj
dotnet test KLA.ModelStartupImporter.Tests/KLA.ModelStartupImporter.Tests.csproj --no-restore
```

## Windows/Revit builds

Set `RevitApiPath` to a matching installed Revit folder. The build fails with an actionable error when `RevitAPI.dll` or `RevitAPIUI.dll` is absent.

```powershell
dotnet build KLA.ModelStartupImporter.Revit/KLA.ModelStartupImporter.Revit.csproj -f net48 -p:RevitApiPath="C:\Program Files\Autodesk\Revit 2024"
dotnet build KLA.ModelStartupImporter.Revit/KLA.ModelStartupImporter.Revit.csproj -f net8.0-windows -p:RevitApiPath="C:\Program Files\Autodesk\Revit 2025"
```

The `net48` build emits `KLA.ModelStartupImporter.Revit_2024.dll`; the `net8.0-windows` build emits the unsuffixed fallback `KLA.ModelStartupImporter.Revit.dll`. Both deploy to the owned `.invokebutton/bin/` module directory, allowing pyRevit to select the Revit 2024-specific assembly and use the .NET 8 fallback for Revit 2025+.

To build and verify both host assemblies plus their runtime dependencies in one Windows packaging gate, run:

```powershell
dotnet msbuild KLA.ModelStartupImporter.Packaging.proj -restore -t:Package `
  -p:Revit2024ApiPath="C:\Program Files\Autodesk\Revit 2024" `
  -p:Revit2025ApiPath="C:\Program Files\Autodesk\Revit 2025"
```

The packaging target consumes only the installed Autodesk API paths supplied by the caller. It does not download or copy `RevitAPI.dll` or `RevitAPIUI.dll` into the bundle.

The shared DevSandbox layout exposes this source-only command by explicit owner
direction. Until the Windows packaging gate places the matching assemblies and
dependencies in the bundle's `bin` directory, the visible button cannot launch.
Live pyRevit/Revit invocation checks for both host generations remain required
before promotion beyond DevSandbox.
