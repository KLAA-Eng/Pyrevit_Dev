# Shared window variants — 2026-10-30

The owner confirmed the design after KLCode grilling. Baseline: `16c1863`.
Superseded in part the same day: Message icons and headings are 32 and 22 (see
[dialog interaction polish](2026-10-30-dialog-interaction-polish.md)) and
KLC-Rename is 346/668/990 wide (see
[dialog sizing and focus](2026-10-30-dialog-sizing-focus.md)).
The [consolidation plan](../../../plans/custom-window-consolidation.md) owns
GUI-31 through GUI-34; [shared-dialog SPEC](../../../../lib/GUI/dialogs/SPEC.md)
and the adjacent Gallery SPEC own behavior. Production tool calls and packaged
DLLs are unchanged. The owner's pre-existing deletion of the retired Selection
Markdown pointer is preserved; historical links now point to the shared API.

Gallery now lists six shared families rather than separate rows for each
selection preset. Variant lists the available options; the adjacent dropdown
chooses a reviewed adapter. Variant labels/category participate in search, and
variant/state choices survive filtering during the session. Window/source and
Variant sorting retain explicit sort paths. Shared factories and Gallery
fixtures supply runtime data; XAML owns layout and fixed control labels.

Message offers Without Details and With Details, each with seven states. Empty
with Details retains diagnostic text. Severity symbols are 24 units and headings
18 Segoe UI SemiBold, both using the outline brush. Message-only Octagon Alert
and Check Check roles preserve other consumers' error/success icons. Info and
Triangle Alert remain; Details uses 16-unit right/down chevrons. Its local
readout template aligns actual text with the body while preserving selection,
copy and scrolling. All new artwork uses the existing pinned Lucide revision
and retained ISC notice.

Command Switch has Commands only and Commands with toggles. KLC-Rename has
one, two or three horizontal caller-defined groups at widths 384/712/1040.
It clones inputs and returns rules, or a separate case operation and field key.
Validation stays inline and protects the action at minimum height. No model
operation or live before/after preview runs in this shared window. The internal
module is `rename_window.py`, keeping the public `rename(...)` helper callable
after lazy loading. Command Switch uses `command_switch_window.py` for the same
reason; a failing isolated import reproduced its previous helper/module collision
before the fix. Public helper names and result contracts remain unchanged.

Verification:

- New choice/rename tests failed before their implementations, then passed.
  Final Python suite: 399 tests, 398 pass and one existing skip.
- Actual IronPython 2.7.12/WPF: 40 catalog rows and 135 custom/variant/state
  constructions; 74 shared-dialog layouts, 15 reference-template layouts and
  45 production layouts pass. Gallery dropdown/filter retention and actual UIA
  ascending/descending sorting pass for Window source and Variant.
- Message probe: eight severity/details combinations; actual text left X=13
  and right X=515 match at width 560. Details UIA toggle, chevron state,
  selection/copy, repeated expansion/collapse, manual resizing, 640 cap and
  both overflow panes pass.
- Rename probe: 15 horizontal variant/state layouts, field bounds, accepted
  snapshots, validation/edit recovery, Enter/click, separate case actions,
  disabled Enter/click rejection and cancellation pass.
- All 22 icon resources, wordmark pixels, scrollbars and 15 focus-style roles
  pass. Two owned shown focus fixtures pass; no system-wide input is injected.
- 17 compiled source tests pass; seven real compiled WPF instances pass on
  each of net48 and net8.0-windows with the added resource roles.
- Generated artwork, Gallery bundle/SPEC metadata, local documentation links
  and whitespace checks pass. Existing documentation adoption advisories remain.
- Independent review found a direct family-launch result bug and disabled
  Rename Enter path; both are fixed with regression evidence. Targeted recheck
  found no further actionable issues.

Inspected renders:

- [Shared families and dropdowns](2026-10-30-shared-window-variants-evidence/gallery-shared-variants.png)
- [Message without Details](2026-10-30-shared-window-variants-evidence/dialog-message-plain-success.png)
- [Message error](2026-10-30-shared-window-variants-evidence/dialog-message-error.png)
- [Expanded Details](2026-10-30-shared-window-variants-evidence/dialog-message-details-expanded.png)
- [Three-group Rename](2026-10-30-shared-window-variants-evidence/dialog-rename-three-normal.png)

Physical keyboard/pointer/DPI and live Revit owner/model acceptance remain with
the owner. Isolated Windows probes and compiled resource smokes do not replace
those checks or deploy packaged binaries.
