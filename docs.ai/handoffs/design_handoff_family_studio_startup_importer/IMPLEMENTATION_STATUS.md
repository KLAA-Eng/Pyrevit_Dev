# Family Studio and Startup Importer implementation status

## Current gate

**Source, Windows compile, and pyRevit packaging are complete. Live Revit visual
and workflow acceptance is the remaining release gate.** Both commands remain in
`05 DevSandbox.panel` until that check is recorded.

## Isolated compiled design system

- `src/KLCode.Wpf` is the only owner of the new compiled control templates and
  extra presentation tokens. It consumes the canonical
  `lib/GUI/Resources/KLCode_palette.xaml` brush keys.
- `lib/GUI/Resources/WPF_styles.xaml` and the Python/pyRevit WPF surfaces were
  not changed. No compiled feature window imports the legacy IronPython
  `Header` event contract.
- The adapter now supplies borderless window chrome, Audiowide `/KLCode`
  branding, header drag/Close behavior, buttons, segmented controls, text and
  combo inputs, check boxes, list rows, scrollbars, cards, status chips,
  footers, and the KL&A alert surface.
- The handoff's `Audiowide-Regular.ttf` is embedded as a compiled WPF resource.
  The handoff HTML is not copied into either command bundle.
- All visible feature copy is keyed in tool-owned English resource dictionaries
  with deterministic English fallback.

## Family Studio

- FS-1 is implemented at exactly `1180 x 740` with the handoff header, toolbar,
  facet row, list/grid results, checked batch membership, empty state, 4:3
  preview, detail/status/type/tag/parameter information, and footer actions.
- Search, category/type/parameter/root/duplicate filtering, favorites, recent
  use, cached previews, refresh, load, load-and-place, batch load, copy path,
  and open folder continue to use the existing repository and Revit services.
- List/grid checkbox state is shared, selection remains independent of batch
  membership, and batch load retains its single `TransactionGroup` rollback
  boundary.
- Views/project scope and project-local type mutation are visible but disabled
  with explanatory copy. Root/tag/duplicate-preference editing remains parked
  because the plan does not define ownership or safe mutation contracts. FS-6
  vendor integration remains out of scope.

## Startup Importer

- SI-1 is implemented at exactly `560 x 470`: checklist and settings are
  independently browsed, parsed, validated, summarized, and required before
  Review is enabled.
- SI-2 is implemented at exactly `860 x 640`: rows preserve checklist order and
  show matched, existing, and unchecked classifications; only actionable rows
  can be selected; import count and requirements update from live state.
- SI-3 is implemented at exactly `560 x 520`: unknown or duplicate selected IDs
  are grouped into a blocking report and import stays disabled.
- SI-6 information/warning/blocking alerts are implemented at exactly
  `440 x 300` using the isolated compiled KL&A alert chrome.
- The command rebuilds and revalidates the review immediately before mutation,
  resolves selected stable IDs again, remains create-only, skips existing
  targets, and rolls back the transaction group on failure.
- SI-4 placement/splitting and SI-5 links/rebuild remain explicitly parked. No
  source-link, rebuild, Extensible Storage, or placement behavior is implied.

## Validation record — 2026-09-01

- Family Studio Core/Database: `24 passed`.
- Startup Importer Core: `15 passed`; new UI/view-model tests: `3 passed`.
- Compiled WPF resource/style/dimension contracts: `13 passed`.
- pyRevit compiled-command bundle/preload checks: `2 passed`.
- Revit 2024 Family Studio and Startup Importer compile/package: passed with no
  errors; the direct Family Studio build has no warnings.
- Revit 2025+ Family Studio and Startup Importer compile/package: passed with no
  errors. Autodesk Revit 2025 references produce the known
  `Microsoft.VisualBasic` unification warning.
- Packaged bundles contain both host families:
  `*_2024.dll`/`KLCode.Wpf_2024.dll` for Revit 2024 and unsuffixed assemblies for
  Revit 2025+.
- Source inspection confirms no native `MessageBox` or `TaskDialog` remains in
  either feature flow and no literal feature copy remains in the XAML windows.

## Remaining live acceptance

In Revit 2024 and 2025+, capture FS-1, SI-1, SI-2, SI-3, and SI-6 at 100% and a
high-DPI scale. Confirm assembly loading, Audiowide rendering, header drag and
Close, clipping, scrollbar behavior, keyboard focus order, disabled states,
and one disposable-project happy/error path for each command. This is runtime
evidence only; no further source implementation is currently blocked.
