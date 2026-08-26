# KLCode Family & View Studio V1 Plan

## Summary
Yes, this is possible inside the KL&A pyRevit plugin, but it should not be built as IronPython. The clean V1 is a compiled C#/.NET product kept in this repo, surfaced through pyRevit metadata and also ship-ready as a native Revit `.addin`.

The chosen defaults are:
- Entry points: both pyRevit ribbon button and native `.addin`.
- Revit target: Revit 2024+.
- Indexer: separate desktop indexer executable, with Revit-hosted extraction where the Revit API is required.
- Architecture: shared testable library + Revit command shell + WPF UI + SQLite persistence.

## Proposed Structure
Add a new compiled solution under `src/KLCode.FamilyStudio/`:

```text
src/KLCode.FamilyStudio/
  KLCode.FamilyStudio.sln
  Directory.Build.props
  Revit/
    KLCode.FamilyStudio.Revit2024/
      Commands/
      Services/
      KLCode.FamilyStudio.Revit2024.addin
  App/
    KLCode.FamilyStudio.Indexer/
      Program.cs
      appsettings.json
  Library/
    KLCode.FamilyStudio.Core/
      Models/
      Indexing/
      Search/
      Configuration/
    KLCode.FamilyStudio.Database/
      Repositories/
      Migrations/
    KLCode.FamilyStudio.RevitServices/
      MetadataExtractor/
      ThumbnailService/
      FamilyLoadService/
    KLCode.FamilyStudio.UI/
      Views/
      ViewModels/
      Resources/
  Tests/
    KLCode.FamilyStudio.Core.Tests/
    KLCode.FamilyStudio.Database.Tests/
```

Add a pyRevit launcher bundle under the existing KL&A hierarchy, likely:

```text
KL&A Tools_dev.tab/
  02 KL&A Tools.panel/
    Family View Studio.pushbutton/
      bundle.yaml
      icon.png
      icon.dark.png
      SPEC.md
```

The pyRevit `bundle.yaml` points to the compiled DLL command. Native `.addin` manifests are generated/copied during build for users who run it outside pyRevit.

## SQLite Schema
Use a local SQLite file such as `%LOCALAPPDATA%\KLCode\FamilyStudio\family_studio.sqlite`.

Core tables:

```sql
families(
  id INTEGER PRIMARY KEY,
  content_kind TEXT NOT NULL DEFAULT 'family',
  family_name TEXT NOT NULL,
  category TEXT,
  file_path TEXT NOT NULL UNIQUE,
  file_hash TEXT,
  file_size INTEGER,
  modified_utc TEXT NOT NULL,
  revit_version TEXT,
  thumbnail_path TEXT,
  status TEXT DEFAULT 'Draft',
  discipline TEXT,
  company_version TEXT,
  indexed_utc TEXT NOT NULL,
  last_error TEXT,
  is_deleted INTEGER NOT NULL DEFAULT 0
);

family_types(
  id INTEGER PRIMARY KEY,
  family_id INTEGER NOT NULL,
  type_name TEXT NOT NULL,
  is_default INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(family_id) REFERENCES families(id) ON DELETE CASCADE,
  UNIQUE(family_id, type_name)
);

parameters(
  id INTEGER PRIMARY KEY,
  family_id INTEGER NOT NULL,
  type_id INTEGER,
  parameter_name TEXT NOT NULL,
  parameter_value TEXT,
  storage_type TEXT,
  is_type_parameter INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(family_id) REFERENCES families(id) ON DELETE CASCADE,
  FOREIGN KEY(type_id) REFERENCES family_types(id) ON DELETE CASCADE
);

tags(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

family_tags(
  family_id INTEGER NOT NULL,
  tag_id INTEGER NOT NULL,
  PRIMARY KEY(family_id, tag_id),
  FOREIGN KEY(family_id) REFERENCES families(id) ON DELETE CASCADE,
  FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

library_roots(
  id INTEGER PRIMARY KEY,
  root_path TEXT NOT NULL UNIQUE,
  enabled INTEGER NOT NULL DEFAULT 1,
  discipline TEXT,
  default_status TEXT,
  last_scan_utc TEXT
);

index_runs(
  id INTEGER PRIMARY KEY,
  started_utc TEXT NOT NULL,
  finished_utc TEXT,
  files_seen INTEGER NOT NULL DEFAULT 0,
  files_updated INTEGER NOT NULL DEFAULT 0,
  files_skipped INTEGER NOT NULL DEFAULT 0,
  files_failed INTEGER NOT NULL DEFAULT 0
);
```

Add SQLite FTS later in V1 once base persistence is stable:

```sql
family_search_fts(
  family_name,
  category,
  type_names,
  parameter_blob,
  tags,
  content='families'
);
```

## Core Interfaces And Classes
Core/testable interfaces:

```csharp
public interface ILibraryConfigurationProvider
{
    LibraryConfiguration Load();
}

public interface ILibraryScanner
{
    IReadOnlyList<LibraryFileCandidate> Scan(LibraryConfiguration config);
}

public interface IChangeDetector
{
    IndexDecision Decide(LibraryFileCandidate file, IndexedFamilyRecord existing);
}

public interface IMetadataExtractor
{
    FamilyMetadata Extract(string filePath, CancellationToken token);
}

public interface IThumbnailService
{
    ThumbnailResult EnsureThumbnail(FamilyMetadata metadata, CancellationToken token);
}

public interface IFamilyRepository
{
    FamilyRecord Upsert(FamilyMetadata metadata, ThumbnailResult thumbnail);
    IReadOnlyList<FamilySearchResult> Search(FamilySearchQuery query);
    FamilyDetail GetDetail(long familyId);
    void MarkMissingFiles(IReadOnlySet<string> seenPaths);
}

public interface IFamilyLoadService
{
    FamilyLoadResult LoadFamily(Document doc, FamilyRecord family, string typeName);
    PlacementResult PlaceInstance(UIDocument uidoc, FamilyRecord family, string typeName);
}
```

Primary classes:

```text
LibraryIndexer
FileSystemLibraryScanner
FileChangeDetector
RevitFamilyMetadataExtractor
RevitThumbnailService
SqliteFamilyRepository
SqliteSearchService
FamilyStudioCommand
FamilyStudioViewModel
FamilyDetailViewModel
RevitFamilyLoadService
KlaFamilyLoadOptions
```

Model for future `.rvt` detail-library support:

```csharp
public enum ContentKind
{
    Family,
    DraftingView
}

public sealed class ContentMetadata
{
    public ContentKind Kind { get; init; }
    public string SourcePath { get; init; }
    public string DisplayName { get; init; }
    public IReadOnlyList<ContentTypeMetadata> TypesOrViews { get; init; }
}
```

## Revit API Workflow
Indexer workflow:
- Scan configured folders for `.rfa`.
- Compare path, modified time, size, and optional hash against SQLite.
- For changed files, open the family file through a Revit API-capable process/session.
- Extract family category, symbols/type names, parameters, Revit version, and previewable metadata.
- Generate thumbnail once and cache it under `%LOCALAPPDATA%\KLCode\FamilyStudio\Thumbnails`.
- Upsert metadata in SQLite.
- Mark missing files as deleted instead of immediately dropping records.

Add-in workflow:
- User opens Family & View Studio from pyRevit or native add-in.
- WPF UI reads only from SQLite for browsing/search.
- Selecting a card loads family detail, types, parameters, tags, approval state, and thumbnail.
- `Load` uses Revit API family loading with `IFamilyLoadOptions`.
- `Place` loads the selected symbol if needed, activates it, regenerates the document, then starts placement.
- Existing/duplicate families are resolved through KL&A policy in `KlaFamilyLoadOptions`: V1 default is keep project values unless user explicitly chooses overwrite.

Future `.rvt` detail-library workflow:
- Store drafting views as `content_kind='drafting_view'`.
- Open source `.rvt` only during indexing or import.
- Copy selected drafting views using `ElementTransformUtils.CopyElements`.

## Incremental Indexing Strategy
- Fast scan: enumerate configured roots and collect path, size, modified UTC.
- Skip unchanged files when path, modified UTC, and size match the database.
- Hash only when timestamps look suspicious or a full validation mode is requested.
- Process changed files in batches with cancellation and per-file error logging.
- Never block the Revit UI for full-library indexing.
- Keep stale records visible but flagged until the next successful scan confirms deletion.
- Store thumbnails by stable content key, for example hash or sanitized family id plus modified timestamp.
- Write index-run summary counts for support diagnostics.

## V1 Roadmap
1. Foundation
   - Add the .NET solution, project references, build properties, and Revit 2024 compile target.
   - Add SQLite repository, schema creation, and basic migration runner.
   - Add config loading for library roots and local cache paths.

2. Indexer
   - Build scanner/change detector.
   - Add Revit-backed metadata extraction for `.rfa`.
   - Add thumbnail generation/cache.
   - Add command-line indexer with progress output and per-file error handling.

3. Search
   - Implement repository search by name, category, type, parameters, tags, status, discipline, and version.
   - Add FTS after the base query shape is stable.

4. Revit Add-in
   - Add `IExternalCommand`.
   - Add WPF browser UI with KLCode visual styling.
   - Add family detail panel, type selector, parameters table, and load/place actions.
   - Add `IFamilyLoadOptions` duplicate handling.

5. pyRevit Integration
   - Add pyRevit pushbutton bundle pointing to the compiled command DLL.
   - Add native `.addin` manifest output for direct Revit add-in deployment.
   - Add `SPEC.md` explaining behavior, inputs, cache location, and validation boundaries.

6. Validation
   - Unit-test indexing decisions, search query behavior, SQLite repository, and config handling.
   - Smoke-test the indexer against a small sample family library.
   - Live-test in Revit 2024: open UI, search, load a family, activate a type, place an instance, and handle existing-family conflicts.
   - Keep live Revit acceptance separate from source-level test results.

## Assumptions
- First compile target is Revit 2024, with later conditional builds for newer Revit API/runtime differences.
- Company metadata can initially come from folder rules, filename conventions, a sidecar JSON/CSV file, or manual DB tags; no live source of truth is assumed yet.
- V1 indexes `.rfa` only, while the data model leaves room for `.rvt` drafting-view libraries.
- The current pyRevit extension remains the delivery shell; the actual Studio code is compiled C# so WPF, SQLite, and Revit API behavior are maintainable.
