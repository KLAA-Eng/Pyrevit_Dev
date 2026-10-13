# Hide/Unhide Revision Clouds

## Purpose

Hide or unhide selected revision-cloud elements on selected project sheets and
their placed views. Hide also removes selected revisions from each selected
sheet's additional revisions. Unhide does not edit additional revisions, but
visible clouds can automatically add their revisions to the sheet's schedule.

## Behavior

The command prompts for **Hide** or **Unhide**, then presents the KLCode green
multi-select dialogs for revisions and non-placeholder sheets. It finds clouds
for the selected revisions visible on each selected sheet, then changes each
cloud in its owner view and any selected placed dependent view that displays
the cloud, matching the Engineering Notes strategy. It uses the sheet's
individual revision-cloud ids instead of expanding related
primary/dependent-sheet relationships.

Hide permanently hides visible matching clouds and removes each selected
revision from every selected sheet's additional revisions, even if that sheet
has no matching revision cloud. Unhide permanently unhides hidden matching
clouds and leaves each selected sheet's additional revisions unchanged. For
both actions, the report compares the selected revisions returned by
`GetAllRevisionIds()` before and after the transaction to show schedule
entries added or removed. It reports additional-revision edits separately.

## Validation boundary

Validate the command in Revit with clouds owned directly by a sheet and by a
placed view, plus cancellation and already-in-requested-state paths. Confirm
the schedule report agrees with visible titleblock entries after Hide and
Unhide, including when a revision remains listed for another reason.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: `pyrevit`, `System.Collections.Generic.List`,
  `Autodesk.Revit.UI`, and `GUI.forms.select_from_dict`
- Model mutation: one Revit transaction using `View.HideElements` or
  `View.UnhideElements` and `ViewSheet.SetAdditionalRevisionIds`

## Current status

This is a Core Tools development-tab command. Static and unit checks do not
replace live Revit acceptance.

## Tool versioning

| Field | Value |
| --- | --- |
| Tool ID | `core.revision.hide-revision-clouds` |
| Path aliases | `KL&A Tools.tab/03 Core Tools.panel/Revision.pulldown/Hide Revision Clouds.pushbutton` (0.0.7–0.0.9); current `KL&A Tools_dev.tab/03 Core Tools.panel/Revision.pulldown/Hide Revision Clouds.pushbutton` |
| Version inputs | `bundle.yaml`; `script.py`; `lib/GUI/forms.py` |
| Tool version | `v1.1` |
| Status/origin | Maintained — KL&A custom command. |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| `v1.0` | `0.0.7` | 09.28.2026 | Added the KL&A hide/unhide revision-cloud workflow. | `2c4a3b2` |
| `v1.1` | `Unreleased` | 10.13.2026 | Report actual selected revision schedule membership after Hide and Unhide. | Pending next main delivery. |
