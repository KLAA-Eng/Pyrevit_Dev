# Five reference templates: review build

Date: 2026-10-28. Baseline: `e443439` on `dev.GUI-Clean`, plus this delivery.
The owner approved all five templates, followed by a grilling interview to
refine their elements. The [consolidation plan](../../../plans/custom-window-consolidation.md)
owns task status and interview progress. The [family guide](../../../../lib/GUI/_templates/README.md)
owns the template compositions and interaction contracts.

This records the initial five-template build. The subsequent [owner-confirmed
Form refinement](2026-10-28-form-template-refinement.md) removes Sample Preview
and replaces Form's field geometry; the initial Form renders below remain
historical evidence.
The subsequent [Message refinement](2026-10-28-message-template-refinement.md)
also supersedes the initial fixed-size/expanded-error Message behavior and
matches Form's heading to Selection's prompt style.

## Delivered reference family

| Gallery entry | Normal render | Additional evidence |
| --- | --- | --- |
| Template - Selection | [Selection](2026-10-28-template-family-evidence/template-selection-normal.png) | Existing settled geometry and native checked-list row template retained |
| Template - Form | [Form](2026-10-28-template-family-evidence/template-form-normal.png) | [Invalid input](2026-10-28-template-family-evidence/template-form-error.png), [minimum size](2026-10-28-template-family-evidence/template-form-minimum.png) |
| Template - Message | [Message](2026-10-28-template-family-evidence/template-message-normal.png) | [Long content/details](2026-10-28-template-family-evidence/template-message-long-content.png), [minimum size](2026-10-28-template-family-evidence/template-message-minimum.png) |
| Template - Options | [Options](2026-10-28-template-family-evidence/template-options-normal.png) | [Validation](2026-10-28-template-family-evidence/template-options-error.png), [minimum size](2026-10-28-template-family-evidence/template-options-minimum.png) |
| Template - Review | [Review](2026-10-28-template-family-evidence/template-review-normal.png) | [Long rows/detail](2026-10-28-template-family-evidence/template-review-long-content.png), [minimum size](2026-10-28-template-family-evidence/template-review-minimum.png) |

These are actual isolated WPF content renders, not drawn approximations. Initial
state images precede interaction checks; minimum-size images show the exercised
normal state (changed inputs, expanded details, checked rows as appropriate).
All Normal references and representative boundary/minimum images were inspected.
Twenty-five state layouts were constructed and checked. The initial dimensions
and added component appearance remain proposals for human refinement.

The former main reference was renamed `KLCodeSelectionTemplate.xaml`; its guide
was renamed too. The generic FindReplace visual was adapted into
`KLCodeFormTemplate.xaml`. The unused Revit-dependent `FindReplace.py` wrapper
and `GUI.forms` export were retired after source/caller inspection. The two Core
rename commands retain their bundled XAML, workflows and shared base behavior.

## Shared implementation

`KLCodeComponents.xaml` merges Foundation and supplies explicit styles for
sections, fields/readouts, dropdowns, radio/toggle controls, action variants,
severity chips/banners, DataGrid and splitter. Repeated dimensions and semantic
colors live in the central token dictionary. The five bodies contain their
composition and event names, with one shared shell instead of copied chrome.

`template_data.py` is the authoritative five-ID/source manifest and pure fixture/
validation owner. `templates.py` owns safe example presenters. The custom preview
factory validates source/state before loading these host adapters. The loader
loads Components while retaining caller resources and DataContext.

Form applies/reset naming rules into a read-only preview; Message changes tone
and details; Options validates finite numeric input and assigns fictional Browse
paths; Review separates checked items from selected detail and preserves checks
across filtering. Generated cell checkboxes actually update Python row models
and the displayed count. Check All selects eligible rows and clears invalid
blocked checks. No production model, file operation or external navigation runs.
Selection uses the same local informational alert behavior as the earlier
reference. The five compiled Gallery previews remain deferred.

Current inventory: 36 Gallery entries and 21 repository Window sources, including
the five templates. Dynamic source discovery still does not authorize new views.

## Verification

- Pure state/validation tests first failed because the new helper did not exist,
  then passed after implementation. Additional presenter tests cover invalid
  form/reset, options validation/fictional Browse, checked-versus-selected review
  state/filtering, severity changes, disabled body and simulated navigation.
- Gallery suite: 63 run, 62 passed, 1 skipped for unavailable symlink privilege.
- Loader/metadata: 9 passed. Core find/replace: 12 passed. Existing window
  regressions: 9 passed. Total focused checks: 92 passed, 1 skipped.
- New presenter/data coverage: 97% under CPython fake-boundary tests. This is
  Python statement coverage, not a XAML or live-host coverage claim.
- Actual installed IronPython/WPF: 36-entry catalog, 71 custom/state constructions,
  existing foundation/Close/selection checks and filter checks passed. Additional
  family probe checks all 25 layouts, normal-state actions and four minimum sizes.
- Disabled ComboBox/radio/toggle descendant text uses the actual shared disabled
  foreground. Review's generated checkbox changes the model and summary. All
  named primary actions retain 8-unit bottom clearance from the footer.

Reproduce:

```powershell
python -B -m unittest discover -s tests -p 'ui_gallery*test.py'
python -B -m coverage run --data-file=.coverage.ui-templates --source=ui_gallery.templates,ui_gallery.template_data -m unittest discover -s tests -p 'ui_gallery*test.py'
python -B -m coverage report --data-file=.coverage.ui-templates -m
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./scripts/validate_ui_gallery_wpf.ps1 -OutputDirectory "$env:TEMP/ui-template-family"
```

The process-only execution-policy override changes no machine settings. The
probe saves all 25 state renders and minimum-size specimens when requested.

## Review corrections and limits

Two independent reviews covered different ownership seams: template author
reviewed presenters/components; component author reviewed presenters/template
bodies. Neither was represented as independent review of their own work.
Confirmed issues were corrected: collapsed ComboBox hover/pressed feedback,
and severity swapping a full-width banner for a compact chip style. Actual
disabled-label and checkbox source/count checks passed. Grid cell text now uses
ellipsis, with full selected-item detail available separately.

Headless DataGrid captures initially preceded queued star-column sizing. The
probe now completes dispatcher layout work before capture and uses meaningful
column minimums. This follows [Microsoft's DispatcherFrame pattern](https://learn.microsoft.com/en-us/dotnet/api/system.windows.threading.dispatcherframe)
and is consistent with [WPF's queued column-sizing implementation](https://source.dot.net/PresentationFramework/System/Windows/Controls/DataGridColumnCollection.cs.html).
This is probe orchestration, not a new production dispatcher loop.

No Window was shown, and compiled windows were not built/rendered or migrated.
Actual pointer/keyboard/focus, popup input, drag/splitter use, ownership,
Narrator, DPI and mixed-monitor acceptance remain live-host work. The templates
are review specimens and starting patterns, not proof that every production
control/workflow can be replaced by a style-only change. The owner-requested
grilling is the next step; its answers will refine this review build.
