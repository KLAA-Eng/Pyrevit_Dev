# Revision Cloud Sheets

## Identity

| Field | Value |
| --- | --- |
| Bundle path | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Revision Cloud Sheets.pushbutton` |
| Tool ID | `devsandbox.revision-cloud-sheets` |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Revision Cloud Sheets.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Revision Cloud Sheets.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Revision Cloud Sheets.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Revision Cloud Sheets.pushbutton/script.py`; `lib/revision_cloud_sheets/` |
| Maturity | Prototype |
| Tool version | `v0.0` |
| Status/origin | Prototype; KL&A custom tool. Status: Unreleased; main delivery: Unreleased. |
| Maintainer | KL&A |
| Revit versions live-tested | None yet |

## Purpose and workflow

`Revision Cloud Sheets` answers "which sheets is this revision cloud on?"
and "which sheets carry this revision?".
It is the inverse of `Find All Revision Clouds`, which groups clouds by sheet.
A cloud drawn in a primary view can appear on several sheets through that
view's dependent views, so one cloud may list more than one sheet.

1. Select one or more revision clouds, or select nothing to report every
   revision cloud in the model.
2. Run the command and choose `Sheets by revision` or `Sheets by cloud`.
   Closing the choice cancels without output.
3. Review the pyRevit output table.

For every non-placeholder sheet, the command reads
`ViewSheet.GetAllRevisionCloudIds()`, which returns clouds placed on the sheet
and clouds in views placed on it, then inverts that map per cloud
(`lib/revision_cloud_sheets/mapping.py`). Sheets are sorted naturally by sheet
number, so `S-2` comes before `S-10`.

## Inputs and prerequisites

- Report choice: `Sheets by revision` or `Sheets by cloud`. Closing the
  choice cancels without output.
- Selected revision clouds in the active document. Selected elements that are
  not revision clouds are ignored. When no revision cloud is selected, every
  revision cloud in the model is reported.
- No external files, libraries, or packages beyond pyRevit.

## Outputs and effects

The command closes other pyRevit output windows, then prints the command
title, the chosen report, and the scope (selected revision clouds or all
revision clouds in the model) with its cloud count. When there are no clouds,
it prints `No revision clouds were found.` and stops.

`Sheets by revision`: one row per revision and sheet, ordered by revision
sequence and then by sheet number. A sheet is listed under a revision when at
least one in-scope cloud of that revision is on it; the row shows the revision
(sequence, number, description), sheet number, sheet name, and how many of
that revision's clouds the sheet shows. Grouping lives in
`sheets_by_revision`. The report then prints the number of revisions on
sheets.

`Sheets by cloud`: one row per cloud, ordered by revision sequence: revision,
a clickable cloud ID, the owner view (shown as `Sheet: <number> - <name>` when
the cloud is drawn on a sheet), the sheet count, and the sheet list,
plus the number of clouds that are not shown on any sheet.

Both reports end with the number of distinct sheets.

A cloud whose revision cannot be found is labeled `Revision not found` and
sorted last. An unexpected error prints a runtime error section with the
traceback in the output window.

Model and external effects: read-only. No transaction is opened and nothing
is written to disk.

## Limits and compatibility

- Linked-model clouds are not reported.
- Placeholder sheets are ignored.
- `bundle.yaml` sets no minimum Revit version. Element IDs are read through
  `ElementId.Value` with an `IntegerValue` fallback, and the revision number
  falls back to the sequence number when `RevisionNumber` cannot be read. No
  Revit version is confirmed until live testing.

## Validation evidence

| Date | Extension release | Revit version | Scenario | Result | Evidence link or location |
| --- | --- | --- | --- | --- | --- |
| 2026-10-29 | Unreleased | None | `tests/revision_cloud_sheets_test.py` mapping and sort rules | Pass | Local unit test run |
| 10.30.2026 | `0.0.14-dev` | None (CPython) | `tests/revision_cloud_sheets_test.py` | Pass | Local run on `dev.revision-cloud-sheets` |

Automated checks do not prove Revit behavior or the user workflow.
Live Revit acceptance is still required: a cloud on a sheet, a cloud in a
placed view, a cloud in a primary view with dependents on two sheets, and a
cloud in an unplaced view.

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | Unreleased | 10.29.2026 | First prototype of the revision and cloud sheet reports. | Pending development commit on `dev.revision-cloud-sheets`. |

Versions reconstruct meaningful main-release deliveries. Dates use MM.DD.YYYY.

## Backlog

- Live Revit acceptance: a cloud on a sheet, a cloud in a placed view, a
  cloud in a primary view with dependents on two sheets, and a cloud in an
  unplaced view.
