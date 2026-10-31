# Shared dialog sizing and focus — 2026-10-30

Baseline: `1285ada`. The owner requested Switch prompt alignment and typography,
removal of its outer green outline, Rename sizing/spacing, and a neutral Text
Entry with a blank center title and gray, focus-aware watermark.
The [consolidation plan](../../../plans/custom-window-consolidation.md) owns
GUI-39 and the subsequent Action Choice interview. The
[shared SPEC](../../../../lib/GUI/dialogs/SPEC.md) owns the resulting behavior.

Switch uses a 16-unit SemiBold prompt with its visible glyphs centered beside
the input. Its outer panel has no outline. Rename fits measured section widths
at 346/668/990 for one/two/three groups, with 16-unit horizontal outer insets.
Its header-to-label and action-to-footer gaps are 12. Height follows current
controls and validation, including the absence of optional case actions.

Independent review reproduced a long-heading regression in the first fitted
layout: Auto columns let a caller heading push later sections offscreen. The
final implementation wraps headings within measured section widths; the exact
two-group reproduction now ends at x=652 in a 668-unit window, preserving the
16-unit right inset. No actionable findings remained after recheck.

Text Entry retains caller Window.Title metadata but has no center chrome title.
Initial focus is the neutral body, with no selected input. Empty unfocused input
shows `[ENTER TEXT]` in `KlaFooterVersionBrush` (#808080); focus hides it before
typing, and leaving an empty input restores it. The watermark remains an overlay,
never caller data. Its compact line box and optical inset center visible glyphs.

Verification:

- Python suite: 399 tests, 398 passed and one existing skip.
- Installed IronPython 2.7.12/WPF: 39 Gallery entries and 130 custom/state
  constructions; existing dialogs, 15 Rename state layouts, Message variants,
  templates and production layouts pass.
- Actual drawing bounds place the Switch prompt and Text watermark ink centers
  within half a unit of the input center.
- Rename checks exact widths/insets, field bounds, 12-unit top/bottom gaps,
  long heading wrapping, optional case-action height and validation recovery.
- Four owned shown focus fixtures pass; Text checks initial neutral focus,
  focus/blur watermark transitions, gray brush and blank title. Existing Switch
  capture/menu/modal routed-pointer checks remain green.
- Independent review verified its long-heading finding was fixed.
- UI scale audit: zero strict violations; 88 advisory consumer literals,
  including the two documented 2-unit optical text insets. Documentation audit
  and all local Markdown links pass.

No live Revit session or model was used. Physical input and Revit/DPI appearance
remain the owner's host review. No compiled resource or packaged assembly changed.

Inspected renders: [Switch](2026-10-30-dialog-sizing-evidence/command-switch.png),
[Rename](2026-10-30-dialog-sizing-evidence/rename.png), and
[Text Entry](2026-10-30-dialog-sizing-evidence/text-entry.png).
