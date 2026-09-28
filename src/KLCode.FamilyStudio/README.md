# KLCode Family Studio

The macOS-verifiable solution contains the host-independent Core, SQLite
repository, desktop indexer, and tests:

```bash
dotnet restore KLCode.FamilyStudio.sln --use-lock-file
dotnet build KLCode.FamilyStudio.sln --no-restore
dotnet test KLCode.FamilyStudio.sln --no-build --no-restore --collect:"XPlat Code Coverage"
```

Run the indexer with a copy of `appsettings.example.json`:

```bash
dotnet run --project App/KLCode.FamilyStudio.Indexer -- --config /absolute/path/config.json
```

The CLI is filesystem-only and never opens Revit files through the Revit API.
It rejects symbolic-link/reparse-point content, deduplicates overlapping roots,
and limits missing-file reconciliation to roots successfully scanned in the
current run.
See the Revit project README and the invokebutton `SPEC.md` for Windows build,
deployment, and live acceptance gates.
