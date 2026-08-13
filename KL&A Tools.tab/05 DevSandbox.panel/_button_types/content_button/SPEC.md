# Content Button Template

## Purpose

Demonstrates a pyRevit content button that supplies bundled Revit family
content.

## Behavior

The bundle contains `.rfa` source assets and button metadata rather than a
Python command. pyRevit handles the content-button interaction; these binary
assets must not be replaced except through an explicitly approved content
update.

## Validation boundary

Validate in a disposable Revit project that the intended family content is
available and that both bundled assets remain intact.

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
