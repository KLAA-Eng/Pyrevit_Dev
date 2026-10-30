# Focus frame and selector summary removal — 2026-10-30

Owner rejected the green frame around focused buttons and checkbox labels,
and the selected/visible summary below selector lists. Baseline: `c871d4a`.
The [consolidation plan](../../../plans/custom-window-consolidation.md) owns
GUI-29; [SPEC](../../../../lib/GUI/dialogs/SPEC.md) owns current behavior.
This supersedes the green-focus/count-summary portions of the
[previous polish](2026-10-29-dialog-polish.md).

All common button/check/radio/toggle families now set FocusVisualStyle to null.
The green adorner resource and its two tokens are removed; no runtime references
remain. Keyboard focus, Tab/Space operation, checked/hover/disabled appearance,
ordinary borders and input/dropdown field-focus styling are retained.

The summary TextBlock and update code are removed from the shared selector.
Filtering, groups, hidden checks and explicit Select behavior are unchanged.
List-to-batch/action gaps remain 8 units; single selection has no doubled empty
gap. Inline validation remains visible and adds its spacing only when needed.

Verification:

- New no-adorner contract failed against the prior green style, then passed.
- 383 Python tests: 382 pass, one existing skip.
- Actual WPF: 45 shared-dialog states, 116 custom/state constructions and 15
  focus-style roles pass, including absent summary and exact action gaps.
- Two owned shown fixtures confirm neutral Command Switch initial focus and
  actual focused buttons/checks with FocusVisualStyle=None. They close on
  success/failure and use no Revit/user document or system-wide input injection.
- 17 C# source tests and seven compiled WPF instances on each of net48 and
  net8.0-windows pass. Zero strict spacing violations; 85 existing advisories.
- Independent read-only review found no material issue in state, spacing,
  validation, resource references or retained keyboard operation.

[Multiple selection](2026-10-30-focus-summary-evidence/dialog-sheets-normal.png)
and [single selection](2026-10-30-focus-summary-evidence/dialog-list-single-normal.png)
show the summary-free layout. The main and optional shown-focus commands are
listed in [DESIGNSYSTEM.md](../../../DESIGNSYSTEM.md#validation).

No production dialog call site or packaged DLL changed. Rebuild/deploy compiled
DLLs to consume shared source-style changes. Physical input/DPI/Revit-owner
acceptance remains owner-owned; source/focus checks do not close those gates.
