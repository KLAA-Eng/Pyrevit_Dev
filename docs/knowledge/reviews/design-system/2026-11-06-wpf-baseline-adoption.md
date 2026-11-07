# WPF baseline adoption — 2026-11-06

The [consolidation plan](../../../plans/custom-window-consolidation.md)
owns tasks GUI-46 through GUI-49. The owner confirmed the migration order and
authorized implementation after grilling. The WPF workspace is the XAML
presentation baseline; its preview-only class/seed attributes never reach the
extension. No remote publication or model operations are part of this work.

## Delivered changes

- Transferred 21 edited WPF XAML files first, including the six standard dialogs,
  resources and other existing window/template edits. The transfer validated
  names/events and source hashes and saved timestamped originals in the WPF
  workspace's Backups directory.
- `GUI.forms.select_from_dict` now uses `GUI.selection_compat` and the shared
  Selection dialog. Existing callers retain sorted labels, initial checks,
  custom captions, visible-only batch operations, hidden checks and list returns,
  including cancellation and single-select values of `None`.
- Duplicate Sheets has a scrollable body, pinned action, four-column include
  choices and local token-based styles. View Range has token rows/spacers and
  Reset above Apply. Existing names, handlers, bindings and operations remain.
- Repaired compiled-window aliases and Gallery feedback consumers of removed
  resource keys. No compiled UI redesign or packaged plugin DLL replacement.
- With separate owner confirmation, replaced the secondary-button border
  literal with the existing exact-color token. No new shared styles or tokens.

## Local verification

All builds used installed dependencies; no restore or installation was run.

| Proof | Result |
| --- | --- |
| WPF `Workspace.ps1 Build` / `Verify` | Build, fresh initialization recovery, cold designer and 159 Gallery state constructions pass; compiled designer surfaces load. |
| `Test-SelectionAdapter.ps1 -Wpf` | 14 tests pass against the final extension adapter, including four real modal windows. Initial red test failed for the missing adapter before implementation. |
| `Test-DialogSamples.ps1` | All six dialogs' designer snapshots and interactive JSONC setups pass. |
| `Test-Sync.ps1` | Source conflict, names/events, preview stripping, refresh and template-local-name protections pass against synthetic repositories. |
| C# `KLCode.Wpf.Source.Tests`, `dotnet test --no-restore` | 17 tests pass. The initial hard-coded border failure was resolved by the owner-approved token reference; the no-literal policy was retained. |
| Compiled desktop smoke, fresh `dotnet build --no-restore -f net48` and `-f net8.0-windows` | Seven instances across all five actual compiled classes pass on each runtime, using fake ports and no Autodesk assemblies. Primary-height assertion now follows the existing 36-unit token. |
| Visual inspection | Normal and minimum-size Duplicate Sheets / View Range renders inspected; Duplicate Sheets scrolls with action visible. |
| Synchronization | Workspace Check reports zero pending files; all 43 tracked source XAML files equal their synchronized baselines. |
| Independent review | Baseline resource consumers and the adapter/window changes reviewed by a separate agent. Removed-key consumers repaired; no remaining correctness findings. |

WPF evidence resides under `.dev.KLCodeWPF/Verification/`, including
`kla-duplicate-sheets.png`, `kla-view-range.png`, `migration-minimum-View39.png`,
`migration-minimum-View3.png`, and the `migration-compiled-*` smoke logs/renders.

## Remaining acceptance

Live Revit model effects, View Range ExternalEvent/close cleanup in the host,
Duplicate Sheets transactions, actual-host focus/ownership and DPI acceptance
remain unverified. Caller refinements, other dialog-call migrations, native
dialogs and unrelated model-operation changes remain outside this delivery.
Historical scripts and old GUI tests that assert retired resource names were
not used as evidence for this new baseline. Local checks do not establish a
release or close the plan's separate live-host acceptance task GUI-08.
