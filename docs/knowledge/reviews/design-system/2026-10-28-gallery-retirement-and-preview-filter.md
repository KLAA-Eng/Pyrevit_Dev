# Legacy rename retirement and Gallery Preview filter

Date: 2026-10-28. Baseline: `2c1d34b` on `dev.GUI-Clean`, plus this delivery.
Owner request: remove legacy sheet/view rename forms from the repository and
add a Preview filter alongside Origin. The [Gallery plan](../../../plans/ui-gallery-coverage.md)
owns status; its [SPEC](<../../../../KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/SPEC.md>)
owns behavior.

## Source removal and caller boundary

Deleted `lib/GUI/RenameViews.xaml`, `lib/GUI/RenameSheets.xaml` and the unused
`lib/GUI/RenameSheets.py` wrapper. Removed their launchers, preview allowlist
entries and old export profiles. Current documentation/test inventories no
longer count them. Dated review references remain historical evidence.

`BaseRenaming` remains used by Core Find and Replace in Views. Its concrete
class overrides `start()` and loads its own adjacent `Script.xaml`; no current
command calls the removed default form loader. The base's obsolete `start()`
implementation now explicitly requires a concrete command implementation.
Removed imports were used only by that old default loader. The active Core
sheet command likewise keeps its own local presentation. Neither production
command script or current XAML was changed.

Source tracing found no remaining runtime imports of the retired sheet wrapper
or loads of the two retired XAML files. Caller tests confirm both active Core
windows still map to their correct calling tools. Older reviews preserve the
source state at their recorded baseline rather than declaring current inventory.

## Preview filter

The labeled, keyboard-addressable Preview ComboBox is beside Origin. Its choices
come from the current catalog's `preview_status` values, with All previews as
the default. Current choices are Interactive preview and Deferred; other status
values appear automatically when present. It filters availability, independently
of the fictional Normal/Empty/Error/etc. state selector.

Search, Origin and Preview combine. Existing selection is preserved when still
visible. Empty intersections clear details and disable launch. The five compiled
entries remain listed as Deferred and unavailable.

The current catalog has 33 entries and 18 repository Window sources after the
two forms were removed: 28 entries available, 5 deferred. The earlier component
review's 20-source/19-remaining inventory describes its pre-retirement baseline.

## Verification

- Registry tests first failed for unsupported Preview filtering and existing
  retired files, then passed after implementation.
- Gallery suite: 52 run, 51 passed, 1 skipped for unavailable symlink privilege.
- Find/replace checks: 12 passed; existing window/background checks: 9 passed.
- Total focused checks: 72 passed, 1 skipped. Caller regression assertions also
  passed for both current Core command-local XAML sources.
- Real installed IronPython/WPF: 33 entries, 56 remaining custom/state
  constructions, all foundation checks, and combined Search/Origin/Preview
  intersections passed. Deferred-only yields five disabled entries; a built-in
  origin plus Deferred yields no rows and disabled launch. Resetting filters
  restores the catalog.
- Visually inspected the default and minimum-width renders plus Deferred view:
  [1060-wide Gallery](2026-10-28-gallery-filter-evidence/gallery-1060.png),
  [900-wide Gallery](2026-10-28-gallery-filter-evidence/gallery-900.png),
  [Deferred-only](2026-10-28-gallery-filter-evidence/gallery-deferred.png).
- Independent static review found no material issue in deletion scope,
  active-Core loader compatibility, filtering or empty-selection handling.

The tests use the same commands documented in prior Gallery verification, with
`ui_gallery*test.py`, `find_replace*test.py`, `window_backgrounds_test.py`, and
`scripts/validate_ui_gallery_wpf.ps1`. No live Revit command/model operations
were run. Live host acceptance remains pending. Version v0.5 remains the same
planned unreleased delivery; no release or remote publication was performed.
