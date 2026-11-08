# FindReplace - Views

| Field | Value |
| --- | --- |
| Tool ID | `core.rename.findreplace-views` |
| Former prototype Tool ID | `devsandbox.findreplace-views-proto` |
| Tool version | `v1.0` |
| Status | Released in 0.0.11 beta; live acceptance pending |
| Status/origin | KL&A-maintained Core command promoted from an EFTools-derived DevSandbox prototype. |
| Main delivery | 0.0.11 |
| Path aliases | Core release layout: `KL&A Tools.tab/03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton`; current `KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton`; former prototype: `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton`, `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton` |
| Version inputs | Core `bundle.yaml`, `script.py`; `lib/find_replace/controller.py`, `planning.py`, `workflow.py`, `revit_batch.py`; `lib/GUI/dialogs/` Rename and Action Choice; `lib/Snippets/_selection.py` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v1.2.EFTools | 0.0.0.beta | 07.16.2026 | Unchanged EFTools 1.2 Core command entered the first mainline delivery. | Upstream header; `484924b`; import `6a46157` |
| v1.2.EFTools | 0.0.5.beta | 08.20.2026 | The parallel DevSandbox prototype first delivered the unchanged EFTools 1.2 behavior. | `8cd45f8` |
| v0.0 | 0.0.6beta | 09.15.2026 | The prototype first delivered KL&A-local WPF/resource and case-button changes; the Core command stayed at v1.2.EFTools. | `300f8d4` |
| v1.0 | 0.0.11 | 10.12.2026 | Promote the prototype to the existing Core button with exact-value batch rename, case conversion, unchecked ID-free picker, and in-dialog outcomes. The prototype's planned v0.1 work is included in this delivery. | `6444c8d` and development promotion; pending owner merge to main. |

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
selection it offers individual non-template views through the shared picker
with no rows initially checked. Element IDs are hidden; equal names are
separated by view type and, when needed, sequence. Explicitly selected templates
remain eligible; sheet views are excluded. Shared Rename uses one View Name
group, including Uppercase/Lowercase actions.

Actions use the shared Rename request window and execute only after it closes.
The request retains literal, case-sensitive Find/Replace, Prefix and Suffix;
Replace requires Find, and an entirely blank rename request stays open with
inline validation. Case actions ignore entered rules and change names only.
There is no live before/after preview.

Exact requested targets are preserved; no collision suffix is invented. One
parent Revit transaction gives each submitted batch one Undo item, with one
subtransaction per element. Other valid elements may change when an item fails.
A clean changed result finishes quietly. A no-op, partial result, or error opens
the shared Action Choice result dialog with counts, expandable Details, Close,
and Edit and Retry when unfinished targets remain. Retry reopens shared Rename
with the entered rules retained and the same unfinished element identities.
After partial success, committed and unchanged elements are excluded; prefixes
or suffixes are never reapplied to earlier successes during that retry.
Cancellation of either request or results ends the command without another run.
A Project Browser refresh failure after committed changes is reported with
Close only; it cannot cause those changes to be reapplied.

## Validation boundary

Static Python/XAML checks and host-independent tests support this prototype.
The owner approved the visual review on 10.09.2026. Live acceptance in Revit
2024, 2025, and 2026 remains required: duplicate or invalid names, templates,
read-only/workshared views, cancellation, reruns, partial results, Undo, and
quiet success.

## Implementation inventory

- Entry point: `script.py`, a thin selection and document adapter.
- Requests: `GUI.dialogs` shared Rename, using `view_fields()` or `sheet_fields()`.
- Exact target planning: `lib/find_replace/planning.py` and `workflow.py`.
- Model transactions: `lib/find_replace/revit_batch.py`.
- Request/result/retry sequence: `lib/find_replace/controller.py`.
- Results: shared Action Choice; no command-local dialog implementation.
- Bundled external assets: None.

## GUI and interaction

Shared Rename owns its one/two property-group layout, validation, keyboard,
close behavior and existing design resources. The caller supplies its title and
tool version. Valid requests close before model work; errors and unchanged
outcomes use shared Action Choice with Details and an explicit Edit and Retry
path. No command-local XAML is a runtime dependency. Shared component,
foundation and token dictionaries are unchanged by this adoption.
## Current execution logic

`planning.py` builds exact target names, then `apply_batch` starts one transaction
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

## Unreleased dialog adoption — 11.08.2026

Shared Rename and Action Choice replace the command-local request/result UI.
Retry targets only unfinished elements after partial success. Tool versions
remain unchanged pending the next meaningful main delivery. Local behavioral
and transaction-boundary tests support this change; live Revit acceptance
remains pending.


