# Custom window consolidation

Owner-approved design: 2026-10-27. Work directly on `master-dev` as requested.
This file owns task status. [DESIGNSYSTEM.md](../DESIGNSYSTEM.md) owns the
shared design rules; the [main template guide](../../lib/GUI/_templates/KLCodeMainTemplate.md)
owns the reference-window implementation and usage.

## Delivery boundaries

The full direction covers repository-owned standalone Python and compiled WPF
windows, with thin host adapters and shared presentation rather than shared
workflow inheritance. Preserve tool operations, modal/modeless lifecycles,
and existing action placement. pyRevit/native dialogs, ribbon icon redesign,
docked panels, and model-operation changes are excluded. The five compiled
Gallery previews remain deferred under the separate Gallery plan.

Only the first delivery is authorized for implementation now: opt-in shared
foundations and the main template/Gallery preview. The owner reviews this
reference before propagation to other custom windows. Icon names/sizes belong
to the foundation; specific replacement artwork will be selected with the owner.

## Task ledger

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| GUI-01 | Confirm shared design and delivery boundary | Confirmed by owner | Interview: equal 24-unit chrome, Segoe UI, fixed button roles, normalized spacing, preserved placements, title ellipsis without tooltip |
| GUI-02 | Create shared shell, tokens, controls, and caller metadata | Implemented; locally verified | Host-free imports; no show/model side effects; existing resources/DataContext preserved; real WPF part bindings/events |
| GUI-03 | Apply foundation to main template and Gallery preview | Implemented; locally verified | Actual 432 x 576 renders; five fictional states; measured header/footer, padding, button dimensions/gaps; simulated navigation |
| GUI-04 | Review template appearance with owner | Ready for owner review | [First-delivery verification and renders](../knowledge/reviews/design-system/2026-10-27-custom-window-foundation.md) |
| GUI-05 | Migrate other Python custom windows | Waiting for GUI-04 | Review each window's body/lifecycle/callers before adopting the shell; preserve command operations |
| GUI-06 | Adopt foundation in compiled WPF adapters/windows | Waiting for GUI-04 | Share source design resources; preserve CLR/host boundaries; build and matching-host evidence required |
| GUI-07 | Select additional in-window artwork | Pending owner selection | Reuse existing Search asset initially; keep semantic keys and 16-unit default |
| GUI-08 | Live pyRevit/Revit acceptance | Pending host availability | Real ownership, keyboard/focus, drag, footer navigation, DPI/work-area and accessibility checks |

## Implementation boundaries and recovery

`KLCodeFoundation.xaml` is opt-in and merges the existing legacy dictionary
for its palette, vector wordmark, and scrollbars. Its new control styles have
explicit names. The legacy dictionary and production XAML/loaders are unchanged.
Removing remaining legacy resource dependencies is part of later migration,
not evidence that this delivery converted every control or host.

The Python adapter loads the shell and binds common events without importing
`GUI.forms`, pyRevit, or an active document. The shell's `Tag` holds
caller metadata; body `Content` and workflow `DataContext` remain caller-owned.
The caller explicitly shows the window and owns accept/cancel/persistence.

Rollback this delivery's opt-in resources, helpers, template, Gallery adapter,
probe/tests and linked documentation together. No data/model migration or
compiled asset replacement is involved. Extension/tool versions remain at
their existing unreleased values; this is not a release delivery.
