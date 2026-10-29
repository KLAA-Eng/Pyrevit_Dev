# GUI architecture Windows verification

Verified 2026-10-29 on `dev.GUI-Clean`, starting from clean baseline `28d5b29`
(the handoff following `7e01901`). This record closes the source/render portion
of the [Windows handoff](../../gui-architecture-review-handoff.md).
The [consolidation plan](../../../plans/custom-window-consolidation.md) owns
current task status. The owner will perform the actual Revit review.

## Changes and findings

The initial Windows probes failed before completing. The fixes are:

- `KLCodeChrome.xaml` now resolves `System.Uri` from `System`, retaining
  `mscorlib` for strings. The old URI namespace prevented loose XAML loading.
  [Microsoft's URI reference](https://learn.microsoft.com/en-us/dotnet/api/system.uri?view=netframework-4.8)
  identifies the .NET Framework assembly; both compiled runtime smokes also pass.
- Palette and compiled-name aliases now use `SolidColorBrush` with a binding to
  the canonical role's `Color`. Element-form `StaticResource` aliases did not
  survive compiled resource lookup: Startup Importer failed on
  `KlaSubtleTextBrush`, then template `BorderBrush` resolution. The replacement
  preserves keys and one source for each color; loose and compiled WPF pass.
- Startup Importer's two Browse buttons use the existing `KlaButtonStyle`.
  They referenced the removed `KlaSmallButtonStyle`, preventing construction.
- Close uses a 0.3-unit bottom inset rather than 2. At the measured 96-DPI
  layout its visible glyph center is (30.00, 9.15), within the existing
  0.25-unit tolerance of the button center (30, 9). The probe now reports
  actual coordinates on failure. A token read before assignment and obsolete
  green-footer assertions were also corrected in the probe.
- Generated wordmark geometry now preserves SVG coordinates and supplies a
  separate drawing transform. Moving the translation into `PathGeometry`
  changed WPF rasterization. The production probe now compares all 840 pixels
  against the former inline SVG-path renderer: exact match.

Handoff item 25 is implemented through shared `ItemsControl` Grid panels:
`KlaFieldRows` replaces seven naming layouts (Form, Find/Replace Views, two
Find/Replace Sheets groups, three Duplicate Sheets groups), and
`KlaFilteredCheckList` replaces four list layouts (Selection reference,
SelectFromDict, Create From Rooms, Steel PSF). Named controls, label targets,
bindings and handlers remain declared in the window namescope. Steel PSF keeps
both secondary action rows in its secondary-actions item. All measured field
sizes, gaps, action placement and state interactions pass.

Handoff item 31 is implemented: Gallery loads through `load_window`, uses the
shared shell/table/dropdowns/buttons and no longer copies chrome or control
templates. The background tests now enforce its shared shell. PreviewFixture
retains its standalone test chrome. Five compiled Gallery entries stay deferred.

## Verification

Environment: Windows, CPython 3.14, installed pyRevit
`6.5.3.26176+2017`, IronPython 2.7.12, .NET SDK 10.0.402. The inspected installed
`forms/_ipy.py` exposes
`load_xaml(self, xaml_source, literal_string=False, handle_esc=True, set_owner=True)`;
this confirms the adapter's positional call against installed source. Real
ownership, host initialization and View Range's production subclass still need
the owner's live review.

| Check | Result |
| --- | --- |
| `python -B scripts/generate_gui_icons.py --check` | Pass: 17 icon roles and wordmark current |
| `python -B scripts/check_ui_scale.py` | Pass: zero strict violations; 85 advisory consumer literals, down from 98 |
| `python -B -m unittest discover -s tests -p "*test.py"` | 351 run: 350 passed, one symlink-creation test skipped on this host |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate_ui_gallery_wpf.ps1 -OutputDirectory <tmp>` | Pass: 36 entries, 71 custom/state constructions, Gallery filtering/deferred selection, five foundation states, 25 template layouts, 45 production layouts, localized Recall captions and icons |
| Additional WPF regressions in that probe | Pass: both scrollbar orientations, thumb geometry, both overflow ranges, exact wordmark pixels |
| `dotnet test src/KLCode.Wpf/Tests/KLCode.Wpf.Source.Tests --no-restore` | 17 passed |
| `dotnet run --project src/KLCode.Wpf/Tests/KLCode.Wpf.Desktop.Smoke --framework net48 --no-restore -- <tmp>` | Pass: seven instances across all five actual compiled classes |
| Same desktop smoke with `--framework net8.0-windows` | Pass: seven instances across all five actual compiled classes |
| Compiled smoke regression assertions | Pass: brush alias colors, localized Close/footer labels, typed footer URIs, existing chrome/action geometry |
| Focused metadata validation | Pass: Gallery, Steel PSF, Startup Importer, Duplicate Sheets, Find/Replace Views and Sheets |

The full metadata scan still reports the pre-existing cache-only Model Checker
directory's missing `bundle.yaml`; that unrelated directory was left alone.
Source/diff self-review was performed; no independent reviewer was used.
The smokes construct actual UI classes with fictional providers and render their
content without showing windows. They do not certify packaged Revit DLLs or
real model/database/import operations; packaged assets were not replaced.

## Render evidence

Selected current PNGs are in
[the evidence folder](2026-10-29-gui-architecture-windows-evidence/).
Inspected examples:

- Gallery [normal](2026-10-29-gui-architecture-windows-evidence/gallery-1060.png),
  [narrow](2026-10-29-gui-architecture-windows-evidence/gallery-900.png),
  [deferred](2026-10-29-gui-architecture-windows-evidence/gallery-deferred.png).
- [Form](2026-10-29-gui-architecture-windows-evidence/template-form-normal.png),
  [Duplicate Sheets](2026-10-29-gui-architecture-windows-evidence/production-kla-duplicate-sheets-normal.png),
  [Find/Replace Sheets](2026-10-29-gui-architecture-windows-evidence/production-kla-find-replace-sheets-normal.png),
  [Steel PSF](2026-10-29-gui-architecture-windows-evidence/production-kla-steel-psf-normal.png).
- [Family Studio](2026-10-29-gui-architecture-windows-evidence/compiled-family-studio.png)
  and [Startup source picker](2026-10-29-gui-architecture-windows-evidence/compiled-source-picker.png),
  including the toolbar segments, single search outline and outlined Cancel.
- [Close at 4x](2026-10-29-gui-architecture-windows-evidence/close-control-4x.png)
  and [horizontal/vertical overflow](2026-10-29-gui-architecture-windows-evidence/scrollbars-overflow.png).

## Owner's live Revit checklist

1. Open Gallery, exercise filters and available previews, and verify the five
   compiled entries remain deferred. Open Family Studio and Startup Importer
   from their own commands for actual compiled-host review.
2. Check body-first Tab order, visible focus, Enter/default actions, Escape and
   header Close, including Create From Rooms cancellation. Confirm real tool
   footer versions and footer navigation.
3. Check ownership/modality, header drag, monitor/work-area placement and DPI.
   Exercise long lists and both scroll directions where content overflows.
4. Open the actual Show View Range command; resize using its grip, verify
   Apply/Reset and event cleanup after closing/reopening. Gallery's safe preview
   does not execute that production subclass.
5. Exercise representative real workflows in a disposable Revit fixture before
   promotion. Record host/version and outcomes under GUI-08; isolated renders
   do not establish transaction behavior or accessibility acceptance.

Handoff item 35: existing commits, including `bd79fb9`, were retained; no shared
history rewrite was performed. Item 39: CustomAlert and CreateFromRooms remain
available as library/Gallery windows pending an owner decision about retirement
or a production caller. Neither is silently deleted or wired to a new command.
The remaining off-scale consumer literals are advisory, not newly classified
defects. No extension/tool version or release/publication action is included.
