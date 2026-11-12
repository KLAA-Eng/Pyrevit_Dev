# Wall Grade Check

Status: implementation built, live Revit acceptance pending (11.12.2026).
Branch `dev.grade-check`, stacked on `dev.pdf-overlay`.

## Goal

Engineers reviewing foundation walls need to see where finished grade sits
against each wall, and where soil comes too close to the top of the wall.
A DevSandbox command draws the grade line along the outside face of the
foundation walls as removable review linework, and flags runs where grade is
within the clearance (default 8") of the top of wall or at/above it. Grade
comes from either Revit topography or a PDF grading plan.

The behavior contract is the command's
[SPEC.md](../../KL&A%20Tools_dev.tab/05%20DevSandbox.panel/Prototype.pulldown/Wall%20Grade%20Check.pushbutton/SPEC.md).

## Settled decisions (11.12.2026)

| Decision | Choice |
| --- | --- |
| Review graphics | Real model lines on each wall's outside face in dedicated line styles, plus a Clear action that deletes them. They print, show in 3D, sections, and elevations, and Undo works. Not a display-only (DirectContext3D) overlay. |
| Grade sources | Both Revit topography (Toposolids and legacy Topography, host and links) and a PDF grading plan. |
| PDF grade source | Spot elevation and contour label **text** read from a PDF Overlay that is aligned in a plan view. Contour linework tracing is out of scope (backlog). |
| Flags | Two levels: grade within the clearance of top of wall, and grade at or above top of wall. Clearance is user-editable, default 8" (IBC 2304.12.1.2); 6" for IRC work. Exactly the clearance passes. |
| Walls checked | Selected walls; with nothing selected, all walls in the active view whose type Function is Foundation or Retaining. |
| Prompts | pyRevit prompts in sequence (action, clearance, then PDF overlay and datum) instead of a custom dialog; the PDF search band is fixed at 10 ft. |
| Ray-casting view | An existing non-template 3D view; the command does not create one. |
| Branch | `dev.grade-check` from `dev.pdf-overlay`, because the PDF source reuses `lib/pdf_overlay`. Its PR into `master-dev` follows the PDF Overlay PR. |

## Task ledger

| ID | Task | Acceptance | Status |
| --- | --- | --- | --- |
| T1 | Bundle scaffold: `bundle.yaml`, `script.py`, adjacent `SPEC.md`, pulldown layout entry | Metadata check passes for the bundle | Implementation complete, locally verified (`scripts/check_tool_metadata.py`) |
| T2 | `lib/wall_grade/profile.py`: stations, exterior offset, clearance input, classification, segments, flagged runs, no-data ranges, note text | `tests/wall_grade_test.py` | Implementation complete, locally verified (19 tests pass) |
| T3 | `lib/wall_grade/pdf_grade.py`: label parsing and prefix rules, elevation range, projection onto wall paths, interpolation with hold and sparse gaps, datum conversion | `tests/wall_grade_test.py` | Implementation complete, locally verified |
| T4 | Revit adapter: wall collection, exterior face sampling, top-of-wall and toposolid ray casting (host and links) | Live: grade matches a sloped toposolid within 1/2" | Implementation complete; live acceptance pending |
| T5 | Drawing and Clear: line styles, model lines, text notes, report, flagged-wall selection, error report | Live: draw, Undo, and Clear in a locked 3D view and a section | Implementation complete; live acceptance pending |
| T6 | PDF source wired to an aligned PDF Overlay | Live: grading-plan check matches hand-read spots within 1" | Implementation complete; live acceptance pending |
| T7 | Validation evidence and review record in SPEC; PR to `master-dev` after PDF Overlay merges | Evidence table filled with live results | Pending |

## Open questions for the owner

- Sample grading-plan PDFs to confirm the label formats (prefixes, contour
  label style, how existing grade is shown).
- Which datum the civil PDFs use on KL&A projects (Survey Point offered
  first).
