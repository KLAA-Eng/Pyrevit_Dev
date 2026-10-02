# KL&A Tools Release History

This is the canonical release record for KL&A Tools. Each controlled `dev` to
`main` release records the version, channel, tested Revit range, affected
tools, user-facing changes, known limits, and rollback tag.

## Unreleased

No pending published release.

## 0.0.9 - 2026-10-01

- **Channel:** Beta
- **Tag:** `v0.0.9-beta`
- **Tested Revit range:** No new live Revit claim. Carbon GWP Pull is a beta
  workflow in the KL&A Tools panel; its deterministic logic is covered by the
  static test suite.

### Added

- Carbon GWP Pull now renders and places managed GWP and material-volume
  doughnut charts from the selected post-processing workbook's `Export` sheet.
- The command reports every chart slice and independently identifies invalid
  GWP or volume rows without discarding valid values for the other chart.
- An informational Material Accuracy check reports actual Excel `#N/A` cells
  in the post-processing workbook without blocking chart creation.

### Fixed

- Carbon GWP Pull command tests now load the current KL&A Tools source bundle.

### Known limits

- Carbon GWP Pull requires Microsoft Excel COM interop and trusted,
  formula-linked `.xlsx` or `.xlsm` workbooks.
- Live Revit acceptance remains required for image import, sheet placement,
  rerun reload, worksharing permissions, model reopening, and undo behavior.

**Rollback tag:** `v0.0.8-beta`

## 0.0.8 - 2026-09-28

- **Channel:** Beta
- **Tag:** `v0.0.8-beta`
- **Tested Revit range:** No new live Revit claim. This release adds a
  host-independent packaging-path regression check; DevSandbox tools remain
  beta development content.

### Fixed

- Family Studio and Startup Importer now preload their managed dependencies
  from the ribbon-tab folder actually present in the extension. This supports
  both the development `KL&A Tools_dev.tab` layout and the distributed
  `KL&A Tools.tab` layout, preventing missing-dependency messages in the
  installed release.

### Known limits

- Family Studio and Startup Importer remain DevSandbox beta tools and require
  their documented live-Revit acceptance before promotion beyond DevSandbox.

**Rollback tag:** `v0.0.7-beta`

## 0.0.7 - 2026-09-28

- **Channel:** Beta
- **Tag:** `v0.0.7-beta`
- **Tested Revit range:** Revision workflows have owner-confirmed live Revit
verification. No extension-wide Revit-version claim is made; DevSandbox tools
remain beta development content.

### Added

- Revision Cloud Finder and Hide/Unhide Revision Clouds workflows in Core
  Tools, including sheet and placed-view cloud handling.
- DevSandbox beta workflows for Family Studio, Startup Importer, and Beam
  Reaction Declutter.

### Changed

- Revision schedule actions use clearer toggle labels and the consolidated
  Revision pulldown layout.

### Fixed

- Release checks now follow the final `KL&A Tools.tab` name and exclude
  compiled WPF source windows from the pyRevit-only UI Gallery launcher set.

### Known limits

- Family Studio, Startup Importer, and Beam Reaction Declutter remain
  DevSandbox beta tools; they are not promoted as stable commands by this
  release.

**Rollback tag:** `v0.0.6beta`

## 0.0.6beta - 2026-09-15

- **Channel:** Beta
- **Tag:** `v0.0.6beta`
- **Tested Revit range:** Historical evidence predates this changelog; consult
the affected command `SPEC.md` files before claiming compatibility.

This is the baseline record created when the formal changelog was adopted.
Earlier release details remain in Git history and existing documentation.
