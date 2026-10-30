# Section Detailer

Status: in progress. Branch: `dev.section-detailer` (from `master-dev`).
Owning command: `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Section Detailer.pushbutton`;
its `SPEC.md` owns current behavior.

## Goal

From a live section view, overlay 2D detail components on the modeled
elements so the section reads as a finished detail with little manual drafting.
The model stays the source of truth for location; the tool chooses, loads,
places, orients, and finishes the 2D content.

## Requested capabilities

| ID | Capability | Notes |
| --- | --- | --- |
| C1 | Find elements visible and cut in the active section | Visible-in-view collector, then classify cut vs. beyond by intersecting each solid with the view's cut plane. |
| C2 | Match each element to a detail component type | Steel by section shape (`FamilySymbol.GetStructuralSection()` / type name such as `W12X26`), concrete/CMU/wood by category and thickness. Multiple matches prompt the user once per distinct element type. |
| C3 | Load missing detail families | When nothing matches, the user browses to an `.rfa` (or a configured KL&A library folder) and the tool calls `Document.LoadFamily`. |
| C4 | Place and orient | Cut members: point-based instance at the cut centroid, rotated to the member's local axes and flipped to match. Members running in the view plane: line-based component along the projected axis. |
| C5 | Break lines | Where a member crosses the crop boundary, place a break-line component at the crop edge, perpendicular to the member and sized to its depth; line-based components stop at the crop edge. |
| C6 | Grid component | For each grid visible in the view, place the grid detail component where the grid crosses the view plane and copy the grid label. |
| C7 | Architectural outline | Draw detail lines around the visible extents of architectural content using a user-selected line style. |
| C8 | Reference detail | User picks an existing detail/drafting view; component types used there are ranked first during matching (C2). |

## Revit API approach

- Cut geometry: `Element.get_Geometry(Options(View=view))`, then
  `BooleanOperationsUtils.CutWithHalfSpace` with the view's cut plane; the
  face coplanar with the plane gives the cut profile (centroid, extents,
  orientation for C4; loops for C7).
- Crop: `view.GetCropRegionShapeManager().GetCropShape()` in view coordinates.
- Placement: `doc.Create.NewFamilyInstance(XYZ, symbol, view)` and the
  `(Line, symbol, view)` overload; rotate with `ElementTransformUtils.RotateElement`
  about the view direction.
- Outline: `doc.Create.NewDetailCurve(view, curve)` with `LineStyle` set to the
  chosen `GraphicsStyle`.
- Linked models: elements in `RevitLinkInstance` documents need the link
  transform applied and are collected separately from host elements.
- Re-run safety: tag created elements (Comments or extensible storage) so a
  second run can update or clear its own overlay without touching hand-drafted
  content. One transaction group per run so cancel leaves no partial work.

## Host-independent logic for `lib/` (unit-testable)

- Section-name normalization and candidate ranking (`W12x26` / `W12X26` /
  `W 12x26`, reference-detail boost, exact vs. family-only match).
- 2D view-plane geometry: crop-edge crossings, break-line position/rotation,
  clipping line-based components, outline hull/offset.
- Grid label and position mapping.

## Proposed phases

| Phase | Scope | Exit |
| --- | --- | --- |
| P1 | C1, C2, C4 for steel and wood members cut, beyond, and along the section; built-up wood as single plies; library loading; prompt on ambiguity; report unmatched | Live test in representative steel and wood sections |
| P2 | Browse for families outside the library, C5 break lines, C6 grids | Live test with cropped views and visible grids |
| P3 | Concrete/CMU, C8 reference detail | Live test on a mixed-material detail |
| P4 | C7 architectural outline, re-run update/clear | Live test with linked architectural model |

## KL&A detail component library

Decided 2026-10-30 from the library on the office share.

- Root: `J:\Standards\910 Revit Support\KLAA Library\KLAA Detail Components`,
  with `Div NN - <Division>` subfolders (03 Concrete, 04 Masonry, 05 Metals,
  06 Wood and Plastic, ...) and shared annotation families at the root.
- File names: `<Div>_<Shape>_<View>_KLAA_<NN>DC.rfa`, where `<View>` is
  `Section` (cut), `Side` (member in the view plane), `Top` (plan), or
  `Elevation`; `<NN>` is a revision year and is sometimes absent (`_KLAA_DC`).
- Steel families carry type catalogs (`.txt` beside the `.rfa`). Type names are
  AISC designations with lowercase `x`: `W44x335`, `HSS20x12x5/8`,
  `HSS20x0.500`, `L8x8x1-1/8`, `C15x50`, `WT22x167.5`, `HP14x117`,
  `Pipe1/2STD`. Missing types load from the catalog with
  `Document.LoadFamilySymbol(path, typeName)` instead of the whole family.
- Shape to family (cut view): W → `5_WideFlange_Section`, HSS rect →
  `5_HSS_Section`, HSS round → `5_HSS_Round_Section`, L → `5_Angle_Section`,
  C/MC → `5_Channel_Section`, WT → `5_WT_Section`, HP → `5_HP_Section`,
  Pipe → `5_Pipe_Section`. In-plane members use the matching `_Side` family.
- Wood families (`Div 06 - Wood and Plastic`) use single-ply catalog sizes
  (`2x10`, `1 3/4x11 7/8`, `5 1/8x12`, heavy timber `6x10 WBx`); prefixed
  variants such as `PT 2x10` and `Rafter 2x10` share a size. Built-up members
  are drawn as one single-ply component per ply (decided 2026-10-30).
- Side catalogs for rectangular HSS are named by seen face and wall
  (`HSS6x1/4`), not the full designation.
- Break line: `00_Break_Line_Pick_KLAA_15DC` (also `00_Dbl_Break_Line_Pick`,
  `00_Break_Pipe_Pick` for round members). Grid: `00_Grid_KLAA_20DC`.
  Parameter names for break width and grid label still need confirming in
  Revit.

## Open decisions

- Whether "architectural outline" means linked architectural model content,
  host architectural categories, or an outline of the whole cut assembly.
- Whether the overlay stays in the live section or is also pushed to a drafting
  view for reuse.
- Whether model elements should be hidden/halftoned after the overlay.

## Task ledger

| ID | Task | Status | Evidence |
| --- | --- | --- | --- |
| SD-1 | Resolve open decisions | Library conventions decided; others open | This plan, KL&A detail component library section |
| SD-2 | Scaffold DevSandbox command, `SPEC.md`, `lib/` module with tests | Implementation complete | `lib/section_detailer/`, `tests/section_detailer_test.py` |
| SD-3 | Deliver P1 (steel and wood; cut, beyond, and along) | Implementation complete; live Revit acceptance pending | Command `SPEC.md` validation evidence |
| SD-4 | Deliver P2 | Not started | |
| SD-5 | Deliver P3 | Not started | |
| SD-6 | Deliver P4 | Not started | |
