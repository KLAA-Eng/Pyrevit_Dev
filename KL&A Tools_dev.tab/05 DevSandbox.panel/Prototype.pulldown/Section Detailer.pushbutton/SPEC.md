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
component on every cut member by hand. This command does the steel part of
that: it reads the members cut by the active section and places the matching
KL&A `Section` detail component on each one.

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
- Members: structural framing and columns visible in the view whose type name
  is an AISC designation (`W12X26`, `HSS6X6X1/4`, `HSS6.000X0.250`, `L4X4X1/2`,
  `C10X15.3`, `MC12X10.6`, `WT9X17.5`, `HP12X53`, `PIPE4STD`).
- KLAA library at
  `J:\Standards\910 Revit Support\KLAA Library\KLAA Detail Components\Div 05 - Metals`
  with type catalogs beside each family. Without the library, only types
  already loaded in the project can be placed.

## Outputs and effects

- Adds one detail component per cut member, at the center of the member's cut
  profile, rotated so the family's up direction follows the member's depth
  direction. Each placed component's Comments is set to `Section Detailer`.
- **Replace** deletes the earlier `Section Detailer` components in this view
  only. Hand-placed components are never touched.
- Loads individual types (`LoadFamilySymbol`) from the newest revision of the
  matching KLAA family, only after the user approves.
- All loading and placement is one undo step. An error rolls back the whole run.
- The pyRevit output lists the count placed and every member skipped, with the
  reason.

## Matching rules

Type names compare without case, spaces, or insignificant decimal zeros, so
Revit's `W12X26` matches the KLAA catalog's `W12x26`. Shape maps to family:
W → `5_WideFlange_Section`, rectangular HSS → `5_HSS_Section`, round HSS →
`5_HSS_Round_Section`, L → `5_Angle_Section`, C and MC → `5_Channel_Section`,
WT → `5_WT_Section`, HP → `5_HP_Section`, Pipe → `5_Pipe_Section`. When several
loaded families match, KLAA families are listed first.

## Limits and compatibility

- Places only members whose axis runs into the view (within about 25° of the
  view direction) and that cross the cut plane. Members running along the
  section, oblique members, curved members, and members beyond the cut are
  reported, not placed.
- S, M, and other shapes without a KLAA section family are reported.
- Unconfirmed until live testing: each family's insertion point (the tool
  places at the profile center), rotation for rotated members, and mirroring of
  asymmetric shapes (L, C, WT).
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
| `v0.0` | Unreleased | 10.30.2026 | Phase 1 prototype: steel section components on members cut by the active section. | `dev.section-detailer` development commits |

## Backlog

- Phase 2: break lines at the crop boundary, grid components, browse for
  families outside the library.
- Phase 3: `Side` components for members along the section, concrete, CMU,
  wood, and a reference detail that ranks families first.
- Phase 4: architectural outline with a chosen line style.
