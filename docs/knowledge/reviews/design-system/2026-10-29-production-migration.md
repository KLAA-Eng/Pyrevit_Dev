# Approved icons and production window migration

Verified 2026-10-28–29 on `dev.GUI-Clean`, against pre-migration baseline
`1815048`. The owner approved the Lucide choices and production migration.
The interrupted implementation was saved in `bd79fb9`; the final follow-up
corrects the remaining layouts and records verification. The
[consolidation plan](../../../plans/custom-window-consolidation.md) owns task
status; [DESIGNSYSTEM.md](../../../DESIGNSYSTEM.md) owns current design rules.

## Delivered source

All nine Python tool windows and five compiled window classes now compose the
shared shell and components. Header/footer are 24 units; common fonts, fields,
button roles, footer identity and state treatments live in canonical resources.
Window bodies retain their tool-specific arrangements and operations. This
migration does not claim that every specialized body property is now a token.

The source owner for the 17 approved icon roles is
[lib/_icons/gui](../../../../lib/_icons/gui/README.md): original SVGs, pinned
revision, license notices and generated native WPF geometry/ImageSources.
Normal presenters are 16 units, with 1.5 stroke on a 24-unit canvas, inherited
foreground and disabled state. Generation preserves full canvas bounds, including
for DrawingImages. No SVG runtime dependency or network access is required.

| Python window | Source | Normal render |
| --- | --- | --- |
| KL&A List Selection | [SelectFromDict.xaml](../../../../lib/GUI/SelectFromDict.xaml) | [Render](2026-10-28-production-migration-evidence/production-kla-select-from-dict-normal.png) |
| Create From Rooms | [CreateFromRooms.xaml](../../../../lib/GUI/Tools/CreateFromRooms.xaml) | [Render](2026-10-28-production-migration-evidence/production-kla-create-from-rooms-normal.png) |
| Duplicate Sheets | [DuplicateSheets.xaml](../../../../lib/GUI/DuplicateSheets.xaml) | [Render](2026-10-28-production-migration-evidence/production-kla-duplicate-sheets-normal.png) |
| Custom Alert | [CustomAlert.xaml](../../../../lib/GUI/CustomAlert.xaml) | [Render](2026-10-28-production-migration-evidence/production-kla-custom-alert-normal.png) |
| Find/Replace Views | Bundled `FindReplace - Views.pushbutton/Script.xaml` | [Render](2026-10-28-production-migration-evidence/production-kla-find-replace-views-normal.png) |
| Find/Replace Sheets | Bundled `FindReplace_Sheets.pushbutton/Script.xaml` | [Render](2026-10-28-production-migration-evidence/production-kla-find-replace-sheets-normal.png) |
| Steel PSF | Bundled `Steel PSF.pushbutton/SteelPsfDialog.xaml` | [Render](2026-10-28-production-migration-evidence/production-kla-steel-psf-normal.png) |
| View Range | Bundled `ViewRange.pushbutton/MainWindow.xaml` | [Render](2026-10-28-production-migration-evidence/production-kla-view-range-normal.png) |
| Standalone Recall | [Shell](../../../../lib/match/clipboard_window.xaml), [body](../../../../lib/match/clipboard_recall_content.xaml) | [Render](2026-10-28-production-migration-evidence/production-kla-match-properties-recall-normal.png) |

| Compiled class | Normal render |
| --- | --- |
| FamilyStudioWindow | [Actual class, empty repository](2026-10-28-production-migration-evidence/compiled-family-studio.png) |
| StartupSourcePickerWindow | [Render](2026-10-28-production-migration-evidence/compiled-source-picker.png) |
| StartupImportReviewWindow | [Render](2026-10-28-production-migration-evidence/compiled-import-review.png) |
| BlockingIssuesWindow | [Render](2026-10-28-production-migration-evidence/compiled-blocking-issues.png) |
| KlaAlertWindow | [Information](2026-10-28-production-migration-evidence/compiled-alert-Information.png), [Warning](2026-10-28-production-migration-evidence/compiled-alert-Warning.png), [Blocking](2026-10-28-production-migration-evidence/compiled-alert-Blocking.png) |

Python loading delegates to the existing pyRevit `load_xaml` method when
available, retaining host initialization. Optional close callbacks preserve
caller-specific cancellation. Shared loading does not show windows or replace
workflow DataContext. C# `WindowChrome` binds the same shell parts; compiled
projects link canonical resources with their relative paths preserved.

Recall's standalone body is isolated from its existing docked body and icons.
Fixed 128 x 28 icon/text buttons fit English, German and Korean captions. Modeless
View Range retains event cleanup and Apply/Reset behavior. Selection tools retain
their distinct filtering/checking/cancellation rules. Find/Replace operations,
outcomes and Steel PSF CSV actions are preserved.

## Verification

| Check | Observed result |
| --- | --- |
| Focused Python suites | 131 tests run: 130 passed, one skipped |
| Icon generator `--check` | All 17 semantic roles current; source geometry, unsupported-shape failures and canvas bounds checked |
| Affected command metadata | All eight changed command bundles pass |
| Isolated IronPython 2.7.12 / real WPF | 36 catalog entries; 71 custom/state constructions; filters and deferred selection pass |
| Template family | 25 state layouts, normal interactions and minimum-size renders pass |
| Python production probe | 45 actual-XAML state layouts; shell/body/field geometry, version, vectors, long/empty bounds and scrolling pass |
| Compiled source/resource tests | 16 passed |
| Actual compiled UI smoke | Seven instances across all five classes pass separately on net48 and net8.0-windows |
| Full Family Studio Revit 2024 build | Pass, zero warnings/errors; packaging disabled |

The compiled smoke uses actual UI constructors and resources. Family Studio's
real UI is linked against its real ports, an empty in-memory repository, and
load services that throw if invoked. No window is shown; no Revit model,
database, import, file picker, clipboard-persistence or navigation action runs.
This verifies construction/layout, not those integrations.

Rendered checks caught and corrected object-valued View Range dropdown labels,
over-wide naming inputs, localized Recall clipping, read-only compiled bindings,
compiled pack-resource resolution, empty Family Studio detail-chip borders and
information-chip accent mismatch. Independent compiled review found no workflow
or lifecycle blockers; its information-chip finding is resolved.

Additional evidence: [all 17 icons](2026-10-28-production-migration-evidence/gui-icons-17-native.png),
[View Range long content](2026-10-28-production-migration-evidence/production-kla-view-range-long-content.png),
[Recall minimum size](2026-10-28-production-migration-evidence/production-kla-match-properties-recall-minimum.png),
[Recall Korean](2026-10-28-production-migration-evidence/production-recall-ko.png),
and [alert scrolled to end](2026-10-28-production-migration-evidence/production-alert-stress-end.png).

Reproduction entry points:

```powershell
python -B scripts/generate_gui_icons.py --check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate_ui_gallery_wpf.ps1 -OutputDirectory <temporary-output>
dotnet test src/KLCode.Wpf/Tests/KLCode.Wpf.Source.Tests --no-restore
dotnet run --project src/KLCode.Wpf/Tests/KLCode.Wpf.Desktop.Smoke --framework net48 --no-restore -- <temporary-output>
dotnet run --project src/KLCode.Wpf/Tests/KLCode.Wpf.Desktop.Smoke --framework net8.0-windows --no-restore -- <temporary-output>
```

Focused Python patterns are `ui_gallery*test.py`, `gui_*test.py`,
`window_backgrounds_test.py`, `select_from_dict_selection_test.py`,
`find_replace*test.py`, `steel_weight*test.py`, `custom_alert_integration_test.py`
and `compiled_command_bundles_test.py` under `tests/`.

## Remaining acceptance and environmental limits

- Full Family Studio Revit 2025 compilation was attempted but hits CS1705:
  installed Revit 2025 API 25.5 assemblies reference System.Runtime 10.0.0.0,
  while the declared project target is .NET 8. Installed 2026 API 26.5 references
  the same runtime family. No project retargeting or proprietary assembly
  replacement was made. The actual Family Studio UI nevertheless compiles and
  constructs successfully in the .NET 8 port-based smoke. A matching API/reference
  set is required before claiming the complete 2025 host build passes.
- Full metadata discovery still encounters the pre-existing ignored,
  cache-only Model Checker command directory without bundle metadata. All eight
  affected bundles pass; that unrelated cache was preserved.
- Live Revit ownership, keyboard/focus, Escape/Close, dragging, footer links,
  DPI/work area, accessibility, and real tool operations remain unverified.
  See GUI-08 and the [compiled acceptance plan](../../../plans/compiled-tools-acceptance.md).
- The five compiled Gallery entries remain listed and disabled as approved.
  Their isolated smoke coverage does not enable Gallery providers.
- Packaged command DLLs, extension/tool versions and generated build metadata
  are unchanged. This source migration is locally verified, not a deployment,
  release, remote push or final owner visual acceptance.
