# Copy Legends to Other Documents

## Purpose

Documents the current command implementation and intended user-facing behavior.

## Behavior

This command is implemented by `script.py` in this pyRevit bundle. It runs in the Revit/pyRevit host and uses the active-document context required by its implementation. It must preserve unrelated model content and report unsupported or cancelled interactions without applying partial changes.

## Validation boundary

Validate this command against a representative Revit fixture, its empty or cancelled-input path, and its documented output or transaction effect before promotion beyond development use.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: import sys;from Autodesk.Revit.DB import Transaction, TransactionGroup;from pyrevit import revit, DB, script, forms;from pyrevit.framework import List;
- Local helper functions: OnDuplicateTypeNamesFound,__init__,log_message_with_doc_and_legend,get_messages,__len__,
- Bundled external assets: None.

## GUI and interaction

Static UI/API references: forms.ProgressBar,tool_dialogs.alert,forms.select_open_docs,forms.select_views,

Use the command from its pyRevit button. Where it exposes a dialog or selection
workflow, make the required selection and review the result before confirming.

## Current execution logic

pyRevit loads the bundle and executes its entry point. The implementation uses
the imports and helper functions listed above; inspect `script.py` for the exact
branching order and host API calls.

## Model and external effects

Detected mutation/external-effect patterns: .SetElementOverrides,TransactionGroup,

## Current status

This is a command. The inventory above is statically derived
from the current bundle and must be confirmed inside the target Revit/pyRevit
environment before promotion or behavior changes.

## Tool versioning

| Field | Value |
| --- | --- |
| Tool ID | `core.copy-legends-to-other-documents` |
| Path aliases | `KL&A Tools.tab/03 Core Tools.panel/Copy Legends to Other Documents.pushbutton` (0.0.0.beta–0.0.9); current `KL&A Tools_dev.tab/03 Core Tools.panel/Copy Legends to Other Documents.pushbutton` |
| Version inputs | `bundle.yaml`; `script.py` (no KL&A-owned shared helper inputs) |
| Tool version | `v1.0.pyRevit` |
| Status/origin | Special — imported unchanged from pyRevit. |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| `v1.0.pyRevit` | `0.0.0.beta` | 07.16.2026 | Unchanged pyRevit snapshot present in the first mainline delivery ledger. | `484924b`; import `5a385ee` |

## Standard-dialog adoption — development (2026-11-08)

OK notices use the shared Message dialog through `GUI.tool_dialogs.alert`. Existing message text, warning selection, acknowledgement, cancellation and early-stop behavior remain. Native file/folder pickers, progress, model operations and transaction boundaries are unchanged.

This presentation change belongs to the next planned tool-version delivery; current released version metadata is retained until delivery. Local adapter tests do not establish live Revit ownership, focus, DPI, or model-effect acceptance.


Document and legend-view selectors use GUI.tool_selectors and shared Selection. Destination documents exclude the active/linked documents and retain family documents. Existing selected eligible legend views can be reused after shared confirmation; otherwise the filtered list opens. Cancellation, progress and copy transactions remain unchanged.
