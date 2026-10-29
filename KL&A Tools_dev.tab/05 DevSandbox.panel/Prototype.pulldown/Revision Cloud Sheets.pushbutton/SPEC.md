# Revision Cloud Sheets

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.revision-cloud-sheets` |
| Tool version | `v0.0` |
| Status | Unreleased |
| Status/origin | Prototype; KL&A custom tool. |
| Main delivery | Unreleased |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Revision Cloud Sheets.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Revision Cloud Sheets.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Revision Cloud Sheets.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Revision Cloud Sheets.pushbutton/script.py`; `lib/revision_cloud_sheets/` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | Unreleased | 10.29.2026 | First prototype of the cloud-to-sheet report. | Pending development commit on `dev.revision-cloud-sheets`. |

Versions reconstruct meaningful main-release deliveries. Dates use MM.DD.YYYY.

## Purpose

`Revision Cloud Sheets` answers "which sheets is this revision cloud on?".
It is the inverse of `Find All Revision Clouds`, which groups clouds by sheet.
A cloud drawn in a primary view can appear on several sheets through that
view's dependent views, so one cloud may list more than one sheet.

## Inputs

- Selected revision clouds in the active document. When no revision cloud is
  selected, every revision cloud in the model is reported.

## Behavior

For every non-placeholder sheet, the command reads
`ViewSheet.GetAllRevisionCloudIds()`, which returns clouds placed on the sheet
and clouds in views placed on it, then inverts that map per cloud
(`lib/revision_cloud_sheets/mapping.py`). Sheets are sorted naturally by sheet
number.

## Output

A pyRevit output table with one row per cloud, ordered by revision sequence:
revision (sequence, number, description), a clickable cloud ID, the owner
view, the sheet count, and the sheet list. A summary gives the number of
distinct sheets and the number of clouds that are not shown on any sheet.

## Model and external effects

Read-only. No transaction is opened and nothing is written to disk.

## Limits

- Linked-model clouds are not reported.
- Placeholder sheets are ignored.

## Validation evidence

| Date | Extension release | Revit version | Scenario | Result | Evidence link or location |
| --- | --- | --- | --- | --- | --- |
| 2026-10-29 | Unreleased | None | `tests/revision_cloud_sheets_test.py` mapping and sort rules | Pass | Local unit test run |

Live Revit acceptance is still required: a cloud on a sheet, a cloud in a
placed view, a cloud in a primary view with dependents on two sheets, and a
cloud in an unplaced view.
