# KLCode Family Studio V1

## Purpose

Family Studio provides a local, searchable SQLite catalog of `.rfa` family
files and a compiled Revit browser shell for loading or placing an indexed
family. V1 does not index `.rvt` content.

## Entry points

- pyRevit loads this `.invokebutton` through
  `KLCode.FamilyStudio.Revit.dll` and
  `KLCode.FamilyStudio.Revit.Commands.FamilyStudioCommand`.
- The native `KLCode.FamilyStudio.Revit2024.addin` manifest supports a direct
  Revit deployment at the documented ProgramData path.
- `KLCode.FamilyStudio.Indexer --config <file>` scans configured roots and
  updates the local database.

The Revit project exposes an opt-in `PackagePyRevit` build target that copies the
compiled command and runtime dependencies into this bundle's `bin` directory
and verifies the host-specific command assembly exists after the copy.
It uses `KLCode.FamilyStudio.Revit_2024.dll` for Revit 2024 and the unsuffixed
assembly for Revit 2025+. No binaries are committed by this source slice, and
the packaging target has not been run on this macOS workspace. The shared panel
layout exposes Family Studio as a development command by explicit owner
direction. The visible button cannot launch until verified Windows artifacts
are copied into this bundle's `bin` directory.

## Indexing behavior

The CLI validates a JSON configuration, scans enabled roots recursively,
includes only `.rfa` files, orders paths deterministically, and compares path,
size, and modified UTC with the stored record. Unchanged files are skipped.
Changed files are upserted and missing files are soft-deleted only after a scan
with no root errors. A failure on one file is recorded in the final summary and
does not stop the remaining files.

Desktop indexing is explicitly filesystem-only: it stores the file name, path,
size, timestamp, and a Draft status. It does not extract Revit category, type,
parameter, version, or thumbnail data. The injected Revit metadata adapter must
run later from a valid Revit API context. Symbolic-link/reparse-point roots,
directories, and family files fail closed, and overlapping configured roots are
deduplicated case-insensitively. Missing-file reconciliation is limited to the
enabled roots that completed the current scan; records from omitted or disabled
roots are not changed.

The Revit-hosted **Refresh Library** action accepts the same external JSON
configuration, verifies it points at the database currently open in Family
Studio, and performs the full metadata/preview refresh. It opens every
discovered family file through the Revit API, records category/types/type
parameter values, and renders a PNG preview from the first available type into
the configured thumbnail cache.
The refresh service accepts a cancellation token. If preview rendering fails
for a family with an existing preview, that preview is retained and the issue
is reported without stopping the rest of the run. A family with no prior
preview is still indexed without one and appears in the refresh issues.

## Search and Revit behavior

Search is parameterized and bounded to 1–200 results. It matches family name,
category, type names, parameters, and tags, with optional exact category,
status, and discipline filters. Deleted records are hidden.

The current WPF shell supports bounded text search, selected-family preview and
detail, type selection with type-parameter values, Favorites, Recent, Copy
Path, Open Folder, Load, and Load & Place.
Favorites and recent Load/Place records are local SQLite data only; they are
not shared approval, status, or tag curation.
Duplicate-family handling keeps project parameter values. A load is accepted
only when `LoadFamily` returns a non-null family and its transaction commits;
there is no filename/name fallback that could select unrelated project content.
The native command also rejects Family Editor documents. Load/Place source is
not accepted as live behavior until it passes the Windows/Revit gates below.

## Local data

The Revit command reads:

`%APPDATA%\KLCode\FamilyStudio\family_studio.sqlite`

For DevSandbox, the pyRevit startup script may select a separate user-local
database name. The repository never owns the active database. If the selected
database does not yet exist, Family Studio creates and migrates an empty local
database; **Refresh Library** then populates it from the operator-selected
configuration.

The CLI uses the explicit `databasePath` and `thumbnailDirectory` from its JSON
configuration. Paths may be absolute or relative to the configuration file.

## Validation boundary

The macOS gate covers Core, SQLite, CLI build, deterministic scanning/change
decisions, orchestration failure containment, migrations, upsert, soft delete,
and bounded search. It cannot compile or run WPF/Revit source without installed
Autodesk references.

Before promotion, build each Revit target on Windows with the matching installed
API, package the DLL and dependencies into this bundle's `bin` directory, and
verify the visible development button resolves the command. Then live-test UI
open/search, duplicate handling, Load, activation, placement, cancellation, and
transaction rollback in Revit 2024 and each later supported version. The
source-level tests require both development commands to be present in the
shared panel layout with valid compiled-command metadata.
