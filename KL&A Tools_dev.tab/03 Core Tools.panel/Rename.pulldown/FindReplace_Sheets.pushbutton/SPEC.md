# FindReplace_Sheets

| Field | Value |
| --- | --- |
| Tool ID | `core.rename.findreplace-sheets` |
| Former prototype Tool ID | `devsandbox.findreplace-sheets-proto` |
| Tool version | `v1.1` |
| Status | Unreleased |
| Status/origin | KL&A-maintained Core command promoted from an EFTools-derived DevSandbox prototype. |
| Main delivery | Unreleased |
| Path aliases | Core release layout: `KL&A Tools.tab/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton`; current `KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton`; former prototype: `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton`, `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton` |
| Version inputs | Core `bundle.yaml`, `script.py`, `Script.xaml`; former prototype bundle files; `lib/find_replace/workflow.py`, `lib/find_replace/revit_batch.py`, `lib/find_replace/window.py`; `lib/Snippets/_selection.py`; `lib/GUI/Resources/WPF_styles.xaml` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v1.1.EFTools | 0.0.5.beta | 08.20.2026 | The parallel DevSandbox prototype first delivered unchanged EFTools 1.1 behavior. | `8cd45f8` |
| v1.0 (Core); v0.0 (prototype) | 0.0.6beta | 09.15.2026 | The Core button first delivered KL&A's sheet UI/resource adaptation; the prototype separately delivered its first local WPF/resource adaptation in the same release. | `300f8d4` |
| v1.1 | Unreleased | 10.09.2026 | Promote the prototype to the existing Core button with exact-value title/number changes, per-sheet rollback, unchecked ID-free picker, case buttons, and in-dialog outcomes. The prototype's planned v0.1 work is included in this delivery. | `6444c8d` and working-tree promotion; pending next main delivery. |

This is one chronological history for the surviving Core identity and its
retired prototype path. The 0.0.6beta row records both versions delivered in
parallel. The prototype's `v0.1` was planned on `dev` but never became a
separate main delivery; its changes are included in Core `v1.1`.

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Purpose

Rename selected sheet titles and numbers with case-sensitive Find/Replace,
Prefix, and Suffix, or change sheet-title case directly.

## Behavior

The command uses selected sheets from the Project Browser or offers a sheet
picker with no rows checked initially. Its visible labels show sheet number and
name, without element IDs. The existing SheetNumber and SheetName columns
remain. Uppercase and Lowercase apply to sheet titles only; sheet numbers are
unaffected.

Actions apply immediately to the full selection's current values. Rename
requires Find text when Replace is nonempty and keeps matching case-sensitive.
Each rerun recomputes from current values, including repeated prefixes or
suffixes. Requested sheet numbers that are already occupied, swapped with
another selected sheet, or duplicated within the batch are skipped. No `*` or
`_` fallback is added to a requested value.

One parent Revit transaction gives the batch one Undo item. A subtransaction
changes a sheet's title and number together or rolls both back if either fails.
Other valid sheets may still change. The dialog closes quietly when the action
succeeds. Rename with no changes stays open. Skipped or failed items expand an
in-dialog result area with counts and reasons; controls remain available for a
full rerun. Results for the same action are replaced on rerun while unresolved
results from other actions remain visible.

## Validation boundary

Static Python/XAML checks and host-independent tests support this prototype.
The owner approved the visual review on 10.09.2026. Live acceptance in Revit
2024, 2025, and 2026 remains required: duplicate or invalid titles and numbers,
swaps, read-only/workshared sheets, cancellation, reruns, partial results, Undo,
quiet success, and Project Browser display.

## Implementation inventory

- Entry point: `script.py`
- Selection and WPF: local `script.py` and `Script.xaml`, with `get_selected_sheets` and shared WPF styles.
- Planning, Revit transaction handling, and result presentation: `lib/find_replace/`.
- Bundled external assets: None.

## GUI and interaction

The local XAML uses shared KLCode brushes, wordmark, header, action buttons, and
footer styles. The original labels and direct case buttons remain. A result
panel is collapsed initially and appears only for no-change Rename or
unresolved items. No preview or success popup is used. The footer version is
set from `__version__` when the dialog loads.

## Current execution logic

`script.py` computes exact targets and rejects initially occupied or repeated
sheet-number targets. `apply_batch` uses a parent transaction with one
subtransaction per changing sheet. It checks commit status and rolls back the
parent on failure. The command attempts its Project Browser refresh only after
a committed change.

## Model and external effects

Changes `ViewSheet.Name` and `ViewSheet.SheetNumber` for Rename, or
`ViewSheet.Name` only for case conversion. It does not write files or contact
external services except when a footer link is clicked.

## Current status

Promoted to the existing Core button on `dev`; the DevSandbox bundle was retired.
The visual review is approved, and live Revit 2024, 2025, and 2026 acceptance
remains pending before release.
