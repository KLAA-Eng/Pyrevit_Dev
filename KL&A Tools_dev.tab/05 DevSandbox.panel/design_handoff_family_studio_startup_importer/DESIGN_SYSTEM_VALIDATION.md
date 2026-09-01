# KLCode compiled-WPF design-system validation

## Checkpoint 1 decision record

- Plan/version: `00_design_system_implementation_plan.md` at evidence commit
  `e856ca3`.
- Decision owner: KL&A engineering, initiated by the repository owner on
  2026-08-31 for this source checkpoint.
- Execution boundary: source-level proof in this macOS worktree; Windows/Revit
  launch evidence remains required.
- Compatibility decision: keep the legacy IronPython-only
  `WPF_styles.xaml` control templates intact and expose a compiled-safe adapter.
  The canonical brush tokens move to `KLCode_palette.xaml`, which the legacy
  dictionary and the compiled `KLCode.Wpf` project both consume.
- Reason: the legacy `Header` template contains `Click="button_close"` and
  hard-coded copy. A compiled resource dictionary cannot own that IronPython
  event target, and compiled feature windows must source copy from locale
  dictionaries.
- Locale inventory: `en_us`, `ko`, `fr_fr`, `ru`, `chinese_s`, `es_es`,
  `de_de`, and `pt_br`. Only the approved English smoke copy exists in this
  checkpoint; every other locale explicitly uses the English fallback until
  owner-supplied translations are approved.
- Font decision: Audiowide is omitted. Distribution/license approval is still
  required before the handoff font can enter a compiled assembly.

Options considered:

1. Remove the IronPython event from the legacy `Header` template. Rejected for
   this checkpoint because existing Python windows own that handler contract.
2. Copy palette values into compiled resources. Rejected because two token
   sources would drift.
3. Extract one data-only palette and add a compiled adapter. Selected because
   it preserves existing windows, gives both C# tools one dependency, and is
   reversible without changing Core behavior.

The tradeoff is one host-specific adapter binary per Revit runtime:
`KLCode.Wpf_2024.dll` for Revit 2024 and `KLCode.Wpf.dll` for Revit 2025+.
Packaging must preserve and verify both. Reconsider this boundary if the legacy
header becomes compiled-safe and localized, or if pyRevit adopts a proven
host-specific dependency probing layout that removes the shared-bin collision.

## Compiled adapter boundary

The compiled adapter owns only behavior and control composition. It references
the canonical palette keys and does not duplicate color values. The legacy
`Header` style is intentionally not exposed to compiled consumers. The smoke
window is the live proof surface for header drag and Close behavior; its
compiled handlers and English resource bindings pass the source/build gates,
while live interaction remains a Windows/Revit gate.

The DevSandbox `Design System Smoke.invokebutton` is the explicit Revit launch
surface. Family Studio packaging copies the matching command assembly and
adapter dependency into that bundle as well as the Family Studio bundle.

Required canonical keys:

- `header_background`, `text_white`, `text_gray`, `text_green`
- `button_fg_normal`, `button_bg_normal`, `button_bg_hover`
- `border_green_dark`, `border_green`
- `uncheckbox_checked_colour`, `checkbox_checked_colour`, `footer_donate`

## Visual and host QA matrix

| Surface | Exact size | Source gate | Revit 2024 | Revit 2025+ | Visual/focus/high-DPI |
| --- | ---: | --- | --- | --- | --- |
| Design-system smoke | 440 x 240 | Required resource/static-copy tests | Unavailable on macOS | Unavailable on macOS | Unavailable on macOS |
| Family Studio FS-1 | 1180 x 740 | Pending feature checkpoint | Pending | Pending | Pending |
| Startup Importer SI-1 | 760 x 540 | Pending feature checkpoint | Pending | Pending | Pending |
| Startup Importer SI-2/SI-3 | Per handoff | Pending feature checkpoint | Pending | Pending | Pending |

Windows acceptance must confirm parser/load success, every required key,
header drag, Close, clipping, keyboard focus order, disabled states, 100% and
high-DPI rendering, and packaging from both consuming projects. Commands remain
in DevSandbox until those gates pass.
