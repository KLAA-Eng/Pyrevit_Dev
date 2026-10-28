# Form reference: owner-confirmed field refinement

Date: 2026-10-28. Baseline: `51105f0`, plus this refinement on `dev.GUI-Clean`.
The [active plan](../../../plans/custom-window-consolidation.md) owns interview
decisions and task status. This supersedes the Form composition in the
[initial template-family evidence](2026-10-28-template-family.md).

The owner retained left labels and the bordered group, removed Sample Preview,
and confirmed 24-high inputs, 60/240 label/input widths, 8-unit row gaps,
vertically centered colon labels and 12-unit group padding. Segoe UI remains 12.
The reference starts at 360 x 352 with the shared header/footer, inline validation,
Reset and Apply Rules. Overall dimensions are a compact review starting point.

Shared typed tokens and opt-in `KlaCompactFieldLabel`/`KlaCompactFieldInput`
styles own the new role. Other references and production windows retain their
current field sizing. The presenter no longer owns a preview display; it still
validates fictional rules and never renames model elements.

| State | Actual isolated WPF render |
| --- | --- |
| Normal | [Compact Form](2026-10-28-template-family-evidence/template-form-refined-normal.png) |
| Error | [Inline validation](2026-10-28-template-family-evidence/template-form-refined-error.png) |
| Long content | [Long input text](2026-10-28-template-family-evidence/template-form-refined-long-content.png) |

Verification:

- Updated presenter test first failed on the retained `preview_lines` control,
  then passed after removing it and adapting the feedback contract.
- Gallery suite: 63 run, 62 passed, 1 skipped for unavailable symlink privilege.
- Installed IronPython 2.7.12/WPF: all 25 template states, normal-state actions,
  minimum sizes, 36-entry catalog and 71 custom/state constructions passed.
- All five Form states measure input width/height 240/24, label width 60,
  centered label content, colon suffixes, 8-unit row gaps, group padding 12 and
  8-unit action-to-footer clearance. A left-aligned inner grid keeps fixed-width
  columns from expanding with the outer group.
- Normal/Error/Long content renders were inspected. A read-only reviewer found
  no blocking implementation issues. Current guides and Gallery SPEC were updated.

Reproduce with the Gallery test command and isolated WPF probe documented in
the [family evidence](2026-10-28-template-family.md#verification). These renders
show actual WPF content without showing a Window. Pointer/keyboard input,
ownership, accessibility and DPI acceptance remain live-host checks.
