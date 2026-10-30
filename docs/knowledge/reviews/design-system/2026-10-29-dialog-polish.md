# Shared dialog spacing and focus polish — 2026-10-29

Owner request: refine Text spacing/actions, match shared selectors to the
Selection template, add an aligned group icon, remove Command Switch's corner
x/initial search focus, and remove persistent white click-focus marks globally.
Baseline: `fd45566` on `dev.GUI-Clean`. The
[consolidation plan](../../../plans/custom-window-consolidation.md) owns GUI-27/28;
[dialog SPEC](../../../../lib/GUI/dialogs/SPEC.md) and
[design system](../../../DESIGNSYSTEM.md) own the current contracts.
The [prior refinement](2026-10-29-dialog-refinement.md) remains historical.
Implementation/verification began on October 29; the milestone was completed
on October 30, 2026.

## Result

- Text has 8-unit prompt/input and input-or-validation/OK gaps. Content-driven
  minimum height removes the former stretched blank space. Cancel is removed;
  title Close/Escape still cancels. The 36-high/FontSize 24 Segoe UI Bold field,
  inline validation, default-text selection and footer opt-out remain.
- All five selector presets open at 432 x 576, matching the template, while
  retaining a 432 x 420 resizable minimum. Search precedes optional Group. Both
  fields are 24 high and align after 16-unit icons plus an 8-unit column gap.
  The 8/4/8 section gaps and centered batch/main button arrangement follow the
  template. Select All/None retain the current gray secondary style, with an
  8-unit gap above green Select. No Cancel row; Close/Escape still cancels.
  Counts/validation, hidden checks, eligibility and explicit Select are retained.
- Command Switch has no corner x or reserved corner inset. Initial focus is
  the neutral panel; typing or Tab can enter search. Existing filtering, toggle
  state, immediate command choice, Escape-clear-then-cancel and blank-click
  behavior remain. Initial Enter on the neutral panel does not choose a command.
- Common button/check/radio/toggle families no longer embed white focus
  underlines or square-border overrides reacting to IsKeyboardFocused. Their
  keyboard-navigation adorner is green, decorative and outside layout. New
  roles are KlaKeyboardFocusBrush (#91C8A6) and KlaKeyboardFocusInset (-2).
  Inputs/dropdowns keep the existing field-focus outlines; footer colors,
  checked/hover/disabled states, native list templates and dimensions remain.

The global change is in shared source resources used by Python and compiled
hosts. Packaged compiled DLLs are not replaced; rebuild/deploy is needed for
those consumers. No production tool call sites, model operations or Action
choice-specific layout/controller behavior changed. The reference Selection
template is unchanged apart from consuming the global focus styles.

## Group icon and licensing

The new semantic Group role uses [Lucide Layers-2](https://lucide.dev/icons/layers-2),
matching the existing outline family. Its
[SVG at the already-pinned revision](https://github.com/lucide-icons/lucide/blob/be09619c1c1124ad09c19fc3e87ee3b939409bbd/icons/layers-2.svg)
was verified against the source after newline normalization. The retained
Lucide ISC notice covers it. Two path primitives need no converter/runtime
dependency changes. Source SVG, manifest, semantic map and icon catalog are
updated; the generator writes KlaGroupGeometry/KlaIconGroup. The catalog now
has 18 roles on the same 24-unit canvas, rendered at 16 with 1.5 stroke.

## Verification

| Check | Evidence |
| --- | --- |
| Complete Python suite | 383 run; 382 pass and one existing symlink-related skip |
| Focus contracts | Three new tests, established failing before the focus fix; inherited focus styles, decorative/non-input adorner and retained field-focus policy pass |
| Default real IronPython/WPF probe | 45 Gallery entries, 116 custom/state constructions, 45 shared-dialog states at normal/minimum size; prior templates/production/Gallery sorting/filter regressions pass |
| New geometry checks | Exact 8-unit Text gaps, no Cancel, selector initial 432 x 576, fields 24 high with matching left edges/order, aligned batch/main buttons, gray secondary fill and 8-unit footer gap |
| Actual focus resource probe | 15 button/check/radio/toggle style roles resolve green keyboard-only decoration, omit embedded FocusMark/ToggleFocus and preserve checkbox/input roles |
| Opt-in shown-window focus | Two owned fictional windows opened/closed. UIA confirms Edit / Filter commands; actual logical/keyboard focus initially stays on neutral panel, search selection is zero; programmatically focused command/checkbox retains ordinary border without white overrides |
| Compiled WPF | 17 C# source tests and seven actual instances across five classes pass on each of net48 and net8.0-windows |
| Generated artwork / spacing | 18 roles and exact wordmark generation pass; zero strict violations, 85 unchanged advisory consumer literals |
| Independent review | No blocking defect found in layout, sizing, initial focus, cancellation/state or shared-focus isolation; reviewer independently ran 10 dialog-model and seven switch tests |
| Documentation | Deterministic integrity audit passed; local Markdown links resolve. Existing progressive-adoption role/ADR/test-registry warnings remain advisory. |

Run standard checks from [DESIGNSYSTEM.md](../../../DESIGNSYSTEM.md#validation).
The default Windows probe remains offscreen. For the additional owned-window
acceptance used here:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate_ui_gallery_wpf.ps1 -ShowFocusProbe -OutputDirectory <tmp>
```

The shown probe inspects the actual UIA role/name and uses framework focus
within its own process. No system-wide input is injected and no Revit/user
document is used. An initial setup check used the wrong FocusManager namespace,
then a role-string expectation was corrected from ControlType.Edit to Edit;
the corrected committed probe passes. No fixture is left open on failure.

WPF's keyboard-initiated FocusVisualStyle is appropriate here because
IsKeyboardFocused triggers also react to pointer/programmatic focus; see
[Microsoft's focus-style reference](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/advanced/styling-for-focus-in-controls-and-focusvisualstyle).
This is source/framework verification, not a claim that physical Tab/mouse
routing or every Revit host/DPI configuration was exercised.

## Inspected renders

| Surface | Render |
| --- | --- |
| Text | [Normal](2026-10-29-dialog-polish-evidence/dialog-text-normal.png), [validation](2026-10-29-dialog-polish-evidence/dialog-text-error.png) |
| Grouped sheets | [Template-sized layout](2026-10-29-dialog-polish-evidence/dialog-sheets-normal.png), [minimum size](2026-10-29-dialog-polish-evidence/dialog-sheets-minimum.png) |
| Single selection | [Checkbox variant](2026-10-29-dialog-polish-evidence/dialog-list-single-normal.png) |
| Command Switch | [No x / neutral initial state](2026-10-29-dialog-polish-evidence/dialog-command-switch-normal.png), [minimum width](2026-10-29-dialog-polish-evidence/dialog-command-switch-minimum.png) |
| Icon catalog | [All 18 native GUI roles](2026-10-29-dialog-polish-evidence/gui-icons-18-native.png) |

Live Revit owner/modal/keyboard/pointer/DPI and model-data acceptance remain
owner-owned. GUI-08, GUI-14 and deferred Action choice redesign GUI-22 are not
closed by this polish. Roll back source resources, generated icon outputs,
dialog bodies/controllers, probes and documentation together if required.
