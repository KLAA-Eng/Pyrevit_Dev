# UI Gallery

## Purpose

Provides a safe launcher gallery for the pyRevit and KL&A dialog families used
by this extension. Each preview uses fictional seeded data and never starts a
Revit transaction or calls a document-changing command.

## Behavior

This command is implemented by `script.py` in this pyRevit bundle. It runs in
the Revit/pyRevit host without requiring active-model content. It must preserve
unrelated model content and report unsupported or cancelled interactions without
applying partial changes.

## Validation boundary

Validate every launcher against a representative Revit fixture and its
cancelled-input path before promotion beyond development use. Confirm that no
preview starts a Revit transaction or changes the document.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: from __future__ import print_function;import os;import sys;from pyrevit import forms;from ui_gallery.launchers import gallery_launchers;
- Local helper functions: _extension_root,__init__,__init__,filter_changed,selection_changed,launch_selected,close_window,_matches,_update_actions,_launch,_launch_dialog,_launch_find_replace_preview,_launch_steel_psf_preview,
- Bundled external assets: None.

## GUI and interaction

Static UI/API references: forms.WPFWindow,forms.alert,forms.ask_for_string,
forms.CommandSwitchWindow,forms.SelectFromList,

Use the command from its pyRevit button, select a row, and choose **Open
Selected Window**. All lists and alerts contain fictional data. The gallery
only opens dialog previews; it does not invoke the corresponding tool command.

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
