# URL Button Template

## Purpose

Demonstrates a pyRevit URL button.

## Behavior

The bundle opens the configured developer-documentation hyperlink through
pyRevit metadata. It runs without a Revit document and does not modify model
content.

## Validation boundary

Validate the destination URL and browser launch behavior, including execution
with no active Revit document.

## Implementation inventory

- Entry point: no Python script
- Direct imports: No Python entry point; behavior is supplied by bundle metadata or bundled assets.
- Local helper functions: Not applicable.
- Bundled external assets: None.

## GUI and interaction

Static UI/API references: No explicit GUI API detected.

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
