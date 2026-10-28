# Message reference and Form prompt refinement

Date: 2026-10-28. Baseline: `70ec1c7`, plus this refinement on `dev.GUI-Clean`.
The [active plan](../../../plans/custom-window-consolidation.md) owns acceptance
decisions and interview progress. The owner requested matching Form's heading to
Selection's Select Elements prompt, and accepted all three Message recommendations.

Form now reuses `KlaFoundationPromptLabel` directly: Segoe UI 14, normal weight,
zero padding and the same foreground. Compact field geometry stays unchanged.

Message grows from a compact size with its content, up to a cap, then scrolls.
Details starts collapsed in every state, including Error; severity changes retain
the user's expansion choice. Heading/body text colors stay consistent. Heading
wording and the banner border distinguish severity. No new icons were selected.

The reference defaults to 288 minimum/640 maximum height. Its natural long
fixture fits at 611. Expanded Details adds its readout height and margins to
the minimum (424) to preserve the message viewport and action at narrow sizes.
These numerical limits are review defaults, not a new limit on all windows.

`GUI.window_chrome.fit_window_height` measures a chromeless shared shell at its
current width, rounds desired height up and clamps to caller limits. The Message
presenter invokes it after content/width changes and after Details template
visibility settles on the dispatcher. It has a recursion guard and no show,
model or file side effects. Production windows remain unchanged.

| Case | Actual isolated WPF render |
| --- | --- |
| Form prompt | [Normal Form](2026-10-28-template-family-evidence/template-form-prompt-normal.png) |
| Compact Message | [Normal](2026-10-28-template-family-evidence/template-message-refined-normal.png) |
| Error, Details closed | [Error](2026-10-28-template-family-evidence/template-message-refined-error.png) |
| User-opened Details | [Expanded](2026-10-28-template-family-evidence/template-message-refined-expanded.png) |
| Height cap and scrolling | [Oversized stress content](2026-10-28-template-family-evidence/template-message-refined-overflow.png) |

Verification:

- The changed Error/Long-content collapsed-details test failed against the
  previous auto-expansion behavior, then passed after implementation.
- Gallery: 63 run, 62 passed, 1 skipped for unavailable symlink privilege.
  Shared GUI: 10 passed, including content-height rounding and min/max clamps.
- Installed IronPython 2.7.12/WPF: all 25 template states, normal-state actions,
  minimum sizes, 36-entry catalog and 71 custom/state constructions passed.
- All Message states initially collapse Details. Short content stays compact;
  the natural long sample grows to 611. A fourfold long-content stress fixture
  reaches 640, has actual overflow and moves its scroll offset to the end.
- Expanding/collapsing Details grows/shrinks height, preserves expansion on
  severity changes, and renders the full 128-high readout. Width refitting,
  stable text colors, warning border and action/footer clearance pass.
- Form resolves the exact same prompt style, size 14 and normal weight. All
  established compact fields and gaps still pass. Normal, expanded, error,
  overflow and minimum-size renders were inspected.

Reproduce with the Gallery test command and isolated WPF probe documented in
the [family evidence](2026-10-28-template-family.md#verification). No Window was
shown. Live pyRevit ownership, actual input/resize events, accessibility and DPI
acceptance remain pending. The stress image extends the ordinary Long content
fixture to exercise the cap; normal Gallery Long content retains its fixture.
