# UI Gallery standalone coverage verification

Date: 2026-10-27. Implementation branch: `master-dev`.
Scope approved by the owner after the KLCode grilling interview.

The [Gallery SPEC](<../../../../KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/SPEC.md>)
owns behavior. The [coverage plan](../../../plans/ui-gallery-coverage.md) owns
task status, pending live acceptance, and deferred compiled previews. This
record describes local evidence; it is not release approval.

## Delivered behavior

- 35 standalone catalog entries on this checkout: 20 repository Window XAML
  surfaces and 15 pyRevit/native dialog-family entries. Thirty entries offer
  previews; five compiled entries remain disabled by owner decision.
- Origin labels distinguish Repository custom, pyRevit built-in, and
  Revit/Windows native. A pyRevit wrapper around a system dialog is labeled native.
- Calling tools show friendly titles and bundle paths. Search includes both,
  and the origin filter can narrow the catalog.
- Supported custom previews reuse production XAML/resources with fictional
  data and local handlers. Interactive state fixtures cover Normal, Empty,
  Error, Disabled, and Long content where applicable. Native picker state
  support is limited honestly to Normal.
- Recall preserves its shell and actual clipboard UserControl. The existing
  production contrast issue remains visible; production GUI fixes are deferred.
- All contained Window sources are accounted for. Unknown sources are listed
  without execution permission. The exact Model Checker review path receives
  its safe adapter when that source is present; the command was not copied
  from `dev.model-checker` onto `master-dev`.

The five deferred windows are Family Studio, Startup Importer source picker,
review, blocking issues, and the shared compiled alert. Working previews are
future task GAL-F01, not a prerequisite for this scope.

## Automated checks

| Check | Result |
| --- | --- |
| Gallery unittest suite | 50 tests run; 49 passed and one platform-dependent symlink test skipped |
| Shared GUI regressions | 17 passed: window backgrounds, Find/Replace presentation, canonical selector behavior |
| Gallery helper statement coverage | 83% across `lib/ui_gallery` under CPython tests; host-only paths are also exercised separately where described below |
| Gallery metadata | `validate_bundle` passed for planned v0.5; script, bundle, SPEC, date, and Unreleased status match |
| Full metadata checker | Pre-existing error remains for the cache-only Model Checker command directory lacking `bundle.yaml`; no unrelated source/cache was removed |
| Independent review | Separate reviewer inspected the parent-owned registry, built-in adapter, Gallery controller/layout, and integration tests; no remaining material finding after corrections |
| Whitespace/diff | Final checks recorded with the local implementation commit |

The caller-index author did not independently review its own implementation.
The coordinating agent inspected that implementation and its tests. Source
review corrections included exact Model Checker identity matching, visible
error/long-content fields, and faithful parameter/sheet grouping. Parameter
preview templates load from installed pyRevit at runtime; no upstream assets
were copied into this repository.

Caller indexing follows static calls/imports and possible class callbacks,
including indirect helpers and compiled consumers. It does not prove runtime
execution or fully resolve dynamic imports/getattr. Unresolved/retired/template
surfaces can display no current tool caller. This is an honest source inventory,
not instrumented runtime usage data.

## Isolated IronPython/WPF validation

Installed reference: pyRevit `6.5.3.26176+2017`; IronPython `2.7.12`,
.NET Framework 4.8. The validation runner loads the installed engine and its
embedded standard library in memory. It uses real WPF/resources/bindings and
the Gallery/custom preview handlers, with a small stand-in for pyRevit's
window loader and alert function.

Observed result:

```text
IronPython 2.7.12: 35 catalog entries; 66 real-WPF custom/state constructions;
Gallery filters/deferred selection passed.
No window was shown. Native dialogs and pyRevit/Revit integration remain host checks.
```

The probe exercised caller-name search, no-result search, origin filtering,
disabled compiled selection, each existing custom/state construction, and list
check-all/check-none handlers. It rendered actual XAML content at 1060- and
900-unit widths. These are isolated content renders, not screenshots from Revit.

| Render | What was inspected |
| --- | --- |
| [Gallery, 1060 units](2026-10-27-ui-gallery-evidence/gallery-1060.png) | Catalog hierarchy, caller detail, state selection, and primary controls |
| [Gallery, 900 units](2026-10-27-ui-gallery-evidence/gallery-900.png) | Minimum-size layout, wrapping caller paths, scrolling, and reachable controls |
| [Recall composition](2026-10-27-ui-gallery-evidence/kla-match-properties-recall.png) | Actual shell and clipboard content; visible production readability issue retained |
| [Core Views rename](2026-10-27-ui-gallery-evidence/kla-find-replace-views.png) | Actual fields, case buttons, rename action, and header/footer |

Reproduce the isolated check from the repository root using the installed
engine, adjusting `-EngineDirectory` when needed:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/validate_ui_gallery_wpf.ps1 -OutputDirectory docs/knowledge/reviews/design-system/2026-10-27-ui-gallery-evidence
```

The execution-policy argument applies only to that process; no system policy
is changed. Omit `-OutputDirectory` to check without saving render files. No
validation run opens a model, shows a Window, or invokes a production command.

## Remaining host evidence

The Revit bridge returned `All connection attempts failed`. No live Revit input,
native picker/dialog, actual pyRevit loader, owner/modal behavior, Narrator,
high-contrast, mixed-monitor, or display-scaling acceptance is claimed.
The installed form signatures, control names, parameter template, and grouping
paths were checked against local pyRevit and official references:

- [pyRevit forms reference](https://docs.pyrevitlabs.io/reference/pyrevit/forms/).
- [IronPython forms implementation reference](https://docs.pyrevitlabs.io/reference/pyrevit/forms/_ipy/).
- [WPF ComboBox reference](https://learn.microsoft.com/dotnet/api/system.windows.controls.combobox).

Complete GAL-06 in representative supported Revit hosts before promoting this
DevSandbox tool. Check every supported family/state, filtering/selection recovery,
keyboard dismissal, native picker cancellation/results, and absence of production
model/file/navigation effects. Production GUI remediation from the October 26
review remains a separate effort.
