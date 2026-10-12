# Carbon GWP Pull — Excel COM troubleshooting

## Observed failure

On Revit 2025 and the reported Revit 2026.5 session, the command reaches
`_export_schedules_to_workbook()` and fails at:

```python
workbook = excel.Workbooks.Open(workbook_path)
```

with `AttributeError: '__ComObject' object has no attribute 'Open'`. The same
workflow worked in Revit 2024.

This happens before schedule cells are written and before the command starts a
Revit transaction. It is therefore not evidence of a schedule, workbook, or
Revit-model API failure. `Open` is an Excel PIA member: Microsoft documents it
on the `Workbooks` interface, which the `Application.Workbooks` property is
supposed to return.

Sources: [Microsoft: Workbooks interface](https://learn.microsoft.com/en-us/dotnet/api/microsoft.office.interop.excel.workbooks?view=excel-pia),
[Microsoft: Workbooks.Open](https://learn.microsoft.com/en-us/dotnet/api/microsoft.office.interop.excel.workbooks.open?view=excel-pia).

## What the Revit API documentation establishes

**High confidence:** Revit 2025 is a relevant compatibility boundary. Autodesk
states that Revit 2025 and later are built on .NET 8 and that legacy add-ins
need to be rebuilt for .NET 8. It also calls out changed assembly-loading
behavior. Revit 2024 used .NET Framework 4.8, so the 2024-versus-2025 result
matches a change in the managed host that is exposing the Excel COM object.

The Revit 2026.5 status shown in the report is also significant: Autodesk says
that update includes the .NET 10 Windows Desktop Runtime and warns that its
.NET 10 update can cause add-in compatibility issues. The common failure in
2025 and 2026.5 makes this *not* a .NET-10-only regression; it is more likely
an incompatibility in the post-2024 pyRevit/IronPython-to-Excel-PIA boundary.

Autodesk documents Revit external commands as in-process code, with Revit API
access restricted to its main thread. That governs Revit API calls, but there
is no Revit API method involved in the failing `Workbooks.Open` dispatch. No
documented Revit transaction, schedule-export, or image API change can repair
this particular exception.

Sources: [Autodesk: migrate from .NET 4.8 to .NET 8](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API/files/Revit_API_Developers_Guide/Introduction/Getting_Started/Using_the_Autodesk_Revit_API/Revit_API_Revit_API_Developers_Guide_Introduction_Getting_Started_Using_the_Autodesk_Revit_API_NET8_Update_html.html),
[Autodesk: Revit 2026.5 update](https://help.autodesk.com/view/RVT/2026/ENU/?guid=RevitReleaseNotes_2026updates_2026_5_html),
[Autodesk: deployment and main-thread rules](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API/files/Revit_API_Developers_Guide/Introduction/Getting_Started/Using_the_Autodesk_Revit_API/Revit_API_Revit_API_Developers_Guide_Introduction_Getting_Started_Using_the_Autodesk_Revit_API_Deployment_Options_html.html).

## Likely technical cause

**Medium confidence:** the command's existing `Excel.ApplicationClass()`
activation and IronPython member binding no longer preserve the typed
`Excel.Workbooks` interface under the newer Revit runtime. Excel activation
itself succeeded; the returned `Workbooks` value is instead exposed as a raw
`System.__ComObject`, so IronPython cannot resolve the PIA's `Open` member.

This is a host/managed-COM binding issue, not proof of an Autodesk Revit API
defect or an Office installation defect. Microsoft marks `ApplicationClass` as
"Reserved for internal use," so it should not be treated as a stable automation
activation contract. Do not switch to the PIA's `_Open` member: Microsoft also
marks that member as internal.

Sources: [Microsoft: ApplicationClass](https://learn.microsoft.com/en-us/dotnet/api/microsoft.office.interop.excel.applicationclass?view=excel-pia),
[Microsoft: Workbooks._Open](https://learn.microsoft.com/en-us/dotnet/api/microsoft.office.interop.excel.workbooks._open?view=excel-pia),
[Microsoft: Office primary interop assemblies](https://learn.microsoft.com/en-us/visualstudio/vsto/office-primary-interop-assemblies?view=visualstudio).

## Implemented compatibility boundary

`lib/excel_com.py` now provides an explicit façade for Carbon GWP Pull, Steel
PSF, and Concrete Mix Header. It owns application creation and workbook
lifecycle plus named property, method, and collection-item operations. Every
Excel access in those commands — including worksheets, cells, ranges, queries,
tables, pivots, charts, refreshes, and shutdown — uses that façade. A raw
`System.__ComObject` is sent directly to `System.Type.InvokeMember` through
`IDispatch`; it is never wrapped in a proxy that guesses whether a member is a
property or a method. That specifically prevents the observed sequence where
`Close` is exposed as a non-callable boolean after `Open` and `Add` were fixed.

The façade does not use the PIA's internal `_Open` member. Workbook opens
temporarily force automation macros off, and cleanup always attempts both
`Close(False)` and `Quit()`. A cleanup error is retained without replacing the
primary export error.

The shared unit tests cover direct PIA-shaped calls, raw-COM property/method/
item dispatch, misleading raw `Close`/`Save` attributes, argument-array
conversion, macro-security restoration, and cleanup. They cannot prove that a
Revit-hosted Excel COM server accepts the façade.

Sources: [Microsoft: Type.InvokeMember](https://learn.microsoft.com/en-us/dotnet/api/system.type.invokemember?view=net-7.0),
[Microsoft: Workbooks.Open](https://learn.microsoft.com/en-us/dotnet/api/microsoft.office.interop.excel.workbooks.open?view=excel-pia).

## Remaining live diagnostic

First run `Dev-Sandbox > Prototypes > Excel COM Smoke Test` once in each
affected Revit host. It creates only a UUID-owned temporary XLSX and CSV,
reports every façade operation in one table, reopens the workbook read-only,
and removes successful-run assets. A failed run preserves only its exact owned
assets for diagnosis. Record the Revit build and the table output before
running Carbon, Steel, or Concrete again.

If the smoke test fails, retain the runtime type and operation detail from its
table. A strongly typed .NET PIA probe is then appropriate only when its result
would distinguish an Office/PIA registration issue from the Python-to-COM
boundary. Do not use a user workbook for that diagnosis.

## Release acceptance still required

Record a Revit 25 and Revit 26 live smoke-test case before release acceptance,
then record Carbon's trusted-workbook case for open, write, save, read-only
refresh, close, and quit. If the smoke test fails, retain its complete table
before investigating Office/PIA registration or repair.
