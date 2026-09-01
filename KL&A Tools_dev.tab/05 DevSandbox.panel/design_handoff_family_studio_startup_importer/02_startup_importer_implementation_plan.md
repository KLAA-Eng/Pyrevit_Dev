# Implementation Plan: Startup Importer Green Windows And Supported Workflow

- Repository / evidence commit: `KLCode.pyRevit`, `e856ca3`; design source: `Startup Importer.dc.html` and this handoff's `README.md`.
- Owner / priority / scope: KL&A engineering, next after the shared design-system foundation. Command remains `KL&A Tools_dev.tab/05 DevSandbox.panel/Startup Importer.invokebutton`.
- Status: `NOT READY` for feature delivery until the design-system prerequisite passes and an owner supplies the controlled seed/catalog/live-Revit fixtures required for mutation validation.
- Outcome: replace the two native file pickers and TaskDialog review/alerts with SI-1, SI-2, SI-3, and SI-6 green WPF screens around the existing deterministic reader, review, and create-only importer.
- Non-goals: SI-4 placement/split implementation, SI-5 Update Startup Links implementation, Extensible Storage/created-element tracking, PDF intake, overwriting/rebuilding existing targets, or production promotion.

## Current Architecture And Constraints

- `StartupImportCommand.cs` owns the native `OpenFileDialog` sequence, calls Core readers/settings, and displays a `TaskDialog`. It is the command adapter to replace.
- `KLA.ModelStartupImporter.Core` is host-independent and currently owns immutable intake data, SHA-256 snapshot parsing, settings/catalog validation, `ImportPlanBuilder`, and `StartupImportReview` classification.
- `RevitStartupImportService` preflights all sources, skips existing targets, and imports actionable matches inside one `TransactionGroup`, rolling back on failure. It currently opens seed documents synchronously and has no progress callback.
- The Revit project multi-targets `net48` and `net8.0-windows` with `UseWPF=true`; no `KLA.ModelStartupImporter.UI` project exists yet. `KLA.ModelStartupImporter.Packaging.proj` is the verified packaging surface.
- Existing SPEC says unknown/duplicate selected IDs block import and link/update/rebuild behavior is deferred. The handoff's SI-4/SI-5 therefore remain designed-but-unimplemented concepts.

## Acceptance Criteria

1. SI-1 selects, validates, and displays a checklist/settings pair before model mutation. Cancel at any point changes nothing.
2. SI-2 displays the actual review classification, catalog version/hash, existing/unchecked states, per-item selection, supported placement target facts, requirements, and an exact import count; SI-3 blocks import for any selected unknown/duplicate ID.
3. Import remains create-only, skips existing targets, validates sources before writes, runs all selected actionable matches in one transaction group, and rolls back the whole group on failure.
4. Success and expected-input failures use localized green alert windows. No newly introduced dialog uses native white chrome or hard-coded user-facing strings.
5. SI-4 and SI-5 have no implementation path in this plan; their controls must not imply stored source links, rebuild semantics, schedule/note splitting, or placement behavior that does not exist.

| Step | Exact files/surfaces | Behavior guarantee | Test-first evidence | Verification | Rollback/containment |
| --- | --- | --- | --- | --- | --- |
| 1. Create UI project and thin command orchestration | **new** `src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/KLA.ModelStartupImporter.UI.csproj`, `Views/`, `ViewModels/`, `Resources/`; update `KLA.ModelStartupImporter.Revit.csproj`; replace `StartupImportCommand.cs` flow | Command creates host adapters and opens the picker/review workflow; view models reference Core models, never Autodesk types; Revit mutation remains in `RevitStartupImportService`. | Failing view-model tests cover initial/cancel/valid/invalid transitions and prevent import before a review has passed. | Build net48/net8.0-windows on Windows, then open SI-1 in Revit with no source selected. | Preserve the current command until green dialogs can complete the existing happy-path preflight; cancellation returns `Result.Cancelled`. |
| 2. Implement SI-1 picker and validation projection | **new** `Views/StartupSourcePickerWindow.xaml`, `ViewModels/StartupSourcePickerViewModel.cs`, localized resources; `StartupDocumentReader.cs`, `JsonStartupSettingsProvider.cs` only if a non-mutating validation/query facade is required | The picker presents selected paths, deterministic reader/hash results, resolved seed path, catalog/version, and destination project name without opening a transaction or changing a model. | Tests fail for stale/unreadable files, invalid JSON/catalog, zero-selected documents, Browse cancellation, and a valid SHA/version projection. | Exercise DOCX and XLSX valid/invalid fixtures; inspect no document write happens before Review. | Do not cache or alter operator files; clear invalid selection state and show a localized error alert. |
| 3. Implement SI-2/SI-3 review state | **new** `Views/StartupImportReviewWindow.xaml`, `Views/BlockingIssuesWindow.xaml`, `ViewModels/StartupImportReviewViewModel.cs`; `StartupImportSettings.cs` / `Models.cs` only for an approved immutable presentation projection | Rows exactly reflect `Matches`, `ExistingMatches`, `SkippedItems`, `UnknownItems`, and `DuplicateItems`; selection is limited to actionable matches; blocking status disables import irrespective of selection state. | Extend `ImportPlanBuilderTests.cs` and add view-model tests for all classification states, select-all/none, count updates, requirement display, and duplicate/unknown blocking. | Compare SI-2 and SI-3 at fixed dimensions; confirm existing entries cannot become actionable. | Keep the original immutable `ImportPlan`; closing/cancelling the review causes no import and no settings/catalog writes. |
| 4. Bind confirmed review to the existing transaction import | `StartupImportCommand.cs`; `RevitStartupImportService.cs`; **new** UI-to-command result DTO only if Core cannot express selected actionable IDs without mutation | Revit revalidates review inputs/sources immediately before starting the group, imports only the user-selected actionable matches, skips existing targets, and rolls back on any post-start failure. | Failing Core tests for selected-match filtering and no-actionable state; Revit service tests/fakes where practical for revalidation and rollback invocation. | Live disposable projects with details, general notes, supported schedules, already-existing targets, forced failure, and placement cancellation where applicable. | The transaction group is rolled back on any exception; no partial result is reported as success. |
| 5. Replace all expected alerts | **new** `Views/KlaAlertWindow.xaml`, success/error view models/resources; `StartupImportCommand.cs` | Parse/settings errors and success summaries use the KL&A alert layout, reflect actual created/skipped/count/version results, and offer `Open First View` only when an actual created view ID has an approved host result. | Tests fail for missing alert fields and absent first-view action; expected input failures stay classified by `IsExpectedInputFailure`. | Manual valid/invalid/forced-error checks in Revit; verify no feature-path `TaskDialog` remains. | Fall back to the command's returned message for unexpected fatal failures; never report `Import complete` before `TransactionGroup.Assimilate`. |
| 6. Explicitly park SI-4 and SI-5 | `Startup Importer.invokebutton/PLAN.md`; `SPEC.md`; **new** decision records only, not `LinkMetadataStore`/placement implementation | Placement/split and links/rebuild have owner-defined identity, versioning, target, extents, schedule/note, idempotency, and failure contracts before any code is started. | A specification-review gate, not an implementation test. | Owner approval plus separate live-Revit proof plan. | No Extensible Storage schemas, source links, rebuild controls, or placement promises are committed in this delivery. |

## Material Decisions, Risks, And Dependencies

- Owner must provide a controlled seed RVT, versioned catalog, DOCX/XLSX fixtures, and disposable Revit 2024/2025+ projects before actual-import live validation. The plan must not invent or commit them.
- Owner must decide whether review-time per-item selection modifies an immutable derived plan or creates a separately validated selection request. The smallest safe route is a UI DTO of actionable item IDs, revalidated by the Revit service immediately before import.
- The handoff's live preview is a seed-view preview placeholder until the owner defines an approved, safe preview-generation path. It cannot silently open/render arbitrary seed documents outside the current preflight.
- SI-4/SI-5 are blocked by the existing SPEC: no Extensible Storage identity/version, element tracking, link persistence, rebuild semantics, multi-column conversion/splitting, or physical sheet placement contract exists.
- Dependencies: design-system/localization foundation; Windows Revit API assemblies; package restore; known fixtures. Current local Core test command is repository-supported but not run here after the Family Studio no-restore gate showed missing assets files; Windows gates remain unavailable in this environment.

## Implementation Checkpoints

1. Shared theme gate and empty compiled WPF launch.
2. SI-1 validated picker and read-only review construction.
3. SI-2/SI-3 classifications and selectable actionable items.
4. Existing create-only importer integration and SI-6 alerts under disposable-project tests.
5. Separate owner-approved specifications for SI-4 and SI-5, if they are still wanted.

Before handoff, run the narrow Core tests, source formatting/compile checks available on the execution host, `git diff --check`, full diff review, Windows packaging via `KLA.ModelStartupImporter.Packaging.proj`, and live Revit 2024/2025+ acceptance. Keep the command in DevSandbox until every applicable gate is `PASS` or an owner records a narrow exception.
