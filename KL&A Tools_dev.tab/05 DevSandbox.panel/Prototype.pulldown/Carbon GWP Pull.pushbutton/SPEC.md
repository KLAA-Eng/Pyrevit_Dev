# Carbon GWP Pull

## Purpose

Prototype pyRevit replacement for the Dynamo `x_Team Carbon GWP Pull_RVT 24.dyn` workflow.

The command exports selected Revit schedule table data to an Excel container workbook, reads calculated GWP and material-volume values from a post-processing workbook, and creates or updates two rendered doughnut charts on the `SYNC TO CENTRAL` sheet.

## Inputs

- Exactly three exportable Revit schedules selected from the active model. The
  selector excludes schedule templates and titleblock revision schedules, and
  pre-checks these Dynamo defaults when present:
  - `z_Project Material Takeoff`
  - `2x Wood Wall Volume`
  - `Composite Deck Volume`
- Export container workbook selected by file picker. Both workbook pickers
  accept `.xlsx` and `.xlsm` files. For a disk-hosted model,
  the first picker opens in the model's local or central-model folder. Cloud
  models use `J:\Standards\910 Revit Support\KLAA Library`, falling back to
  the current user's local Windows profile folder when that location is
  unavailable. Server, detached, and unsaved models use the configured
  Carbon-folder fallback.
- Post-processing workbook selected by file picker. The second picker opens in
  the folder selected for the export container workbook.

The tool prompts every run. It does not save paths.

## Excel Contract

- Each selected schedule is exported to a worksheet named `DYN Out - <clean schedule title>`.
- Schedule title cleanup removes Dynamo-style text before `=` and `)` markers, trims whitespace, removes Excel-invalid sheet-name characters, and limits names to Excel's 31-character worksheet limit.
- Duplicate cleaned names receive a numeric suffix while staying within Excel's
  31-character worksheet-name limit.
- The post-processing workbook must contain a worksheet named `Export`.
- The `Export` worksheet has this chart contract:
  - Column A: stable category/source name.
  - Column B: required positive GWP value in `kgCO₂e`.
  - Column C: required positive material-volume value in `CF`.
  - Columns D and E are not read by the command and may be removed.

The GWP and material-volume charts independently skip and report rows with a
blank name or blank, nonnumeric, zero, negative, or non-finite value for their
own measure. A bad GWP value does not remove a valid material-volume slice, or
vice versa. Every valid row becomes a slice; the command does not group values
into `Other`. Display labels derive from column A with `GWP` removed. Source
names containing steel, concrete, wood, or mason use `#558ED5`, `#D9D9D9`,
`#9BBB59`, or `#7F7F7F` respectively. Other names receive a deterministic
fallback color from the built-in palette.

After Excel refresh and calculation, the command performs an informational
Material Accuracy check against the exact worksheet named `Post-Processing`
(case-insensitive) and cells `F41:F70`. It detects only actual Excel `#N/A`
error values, not text that resembles an error. The check never blocks chart
creation or update. A completed check with one or more errors lists every cell
in the pyRevit report and shows a warning after the report is written. If the
sheet or range cannot be checked, the report records that result and the user
is warned to review the Material Breakdown table in Excel.

## Model Changes

All Revit model writes occur inside one transaction named `Carbon GWP Pull - Update Managed Charts`.

It requires exactly one sheet named `SYNC TO CENTRAL`; it never creates a sheet
or guesses between duplicate names. The user must have that sheet open. On the
GWP chart's top-left is aligned to the unique titleblock's top-right. The
volume chart's top-left is aligned to the GWP chart's bottom-left. There is no
placement picker; both images are re-aligned to the titleblock on every run. A
dedicated Revit Extensible Storage marker identifies only each image created by
this tool; ambiguous or copied managed images stop the update rather than being
changed. If the titleblock or placement cannot be resolved, the transaction
stops with no fallback placement.

Each image is 7.875 × 4.75 inches or taller, with a white background and no
title. It has a fixed 4-inch doughnut, a 3/8-inch left margin, and a 3-inch
right-side legend column separated from the doughnut by 1/4 inch. The legend
shows a 0.25-inch solid color square, a semibold material name, and a regular
rounded-amount-and-percentage detail line. Its center shows the bold rounded
total centered between a 20pt semibold title above and a 20pt semibold unit
below: `Total GWP` or `Total Volume`. The value is 26pt bold. Text uses dark
charcoal Segoe UI, with 0.10 inches between each adjacent center-text layout
box. For each valid material beyond six,
the image grows 0.65 inch vertically while keeping the fixed doughnut and
legend vertically centered. The PNGs are saved beside the selected
post-processing workbook as `Carbon GWP Summary.png` and `Carbon Material
Volume Summary.png`; each successful render replaces those generated files.
They are also imported into the RVT, not linked.
Existing `Carbon Pie.JMP` parameter values are not read, changed, or cleared.

The schedule export and Excel reads do not change the Revit model. Rendering
happens before the Revit transaction, so a render/import/reload failure leaves
the existing managed chart intact.

## Output

The pyRevit output window reports:

- Selected schedules.
- Export and post-processing workbook paths.
- Exported worksheet names.
- Target sheet and whether each managed chart was created or updated.
- GWP and material-volume chart slices as row, source, material, and a
  two-decimal amount in the chart's native unit.
- Skipped Excel rows as row, source, material, and reason.
- Runtime errors.

## Prototype Limits

- Requires Microsoft Excel COM interop on the Revit workstation.
- Uses the built-in Windows/.NET drawing APIs and Revit image APIs; it does not
  require additional Python packages.
- Requires the post-processing workbook formulas or macros to already produce the `Export` worksheet values after schedule export.
- The command does not explicitly invoke workbook macros. It currently does
  not override Excel's automation macro-security setting, so users must select
  only trusted `.xlsx` and `.xlsm` workbooks.
- Refreshes Power Query inputs from the selected export container in the
  read-only post-processing Excel session before reading `Export`. It waits up
  to 60 seconds and stops rather than rendering a chart from still-refreshing
  (stale or temporary zero) values. Refresh, external-link update, or
  calculation errors also stop the command before it reads `Export` or changes
  Revit.
- A pre-existing generated PNG is deleted before its replacement is rendered.
  If rendering fails, the existing Revit chart remains unchanged, but the local
  generated PNG is not retained.
- Does not validate that the exported schedule workbook and post-processing workbook are formula-linked correctly.
- Stops before Revit changes if the target sheet or `Export` worksheet is missing,
  if the target sheet is not active, or if either chart has no positive values.
- Requires live Revit validation for image import, sheet placement, rerun reload,
  worksharing permissions, model reopening, and undo behavior.

