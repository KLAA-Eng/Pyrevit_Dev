# Zoom to Selection

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.zoom-to-selection` |
| Tool version | `v0.0` |
| Status | Unreleased prototype; live acceptance pending |
| Status/origin | Prototype; KL&A custom companion to `Check Hanger Locations`. |
| Main delivery | Unreleased |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Zoom to Selection.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Zoom to Selection.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Zoom to Selection.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Zoom to Selection.pushbutton/script.py`; `lib/hanger_check/revit_check.py` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | Unreleased | 10.28.2026 | First DevSandbox zoom companion for Check Hanger Locations. | Pending commit on `dev.hangers`; pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Purpose

pyRevit's report magnifier calls Revit's `ShowElements`, which did not
reliably zoom to hangers or members in plan. This command zooms the active
view to the current selection itself, following the solution in the pyRevit
forum thread "Zoom / Go to element"
(https://discourse.pyrevitlabs.io/t/zoom-go-to-element/3544/4), and the
`Check Hanger Locations` report links to it with a `Zoom to selection` button.

## Behavior

- Takes each selected element's bounding box in the active view
  (`get_BoundingBox(view)`); an element without one is not visible there.
- Re-selects the elements and calls `ZoomAndCenterRectangle` on the open UI
  view of the active view with the combined box, with no added margin.
- Nothing selected: an alert asks the user to select a hanger or member.
- None of the selection visible in the view: an alert says so and nothing
  zooms. Some not visible: the view zooms to the rest and an alert gives the
  count left out.
- No model data changes.

## Implementation inventory

- Entry point: `script.py`.
- Shared Revit adapter: `zoom_to` in `lib/hanger_check/revit_check.py`, also
  used by `Check Hanger Locations` when run with hangers selected.
- The report button targets this command by control id: the running command's
  control id with its last `%` segment replaced by `Zoom to Selection`, so the
  bundle folder name must stay `Zoom to Selection.pushbutton` in the same
  pulldown as `Check Hanger Locations`.

## Validation boundary

Live Revit 2024+ acceptance must confirm the report button runs this command,
that the zoom frames a hanger and a long member in plan, whether the tight
fit (no margin) shows enough context, and behavior in
sections and 3D views.
