# Wall Grade Check

Status: draft for owner review (11.12.2026). Branch `dev.grade-check`, stacked
on `dev.pdf-overlay`.

## Goal

Engineers reviewing foundation walls need to see where finished grade sits
against each wall, and where soil comes too close to the top of the wall.
A new DevSandbox command draws the grade line along the outside face of the
foundation walls as removable review linework, and flags runs where grade is
within the clearance (default 8") of the top of wall or at/above it. Grade
comes from either Revit topography or a PDF grading plan.

The behavior below is the draft command spec. When T1 creates the bundle,
it moves to the command's adjacent `SPEC.md`, and this plan keeps only the
links, decisions, and task ledger.

## Settled decisions (11.12.2026)

| Decision | Choice |
| --- | --- |
| Review graphics | Real model lines on each wall's outside face in dedicated line styles, plus a Clear action that deletes them. They print, show in 3D, sections, and elevations, and Undo works. Not a display-only (DirectContext3D) overlay. |
| PDF grade source | Spot elevation and contour label **text** read from a PDF Overlay that is aligned in a plan view. Contour linework tracing is out of scope (backlog). |
| Flags | Two levels: grade within the clearance of top of wall, and grade at or above top of wall. Clearance is user-editable, default 8" (IBC 2304.12.1.2); 6" for IRC work. |
| Walls checked | Selected walls; with nothing selected, all walls in the active view whose type Function is Foundation or Retaining. |
| Branch | `dev.grade-check` from `dev.pdf-overlay`, because the PDF source reuses `lib/pdf_overlay`. Its PR into `master-dev` follows the PDF Overlay PR. |

## Draft command spec

### Identity (planned)

| Field | Value |
| --- | --- |
| Bundle path | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Wall Grade Check.pushbutton` |
| Tool ID | `devsandbox.wall-grade-check` |
| Path aliases | Same path under `KL&A Tools.tab/` in releases |
| Version inputs | `bundle.yaml`; `script.py`; `lib/wall_grade/`; shared `lib/pdf_overlay/` (PDF source) and `lib/error_reports*.py` |
| Maturity / version | Prototype, `v0.0`, Unreleased |

### Workflow

1. Select foundation walls (or select nothing to use the Foundation and
   Retaining walls in the active view). Run the command from any view; a
   3D view shows the result best.
2. A small dialog asks for:
   - **Grade source:** Revit topography, or a PDF Overlay (listed by PDF,
     page, and the view it is aligned in).
   - **Clearance** in inches (default 8).
   - **PDF only:** the elevation datum the PDF numbers use (Survey Point,
     default, or Project Base Point), and the search band (default 10 ft
     from the wall's outside face).
   - **Draw** or **Clear review lines**.
3. The tool samples each wall along its length (every 1 ft plus both ends)
   just outside its exterior face, finds grade and top of wall at each
   station, and draws the result in one transaction.
4. The pyRevit output window lists each wall (clickable id) with minimum
   clearance, flagged runs with station range and worst value, and stations
   with no grade data. Flagged walls are selected.
5. **Clear review lines** deletes every element in the review line styles
   and review text type, in all views, in one transaction.

### Grade from Revit topography

- Toposolids (Revit 2024+) and legacy Topography surfaces, in the host model
  and in loaded Revit links.
- Grade at a station is found with `ReferenceIntersector` casting a ray
  straight down from above the wall, filtered to the Toposolid and
  Topography categories, in a non-template 3D view (the active 3D view, else
  the default `{3D}` view, which is created if missing).
- The station point is 3" outside the wall's exterior face so the ray misses
  the wall itself.

### Grade from a PDF grading plan

- Uses an overlay already imported and aligned with PDF Overlay in a plan
  view. Its saved pose maps PDF text to model XY, so the check runs from any
  view, including 3D, even though overlay images only display in 2D views.
- Elevation labels are read with `lib/pdf_overlay/pdftext.py`: spot
  elevations with common prefixes (`FG`, `TOS`, `BW`, `TW`, `FFE`, `EX`,
  `HP`, `LP`, `TOC`) or plain decimals like `94.25`, and integer contour
  labels. `TW`, `TOC`, and `FFE` are not grade and are skipped. The exact
  prefix list is confirmed with the owner's sample grading plans.
- Labels within the search band on the wall's exterior side are projected
  onto the wall line. Grade at each station is linearly interpolated along
  the wall between neighboring labels; past the last label the nearest value
  is held for up to 5 ft, then the station is reported as no data.
- PDF elevations are converted from the chosen datum to Revit internal
  elevation.

### Top of wall and exterior side

- Top of wall at each station comes from the wall's own geometry (top face
  of its solid), so attached or sloped tops and stepped walls are handled.
- Exterior side is `Wall.Orientation`. Walls modeled flipped give a wrong
  side; the report lists the side used, and **Flip** in the backlog covers
  this if it occurs in practice.

### Graphics

- Grade is drawn as model lines, one per sample interval, each on a vertical
  sketch plane through that interval, 1" outside the exterior face.
- Line styles (created when missing, subcategories of Lines):
  - `KLA Grade Review` — grade OK, thin blue.
  - `KLA Grade Review - Clearance` — clearance below the set value, heavier
    orange.
  - `KLA Grade Review - Over Top` — grade at or above top of wall, heavy red.
- Flags: each flagged run gets one text note at its worst station, such as
  `GRADE 5" BELOW T/WALL` or `GRADE 3" ABOVE T/WALL`, in text type
  `KLA Grade Review`. Text notes need a 2D view or a locked 3D view; in an
  unlocked 3D view the runs are still colored and listed, and the report says
  to lock the view for notes.
- A run is flagged when clearance is **less than** the set value; exactly 8"
  passes.

### Limits

- Straight and arc walls; arcs are drawn as chords at the sample interval.
- Stacked walls, curtain walls, and in-place walls are skipped and listed.
- PDF grade depends on label density; between two far-apart labels the
  interpolated line is an estimate, and gaps longer than 25 ft between labels
  are left undrawn and listed as sparse.
- Revit 2024 and later is the design target. No live evidence yet.

## Task ledger

| ID | Task | Acceptance | Status |
| --- | --- | --- | --- |
| T1 | Bundle scaffold: `bundle.yaml`, `script.py` adapter, adjacent `SPEC.md` (moved from this plan), icon | Button shows in Prototype pulldown with versioned tooltip; SPEC has identity and version history | Pending |
| T2 | `lib/wall_grade/` host-independent core: stations along a wall line or arc, exterior offset, clearance classification into OK / Clearance / Over Top runs, worst-station pick, note text | CPython unit tests in `tests/wall_grade_test.py` pass | Pending |
| T3 | PDF elevation labels: parse spot/contour labels, band filter, projection to wall station, interpolation, hold and sparse rules, datum conversion | Unit tests with synthetic `PageText` words pass | Pending |
| T4 | Revit adapter: wall collection, top-of-wall sampling, toposolid ray casting (host and links) | Live: correct grade on a sample model with a sloped toposolid | Pending |
| T5 | Revit drawing and Clear: line styles, model lines, text notes, report with clickable ids, error report on failure | Live: draw, Undo, Clear in a 3D view and a section | Pending |
| T6 | PDF source wired to an aligned PDF Overlay | Live: grading-plan PDF check matches hand-read spots within 1" | Pending |
| T7 | Validation evidence and review record in SPEC; PR to `master-dev` after PDF Overlay merges | Evidence table filled | Pending |

## Open questions for the owner

- Sample grading-plan PDFs to confirm the label formats (prefixes, contour
  label style).
- Which datum the civil PDFs use on KL&A projects (Survey Point assumed).
- Whether runs at exactly the clearance should pass (assumed yes).

## Backlog

- Trace contour linework from the PDF for a denser profile.
- Show grade on both faces (retaining walls with fill on either side).
- Flip exterior side per wall.
- Optional toposolid source from a linked civil model's DWG/IFC.
