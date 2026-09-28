# Revit host adapter

This project is intentionally excluded from the macOS-verifiable solution build.
It requires Windows, WPF, the installed Autodesk Revit API assemblies, and a live
Revit validation pass.

Build Revit 2024 (`net48`):

```powershell
dotnet build -p:RevitVersion=2024 -p:RevitApiDir="C:\Program Files\Autodesk\Revit 2024"
```

Add `-p:PackagePyRevit=true` to copy the command and runtime dependencies into
the owned invokebutton's `bin` directory and fail if the host-specific command
assembly is absent after the copy. The packaging target writes
`KLCode.FamilyStudio.Revit_2024.dll` for the .NET Framework host and the
unsuffixed `KLCode.FamilyStudio.Revit.dll` for Revit 2025+; the bundle metadata
uses the unsuffixed logical assembly name so pyRevit can apply its host-version
resolution convention. Run the packaging build separately for each supported
host and inspect the bundle before distribution. The shared panel layout
exposes the source-level command by explicit owner direction. Until these
verified binary artifacts exist in the bundle's `bin` directory, the visible
button cannot launch.

Build Revit 2025 or 2026 (`net8.0-windows`) by changing `RevitVersion` and the
installed API directory. With no `RevitApiDir`, the project fails with an explicit
unavailable-reference error instead of compiling against substitutes.

`RevitFamilyMetadataExtractor` must be called from a valid Revit API context; it
is not used by the desktop indexer. The `.addin` manifest assumes a deployment
copy under the stated ProgramData path. Deployment and live Load/Place checks are
deferred and have not been performed by the macOS source gate.
