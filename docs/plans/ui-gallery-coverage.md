# UI Gallery standalone coverage

Owner-approved scope: 2026-10-27. Current work branch: `dev.GUI-Clean`.
Initial work was performed on `master-dev`; the owner requested moving all local
GUI commits to the dedicated branch on 2026-10-27.
This plan owns task status. The [Gallery SPEC](<../../KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/SPEC.md>)
owns behavior; the [verification record](../knowledge/reviews/design-system/2026-10-27-ui-gallery-verification.md)
owns dated evidence. The [2026-10-26 review](../knowledge/reviews/design-system/2026-10-26-design-system-and-gui-review.md)
remains historical evidence for production GUI issues.

## Scope and exclusions

Complete standalone-window inventory, explicit Repository custom / pyRevit
built-in / Revit/Windows native origins, source-backed calling-tool lists,
interactive fictional state previews, and faithful production XAML composition.
Native picker results are discarded. Docked panels, overlays, production GUI
fixes, release preparation, and remote publication are excluded. Five compiled
windows remain visible and disabled by explicit owner decision.

## Task ledger

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| GAL-01 | Inventory standalone sources and label origins/availability | Implemented; locally verified | Registry and source-coverage tests; new sources cataloged without execution permission |
| GAL-02 | Show calling tool titles/paths and search them | Implemented; locally verified | Direct/indirect/static caller tests and actual IronPython Gallery filtering |
| GAL-03 | Add interactive states with isolated actions | Implemented; locally verified | Scenario/adapter tests and 66 real-WPF custom/state constructions |
| GAL-04 | Preserve Recall composition and register Model Checker conditionally | Implemented; locally verified | Real Recall shell/UserControl render; exact-path adapter only when source exists |
| GAL-05 | Update SPEC/version and review evidence | Implemented; locally verified | Planned v0.5; dated verification record; targeted metadata and diff checks |
| GAL-06 | Live Revit acceptance | Pending owner review | Owner took actual Revit review on 2026-10-29; every supported family/state, input/dismissal, native pickers, DPI, and no production side effects |
| GAL-07 | Remove retired rename forms and add Preview filter | Implemented; locally verified | 2026-10-28 owner request; source/caller regression checks and real WPF filter intersections; [verification](../knowledge/reviews/design-system/2026-10-28-gallery-retirement-and-preview-filter.md) |
| GAL-08 | Register five template references | Implemented; locally verified | Selection/Form replace old main/generic FindReplace; Message/Options/Review add shared specimens; [family verification](../knowledge/reviews/design-system/2026-10-28-template-family.md) |
| GAL-09 | Repair Window source header sorting | Implemented; locally verified | Missing template-column SortMemberPath made CanUserSort false (reproduced in actual WPF). Explicit RelativePath target fixes it; UI Automation header invocation verifies ascending/descending displayed values. Gallery filtering/deferred/preview regressions remain green. |
| GAL-F01 | Enable five compiled previews | Deferred by owner | Future actual-view providers/actions, runtime builds, and matching-host validation |

GAL-F01 covers Family Studio, Startup Importer source picker/review/blocking
issues, and the shared compiled alert. It is not a prerequisite for GAL-01–05.
Disabled status is a product-scope decision, not proof that all constructors
require active model state.

## Implementation and validation boundaries

Known custom previews are explicitly allowlisted. Runtime XAML discovery never
authorizes execution. Caller indexing never imports scanned source; dynamic
routes can remain unresolved and must not be represented as observed runtime
usage. Model Checker is not present on `master-dev` at this baseline; its
adapter does not merge or copy that command from `dev.model-checker`.

No production XAML/helpers are changed by the Gallery adapters. Pure scenario
logic lives under `lib/ui_gallery`; `script.py` coordinates the pyRevit window.
The separate [custom-window consolidation](custom-window-consolidation.md)
migrates production sources; Gallery follows those actual sources and keeps
all five compiled previews disabled. The subsequent
[migration verification](../knowledge/reviews/design-system/2026-10-29-production-migration.md)
records the current 36-entry catalog and 71 custom/state constructions.
Gallery's own shell now shares the foundation; the architecture follow-up and
current Windows evidence are owned by
[GUI-12](custom-window-consolidation.md) and its linked review record.
Host-independent tests and isolated IronPython/WPF tests complement each other.
Neither substitutes for GAL-06. The full metadata checker has a pre-existing
missing-bundle error for a cache-only Model Checker directory left by the other
branch; validate the Gallery bundle separately and preserve that unrelated work.

## Recovery and continuation

Revert the Gallery command, its new helper/test files, and this delivery's
documentation together if rollback is needed. No model/data migration exists.
Do not replace production GUI assets to repair a preview. Revalidate the current
checkout and this ledger before later work; use GAL-F01 for compiled follow-up.
