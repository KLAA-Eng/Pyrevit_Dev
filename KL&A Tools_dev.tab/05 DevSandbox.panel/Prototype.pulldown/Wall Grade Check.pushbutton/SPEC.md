# Wall Grade Check

## Identity

| Field | Value |
| --- | --- |
| Bundle path | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Wall Grade Check.pushbutton` |
| Tool ID | `devsandbox.wall-grade-check` |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Wall Grade Check.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Wall Grade Check.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Wall Grade Check.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Wall Grade Check.pushbutton/script.py`; `lib/wall_grade/`; shared `lib/pdf_overlay/` (PDF source), `lib/error_reports.py`, and `lib/error_reports_revit.py` |
| Maturity | Prototype |
| Tool version | `v0.0` |
| Status/origin | KL&A DevSandbox prototype; KL&A custom tool. Unreleased (main delivery: Unreleased); live acceptance pending. |
| Maintainer | KL&A |
| Revit versions live-tested | None yet |

## Purpose and workflow

Engineers reviewing foundation walls need to see where finished grade sits
against each wall, and where soil comes too close to the top of the wall
(wood framing needs 8" clearance to exposed earth, IBC 2304.12.1.2). This
prototype draws the grade line along the outside face of the walls as
removable review linework and flags runs where grade is closer than the set
clearance to the top of wall, or at or above it. Grade comes from Revit
topography or from a PDF grading plan.

### Workflow

1. Select the walls to check. With nothing selected, the command uses every
   basic wall in the active view whose type Function is Foundation or
   Retaining.
2. Run the command and choose an action: **Grade from Revit topography**,
   **Grade from PDF grading plan**, or **Clear review lines**.
3. Enter the clearance in inches (default 8; values above 48 are capped and
   unreadable or non-positive entries use 8).
4. PDF only: pick the overlay (when there is more than one), then set the
   vertical placement in USGS: pick a reference level (for example T/SLAB or
   Level 1) and enter its USGS elevation, such as `5432.50` or `5432'-6"`.
   See USGS vertical placement below.
5. The command samples each wall every foot along its location curve, plus
   both ends, finds grade and top of wall at each station, and draws the
   grade as model lines on the exterior of the walls. In the active 3D view
   it sets up the review display (see Review display). Setting up and
   drawing form one undo step (`Wall Grade Check - Draw`). Flagged walls are
   selected.
6. The pyRevit output window lists each wall (clickable id) with its type,
   length, minimum clearance, flagged runs (station range and worst value),
   stations with no grade, and notes.
7. **Clear review lines** deletes every model line in the three review line
   styles, every text note of the review text type, and every PDF grade
   strip, in all views, and returns every view it set up in this model to
   normal (see Review display), in one transaction (`Wall Grade Check -
   Clear`).

### Review display (Temporary View Properties)

- Only in the active view, and only when it is a non-template 3D view;
  otherwise the report says to open the 3D view and run again.
- The command first turns on Revit's **Temporary View Properties** mode for
  the view with its own settings (`EnableTemporaryViewPropertiesMode(view.Id)`),
  so every display change below is temporary. While the mode is on, Revit
  shows the view as being in temporary view properties, and the user can also
  end it with Restore View Properties.
- In the view it then:
  - ghosts the Toposolid and Topography categories: 70% surface transparency
    and halftone, unhidden. Category overrides also reach linked topography
    shown By Host View;
  - unhides Lines and the three review line styles, Walls, Generic Models
    (PDF grade strips), and Text Notes, so the review always shows;
  - switches a Hidden Line or Wireframe view to Shaded, because see-through
    surfaces render only in shaded styles. Only in the temporary mode.
- This runs before grade is read, so topography hidden in the active 3D view
  is visible to the ray cast.
- **Clear review lines** turns the temporary mode off for every view the tool
  turned it on in, which returns the view exactly as it was.
- Fallback: when the mode cannot be turned on (it is already on, or the view
  does not allow it), the same category changes are made directly and the
  original transparency, halftone, and hidden state of each category are
  recorded; the display style is left alone. Clear restores exactly those
  settings, and also does so when the user already ended the temporary mode.
- Which views were set up, how, and the recorded originals are kept per
  model in `%LOCALAPPDATA%\KLA Tools\Wall Grade Check\ghosted_views.json`
  (first record per view and category kept). Because the record is local,
  Clear must run on the computer that set up the view; elsewhere, Restore
  View Properties ends the temporary mode by hand.
- A view template that controls visibility can block the changes; the report
  says so.
- PDF source only: there may be no Revit topography to ghost, so a flat,
  see-through grade strip 4 ft wide is added outside each wall at the PDF
  grade (a Generic Models DirectShape tagged `KLA` / `WallGradeCheck`). In
  the active 3D view it is 50% transparent and halftone. It shows in other
  views too until Clear removes it.

### Wall geometry

- The exterior side is `Wall.Orientation`. Each station's exterior normal is
  the curve's horizontal perpendicular turned to match it, so arc walls work.
- The exterior face is found from the location line (`WALL_KEY_REF_PARAM`)
  and the wall width. Core faces are treated as finish faces, which is exact
  for single-layer foundation walls.
- Top of wall at each station is a ray cast straight down onto the wall's own
  faces, 1" inside the exterior face, so stepped and attached tops are found.
  If the wall is not visible in the ray-casting view, the top of its bounding
  box is used and the report says so.

### Grade from Revit topography

- Toposolids (Revit 2024+) and Topography surfaces, in the host model and in
  loaded Revit links (`FindReferencesInRevitLinks`).
- Grade is a ray cast straight down onto those categories at a point 3"
  outside the exterior face. The highest hit wins.
- Rays are cast in a non-template 3D view: the active view if it is one,
  else `{3D}` or the user's `{3D - name}`, else any 3D view. Elements hidden
  in that view are not found. Run from the 3D view to be reviewed: the review
  display unhides the topography categories there first; in another ray view,
  check that topography is visible.

### Grade from a PDF grading plan

- Uses a PDF Overlay already imported and aligned in a plan view on this
  computer (its local cache state file is needed). The overlay pose maps the
  PDF's text into the plan view, and the view's right/up directions map that
  to model X/Y, so the check runs from any view, including 3D.
- Words are read with `lib/pdf_overlay/pdftext.py`. A grade label is a number
  with up to two decimals, alone or with a prefix or suffix (in the same word,
  joined by `=` or `:`, or as the neighboring word on its baseline):
  - Grade prefixes: `FG`, `FS`, `BW`, `BOW`, `TOS`, `HP`, `LP`, `GR`, `ME`,
    `BC`.
  - Skipped prefixes (not grade, or existing grade): `TW`, `TOW`, `TC`,
    `TOC`, `FF`, `FFE`, `FFL`, `TF`, `TOF`, `BF`, `BOF`, `INV`, `IE`, `RIM`,
    `EX`, `EG`, `EXG`, `EXIST`; any other prefix is skipped too.
  - Plain numbers: with decimals they are spot elevations, whole numbers are
    contour labels. Parenthesized numbers (existing grade on most sheets) are
    skipped.
  - Only numbers between 30 ft below the lowest top of wall and 10 ft above
    the highest (converted to USGS) are kept, which drops sheet numbers,
    dimensions, and note numbers.
- Labels within 10 ft outside the exterior face (and up to 6" inside it) and
  no more than 10 ft beyond either wall end are projected onto the wall.
  Labels within 6" of each other along the wall keep only the nearer one.
- Grade is linear between neighboring labels up to 25 ft apart. Before the
  first label, after the last, and inside wider gaps, the nearer label's
  value is held for 5 ft; beyond that the station has no grade, nothing is
  drawn there, and the report lists the range.

#### USGS vertical placement

- Grading-plan elevations are USGS. The user ties them to the model with one
  known pair: a level and its USGS elevation (the "100'-0" = USGS ..." note
  on the structural drawings). A PDF elevation then converts to Revit as
  `level internal Z + (PDF value - level USGS)`, using `Level.ProjectElevation`.
- Levels are listed by name with their displayed elevation; with one level
  it is used without asking.
- The elevation accepts decimal feet (`5432.50`) or feet and inches
  (`5432'-6 1/2"`); anything else is asked again.
- The last level and value are remembered per model (by document title) in
  the pyRevit user config. With no saved value, a Survey Point that is set up
  (shared elevation differs from internal by more than 1 ft) supplies the
  starting value; otherwise the box starts empty.
- The report states the tie used, for example `Level 1 = USGS 5432.50`.

### Flags

- Clearance = top of wall - grade at a station. A station is flagged
  **Clearance** when 0 < clearance < the set value (exactly the set value
  passes), and **Over top** when clearance <= 0.
- Each drawn segment takes the worse status of its two ends; a flagged run
  is consecutive flagged stations and is Over top if any station is.

## Inputs and prerequisites

- Basic walls with a line or arc location curve; selected, or Foundation or
  Retaining walls in the active view.
- A non-template 3D view in the model where the walls and topography are
  visible.
- Revit source: Toposolid or Topography elements in the model or a loaded
  link.
- PDF source: a grading plan imported and aligned with PDF Overlay in a plan
  view on this computer, with the PDF still at its imported path and its
  labels as real PDF text.

## Outputs and effects

- Line styles `KLA Grade Review` (blue, weight 2), `KLA Grade Review -
  Clearance` (orange, weight 6), and `KLA Grade Review - Over Top` (red,
  weight 8) are created under Lines when missing.
- Model lines are drawn 1" outside the exterior face at grade elevation, one
  per sample interval, on vertical sketch planes (one per straight wall, one
  per segment on arc walls).
- One text note per flagged run, at its worst station 6" above grade, such as
  `GRADE 5" BELOW T/WALL` or `GRADE 3" ABOVE T/WALL`, in text type `KLA
  Grade Review` (duplicated from the default text type, red). Notes are added
  only in plan, ceiling, area, structural plan, section, elevation, and
  detail views, and locked 3D views; elsewhere the report says why.
- The active 3D view is put in Temporary View Properties with ghosted
  topography, and PDF grade strips are added, as described under Review
  display.
- Flagged walls are selected. Draw (a transaction group) and Clear are each
  one undo step. Cancelling any prompt changes nothing; a failure while
  drawing rolls the whole group back.
- Sketch planes made for the lines stay in the model after Clear.
- Unexpected failures write an error report (`WGC` code) and a log at
  `%LOCALAPPDATA%\KLA Tools\Wall Grade Check\wall_grade_check.log`.

## Limits and compatibility

- Stacked walls, curtain walls, in-place walls, and walls with other curve
  types are skipped and listed.
- A flipped wall gives grade on the wrong side; the exterior is always
  `Wall.Orientation`.
- PDF grade is only as dense as the labels near the wall; between distant
  labels the line is a straight estimate. Contour linework is not read.
- Label prefixes and the existing-grade convention are confirmed against
  common practice only, not yet against KL&A project grading plans.
- `bundle.yaml` allows Revit 2023 and later (Toposolids need 2024). Revit
  2024 and later is the repository's design target; no Revit version has
  live evidence yet, so none is claimed as supported.

## Validation evidence

| Date | Extension release | Revit version | Scenario | Result | Evidence link or location |
| --- | --- | --- | --- | --- | --- |
| 11.12.2026 | `0.0.14-dev` | None (CPython) | `tests/wall_grade_test.py` (26 tests) | Pass | Local run on `dev.grade-check` |

`tests/wall_grade_test.py` covers stations, exterior offsets, clearance
input, status classification (including the exact-clearance boundary),
segments, flagged runs, no-data ranges, note text, PDF label parsing and
prefix rules from a generated PDF, the elevation range filter, USGS
elevation input parsing and conversion, projection onto straight and bent wall paths, and interpolation
with hold and sparse-gap rules, the review-view record (first original and first mode kept, category keys, save and load, per-model take), and PDF grade strip quads.

Automated checks do not prove Revit ray casting, drawing, notes, or the user
workflow; live acceptance is pending.

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | Unreleased | 11.12.2026 | First DevSandbox grade-along-wall review from Revit topography or a PDF grading plan (USGS tie), with clearance and over-top flags, a temporary review display (Temporary View Properties, ghosted topography) in the active 3D view, and a Clear action that ends it. | Pending commit on `dev.grade-check`; pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Backlog

- Live Revit acceptance (2024–2026) with a sloped toposolid, a linked civil
  toposolid, an arc wall, and a grading-plan PDF.
- Confirm label prefixes and existing-grade style with KL&A grading plans.
- Trace contour linework from the PDF for a denser profile.
- Show grade on both faces (retaining walls with fill on either side), and a
  per-wall flip of the exterior side.
- Remove the sketch planes on Clear.
