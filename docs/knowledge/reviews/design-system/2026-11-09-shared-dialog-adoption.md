# Shared tool-dialog adoption — 2026-11-09

The [consolidation plan](../../../plans/custom-window-consolidation.md) owns
tasks GUI-50 through GUI-54. The owner confirmed the scope on 2026-11-08:
Find/Replace first, then matching dialogs across active Python tools, including
DevSandbox. WPF XAML remains the presentation baseline. Native file/folder
pickers, progress and selection overlays, compiled add-ins, and Gallery's
intentional built-in demonstrations remain outside the migration.

## Delivered behavior

- Both Find/Replace tools use shared Rename through thin command adapters.
  Rules/case requests close before model execution. The existing transaction
  and per-item rollback implementation is unchanged, including atomic sheet
  name/number changes and collision checks.
- Clean success finishes quietly. Unchanged, partial and failed results show
  shared Action Choice with Details and Edit and Retry. Rules survive retries;
  partial retries target only unfinished elements. A browser-refresh failure
  after committed changes does not offer to apply those changes again.
- `GUI.tool_dialogs` supplies explicit notice, confirmation, small-menu and text
  adapters. `GUI.tool_selectors` supplies the remaining read-only selectors.
  No upstream pyRevit module is patched. Twenty-five direct tool entry points
  and two shared Snippets helpers now use the migrated boundaries.
- Concrete Mix Header retains its two distinct No branches. Suggestions still
  distinguishes accepted blank text from cancellation. Revision filters,
  placeholders, current-selection shortcuts, document exclusions and returned
  object identities remain intact. Dialog ownership defaults lazily to Revit.
- The two duplicate naming XAML files and obsolete inline-result controller,
  layout helper and tests are retired with originals archived in the WPF
  workspace's Backups directory. Gallery/F5 tool previews instantiate the
  actual shared Rename factory and retain fictional data.
- All 41 tracked XAML sources are synchronized. Shared Components, Foundation,
  Tokens and icon dictionaries are unchanged by this delivery.

## Local evidence

| Check | Result |
| --- | --- |
| Find/Replace unit and command tests | 23 pass, covering requests, planning, transaction contracts, cancellation and safe retry. |
| Additional affected command regressions | 108 pass: Beam Reaction Declutter 30, Carbon GWP 27, Revision Clouds 25, Concrete Mix 18, Excel COM smoke command 2, caller identity 3 and alert integration 3. |
| Gallery tests | 76 run, one existing skip; aliases and lazy factory caller discovery pass. |
| Selector, dialog, Rename, collector and compatibility Python suites | 73 run; eight actual-WPF cases are intentionally skipped under CPython and exercised separately under IronPython. |
| `Test-ToolDialogs.ps1 -Wpf` | All 25 adapter/selector tests pass, including four real modal dialog cases. |
| `Test-SelectionAdapter.ps1 -Wpf` | All 14 compatibility tests pass, including four real modal cases. |
| `Test-FindReplaceDialog.ps1` | Actual Rename → result Details → Edit and Retry → Rename passes: blank-rule validation, retained prefix, execution after close and unfinished-only identity. |
| `Workspace.ps1 Verify` | Build, fresh initialization/cold-designer probes, 159 Gallery states and compiled designer surfaces pass. |
| Source/preview checks | Workspace Check reports zero pending XAML changes; all 41 source files match their baselines and shared dictionary hashes are unchanged. |
| Independent review | General adapters, selector call sites and Find/Replace planning/controller were independently reviewed; no remaining blocking findings. |

Evidence images and modal results are in WPF `Verification/dialog-adoption/`,
with normal tool renders in `Verification/kla-find-replace-views.png` and
`Verification/kla-find-replace-sheets.png`. All test/build dependencies were
already installed; no package restore, installation or model operation ran.

The integration was saved in extension commit `8d67281` and WPF commit
`a814a36` while the session was paused. Subsequent completion work updates
metadata, documentation and regression test boundaries without replacing those
commits or discarding owner changes.

The three command fixtures now fake `GUI.tool_dialogs` rather than the retired
pyRevit dialog boundary; their model assertions remain. Steel PSF's integration
assertion now requires the approved shared alert adapter. Initial failures were
missing test-double imports and an obsolete API assertion; the regression
runner's source import path was also corrected. These fixes retain behavior
coverage and do not change production model logic.

## Acceptance boundary

These checks do not prove live Revit model effects, actual-host focus/ownership,
DPI behavior, configuration-mode revision filters or transaction recovery in a
representative model. GUI-54 retains that live acceptance work. Packaged compiled
DLLs, dormant library UI and unrelated model-operation changes remain untouched.
