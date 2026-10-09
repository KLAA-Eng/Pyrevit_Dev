# FindReplace - Views

| Field | Value |
| --- | --- |
| Tool ID | `core.rename.findreplace-views` |
| Former prototype Tool ID | `devsandbox.findreplace-views-proto` |
| Tool version | `v1.0` |
| Status | Unreleased |
| Status/origin | KL&A-maintained Core command promoted from an EFTools-derived DevSandbox prototype. |
| Main delivery | Unreleased |
| Path aliases | Core release layout: `KL&A Tools.tab/03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton`; current `KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton`; former prototype: `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton`, `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton` |
| Version inputs | Core `bundle.yaml`, `script.py`, `Script.xaml`; former prototype bundle files; `lib/find_replace/workflow.py`, `lib/find_replace/revit_batch.py`, `lib/find_replace/window.py`; `lib/Snippets/_selection.py`; `lib/Renaming/BaseClass_FindReplace.py`; `lib/GUI/Resources/WPF_styles.xaml` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v1.2.EFTools | 0.0.0.beta | 07.16.2026 | Unchanged EFTools 1.2 Core command entered the first mainline delivery. | Upstream header; `484924b`; import `6a46157` |
| v1.2.EFTools | 0.0.5.beta | 08.20.2026 | The parallel DevSandbox prototype first delivered the unchanged EFTools 1.2 behavior. | `8cd45f8` |
| v0.0 | 0.0.6beta | 09.15.2026 | The prototype first delivered KL&A-local WPF/resource and case-button changes; the Core command stayed at v1.2.EFTools. | `300f8d4` |
| v1.0 | Unreleased | 10.09.2026 | Promote the prototype to the existing Core button with exact-value batch rename, case conversion, unchecked ID-free picker, and in-dialog outcomes. The prototype's planned v0.1 work is included in this delivery. | `6444c8d` and working-tree promotion; pending next main delivery. |

This is one chronological history for the surviving Core identity and its
retired prototype path. The prototype's `v0.1` was planned on `dev` but was
never a separate main delivery; its changes are included in Core `v1.0`.

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Purpose

Rename selected Revit views with case-sensitive Find/Replace, Prefix, and Suffix,
or convert view names with direct Uppercase and Lowercase buttons.

## Behavior

The command takes selected views from the Project Browser. With no eligible
selection it offers individual non-template views in a picker with no rows
checked initially. Element IDs are hidden; equal names are distinguished by
view type and, when needed, a sequence number. A template is eligible when
explicitly selected in the Project Browser. Sheet views are excluded.

Actions apply immediately to the full selection's current names. Rename
requires Find text when Replace is nonempty and keeps matching case-sensitive.
Each rerun recomputes from current names, including repeated prefixes or
suffixes. Case conversion changes view names only.

Exact target failures skip that view; other valid views may still change. One
parent Revit transaction gives the batch one Undo item, with a subtransaction
for each view. The dialog closes quietly when the action succeeds. Rename with
no changes stays open. Skipped or failed items expand an in-dialog result area
with counts and reasons; controls remain available for a full rerun. Results
for the same action are replaced on rerun while unresolved results from other
actions remain visible.

## Validation boundary

Static Python/XAML checks and host-independent tests support this prototype.
The owner approved the visual review on 10.09.2026. Live acceptance in Revit
2024, 2025, and 2026 remains required: duplicate or invalid names, templates,
read-only/workshared views, cancellation, reruns, partial results, Undo, and
quiet success.

## Implementation inventory

- Entry point: `script.py`
- Selection and WPF: local `script.py` and `Script.xaml`, with `BaseRenaming` and shared WPF styles.
- Planning, Revit transaction handling, and result presentation: `lib/find_replace/`.
- Bundled external assets: None.

## GUI and interaction

The local XAML uses shared KLCode brushes, wordmark, header, action buttons, and
footer styles. The original field labels and direct case buttons remain. A
result panel is collapsed initially and appears only for no-change Rename or
unresolved items. No preview or success popup is used.

## Current execution logic

`script.py` builds exact target names, then `apply_batch` starts one transaction
and an individual subtransaction per changing view. It checks commit status
and reports unexpected failures. The parent transaction is rolled back if its
commit fails.

## Model and external effects

Changes `View.Name` only. It does not change view templates unless the user
explicitly selected them, and it does not write files or contact external
services except when a footer link is clicked.

## Current status

Promoted to the existing Core button on `dev`; the DevSandbox bundle was retired.
The visual review is approved, and live Revit 2024, 2025, and 2026 acceptance
remains pending before release.
