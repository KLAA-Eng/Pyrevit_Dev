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
get the matching `Side` component. A built-up wood member gets one
single-ply component per ply.

1. Open a section view and run the command.
2. If this tool placed components in the view before, choose **Replace** or
   **Add**.
3. If a needed type is not in the project, approve loading it from the KLAA
   library.
4. If more than one loaded family has the type (for example an office family
   and the KLAA family), pick one; the choice applies to every member of that
   type in this run.
5. Review the placed components and the report of members that were not
   placed.

## Inputs and prerequisites

- Active view: a section (`ViewSection`), not a template. Revit 2023 or later.
- Members: structural framing and columns visible in the view (including
  beyond the cut, within the far clip) whose type name is either
  - an AISC designation (`W12X26`, `HSS6X6X1/4`, `HSS6.000X0.250`, `L4X4X1/2`,
    `C10X15.3`, `MC12X10.6`, `WT9X17.5`, `HP12X53`, `PIPE4STD`), or
  - a wood size (`2x10`, `1 3/4x11 7/8`, `5 1/8x12`), optionally built up:
    `3-2x10`, `(3) 2x10`, `2x10 (3)`, or `3 PLY ...`. An integer `Plies`,
    `Number of Plies`, or `Ply Count` parameter on the instance or type
    overrides the name. Material comes from `LVL`, `PSL`, `LSL`, or
    `Glulam`/`GLB` in the type or family name; otherwise sawn lumber.
- KLAA library at
  `J:\Standards\910 Revit Support\KLAA Library\KLAA Detail Components`
  (`Div 05 - Metals`, `Div 06 - Wood and Plastic`) with type catalogs beside
  each family. Without the library, only types already loaded in the project
  can be placed.

## Outputs and effects

- **Cut and beyond (end-on) members:** a `Section` component at the center of
  the cut face (cut) or of the projected profile (beyond), rotated so the
  family's up direction follows the member's depth. Built-up wood gets one
  single-ply component per ply, side by side across the member width; ply
  width is the member width divided by the ply count.
- **Members along the section:** a `Side` component along the member
  centerline for its full projected length, trimmed to the rectangular crop.
  Line-based families are placed on the line; point-based families are
  placed at its midpoint, rotated, with `Length` set when present.
- Each placed component's Comments is set to `Section Detailer`.
- **Replace** deletes the earlier `Section Detailer` components in this view
  only. Hand-placed components are never touched.
- Loads individual types (`LoadFamilySymbol`) from the newest revision of the
  matching KLAA family, only after the user approves.
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

Wood compares the numeric single-ply size, so `1-3/4x11-7/8` matches
`1 3/4x11 7/8`, and the plainest catalog name wins (`2x10` over `PT 2x10`).
Material maps to family stem: sawn → `6_Lumber_Dimension`, then
`6_HeavyTimber`; LVL → `6_Lumber_LVL`; PSL → `6_Lumber_PSL`; LSL →
`6_Lumber_LSL`; Glulam → `6_GluLaminatedBeam`. Wood never matches another
material's KLAA family.

When several loaded families match, the user picks a family (KLAA families
listed first); within a family the plainest type name is used.

## Limits and compatibility

- End-on means the axis is within about 25° of the view direction; along means
  within about 6° of the view plane. Oblique and curved members are reported,
  not placed.
- S, M, and other shapes without a KLAA family, and non-steel, non-wood
  members, are reported.
- Along-section components show the single-ply size; plies overlap in that
  view.
- Unconfirmed until live testing: each family's insertion point (the tool
  places at the profile center and the side centerline), which side of the
  line a line-based `Side` family draws on, rotation for rotated members,
  mirroring of asymmetric shapes (L, C, WT), and the column depth axis (taken
  as the instance Y axis).
- Trimming uses the rectangular crop box; a non-rectangular crop shape is
  ignored. No break lines yet.
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
| `v0.0` | Unreleased | 10.30.2026 | Prototype: steel and wood section components on members cut by or beyond the active section, side components along it, and built-up wood plies. | `dev.section-detailer` development commits |

## Backlog

- Phase 2: break lines at the crop boundary, grid components, browse for
  families outside the library.
- Phase 3: concrete, CMU, and a reference detail that ranks families first.
- Phase 4: architectural outline with a chosen line style.
