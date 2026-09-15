# Create View Detail Folders

## Purpose

`Create View Detail Folders` is a DevSandbox pyRevit prototype that creates a
local deliverable package for each matching individual Detail or Drafting view.
It does not modify, save, or synchronize the Revit model.

## Scope and output

The command lets the user select one or more Detail and Drafting view types,
then select an existing destination folder. It finds non-template project views
whose type matches the selected view types.

For each matching view, the command creates a direct child folder named:

`<detail number or Unplaced> - <view name>`

Folder names are sanitized for Windows path safety. Invalid filename characters
and control characters are replaced with underscores, leading/trailing invalid
folder-name punctuation is removed, and reserved Windows device names are
prefixed with an underscore.

Each successful folder receives:

- `detail.pdf`: native Revit PDF export, combined as a single ANSI A page.
- `detail.jpg`: 2400-pixel JPEG preview exported from the view.
- `index.html`: static HTML page linking the PDF and displaying the JPEG.

The pyRevit output window reports selected view types, matching view count,
created folders, folder errors, and per-folder PDF/JPEG/HTML export status.

## Preflight and overwrite behavior

The command is fail-closed before creating folders. It stops if the destination
is not an existing absolute folder, no matching views exist, multiple views
resolve to the same folder name, a target folder already exists, or a planned
artifact path would collide with existing destination content.

Existing output is never overwritten. Folder creation is direct-child only under
the selected destination, and generated image paths are checked before rename so
an unexpected Revit image path cannot escape the detail folder.

## Exclusions and limits

The command only considers non-template `Detail` and `DraftingView` views. It
does not process sheets, legends, schedules, model views, templates, Revit links,
or view types outside the Detail and Drafting view families.

Views that are not printable do not receive a PDF/JPEG/HTML package and are
reported in the export table. HTML is only written after both PDF and JPEG files
exist.

Native PDF export requires Revit 2022 or later. This remains a DevSandbox
prototype and must be validated against the target Revit/pyRevit environment
before promotion.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: from __future__ import print_function;import os;import sys;import traceback;from pyrevit import DB, forms, revit, script;from System.Collections.Generic import List;from GUI.forms import select_from_dict;from detail_view_deliverables import build_deliverable_plan, has_export_failures, is_direct_child_path;from detail_view_folders import build_folder_plan, create_folder_paths;from detail_view_html import render_detail_html;
- Local helper functions: _extension_root,_element_id_value,_element_name,_view_family_name,_is_target_view_family,_view_type_label,_view_type_options,_select_view_types,_select_destination,_has_supported_revit_version,_detail_number,_matching_view_records,_existing_destination_paths,_show_preflight_errors,_element_id_list,_export_pdf,_jpeg_fit_direction,_export_jpeg,_export_html,_export_view_deliverables,_report,main,
- Shared helper modules: `lib/detail_view_folders.py`, `lib/detail_view_deliverables.py`, `lib/detail_view_html.py`
- Bundled external assets: None.

## GUI and interaction

Static UI/API references: forms.alert,forms.pick_folder,output.print_md,output.print_table,script.get_output,select_from_dict,

Use the command from its pyRevit button. Select the Detail and Drafting view
types to package, choose an existing destination folder, then review the pyRevit
output table and final alert for any folder creation or export failures.

## Model and external effects

Detected model mutation patterns: No Revit transaction or direct model mutation
pattern detected.

External filesystem effects: creates destination child folders and writes
`detail.pdf`, `detail.jpg`, and `index.html` files inside each created folder.

## Current status

This is a development-tab command. The inventory above is statically derived
from the current bundle and must be confirmed inside the target Revit/pyRevit
environment before promotion or behavior changes.
