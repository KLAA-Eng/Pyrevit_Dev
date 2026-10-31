# Review II decisions and behaviour batch — 2026-10-31

Baseline: `105a4aa`. The owner answered the open items of the private KLCode
GUI Review II in one interview round. The
[consolidation plan](../../../plans/custom-window-consolidation.md) records the
decisions as GUI-42 and this batch as GUI-43; the
[shared SPEC](../../../../lib/GUI/dialogs/SPEC.md) and the
[design system guide](../../../DESIGNSYSTEM.md) own the resulting behaviour.

Decisions (Review II item in brackets):

- The shared selector migration waits for live Revit acceptance (GUI-08);
  SelectFromDict stays the shipped selector [A16].
- `lib/GUI/_future/` is a waiting room for dormant windows, outside the scale
  lint [N13].
- The Gallery owns its previews [A28, A13].
- `is_cancelled` is true for `close` as well as `cancel` [N5].
- With cancellation disabled, a close from code, the owner or the system always
  proceeds as `close` [N6].
- An unknown Action Choice default fails when the dialog is built; a disabled
  one still falls back [N10].
- An entirely blank Rename is rejected [N9].
- The Command Switch status line is removed [A24].
- Prompts and field labels carry no trailing colon [A23].
- Disabled controls signalled by their gray, and role brushes that share a
  value, are by design [A9, A21].
- The Text watermark and the Command Switch search hint share one placeholder
  token whose value is the footer version gray [N11].
- Still to come, already decided: the XAML cleanup with no visual change
  [N8, A4, A7, A22] and candidates for the switch edge and toggle pill, picked
  in the design system artifact before any XAML changes [A6, A8].

Changes in this batch:

- `DialogResult.is_cancelled` covers `close`. `ChoiceState` raises for an
  unknown default and gains `forced_close()`. The Action Choice window blocks
  Alt+F4 itself when cancellation is disabled, so its Closing handler no longer
  vetoes: any close that arrives there proceeds.
- `WindowChrome.detach_escape()` replaces Action Choice's use of the private
  handler.
- `RenameState.rename_result()` rejects a request with no rule in any field:
  "Enter at least one rename rule.".
- The Command Switch status line and its Gallery-only Error feedback are
  removed; the switch row offers Normal, Empty, Disabled and Long content.
- `launch_custom` takes an owner; the Gallery passes itself, so every custom
  preview is owned and centred on it. The Gallery tooltip and SPEC row move to
  10.31.2026.
- SelectFromDict's default prompt is "Select Elements" and it strips a trailing
  colon from any caller's prompt, so ten existing tool prompts lose their colon
  without a tool script change.
- KLC-Rename's field labels read Find, Replace, Prefix and Suffix without a
  colon (added after the XAML cleanup). Four shipped tool windows still write
  colon labels: Core Find and Replace Views and Sheets, Duplicate Sheets and
  Steel PSF. Changing them is a user-visible tool change left to the owner.
- Message's OK sets `IsDefault` in XAML instead of code.
- `KlaPlaceholderBrush` (#808080) is added to the palette; the Text watermark
  and the switch search hint use it, and a test keeps it equal to
  `KlaFooterVersionBrush`. The switch hint moves from #B5C2BD to #808080.
- `check_ui_scale.py` skips `_future/`; `_future/README.md` says why.
- The Gallery handler-accounting test now covers key, selection and pointer
  events [A18]. The guide's ghost-button row no longer assigns Cancel [A15].
  The old architecture handoff says it is a superseded snapshot [A27].
- The two untracked DevSandbox folders that held only a `.DS_Store` file and
  compiled caches are deleted; the metadata audit is clean.

Accepted deviations added to the guide: the placeholder gray is 3.96:1 on the
window, which passes for the 24-unit bold watermark and is below 4.5:1 for the
12-unit switch hint; disabled controls rely on the gray and their automation
state.

Verification (macOS, CPython 3.14):

- Full suite: 431 tests, one failure (`carbon_gwp_command_test`, the existing
  macOS path-case comparison). New tests: unknown defaults, forced close,
  close counted as cancelled, blank Rename, switch states, Escape detach,
  placeholder token.
- `check_tool_metadata.py`: 34 bundles, 0 errors. `check_ui_scale.py`:
  0 strict, 65 advisory (88 before; 23 were under `_future/`).
  `generate_gui_icons.py --check` and `git diff --check`: clean.

Limits: nothing here was rendered or driven in WPF. The Windows probes were
updated for the new behaviour and must be run before relying on it:
`validate_ui_action_choice_wpf.py` (host close now proceeds as `close`),
`validate_ui_rename_wpf.py` (blank request rejected),
`validate_ui_shown_focus_wpf.py` (placeholder token), `validate_ui_dialogs_wpf.py`
and `validate_ui_gallery_wpf.py` (switch states, owned previews). Alt+F4 cannot
be simulated by the probes; check it by hand on a trapped Action Choice.
