# Custom window consolidation

Owner-approved design: 2026-10-27. Current work branch: `dev.GUI-Clean`.
The owner requested moving all local GUI commits off `master-dev` on 2026-10-27;
initial work was performed directly there under the earlier authorization.
This file owns task status. [DESIGNSYSTEM.md](../DESIGNSYSTEM.md) owns the
shared design rules; the [shared dialog guide](../../lib/GUI/dialogs/README.md)
owns reusable Message/Selection usage, while the [remaining templates](../../lib/GUI/_templates/README.md)
own Form/Options/Review reference compositions.

## Delivery boundaries

The full direction covers repository-owned standalone Python and compiled WPF
windows, with thin host adapters and shared presentation rather than shared
workflow inheritance. Preserve tool operations, modal/modeless lifecycles,
and existing action placement. Existing pyRevit/native tool calls, ribbon icon redesign,
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
| GUI-08 | Live pyRevit/Revit acceptance | Pending owner review | Owner took the actual Revit review on 2026-10-29; [checklist and Windows evidence](../knowledge/reviews/design-system/2026-10-29-gui-architecture-windows.md) |
| GUI-09 | Review remaining custom-window components and explain implementation | Reviewed; five template additions selected | [2026-10-28 review](../knowledge/reviews/design-system/2026-10-28-custom-window-components-review.md): 19 remaining windows at its baseline, migration risks and candidate primitives; Close label corrected; no production migration |
| GUI-10 | Create five shared reference templates | Implemented; locally verified | Owner approved all five on 2026-10-28; [family guide](../../lib/GUI/_templates/README.md), [verification](../knowledge/reviews/design-system/2026-10-28-template-family.md) |
| GUI-12 | Architecture-review follow-ups | Source cleanup complete; Windows checks pass | Fixed URI assembly, compiled brush aliases, stale Browse style and Close placement; extracted seven naming groups/four filtered lists; Gallery uses shared shell; generated wordmark matches former renderer pixel for pixel. [Evidence and remaining owner decisions](../knowledge/reviews/design-system/2026-10-29-gui-architecture-windows.md). GUI-08 remains separate. |
| GUI-13 | Restore the practical design-system reference | Implemented; documentation verified | Current color/role tables, GUI icon rendering choices/examples, ribbon conventions, component/typed-spacing selection and accurate host/keyboard/validation boundaries in [DESIGNSYSTEM.md](../DESIGNSYSTEM.md). Relocated archive links repaired. |
| GUI-14 | Align host and default-action keyboard contracts | Pending implementation | pyRevit's existing Escape handler can close before the shared caller policy; Find/Replace Views, Find/Replace Sheets and Steel PSF omit IsDefault on main actions. Current limits are documented in the [host/keyboard contracts](../DESIGNSYSTEM.md#host-and-keyboard-contracts); fixing these behaviors is separate from the reference restoration. |
| GUI-15 | Restore original footer text colors | Implemented; Windows verified | Owner requested original green links (#407058) and gray version (#808080). Dedicated KlaFooterLinkBrush/KlaFooterVersionBrush roles affect the shared shell. 32 GUI tests, 17 C# source tests, 71 WPF constructions and both compiled-runtime smokes pass, including independent RGB assertions. [Python render](../knowledge/reviews/design-system/2026-10-29-footer-color-evidence/selection.png); [compiled render](../knowledge/reviews/design-system/2026-10-29-footer-color-evidence/compiled-source-picker.png). Packaged DLLs unchanged. |
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

Current inventory is 25 Window sources: three references, nine Python tool
windows, six opt-in dialog bodies, five compiled windows, the shared-shell
Gallery and the PreviewFixture tooling exception.
The nine Python and five compiled windows are the production/tool migration
scope. Gallery remains the review harness; its previews and source/caller
inventory must follow migrated sources. Only its static fixture retains test
chrome. The absent Model Checker source and five deferred compiled Gallery
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
Recall's docked body/resources remain unchanged for excluded consumers. The
unused legacy `WPF_styles.xaml` was retired in the architecture pass. Gallery
uses the shared shell; its static fixture retains standalone test chrome.

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

## Opt-in reusable dialogs — authorized 2026-10-29

The owner approved new reusable windows and GUI-system integration, explicitly
excluding migration of existing tools. Use KLCode requirements, implementation,
interface-development and test-first workflows. The library's acceptance
contract lives in [GUI/dialogs/SPEC.md](../../lib/GUI/dialogs/SPEC.md).

| ID | Slice | Status | Evidence / completion condition |
| --- | --- | --- | --- |
| GUI-16 | Host-free results and selection models | Implemented; verified | First duplicate-label/hidden-check test failed for missing library, then passed. Ten model/import tests cover host-free import, single selection, hidden checks, cancellation, validation and bad keys. |
| GUI-17 | Message, selection, choice and text windows | Implemented; Windows verified | Four bodies reuse the shell/resources, with explicit results and lazy factories. Actual WPF layouts/actions and inspected normal/minimum/long/error renders pass. |
| GUI-18 | Gallery and practical API documentation | Implemented | Six variants, five states each; API guide, design reference and Gallery SPEC updated. Production calls and existing reference templates preserved. |
| GUI-19 | Verification and review evidence | Local checks complete; owner host review pending | [Evidence](../knowledge/reviews/design-system/2026-10-29-shared-dialogs.md): Python suite, actual IronPython/WPF layouts/actions, both compiled runtimes, source-scope self-review and inspected renders. Live Revit review stays owner-owned. |

File/folder/color pickers, progress/selection overlays, Revit queries, current
CustomAlert/SelectFromDict contracts and packaged DLLs remain outside this slice.
GUI-14's existing-tool keyboard issues remain separate. No production adoption
or release/version delivery is implied by adding the new dialog APIs.

## Shared dialog refinement interview

The owner next requested removal of separate Confirmation and Parameter
selection entries, a KLCode grilling review of the remaining dialogs, sheet,
revision, open-document and single/multiple list selectors, plus a command
switch matching pyRevit's visual layout with KLCode colors. Production tool
migration remains excluded. Historical six-variant evidence above records the
initial delivery; this phase changes the current catalog.

| ID | Slice | Status | Decision / completion condition |
| --- | --- | --- | --- |
| GUI-20 | Remove two Gallery variants | Implemented; locally verified | Confirmation/parameter entries and sample branches removed. 65 Gallery tests (one existing skip), 20 remaining dialog state layouts at normal/minimum sizes, and 91 custom/state WPF constructions pass; current catalog is 40 entries. Four bodies and message/selection APIs retained. |
| GUI-21 | Refine remaining dialog/selector/switch design | Confirmed by owner | Owner explicitly said "confirmed, implement" after the final design summary. No further design approval gate for this scope. |
| GUI-22 | Rework Action choice independently | Future; explicitly deferred by owner | Preserve the existing Action choice window/API. No layout or interaction changes in the current selector/message/text/command-switch delivery. Revisit as its own design effort. |
| GUI-23 | Refine Message, Text and shared selector interactions | Implemented; locally verified | Details growth/manual-height regression, repeated expansion, footer isolation, exact 36/24 Segoe UI Bold field, unclipped validation and explicit Select pass in actual WPF. [Evidence](../knowledge/reviews/design-system/2026-10-29-dialog-refinement.md). |
| GUI-24 | Read-only collectors and five selector presets | Implemented; boundary tested | Eleven collector tests, SDK/API checks, host-free imports and prepared-row/modal helpers pass. Five fictional Gallery presets verified. Actual Revit model collection remains owner acceptance. |
| GUI-25 | Separate floating Command Switch | Implemented; locally verified | Seven model tests plus real-WPF construction, minimum/long layouts, filtering/toggle clones/results/Close/Escape handler checks pass. Actual focus/keyboard/owner remains live acceptance. |
| GUI-26 | Documentation, independent review and verification | Local verification complete; owner host review pending | 380 Python tests (one existing skip), 17 C# tests, 116 WPF constructions/45 shared-dialog state layouts, both compiled runtimes, independent review, inspected renders, source-scope review and documentation audit pass. [Record and host limits](../knowledge/reviews/design-system/2026-10-29-dialog-refinement.md). |

Settled: remove the two separate previews; retain Message, Selection, Action
choice and Text for refinement; add the requested selector types and a separate
KLCode command switch. Round 1 decisions below supersede the initial proposals.
Per-dialog refinements remain open. Collector defaults are settled in Round 2.
Interview outcomes
will be implemented after the complete design is confirmed as settled.

Inspected reference: installed pyRevit 6.5.3 IronPython forms, under
`%APPDATA%/pyRevit-Master/pyrevitlib/pyrevit/forms/`. `_ipy.py` owns
SelectFromList (1024), CommandSwitchWindow (1523), select_revisions (2434),
select_sheets (2487), select_open_docs (2827); associated XAML owns layout.
No upstream implementation/assets are copied by this review.

Design tree / settled Round 1 answers:

| Question | Owner decision | Next dependent decisions |
| --- | --- | --- |
| Q1: Selector family | Yes: one shared foundation with Sheets, Revisions, Open Documents, List Single and List Multiple presets; optional groups | Common search, domain labels/order/eligibility, layout |
| Q2: Selection interaction | Single retains the same checkbox style, with at most one checked row. No double-click or Enter acceptance; use Select. Multiple returns checked rows only, preserving checks across groups/filtering | Multiple acceptance keys, visible batch controls, required/optional defaults |
| Q3: Host/data boundary | Yes: host-free windows plus separate read-only Revit collectors. Gallery stays fictional and existing tools keep their current calls | Collector defaults/API details |
| Q4: Action choice relationship | No to replacement: retain Action choice and add Command Switch as a separate dialog | Refine each dialog's distinct layout/behavior |
| Q5: Switch presentation | Yes: pyRevit-style compact floating panel, prompt/search and wrapping immediate-choice buttons in KLCode colors; exception to standard header/footer | Optional toggles, access keys, keyboard/filter behavior |

Rejected proposals: highlighted-row single selection, double-click/Enter
acceptance for single selection, and replacement of Action choice. These are
not implementation requirements. Single selection should uncheck a previous
row when a new row is checked, including a previous check hidden by filtering.
The current selector has IsDefault=True on Select; the implementation phase
must correct that contract for both modes and prevent Enter acceptance.

Design tree / settled Round 2 answers (all recommendations accepted):

| Question | Owner decision | Consequence |
| --- | --- | --- |
| Q1: Multiple acceptance | Single and multiple match except for one/many checked rows; both require Select, with no Enter/double-click acceptance | Retain shared checkbox layout and explicit acceptance policy; batch actions remain meaningful only for multiple mode |
| Q2: Search and batch scope | Case-insensitive label/description search; no fuzzy ranking or regex. All/None touches visible eligible rows only | Preserve hidden checks and source order |
| Q3: Sheets | Sheet number/name labels, sorted by sheet number; All Sheets plus sheet-set groups. Exclude placeholders by default, with caller option to include them | Apply eligibility consistently in every group and return each sheet once |
| Q4: Revisions | Number, description, date and issued status; sequence order. Include issued/unissued unless caller restricts eligibility | Read-only collector prepares labels/order/eligibility |
| Q5: Open documents | Exclude links/active document by default; include project/family documents. Secondary type/path information distinguishes duplicate titles | Expose caller inclusion options without changing stable payload identity |
| Q6: Command-switch toggles | Support optional on/off switches and return their states with chosen command | Resolve filtering/keyboard/dismissal behavior next |

Next independent frontier: Message presentation/button scope; Text compactness
and acceptance; Action choice layout/acceptance; floating command-switch
keyboard, filtering of optional toggles and visible cancellation. Existing
renders and actual XAML/controllers were inspected before asking this round.
No runtime code changes have been made from these interview answers.

Design tree / Round 3 answers:

| Question | Owner decision | Remaining dependency |
| --- | --- | --- |
| Q1: Message | Yes: OK-only notice, severity icon/heading, wrapping, optional collapsed Details and bounded content fitting. Owner reports current behavior is glitchy | Identify the observed glitch before choosing a sizing/interaction fix; do not claim a reproduced cause |
| Q2: Text | Yes to compact text prompt/inline validation/Cancel-OK/Enter acceptance/Escape cancellation. Increase input size to resemble pyRevit; remove "klcode fitter" | Interpret "fitter" as footer, pending confirmation; settle larger-field presentation |
| Q3: Action choice | Rework independently later | GUI-22 is a future item; leave the current dialog/API unchanged now |
| Q4: Switch keyboard | Yes: typing filters, Tab traverses controls, Space toggles; Enter chooses focused command or sole matching command while search is focused. Escape clears search, then cancels when empty | Implement after settled-design confirmation |
| Q5: Switch toggle filtering | Yes: toggles stay visible while command buttons filter; preserve toggle states | Implement after settled-design confirmation |
| Q6: Switch cancellation | Yes: small corner x for visible cancellation; clicking blank panel space keeps the window open | Implement after settled-design confirmation |

Reference inspected for Text: installed GetValueWindow.xaml lines 181-189 uses
a 36-unit-high input, FontSize=24 bold centered Courier New text, one line, and no
Return/Tab insertion. Current KLCode Text uses a 32-unit input and the body font
size. Proposed adaptation: match the larger 36/24 proportions and centered bold
text while retaining KLCode Segoe UI and colors; this is not yet accepted.

Message source inspection: MessageWindow.message_size_changed refits height
whenever WidthChanged is true; details_changed also refits height via
window_chrome.fit_window_height. This is a candidate for resize instability,
not proof of the owner's unspecified glitch. Existing offscreen layout evidence
does not establish glitch-free live resizing/expansion.

Design tree / settled Round 4 clarifications:

- Text: "fitter" means footer. Remove its Prototype/version/Outreach row while
  retaining title and Close. Input uses the larger 36-high/FontSize=24 centered
  proportions, specifically Segoe UI Bold and KLCode colors.
- Message: owner observes jumping/flickering while resizing; expanding Details
  hides the message instead of growing the bottom of the window.

Sizing diagnostic, performed against the existing real WPF controls without
source changes, visible windows or Revit: a short message initially measured
Window.Height=240 and message_banner.ActualHeight=101. Expanding Details kept
Height=240 while message_banner shrank to 26 and details measured 128. A direct
width-handler dispatch after manually assigning Height=400 reset Height to 344.
This reproduces the hidden-message/forced-height behavior; it does not establish
live pointer-driven flicker. The first diagnostic lacked WPF initialization
before importing Size; after importing wpf first, the diagnostic completed.

## Final refinement design — confirmed for implementation

The proposed delivery implements the recorded choices above, with these
concrete behavior/verification conditions:

1. Five named selector presets (Sheets, Revisions, Open Documents, List Single,
   List Multiple) share checkbox styling/layout. Single permits one check;
   multiple permits many. Select explicitly accepts; Enter and double-click
   never accept either mode. Hidden checks, stable payload identity and ordering
   remain intact; visible All/None is applicable only to multiple mode.
2. Case-insensitive label/description search preserves input order. Sheets use
   number/name order, All Sheets/sheet-set groups and consistent placeholder
   filtering. Revisions show number/description/date/issued state in sequence
   order. Documents default to excluding links/active document while including
   project/family documents, with type/path descriptions. Separate collectors
   only read Revit; imports/windows remain independent of the active document.
3. Message is OK-only, retaining severity and optional collapsed Details. Fit
   initially; manual resizing must not trigger forced height feedback. Details
   grows downward while retaining the message viewport until the existing cap
   is reached, when both contents remain available through bounded scrolling.
   Regression checks must cover the measured 101-to-26 shrink and manual-height
   replacement, repeated expansion/collapse, width changes and capped overflow.
4. Text fits its content, has the larger single-line Segoe UI Bold field,
   inline validation and Cancel/OK; Enter accepts, Escape cancels. Remove only
   its footer row; retain title/Close and preserve raw/accepted-empty semantics.
5. Add a separate pyRevit-shaped floating Command Switch in KLCode colors,
   without the standard shared header/footer. Wrapping command buttons choose
   immediately; optional toggles stay visible and retain state while commands
   filter. Typing searches, Tab traverses, Space toggles; Enter chooses focused
   command or a sole match while search is focused. Escape clears search then
   cancels; corner x cancels; blank panel clicks do not dismiss. Return stable
   choice keys and switch states without running caller operations.
6. Gallery uses actual new/refined windows with fictional state coverage. Update
   SPEC/API/design references and verify host-free logic, real WPF behavior and
   inspected normal/minimum/long/error renders. Native Revit collectors, owner,
   modal/focus/keyboard and DPI need clearly bounded host evidence; the owner
   retains live Revit review. No packaged DLL or production command adoption.

Action choice redesign is explicitly deferred under GUI-22 and remains
unchanged. Separate Confirmation/Parameter previews remain deleted. Existing
tools, native pickers/progress overlays and unrelated GUI-14 work remain outside
this delivery. The owner confirmed this final design and requested implementation.
Runtime changes began only after that confirmation. Earlier "pending" statements
above describe the recorded interview stage rather than a current approval gate.

Useful inspected facts for subsequent rounds: sheet selector uses All Sheets and
sheet sets, sorted sheet numbers; revisions follow SequenceNumber without an
automatic issued/unissued exclusion; open documents excludes links and normally
the active document, without explicitly excluding family documents. Generic
pyRevit search supports fuzzy ranking/regex; these are optional behavior choices.
The floating command switch supports optional toggles, keyboard filtering and
immediate command choices; it has no separate Continue button.

## Owner dialog polish — 2026-10-29

The owner's latest direct feedback supersedes the earlier visible Cancel/
corner-x/initial-focus decisions for Text, Selection and Command Switch.
It also authorizes removing persistent white button/check focus decorations
through the shared GUI system. No new interview gate applies to these explicit
requests; Action choice redesign remains deferred under GUI-22.

| ID | Scope | Status | Acceptance / evidence |
| --- | --- | --- | --- |
| GUI-27 | Text, Selection and Command Switch polish | Implemented; locally verified | Text has 8-unit prompt/input/action gaps and OK only. Selector starts at 432 x 576, follows template spacing/button layout, uses gray batch buttons, Search above a 24-high aligned Group field and licensed Lucide Layers-2. Switch has no x/autofocus and keeps typing/Tab/Escape. Exact WPF bounds and two shown focus fixtures pass. |
| GUI-28 | Shared focus decoration | Initial implementation superseded by GUI-29 | Initial green keyboard-only adorner passed local checks, then owner requested its removal. See GUI-29 for current behavior. |
| GUI-29 | Remove focus frames and selector summary | Implemented; locally verified | Owner rejected the green frame and selected/visible text. Shared button/check/radio/toggle FocusVisualStyle is null; controls stay keyboard operable. Summary/control-update code removed; validation and 8-unit action spacing retained. 383 Python tests (one existing skip), 15 WPF focus roles, 116 constructions, two shown focus fixtures and both compiled runtimes pass. [Evidence](../knowledge/reviews/design-system/2026-10-30-focus-summary-cleanup.md). |
| GUI-30 | Retire duplicate Message/Selection templates | Implemented; locally verified | Shared dialogs are canonical; both duplicate XAML sources and Gallery controllers removed. Form/Options/Review remain. Shared Message adds Warning/Success previews. Gallery integration and evidence are owned by GAL-10 in the [Gallery ledger](ui-gallery-coverage.md). |

[Polish verification and renders](../knowledge/reviews/design-system/2026-10-29-dialog-polish.md)
own the dated evidence. The main Gallery/WPF probe remains offscreen by default;
`-ShowFocusProbe` separately shows and closes two owned fictional windows.
Physical keyboard/pointer/DPI and Revit owner/model acceptance remain bounded
host checks. Compiled source/smoke verification does not replace deployed DLLs.

## Shared window variants interview — 2026-10-30

The owner requested KLCode grilling before implementing this broader slice.
This plan remains its task/decision authority; Gallery behavior changes will
also update its adjacent SPEC. The owner confirmed the settled design and
authorized implementation after resolving the final case-action question.

Settled first-round choices:

- Message has Without Details and With Details variants using one shared base.
  Without Details retains current sizing/resizing and OK. Both offer Normal,
  Empty, Warning, Error, Success, Disabled and Long content. With Details/Empty
  retains sample diagnostics while the message body is empty.
- Severity heading and icon match the outline color. Body text keeps its normal
  color. Apply the new icons only to shared Message: Lucide octagon-alert,
  triangle-alert, info and check-check for error/warning/information/success;
  Details uses chevron-right when collapsed and chevron-down when expanded.
- Severity icons increase from 16 to 24; severity headings increase from 14 to
  18, Segoe UI SemiBold. Details chevrons retain the normal small 16-unit size.
  Body/details text remains 12. Align expanded Details text horizontally with
  the main body text and vertically center the severity icon beside its heading.
- Gallery has one row per shared window family. Variant lists available labels;
  a dropdown beside State selects the preview. Search includes variant labels;
  remember family variant/state for the current session. Selection contains
  Sheets, Revisions, Open Documents, List Single and List Multiple variants.
- Command Switch variants are Commands only and Commands with toggles,
  preserving current visuals and keyboard behavior.
- KLC-Rename is one shared base with caller-defined property groups, each with
  one Find/Replace pair plus Prefix/Suffix. Multiple sequential replacement rules
  on one property are outside this interpretation.
- KLC-Rename supports exactly one, two or three groups, arranged horizontally;
  Gallery offers Single field, Two fields and Multiple fields (three groups),
  each with the same five standard preview states. No wrapping groups vertically.
- Uppercase/Lowercase controls are optional per property group. These remain
  separate actions, returning the operation and property key and closing the
  dialog without applying Find/Replace/Prefix/Suffix rules.
- Rename accepts entered rules and returns them to its caller; no live
  before/after preview or model operation occurs in this shared dialog.
  Enter activates Rename; invalid rules stay open with inline validation.
  Close/Escape cancels. Retain the standard shared header/footer.
- Continue opt-in shared windows and fictional Gallery previews; do not migrate
  production tools in this delivery.

Read-only agents inspected Gallery grouping, current shared/rename contracts
and official Lucide candidates before the interview. All choices above are
settled. No further interview approval gate applies to routine implementation.

| ID | Delivered behavior | Dependencies / scope | Status / evidence |
| --- | --- | --- | --- |
| GUI-31 | Family/variant Gallery rows, picker, search and session choices | Registry, explicit adapter allowlist, Gallery UI and existing SPEC | Implemented; locally verified. 40 rows; variant/state memory, category/variant search, direct-family result handling and both source/Variant UIA sorting pass. |
| GUI-32 | Message variants, severity presentation and aligned Details | Existing Message base, message-only icon roles, canonical pinned Lucide assets | Implemented; locally verified. Both seven-state variants, severity sizes/colors, actual text edges, disclosure/copy/scroll/resize checks pass. |
| GUI-33 | KLC-Rename shared base and 1/2/3-group variants | Caller-owned fields, pure validation/results, lazy public API; Gallery integration follows GUI-31 | Implemented; locally verified. 15 layouts, cloned inputs/results, separate case actions, validation/minimum-height recovery, disabled guard and keyboard/cancel paths pass. |
| GUI-34 | Integrated review, documentation and local milestone | GUI-31/32/33; owning SPEC/API/design references | Locally verified; 399 Python tests (one existing skip), 135 WPF constructions, 17 compiled source tests and both runtime smokes pass. Independent findings fixed and rechecked. [Evidence](../knowledge/reviews/design-system/2026-10-30-shared-window-variants.md). Existing production calls and packaged DLLs remain untouched; live Revit acceptance stays owner-owned. |
