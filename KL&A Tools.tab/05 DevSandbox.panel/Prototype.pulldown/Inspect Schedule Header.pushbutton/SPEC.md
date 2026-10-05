# Inspect Schedule Header

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.inspect-schedule-header` |
| Tool version | `v0.0` |
| Status | Released |
| Status/origin | Prototype; KL&A custom tool. |
| Main delivery | 0.0.6beta |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Inspect Schedule Header.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Inspect Schedule Header.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Inspect Schedule Header.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Inspect Schedule Header.pushbutton/script.py` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | 0.0.6beta | 09.15.2026 | First main delivery of read-only schedule header inspection and JSON/CSV export. | 300f8d4 |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Purpose

`Inspect Schedule Header` is a read-only DevSandbox pyRevit prototype for
capturing the layout of a selected Revit schedule header.

The output is intended to tune tools such as `Concrete Mix Header`, where the
script needs to write Excel data into an existing schedule header without
guessing at rows, columns, widths, merged cells, or styles.

## Workflow

The command asks the user to select one schedule from the active Revit document,
then asks for an export folder. It writes:

- `<schedule-name>_header_inspection_<timestamp>.json`
- `<schedule-name>_header_cells_<timestamp>.csv`

It does not start a Revit transaction and does not modify the model.

## Captured Data

The JSON file includes:

- document title;
- schedule name and element id;
- schedule definition metadata when available;
- header section row/column counts;
- first/last row and column numbers;
- row heights when available;
- column widths when available;
- every header cell's row, column, offsets, text, style properties, and
  accessible merged-cell metadata.

The CSV file includes a flat cell list with row, column, offsets, text, width,
height, and merge summary fields.

## Limits

Revit exposes schedule table style data differently across versions. Unsupported
style, width, height, or merge APIs are captured as blank values or warnings
instead of stopping the export.

This inspector captures API-visible metadata. It should still be paired with a
PDF or screenshot when visual matching matters.
