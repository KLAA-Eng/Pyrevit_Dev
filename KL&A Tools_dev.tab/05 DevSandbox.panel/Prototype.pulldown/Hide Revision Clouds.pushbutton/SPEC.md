# Hide Revision Clouds

## Purpose

`Hide Revision Clouds` is a DevSandbox pyRevit prototype that permanently hides
revision cloud elements for selected revisions on selected sheets and in views
placed on those sheets.

## Scope and output

The command first uses the KLCode green multi-select dialog to select one or
more revisions, then uses the same green multi-select sheet dialog to select
one or more non-placeholder sheets. It scans the selected sheets themselves and
the views placed on those sheets, finds revision cloud elements owned by those
targets, and hides only clouds whose `RevisionId` matches one of the selected
revisions.

The pyRevit output window reports selected revisions, selected sheets, sheet
views checked, total sheet/placed views scanned, hidden clouds, already hidden
clouds, not-hideable clouds, views with no matching clouds, and hide errors.

## Exclusions and limits

The command does not change `Revision.Visibility`, revision numbering, sheet
revision membership, revision schedules, view templates, filters, categories,
or temporary hide/isolate state.

The command processes selected sheets and their placed views. It does not
process the active view unless that view is one of those targets.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: `System.Collections.Generic.List`; `pyrevit.DB`, `forms`,
  `revit`, `script`; `GUI.forms.select_from_dict`
- Model mutation: one Revit transaction calling `View.HideElements` for
  matching revision cloud element ids

## Current status

This is a development-tab command and must be validated inside the target
Revit/pyRevit environment before promotion.
