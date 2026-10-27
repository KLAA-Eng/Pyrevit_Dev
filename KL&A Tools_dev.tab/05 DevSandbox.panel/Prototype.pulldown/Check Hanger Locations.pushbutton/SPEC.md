# Check Hanger Locations

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.check-hanger-locations` |
| Tool version | `v0.0` |
| Status | Unreleased prototype; live acceptance pending |
| Status/origin | Prototype; KL&A custom tool ported from the KL&A Dynamo graph `Check Hanger Locations 1.0.3.dyn`. |
| Main delivery | Unreleased |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Check Hanger Locations.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Check Hanger Locations.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Check Hanger Locations.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Check Hanger Locations.pushbutton/script.py`; `lib/hanger_check/` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | Unreleased | 10.27.2026 | First DevSandbox port of the Check Hanger Locations Dynamo graph, with orientation-based member roles, strict Joist and loose Header size checks, Review/Review details status, wall and steel mounting, highlight refresh, and the Hanger Highlights toggle. | Pending commit on `dev.hangers`; pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Purpose

`Check Hanger Locations` confirms that every placed hanger family sits where a
framing member frames into another member and is oriented with it. For each
hanger it identifies the **supported** member (the member hung by the hanger)
and the **supporting** member (the member the hanger hangs from), colors them
in the active view, and reports hangers that do not match their framing.

## Scope and detection

- Hangers: every instance visible in the active view whose family name
  contains `Hangers_Clever_KLAA` (case-insensitive) is checked and colored.
  With hangers selected, the view zooms to them and the report lists only
  them; otherwise the report lists every visible hanger.
- Orientation: the hanger text direction is the family's local X axis in plan.
- Supported member: structural framing that runs along the top or base of the
  hanger text (within 30 deg of the text) and has an end inside the hanger box:
  2'-0" either way along the text, 1'-0" across it, 2'-0" vertically. The end
  closest to the hanger wins; a second end within 1" of that distance is noted
  as ambiguous. A member ending at the hanger but running more than 30 deg off
  the text gives `Hanger not aligned with member`.
- Supporting member: another framing member crossing the hanger text at 30 deg
  or more (square, or skewed up to 60 deg) whose location line passes within
  1'-0" in plan (2'-0" vertically) of the supported member's end. Members that
  run through are preferred over members that only end there, then the closest
  wins. The skew between supported and supporting members is reported.
- Only structural framing with a location line is considered; walls, columns,
  and ledgers are not supporting members. Curved members use their chord.
- Location status: `OK`, `No framing at hanger`, `Hanger not aligned with
  member`, `No supported member`, `No supporting member`, or `Shared member
  end` when two or more hangers claim the same end of the same member.
- Size check: values are the Smart Hanger schedule text, read from the
  instance, then the type. Plies, width, depth, material, and I-joist series
  are parsed and compared with the member's `Family: Type` name when it
  contains a `W x D` size, otherwise its width/depth parameters (`b`, `Width`,
  `d`, `Depth`, ...). Values that cannot be parsed are noted as not compared,
  never as mismatches.
  - `Joist` vs supported member is strict: depth within 1/8" (nominal sawn
    lumber such as `2x8` also matches its actual size), width when the hanger
    gives one or plies of 1 3/4" LVL/LSL, material (GLB, LVL, PSL, LSL, TJI),
    and I-joist series (`TJI 360`) when both name one. A member modeled as one
    ply of a built-up size matches with a note; an unconfirmed material is
    noted.
  - `Header` vs supporting member is loose, because schedules name the
    supporting member generally (`(2)LVL OR PACKOUT`, `LVL OR 2x8`): each `OR`
    alternative is tried for material and depth only, any match passes, and a
    mismatch needs every alternative to disagree. `WF BEAM` must be a steel W
    shape. A wood alternative on a steel beam (packout) is not compared.
- Support kind comes from the Header and the supporting member: steel (`WF`,
  `STEEL`, or a `W12X26` style member), wall (`PLATE`, `LEDGER`, `LEDGE`,
  `WALL`, `CONCRETE`, `CMU`, `MASONRY`), or column (`COLUMN`, `POST`). Walls
  and columns are not modeled framing, so a missing supporting member is
  expected for them.
- Mounting (from `Fastener-TF`; blank, `-`, or `--` means none): steel with
  top-flange fasteners is `Top flange mounted`, steel without them is `Face
  mounted - needs web packout`; other hangers with top-flange fasteners are
  `Top flange mounted`; otherwise walls show `Wall - ledger or plate` and
  columns `Column - see detail`.
- Reported status: a location problem first, then `Review` for any size
  mismatch, then `Review details` for wall or column supports, else `OK`.
- A hanger is a problem when its status is not `OK` or `Review details`, or it
  has a size mismatch.

## Output and model effects

One transaction first resets every override in the active view that uses a
hanger check color, then sets new overrides, so hangers fixed since the last
run lose their highlight:

- Members (projection and cut line color plus solid surface fill): supported
  = blue, supporting = yellow, supported by one hanger and supporting another
  = green.
- Problem hangers: halftone with red projection lines, no fill, so hanger text
  stays readable.

Existing overrides on colored elements are replaced. No other model data
changes. Views that do not allow graphic overrides are reported and left
uncolored. `Hanger Highlights` turns these colors off or back on.

The pyRevit output lists each hanger, problems first, then `Review details`,
with columns Hanger,
Hanger info (`Designation`, `Header`, `Joist` only), Status, Location match
(`Yes`, `Yes (skewed n deg)`, or `No`), Size mismatch (blank,
`Supported member mismatch`, `Supporting member mismatch`, or
`Both mismatch`), Mounting, Supported member and Supporting member (Id link plus
`Family: Type`), and Notes, plus a link that selects all problem hangers.

Report links use pyRevit's handler: clicking an Id selects the element and the
zoom icon also runs Revit's `ShowElements`, which frames the element's full
bounding box. The selection stays until the user presses Esc; the command
cannot change that behavior, so the report says so and tells users to select
a hanger and re-run to zoom to it.

## Implementation inventory

- Entry point: `script.py` (selection, report).
- `lib/hanger_check/revit_check.py`: Revit collection, hanger info, overrides,
  zoom; shared with `Hanger Highlights`.
- `lib/hanger_check/classify.py`: host-independent supported/supporting
  decisions, skew, shared-end flags, and member roles, covered by
  `tests/hanger_check_test.py`.
- `lib/hanger_check/sizes.py`: host-independent Header/Joist size parsing and
  mismatch labels, covered by `tests/hanger_sizes_test.py`.

## Validation boundary

Live Revit 2024+ acceptance must confirm that the hanger text runs along the
family's local X axis, the hanger box size on representative joist-to-header,
skewed, and header-to-girder framing, the halftone override, zoom, and that
re-running clears highlights for fixed hangers.

## Future development

- Make the hanger family name and box size configurable if other hanger
  families are adopted.
- Optionally report framing ends that frame into another member without a
  hanger.
