# KL&A Tools Release History

This is the canonical release record for KL&A Tools. Each controlled `dev` to
`main` release records the version, channel, tested Revit range, affected
tools, user-facing changes, known limits, and rollback tag.

## Unreleased

No pending published release.

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
