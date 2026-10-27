# Custom-window foundation: first-delivery verification

Date: 2026-10-27. Baseline: `bad8c50` on `master-dev`, plus this delivery's
working changes. The owner confirmed the design and authorized the first
delivery: shared foundations and the main template/Gallery reference before
propagating it to other windows. The
[consolidation plan](../../../plans/custom-window-consolidation.md) owns status;
[DESIGNSYSTEM.md](../../../DESIGNSYSTEM.md#custom-window-foundation) owns rules.

## Result and source boundaries

The main template is now a 432 x 576 workflow body inside the reusable
`KlaWindowShell`. It no longer copies header/footer markup or brand geometry.
Explicitly named styles and typed WPF tokens supply typography, fixed button
roles, spacing, icons, and control states. The opt-in dictionary reuses existing
legacy palette/wordmark/scrollbar resources without editing their source.
Existing production Python/compiled windows and the Gallery catalog layout
are unchanged. The five compiled Gallery previews remain disabled.

`GUI.window_chrome.load_window()` preserves existing resources and DataContext,
does not show the window, and has no import-time CLR/pyRevit/document dependency.
It attaches close/drag/link behavior to named shell parts. Caller metadata owns
title and pure version; missing versions produce empty footer text. Gallery
passes its real `__version__`; footer navigation and selection outcomes remain
local simulations. No external navigation or model operation was performed.

The adapter uses the WPF template namescope through `ApplyTemplate`/`FindName`,
following [Microsoft's template-part guidance](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/controls/how-to-find-controltemplate-generated-elements?view=netframeworkdesktop-4.8).
Resource loading uses scoped merged dictionaries rather than application-global
changes; see [Microsoft's ResourceDictionary reference](https://learn.microsoft.com/dotnet/api/system.windows.resourcedictionary.mergeddictionaries).

## Rendered reference

These are actual WPF content renders at 432 x 576 and 96 DPI. No Window was
shown. Each is the initial fictional state, before exercising the actions.

| State | Evidence |
| --- | --- |
| Normal | [Reference render](2026-10-27-custom-window-foundation-evidence/main-template-normal.png) |
| Empty | [Empty render](2026-10-27-custom-window-foundation-evidence/main-template-empty.png) |
| Error | [Validation render](2026-10-27-custom-window-foundation-evidence/main-template-error.png) |
| Disabled | [Disabled render](2026-10-27-custom-window-foundation-evidence/main-template-disabled.png) |
| Long content | [Wrapped items and title ellipsis](2026-10-27-custom-window-foundation-evidence/main-template-long-content.png) |

All five were visually inspected. Header/footer are both 24 high, the existing
outlined wordmark is preserved, the title has no tooltip, and wrapped names
remain scrollable. The centered 104 x 28 pair with an 8-unit gap aligns with
the 216 x 32 main action. Main-action-to-footer clearance and body insets are
16. The list takes the remaining height rather than fixing itself at 360.

## Automated evidence

| Check | Result and limits |
| --- | --- |
| New `gui_window*test.py` boundary/metadata tests | 9 passed; resource/DataContext preservation, caller formatting, close, drag classification, simulated and ordinary link routing |
| Coverage of new Python helpers | 59 statements, 100% under CPython boundary tests; not a WPF/XAML or live-host coverage claim |
| Existing `ui_gallery*test.py` suite | 50 run: 49 passed, 1 skipped for unavailable symlink privilege |
| Production-window regressions | 17 passed across background/chrome, find/replace, and selection tests |
| Total focused unit checks | 76 run: 75 passed, 1 skipped |
| Isolated installed IronPython/WPF | Existing 35-entry Gallery, 66 custom/state constructions and Gallery filters/deferred selection passed |
| Additional foundation probe | Five reference states plus omitted-version specimen; actual bindings, measured layout, disabled label color, filter recovery, selection actions, simulated link event and routed Close passed |
| Gallery bundle metadata | Targeted `validate_bundle()` returned no errors; planned v0.5 remains Unreleased |

Reproduce unit checks with Python unittest discovery in `tests`, using patterns
`gui_window*test.py`, `ui_gallery*test.py`, `window_backgrounds_test.py`,
`find_replace_window_test.py`, and `select_from_dict_selection_test.py`.
Coverage command:

```powershell
python -B -m coverage run --data-file=.coverage.ui-foundation --source=GUI.window_metadata,GUI.window_chrome -m unittest discover -s tests -p 'gui_window*test.py'
python -B -m coverage report --data-file=.coverage.ui-foundation -m
```

Real-WPF probe, using installed IronPython 2.7.12 / .NET Framework WPF and the
existing minimal pyRevit loader/alert stand-in:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./scripts/validate_ui_gallery_wpf.ps1 -OutputDirectory "$env:TEMP/ui-foundation-review"
```

The execution-policy override is process-only. The foundation companion script
runs inside that probe. Its output:

```text
Foundation: five states, real shell geometry/bindings, caller identity, simulated actions/navigation, and close event passed.
IronPython 2.7.12: 35 catalog entries; 66 real-WPF custom/state constructions; Gallery filters/deferred selection passed.
No window was shown. Native dialogs and pyRevit/Revit integration remain host checks.
```

Calculated sRGB text contrast for the new roles: footer link 8.18:1, muted
text 8.50:1, disabled button text 5.11:1, normal button text 7.35:1, hover button
text 5.71:1. These concern the specified color pairs, not complete accessibility
acceptance or high-contrast mode.

## Review and remaining acceptance

Independent static review found a disabled-label inheritance issue: the merged
legacy TextBlock style overrode inherited checkbox foreground. The wrapping
label template is now shared and explicitly binds to its checkbox foreground.
The reviewer confirmed the fix, and the real-WPF probe verifies the actual
disabled label color. No further material findings remained.

The Revit bridge health request timed out after 10 seconds during this delivery.
No live Revit UI was exercised. Actual keyboard focus/traversal, hover/pressed
input, drag, owner/lifetime behavior, external footer navigation, Narrator,
high contrast, work-area fitting, and DPI/mixed-monitor behavior remain live
acceptance work. Programmatic routed events and static trigger inspection do
not prove those behaviors. The owner still needs to review the reference's
appearance before migration of other windows or selection of replacement icons.
