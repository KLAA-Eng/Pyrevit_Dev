# Shared dialog interaction polish — 2026-10-30

Owner requested Command Switch movement/outside dismissal, Message presentation,
compact neutral Rename, an empty-field Text Entry watermark, and reconciliation
of their window moves and Form deletion. Baseline: `4f0e99d`.
The [consolidation plan](../../../plans/custom-window-consolidation.md) owns
GUI-37/38; the [shared SPEC](../../../../lib/GUI/dialogs/SPEC.md) owns behavior.

Command Switch tracks a left-button drag from any surface and starts native
DragMove after the Windows drag threshold. Completed drags suppress command
and toggle activation. Subtree capture receives outside clicks even when its
modal owner cannot activate; outside buttons and deactivation cancel. Child
captures and Search context menus retain editing behavior. Closing guards
against recursive Deactivated/Close dispatch.

Independent review reproduced an initial context-menu regression: delayed
capture rearming stole the popup's capture and immediately closed Copy/Paste.
The implementation now preserves associated context-menu capture and rearms
when it closes. The regression is covered in the shown WPF probe.
Follow-up review also removed speculative ContextMenuOpening state: WPF can
raise that event without opening a menu. Only an actual owned popup capture
suspends rearming, so right-clicking blank/command areas cannot disable dragging
or subsequent outside dismissal.

Message has a 32-unit severity icon and 22-unit colored SemiBold heading.
Details header and text bind to the main body's foreground. Its center chrome
title is blank; caller Window.Title, Close, OK, sizing and results remain.
Rename starts with neutral focus, four empty unselected fields, a 52-unit label
column and a section border fitted to the inputs with eight units of right
padding. Case/action gaps remain eight. No stray glyph was visible in the
inspected neutral shown-window render; its prior source was not conclusively
reproduced. Text Entry has no visible prompt header. `[ENTER TEXT]` is an overlay
watermark, never input data. Caller defaults and accessible prompt names remain.

Owner file changes are retained: Form removed, Options/Review renamed to
KLC-OptionsTemp/KLC-ReviewTemp, CreateFromRooms moved to GUI/_future with renamed
XAML, and match moved to GUI/_future/match. Gallery mappings, resource loads,
relative/caller imports, tests and documentation links follow the actual paths.

Verification:

- Python suite: 399 tests, 398 passed and one existing skip.
- Installed IronPython 2.7.12/Windows WPF: 39 catalog rows, 24 Window sources and
  130 custom/variant/state constructions; 74 shared layouts, 15 Rename layouts,
  10 template layouts and 45 production layouts pass.
- Message severity/details colors, blank visual title, glyph/text edges,
  disclosure, selection/copy, scroll, cap and resize contracts pass.
- Text watermark visibility, actual empty acceptance, raw defaults, validation
  and shared 104×28 OK/eight-unit gap pass. Rename field bounds, border inset,
  action gaps and neutral shown focus pass.
- Three owned shown focus fixtures and Command Switch's additional shown
  capture/context-menu/modal fixture pass. Outside right-click uses an actual
  routed WPF event; drag activation suppression uses handler dispatch.
- Scale audit: zero strict violations, 86 existing/advisory literals.
- No compiled resource or packaged assembly changed.

Native pointer-driven DragMove and live Revit ownership/DPI remain owner
acceptance. A temporary standalone native-input fixture was attempted but
dismissed on deactivation before a native drag could be exercised; it does not
establish that acceptance. No user Revit session or model was controlled.

Inspected renders: [Message Details](2026-10-30-dialog-interaction-evidence/message-details.png),
[Warning](2026-10-30-dialog-interaction-evidence/message-warning.png),
[neutral Rename](2026-10-30-dialog-interaction-evidence/rename-neutral.png),
[empty Text Entry](2026-10-30-dialog-interaction-evidence/text-entry-empty.png).
