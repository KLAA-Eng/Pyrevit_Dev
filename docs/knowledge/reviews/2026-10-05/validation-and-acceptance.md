# Validation record and live acceptance plan

Date: 2026-10-05, America/Denver. Source baseline: `1562e96a5f6e23b7368c80e317868a0c059dc165` (`0.0.11-dev`). Review documents were created on `codex/comprehensive-design-tools-review`. The initial working tree was clean. No runtime code, icons, logos, compiled deployment assets, specifications or release identity were changed.

## Executed checks

| Check | Command / method | Actual result | What it establishes |
| --- | --- | --- | --- |
| Python suite | `.\.venv-rvt26\Scripts\python.exe -m unittest discover -s tests -p '*_test.py'` | 195 run: 194 passed, one skipped, zero failures; 2.903 seconds test time | Host-independent and mocked/source behavior covered by those tests |
| Visible metadata | `.\.venv-rvt26\Scripts\python.exe scripts/check_tool_metadata.py` | 36 visible command bundles, zero errors | Required current titles, versions, authors, tooltip/SPEC shape and history checks pass |
| Local identity | Import `scripts/release_check.py` and call `check_identity()` | Exit 0, no errors | Local version/build/changelog/ledger identity consistency; not remote publication verification |
| WPF source tests | `.\.dotnet\dotnet.exe test src/KLCode.Wpf/Tests/KLCode.Wpf.Source.Tests/KLCode.Wpf.Source.Tests.csproj --no-restore --nologo` | 13 run: 12 passed, **one failed** | Current compiled-source contract conflict, detailed below |
| Family Studio core tests | Same test command for `src/KLCode.FamilyStudio/Tests/KLCode.FamilyStudio.Core.Tests/KLCode.FamilyStudio.Core.Tests.csproj` | 19 passed | Core/indexer behavior under those tests; not live Revit load/place |
| Family Studio database tests | Same test command for `src/KLCode.FamilyStudio/Tests/KLCode.FamilyStudio.Database.Tests/KLCode.FamilyStudio.Database.Tests.csproj` | Seven passed | SQLite repository behavior under those tests |
| Startup Importer core tests | Same test command for `src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.Tests/KLA.ModelStartupImporter.Tests.csproj` | 15 passed | Reader/settings/import-plan behavior under those tests |
| Startup Importer UI tests | Same test command for `src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI.Tests/KLA.ModelStartupImporter.UI.Tests.csproj` | Three passed | Tested view-model behavior; no rendered-window acceptance |
| XAML source inventory | XML parse of every tracked `.xaml` | 53 parsed, zero parse errors | Well-formed XML, **not** WPF loadability, event wiring, or accessibility |
| PNG inventory | Pillow decode, RGBA statistics, dimensions and SHA-256 | 428 reusable source PNGs and 76 ribbon PNGs decoded | Asset measurements, **not** actual ribbon appearance |
| Startup error reproduction | Extract unchanged `_load_dependency` AST; stub `File` and make `Assembly.Load` raise | `NameError: name 'relative_path' is not defined` | REP-05 confirmed without loading real assemblies or changing source |
| Alert layout reproduction | STA WPF controls only; no Window created/shown | Scroll extent 1620, viewport 1620, scrollable height 0 under 190 units available | GUI-03 layout mechanism; not an actual Revit screenshot |

The five compiled test projects total **57 tests: 56 passed and one failed**. They were built from the current sources with existing restored dependencies. Their normal ignored `bin`/`obj` outputs were updated; no packaging target or Revit bundle deployment was run. The tests targeted .NET 8 / .NET 8 Windows; this does not establish .NET Framework 4.8 build or host acceptance.

The Python executable is CPython 3.14.7 despite the virtual environment's `rvt26` name. Its successful tests do not establish IronPython 2.7 runtime compatibility. The targeted GUI catalog rerun identified the single skip: `test_skips_a_xaml_symlink_that_resolves_outside_the_catalog_root`, because Windows symlink creation returned **WinError 1314**, missing privilege. The symlink-escape scenario therefore remains unexecuted in that test; other catalog safety cases passed.

### Compiled failure details

```text
LegacyStyles_MergeTheCanonicalPaletteInsteadOfForkingBrushes
Assertion failed. Expected collection to contain the specified element.
expected: "KLCode_palette.xaml"
collection: []
DesignSystemResourceContractTests.cs:86
Failed: 1, Passed: 12, Skipped: 0, Total: 13
```

The legacy dictionary repeats its own brushes, as the current design guide says. The test expects consolidation already to have occurred. This discrepancy was recorded, not repaired, under REP-06. See [repository findings](repository-and-assets.md#rep-06--p2--the-consolidated-release-check-does-not-exercise-the-compiled-test-projects). The consolidated release script was inspected; its components were run as useful to this review. **This was not a release check or release approval:** origin was not fetched, remote release evidence was not inspected, and release-delta checks were not treated as current remote evidence.

### Additional targeted behavior probes

The production-tools reviewer exercised extracted unchanged functions and existing mocks for empty/colored Highlight 2D selections, Excel automation-security failure, issued/no-op revision updates, failed sheet revision changes, dependent-view cloud visibility, and View Range setter failure. The tool report records trigger and observed result beside each finding. These are isolated reproductions, not live Revit or Excel runs. No mutation-testing edit was made to application source.

The prototype reviewer also reproduced a failed required-cell clear retaining stale Concrete Mix text, and a filtered Steel PSF list omitting an already checked story. An arithmetic fixture showed that the Steel chart's per-member values of 1 and 3 PSF disagree with the 4 PSF story aggregate for 100 + 300 pounds over 100 square feet. These checks ran without Revit or Excel; actual schedule/chart acceptance remains pending.

## Read-only live host evidence

The actual pyRevit MCP connector reported:

```text
Status: active
Health: healthy
API: revit_mcp
Revit Available: True
Revit version: 2024
Revit build: 24.3.50.51
Python: 2.7.12 (2.7.12.1000)
.NETFramework,Version=v4.8 on .NET Framework 4.8.9345.0 (64-bit)
pyRevit: 6.5.3.26176+2017:
```

The trailing colon is preserved from `get_formatted(extended=True)`; no nonempty signature was returned. Version information was read through the live connector and cross-checked against installed module APIs. The model title is intentionally omitted because no project-specific model content is needed to assess this review.

A second read-only query returned:

| Revit 2024 constant | IntegerValue |
| --- | ---: |
| `DB.PlanViewRange.Unlimited` | -1 |
| `DB.PlanViewRange.Current` | -3 |
| `DB.PlanViewRange.LevelAbove` | -2 |
| `DB.PlanViewRange.LevelBelow` | -4 |
| `DB.ElementId.InvalidElementId` | -1 |

This rejected a possible false positive: mapping Unlimited to -1 is not itself an error in this host. It does not resolve the separately identified handling of Current/Above/Below. No transaction, element edit, view change, save, synchronization, seed-file open, Excel session, family load, modal Revit window, or external message was performed.

## Evidence inventory and reproduction

| Artifact | Contents |
| --- | --- |
| [commands.csv](evidence/commands.csv) | Every visible bundle, panel/type, script length, SPEC/icon presence, metadata errors |
| [xaml.csv](evidence/xaml.csv) | Every tracked XAML path, root type, geometry attributes, parse result and source automation-attribute count |
| [icons.csv](evidence/icons.csv) | Every scoped PNG path, dimensions, alpha bounds, dominant opaque color, measurement flags and SHA-256 |
| [ribbon-contact-sheet.png](evidence/ribbon-contact-sheet.png) | All 57 non-hidden ribbon PNGs on light/dark sample backgrounds, visually inspected; generated asset comparison, not a host screenshot |
| [inventory-summary.json](evidence/inventory-summary.json) | Reconciled baseline counts and measured exceptions |
| [findings.csv](evidence/findings.csv) | All 54 unique finding IDs, priority, title, owning report and link anchor |
| [inventory_snapshot.py](evidence/inventory_snapshot.py) | Reproduction helper; reads repository files and writes only adjacent evidence CSV/JSON |

Run the helper from the repository root with Python 3 and Pillow. No additional dependency was installed; this run used the desktop app's bundled Python/Pillow. It deliberately starts from Git-tracked files for XAML/assets, excluding ignored build products and environments. The visible-command inventory uses the repository's own metadata discovery. The helper does not infer accessibility from an attribute count or design compliance from color counts.

## Required live acceptance before closing behavior findings

Use disposable representative models and copies of workbooks. Record the tool version, extension SHA, exact Revit/pyRevit/Excel versions, expected result, actual result, screenshot/output evidence, and tester/date. “Works in Revit” without those details is not a repeatable result. This table is a proposed acceptance plan, not work already performed.

| Area | Minimum scenarios | Pass condition |
| --- | --- | --- |
| Revit 2024 and .NET 8 hosts | Test each claimed 2025/2026 build, same seed cases | Relevant workflow succeeds on each explicitly claimed host; absent hosts remain unverified |
| Model transactions | Empty/invalid targets, read-only/owned elements, setter refusal, rollback, pending failure processing, cancel | Counts and report match committed outcomes; no false success or unexpected partial mutation |
| Revisions | Issued/unissued, no-op, cloud-required revisions, dependent views on multiple sheets | Actual sheet/cloud state matches report and all eligible selected targets are addressed |
| View Range / graphics | Relative sentinels, unlimited, non-default graphics, multiple Apply/Reset cycles | Values round-trip correctly; reports reflect failed setters; documented graphics policy is respected |
| Carbon GWP and Excel | COM security getter/setter failure, stale refresh, missing data, reopen/cleanup, locale and paths | No unverified refresh/data used; macro policy enforced; actionable cleanup/errors reported |
| Family Studio | Invalid/unavailable roots, same-name families, failed load/commit, large libraries, partial scan | No wrong-content fallback; scan issues visible; truncation discoverable; valid siblings continue when contract allows |
| Startup Importer | Independently created seed/target IDs, missing requirements, unsupported schedule semantics, failed commit | No writes until preflight passes; exact supported content preserved; no false success/partial committed batch |
| Concrete Mix / Steel PSF | Locked/unclearable cells, intentional blanks, known story aggregates, filtered checked items | No stale requirement retained unnoticed; worksheet/chart/report agree; filtering retains intended selection |
| Files and reports | Cancel picker, Unicode/long paths, read-only folders, existing outputs, cleanup failure | Explicit cancel/skip/failure, no unexpected overwrite/deletion; persistent outputs match declared ownership |
| Preflight | Fresh config, discovery before selection, changed document, empty/non-workshared models | Import does not prompt; correct document is audited; cancellations are clean |
| GUI and accessibility | All 20 window surfaces, keyboard-only, Narrator/UIA, long content, high contrast, DPI100–200% | Meaningful names, visible focus, readable text, reachable actions and bounded messages |

Native pyRevit dialogs, docked panes, Gallery fixtures and compiled dialogs should be tested in their correct hosts. Gallery preview is not a substitute for compiled invocation. Full .NET Framework and .NET 8 packaging, deployed-binary/source parity, dependency advisories, load timing, and RFA/RVT content fidelity remain outside the executed evidence.

## Review-document acceptance

Before handoff, verify report links, the 19 + 17 command reconciliation, the 53-XAML reconciliation, unique finding IDs, and path/line evidence. Review the Git diff and ensure only `docs/reviews/2026-10-05/` appears. Check new files separately because ordinary `git diff --check` does not inspect untracked documents. The overview records the final document-validation outcome.
