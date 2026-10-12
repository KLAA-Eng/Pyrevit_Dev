# Invoke C# DLL Button Template

## Purpose

Demonstrates pyRevit metadata for invoking a compiled C# command.

## Behavior

The bundle declares the target assembly and command-class metadata and is safe
with no active document. The actual command contract is owned by the referenced
assembly, not by this bundle.

## Validation boundary

Validate assembly resolution, command-class configuration, and the external
assembly's compatibility with the installed Revit/pyRevit version.

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
