# KLCode Family & View Studio V1 Plan

## Execution amendment — 2026-08-26

Repository and host evidence narrowed the approved source-level V1:

- The owned launcher remains in `05 DevSandbox.panel` and is an
  `.invokebutton`; compiled `assembly` / `command_class` metadata is not valid
  for a scripted `.pushbutton`.
- The desktop CLI scans `.rfa` files, makes deterministic change decisions,
  writes filesystem-only records to SQLite, and reports per-file failures. It
  does not call the Revit API or claim category/type/parameter extraction.
- Revit metadata extraction, WPF browsing, and Load/Place are host adapters in
  the separately gated Revit project. Their source is present, but compilation
  and live behavior require Windows, installed Revit API assemblies, and Revit.
- `.rvt` drafting views, FTS, production ribbon placement, deployment, and
  generated binaries remain deferred. The V1 schema accepts only
  `content_kind='family'`.
- The shared DevSandbox `layout` now exposes the source-level Family Studio
  bundle as an explicitly authorized development command. It remains
  non-runnable until Windows packaging supplies the matching Revit DLL and
  dependencies; live Revit verification is still required before promotion.
- The macOS solution contains Core, Database, Indexer, and their tests. The
  guarded Revit project is deliberately outside that solution so a successful
  macOS build cannot be mistaken for a Revit host validation.

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

## Wave 2 — Library workflow and Simpson research — 2026-08-30

Family Studio remains a DevSandbox tool. Wave 2 adds a Revit-hosted full refresh
path and a richer local browsing workflow; it does not add shared curation,
production deployment, or a Simpson downloader.

### Revit-backed refresh and previews

- The existing JSON library configuration remains the operator-owned source of
  truth. The Revit refresh command requires it to point at the same local
  Family Studio database that is currently open.
- `Refresh Library` is the explicit full Revit metadata/preview pass: it scans
  every discovered `.rfa`, extracts Revit metadata, and renders a PNG preview
  from the first available family type. Previews are cached in the configured
  thumbnail directory using a stable source-path hash. The separate desktop
  indexer remains the lightweight changed-files-only path.
- The desktop indexer remains filesystem-only. Only the explicit Revit refresh
  opens family documents and creates previews.
- Refresh accepts cancellation through its service contract. A preview failure
  retains an existing preview when one exists, still updates available
  metadata, and is shown in the refresh summary. Families with no prior preview
  are indexed without one as a per-file issue, without stopping the remaining
  scan.

### Browser workflow

- Search results now expose a selected-family detail panel with preview,
  category, status, discipline, path, types, tags, and parameters. Selecting a
  family type shows the values of that type's Revit type parameters; instance
  parameter definitions remain visibly separate.
- Favorites and recent Load/Place actions are stored only in the local SQLite
  database. The UI provides Favorites, Recent, favorite toggle, Copy Path, and
  Open Folder actions while preserving Load and Load & Place.
- SQLite schema version 2 owns `family_favorites` and `family_recent_use`.
  These tables are user-local and are never a company approval/tagging system.

### Simpson Drawing Finder research appendix

The Simpson track is research-only. Official pages confirm that Drawing Finder
pulls current content from Simpson's website and provide maintained Revit
plugin releases, but they do not publish a supported catalog API endpoint.
Research may inspect user-observed browser requests from a manual search or an
officially obtained, user-supplied plugin package. Record endpoint host,
request/response shape, authentication, result metadata, and license/terms
evidence. Do not bulk crawl, download RFAs, bypass controls, capture
credentials, redistribute content, or add Simpson results to Family Studio.

### Validation gates

Source tests cover SQLite migration/detail/favorites/recent behavior and
thumbnail-retention logic. Live validation requires a non-production pilot
library and configuration on Revit 2024 and 2025: refresh, preview creation,
preview failure retention, detail display, favorites/recent, path actions,
Load, Load & Place, and placement cancel. Pilot libraries, databases,
thumbnails, configurations, and generated packages remain uncommitted.

## Wave 3 — Catalog browser and library quality — 2026-08-31

### Deferred preview-export refinement

- The Revit-native 2D preview crop/export path is usable for the DevSandbox
  pilot but needs one additional quality pass before production promotion.
  That pass will establish a repeatable 400 x 300 framing check across a
  broader 2D family set and tune the native Revit crop calibration without
  raster resizing after export.
- 3D previews continue to respect the source family view's camera framing.
  Do not spend further pilot time on preview composition unless a new test
  family demonstrates a functional failure.

### Catalog workflow

- Keep the operator-owned JSON configuration as the source of truth for one
  or more enabled roots. Surface the configured roots in the browser and make
  root selection a searchable filter; do not invent shared root administration
  or put operator paths in Git.
- Add faceted filters for category, type, parameter name, and root, alongside
  full-text matching over family name, category, type names, parameter names,
  parameter values, and existing local tags.
- Detect and clearly label two non-destructive review states: exact duplicate
  bytes (same SHA-256 in multiple paths) and same-name variants (same family
  name with different bytes). Surface source path, modified time, Revit version,
  and sibling count so an operator can decide which is authoritative. This
  wave never deletes, renames, overwrites, or auto-selects a version.
- Evolve the WPF window into a catalog browser with faceted controls, result
  cards/list rows, selected-family/type detail, preview, parameters, local
  favorite/recent actions, path actions, and the existing Load/Load & Place
  behavior.

### Validation gates

- Unit-test filter composition, root scoping, hash duplicate classification,
  same-name variant classification, and database migration/query behavior.
- Live-test a disposable multi-root library in Revit 2024 and 2025: root
  filters, category/type/parameter filters, duplicate labels, variant labels,
  detail/type preview switching, favorites/recent, Load, Load & Place, and
  canceled placement.

## Next after Wave 3 validation — Deferred catalog refinement

Start this backlog only after the multi-root and duplicate/version live tests
have passed. It is intentionally separate from the current DevSandbox
acceptance gate.

1. **Catalog-browser polish**
   - Add a thumbnail card/grid view alongside the compact list, sortable
     results, clearer empty states, keyboard navigation, and more legible
     duplicate/version indicators.

2. **Root configuration experience**
   - Keep the external JSON as the source of truth, but provide an in-app
     configuration view/editor with pre-refresh root validation. It must not
     introduce shared root administration or store operator paths in Git.

3. **Refresh reliability and feedback**
   - Add per-root progress, changed/skipped counts, and an actionable issue
     report that can be copied or opened without obscuring successful results.

4. **Preview-export quality round**
   - Return to the deferred 2D/3D framing, sharpness, crop/extents, and
     per-type visual-confirmation work described above.

5. **Larger-library performance evidence**
   - Measure indexing and search behavior against a representative
     multi-folder library, then add caching, pagination, or indexing safeguards
     only where measurements demonstrate a need.
