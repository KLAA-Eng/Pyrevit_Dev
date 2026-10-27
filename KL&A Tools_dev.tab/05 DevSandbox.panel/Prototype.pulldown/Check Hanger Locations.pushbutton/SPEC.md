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
| v0.0 | Unreleased | 10.27.2026 | First DevSandbox port of the Check Hanger Locations Dynamo graph. | Pending commit on `dev.hangers`; pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Purpose

`Check Hanger Locations` confirms that every placed hanger family sits where a
framing member frames into another member. For each hanger it identifies the
**supported** member (the member hung by the hanger) and the **supporting**
member (the member the hanger hangs from), colors them in the active view, and
reports hangers that are missing either one.

## Scope and detection

- Hangers: selected instances whose family name contains `Hangers_Clever_KLAA`
  (case-insensitive); with no hanger selected, every such hanger visible in the
  active view. Other selected elements are ignored.
- Search box: the hanger insertion point +/- 1'-0" in plan and +/- 2'-0"
  vertically, matching the Dynamo graph's D1/D2 inputs. Only structural
  framing with a location line is considered; walls, columns, and ledgers are
  not supporting members.
- Supported member: the framing member whose start or end point lies in the
  box; the end closest to the hanger in plan wins. A second non-parallel member
  end within 1" of the same distance is noted as ambiguous.
- Supporting member: another framing member, not parallel to the supported
  member, whose location line passes through the box. Members that run through
  the hanger are preferred over members that only end there, then the closest
  in plan wins.
- Status: `OK`, `No framing at hanger`, `No supported member`,
  `No supporting member`, or `Shared member end` when two or more hangers claim
  the same end of the same member.

## Output and model effects

One transaction sets element graphic overrides in the active view (projection
and cut line color plus solid surface fill): supported = blue, supporting =
yellow, a member that is supported by one hanger and supporting another =
green, hanger with any non-`OK` status = red. Existing overrides on those
elements are replaced. No other model data changes. Views that do not allow
graphic overrides are reported and left uncolored.

The pyRevit output lists each hanger with status, supported and supporting
member links, and notes, problems first, plus a link that selects all problem
hangers.

Shift+Click clears overrides in the active view whose projection line color is
one of this command's check colors.

## Implementation inventory

- Entry point: `script.py` (hanger and framing collection, overrides, report).
- `lib/hanger_check/classify.py`: host-independent supported/supporting
  decisions, shared-end flags, and member roles, covered by
  `tests/hanger_check_test.py`.

## Validation boundary

Live Revit 2024+ acceptance must confirm hanger insertion points relative to
member ends on representative joist-to-header and header-to-girder framing,
the search box size, and the color overrides. Curved members are evaluated on
their end-to-end chord.

## Future development

- Make the hanger family name and search box size configurable if other
  hanger families are adopted.
- Optionally report framing ends that frame into another member without a
  hanger.
