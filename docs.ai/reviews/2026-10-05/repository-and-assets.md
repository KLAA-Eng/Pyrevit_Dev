# Repository, Startup Importer, preflight checks, and assets

Review date: 2026-10-05. Baseline: `1562e96a5f6e23b7368c80e317868a0c059dc165`, `0.0.11-dev`.
This is a source review with targeted automated verification. No model-changing command was run and no production source or asset was edited. See [validation](validation-and-acceptance.md) for execution evidence and limitations.

## Findings

### REP-01 — P1 — Startup Importer passes seed-document IDs into destination-document operations

**Confidence:** confirmed source defect; exact Revit failure or collision depends on the two documents.

[RevitStartupImportService.cs](../../../src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.Revit/RevitStartupImportService.cs#L198), line 198, creates a destination drafting view with `sourceView.GetTypeId()`. Line 286 similarly adds a destination schedule field using `sourceField.ParameterId`. Positive element IDs identify elements in their owning document; a seed drafting type or project/shared parameter cannot be assumed to have the same ID in an independently created destination. The operation can fail, or resolve an unintended destination object when numbers happen to collide. Built-in negative parameter identifiers are a separate case and should remain supported.

The [Autodesk ViewDrafting.Create reference](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/93dbfef8-b014-3912-124d-812c10b8ebdb.htm) creates the type from the destination document and requires a valid drafting-view family type. The live host was identified as Revit 2024; this is a cross-document identity issue, not a claim that a 2026-only API is available in 2024.

**Recommendation:** resolve a drafting `ViewFamilyType` in the destination. Map non-built-in parameters using an explicit stable identity such as a shared-parameter GUID and validate category binding; reject unresolved mappings before starting writes. Do not substitute a matching integer or a parameter name alone.

**Acceptance:** independently created seed and target RVTs with different IDs; built-in, shared, project, missing, and conflicting parameter cases. A missing mapping must produce an actionable preflight issue and zero committed content.

### REP-02 — P1 — Startup Importer reports success without checking transaction outcomes

**Confidence:** confirmed unchecked return values; rollback scenario requires Revit acceptance.

[RevitStartupImportService.cs](../../../src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.Revit/RevitStartupImportService.cs#L131), lines 131–150, ignores `Transaction.Start`, `Commit`, and `TransactionGroup.Assimilate` statuses. The outer catch only catches exceptions. [StartupImportCommand.cs](../../../src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.Revit/StartupImportCommand.cs#L71), lines 71–82, then reports the selection count as imported and returns `Succeeded`. A transaction that returns `RolledBack` without throwing can therefore be counted as success and leave the intended all-or-nothing operation incomplete.

Autodesk explicitly requires callers to check [Transaction.Commit's return status](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/32714010-7138-f64f-8fde-a310354448e3.htm), including rollback and pending outcomes.

**Recommendation:** require `Started` and `Committed`, handle pending failure processing deliberately, roll back the group on any unsuccessful item, and derive the final report from confirmed outcomes.

**Acceptance:** inject a failure that returns rolled back, rather than throwing; verify no partial group is accepted and no success count is shown. Repeat on each claimed Revit host generation.

### REP-03 — P1 — Schedule import silently omits schedule semantics

**Confidence:** confirmed source omission; visible output varies with the source schedule.

[ScheduleDefinitionTranslator](../../../src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.Revit/RevitStartupImportService.cs#L242), lines 242–343, copies regular fields, headings, widths, sort groups and string filters. It neither copies nor rejects field `IsHidden`, field display/totalling settings, definition `IsItemized`, and other unsupported formatting/definition features. A hidden filter field becomes visible, and a grouped quantity schedule can be recreated with different row/total behavior while the command reports completion. These are data-presentation semantics, not merely color differences. The adjacent [SPEC](../../../KL%26A%20Tools_dev.tab/05%20DevSandbox.panel/Prototype.pulldown/Startup%20Importer.invokebutton/SPEC.md#L92) says unsupported schedule features fail closed before writes.

The [Autodesk schedule guide](https://help.autodesk.com/cloudhelp/2024/PTB/Revit-API/files/Revit_API_Developers_Guide/Basic_Interaction_with_Revit_Elements/Views/View_Types/TableView/ViewSchedule/Revit_API_Revit_API_Developers_Guide_Basic_Interaction_with_Revit_Elements_Views_View_Types_TableView_ViewSchedule_Working_with_ViewSchedule_html.html) explains hidden fields and itemization behavior.

**Recommendation:** define a precise supported schedule subset and validate all relevant properties before writes. Copy each supported property explicitly; reject everything outside that subset with the schedule and property named. Prefer a faithful supported API copy path if it satisfies the product contract.

**Acceptance:** compare source and destination for hidden filter fields, itemized/grouped rows, totals, display types, numeric filters, calculated fields, and unsupported schedules. An unsupported case must leave no destination schedule.

### REP-04 — P2 — Startup Importer's resource requirements are displayed but not validated

**Confidence:** confirmed source/contract mismatch.

[Models.cs](../../../src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.Core/Models.cs#L140), lines 140–154, stores required text types and line styles. [StartupImportReviewViewModel.cs](../../../src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/ViewModels/StartupImportReviewViewModel.cs#L136) displays them. The host's [ValidateSourceViews](../../../src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.Revit/RevitStartupImportService.cs#L167), lines 167–191, only checks source view existence and content category; it does not validate those required resources or schedule support. Unsupported schedule cases are first rejected inside the transaction group.

The review UI even says “Catalog requirements declared · checked again before import” in its [strings dictionary](../../../src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/Resources/Strings/ResourceDictionary.en_us.xaml#L69), so the display promises validation that the service does not perform.

**Recommendation:** implement one preflight result containing missing resources, unsupported schedule features, and unresolved destination mappings. Present blocking rows before enabling Import. If requirements are informational only, explicitly change the contract and label them accordingly.

**Acceptance:** missing text/line resources and unsupported schedule properties appear before any transaction starts; the operator can identify the affected item and remedy.

### REP-05 — P2 — A dependency-load error raises a second exception and stops startup preloading

**Confidence:** reproduced with the unmodified function and simulated assembly boundary.

[startup.py](../../../startup.py#L27), lines 27–36, catches an assembly-loading failure but formats undefined `relative_path` instead of `assembly_path`. An isolated execution of that function with `Assembly.Load` raising returned `NameError: name 'relative_path' is not defined`. This masks the original failure and stops the remaining dependency loop, so one invalid or incompatible dependency can prevent subsequent compiled dependencies from being prepared.

**Recommendation:** report the actual path and original error; decide explicitly which dependency failures block the relevant tool and which allow other independent preload work to continue.

**Acceptance:** simulate missing and invalid DLLs; preserve the original diagnostic and prove that no unrelated dependency is accidentally skipped. Do not test by damaging installed DLLs.

### REP-06 — P2 — The consolidated release check does not exercise the compiled test projects

**Confidence:** confirmed and observed.

[scripts/release_check.py](../../../scripts/release_check.py#L210), lines 210–233, runs Python discovery, metadata, whitespace and identity checks, but no .NET tests. The Python suite passed with 195 tests run (194 passed, one skipped), while the independently run current WPF source tests had 12 passes and one failure at [DesignSystemResourceContractTests.cs](../../../src/KLCode.Wpf/Tests/KLCode.Wpf.Source.Tests/DesignSystemResourceContractTests.cs#L86). That test expects the legacy dictionary to merge the canonical palette; the actual dictionary and design document describe duplicated values. The result is a test/implementation contract conflict, not proof that the GUI fails to load.

**Recommendation:** decide the intended palette boundary, align the test and implementation to that decision, and make compiled test projects explicit conditional release gates for their affected tool families. Run host-specific packaging gates separately from unit tests.

**Acceptance:** the five .NET test projects are discoverable in the release evidence; a deliberate failure in any required compiled suite makes the corresponding release gate fail. Avoid deleting the failing assertion merely to make the report green.

### REP-07 — P2 — Preflight discovery can prompt and exit before a check is selected

**Confidence:** confirmed call-path analysis; not invoked live because discovery itself can show a blocking dialog.

[audit_all_check.py](../../../checks/audit_all_check.py#L35), lines 35–44, reads configuration at module import and calls `alert(..., exitscript=True)` on any exception. The installed pyRevit 6.5.3 `preflight.get_all_preflight_checks()` imports every extension check with `imp.load_source` before presenting the available cases (installed module lines 83–98). A fresh/unconfigured user can encounter the Audit All configuration message and exit while merely discovering checks, affecting unrelated preflight tools.

**Recommendation:** move configuration validation into the selected check's execution/setup and return an explicit configuration-required result. Importing a check should only define it.

**Acceptance:** list available checks with no Audit All config, then run another check successfully; running Audit All itself provides actionable setup instructions.

### REP-08 — P2 — Wall-naming check cancellation uses an unavailable IronPython 2 exception

**Confidence:** confirmed source/target-language mismatch.

[walltypes_naming_convention_check.py](../../../checks/walltypes_naming_convention_check.py#L29), lines 29–33, raises `FileNotFoundError` when the JSON picker is cancelled. The active pyRevit engine is IronPython 2.7.12, where that Python 3 built-in is absent. Cancelling therefore raises `NameError` instead of being handled as cancellation.

**Recommendation:** return a cancellation outcome before accessing the JSON, using the supported engine's control-flow conventions. A cancelled picker is not a missing-file error.

**Acceptance:** cancel both the button and window-close routes in IronPython 2.7; no traceback or partial report should suggest a completed audit.

### REP-09 — P2 — Several preflight checks ignore the supplied document

**Confidence:** confirmed source behavior; impact depends on host discovery and invocation lifecycle.

[grids_check.py](../../../checks/grids_check.py#L15) and [levels_check.py](../../../checks/levels_check.py#L15) capture `DOCS.doc` at import and their report functions call collectors without passing the `doc` supplied by `startTest`. [schedules_not_on_sheet_check.py](../../../checks/schedules_not_on_sheet_check.py#L28) directly collects `revit.doc`. CAD audit similarly caches document and active view. If a check is reused for another document or the active document changes after discovery, results can come from the wrong model.

**Recommendation:** thread the explicit `doc` and selected active view through every collector and report helper; do not bind host state in default arguments.

**Acceptance:** discover in document A, run against B, and verify every count/name belongs to B. Mark this as a lifecycle defect, not a claim that today's single-document launch always selects the wrong model.

### REP-10 — P3 — Startup Importer README contradicts its current model-writing behavior

**Confidence:** confirmed documentation mismatch.

[README.md](../../../src/KLA.ModelStartupImporter/README.md#L3) says the command deliberately does not modify a model and calls it source-only. Current command/service code imports drafting views and schedules; its SPEC documents the Wave 2 implementation. An operator or maintainer following the README receives the wrong safety and maturity description.

**Recommendation:** align source README, SPEC, deployment prerequisites, supported import subset, and validation status. Distinguish prototype maturity from whether the button writes to a model.

**Acceptance:** all entry documents accurately describe review-before-import, model mutation, known unsupported features, and the exact packaging/live evidence still required.

### REP-11 — P3 — Ribbon palette exceptions remain undocumented at the asset level

**Confidence:** measured pixels; interpretation is an optional consistency decision.

The [icon inventory](evidence/icons.csv) records 428 reusable PNGs and 76 ribbon PNGs, including 19 hidden template assets. The 57 non-hidden ribbon assets contain four with dominant opaque `#EBEBEB` and three with `#34495E`, while the named ribbon light/dark tokens are `#E5E4E2` / `#1A252B`. The old colors occur in the Revision pulldown dark icon and the Outreach About, Prototype, and Suggestions pairs. Five additional white-dominant multicolor assets are not automatically defects: the design guide permits meaningful additional visual detail.

**Recommendation:** record deliberate imported/branding exceptions, then normalize only approved non-branding assets. Preserve originals and attribution. An icon filename or dominant pixel alone is insufficient evidence that a multicolor asset is wrong.

**Acceptance:** approved asset table with color/style rationale and dark/light ribbon previews at actual 24/32-pixel display sizes. Do not recolor logos as part of this review.

## Inventory and coverage

### Assets

All 504 scoped PNGs were decoded for size, alpha, color counts and SHA-256. All 428 reusable sources are at most 96 pixels in each dimension; every scoped ribbon PNG has some transparency. Non-hidden ribbon assets are 14 at 24×24, 24 at 32×32, and 19 at 96×96. Mixed sizes are not inherently invalid: pyRevit can scale sources, and the guide says “usually” 32×32.

The [57-asset contact sheet](evidence/ribbon-contact-sheet.png) was generated from the original files and visually inspected on light/dark sample backgrounds, with previews bounded to 32 pixels. It is an asset-comparison sheet, not a Revit screenshot; it deliberately shows each light/dark variant on both backgrounds and does not imply pyRevit uses the wrong variant. The production outline icons have a broadly coherent silhouette/stroke vocabulary. Four Resource Links/KL&A Tools commands share the cube mark, so their text labels remain important for recognition. Repeated orange drills are the documented prototype convention. Branding assets were preserved.

The Excel COM Smoke Test bundle contains only `bundle.yaml`, `script.py`, and `SPEC.md`: it is the one visible command without its own icon asset. A follow-up consistency task can give it the approved prototype icon or explicitly document host fallback; the metadata checker does not currently validate this asset convention.

The simple named-token check flags 82 reusable assets: 80 button diagrams and two KL&A cube logos. The representative button and cube were visually inspected; their second colors are intentional content, so this is not a list of 82 design violations. The CSV exposes the measurement rather than hiding these exceptions. Individual silhouette recognizability and aliasing still need actual ribbon review.

All 53 tracked XAML files parsed as XML: 20 Windows, 30 ResourceDictionaries, two Pages and one UserControl. XML parsing does not load WPF resources or exercise event bindings. The [GUI review](design-system-and-gui.md) provides the surface assessment. The [preview exporter](../../../scripts/export_ui_gallery_window_pngs.py#L68) draws illustrative Pillow profiles; it is not a WPF renderer and must not be used as screenshot acceptance evidence. No `docs/ui-gallery` output folder existed in this checkout at review time.

### Startup Importer backend

| Area | Review depth | Result / boundary |
| --- | --- | --- |
| Word/Excel readers; immutable byte snapshot; row parser | Source and 15 core tests | Useful size limits, same-byte hash, source locations, malformed input checks; compressed expansion/resource limits not load-tested |
| Catalog/settings/selection intent | Source and core/UI tests | Duplicate IDs rejected; selection revalidated; resource requirements need REP-04 |
| Revit command and import service | Full source control-flow review | REP-01–04; no seed RVT opened or destination modified |
| Schedule translator | Full source review against SPEC/API | REP-01 and REP-03; fidelity requires an explicit supported subset |
| View models | Source and three UI tests | Selection/review behavior tested outside Revit; themed windows assessed separately |
| Packaging and dependency registration | Project/source inspection | No deployment or package rebuild; existing binary parity with source not established |

### Preflight checks (outside the 36 ribbon commands)

Installed pyRevit discovers `checks/` independently, so these are not dismissed as dead code merely because no repository ribbon button imports them.

| Check | Review scope | Finding or live requirement |
| --- | --- | --- |
| `audit_all_check.py` | Import/configuration, report structure, linked-doc and CSV/error paths | REP-07; validate fresh config, unloaded links, Unicode CSV, repeat-run row handling |
| `cad_audit_check.py` | Full workflow and RPW interaction path | REP-09; test view-only, model CAD, unloaded/cloud links and CAD without a valid level |
| `grids_check.py` | Full source | REP-09; repeat collectors can be consolidated to one pass |
| `levels_check.py` | Full source | REP-09; empty models, scope-box and formatted-unit output |
| `modelchecker_check.py` | Structural and risk-focused source pass | Large monolithic report; validate empty/family/non-workshared documents and per-section error reporting; not a line-by-line correctness proof |
| `modelchecker_Warnings_check.py` | Structural and report/error-path pass | Validate empty warnings, localized names and unloaded links; benchmark large warning sets |
| `radar_check.py` | Entry, collectors, document defaults and rollback boundary | Uses `revit.DryTransaction`; verify temporary views are removed on errors and no persistent changes remain |
| `refplanes_check.py` | Full source | Read-only report; unused intermediate counters are optional cleanup, not a blocker |
| `schedules_not_on_sheet_check.py` | Full source | REP-09; test schedule templates, internal/titleblock schedules and split placement |
| `walltypes_naming_convention_check.py` | Full source | REP-08; validate JSON schema/read errors and naming inputs |
| `worksets_content_check.py` | Full source | Reports all elements without paging; silently skips some metadata exceptions; validate non-workshared models and communicate exclusions |

### Architecture, security, performance, and provenance

The repository has a useful split between deterministic Python helpers, Revit adapters, compiled core libraries, and UI resources. Remaining command size and duplication concerns should be addressed as focused refactors following behavior fixes; line count alone is not a defect. The inventories count 159 tracked Python files, 68 C# files and 13 C# projects at the baseline. This review did not claim a full formal audit of every generic snippet, localization translation, vendor binary or content family.

The Startup Importer uses read-only OpenXML parsing, file-size limits, and immutable checklist bytes. Family Studio database/path boundaries and Excel automation are covered in the other tool reports. No external file was uploaded. Dependency vulnerability scanning, binary/source attestation and full license/provenance verification were not performed; source asset origin should be recorded before future copying or replacement. Existing GPL text alone is not an asset-by-asset provenance register, and this review makes no legal-compliance verdict.

Performance risks needing measurement are synchronous Revit/Excel operations, large preflight reports, repeated collectors, Family Studio query truncation, and repeated shared-string-table materialization in Excel parsing. Use realistic large projects and cancellation timing measurements before assigning performance failure severity. Do not move Revit API calls to background threads as a blanket fix.
