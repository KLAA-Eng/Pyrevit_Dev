# FindReplace - Views

## Purpose

Documents the current command implementation and intended user-facing behavior.

## Behavior

This command is implemented by `script.py` in this pyRevit bundle. It runs in the Revit/pyRevit host and uses the active-document context required by its implementation. It must preserve unrelated model content and report unsupported or cancelled interactions without applying partial changes.

## Validation boundary

Validate this command against a representative Revit fixture, its empty or cancelled-input path, and its documented output or transaction effect before promotion beyond development use.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: from Autodesk.Revit.DB import *;from Renaming.BaseClass_FindReplace import BaseRenaming;from Snippets._context_manager import ef_Transaction, try_except;from Snippets._selection import get_selected_views;
- Local helper functions: __init__,get_selected_elements,rename_elements,
- Bundled external assets: None.

## GUI and interaction

Static UI/API references: No explicit forms, WPF, or pyRevit-output API detected.

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

## Tool versioning

| Field | Value |
| --- | --- |
| Tool ID | `core.rename.findreplace-views` |
| Path aliases | `KL&A Tools.tab/03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton` (0.0.0.beta–0.0.9); current `KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton` |
| Version inputs | `bundle.yaml`; `script.py` (no KL&A-owned shared helper inputs) |
| Tool version | `v1.2.EFTools` |
| Status/origin | Special — imported unchanged from EF Tools. |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| `v1.2.EFTools` | `0.0.0.beta` | 07.16.2026 | Unchanged EF Tools 1.2 source present in the first mainline delivery ledger. | Upstream header; `484924b`; import `6a46157` |
