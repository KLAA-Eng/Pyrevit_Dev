# Prototype Request

## Identity

- **Tool ID:** `prototype-request`
- **Path aliases:** `KL&A Tools.tab/04 Outreach.panel/Prototype.pushbutton`.
- **Version inputs:** `KL&A Tools_dev.tab/04 Outreach.panel/Prototype.pushbutton/bundle.yaml`, `KL&A Tools_dev.tab/04 Outreach.panel/Prototype.pushbutton/script.py`.
- **Tool version:** `v1.0`
- **Status/origin:** Maintained production utility; KL&A internal derivative of the KL&A Suggestions command.
- **Status:** Released.
- **Maintainer:** KL&A.
- **Ribbon location:** `KL&A Tools_dev.tab/04 Outreach.panel/Prototype.pushbutton`.
- **Live acceptance:** Exact-version Revit/pyRevit acceptance is not recorded.

## Purpose

Open the KL&A prototype request Microsoft Form in the user's default browser.

## Behavior

The command opens `FORM_URL` through Windows' registered URL handler. It needs
no active Revit document, gathers no Revit context, and does not submit the form.

## Validation boundary

Confirm in Revit that the button opens the intended browser form with no active
document. Form access, questions, branching, and submission require live browser
acceptance and are controlled by the form, not by this command.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: `os`.
- Local helper functions: `main`.
- Bundled external assets: None.

## GUI and interaction

Click the button, then complete and submit the request in the browser.

## Current execution logic

pyRevit executes `main()`, which calls `os.startfile(FORM_URL)`.

## Model and external effects

Opens an external browser URL. No Revit transaction or model edit occurs.

## Current status

This utility is visible on the production ribbon panels of the development
extension. Browser/form acceptance is not recorded here.

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| `v1.0` | `0.0.4.beta` | 08.17.2026 | First delivered Prototype Request bundle opens the dedicated Microsoft Form directly in the browser. | `1f3dd23` |

Versions follow meaningful changes between adjacent mainline release snapshots,
including the listed version inputs. Earlier development iterations are grouped
into the first delivery; tab/panel moves, formatting, and metadata/documentation
changes do not create additional milestones. Dates use `MM.DD.YYYY`; released
rows use the main delivery date, and Unreleased rows use the latest meaningful
development change date.
