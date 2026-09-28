# Steel PSF

## Purpose

`Steel PSF` is a read-only DevSandbox pyRevit prototype that reports host-model
structural framing and structural-column pounds per floor area. Pounds equal
usable instance length in feet multiplied by nominal section weight in lb/ft.

## Scope and output

The command collects eligible steel family instances, using framing Reference
Level and column Base Level where available, and computed Floor area. It prints
summary metadata plus groupings by level, category, family/type, and floor type.
Missing level, length, nominal weight, or area is excluded with a reason.

The current command prints results and command messages through the default
pyRevit output window and alert dialogs. Its branded story-selection dialog can
also initialize or append raw CSV export files, then create a companion Excel
workbook when Microsoft Excel COM automation is available. The command does not
start a transaction, modify, save, or synchronize the Revit document.

## Validation boundary

Revit 2024+ fixture validation must confirm where each family's nominal-weight
parameter resides, its storage/unit conversion, known hand calculations, and
read-only behavior before quantity results are relied upon.

## Implementation inventory

- Entry point: `script.py`
- Entry UI: `SteelPsfDialog.xaml`
- Direct imports include Autodesk Revit API, pyRevit, KLCode WPF resources,
  steel-weight aggregation, report formatting, and history CSV helpers.
- Local helper functions include Revit data collection, output printing,
  history CSV export, and Excel workbook creation.
- Bundled external assets: Steel PSF-specific XAML only.

## GUI and interaction

Static UI/API references: forms.alert,forms.pick_folder,output.print_md,output.print_table,script.get_output,wpf.LoadComponent,

Use the command from its pyRevit button. Select stories in the branded dialog
with the search box, `Select All`, and `Select None`. Click `Review Selected
Stories` for a normal run, `Initialize CSV` to create/overwrite the Steel PSF
raw CSV set in a selected folder after the report runs, or `Append CSV` to
append to the Steel PSF raw CSV set in a selected folder after the report runs.
Folder selection is prompted only after the report has been generated and only
for initialize/append modes.

## Current execution logic

pyRevit loads the bundle and executes its entry point. The implementation uses
the imports and helper functions listed above; inspect `script.py` for the exact
branching order and host API calls.

## Model and external effects

Detected mutation/external-effect patterns: No Revit transaction or direct mutation pattern detected.

## Current status

This is a development-tab command. The inventory above is statically derived
from the current bundle and must be confirmed inside the target Revit/pyRevit
environment before promotion or behavior changes.

## CSV and Excel history

- The export set is folder-based:
  `SteelPSF_Steel.csv`, `SteelPSF_Floors.csv`, `SteelPSF_Exclusions.csv`,
  `SteelPSF_LevelSummaries.csv`, `SteelPSF_CategorySummaries.csv`,
  `SteelPSF_FamilyTypeSummaries.csv`, `SteelPSF_FloorTypeSummaries.csv`,
  `SteelPSF_ExcludedUnavailableSummaries.csv`, and `SteelPSF.xlsx`.
- `Run And Append CSV` prompts for the folder containing the raw CSV set and
  validates each existing CSV header before adding current run rows. If any
  header does not match the Steel PSF raw export format, append is stopped.
- `Run And Initialize CSV` prompts for a folder, then overwrites the raw and summary
  CSVs in that folder with fresh headers and current run rows.
- Raw steel and floor CSVs include eligible and ineligible selected records.
  The exclusions CSV records unavailable steel/floor rows and adapter skips for
  audit pivots.
- Each output-window summary table has its own CSV: level, category,
  family/type, floor-type, and excluded/unavailable summaries.
- The companion workbook is created beside the CSV set only when missing.
  Existing workbooks are treated as user-owned and are not overwritten. New
  workbooks connect to raw tabs plus individual CSV-backed tabs for each
  output-window summary table.
- Excel workbook creation depends on installed Microsoft Excel COM automation.
  CSV export remains successful if workbook creation fails.

## Future development

- Live Revit/Excel acceptance should confirm the custom dialog layout, CSV file
  prompts, Excel query refresh, and starter chart usefulness before promotion.
- Revisit a custom KLCode green-themed report window as a future UI item after
  the default pyRevit output workflow is validated and the desired table layout
  is specified.
