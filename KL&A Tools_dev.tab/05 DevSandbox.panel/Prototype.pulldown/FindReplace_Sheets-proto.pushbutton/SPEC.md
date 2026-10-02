# FindReplace_Sheets

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.findreplace-sheets-proto` |
| Tool version | `v0.0` |
| Status | Released |
| Status/origin | Prototype; locally maintained KL&A adaptation of EFTools (Erik Frits). |
| Main delivery | 0.0.6beta |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/script.py`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/Script.xaml` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v1.1.EFTools | 0.0.5.beta | 08.20.2026 | First prototype delivery of the unchanged EFTools version 1.1 functionality. | 8cd45f8 |
| v0.0 | 0.0.6beta | 09.15.2026 | First main delivery of the local KL&A prototype adaptation using shared WPF resources. | 300f8d4 |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Purpose

Documents the current command implementation and intended user-facing behavior.

## Behavior

This command is implemented by `script.py` in this pyRevit bundle. It runs in the Revit/pyRevit host and uses the active-document context required by its implementation. It must preserve unrelated model content and report unsupported or cancelled interactions without applying partial changes.

## Validation boundary

Validate this command against a representative Revit fixture, its empty or cancelled-input path, and its documented output or transaction effect before promotion beyond development use.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: from Autodesk.Revit.DB import *;from Autodesk.Revit.Exceptions import ArgumentException;from pyrevit import forms;from Snippets._selection        import get_selected_sheets;from clr import AddReference;from System.Diagnostics.Process import Start;from System.Windows.Window      import DragMove;from System.Windows.Input       import MouseButtonState;from Autodesk.Revit.UI import DockablePanes, DockablePane;
- Local helper functions: update_project_browser,__init__,rename,rename_sheet_name,rename_sheet_number,sheet_number_find,sheet_number_replace,sheet_number_prefix,sheet_number_suffix,sheet_name_find,sheet_name_replace,sheet_name_prefix,sheet_name_suffix,button_close,Hyperlink_RequestNavigate,header_drag,button_run,
- Bundled external assets: None.

## GUI and interaction

Static UI/API references: forms.WPFWindow,

Use the command from its pyRevit button. Where it exposes a dialog or selection
workflow, make the required selection and review the result before confirming.

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
