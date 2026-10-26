# Design system and GUI review

Review date: 2026-10-26. Branch: `master-dev`.
Source baseline: `a487f28c395020797973cd663a28ae5844670efc` (`update readme`).

## Purpose and handoff boundary

This document preserves the full source review requested on October 26 so the
owner can resume the work later. The owner explicitly deferred remediation.
No application code, assets, command behavior, or model data changed during
the review. The working tree was clean and the final `git diff --exit-code`
passed before this documentation follow-up.

The review applied the KLCode `design-system`, `code-review`, and
`interface-accessibility` skills. This record is historical evidence and a
resumption reference, not an approved implementation plan or a new task ledger.
When remediation starts, recheck the findings against the current source and
use one named [active plan or tracker](../../../plans/README.md) if the effort
needs ongoing task tracking. Link the finding IDs below from that authority.

The living implementation guide remains [DESIGNSYSTEM.md](../../../DESIGNSYSTEM.md).
Command behavior remains owned by each adjacent `SPEC.md`. Earlier evidence is
preserved in the [October 5 review](../2026-10-05/design-system-and-gui.md) and
[October 8 review](2026-10-08-current-state-review.md).

## Assessment

The extension has a recognizable shared palette and largely consistent legacy
window headers. The main gaps concern readable text, keyboard focus, alert
overflow, control states, work-area constraints, accurate labels and versions,
and Gallery fidelity. Address those before broad cosmetic standardization.

The legacy IronPython styles, compiled WPF adapter, and command-local styles
have separate implementations. Some differences are deliberate host boundaries;
their existence alone is not a defect. Native pyRevit dialogs, light docked
panels, and the minimal Gallery fixture have distinct purposes. Match Recall's
mixed light/dark composition is a separate, reproducible concern.

No critical GUI defect was established. Severity in this record:

- **P2:** actionable usability or accuracy issue.
- **P3:** bounded consistency, dormant-surface, or maintenance issue.

## Coverage and evidence limits

All **53 repository XAML files** were parsed and inventoried: **20 Windows,
2 Pages, 1 UserControl, and 30 ResourceDictionaries**. Source review included
layout/resources, relevant Python/C# loaders and handlers, command specifications,
the Gallery registry and previews, and existing validation contracts.

| Surface group | Coverage |
| --- | --- |
| Shared legacy windows | SelectFromDict, CustomAlert, FindReplace, DuplicateSheets, CreateFromRooms, and the legacy RenameViews/RenameSheets forms |
| Command-local windows | Core Find and Replace Views/Sheets, View Range, Steel PSF, and Match Properties Recall |
| Reference/tooling windows | Main template, UI Gallery, and preview fixture |
| Compiled windows | Family Studio, shared alert, Startup Importer source picker, review, and blocking issues |
| Embedded surfaces | Match clipboard Page/UserControl and Custom Properties Page |
| Resource dictionaries | Legacy palette/styles, compiled tokens/controls/strings, clipboard icons/locales, Custom Properties locales, and check locales |

The Revit bridge returned `All connection attempts failed`. No live Revit
window was opened or driven. Host rendering, actual mouse/keyboard operation,
Narrator behavior, high contrast, mixed monitors, and DPI acceptance remain
unverified. Locale key parity was checked; translation quality was not certified.

Read-only, in-memory Windows WPF probes supplemented source inspection. They
instantiated controls and measured layouts without showing a Window or calling
Revit. Where compiled subtrees were loaded, event attributes were removed from
in-memory XML and resource dictionaries were assembled in memory. These are
isolated mechanism checks, not execution of the packaged add-ins. No probe
scripts, screenshots, or raw measurement files were saved; the observed results
are recorded below. Pillow approximations from the Gallery exporter were not
used as visual evidence.

## Findings

### GUI26-01 — P2: View Range labels project-unit values as feet

**Evidence:** [MainWindow.xaml:322](<../../../../KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml>)
hard-codes `Elevation - ft`. [script.py:80](<../../../../KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py>)
selects the document's length unit; the display/update paths convert using it.
The view model already carries a `unit_label`. The adjacent SPEC documents the
static heading, but that does not make it accurate for a metric project.

**Trigger/impact:** a non-feet project displays elevations under an inaccurate
unit heading, creating an interpretation risk when editing offsets.

**Recommended correction:** derive elevation and offset unit labels from the
unit actually used for display and input. Update the command SPEC with the change.

**Validation:** imperial and metric fixtures; verify displayed elevation,
entered offset, resulting model value, and reset behavior.

### GUI26-02 — P2: Match Recall mixes a white surface with inherited light text

**Evidence:** [clipboard_content.xaml:3](../../../../lib/match/clipboard_content.xaml)
sets `Background="White"`. [clipboard.py:457](../../../../lib/match/clipboard.py)
loads shared dark resources for Recall and inserts this UserControl into
`content_host`. An isolated WPF composition reproduced `#E5E4E2` text inherited
from the outer resources on white, approximately **1.27:1 contrast**.

**Trigger/impact:** Recall's embedded content can become a mixed light/dark
surface with very weak text contrast. The docked clipboard has a separate light
host boundary that must be considered when changing the reusable content.

**Recommended correction:** give the embedded content an explicit, coherent
theme appropriate to its host instead of relying on accidental inheritance.

**Validation:** actual Recall and docked clipboard; search, list headers,
checkboxes, disabled paste actions, and long parameter/value text.

### GUI26-03 — P2: alerts do not provide bounded long-message scrolling

**Evidence:** [KlaAlertWindow.xaml:40](../../../../src/KLCode.Wpf/Views/KlaAlertWindow.xaml)
places a ScrollViewer inside a vertical StackPanel in a fixed 440 x 300 window.
The current in-memory long-message probe observed a 191-unit body slot, a message
parent about 4,847 units tall, `ExtentHeight=4820`, `ViewportHeight=4820`, and
`ScrollableHeight=0`. [CustomAlert.xaml:57](../../../../lib/GUI/CustomAlert.xaml)
has an unbounded wrapping message with no ScrollViewer in a fixed 440 x 255 window.

**Trigger/impact:** long errors, paths, or multiple refresh issues can extend
beyond the visible message area without a useful scrolling viewport.

**Recommended correction:** use bounded Grid rows for heading/message content
and retain reachable dismissal controls. Consider copyable technical details.

**Validation:** short text, Unicode, long paths, and eight-error messages; reach
the final character and dismissal action by keyboard and mouse at multiple DPIs.

### GUI26-04 — P2: shared styles suppress keyboard-focus feedback

**Evidence:** [KLCodeControls.xaml:43](../../../../src/KLCode.Wpf/Resources/KLCodeControls.xaml)
and lines 92, 216, and 276 set null focus styles for compiled buttons, segmented
radio options, checkboxes, and list rows without replacement keyboard-focus
triggers. [WPF_styles.xaml:208](../../../../lib/GUI/Resources/WPF_styles.xaml)
does the same for legacy checkboxes.

**Trigger/impact:** a control can receive keyboard focus without identifying the
current keyboard target. Checked, selected, and hovered states serve different roles.

**Recommended correction:** add a consistent focus adorner or explicit keyboard
focus triggers in the shared control implementations.

**Validation:** Tab/Shift+Tab, arrows, Space, Enter, and documented cancellation;
verify focus independently of selection, checking, hover, and disabled neighbors.
See [Microsoft's WPF focus-styling guidance](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/advanced/styling-for-focus-in-controls-and-focusvisualstyle).

### GUI26-05 — P2: text accent and muted colors have weak contrast

**Evidence:** [WPF_styles.xaml:11](../../../../lib/GUI/Resources/WPF_styles.xaml)
defines the text accent and footer colors. Compiled group captions and footers
consume the same colors at [KLCodeControls.xaml:331](../../../../src/KLCode.Wpf/Resources/KLCodeControls.xaml).
The source color pairs give these approximate opaque-sRGB ratios:

| Foreground | Background | Contrast |
| --- | --- | ---: |
| `#33714F` green | `#1A252B` charcoal | 2.69:1 |
| `#407058` footer green | charcoal | 2.74:1 |
| `#808080` gray | charcoal | 3.96:1 |
| Green | `#22303A` compiled panel | 2.33:1 |
| `#E5E4E2` body text | charcoal | 12.30:1 |
| White | `#286048` button fill | 7.35:1 |

**Trigger/impact:** small captions, table headings, metadata, and footer links
are harder to read. The normal white-on-green button pairing is strong.

**Recommended correction:** introduce foreground-specific accent/muted tokens
with sufficient contrast while retaining brand colors for suitable fills/artwork.

**Validation:** actual enabled text pairs in normal, hover, selection, and warning
states. Use 4.5:1 as a normal-text review benchmark, and test high contrast
separately. [WCAG2ICT](https://www.w3.org/TR/wcag2ict-22/) is informative guidance
for desktop software; this review does not establish accessibility conformance.

### GUI26-06 — P2: compiled ComboBox selection text intercepts the toggle area

**Evidence:** [KLCodeControls.xaml:165](../../../../src/KLCode.Wpf/Resources/KLCodeControls.xaml)
places a hit-testable ContentPresenter over the ToggleButton. The legacy template
sets its equivalent presenter to `IsHitTestVisible="False"`. Isolated visual hit
tests reached `TextBlock > ContentPresenter > Grid > ComboBox` at x=12 and x=65,
and the ToggleButton subtree near the arrow at x=140.

**Trigger/impact:** source and hit testing support a concern that clicking the
displayed value fails to open the selector while clicking near the arrow works.
Actual input operation in Revit was not exercised. Microsoft's
[ComboBox source](https://source.dot.net/PresentationFramework/System/Windows/Controls/ComboBox.cs.html)
handles focus separately from the template toggle.

**Recommended correction:** align the selected-value presenter's hit-testing
behavior with the intended full selector click target.

**Validation:** click text, blank body, and arrow; verify open/close behavior and
keyboard selection in the compiled host before closing this finding.

### GUI26-07 — P2: important fields lack programmatic accessible identity

**Evidence:** isolated automation peers returned empty names for Family Studio's
SearchBox, CategoryFilter, TypeFilter, ParameterFilter, and RootFilter. The
[XAML:58](../../../../src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/FamilyStudioWindow.xaml)
supplies visual captions/tooltips without explicit label relationships. Result
checkboxes and the [Startup Importer row checkbox:45](../../../../src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/Views/StartupImportReviewWindow.xaml)
also depend on neighboring row text. Shared icon-only search fields and dynamic
Custom Properties fields deserve the same host inspection.

**Trigger/impact:** assistive technology may announce a field or checkbox without
the search/filter role or item identity needed to operate it.

**Recommended correction:** supply meaningful automation names or associated
labels, including data-bound names for item-selection controls.

**Validation:** inspect actual UI Automation names/roles/states and complete the
workflows using Narrator. Isolated peer results do not replace host acceptance.

### GUI26-08 — P2: fixed window sizes lack a work-area fit strategy

**Evidence:** [FamilyStudioWindow.xaml:5](../../../../src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/FamilyStudioWindow.xaml)
sets 1180 x 740. [KlaWindowStyle:8](../../../../src/KLCode.Wpf/Resources/KLCodeControls.xaml)
sets `ResizeMode=NoResize`. Several legacy selectors enforce fixed/minimum heights.

**Trigger/impact:** a small logical work area, including one reduced by display
scaling, can leave content/actions outside the usable screen. This is a source
constraint/risk; no clipped Revit screenshot was captured in this review.

**Recommended correction:** define minimum usable layouts, work-area fitting,
and appropriate resizing/scrolling behavior, starting with Family Studio.

**Validation:** smaller screens, 100/125/150/200% scaling, enlarged text, and
mixed-monitor movement; verify every primary and close action remains reachable.

### GUI26-09 — P3: disabled and pressed states are inconsistent

**Evidence:** View Range's [local action-button style:202](<../../../../KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml>)
has hover styling but no disabled appearance, while Apply Changes is bound to
`can_modify_view`. Compiled buttons explicitly dim when disabled. Legacy/shared
and local templates also lack a consistent pressed-state treatment.

**Trigger/impact:** an unavailable action can retain an enabled appearance,
and equivalent controls communicate state differently between windows.

**Recommended correction:** define shared disabled and pressed treatments and
apply them consistently to documented local variants.

**Validation:** unavailable editing contexts, disabled neighboring actions,
mouse-down/keyboard activation, and recovery to enabled state.

### GUI26-10 — P3: compiled button templates ignore padding

**Evidence:** [KLCodeControls.xaml:48](../../../../src/KLCode.Wpf/Resources/KLCodeControls.xaml)
does not consume the button's Padding. An isolated Load button measured about
26.7 units wide with both the declared 24-unit total horizontal padding and an
increased 100-unit total padding.

**Trigger/impact:** automatically sized buttons are narrower than their style
contract implies; density and spacing differ from legacy action buttons.

**Recommended correction:** bind padding into the template's content layout.

**Validation:** automatically sized toolbar/action buttons and fixed-width
buttons; ensure the corrected widths do not create row overlap or clipping.

### GUI26-11 — P3: compiled footer versions are inaccurate

**Evidence:** the shared [VersionLabel:9](../../../../src/KLCode.Wpf/Resources/Strings/ResourceDictionary.en_us.xaml)
hard-codes `Version: 2.0`. Family Studio and Startup Importer both declare tool
version `v0.0` in their bundle metadata/SPECs; their windows consume this shared label.

**Trigger/impact:** the visible window reports a different version from its
owning command, complicating support and acceptance evidence.

**Recommended correction:** supply the owning tool's authoritative version.
Keep tool, extension, and assembly versions distinct.

**Validation:** compare every compiled footer with its bundle and adjacent SPEC;
also review legacy footer formats when defining a common version-display policy.

### GUI26-12 — P3: compiled footers look interactive without an action

**Evidence:** [FamilyStudioWindow.xaml:245](../../../../src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/FamilyStudioWindow.xaml)
uses underlined TextBlocks for Prototype and Outreach. Equivalent compiled
Importer footers follow this pattern; legacy footers use real hyperlinks.

**Trigger/impact:** link-like styling suggests a clickable destination that
these TextBlocks do not provide.

**Recommended correction:** select consistent behavior and appearance for each
footer role; use semantic interactive controls where navigation is intended.

**Validation:** mouse and keyboard behavior, focus, accessible role/name, and
correct navigation destinations for actual links.

### GUI26-13 — P3: Gallery previews hide production composition and states

**Evidence:** the [Recall preview:545](<../../../../KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py>)
loads production XAML and then assigns `self.Content = panel`, removing its
chrome and embedded clipboard control. The [rename preview:372](<../../../../KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py>)
closes on actions and does not exercise the outcome panels.

**Trigger/impact:** a successful preview can conceal production composition,
readability, and long/error-state layout problems. Registry completeness alone
does not establish preview fidelity.

**Recommended correction:** preserve production shell composition, seed the
appropriate content host, and provide representative empty, error, long-content,
and disabled states. Preserve the Gallery's no-model-write contract.

**Validation:** registry-to-production correspondence and every changed preview
state; verify no preview invokes document-changing production handlers.

### GUI26-14 — P3: palette ownership conflicts with the source-test contract

**Evidence:** [WPF_styles.xaml:6](../../../../lib/GUI/Resources/WPF_styles.xaml)
defines legacy brushes locally. The compiled adapter uses
[KLCode_palette.xaml](../../../../lib/GUI/Resources/KLCode_palette.xaml).
Common color values match, but the legacy dictionary also has `window_background`,
which the palette lacks. The [C# contract test:79](../../../../src/KLCode.Wpf/Tests/KLCode.Wpf.Source.Tests/DesignSystemResourceContractTests.cs)
requires a canonical palette merge and zero local SolidColorBrush definitions.
That assertion conflicts with the inspected source. The C# suite was not run.

**Trigger/impact:** ownership is split and the test contract does not describe the
implementation. Future theme edits can diverge across adapters/local copies.

**Recommended correction:** explicitly choose consolidation or a documented
separate-adapter contract, then reconcile implementation and tests together.
Preserve IronPython and compiled-resource compatibility.

**Validation:** both resource-loading paths, all required keys, local overrides,
the C# source-contract suite, and representative host windows.

### GUI26-15 — P3: Create From Rooms silently discards invalid input

**Evidence:** [CreateFromRooms.py:148](../../../../lib/GUI/Tools/CreateFromRooms.py)
filters typed characters without validating a complete numeric value. Submission
closes the window before converting the offset or confirming selection; a broad
exception path sets `offset = 0`. Malformed decimal strings can pass the filter.
Current discovered use is the Gallery, making this a dormant-surface concern.

**Trigger/impact:** invalid offset/no-selection input can dismiss the form without
an explanation and substitute a default result.

**Recommended correction:** validate the full input and selection before closing,
retain the entered value on failure, and show a specific error before adding a
production consumer.

**Validation:** empty list, no checked item, empty/malformed/pasted numeric input,
valid units, cancellation, and negative offsets if supported by the chosen contract.

## Validation results at the recorded baseline

| Check | Result and limits |
| --- | --- |
| XAML inventory/parse | 53 files parsed; root counts recorded above. XML parsing does not prove runtime resource resolution. |
| Existing GUI-related Python tests | 28 tests run: 27 passed, 1 skipped. |
| Tested modules | `window_backgrounds_test`, `ui_gallery_launchers_test`, `ui_gallery_catalog_test`, `custom_alert_integration_test`, `find_replace_window_test`, `select_from_dict_selection_test` |
| Gallery window inventory | Existing launcher coverage tests passed, including repository Window correspondence. |
| Localization resource keys | Checked locale dictionaries in `checks/locale`, `lib/match`, and `lib/customprops` matched their English key sets. |
| In-memory WPF probes | Reproduced Recall foreground inheritance, compiled-alert unbounded measurement, ignored button padding, empty Family Studio field names, and ComboBox visual hit paths. |
| Layout hypotheses rejected | The measured source-picker note/buttons did not overlap; Family Studio's English filter controls fit in one row at the declared width. These were not reported as defects. |
| Command metadata checker | `scripts/check_tool_metadata.py`: 35 visible command bundles checked; 1 error for missing `bundle.yaml` in `KL&A Tools_dev.tab/05 DevSandbox.panel/Model Review.pulldown/Model Checker.pushbutton`. No repair made. |
| C# resource-contract suite | Inspected, not executed. GUI26-14 describes a source/assertion discrepancy, not a newly recorded test-run failure. |
| Live Revit acceptance | Unavailable; bridge connection failed. |
| Repository state after source review | Clean `master-dev`; empty final diff before saving this report and its index link. |

Python was run with `-B` to suppress bytecode writes. The existing tests can be
repeated from the repository root with:

```text
python -B -c "import sys,unittest; sys.path.insert(0,'tests'); names=['window_backgrounds_test','ui_gallery_launchers_test','ui_gallery_catalog_test','custom_alert_integration_test','find_replace_window_test','select_from_dict_selection_test']; result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromNames(names)); sys.exit(not result.wasSuccessful())"
python -B scripts/check_tool_metadata.py
```

The metadata-check error is an additional standards/validation issue; it is not
evidence of a rendered Model Checker window defect. The directory was present
with cache content at review time, but lacked the required metadata file.

## Changes since the older reviews

- The older window-background test failures are resolved at this baseline.
- The View Range warning now uses `text_white`; the older green-warning example
  must not be repeated as a current defect.
- The guide distinguishes legacy, View Range, and compiled ComboBox contracts.
  The old documentation mismatch is not a new current finding.
- Core rename previews point to the promoted command-local windows; former
  shared forms are explicitly retained as legacy previews.
- Focus, contrast, long-alert layout, Recall preview fidelity, and the palette
  contract remain relevant concerns, with the current evidence/limits above.

## Suggested resumption sequence

This is a recommendation, not an accepted implementation schedule:

1. Recheck the baseline and adjacent SPECs. Start with units, Recall readability,
   long-alert behavior, keyboard focus, and text contrast (GUI26-01 through 05).
2. Verify the compiled ComboBox concern in a live host, then address accessible
   names and work-area behavior (GUI26-06 through 08).
3. Standardize control states, padding, and footer identity/behavior
   (GUI26-09 through 12).
4. Improve Gallery evidence and reconcile palette contracts before broad token
   consolidation (GUI26-13 and 14). Keep dormant Create From Rooms validation
   ahead of adding any production consumer (GUI26-15).

Typography, spacing, radii, and branding still vary across adapters. Before a
broad visual cleanup, document roles for body/caption/header text, field heights,
button sizing, spacing, radii, and footer behavior. Preserve deliberate runtime
and tooling exceptions. No new light/dark toggle or animation system is proposed.

For host acceptance, record exact Revit/pyRevit versions, DPI/work area, fixture,
interaction state, screenshots, keyboard/Narrator results, and any external/model
effects. Check relevant imports against installed versions and official API
documentation before adopting version-specific APIs. Recheck the final diff and
run narrow tests for each eventual change; this review authorizes no release,
merge, or publication operation.
