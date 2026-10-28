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
  2'-0" either way along the text, 1'-0" across it. In plan views the hanger
  height is ignored and only framing the view shows is considered, matching
  the Dynamo graph's projection onto the level, so hangers placed at a level
  or offset different from the framing still find it; other views also
  require the end within 2'-0" vertically of the hanger. The end
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
  are parsed and compared with the member's `Family: Type` name. Sizes and
  plies come from the type name only, never the family name (for example
  `Framing_KLAA_15SE`); material and I-joist series may come from either.
  Numbers glued to letters or underscores (`15SE`, `2.0E`) are codes, not
  sizes. Non-breaking and thin spaces in schedule text (`7&nbsp;1/4"`) are
  read as spaces. Member depth
  comes from the type name (`W x D`, or a lone size such as `(2)11 7/8" LVL`);
  a depth parameter (`d`, `Depth`, `h`, `Height`, ...) is used only when the
  name gives no depth or only a number under 3" (a grade or mark such as
  `2.0E` or `GL-1`). Member width comes from the type name's `W x D`,
  otherwise the width parameter (`b`, `Width`, ...). Depth notes say which
  source was used. Values that cannot be parsed are noted as not compared,
  never as mismatches.
  - `Joist` vs supported member is strict: depth within 1/8" (nominal sawn
    lumber such as `2x8` also matches its actual size), material (GLB, LVL,
    PSL, LSL, TJI), and I-joist series (`TJI 360`) when both name one; an
    unconfirmed material is noted.
  - Width follows KL&A modeling: a built-up member is one element the full
    width of all plies, plies x 1 3/4" for LVL/LSL and plies x 1 1/2" for
    sawn lumber. The hanger width (explicit, or its plies x ply width) must
    equal the member's full width, so `(2)11 7/8" LVL` needs a 3 1/2" member
    and `(2)2x10` a 3" member. The member width is its width parameter, or the
    `W x D` in its type name; a type name with plies and a one-ply size
    (`(2)1 3/4" x 11 7/8"`, `(2)2x10`) means plies x ply width. When the type
    name gives plies, they must match the hanger's plies and the modeled width
    (plies x ply width). Mismatch notes list the hanger and member sizes.
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
- Mounting, for every hanger, from `Fastener-TF` (blank, `-`, `--`, `N/A`,
  `NONE` mean none): `Top flange mounted` with top-flange fasteners, otherwise
  `Face mounted`. Steel face mounts read `Face mounted - needs web packout`;
  wall supports add `- wall ledger or plate` and columns `- column, see
  detail`.
- Supported slope: `Flat` when the supported member's location line rises
  less than 0.5 deg, otherwise `Sloped r:12 (a deg)`.
- Skew of 2 deg or more between supported and supporting members is noted.
- Reported status: a location problem first, then `Review` for any size
  mismatch, then `Review details` for wall or column supports, else `OK`.
- A hanger is a problem when its status is not `OK` or `Review details`, or it
  has a size mismatch.

## Output and model effects

One transaction first resets every override in the active view that uses a
hanger check color (current or earlier palette) and deletes the check's
hexagon outlines, then highlights again, so hangers fixed since the last run
lose their highlight:

- Members (heavier projection line, cut line color, and solid surface fill):
  supported = blue, supporting = orange, supported by one hanger and
  supporting another = purple.
- Hangers: the hexagon found in the hanger's plan linework (a closed loop of
  six roughly equal sides) is traced with view-specific detail lines in a
  heavy line style, red `KLA Hanger Check - Problem` for problems and teal
  `KLA Hanger Check - Review details` for wall/column supports. The hanger
  itself is not overridden, so its text keeps its own color. A hanger without
  a recognizable hexagon falls back to halftone with colored projection lines.

Existing overrides on colored elements are replaced. The two line styles are
created in the project on first use; outline detail lines exist only in the
checked view and are removed by re-running or by `Hanger Highlights`. No
other model data changes. Views that do not allow graphic overrides are
reported and left uncolored.

The pyRevit output lists each hanger, problems first, then `Review details`,
with columns Hanger,
Hanger info (hanger `Type` name, `Designation`, `Header`, `Joist`), Status,
Size mismatch (`-`, `Supported member mismatch`, `Supporting member mismatch`,
or `Both mismatch`), Mounting, Supported member, Supported slope, Supporting
member (Id link plus `Family: Type`), and Notes, plus a link that selects all
problem hangers. The location result is carried by Status and Notes.

Hanger and member Ids are select-only links. pyRevit's magnifier runs Revit's
`ShowElements`, which did not reliably zoom to hangers or members, so the
report instead shows a `Zoom to selection` button (top, and again below long
tables) that runs the sibling `Zoom to Selection` command on the current
selection. The selection stays until the user presses Esc.

## Implementation inventory

- Entry point: `script.py` (selection, report, zoom button).
- `Zoom to Selection.pushbutton`: zoom companion run by the report button.
- `lib/hanger_check/revit_check.py`: Revit collection, hanger info, overrides,
  zoom; shared with `Hanger Highlights`.
- `lib/hanger_check/classify.py`: host-independent supported/supporting
  decisions, skew, shared-end flags, and member roles, covered by
  `tests/hanger_check_test.py`.
- `lib/hanger_check/sizes.py`: host-independent Header/Joist size parsing and
  mismatch labels, covered by `tests/hanger_sizes_test.py`.
- `lib/hanger_check/outline.py`: host-independent hexagon detection, covered
  by `tests/hanger_outline_test.py`.

## Validation boundary

Live Revit 2024+ acceptance must confirm that the hanger text runs along the
family's local X axis, the hanger box size on representative joist-to-header,
skewed, and header-to-girder framing, plan-only matching on projects with
level offsets, that the hexagon is found and traced in plan, the fallback
override, the Zoom to selection button, the non-breaking space fix on
real schedule text, slope on sloped joists, and that re-running clears highlights for fixed hangers.

## Future development

- Make the hanger family name and box size configurable if other hanger
  families are adopted.
- Optionally report framing ends that frame into another member without a
  hanger.
