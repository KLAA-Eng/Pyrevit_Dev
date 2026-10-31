# Shared dialogs

Opt-in Python WPF library, introduced on 2026-10-29. This contract owns the
shared dialogs and the confirmed refinement; existing tools keep their calls.
The [consolidation plan](../../../docs/plans/custom-window-consolidation.md)
owns implementation status. The [API guide](README.md) owns usage examples.

- AC-001: Importing `GUI.dialogs` requires neither WPF nor an active document.
  Factory functions construct windows; `show_*`/selection/prompt helpers show
  them modally and return `DialogResult`. No automatic script exit occurs.
- AC-002: Message is an OK-only notice with information/warning/error/success
  and optional collapsed Details. Both Message variants omit the shared footer
  and its reserved row; Close and OK remain. The center chrome title is blank;
  the caller title remains Window.Title for accessibility/task switching.
  Initial height fits content up to the cap.
  Width changes do not force height changes during manual resizing. Expanding
  Details grows the bottom, preserving the message viewport until capped;
  content remains scrollable. Repeated expansion/collapse does not drift size.
  Close/Escape cancels; OK returns action `ok`. The 32-unit severity icon and
  22-unit Segoe UI SemiBold heading match the outline severity color; body and
  details text remain 12. Details header and text use the main body foreground.
  Message-only icons are octagon-alert, triangle-alert,
  info and check-check for error, warning, information and success. Details uses
  a 16-unit right/down chevron; expanded text aligns with the body and the icon
  centers vertically beside the heading. Global icon roles remain unchanged.
- AC-003: Generic single/multiple selection preserves input order, payload
  identity, duplicate labels, caller-owned rows, explicit initial checks and
  checks hidden by groups/search. No first item is checked automatically.
  Check All/None acts only on visible eligible rows. Disabled rows cannot be
  accepted. Required selection validates before closing. Both modes use the
  same checkbox style. Single checking unchecks any previous row, including
  hidden rows. Select explicitly accepts; Enter/double-click never accept.
  Batch controls are absent in single mode. Initial size is 432 x 576, matching
  the Selection template. Search precedes the optional group dropdown; both are
  24 high and align after 16-unit Search/Group icons plus an 8-unit gap. The
  Group role uses Lucide Layers-2. Template 8/4-unit vertical gaps separate the
  sections. Gray Select All/None buttons center above the single green Select
  action, with an 8-unit row gap. No visible Cancel button; Close/Escape cancels.
  No selected/visible count summary is shown below the list. Validation remains
  inline, and removing the summary does not leave an empty spacing row.
  Initial focus is the neutral body, with no search selection/autofocus.
  Search text aligns with Group text at an 8-unit rendered input inset.
- AC-004: Action choices return a stable key after explicit selection and
  confirmation. Disabled choices cannot be accepted; no initial choice exists.
  Its existing layout/keyboard behavior stays unchanged; redesign is deferred.
- AC-005: Text prompts preserve raw input. Accepted empty text differs from
  cancellation. Required and optional caller validation show inline feedback.
  Compact height fits input/validation; no separate visible prompt header.
  The empty input displays `[ENTER TEXT]` as a watermark, never a field value
  or accepted result. Caller defaults remain actual editable input.
  Input is 36 high, FontSize 24, centered
  Segoe UI Bold with KLCode colors. Retain title/Close; remove footer and its
  reserved row. Input-or-validation/OK gaps are 8. The only
  visible action is the same 104 x 28 `KlaButton` OK used by Message; no Cancel button.
  Both use the standard 8-unit content-to-action gap. Content-driven minimum height avoids
  extra blank space. Enter accepts valid text; title Close/Escape cancels.
- AC-006: Existing shared palette, typography, controls and icons remain the
  presentation authority. Standard bodies use the shell/green-gray footer;
  Message and Text omit the footer; floating Command Switch has its own compact
  panel. Owner is an explicit WPF window/native handle. No import queries the
  current document. All factories construct without showing; modal helpers
  show and return explicit results without running model operations.
- AC-007: Gallery has one row per shared family, listing available variants and
  selecting one beside State. Search includes variant labels; variant and state
  persist per family for the session. Selection has Sheets, Revisions, Open
  Documents, List Single and List Multiple; Message has Without Details and With
  Details; Command Switch has Commands only and Commands with toggles; Rename
  has Single field, Two fields and Multiple fields. Both Message variants offer
  Normal, Empty, Warning, Error, Success, Disabled and Long content; With Details
  retains diagnostics in Empty. Other shared variants retain five standard
  states. Other catalog rows remain available. Previews use fictional data and
  invoke neither model collectors nor production commands.
- AC-008: Read-only collectors are separate from windows and lazy-load Revit.
  Sheets sort by number, group by saved sheet sets plus implicit All Sheets,
  and exclude placeholders by default consistently in every group. Caller can
  include placeholders/filter rows. Revisions retain sequence order, showing
  number/description/date/issued status; both issued states are eligible by
  default. Per-sheet numbering uses sequence rather than an invalid project
  RevisionNumber lookup. Open documents exclude links/active document by
  default, include family/project documents, and show type/path. Explicit active
  document is required to exclude it; no active document can be silently inferred.
  All collectors preserve payload identity and perform no transaction/mutation.
- AC-009: Separate Command Switch matches the compact floating pyRevit layout
  with KLCode colors: prompt/search, wrapping immediate command buttons,
  optional toggles; no corner x, shared header/footer or Continue button.
  Initial focus is the neutral panel, not the search field. Typing or Tab can
  enter search; it is not selected automatically on open.
  Typing filters commands only; toggles retain state/visibility. Tab traverses,
  Space toggles; Enter chooses a focused command or sole enabled match while
  search is focused, never a toggle. Escape clears search then cancels when
  empty. Dragging beyond the system threshold moves the window from any
  surface, including controls, without activating a command/toggle. Ordinary
  clicks and text editing remain available. Clicking outside dismisses with
  cancel, including over the disabled modal owner; blank inside clicks stay open.
  Confirm returns action `accept`,
  value `{'command': key, 'switches': {key: bool}}`; cancel returns None.
- AC-010: Shared buttons/checks/radios/toggles have no FocusVisualStyle adorner,
  white underline or focus-square override. No light-green frame surrounds a
  focused button or checkbox/label. Controls remain focusable/keyboard usable;
  input/dropdown field-focus styling and ordinary control borders stay unchanged.
- AC-011: KLC-Rename accepts one to three caller-defined property groups laid
  out horizontally. Each group has one Find/Replace pair and Prefix/Suffix;
  optional Uppercase/Lowercase buttons act separately for that field and return
  the operation and field. Rename validates and returns all entered rules;
  Enter activates it. Invalid rules stay open with inline feedback. Close/Escape
  cancels. Case actions close without applying model changes. No live preview,
  Revit mutation or existing tool migration is part of this shared dialog.
  Initial focus is neutral, with no field selected. Compact label/input spacing
  and a fitted section border remove unused trailing space; action gaps are 8.

Prepared-row factories are host-independent; optional modal convenience helpers
invoke collectors in a valid Revit API context before showing UI. Callers own
document lifetime and any subsequent operations. These APIs are not drop-in
replacements for pyRevit return types. Existing multi-button Message options
are retired from this unused opt-in API; existing CustomAlert retains its API.

Native file/folder/color pickers, progress and selection overlays, existing
CustomAlert/SelectFromDict workflow migration and packaged compiled assemblies
are out of scope. The owner's subsequent presentation change removes the footer
from both shared Message variants and legacy CustomAlert.
