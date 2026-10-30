# Shared dialog implementation — 2026-10-29

Owner request: develop the proposed custom windows using KLCode skills and
incorporate them into the GUI system, without changing actual tools yet.
Work branch: `dev.GUI-Clean`; starting baseline: `4f81974`.
The [consolidation plan](../../../plans/custom-window-consolidation.md) owns
task status; [dialog SPEC](../../../../lib/GUI/dialogs/SPEC.md) owns acceptance
criteria; [API guide](../../../../lib/GUI/dialogs/README.md) owns usage.

## Delivered source

Four lazy Python/IronPython WPF window factories: message/confirmation,
single/multiple grouped selection, described action choice and text entry.
They use the current shared shell, geometry icons, styles and green/gray footer.
Three additional opt-in component styles render descriptions/disabled rows and
structured checkbox content. Existing implicit styles and old APIs are retained.

Host-free data models preserve stable identity, duplicate labels, caller rows,
input order, hidden checks and disabled eligibility. Results distinguish
No/Cancel, accepted empty strings and selection payloads. No script exit or
Revit operation occurs. Callers supply prepared rows, owner, version and any
pure text validator. Actual modal showing/host ownership remains unverified.

Gallery adds six allowlisted variants, each with five fictional states. The
current catalog has 42 entries and 25 standalone Window sources. Its five
compiled previews remain deferred. Only the Gallery command SPEC/tooltip
changed: existing tool command scripts, pyRevit dialog calls, workflows,
CustomAlert, SelectFromDict, templates and packaged DLLs were not migrated.

## Verification

Windows environment: installed pyRevit `6.5.3.26176+2017` IronPython 2.7.12
engine assemblies; CPython 3.14; .NET SDK 10.0.402. No Revit process/model was
opened for this slice.

| Check | Result |
| --- | --- |
| Initial behavioral test | Failed for the missing dialog package, then passed after implementing duplicate-label identity and hidden checks |
| Full CPython unittest suite | 362 run; 361 passed, 1 existing symlink-related skip |
| New model/import contracts | 10 tests: host-free package import, identity/order, groups/search, single selection, initial/disabled checks, malformed keys, cancellation/blank and validation |
| Gallery registry/source contracts | Six entries/four sources/five states; all XAML event handlers accounted for |
| Actual installed IronPython/WPF Gallery probe | 42 entries; 101 custom/state constructions; prior 25 template and 45 production-state layout regressions pass |
| New dialog WPF probe | 30 states at normal and minimum sizes; shell/footer RGB, action bounds, default buttons, disabled body and collapsed details pass |
| Actual WPF interaction checks | All five message actions, four severities, conservative confirmation default, No distinct from Cancel, overflow/details scrolling, duplicate-label payloads, visible-only batch checks, hidden checks, disabled rows, single exclusivity, enabled action choice and text validation pass |
| Cancellation checks | Actual header buttons and direct dispatch to the shared Escape handler cancel all four families; native Close leaves the initialized cancel result |
| C# source tests | 17 passed |
| Compiled WPF smoke, net48 and net8.0-windows | Seven actual instances across five existing compiled classes passed on each runtime; shared resources still load |
| Shared scale / artwork | 0 strict violations; 85 existing advisory consumer literals; 17 GUI icon roles and wordmark generation unchanged |
| Documentation integrity | Deterministic audit passed; all local Markdown links resolve. Generic role/ADR/test-registry warnings remain advisory under the repository's existing documentation ownership. |
| Scope / whitespace review | Self-review of changed sources and Git diff; no production command migration; diff whitespace check passes |

The Windows probe is `scripts/validate_ui_gallery_wpf.ps1`, which now executes
`scripts/validate_ui_dialogs_wpf.py`. It constructs, measures and renders actual
windows, raises button events and checks observable results without showing
them. It does not simulate every real keyboard/pointer sequence. No fake-only
test is presented as live Revit acceptance. Changed-code coverage percentage
was not measured across the separate CPython and embedded IronPython hosts;
functional contracts and actual WPF branches above provide the local evidence.

Render inspection caught a structured checkbox ContentTemplate being rendered
as a type name; an opt-in shared style and actual rendered-label regression
check correct it. The full severity check caught an undefined success brush;
success now consumes the existing `KlaReadyBrush`. Binding-preserving toggle
tests confirm single checks update peers without replacing focused controls.

## Representative inspected renders

| State | Render |
| --- | --- |
| Message | [Information](2026-10-29-shared-dialogs-evidence/dialog-message-normal.png) |
| Confirmation | [Yes / No / Cancel](2026-10-29-shared-dialogs-evidence/dialog-confirmation-normal.png) |
| Grouped selection | [Normal](2026-10-29-shared-dialogs-evidence/dialog-selection-normal.png), [minimum size](2026-10-29-shared-dialogs-evidence/dialog-selection-minimum.png) |
| Parameter selection | [Duplicate labels / disabled item](2026-10-29-shared-dialogs-evidence/dialog-parameters-normal.png) |
| Action choice | [Descriptions and disabled action](2026-10-29-shared-dialogs-evidence/dialog-actions-normal.png) |
| Text validation | [Required feedback](2026-10-29-shared-dialogs-evidence/dialog-text-error.png) |
| Long message / details | [Capped scrolling](2026-10-29-shared-dialogs-evidence/dialog-message-overflow.png) |

Additional temporary renders covered long selection/text and minimum choice,
confirmation and prompt layouts. Body/action/footer bounds remain intact.

## Owner host review

Open UI Gallery and search **Shared dialog**. Review the six variants and their
Normal/Empty/Error/Disabled/Long content states. In Revit, check actual modal
ownership, Alt+F4/Close/Escape, Enter defaults, Tab/Space/arrow traversal,
initial focus and checkbox focus retention, dragging, work-area placement,
DPI/contrast and long-content scrolling. Native-handle/WPF owner integration
and the lazy framework-bootstrap fallback require host acceptance as well.

This is a reusable GUI library delivery. Future tool adoption needs the
relevant command SPEC, query/ordering rules and return-type adaptation. The
existing GUI-14 keyboard issues, Model Checker metadata error, deployed compiled
DLL acceptance and other plans are unaffected. Roll back the new package,
opt-in styles, Gallery entries, probes and documentation together if required.
