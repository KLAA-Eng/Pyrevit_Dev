# Command Name

## Identity

| Field | Value |
| --- | --- |
| Bundle path | `KL&A Tools_dev.tab/.../Command.pushbutton` |
| Tool ID | replace-with-stable-command-id |
| Path aliases | Record current path and any previous bundle paths. |
| Version inputs | `bundle.yaml`; `script.py`; list owned/shared helpers. |
| Maturity | Prototype, Beta, or Core |
| Tool version | `v0.0` |
| Status/origin | KL&A DevSandbox prototype; identify original source if imported. |
| Maintainer | Name or team |
| Revit versions live-tested | List exact tested versions |

## Purpose and workflow

State the user problem, intended users, and the result this command provides.
Describe the normal user workflow in plain language, including any choices,
confirmation points, and where users should review the result.

## Inputs and prerequisites

- Active Revit context, selected elements, sheets, views, files, or schedules.
- Required model conditions and user permissions.
- Required workstation software, packages, configuration, and external files.

## Outputs and effects

Describe pyRevit output, dialogs, model changes, graphics overrides, files,
workbooks, launched applications, and external services. State what the command
does not change and how cancellation avoids partial work.

## Limits and compatibility

List exclusions, unsupported cases, known limits, Revit compatibility, and
error or skip reporting. Revit 2024 and later is the design target; only exact
versions with live evidence may be claimed as supported.

## Validation evidence

| Date | Extension release | Revit version | Scenario | Result | Evidence link or location |
| --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD | `0.0.0-beta` | 2024 | Representative workflow | Pass or fail | Link or path |

Record focused automated/static checks separately from live Revit acceptance.
Automated checks do not prove Revit transactions, native dialogs, Excel COM,
file outputs, or user workflow.

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| `v0.0` | Unreleased | 10.02.2026 | Planned prototype template baseline; replace with actual command evidence. | Template example; replace with development commit evidence. |

Follow `docs/guides/TOOL_VERSIONING.md`. Use meaningful user-facing Git
milestones; promote a maintained DevSandbox command to production at `v1.0`.
Keep extension release evidence above separate from the independent tool version.

## Backlog

- Planned feature or improvement.
- Known issue or validation still needed.
