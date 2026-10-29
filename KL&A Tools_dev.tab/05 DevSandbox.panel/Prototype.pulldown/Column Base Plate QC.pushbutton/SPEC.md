# Column Base Plate QC

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.column-base-plate-qc` |
| Tool version | `v0.0` |
| Status | Unreleased prototype; live acceptance pending |
| Status/origin | Prototype; KL&A custom tool. |
| Main delivery | Unreleased |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Column Base Plate QC.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Column Base Plate QC.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Column Base Plate QC.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Column Base Plate QC.pushbutton/script.py`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Column Base Plate QC.pushbutton/BasePlateQcPalette.xaml`; `lib/baseplate_qc/` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | Unreleased | 10.29.2026 | First DevSandbox base plate drawing: reads the base plate schedule and anchor rod table text, draws each column's plate, rods, and mark as a detail group along the supporting wall, flags fit problems, and clears drawn plates. | Pending commit on `dev.column-baseplate-qc`; pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Purpose

Engineers check that each column's scheduled base plate fits the wall or
pier it bears on. This prototype draws every column's base plate in the
active plan view at true size from the column's `Column Base Plate Type`
parameter and the base plate schedule in the drawing set, so plates that hang
past a wall face or clash with the column are visible at a glance.

## Inputs

- **Column mark.** The `Column Base Plate Type` instance (or type) parameter
  of each structural column visible in the active plan view, for example
  `BP7`. Marks compare without case, spaces, or hyphens.
- **Base plate schedule.** Text notes in one view (a drafting view, legend,
  or sheet) that include the title `BASE PLATE SCHEDULE`. The palette lists
  every such view; the first is chosen. The header row is the row holding a
  cell reading exactly `MARK` with `TYPE`, `DIM L`, and `DIM W`; `THICKNESS`,
  `NUMBER`, `SIZE`, and `EMBED` are read when present. Rows are rebuilt from
  the notes' heights and columns from the nearest header, and reading stops
  at the first row below the table whose MARK cell is not a mark.
- **Anchor rod requirements.** In the same view, the table whose header has
  an `ANCHOR ROD` column and an `EDGE DISTANCE` column gives the edge
  distance "C" for each rod diameter. Without it, the built-in KL&A values
  are used: 3/4" 1 1/2", 7/8" 2", 1" 2 1/2", 1 1/4" 2 1/2", 1 1/2" 2 1/2".
- **Walls.** Walls in the host model whose location line is within half the
  wall width plus 6" of the column point, and whose height range is within
  2 ft of the column base. The closest one supports the column.
- **Column size.** Read from an HSS type name (`HSS3x3x3/8`, `HSS8x4x1/2`,
  `HSS6.625x.280`), else from type parameters `d`/`bf`, `Depth`/`Width`, or
  `h`/`b`. The size only draws the column outline and its checks.

A schedule drawn as an imported or linked CAD file cannot be read; its text
is not available to the API. Walls in linked models are not used.

## Layout rules

The geometry follows the base plate detail (Types A, B, and C):

- The column is centered on the plate in both directions.
- Plate **L** runs along the supporting wall's location line and **W**
  across it. Without a wall, L runs along the column's hand orientation (its
  width direction).
- **Types A and B:** four rods, one in each plate corner, "C" in from both
  edges.
- **Type C:** two pairs of rods, "C" in from each L end; the rods of a pair
  are 2 1/2" apart across W, centered on the column.
- An unknown type is drawn as Type A and flagged.

These rules are the prototype's reading of the detail and need engineer
confirmation; the constants live in `lib/baseplate_qc/layout.py`.

## Drawing

Draw Base Plates in Active View works in a plan view. In one transaction it
deletes the view's earlier base plate drawing, then, for each column with a
readable schedule entry, draws detail lines for the plate outline, circles
at rod diameter, a gray column outline, and a text note such as
`BP7 (A) 9x8` beside the plate. These elements become one detail group whose
group type is named `KLA BP QC - <mark> - <column id> - <view id>`. Plate,
rods, and text are blue, or red when the column has an issue, through
per-view element overrides. Drawing creates detail groups and group types;
Undo reverses the whole draw.

## Checks and report

A column is listed for review, and selected in Revit, when:

- it has no `Column Base Plate Type`, or its mark is not in the schedule, or
  the schedule row has no readable L or W;
- its plate hangs past a face of the supporting wall (more than 1/16");
- the column outline is larger than the plate;
- a rod circle falls on the column outline;
- the plate is too small for the rod edge distance, the rod diameter has no
  edge distance (rods not drawn), or the schedule lists other than four rods;
- its size could not be read (the plate is drawn without the column outline).

The pyRevit output window lists flagged columns with clickable ids, the mark,
plate, orientation source, and issues, plus any schedule reading problems.

## Clearing

- **Clear Active View** deletes the tool's group types placed in the active
  view, and so their groups.
- **Clear All Views** deletes every group type whose name starts with
  `KLA BP QC - ` in the model.
- **Delete base plates drawn here when this closes** (on by default) deletes
  the group types drawn while the palette was open when it closes. Drawings
  from earlier sessions, and plates in a model closed before the palette,
  stay until cleared. If Revit itself closes with the palette open, nothing
  is deleted; the plates are saved only if the model is saved.

## Limits

The command writes a log to
`%LOCALAPPDATA%\KLA Tools\Column Base Plate QC\baseplate_qc.log` on failure.
It does not persist settings or modify the columns. Live acceptance remains
required in Revit 2023 through 2026 with a project whose schedule is text
notes, including rotated columns, curved walls, and columns without walls.
