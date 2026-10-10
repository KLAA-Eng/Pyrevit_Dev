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

The View Range window shows the four planes in a table headed **Plane**,
**Elevation - ft**, **Level Offset**, and **Level**. These headings are static;
the displayed elevation and offset values follow the model's length units.
The heading text is bold 16, table values and controls are 14, and status
messages are 12. The plane names are left-aligned under their centered header;
other table content is centered by column, while numeric offsets remain
right-aligned inside their fields. The instruction area reserves 40 layout
units for its one- or two-line message. Apply and Reset use the main template's
Arial 14 action-button text. Nearby vertical gaps use 8 layout
units, with 16 between sections. Empty status messages take no space; longer
messages can expand the window or scroll within the content area. The footer,
KLCode palette, and four plane colors retain their existing treatment.

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

## Tool versioning

| Field | Value |
| --- | --- |
| Tool ID | `core.viewrange` |
| Path aliases | `KL&A Tools.tab/03 Core Tools.panel/ViewRange.pushbutton` (0.0.0.beta–0.0.9); current `KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton` |
| Version inputs | `bundle.yaml`; `script.py`; `MainWindow.xaml`; `lib/GUI/Resources/WPF_styles.xaml` |
| Tool version | `v1.1` |
| Status/origin | Maintained — KL&A adaptation of pyRevit; unreleased View Range UI refinement on `dev`. |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| `v1.0` | `0.0.6beta` | 09.15.2026 | KL&A adapted the shared window and branding behavior. | `300f8d4` |
| `v1.1` | `Unreleased` | 10.09.2026 | Refined table headings, text size, column alignment, message space, and vertical spacing for the View Range editor. | `70af2e1`, `d8c1d4f`; pending next main delivery. |
