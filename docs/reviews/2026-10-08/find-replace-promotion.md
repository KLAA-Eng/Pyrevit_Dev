# Find and Replace promotion review

## Current gate

The Views and Sheets commands remain in DevSandbox. Their planned tool version
is `v0.1` (Unreleased). The two Core Tools buttons have not been changed. The
owner's final visual review and live Revit 2024, 2025, and 2026 acceptance are
required before the prototype scripts replace the core implementations.

The prototype dialogs retain their existing labels and direct action buttons.
They use shared KLCode WPF resources. An issue panel is collapsed initially and
expands for skipped/failed items or a no-change Rename result. A complete action
closes quietly; no preview or success popup is used.

## Design-system source review

Compared both prototype `Script.xaml` files with `DESIGNSYSTEM.md`,
`lib/GUI/_templates/KLCodeMainTemplate.xaml`, and
`lib/GUI/Resources/WPF_styles.xaml` on 10.08.2026. Both dialogs already use the
template's 24 px borderless header, 86 px header edge columns, 70 x 12 outlined
wordmark, centered title, shared close/action button styles, dark palette,
green form borders, and shared three-column footer. Their compact, one- and
two-column forms are command-specific variants of the list-selection template.

The source review aligned the window, body, and header backgrounds with the
shared brush keys; let the input fields inherit their shared colors; matched
the template's 216 x 32 px, 14 px-font main action; and framed the outcome panel
with the same green border and corner radius as the form sections. The
SheetNumber/SheetName labels and direct case buttons were preserved.

This is a source comparison, not a rendered WPF review. The owner's live visual
review still needs to check title truncation, initial compact spacing, and the
expanded outcome panel at normal and high display scaling. In particular,
verify that the dynamically sized outcome panel and footer remain visible when
two action results are shown.

## Static evidence

| Check | Result |
| --- | --- |
| Focused planning, transaction-boundary, and window-state tests | 11 passed on 10.08.2026 |
| Branded-window tests | 9 passed on 10.08.2026 |
| Python AST and XAML XML parsing | Passed on 10.08.2026 |
| Visible command metadata check | 36 bundles, 0 errors on 10.08.2026 |
| `git diff --check` | Passed on 10.08.2026 |

The transaction tests use stand-ins for Revit. They confirm intended item
rollback and batch failure reporting; they do not prove live Revit behavior.
The implementation uses a parent transaction with per-item subtransactions,
consistent with the [Autodesk transaction guide](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-API/files/Revit_API_Developers_Guide/Basic_Interaction_with_Revit_Elements/Transactions/Revit_API_Revit_API_Developers_Guide_Basic_Interaction_with_Revit_Elements_Transactions_Transaction_Classes_html.html).

## Live acceptance record

Use a disposable local model with representative views, templates, and sheets.
Record each host's outcome here after testing. Do not use a project central
model for acceptance.

| Host | pyRevit loads this checkout | Behavior | Visual review | Outcome |
| --- | --- | --- | --- | --- |
| Revit 2024 | Pending | Pending | Pending | Pending |
| Revit 2025 | Pending | Pending | Pending | Pending |
| Revit 2026 | Pending | Pending | Pending | Pending |

The Revit 2024 application launched on 10.08.2026 but its MCP listener did not
respond within 120 seconds. Its current journal ended during license startup
with `LicenseUpd(1) Adlsdk Error:(22) vendor:SERVICE`. No Revit command or model
edit was run. Revit 2025 and 2026 have not yet been launched for this review.

### Views

- Confirm selected views are used directly; the fallback picker lists distinct
  IDs, excludes templates by default, and allows an explicitly selected template.
- Test Find/Replace (case sensitive), Prefix, Suffix, and direct UPPERCASE and
  lowercase actions. Confirm a clean action closes quietly and no-change Rename
  stays open.
- Test invalid/duplicate names, read-only/workshared views, cancellation,
  partial success, exact skip reasons, full rerun from current names, and Undo.
- Check the initial dialog and expanded result area for clipping, spacing,
  readability, and alignment with `DESIGNSYSTEM.md`.

### Sheets

- Test independent sheet-title and sheet-number fields. Case buttons must
  change titles only.
- Test invalid and occupied numbers, a two-sheet number swap, duplicate batch
  targets, invalid titles, and read-only/workshared sheets. Confirm no automatic
  `*` or `_` suffix is added.
- When a title and number are both requested, confirm failure of either one
  leaves that sheet unchanged while valid sheets can still change.
- Test cancellation, no-change Rename, quiet success, detailed partial results,
  a full rerun from current values, Undo, and Project Browser display after
  commit. Inspect both the initial dialog and expanded result area visually.

## Promotion after acceptance

1. Copy the accepted prototype scripts and local XAML into the two existing
   Core Tools bundles on `dev`, retaining the core button identities and icons.
2. Update core `SPEC.md`, `bundle.yaml`, tool versions, UI Gallery paths, and
   the design-system catalog to match the new implementation.
3. Remove the two DevSandbox prototype bundles only after the owner's final
   review, then rerun focused checks and inspect the complete diff.
