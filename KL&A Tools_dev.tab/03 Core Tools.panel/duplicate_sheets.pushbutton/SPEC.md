# duplicate_sheets

## Purpose

Documents the current command implementation and intended user-facing behavior.

## Behavior

This command is implemented by `script.py` in this pyRevit bundle. It runs in the Revit/pyRevit host and uses the active-document context required by its implementation. It must preserve unrelated model content and report unsupported or cancelled interactions without applying partial changes.

## Validation boundary

Validate this command against a representative Revit fixture, its empty or cancelled-input path, and its documented output or transaction effect before promotion beyond development use.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: from Autodesk.Revit.DB import *;from Autodesk.Revit.UI.Selection import *;import pyrevit;from pyrevit import revit;from pyrevit import forms;from Snippets._selection import get_selected_sheets;import clr;from pyrevit.forms import WPFWindow;from System.Diagnostics.Process import Start;from System.Collections.Generic import List;from System.Windows.Window import DragMove;from System.Windows.Input import MouseButtonState;
- Local helper functions: __init__,remove_special_charachter,update_view_name,update_sheet_name,update_sheet_number,duplicate_schedules,duplicate_legends,duplicate_views,duplicate_elements,duplicate_lines,duplicate_clouds,duplicate_images,duplicate_text,duplicate_dimensons,duplicate_symbols,duplicate_dwgs,duplicate_selected_sheets,set_additional_revisions_on_sheet,get_sheet_title_block,get_selected_sheets,view_find,view_replace,view_prefix,view_suffix,sheet_number_find,sheet_number_replace,sheet_number_prefix,sheet_number_suffix,sheet_name_find,sheet_name_replace,sheet_name_prefix,sheet_name_suffix,checkbox_views,checkbox_legends,checkbox_schedules,checkbox_images,checkbox_lines,checkbox_text,checkbox_clouds,checkbox_dwgs,checkbox_symbols,checkbox_dimensions,checkbox_additional_revisions,use_existing_legends,use_existing_schedules,button_close,Hyperlink_RequestNavigate,header_drag,radiobutton_duplicate_option,button_run,
- Bundled external assets: None.

## GUI and interaction

Static UI/API references: WPFWindow,forms.WPFWindow,forms.alert,

Use the command from its pyRevit button. Where it exposes a dialog or selection
workflow, make the required selection and review the result before confirming.

## Current execution logic

pyRevit loads the bundle and executes its entry point. The implementation uses
the imports and helper functions listed above; inspect `script.py` for the exact
branching order and host API calls.

## Model and external effects

Detected mutation/external-effect patterns: No Revit transaction or direct mutation pattern detected.

## Current status

This is a development-tab command. The inventory above is statically derived
from the current bundle and must be confirmed inside the target Revit/pyRevit
environment before promotion or behavior changes.
