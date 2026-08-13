# Highlight Changed Elements

## Purpose

`Highlight Changed Elements` is a DevSandbox pyRevit prototype for comparing
selected sheets and their placed-view content with a separate local baseline
RVT. It is a graphics-only review aid: it never saves either document.

## Compared scope

For selected sheets, the command compares eligible content in placed views and
direct sheet-owned content. This includes detail components, annotations, tags,
text notes, keynotes, dimensions, and placed schedules. A fingerprint records
type, location, and parameter/content values. Schedules additionally include
available table header/body cells. Missing comparison data is reported as
unsupported; it is never silently treated as unchanged.

Title blocks, revision clouds, Revit links, and deleted current-model elements
are excluded from highlighting. Deleted baseline elements remain report-only.

## Highlight and clear behavior

New or modified eligible content is highlighted red in its placed view. A
changed schedule definition/content is highlighted by overriding its
`ScheduleSheetInstance` on every selected owning sheet. Existing overrides are
preserved in highlight mode. Clear mode removes matching red element overrides
only for currently changed targets. Unsupported override operations are reported
per target and do not abort unrelated targets.

## Validation boundary

This remains a Revit 2024+ DevSandbox prototype. A paired baseline/current RVT
fixture must validate each requested annotation class, schedule content
signature, schedule-instance graphics, preserved existing overrides, and
read-only close-without-save behavior before the prototype is promoted.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: from __future__ import print_function;import os;from Autodesk.Revit import Exceptions as RevitExceptions;from pyrevit import DB, forms, revit, script;from changed_elements.comparison import compare_fingerprints;from GUI.forms import select_from_dict;from graphics.overrides import create_red_projection_override;
- Local helper functions: _stop,_is_supported_revit_version,_select_baseline_path,_sheet_label,_select_sheets,_open_baseline_document,_worksharing_conflict_message,_is_supported_element,_type_key,_rounded_coordinate,_location_key,_parameter_value,_content_key,_schedule_content_key,_fingerprint,_elements_owned_by_view,_elements_visible_in_view,_sheet_in_document,_fingerprints_for_sheets,_add_fingerprint,_placed_views,_schedule_instances,_has_existing_overrides,_visible_changed_elements,_is_highlight_override,_red_override_settings,_clear_override_settings,_apply_highlights,_clear_highlights,_changed_targets,_append_changed_owned_elements,_append_changed_visible_elements,_append_target,_highlighted_changed_elements,_highlight_sheet,_print_change_report,main,
- Bundled external assets: None.

## GUI and interaction

Static UI/API references: forms.alert,forms.pick_file,output.print_md,output.print_table,script.get_output,

Use the command from its pyRevit button. Where it exposes a dialog or selection
workflow, make the required selection and review the result before confirming.

## Current execution logic

pyRevit loads the bundle and executes its entry point. The implementation uses
the imports and helper functions listed above; inspect `script.py` for the exact
branching order and host API calls.

## Model and external effects

Detected mutation/external-effect patterns: .SetElementOverrides,revit.Transaction,

## Current status

This is a development-tab command. The inventory above is statically derived
from the current bundle and must be confirmed inside the target Revit/pyRevit
environment before promotion or behavior changes.
