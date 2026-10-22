# DevSandbox prototypes and Family Studio review

Reviewed 2026-10-05 against `1562e96a5f6e23b7368c80e317868a0c059dc165`, extension `0.0.11-dev`. This is a review record; no command, shared helper, model, workbook, catalog, configuration, graph, or binary was changed. The assigned write scope was this document only.

This pass covers the behavior of all **17 visible DevSandbox commands**, their adjacent specifications and metadata, the hidden starter bundles, and the Family Studio source and package boundaries. GUI appearance, XAML design-system consistency, accessibility, and visual acceptance are assessed in the companion GUI report. Startup Importer's compiled backend is assessed in [repository-and-assets.md](repository-and-assets.md); its launcher is included here so the command inventory is complete.

The review follows `AGENTS.md` and the code-review-and-quality skill across correctness, readability, architecture, security, and performance. The user authorized review only, so the skill's suggested source-mutation experiment was not performed. Two small adapter probes extracted existing functions into memory without importing Revit or Excel, changing source, or writing output files.

## Evidence and limits

The coordinating reviewer reported the current host as Revit 2024, build `24.3.50.51`, IronPython `2.7.12`, .NET Framework `4.8`. The current coordinated validation is Python **195 run: 194 passed, 1 skipped, 0 failed**, visible-command metadata **36 bundles, 0 errors**, Family Studio Core **19 passed**, and Database **7 passed**. These results demonstrate the tested host-independent behavior and metadata contracts; they do not demonstrate Revit family loading, geometry regeneration, placement, Excel charts, graph execution, or visual acceptance. See the companion validation record for the exact execution evidence and the shared WPF test failure.

Deep inspection: all visible Python command entry points; their main success, cancellation, report, and failure paths; Detail Folders planning/export/HTML helpers; changed-element comparison; Beam Reaction workflow rules; Concrete Mix mapping/reconciliation and write adapter; Steel aggregation, report, history write boundary, dialog selection, and workbook chart construction; UI Gallery launch dispatcher and conservative preview/catalog helpers; Family Studio load, refresh, shared-document lifecycle, metadata/thumbnail services, index orchestration, scanner, repository query/upsert boundaries, migration flow, and browser event handlers.

Inventory/targeted inspection: Family Studio immutable model/configuration contracts and test cases, project/package manifests, bundled dependency filenames, unused Dynamo graphs, and repeated hidden template examples. This is **not** an assertion that every generated file, binary instruction, every test line, or every WPF layout line was audited. No Revit deployment package was rebuilt or packaged command assembly invoked; coordinated test builds/executions are recorded separately. No dependency vulnerability audit was completed, binary/source equivalence proved, or model/Excel/graph workflow executed. Old recorded live trials were used only to locate lifecycle concerns and were not treated as current acceptance.

Confidence labels:

- **Confirmed:** an explicit source/control-flow or specification contradiction, optionally reproduced by a host-independent probe. The host consequence still needs the stated live fixture when applicable.
- **Inferred:** the source makes an unsafe assumption, but the particular Revit failure/geometry behavior needs a supported-host reproduction.
- **Live-needed:** a remaining acceptance requirement, not a proved defect.

Priority uses P1 for the most urgent content-safety defect, P2 for behavior/integrity defects to resolve before promotion, and P3 for lower-impact usability, documentation, or starter-template defects. These priorities do not authorize implementation.

## Visible command coverage matrix

Paths in this table are exact repository-relative bundle paths. `P/` means `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/`; `D/` means `KL&A Tools_dev.tab/05 DevSandbox.panel/`. Each visible bundle's `bundle.yaml` and `SPEC.md` was checked against its actual entry mechanism and effects. The centralized metadata check passes, but its structural success does not establish specification accuracy (DEV-17).

| Command / version / exact bundle path | Behavior and effects inspected | Coverage, concern, and live acceptance |
|---|---|---|
| Beam Reaction Declutter / v0.0 / `P/Beam Reaction Declutter.pushbutton` | Project/2024+/plan guards, Move versus Reset, straight local beam direction, reaction-tag candidates, blocker loop, bounded steps, restoration, marker overrides, per-view outcomes. Model positions/overrides change inside a transaction. | Workflow and adapter tests cover guard/rule/marker paths. DEV-12/13 concern the actual movement lifecycle. Live: one-step collision, multiple blockers, rotated plans, linked/curved/missing beams, pinned tags, restoration failure, repeated run, Undo, reset. Reset only clears markers; it is not a position restore. Fresh overrides/reset semantics are documented and not separately called defects here. |
| Steel PSF / v0.5 / `P/Steel PSF.pushbutton` | Checked-story dialog, steel/floor eligibility, parameter units, level attribution, total/category/type/exclusion report, report-only/initialize/append, eight CSV histories, Excel query/pivot/chart creation, owned Excel cleanup. Reads Revit; writes selected CSV/workbook files. | Pure aggregation/report/history tests exist. DEV-04/05/14; fixed chart row limit and pivot capacity remain acceptance concerns. Live: report totals versus independently counted fixture, filtered selection, missing nominal weights/areas, multiple documents/runs, non-ASCII names, >2000 raw history rows, >17 pivot result rows, unavailable Excel and locked later CSV. |
| Highlight Changed Elements / v0.1 / `P/Highlight Changed Elements.pushbutton` | Project/version guards, sheet picker, distinct saved baseline, open/close baseline without save, sheet matching, type/location/content fingerprints, schedules, comparison, red overrides/clear, unsupported and deleted reports. Current-view overrides change; baseline is read only. | Pure comparison tests cover difference classification. DEV-07 covers unreadable fingerprint fields. Live: baseline/new/modified/unchanged/deleted fixtures, unreadable parameter/location, annotations/schedules, missing sheet, baseline open errors, cancellation, original overrides, Undo. Clear uses the documented red-marker heuristic and has no ownership record; do not infer that it restores arbitrary previous overrides. |
| Create Detail Folders / v0.0 / `P/Create Detail Folders.pushbutton` | Detail/drafting filter, destination selection, Windows folder names/reserved names/collisions, preflight plan, sequential folder creation, native combined PDF, JPEG discovery/rename, HTML escaping and local links, per-folder partial outcome report. No model edits. | Planning/export-link helpers have focused tests. No new high-confidence defect identified in this pass. Live: native PDF availability, disabled/unsupported export, JPEG suffixes, portrait/extents, Unicode/UNC/long paths, locked destination, partial export failure, existing folder collision, usable browser links. Runtime file work can partially complete and the command reports that; preflight is not a filesystem transaction. |
| Element Takeoff / v0.0 / `P/Element Takeoff.pushbutton` | Current selection, length/volume parameter presence and type, length and cubic-yard conversion, per-element/count totals, empty selection. Read only. | Deterministic formatting remains embedded in the adapter. DEV-19. Live: mixed selected categories, zero/missing values, positive/negative lengths, integral/fractional/carry cases, Unicode family names and large element IDs on supported releases. |
| Launch Dynamo Script / v0.0 / `P/Launch Dynamo Script.pushbutton` | Graph existence/document guard, Dynamo assembly fallback, journal flags, execute result alert; graph JSON nodes and dependencies inspected without execution. Bundled `script.dyn` hides/unhides engineering-note content. | DEV-17: SPEC understates both graph assets and model effects. Graph records Dynamo `2.19.3.6394`, archi-lab.net `2023.213.1722` and `archilabUI2022` node types; those are inventory facts, not a compatibility verdict. Live: clean supported Dynamo installation, resolved packages, graph review, target views/elements, cancellation, warnings versus success, Undo, exact hidden/unhidden content. `script_unknown.dyn` is an unused imported graph and was not accepted as a supported workflow. |
| FindReplace - Views-proto / v0.0 / `P/FindReplace - Views-proto.pushbutton` | Selected-view acquisition, local WPF inputs, inherited BaseRenaming, replace/prefix/suffix and case conversion, per-view swallowed exceptions inside `ef_Transaction`. Renames selected views. | DEV-17: SPEC says no direct mutation/UI/assets despite adapter and inherited WPF behavior. No changed/already/skipped/failed summary; tracebacks are the only per-item failure evidence. Live: empty/cancel, duplicate/invalid/read-only names, accepted suffix policy, partial success, rollback, Undo and report accuracy. Shared base/context-manager concerns are also relevant to the Core Tools review. |
| FindReplace_Sheets-proto / v0.0 / `P/FindReplace_Sheets-proto.pushbutton` | Sheet selection, names and numbers, five-attempt automatic `*`/`_` suffix fallback, case conversion, Project Browser refresh, raw transaction. Renames sheets. | DEV-03/17. Live: unchanged/duplicate/invalid names and numbers, retry exhaustion, read-only/workshared sheet, pane failure, commit rollback, cancel and Undo. User must be told which requested names were altered by fallback and which targets failed. |
| Open Keynote File / v0.0 / `P/Open Keynote File.pushbutton` | Live KeynoteTable external path, saved TransmissionData fallback, resolution/existence checks, OS default-editor launch, launch error. Does not itself edit the model or keynote text. | No new high-confidence defect identified. Live: current external path versus saved state, relative/UNC path, unsaved/cloud model, missing/unavailable file, unregistered editor and user cancellation. Saved-state fallback must remain visible in diagnostic evidence when used. |
| Concrete Mix Header / v0.1 / `P/Concrete Mix Header.pushbutton` | Read-only Excel table/fallback read, mapping and coercion, chosen schedule/header dimensions, paired-row reconciliation, unknown/duplicate rejection, explicit deletion/write confirmations, row edits, cell clears/writes, column width warnings, transaction and output. | DEV-02; template-identity/shape preflight is a promotion requirement. Pure mapping/reconciliation tests do not test failed Revit clears. Live: exact GN03 layout and merges/styles, blank replacement, added/missing mixes, deletion No/Yes, shifted notes/anchor, wrong schedule rejection, locked cells, COM read failure, rollback and Undo. Excel cancellation currently offers the second file-type picker; verify intended UX. |
| Excel COM Smoke Test / v0.0 / `P/Excel COM Smoke Test.pushbutton` | UUID-owned temp paths, facade create/add/sheet/range/query/pivot/chart/save/reopen/refresh/calculate, per-operation results, cleanup, retain-on-failure reporting. Diagnostic files/hidden owned Excel only. | DEV-06. Existing command test checks source contracts rather than a full fake lifecycle. Live: each supported host/Excel pair, missing Excel, failed reopen/refresh/calculate/close, no orphan process, successful exact-owned-file removal, failed-run actual retained paths, never deletion of unrelated files. |
| URL Button (bundle `Trial`) / v0.0 / `P/Trial.urlbutton` | YAML URL launcher to configured `https://forms.cloud.microsoft/r/HjuggSZqyU`; no Python or model effect. | Inventory-only browser target review. Live-needed: destination is the intended current KL&A form, browser/account behavior, Cancel/close. No submission or message was sent during review. |
| Family Studio / v0.0 / `P/Family Studio.invokebutton` | Compiled `FamilyStudioCommand`, project context, SQLite browser/filter/favorite/recent/detail/paths, load/batch/place, configuration-driven refresh, metadata/previews and shared opened-RFA lifetime. Local DB/cache/status writes; explicit model family loads and placement. | Deep backend assessment below; DEV-01/08/09/10/11/15. Core19/Database7 pass independently of Revit services. Live gates must cover content identity, existing-name conflicts, atomic batch rollback, type activation/placement, source preservation, preview failure and indexed-root failures on 2024/2025/2026. |
| Startup Importer / v0.0 / `P/Startup Importer.invokebutton` | `context: doc-project`, `assembly: KLA.ModelStartupImporter.Revit.dll`, `command_class: StartupImportCommand`, create-only review/confirmation contract and SPEC. | Backend findings and tests belong to [repository-and-assets.md](repository-and-assets.md). Live-needed: checklist/settings/catalog/seed mismatches, blocked plan, skipped existing target, cross-document view types, commit failure, schedule fidelity, complete rollback and report. Launcher presence is not backend acceptance. |
| Inspect Schedule Header / v0.0 / `P/Inspect Schedule Header.pushbutton` | Schedule picker, header/body section metadata, cell text/styles/merges/row/column information, optional API warnings, Unicode JSON/CSV export and preview output. Read-only Revit inspection with selected-folder file writes. | Source inspected; no focused adapter behavior test located. No new high-confidence model-safety defect. Live: unsupported property warnings, merged cells, unusual first-row/column numbering, Unicode, ordinary/key/revision schedule boundaries, cancelled picker, locked folder and JSON-success/CSV-failure partial result. Timestamp filenames have second resolution; overwriting same-name same-second exports is a minor acceptance edge. |
| UI Gallery / v0.3 / `P/UI Gallery.pushbutton` | Explicit dispatcher, synthetic preview data, disabled compiled catalog rows, conservative XAML classification and bounded path policy, prototype dialog preview import, close/filter/action paths. Does not run the corresponding model-writing commands. | Gallery catalog/launcher tests exist; GUI agent covers visual surface coverage. DEV-16. Live: each enabled row under both tab layouts, no command side effects, import isolation, unsupported-resource explanation, compiled-row disabled state, nested preview close and output. |
| Launch Dynamo Player / v0.0 / `D/Launch Dynamo Player.pushbutton` | DynamoPlayer/Playlist/postable-ID fallbacks, `CanPostCommand`, warning and post. Opens host UI; does not itself run a graph. | Thin adapter with explicit capability check. Live-needed: each supported Revit/Dynamo combination, unavailable command, another active command, post completes, and no graph starts automatically. |

## Findings

### DEV-01 — P1, confirmed: failed Family Studio loads can resolve to unrelated same-name content

**Evidence:** `src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Services/RevitFamilyLoadService.cs:74` calls `LoadFamily`; lines 75-79 accept only `loaded && loadedFamily != null && Committed`. Lines **82-91** then search every project `Family` by case-insensitive `FamilyName` and return it even when the selected load returned false/null or did not commit. `LoadAndPlace` chooses that family's first symbol at lines 26-33. Browser lines 188-191 and 405-406 record the selected catalog ID as successfully loaded. The adjacent Family Studio `SPEC.md:95-97` explicitly forbids this fallback.

**Trigger/consequence:** select library family B while unrelated/different family A of the same name is already in the model, and make B's load return false/null or roll back. The command can return A, place A, and record B as loaded. A batch can similarly assimilate and report success despite the failed selected load. This is a source-confirmed identity and acceptance-contract defect; the precise Revit conflict/failure fixture has not been executed.

**Remedy:** remove name-based acceptance after a failed load. Model load outcomes explicitly, fail closed on null/false/noncommitted status, validate activation/group outcomes, and surface the selected file and cause. If intentional reuse of existing content is desired, make it a separate approved identity policy with verifiable provenance rather than a name match.

**Verification:** supported-host fixtures for new load, same-name identical/different source, false/null load, rollback/pending failure handling, missing/newer/corrupt source, and second-item batch failure. Assert only the selected content is placeable, no false recent-use row is recorded, and the batch remains unchanged on failure. [Autodesk's transaction contract](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/32714010-7138-f64f-8fde-a310354448e3.htm) requires checking returned status; the current official reference is 26.4, while this review's observed host is 2024.

### DEV-02 — P2, confirmed and reproduced: blank Concrete Mix replacements can retain old requirements

**Evidence:** `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Concrete Mix Header.pushbutton/script.py:288` clears every paired cell, but lines **293-296** ignore every clear exception. `_write_pair` lines **379-382** skips all blank replacement values. The enclosing successful transaction is followed by “Import complete” at line 562.

**Trigger/consequence:** a required writable/owner cell currently contains an old requirement, the clear operation fails, and the incoming mapped value is blank. That old value persists and the import reports completion. A non-mutating AST probe with a fake owner-cell clear failure reproduced `OLD REQUIREMENT` remaining after `_clear_pair` and `_write_pair` without an exception. This is distinct from expected errors clearing non-owner cells in a merged region.

**Remedy:** resolve merged owner cells explicitly, distinguish harmless non-owner operations from required clears, and fail/roll back or report a precise failed outcome when a required destination cannot be blanked. The resulting header must be verified against the planned values before reporting success.

**Verification:** adapter test for a failed owner-cell clear followed by blank replacement; live fixture with stale strength/slump/exposure/note-reference text, merged layout, write error and rollback. No old requirement may survive an accepted blank update.

### DEV-03 — P2, confirmed: sheet prototype transactions can escape their scope

**Evidence:** `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/script.py:65-71` and **98-109** create/start raw transactions without `using`, a context manager, or rollback/finally. `update_project_browser()` hides/shows a pane before `Commit`. Commit status is ignored.

**Trigger/consequence:** pane refresh or an unexpected rename error occurs after one or more writes. The transaction has no deterministic close/rollback path in that event handler; Revit must handle the leaked scope or subsequently reject work. A rolled-back commit is also not distinguished from success. Separately, five retries can silently exhaust or change the requested name with `*`/`_` suffixes without an outcome report.

**Remedy:** enclose the transaction in an established safe lifecycle, check commit result, move browser refresh after commit, and aggregate changed/already/skipped/failed and adjusted-name outcomes. Preflight invalid/duplicate requested values rather than treating unrelated exceptions as suffix collisions.

**Verification:** fake pane failure after one renamed sheet must trigger rollback/cleanup; live invalid/duplicate/workshared name and number, retry exhaustion, failure processing, browser already hidden, subsequent transaction, and Undo. [Autodesk's Commit example](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/32714010-7138-f64f-8fde-a310354448e3.htm) uses guarded scope and explicit status checks.

### DEV-04 — P2, confirmed: Steel PSF history charts compute member PSF instead of story PSF

**Evidence:** `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/script.py:550-558` takes one eligible **Steel Raw** member's weight in column G and divides it by the summed story floor area. Lines **504-506** chart those rows as “Steel PSF - PSF History”. The report/level-summary calculation aggregates all eligible story weights.

**Trigger/consequence:** a story has more than one steel element. For 100 lb and 300 lb over 100 sf, the chart emits 1 and 3 PSF; the story report is 4 PSF. This arithmetic counterexample was checked in memory. It also groups on timestamp/level instead of the exported run identity, and the charts consume only the first 2000 raw history rows.

**Remedy:** use the existing level-summary history (or aggregate steel/floor once per run/document/level) as the chart source. Use the run identity, distinguish story series, and either grow the source range or clearly disclose a deliberate display limit.

**Verification:** multiple members/floors, excluded members, zero area, two documents with the same level names, several runs and >2000 raw rows. Charted PSF must equal the independent story aggregate and the CSV/report value. Excel rendering and refresh remain live-needed.

### DEV-05 — P2, confirmed and reproduced: Steel PSF drops checked stories hidden by a filter

**Evidence:** the Steel PSF adapter `_finish_selection`, **script.py:224-229**, collects checked items from `main_ListBox.ItemsSource`, which is the filtered visible list, rather than the complete item collection. It clears the filter only after choosing the output selection.

**Trigger/consequence:** check Level 1, filter to Level 2, check Level 2 and Run/Initialize/Append. Level 1 is silently omitted from the calculation/export even though its retained item is checked. An AST probe with both underlying items checked and only Level 2 visible returned only Level 2.

**Remedy:** collect from the full canonical collection or a stable checked-ID set; render the selected count and make filter-scoped Select All/None semantics explicit.

**Verification:** select across two successive filters, run with a filter active, clear/reapply filter, select-all/no-items and all three output modes. The exact selected-story set must survive filtering.

### DEV-06 — P2, confirmed: late Excel smoke failures delete the promised diagnostic assets

**Evidence:** `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Excel COM Smoke Test.pushbutton/script.py:220-229` runs reopen/refresh/calculation after the prior retention decision. Reopen-stage `_record` failures do not update `retain_assets` before `_cleanup`. Line **228** also discards suppressed close/quit errors. Line 233 says failed runs retained assets.

**Trigger/consequence:** the first save succeeds, then Excel creation/reopen/refresh/calculation fails. The diagnostic workbook/CSV can be deleted while the warning states they were retained. Late close errors are absent from the result table, reducing this tool's diagnostic value.

**Remedy:** merge all close/quit failures into the operation results, recompute retention after the final owned Excel lifecycle, then delete exact-owned assets only for a wholly successful run. Report actual retained paths and cleanup failures.

**Verification:** fake lifecycle tests for each reopen-stage and cleanup failure; live supported Revit/Excel versions, failed reopen/refresh and an orphan-process check. Assert failed runs retain the exact UUID folder and successful runs remove only owned files.

### DEV-07 — P2, confirmed: unreadable comparison fields can be reported as unchanged

**Evidence:** `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Highlight Changed Elements.pushbutton/script.py:156-157` turns a location-read exception into the ordinary tuple `('unavailable',)`. Lines **184-189** turn per-parameter failures into sorted ordinary content entries and return no unsupported error. `_fingerprint` at lines 211-213 passes only the outer content error to the unsupported report. `lib/changed_elements/comparison.py:23-29` therefore classifies equal unavailable/error sentinels as unchanged. The command SPEC requires unavailable comparison data to be reported as unsupported rather than silently unchanged.

**Trigger/consequence:** both snapshots fail reading the same field in the same way. A real location/content difference is unknown, but the result reports unchanged and can omit the warning.

**Remedy:** return a validity/error result for each fingerprint field and route invalid comparisons to an explicit unsupported/unknown classification. Error text is diagnostic data, not an equality fingerprint.

**Verification:** host-independent adapter fixtures for identical read errors on both snapshots, one-sided read error, and partial parameter failure; live problematic annotation/parameter cases. Unknown data must never support an unchanged conclusion.

### DEV-08 — P2, confirmed: Family Studio omits failed-root warnings from Refresh Complete

**Evidence:** `src/KLCode.FamilyStudio/Library/KLCode.FamilyStudio.Core/Indexing/LibraryIndexer.cs:43-48` separates `Errors`/`FilesFailed` from `ScanIssues`. `FileSystemLibraryScanner.cs:45-54` and 85-87 emit missing/reparse/unreadable roots as scan issues. `FamilyStudioWindow.xaml.cs:465-482` branches solely on `FilesFailed`; `BuildRefreshDetails` at lines 493-497 uses only `Errors`.

**Trigger/consequence:** a root is missing, unreadable, or rejected, but all discovered families succeed (including zero discovered files). The browser shows “Refresh Complete” with zero failures and omits the root's issue. The conservative missing-file reconciliation is a strength, but the operator may think the catalog is current when that root was not scanned.

**Remedy:** include root/directory scan issues in the visible summary and warning decision, show scanned versus unscanned roots, preserve their paths, and distinguish complete from partial refresh.

**Verification:** one missing root with no files; one successful plus one unreadable root; a reparse root/directory; >8 issues with an explicit omitted count and durable details. Tests must assert browser warning semantics as well as repository reconciliation.

### DEV-09 — P2, confirmed: partial Family Studio type-preview failure is silently accepted and discards prior mappings

**Evidence:** `src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Services/RevitThumbnailService.cs:80-90` catches each type-preview exception without retaining diagnostics. Lines **46-49** return success as soon as any type preview exists. `SqliteFamilyRepository.cs:348-349` clears old preview/type mappings and lines 377-394 insert only the returned previews. LibraryIndexer reports/retains prior previews only when the whole thumbnail call throws.

**Trigger/consequence:** type A renders and type B fails, although B previously had a preview. Refresh reports no type issue and replaces the old mappings with A only; B's old preview is no longer associated. Type B detail may fall back to A's family thumbnail, visually suggesting the wrong type. This contradicts the SPEC's retention/reporting promise for failed previews.

**Remedy:** make the thumbnail result carry successful previews and per-type failures, preserve valid old previews by stable type name for failed types, and report partial refresh. Do not silently substitute another type's image as an exact-type preview.

**Verification:** three-type fixture with a middle render failure, prior preview present/absent, all types failed, family fallback, renamed/deleted type and cancellation. Inspect mappings, warning counts, displayed type labels and the actual cached images.

### DEV-10 — P2, confirmed: corrupt cached images can escape Family Studio selection handlers

**Evidence:** `src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/FamilyStudioWindow.xaml.cs:371-384` checks only file existence, then constructs an absolute URI and decodes/freezes a BitmapImage without a catch. `UpdateTypeDetail` calls it from selection handlers (lines 70 and 350-368), outside the Load action's guarded error path.

**Trigger/consequence:** a cached PNG is corrupt, inaccessible after the existence check, or contains a bad persisted path. Opening/selecting that catalog item can throw from a WPF routed event instead of displaying the placeholder and a useful diagnostic. Startup construction may be caught by the external command, but interactive event failure is not safely handled here.

**Remedy:** contain file/URI/decode failures at the thumbnail boundary, return a placeholder/error state, and show/log a path-specific warning while keeping the browser usable.

**Verification:** corrupt/zero-byte/deleted/locked PNG, non-absolute persisted path, valid image and repeated selection. The browser must survive and Load actions remain available independently of image validity.

### DEV-11 — P2, inferred: placed-family recent history can be lost when placement ends with Esc

**Evidence:** `src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Commands/FamilyStudioCommand.cs:49-55` records `Placed` only after `LoadAndPlace` returns normally. Its cancellation catch assumes Esc means no instance was created. The service uses interactive `PromptForFamilyInstancePlacement` at line 33.

**Trigger/consequence:** place one or more instances, then end the interactive placement session with Esc. If the prompt raises cancellation on session exit, placed instances remain but the recent-use record is skipped. Autodesk's developer guidance confirms cancellation can throw; the [developer sample](https://github.com/jeremytammik/the_building_coder_samples/blob/master/BuildingCoder/CmdPlaceFamilyInstance.cs) counts added IDs across the prompt and handles cancellation separately. Current 2024 behavior still needs the exact fixture.

**Remedy:** distinguish zero placements from completion of a session containing placements. Track the actual matching added instances during the prompt with deterministic subscription cleanup, or explicitly define recent history as attempted placement and label it accordingly.

**Verification:** Esc before placing, one/two placements then Esc, host cancel/right-click exit, failed hosted placement, and repeated runs. Persist history only according to the chosen documented outcome, without leaking event subscriptions.

### DEV-12 — P2, inferred: Beam Reaction collision checks read modified geometry before regeneration

**Evidence:** `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Beam Reaction Declutter.pushbutton/script.py:218-223` moves a tag and immediately obtains both bounding boxes inside the still-open transaction. There is no regeneration in that loop; the outer transaction regenerates only at commit.

**Trigger/consequence:** a moved tag's bounding box is not updated by the host until regeneration. The bounded loop can keep evaluating its old position, take excess steps, report unresolved, or accept incorrect collision outcomes. [Autodesk's Regenerate reference](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/22468e2c-9772-8478-0816-c9759aa43428.htm) shows geometry-derived data can be stale before regeneration. The particular tag behavior needs host measurement.

**Remedy:** regenerate before reading geometry after a move, or use a validated transformed-box calculation with regeneration before the final check. A regeneration failure must abort the active transaction rather than continuing geometry reads. Recheck all blockers at the final position; clearing a later blocker can introduce an earlier collision.

**Verification:** one-step-clear fixture comparing pre/post-regeneration bounds, multiple blockers, rotated plans, pinned tags and regen failure. Measure step counts, final overlap and actual displacement, not just reported category.

### DEV-13 — P2, inferred: Beam Reaction failure restoration is not guaranteed by rollback

**Evidence:** the Beam Reaction adapter **script.py:302-307** and **311-317** catches a failed restoration and still returns `skipped`; the outer view transaction can commit. When a movement fails after partial progress, the outstanding step count also crosses nested exception paths rather than being isolated in a rollback scope.

**Trigger/consequence:** a tag has moved, a later move/marker operation fails, and the reversal also fails. The report can say skipped while the tag remains displaced and unmarked. The exact double-failure fixture is live-needed; swallowing the restore error is source-confirmed.

**Remedy:** isolate each tag in a subtransaction and roll it back on unresolved/move/marker failure. If rollback itself fails, stop the enclosing transaction and report the actual failed target; do not imply restored position.

**Verification:** injected second-step failure, marker failure, failed reverse move, and a subsequent successful tag. Verify failed targets' actual coordinates and overrides equal their starting state and report counts reflect the model.

### DEV-14 — P2, confirmed: late Steel CSV write failure leaves a mismatched history set

**Evidence:** `lib/steel_weight/history.py:265-283` opens/writes each of eight history files sequentially. Initialize truncates earlier files; Append adds earlier rows. There is no staged set, rollback, manifest, or completion record when a later file write raises.

**Trigger/consequence:** a later CSV is locked or storage fails after Steel Raw succeeds. The history set contains part of the run; initialize may already have discarded earlier history files, and retrying append can duplicate rows in the files already written. Workbook summaries/charts can then compare different run sets despite passing the pre-write header check.

**Remedy:** stage a complete export set and publish with recoverable backups/completion manifest, or use a transactional history store followed by generated CSVs. Include run-ID reconciliation and an explicit partial-write diagnostic if publication cannot be completed.

**Verification:** file-writer fault at each later file and mid-write, initialize/append, retry with the same run identity, locked Excel/query source. Assert either the old complete set remains or the new complete set is published; no unnoticed truncated or duplicate history.

### DEV-15 — P3, confirmed: Family Studio's 200-result cap is presented as the complete result count

**Evidence:** browser **FamilyStudioWindow.xaml.cs:62-63** calls Favorites/Recent with 200; Search at lines **235-244** likewise uses 200. Repository query `SqliteFamilyRepository.cs:458` applies `LIMIT $limit`. Browser result text at lines 266-268 uses returned count only. There is no total count, next page, or truncation marker.

**Trigger/consequence:** >200 catalog matches/favorites/recent items. Results after the ordered cap cannot be browsed, and “200 results” does not tell the operator there are additional matches. Exact search/facets can narrow some queries but cannot show a complete favorites/recent list.

**Remedy:** preserve bounded queries but expose total/truncated state and a narrowing cue; add deterministic pagination or a load-more action if complete browsing is required. Include a stable tie-breaker in paged order.

**Verification:** 199/200/201/500 matches and favorites/recent entries, duplicate display names, filter reset and page selection. Assert no silent omission and acceptable query/thumbnail latency. This is the functional counterpart of the GUI reviewer observation, not a second independent defect.

### DEV-16 — P3, confirmed: three UI Gallery previews assume the development tab exists

**Evidence:** `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py:326-328`, **354-356**, and **579-581** build paths containing literal `KL&A Tools_dev.tab` for the prototype view/sheet rename and ViewRange previews. `AGENTS.md:5-6` and adjacent tool path aliases define the release layout as `KL&A Tools.tab`.

**Trigger/consequence:** use the same gallery in the release layout after the tab is renamed. These preview actions cannot find the real XAML despite being listed as enabled. Other library-based previews can work, making the catalog appear partly broken.

**Remedy:** resolve the actual containing tab or an established alias-aware root/path helper, and test both layouts for every file-backed enabled launcher.

**Verification:** host-independent path resolution in both development/release directory fixtures and one live launch per affected row. No model command should execute while checking gallery coverage.

### DEV-17 — P2, confirmed: generated prototype specifications misstate mutation, UI, and asset boundaries

**Evidence:** prototype view/sheet `SPEC.md:58` each states no Revit transaction/direct mutation detected. Their adapters rename Views/Sheets, and the sheet adapter explicitly starts transactions. View SPEC line 45 says no WPF/output API detected although BaseRenaming constructs WPF; both list no bundled assets despite adjacent `Script.xaml`. Dynamo launcher `SPEC.md:40` says no assets and line **57** says no mutation detected, but its `script.dyn:778`, 817, 1141 and 1180 references HideElements/UnHideElements and its launcher requests execution.

**Trigger/consequence:** a maintainer/operator uses the adjacent SPEC to approve a trial, evaluate cancellation, or determine model effects. A syntactic token scan supplies misleading safety/behavior evidence, especially across imported APIs/inheritance/graphs. The “statically derived” disclaimer does not make those concrete statements accurate.

**Remedy:** replace generated absence claims with a human-reviewed behavior/effect contract, name transitive helpers/XAML/graphs/packages and the intended selection scope, cancellation/partial-success semantics, and acceptance fixture. Static inventory must distinguish “not detected by this scanner” from “does not occur”.

**Verification:** trace each visible prototype's actual entry mechanism and model/external effects into SPEC; review Find/Replace and the executing Dynamo graph first. Add metadata checks for referenced assets as structural checks, without claiming semantic safety from them.

### DEV-18 — P3, confirmed: hidden starter examples contain copy-time runtime errors

**Evidence:** `_Templates/_Template.pushbutton/script.py:42` imports missing `Snippets._customprint`; the same placeholder import appears in repeated Example.tab starter buttons. `_Bundles/with_config-xx.pushbutton/script.py:44` sets `warnings` to a string and line **50** calls `warnings(doc)`; `doc_warnings` at lines 35-40 returns None for zero warnings but line 59 concatenates it. `Example.tab/.panel/.stack/StackMenu.pulldown/StackPulldownButton3.pushbutton/script.py:101` calls undefined `convert_internal_units`. Configuration Cancel at `config.py:14-16` saves default selections instead of preserving current config.

**Trigger/consequence:** a contributor promotes/copies these examples as working starter code. Ordinary empty config, zero warnings, or wall-selection cases fail or reset persisted settings unexpectedly. These underscore/dot hidden examples are not present in the visible panel and do not constitute a current visible-command outage.

**Remedy:** label archival examples clearly and direct contributors to the authoritative current command template; repair runnable examples separately if they are intended to be maintained. Remove placeholder printing only as an approved cleanup and keep Cancel non-mutating.

**Verification:** independent host-free import/smoke cases for no-warning/empty-config and missing helper, followed by a disposable-host copy trial. Do not add broken starter code to the visible layout to test it.

### DEV-19 — P3, confirmed: Element Takeoff omits the inches mark for integral lengths

**Evidence:** `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Element Takeoff.pushbutton/script.py:48-59` includes the inches quote only in `frac_str` for fractional values; when the remainder is zero it is empty. For example 3 ft 6 in formats as `3'- 6`, whereas a fractional value includes the mark.

**Remedy/verification:** append the inches mark independently of the fraction and move this deterministic formatter into a testable helper. Check 0, 3 ft, 3 ft 6 in, fractional sixteenths, rounding carry and negative inputs against a clear output policy. This is report notation, not a model mutation defect.

## Family Studio backend assessment

| Layer / exact source directory | Inspected behavior and positive evidence | Limits and required next evidence |
|---|---|---|
| `src/KLCode.FamilyStudio/Library/KLCode.FamilyStudio.Core/Configuration/` | Operator-owned JSON path normalization relative to configuration file, enabled root validation, immutable settings boundary. Revit refresh checks normalized selected/active database equality. | Current JSON deserialization/model contracts were inspected selectively; test suite establishes the covered cases. Live wrong database, UNC/network unavailable, readonly DB/cache and malformed configuration; no active/shared catalog was touched. |
| `.../Core/Indexing/` | Deterministic `.rfa` scan, case-insensitive overlapping-root deduplication, fail-closed reparse handling, file state/hash decisions, per-family continuation, cancellation boundaries, progress/current-family status, conservative missing-file handling; preview failures retain the prior family preview in the core path. | Scan warnings are lost in the browser (DEV-08); partial per-type failures do not reach core (DEV-09). Scanning is synchronous and not cancellation-aware within a long directory scan. Each Revit open/render call is synchronous; a token does not interrupt that call. |
| `.../Core/Models/`, `Search/`, `Repositories/` | Typed validated input/result models and repository abstraction allow filesystem-only CLI and host-specific extractors; search limit is validated. | Contract/model test inspection was targeted rather than a line-by-line audit of every model. Browser needs total/truncation semantics (DEV-15) and explicit outcome models for load/preview. |
| `src/KLCode.FamilyStudio/Library/KLCode.FamilyStudio.Database/` | SQLite schema versions 1-3 with transaction-wrapped migrations, newer-schema rejection, parameterized query values, transaction-wrapped family upsert, typed favorites/recent, hidden deleted records, root-aware matching and informational duplicate signals. No concatenation of user search text into SQL was found. | Migration/queries were source reviewed; no production database was opened. Upsert clears previous type/preview children (DEV-09). Live concurrent reader/refresh, readonly/full/locked database, corrupt database and migration recovery. Passing Database tests do not prove deployed native SQLite loading. |
| `src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Services/` | Shared RFA session avoids opening a family twice; thumbnail finally closes it without saving. Revit metadata extracts types/parameters; preview filenames sanitize names and add a source/type SHA-256-derived suffix; changed image detection prevents simply promoting an old unchanged export. | DEV-01/09. `RevitFamilyDocumentSession.Close:36-37` removes its dictionary entry before `Close(false)`; close failure/false result has no explicit recovery evidence. Type activation and batch-group final status require acceptance/checking. No source RFA or assembly was changed. |
| `.../Revit/Commands/FamilyStudioCommand.cs` and `Views/FamilyStudioWindow.xaml.cs` | Project/family-editor guard, using-scope repository, modal browser, placement after browser closes, external refresh configuration selection, favorite/local recent, selected-family/path operations and mode/selection synchronization. | DEV-08/10/11/15. Refresh passes `CancellationToken.None` and blocks on `GetResult`; there is no user cancel route from this UI. Persistent status helps diagnose long runs but is not responsive GUI progress. Some database/clipboard/shell event handlers are not individually guarded; readonly DB and clipboard-unavailable behavior need a UI fixture. |
| `src/KLCode.FamilyStudio/App/KLCode.FamilyStudio.Indexer/` | CLI argument/configuration boundary and explicit filesystem-only metadata extraction; no Revit category/type/parameter/preview promises for desktop indexing. | Inventory/targeted source and Core test review only. Do not substitute CLI completion for Revit extraction/preview completion. No indexer executable was launched or generated. |

Refresh remains a manually supervised prototype: the browser passes no cancellable token, fully reprocesses each discovered family, and operates synchronously in a valid Revit API context. The current adapters return completed tasks, so the core's `ConfigureAwait(false)` does not itself prove an active thread violation; any future genuinely asynchronous host adapter must preserve the Revit-thread boundary explicitly. Do not move Revit API work into arbitrary background tasks to fix responsiveness.

The local design is appropriately separated: host-independent scanner/index/repository rules have tests, Revit work stays in a host adapter, search values are parameterized, roots are operator controlled, preview paths have collision-resistant keys, and source documents are intended to close without save. Promote these strengths while replacing silent fallback outcomes and hard-to-test UI/repository coupling with explicit result objects.

### Compiled package and compatibility boundary

The invokebutton advertises `KLCode.FamilyStudio.Revit.dll` / `FamilyStudioCommand`. The bundle also contains `KLCode.FamilyStudio.Revit_2024.dll`, `KLCode.Wpf_2024.dll`, unsuffixed WPF/Revit assemblies, Core/Database assemblies, SQLite managed/native providers and supporting framework libraries. The Family Studio project targets `net48` for Revit 2024 and `net8.0-windows` for 2025/2026, limits permitted versions at build validation, uses installed API references with `Private=false`, and packages the 2024 suffix separately. Core/Database target `netstandard2.0`; the host variant removes Core's standalone JSON provider. Database references `Microsoft.Data.Sqlite 8.0.30` and `SQLitePCLRaw.provider.e_sqlite3 2.1.12`. The bundled `.deps.json` describes the .NET 8 runtime set and is not proof of the deployed .NET Framework dependency closure.

This review inventoried those assets and manifests without rebuilding or loading them. Exact selected assembly by host, public type/dependency closure, native SQLite resolution, shared WPF theme resolution, source-to-binary correspondence and every supported host remain release/promotion gates. The companion repository/asset review owns cross-command preload/package findings. There is no claim here that an assembly's existence, an old successful build, or Core/Database tests validates native command launch on 2024/2025/2026. Package rebuild targets can overwrite tracked bundle assets; none was run for this review.

### Family Studio acceptance order

1. **Protect content identity:** DEV-01, loaded family source identity, false/null/rollback/pending results, same-name variants, missing/newer/corrupt files, batch second-family failure, no false history entries. Stop promotion until that contract is resolved.
2. **Verify host lifetime:** project versus family editor/no active project, RFA open/read/preview/close failure, repeated refresh, no leaked family documents, source bytes/timestamp unchanged, native dependency launch in each supported Revit release.
3. **Verify refresh truth:** successful/missing/unreadable/reparse/omitted/disabled roots, mixed file failures, cancellation/long-current-file monitoring, prior-preview and partial-type preservation, exact counts, migration/locked database, and selected/active DB mismatch.
4. **Verify selection and placement:** selected family/type detail, exact placed type policy (the current service chooses the first family symbol), zero/one/many instances then Esc, host-based/unplaceable families, activation failure and correct recent outcome.
5. **Verify browsing at scale:** 201+ matches/favorites/recent, filters and duplicated names, list/grid consistency, corrupt cached images, missing paths, clipboard/shell errors, query latency, memory and image decode cost on a representative catalog.

## Hidden DevSandbox template coverage

The underscore `_Templates` subtree and dot-prefixed sample bundle directories are outside the visible panel layout. These are scaffolding/examples, not additional visible commands. Their metadata was inventoried proportionately; every sample is not claimed to meet visible-command governance until copied/promoted.

| Exact path below `KL&A Tools_dev.tab/05 DevSandbox.panel/_Templates/` | Inspection and acceptance |
|---|---|
| `_Template.pushbutton/script.py`, `bundle.yaml` | Read standard imports/placeholders; missing `_customprint` at line 42 (DEV-18). Do not copy as a tested current command starter. |
| `_Bundles/with_config-xx.pushbutton/script.py`, `config.py`, `bundle.yaml` | Read config lookup/defaults, queries and output. Empty-config call error, zero-warning concatenation and Cancel saving defaults (DEV-18). Model read only. |
| `_Bundles/OpenProjectFolder-xx.pushbutton/script.py`, `bundle.yaml` | Read actual Project Information text parameter/path read/open/update flow plus obsolete commented predecessor. Check missing/wrong/read-only parameter, empty/cancel, Set result, nonexistent/network path and shell failure before using. Model parameter update uses transaction. Hidden imported example, not live accepted. |
| `_Bundles/dynamo_script-xx.pushbutton/script.dyn`, `bundle.yaml` | Inventory and node inspection: imported graph includes view-template parameter include/exclude, Data-Shapes/BIM One/archi-lab Python/UI code and legacy unit/parameter APIs. No launcher script, graph runtime/package/license/compatibility acceptance here. Promotion needs graph-specific specification and supported-host/package review; do not automatically execute it. |
| `_Bundles/invoke_dll_button-xx/bundle.yaml`, `bin/AliTpyRevitConcepts.dll` | Imported DLL launcher inventory only; source/dependency/content provenance not established in this pass. Parent asset/governance review applies; no execution or replacement. |
| `Example.tab/.panel/.pushbutton/script.py`, `bundle.yaml` | Read simple Hello World/wall-count model-read example. Host selection and metadata need current-template treatment if promoted. |
| `Example.tab/.panel/.pulldown/PulldownButton1.pushbutton/script.py`; `PulldownButton2.pushbutton/script.py`; `PulldownButton3.pushbutton/script.py` | Repeated placeholder startup/import/printing bodies inspected as samples; same missing `_customprint` family (DEV-18). Not three accepted tools. |
| `Example.tab/.panel/.stack/Button1.pushbutton/script.py`; `Button2.pushbutton/script.py` | Same repeated placeholder starter pattern, inventory and representative behavior review. |
| `Example.tab/.panel/.stack/StackMenu.pulldown/StackPulldownButton1.pushbutton/script.py`; `StackPulldownButton2.pushbutton/script.py` | Same repeated placeholder starter pattern, inventory and representative behavior review. |
| `Example.tab/.panel/.stack/StackMenu.pulldown/StackPulldownButton3.pushbutton/script.py` | Read class/category/wall-height selection examples, top-level picks, unguarded Esc and category-null assumptions; undefined unit-conversion helper at line 101 (DEV-18). Live copy trial only after missing-helper/cancellation repair. |
| `Example.tab/.panel/_Advanced/.urlbutton/bundle.yaml`; `.content/bundle.yaml`; `.combobox/bundle.yaml`; `Example.tab/.panel/bundle.yaml` | Bundle-type/layout inventory only. External URL/content/combobox runtime, placeholder values and imported asset provenance require separate acceptance before promotion. |

## Cross-cutting assessment and next review slices

Correctness is the dominant concern: source-confirmed false load acceptance, stale schedule data, incorrect story chart arithmetic, hidden selected scope, incomplete diagnostic retention, and understated refresh/comparison outcomes. Several shared pure helpers already embody clearer behavior than their adapters; the missing tests concentrate at the adapter/lifecycle boundary.

Readability/architecture: the short Dynamo/Keynote/Player adapters are proportionate. The Steel workbook code, Concrete reconciliation adapter, large Inspector and Gallery dispatcher contain meaningful feature-specific behavior that is difficult to verify through source-token tests. Extract result planning and lifecycle states into owning packages, leaving Revit/Excel calls in thin adapters. Family Studio has a useful Core/Database/Revit split, but silent name/preview/error fallbacks should become explicit outcomes instead of being hidden behind `void` or an ordinary success thumbnail result.

Security/file safety: no concrete SQL injection or command-secret issue was identified in the inspected paths. Detail Folders validates Windows names, direct-child generated outputs, encodes HTML and URLs, and reports partial file outcomes. Excel smoke confines cleanup to UUID-owned paths. Family Studio rejects reparse library content and uses parameterized searches. Actual defects are integrity/acceptance issues (DEV-01/02/06/14), not an inferred security vulnerability merely because exception handling is broad. Operator-selected graphs/DLLs/paths remain external artifacts whose provenance and compatibility need specific approval before promotion; no such artifacts were replaced or executed during review.

Performance: bounded Family Studio result queries are good, but disclose truncation (DEV-15); decoding details and several repository calls on selection still need representative latency. Refresh is synchronous and full; persistent status does not supply GUI cancellation. Beam loops compare every candidate against visible blockers; rotated-view geometry and blocker counts need profiling alongside DEV-12. Highlight rescans schedule instances per sheet and rereads schedule cell content; cache per-run shared collections if live measurements show a bottleneck. Steel fills thousands of formulas and fixed-position pivots, so correctness/source-range/capacity acceptance should precede optimization. None of these statements supplies an unmeasured runtime estimate.

Suggested authorized-review follow-up slices, after the user chooses implementation scope:

- Family Studio load result/identity and atomic batch tests first; then refresh/type-preview/result-count/browser error handling as separate changes.
- Concrete required-clear failure handling and exact template preflight with an adapter fixture.
- Steel checked-selection preservation and level-summary chart source; separately design recoverable history publication.
- Sheet transaction/report lifecycle, then Highlight unknown fingerprint status and Beam per-tag rollback/regeneration.
- Excel smoke late-stage retention/cleanup lifecycle and semantic prototype SPEC repair.
- Current starter-template cleanup can remain a separate low-priority maintenance change.

All live acceptance above remains pending. This review provides concrete implementation decisions and fixtures; it does not authorize model-writing trials or certify prototypes for production use.
