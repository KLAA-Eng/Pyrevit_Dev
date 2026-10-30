# Shared dialogs

Opt-in Python WPF library, introduced on 2026-10-29. This contract owns the
four reusable dialog families; the existing tools keep their current calls.
The [consolidation plan](../../../docs/plans/custom-window-consolidation.md)
owns implementation status. The [API guide](README.md) owns usage examples.

- AC-001: Importing `GUI.dialogs` requires neither WPF nor an active document.
  Factory functions construct windows; `show_*`/selection/prompt helpers show
  them modally and return `DialogResult`. No automatic script exit occurs.
- AC-002: Message windows support information/warning/error/success, collapsed
  optional details, and one to three explicit OK/Yes/No/Retry/Cancel actions.
  No is distinct from Cancel. Close/Escape/window close always cancel.
- AC-003: Generic single/multiple selection preserves input order, payload
  identity, duplicate labels, caller-owned rows, explicit initial checks and
  checks hidden by groups/search. No first item is checked automatically.
  Check All/None acts only on visible eligible rows. Disabled rows cannot be
  accepted. Required selection validates before closing.
- AC-004: Action choices return a stable key after explicit selection and
  confirmation. Disabled choices cannot be accepted; no default choice exists.
- AC-005: Text prompts preserve raw input. Accepted empty text differs from
  cancellation. Required and optional caller validation show inline feedback.
- AC-006: All windows use existing shared shell, palette, icon geometry,
  typography, controls and green/gray footer. Enter invokes the default action;
  Escape follows the same cancellation path as Close. Explicit owners may be
  WPF windows or native handles. No implicit document/host lookup occurs.
- AC-007: Gallery offers message, confirmation, grouped selection, parameter
  selection, action choice and text prompt previews in five fictional states.
  These exercise real library windows without running production commands.

Prepared rows are a caller responsibility. The library does not collect Revit
sheets, revisions, views, documents or parameters; apply sheet-set grouping,
revision ordering/issued rules and parameter eligibility before constructing
rows. It is not a drop-in replacement for pyRevit's return types.

Native file/folder/color pickers, progress and selection overlays, existing
CustomAlert/SelectFromDict and packaged compiled assemblies are out of scope.
