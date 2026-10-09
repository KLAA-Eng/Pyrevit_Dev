# Find and Replace promotion review

## Current gate

The owner approved the visual review on 10.09.2026. The accepted Views and
Sheets prototype implementations now occupy the existing Core Tools buttons
on `dev`, with planned Core versions `v1.0` and `v1.1` respectively. Their
DevSandbox bundles were retired. Live Revit 2024, 2025, and 2026 acceptance
remains the next gate before release.

The promoted dialogs retain their existing labels and direct action buttons.
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
KLCharcoal palette; let the input fields inherit their shared colors; matched
the template's 216 x 32 px, 14 px-font main action; and framed the outcome panel
with the same green border and corner radius as the form sections. The
SheetNumber/SheetName labels and direct case buttons were preserved. The button
captions now read Uppercase and Lowercase. Both fallback pickers start with no
checked rows, and visible choices omit element IDs. Equal view names remain
distinct through view type and, when needed, a sequence number.

The owner accepted this visual review on 10.09.2026. During live Revit tests,
verify that host rendering preserves title legibility, compact spacing, and
visibility of the expanded outcome panel and footer, including two unresolved
action results at normal and high display scaling.

## Static evidence

| Check | Result |
| --- | --- |
| Focused planning, transaction-boundary, picker-label, and window-state tests | 12 passed on 10.09.2026 |
| Shared picker selection-state tests | 3 passed on 10.09.2026 |
| Branded-window tests | 9 passed after promotion on 10.09.2026 |
| Python AST and XAML XML parsing | Passed on 10.09.2026 |
| Promoted XAML event handlers | All 6 handlers resolved for each Core dialog on 10.09.2026 |
| UI Gallery source catalog tests | 5 passed after promotion on 10.09.2026 |
| Visible command metadata check | 34 bundles, 0 errors after promotion on 10.09.2026 |
| `git diff --check` | Passed on 10.09.2026 |

The transaction tests use stand-ins for Revit. They confirm intended item
rollback and batch failure reporting; they do not prove live Revit behavior.
The implementation uses a parent transaction with per-item subtransactions,
consistent with the [Autodesk transaction guide](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-API/files/Revit_API_Developers_Guide/Basic_Interaction_with_Revit_Elements/Transactions/Revit_API_Revit_API_Developers_Guide_Basic_Interaction_with_Revit_Elements_Transactions_Transaction_Classes_html.html).

## Live acceptance record

Use a disposable local model with representative views, templates, and sheets.
Record each host's outcome here after testing. Do not use a project central
model for acceptance.

| Host | pyRevit loads this checkout | Behavior | Approved design renders correctly | Outcome |
| --- | --- | --- | --- | --- |
| Revit 2024 | Pending | Pending | Pending | Pending |
| Revit 2025 | Pending | Pending | Pending | Pending |
| Revit 2026 | Pending | Pending | Pending | Pending |

The Revit 2024 application launched on 10.08.2026 but its MCP listener did not
respond within 120 seconds. Its current journal ended during license startup
with `LicenseUpd(1) Adlsdk Error:(22) vendor:SERVICE`. No Revit command or model
edit was run. Revit 2025 and 2026 have not yet been launched for this review.

### Views

- Confirm selected views are used directly; the fallback picker starts unchecked,
  lists distinct names without IDs, and excludes templates by default. A
  template selected in the Project Browser remains eligible.
- Test Find/Replace (case sensitive), Prefix, Suffix, and direct Uppercase and
  Lowercase actions. Confirm a clean action closes quietly and no-change Rename
  stays open.
- Test invalid/duplicate names, read-only/workshared views, cancellation,
  partial success, exact skip reasons, full rerun from current names, and Undo.
- Check the initial dialog and expanded result area for clipping, spacing,
  readability, and alignment with `DESIGNSYSTEM.md`.

### Sheets

- Confirm the fallback sheet picker starts unchecked and omits element IDs.
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

## Promotion completed on `dev`

1. Copied the approved scripts and local XAML into the existing Core bundles,
   retaining their button identities and icons.
2. Combined each Core and prototype lineage in the Core `SPEC.md` histories;
   updated the Core tool versions, bundle tooltips, UI Gallery, and design-system
   catalog.
3. Removed the two DevSandbox prototype bundles and their ribbon entries after
   the owner's visual approval. The prior shared rename XAML remains labeled as
   legacy gallery previews, with no active Core button using those files.
