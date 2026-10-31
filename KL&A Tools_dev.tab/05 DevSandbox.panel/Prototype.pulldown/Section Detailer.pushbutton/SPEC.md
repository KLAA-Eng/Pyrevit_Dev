# Section Detailer

## Identity

| Field | Value |
| --- | --- |
| Bundle path | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Section Detailer.pushbutton` |
| Tool ID | `devsandbox.section-detailer` |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Section Detailer.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Section Detailer.pushbutton` |
| Version inputs | `bundle.yaml`; `script.py`; `lib/section_detailer/` |
| Maturity | Prototype |
| Tool version | `v0.0` |
| Status/origin | KL&A DevSandbox prototype; KL&A custom tool. |
| Maintainer | KL&A |
| Revit versions live-tested | None yet |

Plan and task authority: [docs/plans/section-detailer.md](../../../../docs/plans/section-detailer.md).

## Purpose and workflow

Drafting a structural detail over a live section means placing a 2D detail
component on every member by hand. This command does that for steel and wood
framing and columns: members seen end-on (cut by the section or beyond it) get
the matching KL&A `Section` component, and members running along the section
get the matching `Side` component. Wood is matched by its modeled depth and
width, and LVL and dimension lumber are stacked from single plies. Wood
walls get a 2x double top plate and single bottom plate. Floor and roof
sheathing gets a sheathing component, members and floors running out of the
crop get `Break Line small` break lines, visible floor and steel tops get
elevation symbols, and a visible linked architectural model is outlined with
a halftoned `S-OBJ4` line. Only host-model elements get components; nothing
is placed over the linked model.

1. Open a section view and run the command.
2. If this tool placed components in the view before, choose **Replace** or
   **Add**.
3. If a needed type is not in the project, approve loading it from the KLAA
   library.
4. If more than one loaded family has a steel type (for example an office
   family and the KLAA family), pick one; the choice applies to every member
   of that type in this run.
5. If several linked models show in the view, pick the ones to outline. If
   the project has no `S-OBJ4` line style, pick another or cancel to skip
   the outline.
6. Review the placed components and the report of members that were not
   placed.

## Inputs and prerequisites

- Active view: a section (`ViewSection`), not a template. Revit 2023 or later.
- Members: structural framing and columns visible in the view (including
  beyond the cut, within the far clip) whose type name is either
  - an AISC designation (`W12X26`, `HSS6X6X1/4`, `HSS6.000X0.250`, `L4X4X1/2`,
    `C10X15.3`, `MC12X10.6`, `WT9X17.5`, `HP12X53`, `PIPE4STD`), or
  - a wood member: structural material Wood, or a type or family name with a
    wood size (`2x10`) or a word such as `LVL`, `Lumber`, or `Timber`.
    Material comes from `LVL`, `PSL`, `LSL`, or `Glulam`/`GLB` in the type
    or family name; otherwise sawn lumber. The size is read from the
    modeled geometry, not the name.
- Floors visible in the view and cut by the section. A layer whose material
  says plywood, OSB, sheathing, or subfloor (or a one-layer floor whose type
  says so) is the sheathing. Roofs cut by the section are read the same way.
- Structural foundations and concrete walls cut by the section, a
  `Concrete` filled region type, and grids crossing the section plane (the
  grid component needs a crop region).
- Wood walls cut square by the section: basic walls with a layer whose
  material says stud, wood, or lumber (not sheathing), or whose type name
  says so (then the thickest structure layer, or a one-layer wall's width).
- Optional: a loaded Revit link visible in the view, for the outline.
- KLAA library at
  `J:\Standards\910 Revit Support\KLAA Library\KLAA Detail Components`
  (`Div 05 - Metals`, `Div 06 - Wood and Plastic`, and
  `00_Break_Line_Pick_KLAA_15DC` at the root) with type catalogs beside each
  family, `6_Sheathing_Ply_Section` in `Div 06`, plus
  `KLAA Annotations\Symbols\Elevation_KLAA_17SY.rfa`. Without
  the library, only families already loaded in the project can be placed.

## Outputs and effects

- **Cut and beyond (end-on) members:** a `Section` component at the center of
  the cut face (cut) or of the projected profile (beyond), rotated so the
  family's up direction follows the member's depth. Wood gets one component
  per ply, side by side across the member width (see Matching rules).
- **Oblique members cut by the section** (skewed in plan, for example): a
  `Section` component at the center of the cut face, chosen and spaced by
  the member's own size measured square to its axis, not by the stretched
  cut face. Wood sizes for end-on members are measured the same way.
- **Members along the section:** a `Side` component (for wood,
  `6_Lumber_LVL_Side`, `6_Lumber_Dimension_Side`, and so on, by visible
  depth) along the member centerline for the length visible in the view,
  trimmed 3 in inside the rectangular crop. Line-based families are placed
  on the line; point-based families are placed at its midpoint, rotated,
  with `Length` set when present.
- **Roof sheathing:** the same sheathing component along each up-facing
  edge of a cut roof's face (sloped or flat), set down square to the roof
  surface by the layers above the sheathing, and trimmed to the crop.
- **Wood wall plates:** each wood wall cut square by the section gets a
  double top plate and a single bottom plate: `6_Lumber_Dimension_Section`
  2x types laid flat (turned 90°) whose depth matches the stud layer
  (`2x4` for 3 1/2 in studs, `2x6` for 5 1/2 in), centered on the stud
  layer and stacked down from the wall's top and up from its bottom. Plates
  outside the crop are left out.
- **Floor sheathing:** a `6_Sheathing_Ply_Section` component along the
  sheathing layer of each cut floor, centered on the layer and trimmed like
  side components. The type whose name has the thickness (`3/4`) is used,
  else the first type; a writable `Thickness`, `Sheathing Thickness`, or
  `Depth` instance parameter is set to the layer thickness.
- **Center alignment:** families do not all insert at their center (HSS, for
  one), so after placing, each component is moved so the center of its
  visible lines lands on the target: fully for section components, and
  across the line only for side and sheathing components. Invisible lines
  are ignored; the bounding box is the fallback when no lines are found.
- **Break lines:** where members along the section or cut floors run out of
  the crop (horizontal ones at the left and right edges, vertical ones at the
  top and bottom), a `Break Line small` instance of
  `00_Break_Line_Pick_KLAA_15DC` is placed 3 in inside the crop edge,
  spanning the members' depth. Touching members (sheathing on joists) share
  one break line. The line is oriented with the outside of the crop on its
  right, the side the family is assumed to mask.
- **Elevation symbols:** each distinct floor top cut by the section, and
  each distinct top of steel cut by or along the section, gets a
  `Right Elevation` `Elevation_KLAA_17SY` symbol with its line at the top.
  With a crop, the symbols line up 1/2 in (paper) past the crop's right
  edge, outside the break lines; without one, each starts 1/2 in past its
  element's right end. Tops outside the crop, or elements that do not
  reach into it, get none. Floor text is `T/SHEATHING` for wood floors,
  `T/SLAB` for concrete, and `T/FLOOR` otherwise, from the floor type and
  layer material names; steel text is `T/STEEL`. The text goes in the
  description above the line (`Text Top`, `text right top`, `text left top`,
  or `Description`), and the elevation below the line (`Text Bottom`,
  `text right bottom`, `text left bottom`, or `Elevation`) is left blank for
  the drafter. No other parameter is used; the report says when no
  description parameter is found.
- **Concrete:** structural foundations and concrete walls (a structure
  layer, or with no structure layer any layer or the type name, says
  concrete) cut by the section get a filled region of their cut face,
  clipped to the crop. The filled region type is the shortest-named one
  containing `Concrete`; with none, the user picks one or skips.
- **Soil:** the lowest cut footing (and any within 1/8 in of it) gets a
  `31_Soil_KLAA_18DC` (`4" SOIL`) component along its bottom, just below
  it, for the footing's width.
- **Grids:** each straight grid that crosses the section plane inside the
  crop gets a `Vertical` `00_Grid_KLAA_20DC` component at that point, from
  the crop's top (point-based) or spanning the crop (line-based), labeled
  with the grid name in the first of `Grid`, `Grid Label`, `Grid Number`,
  `Label`, `Text`, or `Name`.
- **Linked model outline:** model elements of the chosen links that are cut
  by the section inside the crop are merged, and their outer boundary is
  drawn as detail lines in the `S-OBJ4` line style, halftoned in the view
  and clipped to the crop. Edges where two linked elements meet, or inside
  another element, are not drawn. Linked elements get no components.
- Each placed item's Comments is set to `Section Detailer` where the family
  has a Comments parameter.
- **Replace** deletes the earlier `Section Detailer` items in this view
  only. Hand-placed items are never touched.
- Loads individual types (`LoadFamilySymbol`) from the newest revision of the
  matching KLAA family, and the break line, elevation, and sheathing
  families when absent (`LoadFamily`), only after the user approves.
- All loading and placement is one undo step. An error rolls back the whole run.
- The pyRevit output lists the count placed and every member skipped, with the
  reason.

## Matching rules

Steel type names compare without case, spaces, or insignificant decimal
zeros, so Revit's `W12X26` matches the KLAA catalog's `W12x26`. Shape maps to
family stem (`_Section` end-on, `_Side` along): W → `5_WideFlange`,
rectangular HSS → `5_HSS`, round HSS → `5_HSS_Round`, L → `5_Angle`, C and
MC → `5_Channel`, WT → `5_WT`, HP → `5_HP`, Pipe → `5_Pipe`. Rectangular HSS
side types are named by the face seen and the wall (`HSS6x1/4`).

Wood is matched by size, not name. Material maps to family stem: sawn →
`6_Lumber_Dimension`, then `6_HeavyTimber`; LVL → `6_Lumber_LVL`; PSL →
`6_Lumber_PSL`; LSL → `6_Lumber_LSL`; Glulam → `6_GluLaminatedBeam`. Only
these KLAA families are used for wood. Their types, loaded or in the type
catalog (`Width` and `Depth` columns, or type parameters), are compared with
the member's modeled size within 1/16 in:

- End-on: the type's depth must equal the member's depth, and a whole
  number of the type side by side must make up the member's width. LVL
  prefers 1 3/4 in plies and sawn lumber 1 1/2 in plies (a 3 1/2x11 7/8 LVL
  is two `1 3/4x11 7/8`, a 4 1/2x9 1/4 member is three `2x10`); when the ply
  does not divide the width, a solid size is used (`4x8`). PSL, LSL, and
  glulam use the fewest pieces.
- Along: the type's depth must equal the visible depth; one piece is used.
- Ties go to the plainest name (`2x10` over `PT 2x10`), and loaded types
  win over catalog types of the same name.

For steel, when several loaded families match, the user picks a family
(KLAA families listed first); within a family the plainest type name is
used.

## Limits and compatibility

- End-on means the axis is within about 25° of the view direction; along means
  within about 6° of the view plane. Oblique members cut by the section are
  placed (see Outputs); oblique members beyond the cut and curved members
  are reported, not placed. A strongly skewed member keeps the section
  component's rotation from its depth direction only.
- S, M, and other shapes without a KLAA family, and non-steel, non-wood
  members, are reported.
- Along-section components show one ply; plies overlap in that view.
- Wood sizes must match a catalog size: the heavy timber catalog lists
  `6x10 WBx` as 9 1/4 in deep, so a 6x10 modeled at 9 1/2 in is reported.
- Center alignment uses the family's visible lines, so a family whose lines
  are off-center from its drawn shape will land off-center.
- Wall plates sit inside the modeled wall height, at its cut top and bottom,
  and assume the wall's exterior is its `Orientation` side. Walls running
  along the section and curved walls get none.
- Roof sheathing assumes layer thicknesses are measured square to the roof
  and the section is cut square to the ridge; a skewed cut shows a flatter
  slope and the offset is not corrected. Roofs get no break lines or
  elevation symbols.
- Floor sheathing assumes a level floor and the sheathing family's types
  and thickness parameter are unconfirmed.
- The outline uses each link's cut faces on the section plane; linked
  elements beyond the cut are not outlined. Large links are filtered to the
  crop first; with no crop, every linked element is checked.
- Unconfirmed until live testing: which side the break family masks
  (`BREAK_MASKS_RIGHT` in `script.py`), that the elevation symbol inserts on
  its datum line, that `Text Top` is its description and `Text Bottom` its
  elevation (read from the family file, not seen in Revit), the grid
  component's insertion point and label parameter name, where the soil
  family draws relative to its line, rotation for rotated members,
  mirroring of asymmetric shapes (L, C, WT), the column depth axis (taken
  as the instance Y axis), and whether detail lines keep Comments for
  **Replace**.
- Trimming and breaks use the rectangular crop box; a non-rectangular crop
  shape is ignored. Slanted members get no break line.
- Generic annotations may have no Comments parameter; then **Replace** cannot
  find earlier elevation symbols, and they must be deleted by hand.
- The library path is the mapped `J:` drive.
- Allowed from Revit 2023, below the repository's usual 2024+ target, so
  it can be tested where it is used today. It relies on no 2024-only API;
  live acceptance should cover 2023 and 2024.

## Validation evidence

| Date | Extension release | Revit version | Scenario | Result | Evidence link or location |
| --- | --- | --- | --- | --- | --- |
| 10.30.2026 | `0.0.14-dev` | None (CPython) | `tests/section_detailer_test.py` matching and geometry rules | Pass | Local run on `dev.section-detailer` |

Automated checks do not prove Revit transactions, family loading, placement,
or the user workflow; live acceptance is pending.

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| `v0.0` | Unreleased | 10.30.2026 | Prototype: steel and wood section components on members cut by or beyond the active section, side components along it, oblique cut members sized from the member, wood matched by modeled size and stacked as plies, 2x wall plates, floor and roof sheathing, concrete filled regions with soil below the lowest footing, vertical grid components, center alignment, break lines, floor and steel elevation symbols, and a halftoned linked model outline. | `dev.section-detailer` development commits |

## Backlog

- Phase 2: browse for families outside the library.
- Phase 3: CMU, concrete beams and slabs, and a reference detail that ranks
  families first.
- Phase 4: re-run update of an existing overlay.
