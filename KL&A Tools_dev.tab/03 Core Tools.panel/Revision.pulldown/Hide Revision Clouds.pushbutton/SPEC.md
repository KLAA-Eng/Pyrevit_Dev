# Hide/Unhide Revision Clouds

## Purpose

Hide or unhide selected revision-cloud elements on selected project sheets and
their placed views. Hide also turns the selected revisions off in each selected
sheet's titleblock revision schedule; Unhide leaves that schedule unchanged.

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
clouds and leaves each selected sheet's titleblock revision schedule unchanged.

## Validation boundary

Validate the command in Revit with clouds owned directly by a sheet and by a
placed view, plus cancellation and already-in-requested-state paths. Confirm
the titleblock revision schedule removes entries on Hide and remains unchanged
on Unhide.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: `pyrevit`, `System.Collections.Generic.List`,
  `Autodesk.Revit.UI`, and `GUI.forms.select_from_dict`
- Model mutation: one Revit transaction using `View.HideElements` or
  `View.UnhideElements` and `ViewSheet.SetAdditionalRevisionIds`

## Current status

This is a Core Tools development-tab command. Static and unit checks do not
replace live Revit acceptance.
