# Family Studio dependency record

Pinned dependencies for the source-level V1:

| Package | Version | Purpose | License/provenance |
| --- | ---: | --- | --- |
| `Microsoft.Data.Sqlite` | 8.0.30 | Parameterized SQLite persistence | Microsoft package on NuGet; MIT |
| `System.Text.Json` | 8.0.5 | JSON configuration on the `netstandard2.0` core | Microsoft package on NuGet; MIT |
| `MSTest` | 4.3.3 | Unit/integration test framework | Microsoft Test Platform package on NuGet; MIT |
| `coverlet.collector` | 10.0.1 | Test coverage collection | coverlet project package on NuGet; MIT |

Versions are exact in project files and resolved transitively in NuGet lock files.
No package lifecycle scripts are invoked by the projects. The Revit adapter uses
Autodesk-provided assemblies from the installed Revit directory and does not copy
or redistribute them.
