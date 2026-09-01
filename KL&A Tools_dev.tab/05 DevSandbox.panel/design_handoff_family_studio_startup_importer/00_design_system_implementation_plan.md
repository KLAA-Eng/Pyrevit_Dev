# Implementation Plan: KLCode WPF Design-System Foundation

- Repository / evidence commit: `KLCode.pyRevit`, `e856ca3`; design handoff is an untracked input bundle in this directory.
- Owner / priority / scope: KL&A engineering, active prerequisite for the Family Studio and Startup Importer DevSandbox windows.
- Status: `NOT READY` for feature delivery until checkpoint 1 proves the theme/resource boundary and the locale inventory is approved.
- Outcome: deliver one compiled-WPF consumption path for the existing green theme so both tools render fixed-size, borderless KLCode dialogs without hard-coded user-facing copy or forked palette values.
- Non-goals: changing the native-theme tools, changing the visual-system source of truth, shipping the handoff HTML, adding a web UI framework, or promoting either command out of `05 DevSandbox.panel`.

## Current Evidence And Invariants

- `lib/GUI/Resources/WPF_styles.xaml` defines the shared green brushes and control templates. It is currently loaded from IronPython in `lib/GUI/WPF_Base.py`, not from a compiled C# WPF project.
- The existing Family Studio Revit project already uses WPF but creates controls imperatively in `src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/FamilyStudioWindow.cs`.
- The Startup Importer Revit project has `UseWPF=true` but no XAML or UI project: `src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.Revit/KLA.ModelStartupImporter.Revit.csproj`.
- The repository has a per-locale WPF resource-dictionary pattern in `lib/match/clipboard.py` and `lib/match/clipboard_ui.ResourceDictionary.en_us.xaml`; the complete set and compiled-WPF loading mechanism have not yet been inventoried.
- All generated chrome must bind the named brushes/styles from `WPF_styles.xaml`; the handoff's literal hex values are reference-only. Windows stay fixed-size, green-theme only, with no animation other than ComboBox `PopupAnimation="Slide"`.
- User-facing copy must come from tool locale ResourceDictionaries. The Audiowide source in the handoff may be used only for the brand mark after its distribution/license status is verified; existing `lib/_icons/` PNGs must be used where they cover needed controls.

## Acceptance Criteria

1. A Revit-hosted compiled WPF smoke window merges the shared green dictionary without parser/runtime errors, resolves every required brush/style by key, and has the requested header/footer drag/close behavior.
2. The smoke window has no manually copied design-token colors and its text comes from the approved locale dictionaries, including the English fallback.
3. A Windows build for Revit 2024 and 2025+ proves the resource packaging and source paths work in each target framework.
4. The implementation explicitly documents any styles that the shared dictionary cannot safely expose to compiled WPF and obtains an owner-approved, non-forking adaptation before feature work uses them.

| Step | Exact files/surfaces | Behavior guarantee | Test-first evidence | Verification | Rollback/containment |
| --- | --- | --- | --- | --- | --- |
| 1. Prove the resource boundary | `lib/GUI/Resources/WPF_styles.xaml`; **new** minimal compiled-WPF spike under one of the existing Revit projects; `lib/GUI/WPF_Base.py`; `lib/match/clipboard.py` | The compiled host can merge and instantiate the shipped resource dictionary without relying on IronPython event handlers such as `button_close`. | A failing smoke test/window that loads the dictionary and resolves the required keys (`header_background`, `text_white`, `text_green`, `button_*`, `border_green*`, `footer_donate`). | Windows build/run in Revit 2024 and 2025+; inspect WPF parser/load exceptions. | Remove the spike only; do not copy or edit production colors. Stop feature work if the existing dictionary cannot be consumed safely. |
| 2. Decide the smallest reusable compiled surface | **new, provisional** `src/KLCode.Wpf` project only if step 1 proves both tools need the same compiled templates; otherwise per-tool `Resources/` folders; **new** `ThemeBootstrapper`, chrome/group/alert styles | One owner-defined compiled adapter supplies shared chrome, group borders, alert layout, status chips, scrollbars, and fixed control dimensions while referencing the canonical dictionary rather than duplicating palette tokens. | XAML/resource-key tests that fail for missing dictionaries/keys; screenshot checklist for all control states. | Build each consuming project on Windows; compare Family Studio FS-1 and Startup Importer SI-2 against the handoff at their fixed dimensions. | Keep the adapter internal and unversioned; revert the new adapter/project without changing host-independent Core code. |
| 3. Establish localization before adding screens | **new** per-tool `Resources/Strings/ResourceDictionary.<locale>.xaml`; locale inventory derived from existing extension resources; **new** locale loader and English fallback tests | Every visible string is a keyed resource with deterministic current-locale selection and English fallback; data values/paths remain data bindings, not translated literals. | Tests fail for missing keys in one locale and for an unknown locale without fallback. | Load every supported locale in a compiled WPF smoke window; code review confirms no new hard-coded user-facing strings. | Fallback to English only when a locale file is absent; never silently substitute incomplete text for an existing locale. |
| 4. Package approved assets | `lib/_icons/`; handoff `assets/fonts/Audiowide-Regular.ttf`; **new** project item entries and resource tests | Only approved bitmap icons and the approved logo font are embedded/copied for the compiled WPF assemblies; no SVG redraws or design HTML are packaged. | Build assertion for each declared `Resource`/`Content` item and an asset-not-found UI test. | Inspect Revit bundle output after the existing packaging targets run. | Exclude an unapproved or missing asset and use an existing approved PNG/text fallback; do not replace binary source assets. |
| 5. Record the visual QA gate | **new** `DESIGN_SYSTEM_VALIDATION.md` in this handoff; existing Windows packaging targets in the two `.csproj` files | Each feature screen is reviewed at its exact fixed size for colors, spacing, clipping, focus order, keyboard navigation, disabled state, and high-DPI rendering in Revit. | A screen-by-screen manual test matrix exists before the first implementation slice is accepted. | Windows/Revit 2024 and 2025+ screenshot evidence, then `git diff --check` and complete diff review. | Keep both commands in DevSandbox and do not package/publish an unvalidated visual surface. |

## Dependencies, Decisions, And Gates

- Owner decision required: whether the existing `WPF_styles.xaml` can receive narrowly scoped compiled-WPF compatibility changes, or must remain unmodified with a consuming adapter. Its `Header` template includes an event-handler reference, so this cannot be assumed.
- Owner decision required: the authoritative list of the eight supported locales and translations for all new keys. The current source shows an English resource dictionary and a locale-loader pattern, but not the compiled-WPF contract.
- Owner decision required: confirm whether the handoff font is an approved distributable asset for the Revit assemblies. Existing shared logo assets were not identified in the handoff bundle.
- Required gates: source-level resource tests `PASS`; Windows Revit 2024 and 2025+ compile/package `UNAVAILABLE` in this macOS workspace; live visual QA `UNAVAILABLE`; accessibility/focus inspection `UNAVAILABLE` until a Windows Revit host is available.

## Execution Order And Handoff

Run this plan before either tool plan. Checkpoint 1 has exclusive write scope over the selected theme-integration spike; checkpoint 2 can create the approved shared/per-tool resource structure; feature plans then own their separate UI projects. Route an approved plan to `$build` only after the three owner decisions and the smoke-window result are recorded.
