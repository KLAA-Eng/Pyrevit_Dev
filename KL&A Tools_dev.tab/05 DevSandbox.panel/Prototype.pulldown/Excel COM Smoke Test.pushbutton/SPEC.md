# Excel COM Smoke Test

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.excel-com-smoke-test` |
| Tool version | `v0.2` |
| Status | Unreleased diagnostic update; prototype live acceptance remains pending |
| Status/origin | Prototype; KL&A custom tool. |
| Main delivery | 0.0.12 |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Excel COM Smoke Test.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Excel COM Smoke Test.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Excel COM Smoke Test.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Excel COM Smoke Test.pushbutton/script.py`; `lib/excel_com.py` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | 0.0.10 | 10.05.2026 | First main delivery of a disposable Excel facade lifecycle and operation smoke test. | 74eccba; verified v0.0.10-beta snapshot |
| v0.1 | 0.0.12 | 10.13.2026 | Report the first Excel assembly lookup error and the loaded assembly identity and path. | `25c3e39`; 0.0.12 delivery snapshot. |
| v0.2 | Unreleased | 10.15.2026 | Identify the running script and shared facade, inspect Excel interop DLL locations, trial an identity-checked Office 16 DLL by path after a failed shared startup, and probe direct Excel activation. | Current branch; pending main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

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
chart-object creation, the reopened application's macro-security property,
refresh and calculation. Each operation is reported as
PASS or FAIL with its runtime type and error detail. Successful runs remove
only their exact owned assets; failed or unsafe cleanup retains them for review.
Before creating Excel, it prints the running script and shared facade paths and
SHA-256 fingerprints,
reports whether an Excel interop assembly was already loaded, and tries the
first short-name assembly lookup. It then tests the shared Excel loader from
that state, so the diagnostic's own path trial cannot mask a loader failure.
The page text keeps the full lookup error; the table uses its first line so
multiline stack traces do not break the row.
If shared startup fails after name lookup and no Excel interop assembly was
loaded by that attempt, the command validates the identity of the installed
Office 16 DCF Excel interop DLL
and tries `clr.AddReferenceToFileAndPath` on its absolute path. It skips this
trial when loaded-assembly inspection fails or finds an existing Excel interop
assembly after shared startup, avoiding a second version in that process. It
reports the trial result and any loaded assembly. If the shared facade could
not create Excel and the diagnostic path load succeeds, it imports Excel from
the loaded assembly and tries to create, configure, and close a hidden Excel
instance without repeating the name lookup. These probes are diagnostic;
they do not change the shared loader's result. The command also reads the
assembly identity of interop DLLs in common Office and GAC locations. Output
table cells replace line breaks and pipe separators so each diagnostic remains
in one row. An empty file inventory is not proof that the DLL is absent from
the machine. Assembly-inspection errors do not change the facade result or
temp-file cleanup decision.

## Prerequisites and effects

Requires a local Microsoft Excel COM registration. It does not access the
active model or create a Revit transaction. It never opens, changes, or deletes
a user-selected workbook. When the name lookup fails, the explicit-path trial
can load an Office interop assembly into the Revit process until Revit closes;
run this trial in a fresh Revit session and close it after reviewing the result.

## Limits and validation

This verifies every public operation used by the shared facade, but it does not
prove Carbon GWP chart placement, Steel PSF business results, or Concrete Mix
Header schedule writes. Required acceptance is one successful run in each of
Revit 25 and Revit 26 with Excel installed, retaining the output table.
The affected Revit 2025 workstation passed shared Excel startup, worksheet,
query, table, pivot, chart, and SaveAs operations on 10.15.2026. The read-only
reopen failed at the separate `Office` assembly lookup for macro security;
the shared facade fix for that lookup awaits a fresh live rerun.
