# Launch Dynamo Script

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.launch-dynamo-script` |
| Tool version | `v0.0` |
| Status | Released |
| Status/origin | Prototype; KL&A custom tool. |
| Main delivery | 0.0.0.beta |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Launch Dynamo Script.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Launch Dynamo Script.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Launch Dynamo Script.pushbutton`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Launch Dynamo Script.pushbutton`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototypes.pulldown/Launch Dynamo Script.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Launch Dynamo Script.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Launch Dynamo Script.pushbutton/script.py`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Launch Dynamo Script.pushbutton/script.dyn` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | 0.0.0.beta | 07.16.2026 | First main delivery of the bundled Dynamo graph launcher. | 484924b |

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
- Direct imports: import os;import clr;from pyrevit import HOST_APP, forms;from Autodesk.Revit.UI import Result;from Dynamo.Applications import DynamoRevit, DynamoRevitCommandData, JournalKeys;
- Local helper functions: Top-level script flow.
- Bundled external assets: None.

## GUI and interaction

Static UI/API references: forms.alert,

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
