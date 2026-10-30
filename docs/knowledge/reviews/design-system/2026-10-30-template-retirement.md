# Message and Selection template retirement — 2026-10-30

The owner requested removal of the duplicate Message and Selection templates,
retention of the other templates, and Warning/Success shared Message previews.
Baseline: `d7d6746`. The [Gallery ledger](../../../plans/ui-gallery-coverage.md)
owns GAL-10 status; [GUI-30](../../../plans/custom-window-consolidation.md)
records the consolidation. The [dialog SPEC](../../../../lib/GUI/dialogs/SPEC.md)
owns current shared-dialog behavior.

Both template XAML files, their Gallery registrations, fixture data and
controllers are deleted. Form, Options and Review remain with their existing
interactions. Shared Message and Selection dialogs remain canonical. The old
Selection Markdown guide is only a retirement pointer, preserving historical
links without retaining an implementation. Shared component resources remain.

The shared Message Gallery entry now exposes Normal, Empty, Warning, Error,
Success, Disabled and Long content. Warning and Success use the actual dialog's
severity styling; other windows retain their five existing states. No production
tool call site or packaged DLL changed.

Verification:

- The new inventory/state tests failed against the prior implementation, then
  passed. Final Python suite: 383 tests, 382 pass and one existing skip.
- Actual IronPython/WPF: 43 catalog entries and 108 custom/state constructions;
  15 remaining template layouts and 47 shared-dialog layouts pass. The Gallery
  Message state dropdown includes Warning and Success, and their headings and
  severity brushes match the actual shared resources.
- Foundation checks now exercise the shared selector directly, preserving five
  state fixtures, shell/Close/native-row geometry, filtering, checked results,
  navigation and cancellation coverage.
- Production's 45 layouts, 18 icons, wordmark, scrollbars, 15 focus-style roles
  and actual Gallery column sorting pass. The earlier shown-focus fixtures also
  passed during this change; the final main probe ran offscreen.
- Gallery bundle/SPEC metadata and the documentation integrity audit pass;
  all local Markdown links resolve. Existing progressive-adoption advisories
  remain. `git diff --check` reports no whitespace errors.

[Warning preview](2026-10-30-template-retirement-evidence/dialog-message-warning.png)
and [Success preview](2026-10-30-template-retirement-evidence/dialog-message-success.png)
were rendered from the real shared Message dialog and visually inspected.

Live Revit ownership, physical input and DPI acceptance remain with the owner.
The Windows probes use fictional data and do not change a model.
