# Check Hanger Locations

## Identity

| Field | Value |
| --- | --- |
| Bundle path | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Check Hanger Locations.pushbutton` |
| Tool ID | `devsandbox.check-hanger-locations` |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Check Hanger Locations.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Check Hanger Locations.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Check Hanger Locations.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Check Hanger Locations.pushbutton/script.py`; `lib/hanger_check/` |
| Maturity | Prototype |
| Tool version | `v0.0` |
| Status/origin | Prototype; KL&A custom tool ported from the KL&A Dynamo graph `Check Hanger Locations 1.0.3.dyn`. Unreleased prototype; live acceptance pending. |
| Maintainer | KL&A |
| Revit versions live-tested | None yet |

## Purpose and workflow

`Check Hanger Locations` confirms that every placed hanger family sits where a
framing member frames into another member and is oriented with it. For each
hanger it identifies the **supported** member (the member hung by the hanger)
and the **supporting** member (the member the hanger hangs from), colors them
in the active view, and reports hangers that do not match their framing.

1. Open the printing plan view that shows the hangers.
2. Select nothing to check and report every hanger in the active view, or
   select hangers to zoom to them and report only those.
3. Review the colors and the report. Click an Id to select it in Revit, then
   **Zoom to selection** to zoom the view to it; press Esc to clear the
   selection.
4. Fix the framing or hangers and re-run to clear resolved highlights.
5. Close the report to remove the colors, or use `Hanger Highlights` to turn
   them off or on.

### Scope and detection

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
  require the end within 2'-0" vertically of the hanger.
- Hexagon alignment: the KL&A standard places the hanger hexagon beside the
  supported member, with its top or bottom flat side (the two sides running
  along the text) on the member's side face, not overlapping the member. When
  the hexagon is found in the hanger's plan linework and has flat sides along
  the text (within 10 deg), candidates whose nearer side face lies within 1" of
  either flat side win over closer candidates that do not. The face is the
  member's location line offset by half its modeled width (type name `W x D`,
  width parameter, or type plies x ply width; the centerline when unknown).
  The chosen member is noted when the hexagon overlaps it (`Hexagon overlaps
  the supported member; align its top or bottom side with the member edge`)
  or when its edge is more than 1" off the flat sides. Without a usable
  hexagon the closest end wins, as before.
- Among equally aligned candidates the end closest to the hanger wins; a
  second end within 1" of that distance is noted as ambiguous. A member
  ending at the hanger but running more than 30 deg off the text gives
  `Hanger not aligned with member`.
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
  read as spaces. Member depth comes from the type name (`W x D`, or a lone
  size such as `(2)11 7/8" LVL`); a depth parameter (`d`, `Depth`, `h`,
  `Height`, ...) is used only when the name gives no depth or only a number
  under 3" (a grade or mark such as `2.0E` or `GL-1`). Member width comes
  from the type name's `W x D`, otherwise the width parameter (`b`, `Width`,
  ...). Depth notes say which source was used. Values that cannot be parsed
  are noted as not compared, never as mismatches.
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

## Inputs and prerequisites

- A project document; in a family document the command stops with an alert.
- Active view: any view; plan views use the plan-only matching above. Views
  that do not allow graphic overrides are checked and reported but not
  colored.
- Hangers: `Hangers_Clever_KLAA` point-based family instances visible in the
  active view, plus any selected ones. With none selected or visible the
  command stops with an alert.
- Hanger schedule parameters, read from the instance, then the type:
  `Designation`, `Header`, `Joist`, and `Fastener-TF`.
- Structural framing with a location line near each hanger. Member type
  names, and the width (`b`, `Width`, `B`, `Beam Width`, `Nominal Width`) and
  depth (`d`, `Depth`, `h`, `Height`, `Beam Depth`, `Nominal Depth`)
  parameters when the name does not give the size.
- Hanger plan linework that contains the hexagon (optional; see Scope and
  detection).
- The sibling `Zoom to Selection` bundle loaded on the ribbon, for the
  report's zoom button.
- pyRevit with a persistent engine for this bundle (`engine: persistent:
  true` in `bundle.yaml`), so the close handler survives after the script
  returns.

### Implementation inventory

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
- `lib/hanger_check/spatial.py`: host-independent plan grid index of member
  bounding boxes, covered by `tests/hanger_spatial_test.py`.

## Outputs and effects

### Model effects

One transaction (`Refresh hanger check highlights`) first resets every
override in the active view that uses a hanger check color (current or
earlier palette) and deletes the check's hexagon outlines, then highlights
again, so hangers fixed since the last run lose their highlight:

- Members (heavier projection line, cut line color, and solid surface fill):
  supported = blue, supporting = orange, supported by one hanger and
  supporting another = purple.
- Hangers: the hexagon found in the hanger's plan linework during the check
  (a closed loop of six roughly equal sides) is traced with view-specific
  detail lines in a heavy line style, red `KLA Hanger Check - Problem` for
  problems and teal `KLA Hanger Check - Review details` for wall/column
  supports. The hanger itself is not overridden, so its text keeps its own
  color. A hanger without a recognizable hexagon falls back to halftone with
  colored projection lines.

Closing the report window clears the highlights so no view or sheet keeps
them. The check only colors the view it runs in, and sheets show those same
views, so each colored view id is recorded in the AppDomain (per document,
for the Revit session) and closing the report clears just the recorded views
instead of scanning every view in the model, which was slow on large models.
The window's `Closed` event schedules that clear through pyRevit's
`execute_in_revit_context`, because the window closes outside Revit's API
context; the clear runs in its own `Clear hanger check highlights`
transaction. Each run (and `Hanger Highlights` turning colors on) stores a
run token in the AppDomain; a window only clears when its run is still the
latest, so closing an older report does not remove newer colors. The bundle
uses a persistent pyRevit engine so the close handler survives after the
script returns. The report says so in bold. If the window cannot be watched,
the report says to run `Hanger Highlights` to remove the colors.

Existing overrides on colored elements are replaced. The two line styles are
created in the project on first use, and their color and projection line
weight are set again each time outlines are drawn; outline detail lines exist
only in the checked view and are removed by re-running or by
`Hanger Highlights`. No other model data changes. Views that do not allow
graphic overrides are reported and left uncolored, and no transaction runs.

The command has no cancel point once started; the check itself only reads
the model, and all highlight changes of a run are in the one transaction
above.

### Report

The pyRevit output lists each hanger, problems first, then `Review details`,
with columns Hanger, Hanger info (hanger `Type` name, `Designation`,
`Header`, `Joist`), Status, Size mismatch (`-`, `Supported member mismatch`,
`Supporting member mismatch`, or `Both mismatch`), Mounting, Supported
member, Supported slope, Supporting member (Id link plus `Family: Type`), and
Notes, plus a link that selects all problem hangers. A summary line gives the
hangers reported and their source (selection or active view), problems,
review details, and the view name. The location result is carried by Status
and Notes.

### Selection and zoom

Hanger and member Ids are select-only links. pyRevit's magnifier runs Revit's
`ShowElements`, which did not reliably zoom to hangers or members, so the
report instead shows a `Zoom to selection` button (top, and again below
tables longer than 10 rows) that runs the sibling `Zoom to Selection` command
on the current selection. pyRevit runs the button by looking up its ribbon
control id and silently does nothing when the id is not found, so the report
reads the real id from the loaded Revit ribbon (an item whose id ends in
`%Zoom to Selection`, preferring this command's pulldown) instead of deriving
it; the report also tells users to run `Prototypes > Zoom to Selection` if
the button does nothing. With hangers selected, this command zooms to them
the same way.

The check records each hanger's framing joint: the supported member's end
projected onto the supporting member's location line (the supported end when
there is no supporting member). Zooms frame a hanger's insertion point and
its joint. The joint is an output only; the members are still found from the
hanger insertion point, text direction, and hexagon. The selection stays
until the user presses Esc. The report tells users, in bold, to zoom from the
printing plan view rather than from a sheet.

## Limits and compatibility

- The hanger family name (`Hangers_Clever_KLAA`) and the hanger box size are
  fixed in `lib/hanger_check/classify.py`.
- Only structural framing with a location line can be a supported or
  supporting member; walls, columns, and ledgers are reported through the
  Header support kind instead.
- Any element override in the view whose projection line color exactly
  matches a hanger check color (current or earlier palette) is treated as a
  check highlight and reset.
- The colored-view record and run token live in the AppDomain for the
  current Revit session only.
- Each hanger type's hexagon is assumed not to change with instance
  parameters (see Performance).
- Revit 2024 and later is the repository design target; no Revit version has
  live evidence yet.

### Performance

Each run does its Revit work once, not once per hanger:

- Framing is collected in one pass for all hangers (one view-scoped collector
  in plan views, bounded by all hangers plus the search reach), indexed by
  model bounding box in a 6'-0" plan grid; each hanger's candidates are the
  members whose box meets its search box, the same test as Revit's
  `BoundingBoxIntersectsFilter` used before.
- Each member's `Family: Type`, width parameter, parsed width and (when
  compared) depth parameter are read once and reused for half widths, size
  checks, notes, support kind, and the report.
- Each hanger type's hexagon is read from geometry once, kept in family
  coordinates, and placed at later instances with their transform (mirrored
  and rotated instances included). This assumes the hexagon does not change
  with instance parameters; a type with no hexagon found is read per
  instance.

## Validation evidence

| Date | Extension release | Revit version | Scenario | Result | Evidence link or location |
| --- | --- | --- | --- | --- | --- |
| 10.30.2026 | `0.0.14-dev` | None (CPython) | `tests/hanger_check_test.py`, `tests/hanger_sizes_test.py`, `tests/hanger_outline_test.py`, and `tests/hanger_spatial_test.py` classification, size, hexagon, and spatial index rules | Pass | Local run on `dev.hangers` |

Automated checks do not prove Revit transactions or the user workflow; live
acceptance is pending.

### Validation boundary

Live Revit 2024+ acceptance must confirm that the hanger text runs along the
family's local X axis, the hanger box size on representative joist-to-header,
skewed, and header-to-girder framing, plan-only matching on projects with
level offsets, that the hexagon is found and traced in plan, the fallback
override, the Zoom to selection button, the close-window clear (including
views on sheets, a second report open at once, and its speed on a large
model), the non-breaking space fix on real schedule text, hexagon flat-side
alignment on real hanger linework, slope on sloped joists, and that
re-running clears highlights for fixed hangers.

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | Unreleased | 10.27.2026 | First DevSandbox port of the Check Hanger Locations Dynamo graph, with orientation-based member roles, strict Joist and loose Header size checks, Review/Review details status, wall and steel mounting, highlight refresh, and the Hanger Highlights toggle. | Pending commit on `dev.hangers`; pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Backlog

- Make the hanger family name and box size configurable if other hanger
  families are adopted.
- Optionally report framing ends that frame into another member without a
  hanger.
- Live Revit acceptance (see Validation boundary).
