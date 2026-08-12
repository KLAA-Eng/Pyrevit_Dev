# Highlight Changed Elements

## Purpose

`Highlight Changed Elements` is a DevSandbox pyRevit prototype for finding host-model elements that are new or materially changed compared with a separate baseline RVT file.

The tool is sheet-focused. It does not highlight every changed element in the model. It only highlights changed elements that are visible inside placed views on the sheets selected by the user.

## User Flow

1. The user runs the command from pyRevit.
2. The command verifies that the active document is a Revit project and that the Revit version is 2024 or newer.
3. The command opens the green-themed multi-select sheet picker.
4. The user selects one or more non-placeholder project sheets.
5. The command asks the user to pick a local baseline `.rvt` file.
6. The command compares the active project model against the baseline project model.
7. The command either highlights changed elements or clears existing red highlights, depending on the current state of the selected sheets.
8. The command prints a pyRevit output report with comparison totals and per-sheet results.

## Inputs

- Active Revit project document.
- One or more selected non-placeholder sheets from the active document.
- A local baseline `.rvt` file.

The baseline file must exist, must have the `.rvt` extension, must be a Revit project, and must not be the same file as the active model.

## What The Script Looks For

The script compares model elements by `UniqueId`.

For each host-model element in both the baseline model and the active model, it builds a fingerprint containing:

- The element type identity, based on the element type `UniqueId`.
- The element location.

Location is reduced to a stable comparison key:

- Point-based elements compare point `X`, `Y`, `Z`, and rotation.
- Curve-based elements compare start point `X`, `Y`, `Z` and end point `X`, `Y`, `Z`.
- Elements without a point or curve location use a generic `none` location key.

Coordinate values are rounded to 6 decimal places before comparison.

## Change Categories

The comparison produces four categories:

- `New`: element exists in the active model but not in the baseline.
- `Modified`: element exists in both models but its type or location fingerprint changed.
- `Unchanged`: element exists in both models and its fingerprint matches.
- `Deleted`: element exists in the baseline but not in the active model.

Only `New` and `Modified` elements are candidates for highlighting or clearing.

`Deleted` elements are report-only because they do not exist in the active model and cannot be highlighted.

## Sheet Visibility Logic

After the model comparison is complete, the script checks the selected sheets.

For each selected sheet, it gathers placed views using `sheet.GetAllPlacedViews()`.

Only placed views that allow graphic overrides are processed.

Within each processable placed view, the script collects visible, non-type elements and checks whether each element's `UniqueId` is in the `New` or `Modified` result set.

The same element can be processed once per placed view. If an element appears in multiple selected sheets or multiple views, each view-specific override is handled separately.

## Highlight Mode

If the selected sheets do not already contain a matching red highlight on any visible `New` or `Modified` element, the command runs in highlight mode.

In highlight mode, the script applies a red element override to visible `New` and `Modified` elements.

The override currently sets:

- Red projection line color.
- Red cut line color.

Before applying a highlight, the script checks whether that element already has an element-level override in that view.

If an existing override is found, the script does not overwrite it. The element is skipped and reported as `Existing element override preserved`.

## Clear Mode

If any visible `New` or `Modified` element on the selected sheets already has a red projection-line or cut-line override, the command runs in clear mode.

Clear mode follows the same core reset behavior as `Override 2D.smartbutton`: it applies a fresh empty `DB.OverrideGraphicSettings()` to the matching elements.

This removes the element-level override in that view.

Clear mode only targets visible `New` or `Modified` elements whose current element override has:

- Projection line color red, or
- Cut line color red.

The red match is exactly RGB `255, 0, 0`.

## Important Clear-Mode Limitation

Revit element overrides do not record which command created them.

Because of that, the script cannot prove that a red override came from this tool. It treats matching red projection-line or cut-line overrides on currently changed elements as highlights to clear.

This is practical for prototype behavior, but it is not command-owned state tracking.

## What The Script Does Not Look For

The script intentionally does not compare or process:

- Linked models.
- View-specific elements.
- Revit link instances.
- Annotation elements.
- Detail items.
- Tags.
- Dimensions.
- Revision clouds.
- Sheet title blocks as sheet annotations.
- Deleted active-model elements, because they no longer exist in the active model.
- Parameter changes unrelated to element type or location.
- Geometry changes that do not change the tracked type or location fingerprint.
- Category-level, filter-level, view-template, or object-style graphic differences.

## What The Script Does Not Do

The script does not:

- Modify the baseline RVT.
- Save the active model.
- Create revision clouds.
- Create a persistent audit record.
- Store command-owned highlight IDs.
- Restore prior element overrides after clearing.
- Process placeholder sheets.
- Process views that do not allow graphic overrides.
- Compare cloud models, central/local model metadata, or worksharing history.

## Output Report

The command writes a pyRevit output report with:

- The action performed: `Highlighted` or `Cleared`.
- The number of selected sheets.
- The baseline file path.
- Counts for `New`, `Modified`, `Unchanged`, and `Deleted`.
- Total highlighted or cleared element-view pairs across selected sheets.
- Total skipped overrides.
- A per-sheet table showing placed views checked, elements highlighted or cleared, and skips.
- A modified-elements table with each modified element `UniqueId` and the detected reason.
- A deleted-elements table for baseline elements missing from the active model.
- A skipped-overrides table when applicable.

## Current Status

This command is still a DevSandbox prototype. It has been syntax-checked outside Revit, but full validation requires running it in Revit 2024 or newer with an active project model and a separate local baseline RVT.
