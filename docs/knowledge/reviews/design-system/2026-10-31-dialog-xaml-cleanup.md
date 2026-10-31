# Shared dialog XAML cleanup — 2026-10-31

Baseline: `3d7e687`. The owner approved a XAML cleanup with no intended visual
change (consolidation plan GUI-42; Review II items N8, A4, A7, A22). The
[design system guide](../../../DESIGNSYSTEM.md) lists the new styles and tokens.

Changes:

- The Details disclosure that Message and Action Choice each defined in their
  own window resources is one pair of shared styles, `KlaDetailsExpander` and
  `KlaDetailsToggle`, in Components. The two local toggles differed only in
  foreground; the shared toggle takes the Expander's foreground, which is the
  Message body colour in Message and `KlaMutedBrush` in Action Choice, as
  before. Template part names `DetailsToggle`, `DetailsChevron` and
  `DetailsContent` are unchanged for code and probes.
- Message's body-aligned readout is `KlaDetailsReadout`, and Action Choice's
  command link is `KlaCommandLink` with `KlaCommandArrowGeometry`, both in
  Components. Neither dialog keeps window resources.
- New typed tokens replace every numeric layout literal in the six shared
  dialog bodies except their window sizes: stack gaps, the icon-text gap, the
  optical 2-unit inset, the floating margin and radius, command-link sizes,
  severity icon and heading sizes, the Details height, option maximum height,
  the Rename label column and the switch prompt width. Rename's row grid uses
  the existing compact field tokens. Action Choice's button grid and the
  selector's feedback spacing read tokens in code instead of literals.
- `KLCodeCommandSwitch.xaml` is in `check_ui_scale.STRICT`; its toggle track,
  thumb and column sizes are tokens local to that dictionary.
- The Command Switch window uses the new `KlaFloatingWindow` style, based on
  `KlaFoundationWindow` with a transparent background and no taskbar entry,
  instead of re-declaring font, foreground and window flags. It now also gets
  the foundation's layout rounding and pixel snapping.

Expected visual change: none, except that layout rounding on the Command
Switch can move its edges by under one device pixel.

Verification (macOS):

- Every edited XAML file parses; the shared dialog bodies have no numeric
  layout literal outside their window sizes.
- Python suite: 431 tests, one existing macOS path-case failure.
- `check_ui_scale.py`: 0 strict (now three strict files), 62 advisory.
- C# source-contract tests: 17 of 17 pass (`dotnet test`, net8.0).

Limits: nothing was rendered. Before relying on this, run on Windows
`validate_ui_dialogs_wpf.py`, `validate_ui_message_variants_wpf.py`,
`validate_ui_action_choice_wpf.py`, `validate_ui_rename_wpf.py`,
`validate_ui_command_switch_pointer_wpf.py` and
`validate_ui_gallery_wpf.ps1`, and compare the renders with the 2026-10-30
evidence folders. Any pixel difference beyond the switch's rounding is a
defect of this change.
