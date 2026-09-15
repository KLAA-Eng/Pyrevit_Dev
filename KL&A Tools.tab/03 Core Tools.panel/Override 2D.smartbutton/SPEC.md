# Override 2D

## Purpose

Documents the current command implementation and intended user-facing behavior.

## Behavior

This command is implemented by `script.py` in this pyRevit bundle. It runs in the Revit/pyRevit host and uses the active-document context required by its implementation. It must preserve unrelated model content and report unsupported or cancelled interactions without applying partial changes.

## Validation boundary

Validate this command against a representative Revit fixture, its empty or cancelled-input path, and its documented output or transaction effect before promotion beyond development use.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: from time import sleep;from pyrevit import DB, script, revit;from pyrevit import forms;from pyrevit.framework import List;from pyrevit.revit import ui;import pyrevit.extensions as exts;from graphics.overrides import create_red_projection_override;
- Local helper functions: set_config,__selfinit__,override_projection_lines,clear_overrides,collect_view_specific_elements,disable_temp_isolation,enable_temp_isolation,
- Bundled external assets: None.

## GUI and interaction

Static UI/API references: forms.WarningBar,forms.alert,script.get_output,

Use the command from its pyRevit button. Where it exposes a dialog or selection
workflow, make the required selection and review the result before confirming.

## Current execution logic

pyRevit loads the bundle and executes its entry point. The implementation uses
the imports and helper functions listed above; inspect `script.py` for the exact
branching order and host API calls.

## Model and external effects

Detected mutation/external-effect patterns: .SetElementOverrides,revit.TransactionGroup,

## Current status

This is a development-tab command. The inventory above is statically derived
from the current bundle and must be confirmed inside the target Revit/pyRevit
environment before promotion or behavior changes.
