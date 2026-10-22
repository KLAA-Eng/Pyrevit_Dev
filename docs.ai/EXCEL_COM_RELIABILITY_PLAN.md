# Excel COM reliability plan

**Status:** Proposed investigation and implementation plan, 10.22.2026. No
production change or affected-host acceptance is implied by this document.

## Scope and current evidence

Carbon GWP Pull, Steel PSF, Concrete Mix Header, and the Excel COM Smoke Test
use `lib/excel_com.py`. Carbon writes selected schedules to an export workbook,
then asks Excel to open a separate analyst workbook, refresh Power Query and
external links, recalculate, and read its `Export` sheet. A file-only XLSX
library cannot replace that second stage without changing the workbook contract.

The original Carbon failure on coworker B's Revit 2025 host was an Excel
interop assembly lookup before workbook processing. The Carbon script and
Excel helper were unchanged between `v0.0.10-beta` and `v0.0.11-beta`. An
affected-host diagnostic loaded an Office 16 Excel interop DLL by verified
absolute path and directly activated Excel. After the shared loader changed,
the smoke test passed operations through SaveAs but failed on read-only reopen
because a separate `Office` assembly lookup was used for macro security. That
lookup was removed in the current `dev.ben-debug` helper. A full affected-host
reopen, refresh, and calculation result after that change is now recorded for
both coworkers B and L.

The present shared startup path is short-name PIA lookup, already-importable
Excel namespace, verified Office 16 DCF PIA by path, then a legacy version 11
assembly reference. It constructs `Excel.ApplicationClass`. This handles the
observed Office 16 machine, but depends on assembly resolution and an Office
installation path. Microsoft labels `ApplicationClass` reserved for internal
use [1]. A version 15 PIA found on disk is not proof that the running Revit
host can bind to it; .NET 5+ does not use the .NET Framework GAC [2].

## Baseline: coworkers B and L

### Recorded baseline: B

Coworker B's Revit 2025 smoke result received 10.22.2026 used script SHA-256
`feb76308d1d4dd07c09658315b8d9009bab837c39efa513f460da6759cb6dc08`
and shared facade SHA-256
`6cfaaf5285c04fd6122bbb8a553368384371602bc48b8d50ed06b987bc3bc872`.
Both match the current `dev.ben-debug` files. No Excel interop assembly was
loaded before the lookup. The short-name lookup failed (reported as `INFO`),
but shared startup passed with the Office 16 PIA loaded from the DCF path.
Every operation shown in B's two screenshots passed, including SaveAs,
`Read reopen AutomationSecurity`, read-only `Workbooks.Open`, `RefreshAll`,
`CalculateFullRebuild`, and owned-temp cleanup. This establishes the disposable
shared-facade lifecycle on B's host; it does not establish Carbon workbook
refresh correctness or Revit chart placement. B's Office build and Revit build
were not included in the submitted smoke output.

### Recorded baseline: L

Coworker L's Revit 2026 smoke result received 10.22.2026 used the same smoke
script and shared facade SHA-256 values as B, both matching `dev.ben-debug`.
No Excel interop assembly was loaded before lookup. The short-name lookup
failed as `INFO`, while shared startup passed using the Office 16 PIA from the
DCF path. Every operation shown in L's two screenshots passed, including
SaveAs, `Read reopen AutomationSecurity`, read-only `Workbooks.Open`,
`RefreshAll`, `CalculateFullRebuild`, and owned-temp cleanup. This establishes
the disposable shared-facade lifecycle in Revit 2026 on L's host; it does not
establish Carbon workbook refresh correctness or Revit chart placement. L's
Office build was not included in the submitted smoke output.

### Evidence to retain for later runs

The unchanged smoke test uses disposable, owned temp files and does not access
the model or a user workbook. Keep its complete operation table, including
failures after the first failed row. Capture for each run:

| Field | Why it matters |
| --- | --- |
| Coworker label B or L; run date; Revit version/build; pyRevit engine/version; Excel version | Separates host configurations. |
| Smoke script path and SHA-256; shared Excel facade path and SHA-256 | Proves both people exercised the same code. |
| First Excel interop name lookup and loaded assembly identity/location | Identifies the assembly route and any preloaded version. |
| Every operation from `Create hidden Excel application` through `Owned temp cleanup` | Distinguishes startup, SaveAs, reopen, refresh, calculation, and cleanup. |
| Full error text, especially `Read reopen AutomationSecurity` and `Workbooks.Open read-only` | Prevents a secondary failure from being mistaken for the original one. |

Do not compare only the PASS/FAIL alert: a failed run can retain temp assets and
can skip later operations. If either script or facade hash differs, resolve
that mismatch before comparing B and L. If both pass, use an approved trusted
Carbon workbook fixture on each affected host; the disposable smoke workbook
cannot prove Power Query source links, chart values, or Revit placement.

### Reading the results

| Observation | Next investigation |
| --- | --- |
| Name lookup fails, shared startup passes | Office 16 path fallback likely worked; inspect assembly location and proceed to reopen rows. |
| Shared startup fails, explicit path load and direct activation pass | Compare the exact facade version and the shared loader errors before changing Office installation. |
| Startup and SaveAs pass, reopen fails | Inspect `AutomationSecurity` and `Workbooks.Open` errors separately. |
| Entire smoke test passes, Carbon fails | Investigate the selected workbook's links, queries, refresh result, and Excel data contract before blaming COM startup. |
| B and L differ at the same code hashes | Preserve both environment records; avoid a machine-wide repair based on only one result. |

**Decision after both baselines:** The shared loader and disposable workbook
lifecycle now pass on B and L. B then ran Carbon: it produced accurate charts,
but the selected post-processing workbook remained blank on disk. Source review
found that Carbon opened the analyst workbook read-only and closed without
saving, so its calculated values existed only in that Excel session. A focused
`v1.1` change on `dev.ben-debug` now opens the analyst workbook for editing,
checks `Workbook.ReadOnly`, saves after refresh/calculation and reading `Export`,
and reports the save. Focused static tests pass; a fresh B run that reopens the
workbook and verifies persisted values is still required. Keep the current
loader stable for that comparison. The ProgID experiment below is an
architecture test to reduce future assembly dependence; it should run
separately and should not be treated as the present Carbon fix.

## Proposed connection design

**First experiment:** In a separate diagnostic, and before any PIA lookup in a
fresh Revit process, resolve the registered `Excel.Application` COM ProgID with
`.NET Type.GetTypeFromProgID`, then create a **new** Excel instance with
`Activator.CreateInstance` [3]. Pass the returned object through the existing
explicit property/method facade. Record its runtime type, any loaded Excel
interop assembly, and each operation of the current smoke lifecycle. Do not
attach to a person's running Excel process.

This route is intended to remove the Excel PIA lookup from application
creation. It remains a hypothesis until live testing proves that IronPython
can invoke all required members on the returned COM wrapper. The experiment
must cover optional `Workbooks.Open` arguments, SaveAs, QueryTable refresh,
ListObject and PivotCache creation, chart objects, read-only reopen, refresh,
calculation, and Close/Quit. Run the PIA-backed baseline and ProgID experiment
in **separate fresh Revit sessions** so an earlier assembly load cannot mask a
dependency. Record errors and loaded assemblies for both routes.

If the experiment passes on B and L, and in the supported Revit/Office matrix,
make ProgID activation the shared facade's preferred route in a focused code
change. Keep the verified PIA route temporarily as a visible fallback, with a
clear route and error in diagnostics. Remove brittle version/path assumptions
only after both routes' behavior and failures are understood. If ProgID
activation still requires a PIA or breaks a required operation, retain the
current route and evaluate a small compiled bridge or an isolated Excel helper
process; those add deployment and process-boundary complexity.

## Reliability work independent of startup

1. **Fail closed on macro security.** `open_workbook()` currently continues if
   reading `AutomationSecurity` raises. Its stated contract is to open with
   macros disabled, while Excel's documented startup value is Low and
   `Workbooks.Open` enables macros by default [4, 5]. A later code change
   should require a successful read, set, and verification of force-disable
   before opening, then restore the previous value in `finally`. Keep the
   current numeric value `3` and CLR enum conversion to avoid another `Office`
   assembly dependency. Excel 4.0 macro prompts remain a documented exception
   [4].
2. **Detect failed Power Query table refreshes.** Carbon currently calls
   `RefreshAll`, waits for `Refreshing` flags, and recalculates. Microsoft
   documents that a Power Query refresh into a worksheet table can fail
   without a `RefreshAll` exception and leave previous data in place, even
   with background refresh disabled [6]. For actual Power Query-backed
   `ListObject` tables in the analyst workbook, evaluate individual
   `ListObject.QueryTable.Refresh(BackgroundQuery=False)` calls and surface
   errors or false returns. Verify expected source rows or a known freshness
   marker before using `Export`; account separately for connection-only or
   data-model queries. Do not silently swallow errors for required queries.
3. **Own the Excel instance through partial failures.** If configuration
   raises after creating Excel, call Quit on the instance. Ensure Close(False)
   and Quit paths are reported independently. Consider explicit COM wrapper
   release only if a live retained-process problem is demonstrated; it needs
   careful handling of nested COM references.

These changes should stay in the shared facade or narrow Carbon workflow as
appropriate, with focused static tests. Update their adjacent SPEC and bundle
metadata when behavior or tool version meaningfully changes. Do not advance a
tool version solely for this planning document.

## Acceptance before promoting a replacement

- B and L: current smoke output with matching script/facade hashes is recorded;
  complete ProgID diagnostic output in separate fresh sessions remains pending.
- Supported host coverage: at least Revit 2025 and 2026 with Excel installed;
  also exercise Revit 2024 because Carbon declares it supported. Record the
  pyRevit engine and Office build for each run.
- Full disposable lifecycle passes, including reopen, `AutomationSecurity`,
  refresh, calculation, and cleanup; verify no owned hidden Excel process is
  left behind after failure cases.
- Carbon fixture: known expected `Export` values and chart totals after a
  successful refresh; a deliberately broken source/query must stop before
  creating a chart from cached values. Reopen the analyst workbook after the
  run and confirm the refreshed values persisted; verify normal rerun and
  chart placement separately in Revit.
- Static tests cover route selection, actionable errors, macro-security
  failure, and partial-startup cleanup. Static success is not live acceptance.

## References

1. [Excel `ApplicationClass` (reserved for internal use)](https://learn.microsoft.com/en-us/dotnet/api/microsoft.office.interop.excel.applicationclass?view=excel-pia)
2. [.NET global assembly cache compatibility](https://learn.microsoft.com/en-us/dotnet/core/compatibility/core-libraries/5.0/global-assembly-cache-apis-obsolete)
3. [.NET `Type.GetTypeFromProgID`](https://learn.microsoft.com/en-us/dotnet/api/system.type.gettypefromprogid?view=net-10.0)
4. [Excel `Application.AutomationSecurity`](https://learn.microsoft.com/en-us/office/vba/api/excel.application.automationsecurity)
5. [Excel `Workbooks.Open`](https://learn.microsoft.com/en-us/office/vba/api/excel.workbooks.open)
6. [Excel `Workbook.RefreshAll`](https://learn.microsoft.com/en-us/office/vba/api/excel.workbook.refreshall)
