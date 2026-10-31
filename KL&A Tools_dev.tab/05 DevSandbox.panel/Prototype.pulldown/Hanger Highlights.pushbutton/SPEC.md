# Hanger Highlights

## Identity

| Field | Value |
| --- | --- |
| Bundle path | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Hanger Highlights.pushbutton` |
| Tool ID | `devsandbox.hanger-highlights` |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Hanger Highlights.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Hanger Highlights.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Hanger Highlights.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Hanger Highlights.pushbutton/script.py`; `lib/hanger_check/` |
| Maturity | Prototype |
| Tool version | `v0.0` |
| Status/origin | Prototype; KL&A custom companion to `Check Hanger Locations`. Unreleased prototype; live acceptance pending. |
| Maintainer | KL&A |
| Revit versions live-tested | None yet |

## Purpose and workflow

Turns the hanger check colors on or off in the active view without opening a
report, so users can review the plan clean and bring the check back quickly.

1. Open the view to toggle.
2. Click the command. If the view has hanger check highlights they are
   cleared; otherwise every visible hanger is checked and colored.
3. Read the alert, and run `Check Hanger Locations` for the full report.

### Behavior

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
  message and no changes. Turning on also marks a new run so an older open
  report closing does not clear the new colors.

## Inputs and prerequisites

- A project document and an active view that allows graphic overrides;
  otherwise the command stops with an alert and changes nothing.
- To turn colors on: `Hangers_Clever_KLAA` hangers visible in the active
  view, with the same hanger parameters and framing as
  `Check Hanger Locations`. With no visible hangers an alert says so and
  nothing changes.
- The current selection is not used.

### Implementation inventory

- Entry point: `script.py`.
- Shared Revit adapter: `lib/hanger_check/revit_check.py`; rules in
  `lib/hanger_check/classify.py`.

## Outputs and effects

- Off: one `Clear hanger check highlights` transaction resets the matching
  element overrides to default and deletes the check's outline detail lines
  in the active view, and removes the view from the session's colored-view
  record.
- On: one `Refresh hanger check highlights` transaction applies the same
  member overrides, hexagon outlines, and fallback hanger overrides as
  `Check Hanger Locations`, creating or updating its two
  `KLA Hanger Check - ` line styles, and records the view as colored for the
  session. A new run token is stored in the AppDomain before coloring.
- No report window is opened; results are shown in an alert only.
- No other model data changes. The command has no cancel point once started.

## Limits and compatibility

- Clearing affects only the active view; other colored views are cleared by
  closing the `Check Hanger Locations` report.
- An unrelated override that happens to use exactly one of the check colors
  is cleared too.
- Revit 2024 and later is the repository design target; no Revit version has
  live evidence yet.

## Validation evidence

| Date | Extension release | Revit version | Scenario | Result | Evidence link or location |
| --- | --- | --- | --- | --- | --- |
| 10.30.2026 | `0.0.14-dev` | None (CPython) | Shared hanger rules in `tests/hanger_check_test.py`, `tests/hanger_sizes_test.py`, `tests/hanger_outline_test.py`, and `tests/hanger_spatial_test.py`; the toggle itself is host-only | Pass | Local run on `dev.hangers` |

Automated checks do not prove Revit transactions or the user workflow; live
acceptance is pending.

### Validation boundary

Live Revit 2024+ acceptance must confirm the toggle clears only hanger check
colors and that other element overrides in the view are untouched. An
unrelated override that happens to use exactly one of the check colors is
cleared too.

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | Unreleased | 10.27.2026 | First DevSandbox highlight toggle for Check Hanger Locations. | Pending commit on `dev.hangers`; pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Backlog

- Live Revit acceptance (see Validation boundary).
