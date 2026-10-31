# UI Gallery

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.ui-gallery` |
| Tool version | `v0.5` |
| Status | Unreleased; isolated WPF verified; live Revit acceptance pending |
| Status/origin | Prototype; KL&A custom tool. |
| Main delivery | Unreleased |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototypes.pulldown/UI Gallery.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml`; `lib/ui_gallery/`; `lib/GUI/_templates/`; `lib/GUI/dialogs/`; `lib/GUI/Resources/KLCodeFoundation.xaml`; `lib/GUI/Resources/KLCodeFoundationTokens.xaml`; `lib/GUI/Resources/KLCodeComponents.xaml`; `lib/GUI/Resources/KLCodeCommandSwitch.xaml`; `lib/GUI/window_chrome.py`; `lib/GUI/window_metadata.py` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | 0.0.1.beta | 08.13.2026 | First main delivery of safe XAML cataloging and static previews. | 78b2aee |
| v0.1 | 0.0.4.beta | 08.17.2026 | Deliver seeded dialog previews, including rename, duplicate-sheet, and ViewRange examples. | 1f3dd23 |
| v0.2 | 0.0.5.beta | 08.20.2026 | Deliver additional prototype/room/recall previews and safe catalog launch permissions. | 8cd45f8 |
| v0.3 | 0.0.6beta | 09.15.2026 | Deliver expanded host picker and themed previews with repaired launcher/resource paths. | 300f8d4 |
| v0.4 | 0.0.11 | 10.12.2026 | Point rename previews to the promoted Core windows; retain the previous shared forms as labeled legacy previews. | Development promotion; pending owner merge to main. |
| v0.5 | Unreleased | 10.27.2026 | Add standalone inventory, origin labels, source column, tool callers, interactive states, faithful Recall, deferred compiled status, reference templates and shared-dialog family previews. | Gallery source and dated verification records; pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Shared dialog previews — 2026-10-29

The owner authorized reusable GUI windows and Gallery integration without
migrating actual tools. Six **Shared dialog** family rows exercise the actual
`lib/GUI/dialogs/` XAML bodies: Message, Selection, existing Action choice,
Text, Command Switch and KLC-Rename. Variant lists the available labels; a
dropdown beside State selects the preview. Search includes variant names, and
each family's variant and state are remembered for the session. Selection has
Sheets, Revisions, Open Documents, List Single and List Multiple. Message has
Without Details and With Details, each offering Normal, Empty, Warning, Error,
Success, Disabled and Long content; With Details retains diagnostics in Empty.
Command Switch has Commands only and Commands with toggles; KLC-Rename has
Single field, Two fields and Multiple fields (three groups). Other shared
variants retain Normal, Empty, Error, Disabled and Long content. Separate
confirmation and parameter-selection previews remain removed. These source
files are version inputs for this same unreleased v0.5 delivery.

These adapters use the real opt-in dialog factories and explicit result
contracts, with simulated footer navigation. No production tool class, query,
transaction or workflow is invoked. The existing pyRevit previews remain
available for comparison. The catalog contains 39 entries and 24 Window
sources, with five compiled previews still deferred.

The Form reference was removed by the owner. Options and Review now load
`KLC-OptionsTemp.xaml` and `KLC-ReviewTemp.xaml`; their stable preview IDs remain.
Create From Rooms and Match Recall keep their reviewed adapters while their
sources live under `lib/GUI/_future/`. Relocation does not adopt these dormant
windows into production commands.

The [dialog contract](../../../../lib/GUI/dialogs/SPEC.md) and
[API guide](../../../../lib/GUI/dialogs/README.md) own the reusable behavior;
the [consolidation plan](../../../../docs/plans/custom-window-consolidation.md)
owns this slice's tasks. [Verification](../../../../docs/knowledge/reviews/design-system/2026-10-29-shared-dialogs.md)
records actual WPF results and live-host limits.

The confirmed refinement uses explicit Select-button acceptance for both
checkbox modes, content-stable Message Details, a compact footerless Text
prompt with 36/24 Segoe UI Bold input, and a separate floating pyRevit-shaped
KLCode Command Switch with search, persistent toggles and neutral initial focus.
It has no corner x; Escape clears search and then cancels. The latter
returns fictional outcomes immediately; it never invokes a chosen command.
Action choice redesign is deferred and its window is unchanged. Read-only
Revit collectors exist for future caller adoption but are not run by Gallery.
[Refinement evidence](../../../../docs/knowledge/reviews/design-system/2026-10-29-dialog-refinement.md)
owns the new regression/render checks. The shared Command Switch dictionary
`lib/GUI/Resources/KLCodeCommandSwitch.xaml` is also a v0.5 version input.

The owner's subsequent polish uses template-sized 432 x 576 shared selectors,
Search above the aligned 24-high Group dropdown with Lucide Layers-2, centered
gray Select All/None above Select, and template section spacing. Text has one
OK action with 8-unit prompt/field/action gaps. Shared focus styles omit white
mouse-focus marks and disable the green focus adorner while retaining keyboard
operation. The selected/visible summary below shared selector lists is removed.
These previews
still use fictional data and do not adopt the dialogs in production tools.

## Purpose

Provide a visual review workspace for standalone windows used by this extension.
The owner approved this scope on 10.27.2026: interactive state previews, explicit
origin labels, and calling-tool lists, with production GUI fixes deferred.
Docked panels, overlays, progress bars, and balloon notifications are excluded.

The task authority is the [Gallery coverage plan](<../../../../docs/plans/ui-gallery-coverage.md>).
The [verification record](<../../../../docs/knowledge/reviews/design-system/2026-10-27-ui-gallery-verification.md>)
owns dated validation evidence and limitations.

## Behavior and GUI

Search by window name, variant label, source path, tool name, or calling-tool path. Filter by:

- Repository custom: windows supplied by this repository, including imported
  legacy forms and compiled WPF windows; this label does not assert authorship.
- pyRevit built-in: pyRevit's own WPF dialogs.
- Revit/Windows native: host/system dialogs, including native dialogs opened
  through pyRevit wrappers.

The **Preview** filter uses the catalog's current availability labels, such as
**Interactive preview**, **Deferred**, **Source unavailable**, and **Needs preview
adapter** when present. **All previews** resets it. Search, Origin, and Preview
combine; an empty intersection clears details and disables Open preview.
Availability filtering is separate from choosing a fictional preview state.

The legacy sheet/view rename forms were removed on 10.28.2026 at the owner's
request. Their Gallery entries and unused sheet wrapper were removed too.
The active Core rename commands retain their own command-local `Script.xaml`.

The table includes a **Window source** column showing the repository-relative
XAML path for custom windows (for example, `lib/GUI/SelectFromDict.xaml`) or the
API reference for built-in/native dialogs. Long values wrap and are available
in full on hover; columns can be resized and the table scrolls horizontally
when needed.

Click **Window source** to toggle ascending/descending order by its displayed
source/API value (`RelativePath`). Its wrapped template column explicitly sets
SortMemberPath so WPF enables header sorting, matching the bound text columns.

Select a window to see its description, source/API, calling tools with friendly
titles and command paths, and an explicit reason if its preview is unavailable.
The calling-tool list is built from source imports/calls, following shared helpers,
constructor XAML paths, class inheritance, configuration entry points, and
compiled command ownership without importing or executing the scanned code.
It describes statically reachable callers, not proof that every runtime branch ran.
Dynamic imports/getattr and parameterized routes can be unresolved. Templates,
retired forms, and orphaned library windows may have no current tool caller.

Choose a supported variant and state and **Open preview**. Custom previews load actual
repository XAML and resources with Gallery-owned handlers and fictional data.
Standard custom states are Normal, Empty, Error, Disabled, and Long content;
the shared Message dialog additionally offers Warning and Success.
The static fixture and Gallery shell offer Normal only. Controls support
filtering/checking, sample rename validation/results, duplicate options, numeric
validation, and local outcomes as applicable. No production command is invoked.

The separate Message and Selection templates and their XAML/controller/sample
branches are removed. The actual shared Message and Selection dialogs are the
canonical references and Gallery previews. Shared layout/component resources
used by production windows remain; no tool caller migrates in this cleanup.

The retained reference family is **Template - Form**, **Template - Options**
and **Template - Review**, each with five fictional states. They share the
shell, tokens and component styles. The generic FindReplace visual was adapted
into Form; actual Core rename commands retain their own windows.
See the [template family guide](../../../../lib/GUI/_templates/README.md) for
composition, interactions and source ownership. Browse uses fictional paths;
Form validates compact naming-rule fields without a Sample Preview, and Review
separates checked items from selected detail. Sample operations remain local.
The shared Message preview uses caller-selected severity and its corrected
Details/manual-size behavior; Warning/Success do not create duplicate windows.
KLC-Rename returns fictional rules or a separate field case action; it performs
no model operation or live before/after preview.
Review's Check All affects only eligible rows shown by the filter, preserving
hidden checks. Apply Checked validates the full checked collection. Clicking a
row updates details without checking it. Ready/Warning/Blocked chips center in
their Status cells; blocked rows remain unavailable for checking.

The nine Python tool previews now load their migrated source bodies through the
shared loader. Their canonical controls, operations and lifecycle remain
caller-owned. Caller discovery recognizes aliased `GUI.window_chrome.load_window`
calls, preserving tool lists after migration. Gallery also uses `load_window`,
the shared shell, `KlaDataGrid` and compact dropdown styles. Its header/footer
receive this command's title and version, and Escape follows the shared Close
policy. The static fixture retains its standalone test chrome. See the
[shared dialog guide](../../../../lib/GUI/dialogs/README.md) and
[consolidation plan](../../../../docs/plans/custom-window-consolidation.md).

Recall preserves the actual recall shell and hosts the standalone-specific
`clipboard_recall_content.xaml` UserControl inside `content_host`; its search,
selection, sample load, and
paste actions are local simulations. The production light/dark issue remains
visible. The Gallery does not fix or certify production GUI appearance.

pyRevit model-backed selectors reuse the actual shared list window with
fictional items. Parameter previews use the installed parameter item template
and All/Instance/Type groups; sheet previews include fictional sheet-set groups.
They do not query the current model or call the model-query wrappers.
Error picker data represents a fictional source issue; it does not execute an
actual failing model query.

Native file/folder/color pickers offer Normal only. They open actual picker
dialogs; returned paths/colors are discarded without reading/opening the chosen
file, writing files, or changing the model. Alerts, command switches, and text
prompts offer Normal, Error, and Long content. The command-link example opens an
actual Revit TaskDialog with fictional actions.

The catalog inventories every contained Window XAML source. New unregistered
windows are listed as **Needs preview adapter**, with opening disabled: discovery
never grants execution permission. The Model Checker
command remains on its own development branch until separately integrated; the
Gallery does not copy it onto this branch, and its former sample adapter was
removed on 2026-10-29 (discovery lists the source without a preview if it appears). Pages, UserControls, and resource
dictionaries do not become standalone entries.

## Deferred compiled previews

Owner decision on 10.27.2026: keep these five entries listed and disabled with
**Deferred** status, no selectable states, and a future-work explanation:

1. Family Studio.
2. Startup Importer source picker.
3. Startup Importer review.
4. Startup Importer blocking issues.
5. Shared compiled alert.

Working previews are future work, not a prerequisite for this delivery. Some
constructors are host-independent; their disabled status reflects this scope
decision and the absence of reviewed compiled preview integration. A future
change should reuse actual compiled views, provide sample providers/actions,
build the correct runtime assemblies, and validate in the matching Revit hosts.

## Implementation inventory

- `script.py`: thin pyRevit Gallery adapter, filtering, selection, and dispatch.
- `Gallery.xaml`: local layout, origin/preview filters, caller details, state selector.
- `lib/ui_gallery/launchers.py`: stable known dialog identities.
- `lib/ui_gallery/registry.py`: source inventory, origins, availability, and search.
- `lib/ui_gallery/callers.py`: host-independent static caller discovery.
- `lib/ui_gallery/scenarios.py`: deterministic fictional data and interactions.
- `lib/ui_gallery/template_data.py` and `templates.py`: reference identities,
  fictional fixtures, validation and safe presenters.
- `lib/ui_gallery/windows.py`: explicitly allowlisted custom-XAML preview handlers.
- `lib/ui_gallery/builtin.py`: real built-in/native dialog examples with discarded results.
- `scripts/validate_ui_gallery_wpf.ps1` and `.py`: isolated IronPython/WPF validation.
- `scripts/validate_ui_foundation_wpf.py`: reference-shell geometry, bindings,
  simulated actions/navigation, routed Close, and state-render checks.
- `scripts/validate_ui_templates_wpf.py`: 15 retained-template state layouts, sample
  interactions, generated checkbox bindings and minimum-size evidence.
- `scripts/validate_ui_production_wpf.py`: 45 production-window state layouts,
  compact naming fields, caller identity, localized Recall captions, overflow
  scrolling and the 18 vector icon roles.

## Model and external effects

No Revit transaction, production load/import/export, model selection/view
creation, clipboard persistence, database write, or external navigation is
performed by sample actions. Production footer navigation is suppressed in
custom previews. Native dialogs may keep their own ordinary host/OS UI state;
the Gallery discards their return values. Source scanning reads local repository
files only. The explicit validation script can save render evidence to its
chosen output directory.

## Compatibility and validation

Command paths remain IronPython 2.7 compatible. This implementation was checked
with installed pyRevit 6.5.3.26176+2017 form signatures and IronPython 2.7.12 on
.NET Framework 4.8. Do not copy upstream pyRevit XAML/assets into the extension;
the parameter preview loads the installed template at runtime.

Host-independent checks cover inventory, origins, callers, containment, state
fixtures, disabled compiled entries, and simulated interactions. The isolated
WPF probe uses real IronPython, WPF/resources/bindings, and custom handlers with
a minimal pyRevit loader/alert stand-in. It checks Gallery filters/selection and
constructs all existing custom/state combinations without showing a Window.
These checks do not establish real Revit ownership, input, DPI, Narrator, or
native-dialog integration. Live Revit acceptance remains pending.

Before promotion, open every supported family/state in the target Revit hosts.
Verify caller lists, origin filtering, empty results, keyboard dismissal,
selection/validation recovery, native-picker cancellation, and no production
side effects. Confirm five compiled entries remain disabled and arbitrary
discovered windows cannot launch.

## Future work

The plan owns task status. The deferred compiled-preview task is separate from
the current scope; docked panels and production GUI fixes require their own
scope decisions. The historical design-system review remains evidence for
production issues and is not superseded by this Gallery implementation.
