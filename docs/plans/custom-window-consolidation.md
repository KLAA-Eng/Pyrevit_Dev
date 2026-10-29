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
review. After the first refinement pass, the owner requested icon selection
followed by production migration. The settled reference choices are the baseline
for that next phase; do not request the migration authorization again.
The owner subsequently approved all icon choices and their location under
`lib/_icons/gui/`. Source migration is implemented; local evidence and remaining
host/build limits are recorded in the
[production migration review](../knowledge/reviews/design-system/2026-10-29-production-migration.md).

## Task ledger

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| GUI-01 | Confirm shared design and delivery boundary | Confirmed by owner | Interview: equal 24-unit chrome, Segoe UI, fixed button roles, normalized spacing, preserved placements, title ellipsis without tooltip |
| GUI-02 | Create shared shell, tokens, controls, and caller metadata | Implemented; locally verified | Host-free imports; no show/model side effects; existing resources/DataContext preserved; real WPF part bindings/events |
| GUI-03 | Apply foundation to main template and Gallery preview | Implemented; locally verified | Actual 432 x 576 renders; five fictional states; measured header/footer, padding, button dimensions/gaps; simulated navigation |
| GUI-04 | Review template appearance with owner | Follow-up refinements implemented; ready for visual review | 8-unit top/bottom gaps, 14-unit Title Case prompt, native row hover; [current renders](../knowledge/reviews/design-system/2026-10-27-main-template-refinement.md); [initial delivery](../knowledge/reviews/design-system/2026-10-27-custom-window-foundation.md) |
| GUI-05 | Migrate other Python custom windows | Implemented; locally verified | All nine tool windows use shared shell/components; 45 actual WPF state layouts and focused workflow contracts pass; [migration evidence](../knowledge/reviews/design-system/2026-10-29-production-migration.md) |
| GUI-06 | Adopt foundation in compiled WPF adapters/windows | Source implemented; runtime layout verified; host build limitation recorded | All five classes construct on net48/net8.0-windows using canonical linked resources; full Family Studio 2025 build blocked by installed API/System.Runtime mismatch; packaged DLLs unchanged; compiled Gallery previews remain deferred |
| GUI-07 | Select additional in-window artwork | Owner approved; implemented | 17 pinned Lucide roles under lib/_icons/gui; 16-unit default, 1.5 stroke, semantic geometry/ImageSource keys, source/license attribution and generation check |
| GUI-08 | Live pyRevit/Revit acceptance | Pending host availability | Real ownership, keyboard/focus, drag, footer navigation, DPI/work-area and accessibility checks |
| GUI-09 | Review remaining custom-window components and explain implementation | Reviewed; five template additions selected | [2026-10-28 review](../knowledge/reviews/design-system/2026-10-28-custom-window-components-review.md): 19 remaining windows at its baseline, migration risks and candidate primitives; Close label corrected; no production migration |
| GUI-10 | Create five shared reference templates | Implemented; locally verified | Owner approved all five on 2026-10-28; [family guide](../../lib/GUI/_templates/README.md), [verification](../knowledge/reviews/design-system/2026-10-28-template-family.md) |
| GUI-12 | Architecture-review follow-ups | Implemented on dev.GUI-Clean; WPF render pending | Shell correctness (db919d4), dead weight (53dd182), template pass (d9830dc), tokens and scale lint (c7f1160), icons and wordmark (4283862), chrome data (28c96f7), contrast / aliases / caching / docs (this commit); `check_ui_scale.py` reports consumer margins; the review page lists what remains |
| GUI-11 | Refine template elements with owner using grilling | Settled choices implemented; locally verified | Selection baseline retained; accepted Form, Message, Options, Review and icon choices implemented; final owner/live-host acceptance remains pending |

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
Follow-up: owner requested Edit Naming Rules match Selection's Select Elements
styling. Implemented with the exact same prompt Label style, including normal
weight. The field geometry stays settled.

Message round 1: owner confirmed content-fitting height with bounded overflow
scrolling, Details initially collapsed even for errors, and stable text colors
with heading/border severity distinctions. Implemented with an opt-in shared
height-fit helper. Review defaults: minimum 288, maximum 640; opening its Details
readout raises the minimum to 424. [Verification and renders](../knowledge/reviews/design-system/2026-10-28-message-template-refinement.md)
cover growth/shrinkage, cap/scrolling, width refit, expanded Details and prompt
styling. Next interview frontier: Options, then Review. Production windows retain
their current behavior during this interview.

Options round 1: owner accepted 24-high dropdown/offset/path fields and the
shared Selection/Form prompt style. Implemented those independent choices
using opt-in shared styles, with centered field labels. The follow-up settled
the remaining choices: use Form's 60-unit label column and replace the toggle
with a self-labelled Include Existing checkbox. Implemented using the existing
shared column token and checkbox style. Offset's unit moved beside its input
so the label fits without clipping. No production windows were changed.

Partial Options verification: Gallery 63 run/62 passed/1 skipped; actual WPF
25 template states, normal interactions, minimum-size renders and 71 custom/
state constructions passed. All five Options states measure the three fields
at height 24 and both prompts resolve the exact shared style, size 14, normal
weight. The [earlier partial render](../knowledge/reviews/design-system/2026-10-28-template-family-evidence/template-options-compact-fields.png)
retains the former label column/toggle for historical comparison.

Final Options verification: the same Gallery and WPF suites pass after the
follow-up. All five states measure a 60-unit label column and use the actual
Include Existing CheckBox. Checked/unchecked feedback and disabled text pass;
Normal, Disabled and minimum-size renders were inspected.
[Current render](../knowledge/reviews/design-system/2026-10-28-template-family-evidence/template-options-confirmed.png).
Live input/DPI acceptance remains pending.

Review round 1: owner confirmed separate checked/selected rows, the right-hand
detail pane and resizable divider, visible-only Check All, and labelled
Ready/Warning/Blocked chips with blocked rows unavailable for checking. The
owner additionally requested centering chips in the column. Implemented an
opt-in Status-cell alignment style and filtered-only checking with hidden
checks preserved. Selected rows are brought into view after filtering; Apply
Checked still validates all checked rows. The summary makes visible/total
counts and Check All scope explicit.

[Review verification and renders](../knowledge/reviews/design-system/2026-10-28-review-template-refinement.md)
cover actual chip centers, blocked/disabled checkboxes, selected-versus-checked
behavior, hidden-check preservation, empty filters and filtered-row visibility.
This completes the first refinement pass across the five reference templates.
The following phase implemented owner-approved artwork and production source
migration. Live-host acceptance remains a separate task.

## Icon selection and authorized migration sequence

On 2026-10-28 the owner requested icon selection, then production migration,
and supplied `https://lucide.dev/icons/`. Lucide is the selected family. The
[review package](../knowledge/reviews/design-system/2026-10-28-icon-selection/README.md)
contains actual inventory, 17 attributed source candidates and a WPF-rendered
sheet. The owner approved every proposed mapping, 1.5 stroke, applicable message
symbols, retained word/border status chips and text-only larger actions. The
canonical implementation is `lib/_icons/gui/`; the candidate package remains
historical evidence. Fixed 128 x 28 icon/text buttons accommodate Recall's
English, German and Korean captions without fitting buttons to text.

The following source batches are implemented on `dev.GUI-Clean` under the
existing authorization:

1. Shared modal Python windows: CustomAlert, SelectFromDict, CreateFromRooms and
   DuplicateSheets. Preserve nested checkbox content/handler contracts and each
   tool's filtering, confirmation and close policy.
2. Core Find/Replace Views and Sheets, then Steel PSF. Preserve named controls,
   one/two naming groups, outcomes, case actions and CSV action placement.
3. Modeless View Range and standalone Recall. Preserve Revit event cleanup,
   persistence and ownership; Recall's shared docked consumer needs isolation
   or compatible resources, not an accidental docked redesign.
4. Compiled shared alert, Family Studio, Startup source picker/review/blocking
   issues. First make resource packaging compatible with CLR/localization
   adapters; build supported targets and retain honest matching-host limits.

Current inventory is 21 Window sources: five references, nine Python tool
windows, five compiled windows, and Gallery/PreviewFixture tooling exceptions.
The nine Python and five compiled windows are the production/tool migration
scope. Gallery remains the review harness; its previews and source/caller
inventory must follow migrated sources. Its own shell/fixture are tooling
exceptions. The absent Model Checker source and five deferred compiled Gallery
previews are not silently replaced with invented implementations.

Read adjacent command SPECs and trace actual callers before each batch; use the
existing component review as a risk map, not as permission to alter workflows.
Verify shared resources, focused command contracts and actual WPF bounds/states;
keep live ownership, input, Revit operations and DPI acceptance explicit.
Make local verified milestone commits. No release/version change or remote
publication is part of this request.

## Implementation boundaries and recovery

`KLCodeFoundation.xaml` merges event-free `KLCodeSharedPrimitives.xaml` for the
canonical palette, vector wordmark, footer links and scrollbars. Explicit
control styles are shared by Python windows and compiled resource aliases.
Legacy `WPF_styles.xaml` and Recall's docked body/resources remain unchanged for
excluded consumers. Gallery's own shell/fixture remain tooling exceptions.

The Python adapter loads the shell and binds common events without importing
`GUI.forms`, pyRevit, or an active document. The shell's `Tag` holds
caller metadata; body `Content` and workflow `DataContext` remain caller-owned.
The caller explicitly shows the window and owns accept/cancel/persistence.

Rollback shared resources, both adapters, migrated window bodies, Gallery
previews, probes/tests and linked documentation together; the consumers depend
on the new shared keys. No data/model migration or packaged compiled asset
replacement is involved. Extension/tool versions remain unchanged; this is not
a release delivery. The local source/build checks do not close GUI-08 or the
separate compiled-tools host acceptance plan.
