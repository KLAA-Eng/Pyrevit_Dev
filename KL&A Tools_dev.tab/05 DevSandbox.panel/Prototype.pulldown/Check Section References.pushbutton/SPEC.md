# Check Section References

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.check-section-references` |
| Tool version | `v0.0` |
| Status | Unreleased prototype; live acceptance pending |
| Status/origin | Prototype; KL&A custom tool. Reuses the Check Hanger Locations Revit helpers for element labels, Ids, and the Zoom to Selection button. |
| Main delivery | Unreleased |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Check Section References.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Check Section References.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Check Section References.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Check Section References.pushbutton/script.py`; `lib/section_check/`; shared `lib/hanger_check/revit_check.py` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | Unreleased | 10.28.2026 | First DevSandbox section reference check: approximate match percentage per reference section against a live referenced section or a drafting view, with SIM and OH notes. | Pending commit on `dev.hangers`; pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Purpose

Plans often place a section marker that references a detail drawn somewhere
else (a section cut at another location, or a typical drafting detail). This
command reviews every such marker in the active plan view and gives an
approximate percentage of how well the modeled condition at the marker
matches the referenced detail, so reviewers can look at the lowest matches
first. It does not check sections that show their own location.

## Scope and detection

- Markers: the active plan view's reference sections
  (`View.GetReferenceSections`), each with its referenced view from
  `ReferenceableViewUtils.GetReferencedViewId`. Other section, callout, and
  elevation markers are counted and skipped. The command stops in non-plan
  views and when the view has no reference sections.
- Cut line: the marker's longest drawn line plus the lines collinear with it,
  read from the marker's geometry in the view. The look direction is the side
  of the line its head and tail symbols are drawn on; when they balance, the
  hand is unknown. Without drawn lines the long axis of the marker's box in the
  view is used and the hand is unknown.
- SIM / OH: text notes in the plan whose box is within 3/4" (paper, at the
  view scale) of a marker's cut line. `SIM`, `SIMILAR` mark similar; `OH`,
  `O.H.`, `OPP`, `OPP HAND`, `OPPOSITE HAND` mark opposite hand. Each note
  belongs to its nearest marker only. Words that merely contain the letters
  (`SIMPSON`, `OHIO`) do not count.
- Cut window: a vertical rectangle on the cut plane, 1'-0" deep to each side,
  intersected by solid with walls, floors, structural framing, structural and
  architectural columns, structural foundations, and roofs in the host model.
  - Live referenced section (a vertical section or detail view): its crop box
    width and height, anchored to the level nearest the crop's middle. The
    marker's window uses the same width, centered on the marker, and the same
    height above and below the plan's level, so both frame the same part of
    the condition. A section referenced by several markers is cut once.
  - Referenced drafting view: the marker length clamped to 4'-0"..12'-0",
    4'-0" below to 4'-0" above the plan's level.
- Each cut element becomes a condition: group (Wall, Floor, Framing, Column,
  Foundation, Roof), `Family: Type` label, sizes (`W16X31`, `HSS6X6X1/4`,
  `2X10`, `8IN`, `11-7/8IN`) and materials (CMU, CONC, LVL, GLB, PSL, LSL,
  TJI, CLT, STUD, STEEL, WOOD, BRICK, DECK) read from the label, orientation
  to the cut (`along` within 30 deg of the cut line, `cut` within 30 deg of
  the view direction, else `skew`; columns `vertical`), and side (`L`, `C`
  within 1'-0" of the window center, `R`) from its location line or point.

## Scoring

The percentage is a review guide, not a pass/fail.

- Live referenced section: each element at the marker pairs with the best
  unpaired element in the reference cut. A pair needs the same group and
  scores 1.0 for the same type, 0.75 for a shared size or material, 0.5 for
  the group alone; a different orientation multiplies by 0.6 and a different
  side by 0.8. SIM raises size/type differences to 0.9. OH mirrors the
  reference's sides first. Match = 2 x paired score / (elements at marker +
  elements in reference), so missing and extra elements both lower it.
  - Hand: when the mirrored comparison beats the drawn one by 10 points or
    more, the finding says `OH may be missing` (no OH note) or `OH note may be
    wrong`. When the marker's look direction is unknown the better hand is used
    and the finding says the hand was not checked.
  - Without SIM, paired elements with different types are listed with a
    suggestion to add SIM or check the reference.
- Referenced drafting view: the detail's detail component and filled region
  type names and its text notes are read for groups (keywords such as WALL,
  CMU, SLAB, DECK, BEAM, JOIST, COLUMN, FOOTING), sizes, and materials. Each
  element at the marker earns 1.0 when the detail names its size, 0.8 for its
  material, 0.6 for its group (SIM: 1.0 material, 0.8 group). Groups the
  detail names that are not modeled at the marker count as missing. Match =
  credits / (elements at marker + missing groups). Hand is not checked; an OH
  note is reported as not checked. A detail naming nothing recognizable gives
  `Can't tell`.
- Rating: `Likely match` at 80% or more, `Review` from 50%, `Likely mismatch`
  below 50%, `Can't tell` when nothing could be compared.

## Output and model effects

Read only: no transaction, no model or view changes. The pyRevit output shows
the view, number of reference sections, average match, and how many need
review (under 80% or unknown), with a link that selects them. The table lists
unknown and lowest matches first: Marker (select link), References (view name
and detail/sheet), Compared with (Section, Drafting, Not compared), SIM/OH,
Match, Rating, Cut at marker, Cut in reference (live sections), and Findings.
The `Zoom to selection` button runs the sibling `Zoom to Selection` command,
found from the loaded ribbon as in Check Hanger Locations.

## Implementation inventory

- Entry point: `script.py` (view checks and report).
- `lib/section_check/revit_sections.py`: Revit collection, marker geometry,
  windows, cut solids, drafting content.
- `lib/section_check/markers.py`: host-independent cut line, look direction,
  SIM/OH parsing, and note-to-marker assignment.
- `lib/section_check/conditions.py`: host-independent label parsing,
  orientation, side, and drafting content keywords.
- `lib/section_check/score.py`: host-independent pairing, percentages, and
  findings.
- Host-independent modules are covered by `tests/section_check_test.py`.

## Limits

- Linked models are not read, so conditions modeled in a linked architectural
  or structural model score as missing.
- Only reference sections in plan views; reference callouts and elevations,
  and markers in section or elevation views, are not checked.
- Drafting comparisons depend on consistent detail component names and note
  wording.
- A typical detail placed at many locations will legitimately score lower at
  some of them; the score only orders the review.

## Validation boundary

Live Revit 2024+ acceptance must confirm that `GetReferenceSections` returns
the plan's reference markers, that the marker geometry in the view gives the
cut line and that the head/tail symbols sit on the look side (or report the
hand as unknown), `Level.ProjectElevation` alignment with model coordinates
on projects whose base point is moved, the crop-box window on rotated and
detail-type sections, the SIM/OH note reach at common scales, and scores on
representative wall-bearing, beam-to-wall, and footing details.

## Future development

- Reference callouts, and markers in section and elevation views.
- Linked model elements.
- Optional color overrides of low-scoring markers in the view.
