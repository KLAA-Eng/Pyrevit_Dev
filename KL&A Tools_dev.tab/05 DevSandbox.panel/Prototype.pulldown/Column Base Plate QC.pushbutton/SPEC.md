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
| v0.0 | Unreleased | 10.29.2026 | First DevSandbox base plate drawing: reads the base plate schedule and anchor rod table text and each type's shape and rods from its detail drawing, draws each column's plate, rods, and mark as a detail group along the supporting wall, flags fit problems, and clears drawn plates. | Pending commit on `dev.column-baseplate-qc`; pending next main delivery. |

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
  at the first row below the table whose MARK cell is not a mark. Drafted
  ("dumb") schedules may hold one note per cell, one multi-line note per
  column (each line is placed in its row by sharing the note's height
  evenly), or one note per row with values separated by tabs or two or more
  spaces.
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

- **Base plate detail types.** In the same view, each detail above a text
  note reading `TYPE <key>` (TYPE A, TYPE B, ...) defines that type; see
  [Detail types](#detail-types).

A schedule drawn as an imported or linked CAD file cannot be read; its text
is not available to the API. When the schedule rows, the anchor rod table,
or any detail type cannot be read, the schedule view's text notes,
linework, and dimensions are written to
`%LOCALAPPDATA%\KLA Tools\Column Base Plate QC\schedule_view.json` and the
palette names the file. Walls in linked models are not used.

## Detail types

Types are read from the drawing, not built in, so a changed or added detail
changes the plates (`lib/baseplate_qc/details.py`):

- **Area.** A detail's area is above its label, half the gap to the
  neighboring labels each side, up to the first wide text above (a table
  note).
- **Plate outline.** The largest closed loop of lines in the area (detail
  lines, detail components, filled regions, or imported CAD). Lines dangling
  off an outline are ignored. Four corners is a **square** plate (drawn
  sides within 15%) or a **rectangular** plate; six corners is an
  **L-shaped** plate. Any other outline, an outline not square to the page,
  or an L whose legs differ by more than 15% is too complex: the type is left
  out, the palette says why, and its columns are listed but not drawn.
- **L and W.** For square and rectangular plates, a dimension whose text is
  overridden to `L` gives the L direction (else the longer drawn side); W is
  across it. An L-shaped plate has two legs, each L long and W wide, meeting
  at a W x W corner.
- **Anchor rods.** Circles inside the plate (concentric circles are one
  rod). Each rod coordinate takes the nearest rule: "C" from a plate edge;
  "C" from the inside of an L leg; "C" from an L leg end; the middle of the
  plate or leg; or the middle plus or minus half of a dimensioned spacing.
  A dimension counts as a spacing when it is measured (its length is the
  true spacing, such as 2 1/2") or typed over with a size; a rule from a
  spacing wins a near tie. A rod matching no rule leaves the type out.
- **"C".** The drawn edge distance is the dimension typed over to `C`, else
  the smallest drawn rod-to-edge distance. The true "C" comes from the
  anchor rod requirements table for the scheduled rod diameter.
- **Column.** The largest other loop inside the plate (not around a rod);
  it must be centered on a square or rectangular plate, or in the corner
  square of an L, or the type is left out.

## Layout rules

- The column point is the column's center on the plate as drawn in its
  detail.
- For square and rectangular plates, **L** runs along the supporting wall's
  location line and **W** across it. Without a wall, L runs along the
  column's hand orientation (its width direction).
- For L-shaped plates, one leg runs along the supporting wall toward its
  longer run from the column. The other leg follows a crossing wall at the
  column (within 17 degrees of square) toward that wall's longer run; with
  no crossing wall it takes one side and the column is flagged. A plate
  corner past the faces of both walls is an overhang.

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
- its type has no detail or the detail was left out (not drawn);
- its plate hangs past a face of the supporting wall (more than 1/16");
- the column outline is larger than the plate;
- a rod circle falls on the column outline;
- a rod falls outside the plate (too small for the edge distance), the rod
  diameter has no edge distance (rods not drawn), or the schedule's rod
  count differs from the detail's;
- an L-shaped plate has no crossing wall, or its W is not less than L;
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
