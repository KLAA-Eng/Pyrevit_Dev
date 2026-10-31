# GUI architecture review — Windows handoff

This is the original handoff snapshot, superseded: its counts and open items
are as of `7e01901`. The consolidation plan and the dated design-system reviews
hold the current state. The Windows follow-up is recorded in
[2026-10-29 Windows verification](reviews/design-system/2026-10-29-gui-architecture-windows.md);
the [consolidation plan](../plans/custom-window-consolidation.md) owns current
status. The owner will perform the actual Revit review.

Snapshot taken 2026-10-29 on branch `dev.GUI-Clean` at `7e01901` (eight commits after the migration verification
`0f8c599`). Everything below was written and tested on macOS: the CPython suite (351 tests, one macOS-only failure
in `carbon_gwp_command_test`) and the C# source-contract project (17 tests) pass. **Nothing has been rendered in
WPF.** The IronPython probes, the desktop smoke, the icon generator check and a Revit session are the work left,
plus the five items that need a render or an owner decision.

The design rules are in [DESIGNSYSTEM.md](../DESIGNSYSTEM.md) (rewritten, 75 lines); task status is the
[consolidation plan](../plans/custom-window-consolidation.md) (row GUI-12); the full findings table with status is
the private review page `KLCode GUI Architecture Review` (claude.ai artifact; ask Logan for access) and the
Claude design-system artifact's *Repo cleanup list*.

## What changed, by commit

| Commit | Change | What to verify on Windows |
| --- | --- | --- |
| `db919d4` | Version defaults `None`, nine callers pass `__version__`, titles required, `CreateFromRooms` Close sets `cancelled`, Escape in both adapters, `KlaFoundationInput` template-binds its border, `KlaStatusInfo`-style chip | Footers show `vX.X` in Hide Revision Clouds and the five DevSandbox prototypes; Escape closes every Python window; Family Studio search box has one outline |
| `53dd182` | `WPF_styles.xaml`, `add_wpf_resource`, legacy handlers, Model Checker adapter, dead tokens / palette keys / compiled brushes removed | Gallery opens every catalog entry; `PreviewFixture` still loads |
| `d9830dc` | Scrollbar orientation trigger, Close glyph margin, indeterminate checkbox, colour-only link focus, body-first Tab order, no disabled opacity | Horizontal scrollbar in Recall and `KlaDataGrid`; first Tab lands in the body; disabled combo items readable |
| `c7f1160` | Role brushes with snake_case aliases; typed `KlaRadius*` / `KlaHairline` / `KlaClose*` / … tokens; probes read tokens; `scripts/check_ui_scale.py` | All three probes pass unchanged in output; `StaticResource` alias elements resolve in loose XAML (IronPython `wpf.LoadComponent`) |
| `4283862` | `KLCodeIcons.xaml` geometry-only merged by Foundation; presenter / pen / `KlaIcon<Role>` in Foundation; wordmark generated from the SVG | `generate_gui_icons.py --check` passes; icons render; the wordmark is pixel-identical to the previous hand-pasted version |
| `28c96f7` | `KLCodeChrome.xaml` (URIs + `DynamicResource` labels), shared version vectors JSON, implicit TextBox / ComboBox / CheckBox styles in Components | Compiled windows show localised Close / Prototype / Outreach from `Strings/ResourceDictionary.en_us.xaml`; footer links navigate |
| `7e01901` | Muted footer text `#B5C2BD`; View Range `CanResizeWithGrip`; automation names; `find_replace/layout.py`; `KLCodeCompiledTokens.xaml` deleted; `KlaLinkButton` / `KlaGhostButton` / `KlaSegmentButton`; role-named style aliases; `window_chrome.shared_resources()`; DESIGNSYSTEM rewrite | **Family Studio toolbar** (segments, link buttons) and importer Cancel render as intended; View Range resizes from the grip; the shared dictionary instance merges into several windows without a WPF ownership error |

## Run these first (Windows, Revit + pyRevit + .NET SDK installed)

```powershell
python -B scripts/generate_gui_icons.py --check
python -B scripts/check_ui_scale.py
python -B -m unittest discover -s tests -p "*test.py"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate_ui_gallery_wpf.ps1 -OutputDirectory <tmp>
dotnet test src/KLCode.Wpf/Tests/KLCode.Wpf.Source.Tests --no-restore
dotnet run --project src/KLCode.Wpf/Tests/KLCode.Wpf.Desktop.Smoke --framework net48 --no-restore -- <tmp>
dotnet run --project src/KLCode.Wpf/Tests/KLCode.Wpf.Desktop.Smoke --framework net8.0-windows --no-restore -- <tmp>
```

`validate_ui_gallery_wpf.ps1` runs the foundation, template and production probes under IronPython 2.7.12 with real
WPF. They now read every expected value from the token dictionaries (`window.FindResource('KlaButtonWidth')` and so
on) instead of pinning numbers, so a failure means a real layout change, not a stale constant. Expected risks to
look at first if something fails:

1. **`StaticResource` alias elements** (`<StaticResource x:Key="header_background" ResourceKey="KlaWindowBrush"/>`
   in `KLCode_palette.xaml`, and the compiled-name aliases in `KLCodeComponents.xaml`). They are standard WPF, but
   loose XAML through IronPython has not been exercised. If the loose loader rejects them, replace each alias with a
   `SolidColorBrush` whose `Color` binds the role brush's colour, keeping the keys.
2. **`sys:Uri` resources** in `KLCodeChrome.xaml` bound to `Hyperlink.NavigateUri`, and `Run Text="{DynamicResource …}"`
   inside the shell template.
3. **Shared dictionary instance** (`window_chrome.shared_resources()`): one `ResourceDictionary` merged into several
   windows and into Recall's content control. WPF allows it; if a probe reports a frozen / owner error, fall back to
   one instance per window (`ResourceDictionary()` per call) and keep the function.
4. **Close glyph**: the probe measures the visible glyph centre; the lift is now a 2-unit bottom margin, not a
   render transform. A sub-pixel difference is expected to stay under the probe's 0.25 tolerance.

## The five open items (need a render or an owner decision)

| # | Item | Why it waited | Suggested approach |
| --- | --- | --- | --- |
| 25 | Collapse the copied naming group (6×) and filtered check-list (4×) into compositions | Rewrites window bodies; cannot be verified without WPF | `KlaFieldRows` as an `ItemsControl` template and `KlaFilteredCheckList` as a `ContentControl` template in Components; migrate Form, Find and Replace Views / Sheets, Duplicate Sheets, then Selection, Create From Rooms, Steel PSF; keep `x:Name`s so controllers and probes still bind |
| 31 | Gallery window on the shell | `Gallery.xaml` keeps its own 30-tall header and palette; `tests/window_backgrounds_test.py` enforces that chrome | Load through `load_window`, replace the local `DataGrid` / `ComboBox` styles with `KlaDataGrid` / `KlaComboBox`, delete the exception branch in the test |
| 16 | Host smoke: the production `load_xaml` branch and View Range's real `WPFWindow` subclass run under no probe | Needs Revit | Open each migrated window from the UI Gallery in a live session and record GUI-08 evidence; record the pyRevit version whose `load_xaml` signature `window_chrome.py` assumes |
| 35 | `bd79fb9` ("partial", 111 files) is unbisectable | Rewrites history on the shared branch | Owner decision; `git add -p` into the plan's batches before merging to `master-dev`, or leave and note |
| 39 | `CreateFromRooms` and `CustomAlert` have no production callers | Owner decision | Wire to a tool, move to DevSandbox, or delete with their Gallery entries |

Also worth a look while a Revit session is open: `scripts/check_ui_scale.py` lists 98 off-scale `Margin` /
`Padding` literals in consumer windows (mostly the compiled views and View Range); none is a defect, but moving them
onto `KlaGridSpace*` / `KlaCompactInset` is mechanical once a render is available to compare against.

## Conventions to keep

- Shared dictionaries never spell a colour or a number (`gui_token_scale_test.py` and the C# contract test fail if
  they do); add a token to `KLCodeFoundationTokens.xaml` and reference it.
- `KLCodeIcons.xaml`, the `generated-icons` block in `KLCodeFoundation.xaml` and `lib/_logos/KLCodeWordmark.xaml`
  are generated; edit the SVG sources and run `scripts/generate_gui_icons.py`.
- Version strings passed to `load_window` / `select_from_dict` are `__version__` or `None`; `gui_caller_identity_test`
  scans every caller.
- Keep `CustomAlert.py` importing `WPF_Base` directly: `GUI.forms` loads the Revit-bound `SelectFromDict` at import.
- Commit per step with its tests; do not push to `main`; the release path is unchanged (see `docs.ai/RELEASING.md`).
