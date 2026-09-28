# ViewRange

## Purpose

Documents the current command implementation and intended user-facing behavior.

## Behavior

This command is implemented by `script.py` in this pyRevit bundle. It runs in the Revit/pyRevit host and uses the active-document context required by its implementation. It must preserve unrelated model content and report unsupported or cancelled interactions without applying partial changes.

## Validation boundary

Validate this command against a representative Revit fixture, its empty or cancelled-input path, and its documented output or transaction effect before promotion beyond development use.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: from pyrevit import script, forms, revit, HOST_APP, DB, UI;from pyrevit.revit import events;from pyrevit.framework import Convert, List, Color, SolidColorBrush;from pyrevit.compat import get_elementid_value_func;import traceback;from Autodesk.Revit.Exceptions import InvalidOperationException;from collections import OrderedDict;
- Local helper functions: __init__,Execute,GetName,__init__,Execute,GetName,__new__,__init__,active_view,active_view,source_view,source_view,update_view_range,_update_view_range_internal,_validate_view_range_order,_populate_available_levels,__init__,_set_current_level_selections,context_changed,is_valid,__init__,message,message,warning_message,warning_message,can_modify_view,can_modify_view,available_levels,available_levels,topplane_level_id,topplane_level_id,bottomplane_level_id,bottomplane_level_id,viewdepth_level_id,viewdepth_level_id,cutplane_level_name,cutplane_level_name,topplane_elevation,topplane_elevation,cutplane_elevation,cutplane_elevation,bottomplane_elevation,bottomplane_elevation,viewdepth_elevation,viewdepth_elevation,topplane_new_value,topplane_new_value,cutplane_new_value,cutplane_new_value,bottomplane_new_value,bottomplane_new_value,viewdepth_new_value,viewdepth_new_value,__init__,window_closed,apply_changes_click,reset_values_click,refresh_active_view,view_activated,selection_changed,doc_changed,compare_views,can_use_view_as_source,corners_from_bb,create_edges,create_triangles,get_color_from_plane,
- Bundled external assets: None.

## GUI and interaction

Static UI/API references: forms.Reactive,forms.WPFWindow,forms.alert,forms.reactive,script.get_output,

Use the command from its pyRevit button. Where it exposes a dialog or selection
workflow, make the required selection and review the result before confirming.

## Current execution logic

pyRevit loads the bundle and executes its entry point. The implementation uses
the imports and helper functions listed above; inspect `script.py` for the exact
branching order and host API calls.

## Model and external effects

Detected mutation/external-effect patterns: revit.Transaction,

## Current status

This is a development-tab command. The inventory above is statically derived
from the current bundle and must be confirmed inside the target Revit/pyRevit
environment before promotion or behavior changes.
