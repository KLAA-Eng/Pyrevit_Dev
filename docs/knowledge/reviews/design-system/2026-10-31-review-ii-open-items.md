# Review II open items, first batch — 2026-10-31

Baseline: `40bbc85` (the generator fix after `48119c2`). This batch takes the
open items of the private KLCode GUI Review II that can be fixed and checked
without a Windows host: pure-model defects, adapter guards, dead resources,
documentation drift and the keyboard contract. Owner decisions (GUI-15,
GUI-29, AC-004, AC-005) are not changed; they are now written into the
[design system guide](../../../DESIGNSYSTEM.md) as accepted deviations with the
WCAG criteria they touch, beside a dialog-by-dialog keyboard table. The
[shared SPEC](../../../../lib/GUI/dialogs/SPEC.md) and the
[consolidation plan](../../../plans/custom-window-consolidation.md) keep the
behavior and status.

Changes (Review II item in brackets):

- Sheets sort by number, not text: `S2` before `S10`, digit runs as numbers,
  the rest case-insensitively (SPEC AC-008) [A19].
- `create_sheet_selector(all_label=…)` no longer raises; `None` descriptions on
  selection items and action choices become empty strings, so filtering and
  search never fail on a caller's `None` [A25].
- The selector ignores Enter only from the list and the filter; a focused
  button (Select, Close), the group dropdown and the footer links keep their
  own Enter [A1].
- KLC-Rename's window-level Enter no longer hijacks a focused Uppercase or
  Lowercase button; Enter and Space on a button now do the same thing [N4].
- Text entry follows its content height until the user resizes with the grip;
  a resized window keeps its height unless the content no longer fits [A11].
- `load_window` uses the same `pyrevit.framework.wpf` fallback as the
  adapters, so the fallback is no longer dead for the four shell dialogs [A12].
- The Message severity icon carries the severity word as its automation name
  [A10].
- Command Switch: `pointer_down` and `on_key_down` ignore input after close;
  an outside click is judged against the visible panel, so the 16-unit
  transparent margin counts as outside [N12].
- The dead `KlaFocusMarkHeight` and `KlaFocusMarkInset` tokens are removed;
  nothing consumed them [A20].
- The Gallery tooltip shows one planned-version summary dated 10.30.2026
  (TOOL_VERSIONING) and no longer tells users to review Form; the SPEC row
  carries the same date [A17].
- Records: the shared-window-variants record says which same-day records
  supersede its 24/18 and 384/712/1040 figures; the plan's 24/18 paragraph
  points to the 32/22 polish; GUI-20's "40 entries" is dated; the Gallery SPEC
  names Options and Review as the retained references and 22 icon roles; the
  guide lists Action Choice among the footerless dialogs and Text among the
  blank-title ones [A26, A27, N7].

Not changed, by design or for lack of a host: the selector migration order
(A16), the Command Switch shadow and strict-lint membership (A4, A6, A7),
toggle-pill and disabled-text contrast (A8, A9), owner defaults (A13), the
`is_cancelled` contract for `close` (N5), the Closing veto scope (N6), the
window-local Details and command-link templates (N8), the blank-Rename rule
(N9), the dormant `_future` windows (N13) and Gallery owners (A28).

Verification (macOS, CPython 3.14):

- `python -B -m unittest discover -s tests -p "*_test.py"`: 425 tests, one
  failure (`carbon_gwp_command_test`, the existing macOS path-case comparison).
  Three tests added: numeric sheet sort, `None` descriptions, `all_label`
  override.
- `scripts/generate_gui_icons.py --check`, `scripts/check_ui_scale.py`
  (0 strict, 88 advisory, unchanged), `git diff --check`: clean.
- `scripts/check_tool_metadata.py`: the Gallery bundle passes; the two
  existing errors are the stray `Family Studio.invokebutton` and
  `Carbon GWP Pull.pushbutton` folders without a bundle.

Limits: the four adapter changes (selector Enter, Rename Enter, Text height,
Switch bounds) touch WPF routing and layout and were not rendered or driven
here. Run `validate_ui_dialogs_wpf.py`, `validate_ui_rename_wpf.py`,
`validate_ui_input_alignment_wpf.py` and
`validate_ui_command_switch_pointer_wpf.py` on Windows before relying on them,
and add a shown-window check that Enter on a focused Rename case button acts
once.
