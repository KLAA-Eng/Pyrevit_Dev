# Review reference: filtered actions and centered status chips

Date: 2026-10-28. Baseline: `1688995`, plus this refinement on `dev.GUI-Clean`.
The [active plan](../../../plans/custom-window-consolidation.md) owns accepted
choices and task status. The owner confirmed all four Review recommendations
and requested centering the status chips in their column.

Checked items remain separate from the selected row. Clicking a row changes
the right-hand details without checking it, and the divider remains resizable.
After filtering, the selected visible row is brought into view.

Check All now affects eligible rows in the current filtered view only. Hidden
checks are preserved; no matches means no changes. Apply Checked still validates
the complete checked collection. The summary reports shown/total counts and
states Check All's scope. The Error fixture's recovery instruction now tells
the reviewer to clear the filter before using Check All to remove invalid
blocked checks. Blocked rows cannot be checked through the UI.

Ready/Warning/Blocked retain labelled, colored-border chips. The new opt-in
`KlaDataGridStatusCell` style centers its content horizontally and vertically;
only Review's Status column selects it. Other columns and chip consumers retain
their existing alignment. Production windows remain unchanged.

| Case | Actual isolated WPF render |
| --- | --- |
| Normal | [Review](2026-10-28-template-family-evidence/template-review-confirmed.png) |
| Filtered to one item | [Visible row and action scope](2026-10-28-template-family-evidence/template-review-confirmed-filtered.png) |
| Minimum size | [Narrow table and details](2026-10-28-template-family-evidence/template-review-confirmed-minimum.png) |

Verification:

- New presenter test failed when Check All checked an eligible hidden row,
  then passed after restricting the action to the filtered ItemsSource.
- Gallery suite: 64 run, 63 passed, 1 skipped for unavailable symlink privilege.
- Installed IronPython 2.7.12/WPF: all 25 template states, normal interactions,
  minimum sizes, 36-entry catalog and 71 custom/state constructions passed.
- Generated status-chip centers match their cell centers within 1 WPF unit,
  horizontally and vertically. Actual blocked checkboxes remain disabled;
  the Disabled specimen disables all body checkboxes.
- Actual selected-row changes preserve checkbox state. Filtered Check All leaves
  hidden eligible rows unchanged; an empty filter result changes no checks.
  Filtered captures contain a generated visible row after ScrollIntoView.
- Fake-boundary tests also preserve an existing hidden check and reject checked
  blocked rows. Normal, filtered and minimum-size renders were inspected.
- A read-only reviewer found no blocking issues in action scope or alignment.

Reproduce with the Gallery tests and isolated WPF probe documented in the
[family evidence](2026-10-28-template-family.md#verification). No Window was
shown. Live splitter dragging, actual input, ownership, accessibility and DPI
acceptance remain pending. The reference is a safe fictional specimen; no
production operation or data was changed.
