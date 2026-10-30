# Input alignment and shared OK actions — 2026-10-30

Owner requested left-aligned Rename/Search text, Search/Group text alignment,
neutral Selection initial focus and matching Text Entry/Message OK buttons and
spacing. Baseline: `77d4a4d`. The [consolidation plan](../../../plans/custom-window-consolidation.md)
owns GUI-36; [shared SPEC](../../../../lib/GUI/dialogs/SPEC.md) owns behavior.

The foundation TextBox template applied Padding twice: natively and as the
content-host margin. Installed WPF measured Search's text at 19 units inside
its border, while Group used 8. Removing the redundant host margin and using
`KlaTextBoxPadding=5,0` gives 8 after the native two-unit inset and one-unit
border. Generic button/toggle padding remains 8. This fixes shared TextBox
consumers rather than adding offsets to individual Search/Rename controls.
Multiline readouts apply their own padding once; Message's separately aligned
Details template remains intact. The derived five-unit native compensation is
intentional; the rendered alignment remains on the eight-unit scale.

Selection's Loaded handler focuses its neutral body, leaving Search unfocused
and unselected. Tab still reaches controls. Text Entry now uses Message's
`KlaButton` OK (104 x 28). Both use `KlaActionTopGap` (8), including expanded
Message Details. Header, footer opt-outs and result/validation behavior remain.

Verification:

- Actual WPF alignment assertion reproduced Search X=43 versus Group X=32,
  then passed with both X=32 and an 8-unit inset. Rename uses the same inset.
- Actual OK styles/dimensions and 8-unit gaps pass for Text, plain Message
  and expanded Details. Existing validation, sizing and overflow probes pass.
- 399 Python tests: 398 pass, one existing skip. The CustomAlert test double
  was updated for the already-shipped footer opt-out; production code unchanged.
- 135 custom/variant/state constructions, 74 shared layouts, 45 production
  layouts, 15 templates, Message alignment/copy/resize and 15 Rename layouts pass.
- Shown owned Selector confirms neutral focus and no Search selection before
  testing keyboard checkbox focus. Command Switch shown-focus fixture also passes.
- 17 C# source tests and seven compiled WPF instances on each of net48 and
  net8.0-windows pass. Zero strict scale violations; 86 advisory literals include
  the deliberate native TextBox compensation token. Generated artwork is current.
- Independent read-only review found no actionable regression in the foundation,
  multiline hosts, neutral focus, action styles or documented contracts.

Inspected renders: [Search/Group](2026-10-30-input-alignment-evidence/selection-search.png),
[Rename](2026-10-30-input-alignment-evidence/rename.png),
[Text Entry](2026-10-30-input-alignment-evidence/text-entry.png) and
[Message](2026-10-30-input-alignment-evidence/message.png).

No model operation or packaged DLL changed. Compiled consumers need rebuilt
deployment assets to receive the foundation correction. Live Revit/input/DPI
acceptance remains with the owner.
