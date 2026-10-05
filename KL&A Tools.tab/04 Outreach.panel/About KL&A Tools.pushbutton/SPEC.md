# About KL&A Tools

## Identity

- **Tool ID:** `about-kla-tools`
- **Path aliases:** `KL&A Tools.tab/04 Outreach.panel/About KL&A Tools.pushbutton`, `KL&A Tools.tab/05 DevSandbox.panel/About KL&A Tools.pushbutton`, `KL&A Tools_dev.tab/05 DevSandbox.panel/About KL&A Tools.pushbutton`.
- **Version inputs:** `KL&A Tools_dev.tab/04 Outreach.panel/About KL&A Tools.pushbutton/bundle.yaml`, `KL&A Tools_dev.tab/04 Outreach.panel/About KL&A Tools.pushbutton/script.py`.
- **Tool version:** `v1.1`
- **Status/origin:** Maintained production; KL&A custom command.
- **Status:** Released.
- **Maintainer:** KL&A.
- **Ribbon location:** `KL&A Tools_dev.tab/04 Outreach.panel/About KL&A Tools.pushbutton`.
- **Live acceptance:** Exact-version Revit/pyRevit acceptance is not recorded.

## Purpose

Documents the current command implementation and intended user-facing behavior.

## Behavior

This command is implemented by `script.py` in this pyRevit bundle. It runs in the Revit/pyRevit host and uses the active-document context required by its implementation. It must preserve unrelated model content and report unsupported or cancelled interactions without applying partial changes.

## Validation boundary

Validate this command against a representative Revit fixture, its empty or cancelled-input path, and its documented output or transaction effect before promotion beyond development use.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: import os;import sys;from pyrevit import forms;import pyrevit;import build_info;
- Local helper functions: find_extension_root,get_pyrevit_version,get_revit_build,main,
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

This utility is visible on the production ribbon panels of the development
extension. The implementation inventory is static; its external application or
form behavior still requires representative live acceptance.

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| `v1.0` | `0.0.0.beta` | 07.16.2026 | Delivered the extension/build metadata, loaded path, pyRevit version, and Revit build dialog. | `484924b` |
| `v1.1` | `0.0.1.beta` | 08.13.2026 | Delivered loaded-extension library resolution so build metadata imports work from the actual checkout. | `78b2aee` |

Versions follow meaningful changes between adjacent mainline release snapshots,
including the listed version inputs. Earlier development iterations are grouped
into the first delivery; tab/panel moves, formatting, and metadata/documentation
changes do not create additional milestones. Dates use `MM.DD.YYYY`; released
rows use the main delivery date, and Unreleased rows use the latest meaningful
development change date.
