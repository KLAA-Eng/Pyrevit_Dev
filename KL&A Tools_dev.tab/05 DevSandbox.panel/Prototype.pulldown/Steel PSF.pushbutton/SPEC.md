# Steel PSF

## Purpose

`Steel PSF` is a read-only DevSandbox pyRevit prototype that reports host-model
structural framing and structural-column pounds per floor area. Pounds equal
usable instance length in feet multiplied by nominal section weight in lb/ft.

## Scope and output

The command collects eligible steel family instances, using framing Reference
Level and column Base Level where available, and computed Floor area. It prints
summary metadata plus groupings by level, category, family/type, and floor type.
Missing level, length, nominal weight, or area is excluded with a reason.

The current command only prints to the pyRevit output window. It does not export
CSV from the active workflow. The command does not start a transaction, modify,
save, or synchronize the Revit document.

## Validation boundary

Revit 2024+ fixture validation must confirm where each family's nominal-weight
parameter resides, its storage/unit conversion, known hand calculations, and
read-only behavior before quantity results are relied upon.

## Implementation inventory

- Entry point: `script.py`
- Direct imports: from __future__ import print_function;import csv;import os;import sys;from collections import defaultdict;from Autodesk.Revit import Exceptions as RevitExceptions;from pyrevit import DB, forms, revit, script;from steel_weight.aggregation import aggregate_steel_weight;from steel_weight.reporting import summary_csv_rows;
- Local helper functions: _extension_root,_level_record,_assignment_level,_first_parameter,_usable_length,_nominal_weight_lb_per_foot,_family_type_label,_steel_records,_collect_steel_record,_floor_area_records,_number,_print_summary,_print_report,_print_exclusions,_export_summary_csv,main,
- Bundled external assets: None.

## GUI and interaction

Static UI/API references: forms.alert,forms.save_file,output.print_md,output.print_table,script.get_output,

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

## Future development

- Wire the existing CSV projection into the active workflow with an explicit
  user prompt and `forms.save_file()` save-location dialog after the report is
  generated.
- CSV export should contain the same summary-level data shown in the pyRevit
  output, including level-split category, family/type, floor-type, and
  excluded/unavailable length summaries. It should continue to exclude raw
  steel-element and floor-element rows.
