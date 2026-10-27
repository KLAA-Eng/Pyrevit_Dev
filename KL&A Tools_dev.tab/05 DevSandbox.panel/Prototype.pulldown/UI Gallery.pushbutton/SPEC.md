# UI Gallery

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.ui-gallery` |
| Tool version | `v0.5` |
| Status | Unreleased; isolated WPF verified; live Revit acceptance pending |
| Status/origin | Prototype; KL&A custom tool. |
| Main delivery | Unreleased |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototypes.pulldown/UI Gallery.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml`; `lib/ui_gallery/`; `lib/GUI/_templates/`; `lib/GUI/Resources/KLCodeFoundation.xaml`; `lib/GUI/Resources/KLCodeFoundationTokens.xaml`; `lib/GUI/window_chrome.py`; `lib/GUI/window_metadata.py` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | 0.0.1.beta | 08.13.2026 | First main delivery of safe XAML cataloging and static previews. | 78b2aee |
| v0.1 | 0.0.4.beta | 08.17.2026 | Deliver seeded dialog previews, including rename, duplicate-sheet, and ViewRange examples. | 1f3dd23 |
| v0.2 | 0.0.5.beta | 08.20.2026 | Deliver additional prototype/room/recall previews and safe catalog launch permissions. | 8cd45f8 |
| v0.3 | 0.0.6beta | 09.15.2026 | Deliver expanded host picker and themed previews with repaired launcher/resource paths. | 300f8d4 |
| v0.4 | 0.0.11 | 10.12.2026 | Point rename previews to the promoted Core windows; retain the previous shared forms as labeled legacy previews. | Development promotion; pending owner merge to main. |
| v0.5 | Unreleased | 10.27.2026 | Add standalone inventory, origin labels, source column, tool callers, interactive states, faithful Recall, deferred compiled status, and the shared main-template reference. | Gallery source/tests and the 2026-10-27 verification records; pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Purpose

Provide a visual review workspace for standalone windows used by this extension.
The owner approved this scope on 10.27.2026: interactive state previews, explicit
origin labels, and calling-tool lists, with production GUI fixes deferred.
Docked panels, overlays, progress bars, and balloon notifications are excluded.

The task authority is the [Gallery coverage plan](<../../../../docs/plans/ui-gallery-coverage.md>).
The [verification record](<../../../../docs/knowledge/reviews/design-system/2026-10-27-ui-gallery-verification.md>)
owns dated validation evidence and limitations.

## Behavior and GUI

Search by window name, source path, tool name, or calling-tool path. Filter by:

- Repository custom: windows supplied by this repository, including imported
  legacy forms and compiled WPF windows; this label does not assert authorship.
- pyRevit built-in: pyRevit's own WPF dialogs.
- Revit/Windows native: host/system dialogs, including native dialogs opened
  through pyRevit wrappers.

The table includes a **Window source** column showing the repository-relative
XAML path for custom windows (for example, `lib/GUI/SelectFromDict.xaml`) or the
API reference for built-in/native dialogs. Long values wrap and are available
in full on hover; columns can be resized and the table scrolls horizontally
when needed.

Select a window to see its description, source/API, calling tools with friendly
titles and command paths, and an explicit reason if its preview is unavailable.
The calling-tool list is built from source imports/calls, following shared helpers,
constructor XAML paths, class inheritance, configuration entry points, and
compiled command ownership without importing or executing the scanned code.
It describes statically reachable callers, not proof that every runtime branch ran.
Dynamic imports/getattr and parameterized routes can be unresolved. Templates,
retired forms, and orphaned library windows may have no current tool caller.

Choose a supported state and **Open preview**. Custom previews load actual
repository XAML and resources with Gallery-owned handlers and fictional data.
Supported custom states are Normal, Empty, Error, Disabled, and Long content.
The static fixture and Gallery shell offer Normal only. Controls support
filtering/checking, sample rename validation/results, duplicate options, numeric
validation, and local outcomes as applicable. No production command is invoked.

The **KLCode main template** preview uses the opt-in custom-window foundation:
equal 24-unit header/footer, Segoe UI, fixed buttons, shared spacing and the
existing semantic Search icon. It receives the Gallery's actual tool version
as caller metadata; footer navigation remains simulated. Long content shows
title ellipsis without a tooltip. Empty, Error and Disabled states are fictional.
Owner refinement matches Create from rooms' 24-high search field and compact
checkbox rows, uses its footer green/gray, omits the version prefix, and removes
the default main-button outline. The gap below the header is 4 units.
Other production forms and the Gallery catalog shell keep their existing
layouts pending review of this first reference. See the
[template guide](../../../../lib/GUI/_templates/KLCodeMainTemplate.md) and
[consolidation plan](../../../../docs/plans/custom-window-consolidation.md).

Recall preserves the actual recall shell and hosts the actual clipboard
UserControl inside `content_host`; its search, selection, sample load, and
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
never grants execution permission. The exact Model Checker `review.xaml` path
has a reviewed sample adapter when that source is present. The Model Checker
command remains on its own development branch until separately integrated; the
Gallery does not copy it onto this branch. Pages, UserControls, and resource
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
- `Gallery.xaml`: local Gallery layout, origin filter, caller details, state selector.
- `lib/ui_gallery/launchers.py`: stable known dialog identities.
- `lib/ui_gallery/registry.py`: source inventory, origins, availability, and search.
- `lib/ui_gallery/callers.py`: host-independent static caller discovery.
- `lib/ui_gallery/scenarios.py`: deterministic fictional data and interactions.
- `lib/ui_gallery/windows.py`: explicitly allowlisted custom-XAML preview handlers.
- `lib/ui_gallery/builtin.py`: real built-in/native dialog examples with discarded results.
- `scripts/validate_ui_gallery_wpf.ps1` and `.py`: isolated IronPython/WPF validation.
- `scripts/validate_ui_foundation_wpf.py`: reference-shell geometry, bindings,
  simulated actions/navigation, routed Close, and state-render checks.

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
