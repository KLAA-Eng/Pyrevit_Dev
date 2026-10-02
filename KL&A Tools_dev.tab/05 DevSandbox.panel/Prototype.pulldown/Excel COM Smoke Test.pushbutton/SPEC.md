# Excel COM Smoke Test

## Identity

- Bundle: `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Excel COM Smoke Test.pushbutton`
- Maturity: Prototype
- Live Revit validation: pending Revit 25 and Revit 26 acceptance

## Purpose

Diagnose the shared Excel COM facade in one disposable lifecycle, without a
Revit transaction, selection, schedule export, or user workbook.

## Workflow

The command creates a UUID-owned folder below the system temp folder, then
creates an XLSX and CSV inside that exact folder. It tests Excel application
properties, workbook Add/Open/Close/SaveAs, worksheet collections and names,
ranges and formulas, CSV query tables and list objects, pivot-cache creation,
chart-object creation, refresh and calculation. Each operation is reported as
PASS or FAIL with its runtime type and error detail. Successful runs remove
only their exact owned assets; failed or unsafe cleanup retains them for review.

## Prerequisites and effects

Requires a local Microsoft Excel COM registration. It does not access the
active model or create a Revit transaction. It never opens, changes, or deletes
a user-selected workbook.

## Limits and validation

This verifies every public operation used by the shared facade, but it does not
prove Carbon GWP chart placement, Steel PSF business results, or Concrete Mix
Header schedule writes. Required acceptance is one successful run in each of
Revit 25 and Revit 26 with Excel installed, retaining the output table.
