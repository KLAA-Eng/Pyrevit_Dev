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
The window opts into `KlaWindowShell`: its header and footer are both 24 units
high, body padding is 16 horizontally and 8 vertically, and the centered footer
receives the calling command's pure version. Typography is Segoe UI: shared
14-unit section/table headings and 12-unit values/status text. The plane names
remain left-aligned under their centered heading; other table content is
centered by column, while numeric offsets remain right-aligned inside their
24-high shared compact fields. Level selectors use the shared dark ComboBox
and item styles, including full-surface opening and disabled/focus states.

The instruction area reserves at least 40 and at most 96 units, scrolling longer
messages so instruction text remains reachable.
Apply Changes and Reset remain a centered horizontal group with an 8-unit gap;
Apply uses the shared 216 x 32 main role and Reset the 104 x 28 secondary role.
Empty warnings take no space. Table/warning content can scroll independently
of the action group when the resizable, height-sized window reaches its limit.
The four plane colors, length formatting, table headings and Revit operations
are preserved by this presentation migration. In particular, the static
`Elevation - ft` heading remains the separately recorded unit-label issue.

`GUI.window_chrome.load_window()` delegates XAML loading to the installed
pyRevit `load_xaml` method for this `forms.WPFWindow`, retaining its host owner,
icon and Escape handling. The command still assigns its ViewModel, calls
`show()` modelessly, and removes the drawing server/events on Closed. The
shared loader does not show the window or own Revit event/transaction logic.

## Current execution logic

pyRevit loads the bundle and executes its entry point. The implementation uses
the imports and helper functions listed above; inspect `script.py` for the exact
branching order and host API calls.

## Model and external effects

Detected mutation/external-effect patterns: revit.Transaction,

## Current status

This is a command. The inventory above is statically derived
from the current bundle and must be confirmed inside the target Revit/pyRevit
environment before promotion or behavior changes.

## Tool versioning

| Field | Value |
| --- | --- |
| Tool ID | `core.viewrange` |
| Path aliases | `KL&A Tools.tab/03 Core Tools.panel/ViewRange.pushbutton` (0.0.0.beta–0.0.9); current `KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton` |
| Version inputs | `bundle.yaml`; `script.py`; `MainWindow.xaml`; `lib/GUI/window_chrome.py`; `lib/GUI/Resources/KLCodeComponents.xaml`; `lib/GUI/Resources/KLCodeFoundation.xaml`; `lib/GUI/Resources/KLCodeFoundationTokens.xaml` |
| Tool version | `v1.1` |
| Status/origin | Maintained — KL&A adaptation of pyRevit; View Range UI refinement released in the 0.0.11 beta. |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| `v1.0` | `0.0.6beta` | 09.15.2026 | KL&A adapted the shared window and branding behavior. | `300f8d4` |
| `v1.1` | `0.0.11` | 10.12.2026 | Refined table headings, text size, column alignment, message space, and vertical spacing for the View Range editor. | `70af2e1`, `d8c1d4f`; pending owner merge to main. |
