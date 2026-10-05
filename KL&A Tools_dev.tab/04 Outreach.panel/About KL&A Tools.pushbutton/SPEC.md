# About KL&A Tools

## Identity

- **Tool ID:** `about-kla-tools`
- **Path aliases:** `KL&A Tools_dev.tab/04 Outreach.panel/About KL&A Tools.pushbutton`, `KL&A Tools.tab/04 Outreach.panel/About KL&A Tools.pushbutton`, `KL&A Tools.tab/05 DevSandbox.panel/About KL&A Tools.pushbutton`, `KL&A Tools_dev.tab/05 DevSandbox.panel/About KL&A Tools.pushbutton`.
- **Version inputs:** `KL&A Tools_dev.tab/04 Outreach.panel/About KL&A Tools.pushbutton/bundle.yaml`, `KL&A Tools_dev.tab/04 Outreach.panel/About KL&A Tools.pushbutton/script.py`.
- **Tool version:** `v1.1`
- **Status/origin:** Maintained production; KL&A custom command.
- **Status:** Released.
- **Maintainer:** KL&A.
- **Ribbon location:** `KL&A Tools_dev.tab/04 Outreach.panel/About KL&A Tools.pushbutton`.
- **Live acceptance:** Exact-version Revit/pyRevit acceptance is not recorded.

## Purpose

Show the loaded extension's version identity, channel, identity date, metadata
source commit, build date, loaded path, and Revit/pyRevit versions for support.

## Behavior

This zero-document command reads generated `lib/build_info.py` and shows a
pyRevit alert. It does not modify the model, query Git, or open Excel. The loaded
extension path identifies the actual folder supplying the command and metadata.

`VERSION_LABEL` is a display identity such as `v0.0.11-dev`; it does not assert
that a Git tag exists. `METADATA_SOURCE_SHA` is HEAD when the metadata was
generated, preceding any preparation commit and squash merge. It does not prove
the loaded checkout's current HEAD. Verified release commits and tags are in
`docs/releasing/tool-version-delivery-ledger.md`.

## Validation boundary

Static tests check the displayed identity and provenance labels with host stubs.
Live acceptance must confirm the alert and expected loaded extension path in
the intended Revit/pyRevit installation. No new live Revit claim is made.

The development metadata-label clarification does not increment the independent
tool version: metadata/documentation normalization is excluded by the tool-version
rules. The functional delivery history below remains unchanged.

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
