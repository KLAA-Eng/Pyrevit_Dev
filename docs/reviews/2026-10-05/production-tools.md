# Production command review — 2026-10-05

This review covers **all 19 commands in panels 01–04** of `KL&A Tools_dev.tab`. It is a source review of command behavior, specifications, bundle metadata, shared runtime helpers, and their existing tests. No command was run against the model, no workbook or external form was opened, and no runtime source was changed.

The reviewed baseline is commit `1562e96a5f6e23b7368c80e317868a0c059dc165`, extension identity `0.0.11-dev`. The coordinating review verified a connected Revit **2024**, build **24.3.50.51**, with IronPython **2.7.12**, .NET **4.8**, and pyRevit **6.5.3.26176+2017**. Those observations establish the installed environment; they do not establish command acceptance. Other Revit versions need their own acceptance evidence.

The most urgent findings are the Excel macro guard's error path and Highlight 2D's removal of existing graphics. Several other commands can omit requested work or report success without the corresponding change. The newer Carbon and visibility workflows have stronger cancellation and reporting boundaries, but their host integration still needs deliberate fixtures.

## Evidence and interpretation

Severity: **P1** means address before routine production use of the affected path; **P2** means a reproducible correctness issue for a supported workflow; **P3** means documentation or maintainability work. A confirmed source defect means the failing branch is demonstrable from current code, sometimes with a host-free probe. It does **not** mean the failure was observed in live Revit or Excel.

The coordinating review reports **195 Python tests run: 194 passed, one skipped, zero failed**, and the visible-tool metadata check reports **36 bundles, zero errors**. This production review additionally executed targeted in-memory source probes. These used extracted functions or the repository's existing revision-cloud stubs; they did not edit source files, add tests, or invoke Revit/Excel.

| Probe | Result | Meaning |
| --- | --- | --- |
| Highlight with no view-specific elements | `IndexError` | Its empty guard occurs after first-element indexing. |
| Highlight with a blue first-element override | No actions | The toggle has no branch for a valid non-red color. |
| Excel macro-security getter raises | `Workbooks.Open` still called | The macro precondition fails open. |
| Installed revision helper, issued-only selection | Empty saved revision list; one returned updated sheet | Selection exposure and update behavior disagree. |
| Installed revision helper, removal of an absent additional revision | Empty saved revision list; one returned updated sheet | Returned sheets do not distinguish changes from no-ops. |
| Hide-cloud schedule setter raises | `changed=1`, one error | Success counts advance before persistence. |
| View Range level setter raises | Returns true and reports success | Requested level change can be dropped. |
| Unhide one cloud hidden in two selected dependent views | Only view 21 targeted; view 22 omitted | Fallback stops at the first dependent. |

Autodesk's [PlanViewRange reference](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/7edc5f13-a5fa-5c7a-9a03-ac6cbed1f005.htm) documents `Current`, `LevelAbove`, `LevelBelow`, and `Unlimited`. The coordinating review read their values from installed Revit 2024: `Current=-3`, `LevelAbove=-2`, `LevelBelow=-4`, `Unlimited=-1`, and `InvalidElementId=-1`. **Unlimited equalling InvalidElementId is valid in this observed host; it is not a finding.** The special relative-level values are the actual missing case.

Installed pyRevit dependency behavior was read directly from `C:\Users\lmadden\AppData\Roaming\pyRevit-Master\pyrevitlib\pyrevit\revit\db\update.py`, lines 22–44. This installation detail is relevant to TOOL-04 and should be rechecked when pyRevit changes.

## Confirmed findings

### TOOL-01 — P1: Stop before opening a workbook when macro security cannot be established

**Confidence: high.** Evidence: [macro guard](../../../lib/excel_com.py#L152), lines 152–163, and [workbook opening](../../../lib/excel_com.py#L172), lines 172–193.

`_disable_automation_macros()` catches a failed read of `AutomationSecurity` and returns `None`. `open_workbook()` then opens the selected file without attempting the force-disable setter. This affects both Carbon workbook roles and any other consumer of the shared Excel boundary.

**Trigger:** an Excel PIA/IDispatch security-property read fails while the workbook itself remains openable. **Consequence:** a selected macro-enabled workbook can open without the safeguard promised by the command contract. The in-memory probe reproduced this: the getter threw and `Open` still ran. Microsoft documents that a newly started Excel application defaults to a mode that enables macros, and that `DisplayAlerts=False` does not substitute for macro security. [Microsoft Excel AutomationSecurity](https://learn.microsoft.com/en-us/office/vba/api/excel.application.automationsecurity).

**Recommendation:** require a successful force-disable operation before calling `Open`; propagate an explicit compatibility error when the security boundary cannot be established. Preserve the original state only after a successful read. Cleanup should still request Excel exit.

**Acceptance:** getter failure and setter failure must both prevent `Open`; normal PIA and raw-COM `.xlsx`/`.xlsm` opening must restore the previous security state. Use a trusted macro fixture to verify that an automatic VBA macro does not execute. Excel 4.0 macro prompts remain a separately documented limitation.

### TOOL-02 — P1: Highlight 2D clears graphics it does not own

**Confidence: high.** Evidence: [Highlight 2D](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Override 2D.smartbutton/script.py#L55>), lines 55–63 and 95–104; [fresh red override](../../../lib/graphics/overrides.py#L4), lines 4–8.

`clear_overrides()` assigns a completely empty `OverrideGraphicSettings` to every collected view-specific element. There is no snapshot of the previous settings and no marker identifying tool-owned state. The toggle decides to clear solely because the first element has a red projection-line override.

**Trigger:** the first element already has a user-created red override, or a Highlight/Clear cycle encounters pre-existing line weights, patterns, colors, transparency, or other graphics on any target. **Consequence:** Clear removes those settings along with the highlight. The clearing occurs after disabling the temporary mode, so an earlier temporary-mode restoration does not protect the subsequent empty-settings assignment.

**Recommendation:** define ownership explicitly and restore the exact previous settings for affected elements, or let a supported temporary display mechanism handle restoration without subsequently clearing element overrides. Do not infer ownership from a color.

**Acceptance:** first-click user-red graphics, mixed overrides, newly added/deleted elements between clicks, switching views, and a full toggle cycle must preserve every pre-existing setting. Verify temporary-view mode and Undo in Revit.

### TOOL-03 — P2: Highlight 2D fails on empty views and does nothing for a valid non-red first override

**Confidence: high.** Evidence: [main toggle](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Override 2D.smartbutton/script.py#L94>), lines 94–111, and the late [empty guard](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Override 2D.smartbutton/script.py#L38>), lines 38–52.

The main block reads `elements_set[0]` before checking that the collection is non-empty. Its `if plcolor.IsValid` branch only acts when that color is red; other valid colors have no action. Both behaviors were reproduced without the host.

**Trigger:** no view-specific elements, or a blue/green/etc. projection override on the first collected element. **Consequence:** an exception or a silent no-op instead of the advertised highlight behavior. Collector order also controls the state decision for the entire view.

**Recommendation:** validate the target collection first and use explicit tool state/ownership with a complete apply/clear policy. Reuse the existing safe graphics readers rather than assuming that an unset color is the only valid initial state.

**Acceptance:** empty collection, unreadable/unset color, each non-red color, mixed overrides, and changed collection order must produce a clear result without relying on first-item ordering.

### TOOL-04 — P2: Revision schedule toggles report no-ops as changes and Shift-click does not update issued revisions

**Confidence: high for the installed pyRevit version.** Evidence: [Turn on](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Revision.pulldown/Set Revision On Sheets.pushbutton/script.py#L8>), lines 8–32; [Turn off](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Revision.pulldown/Remove Revision From Sheets.pushbutton/script.py#L21>), lines 21–43; installed dependency `revit/db/update.py`, lines 35–43.

The installed `update_sheet_revisions()` skips every issued revision, then appends every processed sheet to its returned `updated_sheets`. Turn on uses that result as proof of additions. Turn off uses it as proof of removal and only classifies sheets absent from the return value as cloud-required. Shift-click exposes issued revisions in Turn on but the shared helper still ignores them.

**Trigger:** issued-only selections through Shift-click; already-added revisions; removal when the revision is absent from additional revisions; or a cloud-driven schedule entry. **Consequence:** the commands report selected revisions turned on/off even when no requested membership changed, and Turn off's intended cloud-required report is not reached with the normal helper result. The source probe returned an updated sheet for issued-only and no-op-removal cases.

**Recommendation:** compute before/after additional membership per sheet and classify changed, unchanged, issued-policy-skipped, cloud-required, and failed outcomes. Implement the intended issued-revision policy deliberately or remove the unsupported Shift-click instruction. If revising an imported tool, treat that as a maintained adaptation under the tool-version rules.

**Acceptance:** issued/unissued and mixed selections; absent/present additional membership; cloud-only and additional-plus-cloud cases; already-requested state; placeholders; cancellation; read-only/workshared sheets. Compare the resulting titleblock schedule, not only the returned helper list.

### TOOL-05 — P2: Unhide omits the second selected dependent view for the same hidden cloud

**Confidence: high.** Evidence: [hidden-cloud fallback](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Revision.pulldown/Hide Revision Clouds.pushbutton/script.py#L237>), lines 237–270, and [dependent targeting](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Revision.pulldown/Hide Revision Clouds.pushbutton/script.py#L284>), lines 284–294.

When a cloud is absent from the visible-sheet lists, the fallback records the first matching placed dependent's `sheet_values` and immediately breaks. It does not union the other selected sheets where the same cloud is independently hidden. Subsequent targeting is restricted to that first sheet set.

**Trigger:** select two sheets containing different dependent views of one primary owner; hide the same cloud independently in both dependents while it is not hidden in the primary. **Consequence:** Unhide only targets the first dependent and incorrectly lists the second sheet as having no matching cloud. The existing test stubs reproduced targets `[21]` for expected hidden views `[21, 22]`.

**Recommendation:** accumulate every selected sheet/dependent association for each fallback cloud before constructing target views. Preserve the existing owner-view policy, but avoid discarding distinct selected placements.

**Acceptance:** two and three placed dependents with mixed independent hidden states, owner hidden/not hidden, clouds outside one dependent crop, and duplicate cloud discovery must target each applicable view once. Confirm propagation and crop behavior in Revit.

### TOOL-06 — P2: Hide-cloud schedule counts increase before the sheet accepts the change

**Confidence: high.** Evidence: [schedule update](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Revision.pulldown/Hide Revision Clouds.pushbutton/script.py#L330>), lines 330–360, and [completion report](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Revision.pulldown/Hide Revision Clouds.pushbutton/script.py#L405>), lines 405–409.

`schedule_entries_changed` is incremented while editing the in-memory ID collection, before `SetAdditionalRevisionIds()` runs. The setter exception is recorded and the command continues, retaining those success counts.

**Trigger:** a sheet rejects the additional-revision write, for example because of permissions or a host failure. **Consequence:** the report simultaneously claims an entry was turned off and records the setter failure, overstating completed work. The probe returned `changed=1` with one write error.

**Recommendation:** accumulate tentative changes locally, then advance successful counts only after the setter succeeds. Report failed requested changes separately; final counts should reflect the committed transaction outcome.

**Acceptance:** one failed sheet among successful sheets, multiple requested revisions on a failed sheet, no-op memberships, and transaction failure must leave accurate changed/unchanged/failed totals.

### TOOL-07 — P2: View Range treats relative level references as missing planes

**Confidence: high.** Evidence: [available level list](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py#L313>), lines 313–345; [current selection](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py#L353>), lines 353–399; [plane lookup](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py#L449>), lines 449–466.

The level list contains Unlimited and actual Level elements. `Current`, `LevelAbove`, and `LevelBelow` are retained as negative IDs when reading the view range, but are absent from that list. `Document.GetElement()` cannot resolve them as actual Level elements, so the rendering path marks valid finite planes `N/A` and drops their offsets/elevations.

**Trigger:** a valid view-range plane references Associated/Current Level, Level Above, or Level Below. **Consequence:** missing selector matches, incorrect `N/A` display, and omitted colored planes for an otherwise valid view range.

**Recommendation:** model special relative references explicitly, resolve their effective levels/elevations against the source view, and preserve their semantics on apply/reset. The same resolver should serve display, ordering validation, and mutation.

**Acceptance:** actual levels, Current, Above, Below, Unlimited, missing adjacent levels, and a level added between existing levels. Verify exactly which references Revit returns and how they react to level changes in each claimed host version.

### TOOL-08 — P2: View Range can discard a requested level change and report success

**Confidence: high.** Evidence: [level writes](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py#L133>), lines 133–163, and [success message](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py#L191>), lines 191–195.

Both `SetLevelId()` exception handlers silently continue. The command then applies the remaining range and reports `View range updated successfully`. A mocked rejected level setter reproduced a true return and the success message.

**Trigger:** a requested plane/level combination is rejected while other values remain valid. **Consequence:** the selected level is omitted and other offsets may still be committed without telling the user which request failed.

**Recommendation:** build and validate a complete proposed range before mutation; do not swallow level assignment errors. Either reject the proposal atomically with a useful message or explicitly report partial outcomes under a documented contract. Announce success after commit completes.

**Acceptance:** rejected level, invalid ordering, template-controlled range, read-only view, mixed valid/invalid edits, and a failed commit. Confirm resulting API values against the user's exact requested values.

### TOOL-09 — P2: Section preview draws depth and cut faces before applying the cut-plane translation

**Confidence: high for the geometry logic; visual consequence unverified in Revit.** Evidence: [section branch](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py#L519>), lines 519–538, and [accepted source types](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py#L978>), lines 978–979.

The section branch emits both plane meshes from the same `cut_plane_vertices`. Only after the Cut iteration has emitted its edges/triangles does it compute the translation intended to move the cut plane. That translated list is never rendered.

**Trigger:** a section source with nonzero crop-box depth. **Consequence:** cut and depth faces are generated at the same location instead of showing their intended separation; the colored preview can mislead the user.

**Recommendation:** derive the two vertex sets first, then render each at its intended section position. Extract that geometry into deterministic helpers so rotated section boxes and view directions can be tested.

**Acceptance:** shallow/deep sections, positive/negative viewing directions, rotated section boxes, and a numeric comparison of cut/depth face coordinates, followed by rendered Revit review.

### TOOL-10 — P2: Duplicate Sheets commits omitted viewports without an outcome report

**Confidence: high.** Evidence: [view duplication and placement](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/duplicate_sheets.pushbutton/script.py#L267>), lines 267–290, and [outer transaction](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/duplicate_sheets.pushbutton/script.py#L613>), lines 613–616.

After creating and renaming a duplicate view, the tool catches every exception from viewport placement/type assignment and does nothing. Processing continues and the outer transaction commits. The tool produces no completion report identifying the omitted viewport or the unplaced duplicate view it created.

**Trigger:** `Viewport.Create()` or its subsequent type assignment fails for a selected source viewport. **Consequence:** the new sheet is incomplete and an unplaced duplicate can remain in the model without an explanation. This conflicts with the adjacent SPEC's generic no-partial-changes claim.

**Recommendation:** define per-sheet atomicity or a deliberate best-effort contract; use guarded transaction/subtransaction scopes and retain exact outcomes for each sheet/view. Under atomicity, roll back the duplicate view when placement fails. Under best effort, report every omission and leftover.

**Acceptance:** a placement failure midway through a sheet, an unsupported duplication option, a worksharing restriction, and several sheets with one failing source. Verify no unexplained duplicates and accurate counts; cancellation must precede model writes.

### TOOL-11 — P2: Legend copying assumes a source-to-destination ID correspondence that the API does not promise

**Confidence: high.** Evidence: [copy and override loop](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Copy Legends to Other Documents.pushbutton/script.py#L131>), lines 131–144.

The command zips `CopyElements()`' returned ID collection with its input ID list and transfers graphics by position. Autodesk describes the result as newly created elements **including dependencies**; it does not provide an ordered source/destination correspondence. The collection may therefore contain additional IDs, and positional pairing cannot reliably identify the corresponding copied element. Actual return ordering and misapplied overrides were not measured in live Revit; the finding is the unsupported mapping assumption in the implementation. [Autodesk copying-elements guide](https://help.autodesk.com/cloudhelp/2016/ESP/Revit-API/files/GUID-3ABACFE3-EC8F-4D5C-ACC6-48A7E6C333A6.htm).

**Trigger:** copying elements with generated dependent elements or a result ordering that differs from input. **Consequence:** overrides can be assigned to the wrong created element, and some copied elements may never receive their intended override.

**Recommendation:** implement an explicit, tested correspondence strategy appropriate to supported legend contents. Do not treat the returned collection as ordered pairs. If reliable mapping is unavailable, disclose that individual overrides are not preserved and define supported content accordingly.

**Acceptance:** distinct graphics on multiple element types, a source with dependencies, tags/group-like content where supported, and cross-document type-name collisions. Compare each corresponding element in the resulting legend.

### TOOL-12 — P2: Legend-copy completion counts selections rather than actual copies

**Confidence: high.** Evidence: [empty-view skip](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Copy Legends to Other Documents.pushbutton/script.py#L113>), lines 113–121, and [success report](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Copy Legends to Other Documents.pushbutton/script.py#L181>), lines 181–208.

Empty legends are skipped, but `legend_count` is always `len(legends)` and the report lists every selected legend under COPIED. A destination with a base legend is treated as processed even if every selected source legend was empty.

**Trigger:** select an empty source legend or one with no accepted elements. **Consequence:** the modal report says a legend was copied successfully when no new legend exists. Destination classification by `doc.Title` also merges the status of distinct open documents sharing a title.

**Recommendation:** record successful, skipped, failed, and cancelled operations by document identity and source legend ID. Derive the report from that ledger. Surface partial completion across documents if a later document is cancelled or fails.

**Acceptance:** all-empty and mixed-empty selections, destination without a base legend, two destinations with equal titles, and cancellation after one destination has committed. Report only verified copies.

## Complete command inventory and live acceptance matrix

Every row's script, adjacent `bundle.yaml`, and adjacent `SPEC.md` was read. Versions below are the current independent tool versions, not extension versions. A row with no confirmed finding is not an acceptance claim. `T01–T19` are inventory references for this review only.

| Ref / command / physical bundle | Version and origin | Behavior and UI | Source assessment | Required live acceptance |
| --- | --- | --- | --- | --- |
| T01 — [Gen Notes / TYP DTLS](<../../../KL&A Tools_dev.tab/01 KL&A Resource Links.panel/Launch Gen Notes Typ Details.pushbutton/script.py>) — `01 KL&A Resource Links.panel/Launch Gen Notes Typ Details.pushbutton` | `v1.0`, KL&A | Opens a fixed `studio://` Bluebeam Session through Windows; zero-document context. | No Revit mutation. Fixed URL avoids user-input shell construction. No launch failure handling. Tooltip discloses Studio-session switching; SPEC effects still generic. | Handler installed/missing; authenticated/unauthorized access; existing Bluebeam session; multiple instances; zero document; endpoint identity. |
| T02 — [RVT Stds / OneNote](<../../../KL&A Tools_dev.tab/01 KL&A Resource Links.panel/Launch Revit Standards.pushbutton/script.py>) — `01 KL&A Resource Links.panel/Launch Revit Standards.pushbutton` | `v1.0`, KL&A | Opens the fixed KL&A SharePoint notebook `onenote:` URI; zero document. | No Revit mutation. No launch/access result handling. Endpoint validity was not tested by opening the private resource. | OneNote handler present/absent; sign-in/access denial; offline; correct notebook; zero document. |
| T03 — [Hide/Unhide Eng Notes](<../../../KL&A Tools_dev.tab/02 KL&A Tools.panel/Hide Engineering Notes.pushbutton/script.py>) — `02 KL&A Tools.panel/Hide Engineering Notes.pushbutton` | `v1.1`, KL&A beta | Native Hide/Unhide chooser; scans matching TextNotes in eligible sheet/placed-view relationships; one best-effort transaction; pyRevit report; Shift diagnostics. | Clear four-outcome contract. Cancel before scan/transaction. Owner plus placed-dependent changes are intentional. Batch failure/commit, whole-model scan, no dedicated behavioral tests, and zero-change explanation need scrutiny. | Each supported view type; prefix/apostrophe normalization; eligible/excluded sheets; direct/primary/dependent ownership; cropped notes; already hidden; failures; Undo; startup without dialog. |
| T04 — [Carbon GWP Pull](<../../../KL&A Tools_dev.tab/02 KL&A Tools.panel/Carbon GWP Pull.pushbutton/script.py>) — `02 KL&A Tools.panel/Carbon GWP Pull.pushbutton` | `v1.0`, KL&A beta | Active unique SYNC TO CENTRAL sheet; shared schedule selector; two workbook pickers; exports three schedules; refresh/read-only analyst workbook; renders two PNGs; updates marked imported images in one transaction; report. | TOOL-01. Strong pre-write cancellation, same-path rejection, export-save boundary, macro policy, positive data checks, ownership guards, and retained run folders. Remaining Excel/ownership risks detailed below. | Trusted XLSX/XLSM; all cancellation points; PIA/raw COM; Power Query/link failure/timeout; correct workbook linkage; case collisions; first/rerun/shared/copied images; ambiguous titleblocks; permissions; Undo/reopen; visual charts. |
| T05 — [Find and Replace in Views](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton/script.py>) — `03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton` | `v1.2.EFTools`, special import | Shared RenameViews WPF; preselected or chosen views; find/replace/prefix/suffix; transaction with per-view exception capture. | Explicit partial success through `try_except`; traceback only, no clear outcome ledger/preview. Generic SPEC misses mutation and GUI. Selection includes templates and broad view types. | Duplicate/invalid names; collision order; template/unsupported views; read-only/workshared targets; cancellation; repeated Run; non-ASCII; partial errors and Undo. |
| T06 — [Find and Replace in Sheets](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton/script.py>) — `03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton` | `v1.0`, KL&A adaptation | Shared RenameSheets WPF; transforms names/numbers; up to five write attempts with `*`/`_` suffix fallback; browser hide/show refresh. | Failure outcomes and adjusted names are silent. Raw transaction has no try/finally rollback; browser operation happens before commit. Number swaps can receive suffixes rather than requested identities. Generic SPEC falsely says no mutation. | Valid/duplicate/invalid/empty names and numbers; swaps/cycles; placeholders; permissions; browser refresh failure; repeated Run; unchanged names; rollback/Undo and accurate reporting. |
| T07 — [Find All Revised Sheets](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Revision.pulldown/Find All Revised Sheets.pushbutton/script.py>) — `03 Core Tools.panel/Revision.pulldown/Find All Revised Sheets.pushbutton` | `v1.0.pyRevit`, special import | Read-only output of revisions and sheets; sheet-number sorting; union of schedule/additional revision IDs. | No writes. Set iteration does not preserve revision sequence order. Whole-document report and empty-result usability remain observational risks. | Cloud/additional/both membership; per-sheet/per-project numbering; issued revisions; placeholders; empty model; output links and ordering. |
| T08 — [Find All Revision Clouds](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Revision.pulldown/Find All Revision Clouds On Views.pushbutton/script.py>) — `03 Core Tools.panel/Revision.pulldown/Find All Revision Clouds On Views.pushbutton` | `v1.0`, KL&A adaptation | Read-only per-sheet cloud IDs; reports sheet/direct/dependent placement; revision-sequence sorting; clickable IDs. | Stronger placement logic and dedicated stubs. English parameter-name lookups and missing-parameter `.AsValueString()` are compatibility risks; dependent labels can list all placed dependents without proving each crop contains the cloud. | Sheet/direct/primary/multiple-dependent clouds; crops; hidden/issued/no-cloud cases; custom numbering; missing/localized parameters; output link selection. |
| T09 — [Toggle on Revision Schedule](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Revision.pulldown/Set Revision On Sheets.pushbutton/script.py>) — `03 Core Tools.panel/Revision.pulldown/Set Revision On Sheets.pushbutton` | `v1.0`, KL&A adaptation | Native revision/sheet selectors; Shift-click exposes issued revisions; one pyRevit transaction; text report. | TOOL-04. No own before/after outcome policy; installed helper semantics determine behavior. | Issued policy, added/already-present/cloud-only revisions, placeholders, cancelled selectors, worksharing/read-only failures, transaction result, Undo. |
| T10 — [Toggle off Revision Schedule](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Revision.pulldown/Remove Revision From Sheets.pushbutton/script.py>) — `03 Core Tools.panel/Revision.pulldown/Remove Revision From Sheets.pushbutton` | `v1.0`, KL&A adaptation | Native revision/sheet selectors; removes additional memberships; attempts to distinguish cloud-required sheets. | TOOL-04. Report cannot infer cloud removal from installed helper return values. | Issued/mixed revisions; cloud-only/additional-only/both/absent memberships; placeholders; cancellation; permissions; schedule appearance and Undo. |
| T11 — [Hide/Unhide Revision Clouds](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Revision.pulldown/Hide Revision Clouds.pushbutton/script.py>) — `03 Core Tools.panel/Revision.pulldown/Hide Revision Clouds.pushbutton` | `v1.0`, KL&A custom | Native action chooser; unchecked shared revision/sheet lists; owner/dependent visibility; Hide removes selected additional memberships even without clouds; Unhide leaves schedule membership alone; report. | TOOL-05/06. Intentional best-effort transaction, owner-view scope and asymmetric schedules. Several state-query exceptions are reduced to counts; schedule update proceeds even after cloud errors. | Multi-dependent fallback; crop/issued/grouped clouds; failed state/hide/schedule calls; all result classes; no-cloud schedule changes; Cancel; Undo; effect on other sheets sharing an owner. |
| T12 — [Highlight 2D](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Override 2D.smartbutton/script.py>) — `03 Core Tools.panel/Override 2D.smartbutton` | `v1.0`, KL&A adaptation | Smartbutton passive icon initializer; collects view-specific elements; red graphics toggle and temporary mode; config/icon; transaction group. | TOOL-02/03. Import closes other output windows. First-element state and existing temporary mode need ownership handling. | Empty/mixed overrides; user-red first element; unsupported active views; sheet temporary isolation; switching/reloading; graphics preservation; icon/config; Undo. |
| T13 — [Duplicate Sheets](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/duplicate_sheets.pushbutton/script.py>) — `03 Core Tools.panel/duplicate_sheets.pushbutton` | `v1.0`, KL&A adaptation | Shared sheet selector then options WPF; copies selected views/legends/schedules/annotations/imports/revisions; naming rules; one raw transaction spans selectors/dialog. | TOOL-10. Initial titleblock type only, no instance parameters/location/multiple-titleblock preservation. Naming retry failures silent. Whole-document schedules/titleblocks re-collected per sheet; no result report. | Each checkbox/duplication mode; titleblock count/location/parameters; viewport labels/type; split schedules; template/3D/dependent views; invalid naming; failures/cancellation; source unchanged; no stray views; Undo. |
| T14 — [Show View Range](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py>) — `03 Core Tools.panel/ViewRange.pushbutton` | `v1.0`, KL&A adaptation | Persistent modeless WPF with reactive fields; Project Browser selection and view/document events; DirectContext3D preview; ExternalEvent Apply; Reset to Original. | TOOL-07/08/09. Context, relative levels, units, asynchronous request snapshots, document identity, reset semantics and cleanup require focused tests. Metadata advertises Revit 2023 while repo target is 2024+. | Actual/relative/unlimited levels; plans/RCP/sections; unit precision; active-document switching; quick Apply/selection changes; pending event after close; Reset; commit/permissions; multiple launches; preview/cleanup; exact supported versions. |
| T15 — [Copy legends to other documents](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Copy Legends to Other Documents.pushbutton/script.py>) — `03 Core Tools.panel/Copy Legends to Other Documents.pushbutton` | `v1.0.pyRevit`, special import | Native destination/view pickers; cancellable progress; requires destination base legend; duplicates base, copies contents, transfers overrides, unique names; per-document group; modal result. | TOOL-11/12. Raw transactions are unguarded against copy/rename failure; earlier destination groups remain committed if a later group fails/cancels. Imported German tooltip disallows legend components; English tooltip does not. | Empty/full legends; legend components/content policy; overrides/dependencies; no base legend; duplicate names; equal destination titles; read-only/family docs; failure/cancellation after earlier success; Undo per document. |
| T16 — [Who did that??](<../../../KL&A Tools_dev.tab/03 Core Tools.panel/Who Did That.pushbutton/script.py>) — `03 Core Tools.panel/Who Did That.pushbutton` | `v1.0.pyRevit`, special import | Native switch offers active-view creator, selected-element history, keynote reload ownership; alerts. | Read-only. Active-view option lacks the workshared gate used by others. TransmissionData failures all reported as unsaved model; current ownership is presented as last reload, though it is not a historical reload log. | Workshared/non-workshared models; exactly-one/multiple/no selection; local/central/cloud/unsaved files; missing/unowned keynotes; accurate interpretation of ownership vs history. |
| T17 — [About KL&A Tools](<../../../KL&A Tools_dev.tab/04 Outreach.panel/About KL&A Tools.pushbutton/script.py>) — `04 Outreach.panel/About KL&A Tools.pushbutton` | `v1.1`, KL&A | Zero-document alert of generated identity/channel/source SHA/date, loaded path, Revit/pyRevit build. | Clear provenance labels and library resolution. Generated SHA intentionally differs from current HEAD; adjacent SPEC explains it. No confirmed defect. | Zero/open document; loaded clone path; generated identity vs release tag; actual pyRevit version; missing metadata handling and readable dialog/copy behavior. |
| T18 — [Suggestions/Bugs Feedback](<../../../KL&A Tools_dev.tab/04 Outreach.panel/Suggestions.pushbutton/script.py>) — `04 Outreach.panel/Suggestions.pushbutton` | `v1.0`, KL&A | Zero-document native report-type + subject prompts; URL-encodes five configured prefill fields; launches Microsoft Form; user submits in browser. | Cancel before launch. Only report type, subject, username, build, workshared status are sent; document path/title/machine are collected but not in FIELD_MAP. No automatic submission. No launch/prefill result handling; SPEC omits external effect. | No document; cancellation both prompts; Unicode/symbol subjects; current Form field IDs; access denial; default browser missing; intended prefill values; browser submission by user. |
| T19 — [Prototype Request](<../../../KL&A Tools_dev.tab/04 Outreach.panel/Prototype.pushbutton/script.py>) — `04 Outreach.panel/Prototype.pushbutton` | `v1.0`, KL&A | Zero-document fixed Microsoft Form URL launcher; no context or form submission. | Small, clear adapter and accurate effects in SPEC. Missing handler/access failures unhandled. No confirmed defect. | No document; correct active Form/tenant; permissions/sign-in; missing browser/offline; user completes form separately. |

## Cross-command risks and recommended design work

These are review observations and acceptance gaps, not additional claims of demonstrated host failures.

### Transactions, cancellation and partial results

- **Rename Sheets** owns a raw transaction around both name/number writes and a browser refresh. It needs guaranteed rollback/disposal and an explicit commit result. Its five retry variants may change requested identifiers without any output. **Rename Views** deliberately suppresses per-view exceptions and commits successful peers, but reports tracebacks instead of a concise changed/skipped/failed ledger. A two-phase planned-name mapping would also make number/name swaps predictable.
- **Duplicate Sheets** starts a transaction before selection and holds it across the options dialog. Its WPF Run callback closes the window before model work. Move validated input collection before transaction start and use a small adapter over a testable copy plan. Define per-sheet atomicity before implementing partial handling.
- **Copy Legends** manually starts transactions/groups without a general exception-safe cleanup path. Its cancellation only rolls back the current document group; already assimilated destination groups remain changed. This should be described and reported as partial completion, with precise document IDs.
- **Hide Engineering Notes** and **Hide Revision Clouds** collect success counts before the final enclosing transaction is known to have committed. Confirm failure behavior of the installed pyRevit transaction wrapper and fail/report accordingly. The engineering-note command batches all valid notes in a view; a failing batch does not attempt each remaining note separately. Verify that this fulfills the stated best-effort policy for relevant failure types.
- **Hide Revision Clouds** mutates a primary owner even when the selected placement is a dependent and schedules are only changed for selected sheets. Other placements sharing that owner can be affected. The SPEC states this owner policy, but live fixtures and action-dialog wording should make its reach reviewable.

### View Range state and version boundaries

- `context_changed()` clears the supposedly original offset/level dictionaries on **every** refresh (lines 406–409), including after Apply (line 193) and document-change events (line 960). The `Reset to Original` label could mean launch-time originals or current committed values; choose and document the intended meaning, then snapshot at that boundary. Offsets are rounded to two display decimals before originals are saved (lines 480–493), so a no-op Apply may lose finer precision.
- Queued update requests store a mutable `Context` reference, not a frozen source-document/view identity (lines 127–130). A changed selection before execution can direct the edit at the then-current source view. `_update_view_range_internal()` uses `revit.doc` for the transaction while operating on `source_view`; active/source views are not required to belong to the same document. Test document switches and fast queued actions before accepting this modeless editor.
- A pending refresh event can change the active view and selection (lines 912–921), including while the window is closing. External-event pending/denied outcomes are not checked. Test lifecycle races, repeated launches, and closed-window pending events.
- The ordering validator uses a single top/cut/bottom/depth ordering and skips all comparisons when it has fewer than four elevations (lines 252–254). Revit API validation must remain authoritative for partial/unlimited references, reflected ceiling plans, and template-controlled ranges. Do not rely on the custom ordering alone.
- The selection event's `ProjectBrowser` gate (lines 932–945), active graphical view, document events, and DirectContext3D cleanup require a real browser-selection test. This review did not infer acceptance from the handler names. `min_revit_version: 2023` conflicts with the stated repository design target of 2024+; clarify the supported baseline before claiming 2023 support.

### Carbon GWP and external inputs

- The current command now retains PNGs in a unique run folder and force-disables automation macros on the normal opening path. Older memory of overwrite behavior or unrestricted macro opening should not be used to describe the current main path. TOOL-01 concerns the security property's **error path**.
- Workbook roles are rejected by normalized string equality only (lines 886–897); equivalent network aliases/hard links are not identified. The SPEC explicitly states that the command does not validate formula/Power Query linkage between the chosen workbooks. A fresh refresh can still read data from another container if the analyst workbook is configured differently.
- Query-state inspection tolerates unavailable COM properties/collection reads (lines 600–678). A false negative can make the wait believe refresh is complete even though the inspector could not determine that. Add probes for unreadable connection/table state and confirm the asynchronous-calculation boundary in Excel. A fixed 60-second polling limit does not bound a blocking `RefreshAll()` or calculation COM call.
- Excel settings are applied before the local `try/finally` in both export and reader (lines 496–507 and 748–753); a settings failure during application creation/setup can leave cleanup unattempted. Macro-state restoration failure after `Open` also needs explicit workbook ownership cleanup. `Quit` requests exit, but does not itself prove every COM reference/process released.
- Schedule values are written one cell at a time as `Value2` strings (lines 391–395). This creates many COM boundary calls and allows Excel to interpret formula-like text. Treat schedule content as data; define whether literal strings or formulas are expected and use a bulk rectangular write with the appropriate format. Benchmark representative large schedules before claiming performance.
- Managed image ambiguity checks are appropriately conservative, but existing Python chart tests cover renderer overload shape and corner helpers rather than the full marker/type-sharing/reload lifecycle. Add host-free ownership-path fixtures and live create/rerun/copy/reopen/Undo checks. A later model failure leaves the already-saved export workbook and generated files, which the report should state clearly.
- The run-folder retention policy has no cleanup policy. This is deliberate evidence preservation, but long-running project use can accumulate large PNGs. Document ownership and a user-controlled retention procedure.

### Shared presentation, metadata and specifications

- All 19 visible production commands have script titles/versions, bundle author/versioned English tooltip, and adjacent identity/history SPEC sections. The coordinating metadata audit passed. This is a structural result, not a semantic documentation pass.
- Most Core Tools SPECs are generated inventories rather than usable contracts. For example, both rename SPECs say no direct mutation was detected despite parameter writes; Rename Views says no GUI was detected despite its shared WPF base. Duplicate Sheets promises no partial changes without a corresponding atomicity policy. Describe real inputs, transaction scope, supported content, collision behavior, cancellation, and outcomes.
- Carbon's [SPEC](<../../../KL&A Tools_dev.tab/02 KL&A Tools.panel/Carbon GWP Pull.pushbutton/SPEC.md#L113>) contains consecutive statements saying each run replaces stable PNGs and also saying it writes a new timestamped folder without replacing earlier files. The latter matches current code; remove the contradictory replacement statement during a documentation fix.
- View Range's tooltip presents it as a visualizer while its dialog can change view ranges. Its SPEC inventory lists the setter but does not explain the Apply workflow, input units, reset policy, document scope, or persistence.
- Resource launcher SPECs and Suggestions still claim no external effect was detected. They open external applications/URLs. Suggestions sends user/build/workshared context in the URL; list those exact fields rather than the unused context collected by the script. These URLs were not opened or tested during the review.
- Shared selectors preserve hidden checked items when filtering and now support explicit empty defaults; existing selector tests cover those important contracts. Rename/Duplicate selectors retain the first-sorted default and include broad view/sheet sets. Confirm intentional defaults, placeholder/template eligibility, keyboard behavior, and the selected-item summary before mutation.
- Graphical settings already have safe readers and predicates in [graphics helpers](../../../lib/graphics/overrides.py), but Highlight 2D only reuses the fresh-red builder. Reuse the established helpers while implementing ownership; avoid another copy of color/state rules.

## Shared helper coverage and test priorities

| Helper | Reviewed responsibility | Existing evidence / next useful tests |
| --- | --- | --- |
| [carbon workflow](../../../lib/carbon_gwp/workflow.py) | Text/grid normalization, schedule cleanup, worksheet names and unique suffixes | Good deterministic coverage. Add truncated-apostrophe names and collision against existing workbook names differing only by case. |
| [carbon chart data](../../../lib/carbon_gwp/chart.py) | Positive finite values, per-measure skips, colors/labels, totals/formatting, size | Good row parsing coverage. Test extreme totals, long/non-ASCII labels, and actual layout with rendered fixtures. |
| [carbon Revit charts](../../../lib/carbon_gwp/revit_chart.py) | Drawing resources, marker schema, ownership, type sharing, import/reload, anchoring | Only two focused tests in its dedicated test module; important ownership branches remain unproven by those tests. Add fake ownership/reload outcomes, then live image API acceptance. |
| [Excel boundary](../../../lib/excel_com.py) | PIA/IDispatch operation shape, optional arguments, macros, workbook lifecycle | Existing tests cover direct/raw dispatch and cleanup. Some replace macro guards with lambdas; add actual getter/setter/restoration failure tests for TOOL-01. |
| [selection](../../../lib/Snippets/_selection.py) | Preselection/fallback lists for Views/Sheets | Runtime globals/default UIDocument and broad dictionaries couple it to loaded host state. Extract input eligibility/labels from presentation and test active-document changes and explicit defaults. |
| [context managers](../../../lib/Snippets/_context_manager.py) | Per-item exception suppression and transaction commit/rollback | Rename Views intentionally commits after item failures. Test/report this contract; inspect commit status and avoid swallowing outcomes needed by the UI. |
| [RenameViews base](../../../lib/Renaming/BaseClass_FindReplace.py), [RenameSheets UI](../../../lib/GUI/RenameSheets.py), [DuplicateSheets UI](../../../lib/GUI/DuplicateSheets.py) | Shared resources, WPF input properties, callback wiring | Reviewed event-to-command flows. Layout/accessibility is covered separately by the design/GUI review. Add tests around repeated Run, Cancel, and callback failures after transaction refactoring. |
| [SelectFromDict](../../../lib/GUI/SelectFromDict.py), [GUI facade](../../../lib/GUI/forms.py) | Canonical selection, search filtering, explicit initial choices, resources | Shared selection invariants have tests. Host globals and import-time document access limit zero-document/general reuse; remain explicit about supported context. |
| [graphics](../../../lib/graphics/overrides.py) | Fresh red override, safe property reads, red/existing-graphics detection | Predicate tests do not test Highlight 2D's command toggle. Add meaningful command-state/restore tests rather than more builder-only checks. |
| Installed pyRevit revision update/selectors/events | Issued revision policy, return values, active selection filtering, event unregistration | Read current installed source. TOOL-04 needs integration tests against actual helper semantics; event cleanup is scoped by execution ID in this installation. |

Hide Engineering Notes has no dedicated behavior test module in the current inventory. Its SPEC explicitly defers deterministic extraction. Keep that future work focused: extract normalization, eligibility decisions and outcome classification, then verify best-effort error handling with host stubs and a representative Revit fixture. Do not replace host acceptance with those tests.

## Suggested implementation order

1. Close TOOL-01 and TOOL-02 with narrow fixes and meaningful failure/preservation tests. Their acceptance must include trusted Excel macro fixtures and existing Revit graphics.
2. Repair the revision result contract and multi-dependent Unhide behavior (TOOL-04/05/06). Test the installed dependency policy rather than assuming its return values prove a change.
3. Make View Range's level model and complete-proposal validation explicit (TOOL-07/08), then correct section geometry (TOOL-09). Freeze source identity when queuing modeless edits and define Reset before adding more UI behavior.
4. Introduce explicit copy outcomes and safe transaction scopes for Duplicate Sheets and Copy Legends (TOOL-10/11/12), plus the Highlight edge cases (TOOL-03).
5. Replace generic and contradictory production specifications with actual workflows/effects. Record the live matrix results with exact Revit/pyRevit/Excel versions before expanding support claims or promoting beta workflows.

This document proposes work for review. It does not implement fixes, approve release readiness, or record live acceptance of any command.
