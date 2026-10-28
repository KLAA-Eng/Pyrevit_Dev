# Hanger Highlights

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.hanger-highlights` |
| Tool version | `v0.0` |
| Status | Unreleased prototype; live acceptance pending |
| Status/origin | Prototype; KL&A custom companion to `Check Hanger Locations`. |
| Main delivery | Unreleased |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Hanger Highlights.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Hanger Highlights.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Hanger Highlights.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Hanger Highlights.pushbutton/script.py`; `lib/hanger_check/` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | Unreleased | 10.27.2026 | First DevSandbox highlight toggle for Check Hanger Locations. | Pending commit on `dev.hangers`; pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Purpose

Turns the hanger check colors on or off in the active view without opening a
report, so users can review the plan clean and bring the check back quickly.

## Behavior

- Off: if any hanger or framing element in the active view has an override
  whose projection line color is a hanger check color, or the view has check
  hexagon outlines, they are reset and deleted in one transaction. Only the
  active view changes (clearing every view was too slow); closing the
  `Check Hanger Locations` report clears every view the check colored.
- On: otherwise every hanger visible in the active view is checked with the
  same rules as `Check Hanger Locations` and the framing and problem hangers
  are colored (see that command's SPEC for rules and colors).
- An alert reports the count cleared, or hangers checked and problems found.
- Views that do not allow graphic overrides and family documents stop with a
  message and no changes. Turning on also marks
  a new run so an older open report closing does not clear the new colors.

## Implementation inventory

- Entry point: `script.py`.
- Shared Revit adapter: `lib/hanger_check/revit_check.py`; rules in
  `lib/hanger_check/classify.py`.

## Validation boundary

Live Revit 2024+ acceptance must confirm the toggle clears only hanger check
colors and that other element overrides in the view are untouched. An unrelated
override that happens to use exactly one of the check colors is cleared too.
