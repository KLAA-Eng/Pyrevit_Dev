# Generated XAML after the formatting pass — 2026-10-31

Baseline: `48119c2` ("xaml formatting"). That commit reformatted all 34 XAML
files, including the three outputs that
[generate_gui_icons.py](../../../../scripts/generate_gui_icons.py) owns:
`lib/_icons/gui/KLCodeIcons.xaml`, `lib/_logos/KLCodeWordmark.xaml` and the
`generated-icons` block in `lib/GUI/Resources/KLCodeFoundation.xaml`. The
generator's contract is byte equality, so after the reformat `--check` raised
(the `generated-icons:end` marker had gained comment padding), three
`gui_icons` tests and one `window_backgrounds` test failed, and no evidence
record existed after the commit. A canonical-XML comparison of all 34 files at
`44cee3e` and `48119c2` showed no semantic change, so the runtime was not
affected; the validation was. The
[design system guide](../../../DESIGNSYSTEM.md) owns the generator rule.

Changes:

- The three generated outputs are regenerated. The two generated files are byte
  for byte what `44cee3e` had; the Foundation block is too. The hand-written
  part of Foundation keeps the new formatting.
- The generator finds its markers through a tolerant pattern (comment padding,
  re-wrapped text) and always writes the canonical marker lines back, so a
  future formatting pass is repaired by running the generator instead of
  crashing it. A missing or inverted marker pair still raises.
- The two assertions on hand-written Foundation XAML that matched attribute
  text (the `KlaGuiIconPen` brush and thickness, the merged icon dictionary,
  the wordmark width and height) now parse the XAML or match one attribute at
  a time, so formatting cannot fail them.
- `scripts/release_check.py` runs `generate_gui_icons.py --check` as a gate.
- The guide says to keep XAML formatters off the generated files and block, and
  to regenerate after formatting the hand-written resources.

Verification (macOS, CPython 3.14):

- `python -B scripts/generate_gui_icons.py --check`: 22 roles and the wordmark
  verified.
- `python -B -m unittest discover -s tests -p "*_test.py"`: 422 tests, one
  failure (`carbon_gwp_command_test`, a case-insensitive path comparison that
  fails on macOS before and after this change).
- `python -B scripts/check_ui_scale.py`: 0 strict, 88 advisory, unchanged.
- `git diff --check`: clean.

Limits: the Windows WPF probes and the .NET smoke tests were not re-run here;
the last recorded Windows evidence is at `44cee3e`. The repository has no
formatter configuration, so the exclusion is a documented rule and a gate, not
a tool setting; XAML Styler has no per-file exclusion, so a formatting pass must
be given an explicit file list.
