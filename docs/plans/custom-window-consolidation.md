# Custom window consolidation

Owner-approved design: 2026-10-27. Current work branch: `dev.GUI-Clean`.
The owner requested moving all local GUI commits off `master-dev` on 2026-10-27;
initial work was performed directly there under the earlier authorization.
This file owns task status. [DESIGNSYSTEM.md](../DESIGNSYSTEM.md) owns the
shared design rules; the [Selection template guide](../../lib/GUI/_templates/KLCodeSelectionTemplate.md)
owns the reference-window implementation and usage.

## Delivery boundaries

The full direction covers repository-owned standalone Python and compiled WPF
windows, with thin host adapters and shared presentation rather than shared
workflow inheritance. Preserve tool operations, modal/modeless lifecycles,
and existing action placement. pyRevit/native dialogs, ribbon icon redesign,
docked panels, and model-operation changes are excluded. The five compiled
Gallery previews remain deferred under the separate Gallery plan.

The first delivery introduced opt-in foundations and the Selection reference.
On 2026-10-28 the owner approved all five reference templates followed by
grilling to refine their elements. Current scope is reference construction and
review; propagation to production windows still waits for reference acceptance.
Icon names/sizes belong to the foundation; specific replacement artwork will
be selected with the owner.

## Task ledger

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| GUI-01 | Confirm shared design and delivery boundary | Confirmed by owner | Interview: equal 24-unit chrome, Segoe UI, fixed button roles, normalized spacing, preserved placements, title ellipsis without tooltip |
| GUI-02 | Create shared shell, tokens, controls, and caller metadata | Implemented; locally verified | Host-free imports; no show/model side effects; existing resources/DataContext preserved; real WPF part bindings/events |
| GUI-03 | Apply foundation to main template and Gallery preview | Implemented; locally verified | Actual 432 x 576 renders; five fictional states; measured header/footer, padding, button dimensions/gaps; simulated navigation |
| GUI-04 | Review template appearance with owner | Follow-up refinements implemented; ready for visual review | 8-unit top/bottom gaps, 14-unit Title Case prompt, native row hover; [current renders](../knowledge/reviews/design-system/2026-10-27-main-template-refinement.md); [initial delivery](../knowledge/reviews/design-system/2026-10-27-custom-window-foundation.md) |
| GUI-05 | Migrate other Python custom windows | Waiting for GUI-04 | Review each window's body/lifecycle/callers before adopting the shell; preserve command operations |
| GUI-06 | Adopt foundation in compiled WPF adapters/windows | Waiting for GUI-04 | Share source design resources; preserve CLR/host boundaries; build and matching-host evidence required |
| GUI-07 | Select additional in-window artwork | Pending owner selection | Reuse existing Search asset initially; keep semantic keys and 16-unit default |
| GUI-08 | Live pyRevit/Revit acceptance | Pending host availability | Real ownership, keyboard/focus, drag, footer navigation, DPI/work-area and accessibility checks |
| GUI-09 | Review remaining custom-window components and explain implementation | Reviewed; five template additions selected | [2026-10-28 review](../knowledge/reviews/design-system/2026-10-28-custom-window-components-review.md): 19 remaining windows at its baseline, migration risks and candidate primitives; Close label corrected; no production migration |
| GUI-10 | Create five shared reference templates | Implemented; locally verified | Owner approved all five on 2026-10-28; [family guide](../../lib/GUI/_templates/README.md), [verification](../knowledge/reviews/design-system/2026-10-28-template-family.md) |
| GUI-11 | Refine template elements with owner using grilling | Interview in progress | Selection keeps settled baseline; review new Form, Message, Options and Review decisions before production migration |

## Template refinement interview — 2026-10-28

Form round 1 owner answers:

- Keep labels in an aligned left column and keep the bordered field group.
- Remove the Sample Preview from Form. This supersedes the proposed live naming
  preview; preview row count/height is no longer applicable.
- Prefer the existing Core Find/Replace tools' field labels and input boxes.
  Settle their sizing and spacing before implementing the Form refinement.

Read-only isolated WPF measurement on baseline `51105f0`: both Views and Sheets
Find/Replace use Segoe UI 12, 200-wide inputs with Auto height realized as 17.96,
a 60-wide label column, and 4-unit gaps between input boxes. Form uses the same
font size with 32-high inputs, a 112-wide label column, and 8-unit row gaps;
its inputs stretch to 430 at the initial 600-wide window size. Both use input
padding `8,0` and a 1-unit border. Existing labels include a trailing colon.
These are isolated WPF measurements, not live pyRevit/DPI acceptance.

Form sizing confirmed by the owner: input height 24, label/input widths 60/240,
row gap 8, vertically centered colon labels, group inset 12. Implemented with
opt-in compact field styles and no Sample Preview; the reference starts at
360 x 352. [Verification and renders](../knowledge/reviews/design-system/2026-10-28-form-template-refinement.md)
cover actual geometry in all five states and retained validation/Reset actions.
Next interview frontier: Message, then Options and Review. Other template bodies
and production windows retain their current behavior during this interview.

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
