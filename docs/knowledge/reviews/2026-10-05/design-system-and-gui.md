# Design system and GUI review

Review date: 2026-10-05. Baseline: `1562e96a5f6e23b7368c80e317868a0c059dc165`.
Scope: current tracked design documentation, all repository XAML sources,
resource-loading paths, relevant presentation handlers, and the UI Gallery.
This is a review deliverable; no application code, assets, or model data were changed.

## Assessment and boundaries

The repository has a coherent shared visual foundation and an unusually useful
explicit GUI inventory. The legacy/compiled boundary is documented, most reusable
legacy forms load shared resources, compiled forms share a real WPF adapter,
and the Gallery deliberately limits executable previews. The most consequential
remaining issues concern keyboard focus, readable text, bounded alert messages,
and faithful preview coverage. These should precede cosmetic standardization.

All **53 XAML sources** were parsed and inventoried: **20 Windows, 2 Pages,
1 UserControl, and 30 ResourceDictionaries**. All 20 Window surfaces received
source/layout review; the larger production and compiled surfaces also received
resource/handler tracing. Page/UserControl sources received structural and
resource-boundary review. Locale dictionaries were inventoried and parsed, not
linguistically certified. This is complete source-surface coverage, not complete
live acceptance of every possible interaction.

The review applies the `agent-skills:code-review-and-quality`, `ecc:design-system`,
and `ecc:accessibility` skills. Their web/mobile examples were adapted to desktop
WPF. No source mutation experiment was performed: this is a documentation-only
review of existing behavior. Findings distinguish confirmed source facts from
inferred runtime effects and live checks still needed.

No Revit window was opened or driven for this review. The coordinating review
verified a connected Revit 2024 host, build `24.3.50.51`, IronPython `2.7.12`,
.NET Framework 4.8, and pyRevit `6.5.3.26176+2017`; that establishes availability,
not rendered acceptance. No assertion here equates Python or C# source tests
with Revit rendering, keyboard, screen-reader, DPI, or multi-monitor acceptance.
One isolated WPF layout reproduction instantiated controls without creating or
showing a Window; it is described under GUI-03.

`scripts/export_ui_gallery_window_pngs.py` produces Pillow approximations; any
outputs from it are not evidence of current live rendering. Its `docs/ui-gallery`
output folder does not exist in the reviewed baseline. Gallery
seeded previews also replace production behavior intentionally. Neither source
should be presented as a screenshot-based accessibility audit.

Severity: P1 = urgent serious failure; P2 = actionable functional/usability issue;
P3 = bounded maintenance or dormant-surface issue. No P1 GUI issue was established.
Paths and one-based line references below refer to the reviewed baseline.

## Findings

### GUI-01 — P2: shared styles remove keyboard focus feedback

**Confidence: confirmed source defect; live navigation acceptance outstanding.**

`src/KLCode.Wpf/Resources/KLCodeControls.xaml:43`, `:92`, `:216`, and `:276`
set `FocusVisualStyle` to null for the shared button, segmented radio button,
checkbox, and list-row styles. Their templates provide hover/checked/selected
states but no `IsKeyboardFocused` or `IsKeyboardFocusWithin` replacement.
`lib/GUI/Resources/WPF_styles.xaml:208` does the same for the legacy checkbox.
The compiled consumers actually load these resources before InitializeComponent
through `src/KLCode.Wpf/ThemeBootstrapper.cs:24` and, for example,
`src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/FamilyStudioWindow.xaml.cs:44`.

Tab navigation can therefore put focus on a button or checkbox without the
shared template showing where it is. Selected rows or checked boxes are not
equivalent to the current keyboard target. This affects the five compiled
windows and checkbox-bearing legacy selectors/options forms.

**Remedy:** define a reusable focus adorner or explicit keyboard-focus trigger
for each affected control family. Preserve selection and hover independently.
Do not simply add a focus border to one dialog while leaving the shared style
unchanged. Microsoft describes both supported mechanisms in
[WPF focus visual styling](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/advanced/styling-for-focus-in-controls-and-focusvisualstyle).

**Acceptance:** complete each available form with Tab, Shift+Tab, arrows, Space,
Enter, and the documented cancel action; capture every focus state, including
unchecked checkbox, selected row, radio segment, disabled neighbor, and footer.
Focus must remain visibly identifiable without the mouse.

### GUI-02 — P2: accent and muted text tokens are too dark for their actual backgrounds

**Confidence: confirmed source values and calculated contrast; live rendering outstanding.**

`lib/GUI/Resources/WPF_styles.xaml:11` defines `text_green=#33714F`;
`:22` defines `footer_donate=#407058`; `:201` applies green to Labels;
`:179` supplies footer-link styling. The compiled group-caption and footer
styles use these same colors at
`src/KLCode.Wpf/Resources/KLCodeControls.xaml:331` and `:349`.
The compiled muted text is `#808080` at
`src/KLCode.Wpf/Resources/KLCodeCompiledTokens.xaml:7`.
These are actual text uses, not merely decorative strokes:

- Family Studio group captions and small metadata use those styles at
  `src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/FamilyStudioWindow.xaml:199`
  and `:221`.
- Startup Importer review table headings use green on the panel surface at
  `src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/Views/StartupImportReviewWindow.xaml:31`.
- The View Range warning uses green at
  `KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml:378`.

Opaque sRGB source-pair calculations, using relative luminance and
`(Llighter+0.05)/(Ldarker+0.05)`, give:

| Foreground | Background | Ratio | Source-use assessment |
| --- | --- | ---: | --- |
| KLGreen `#33714F` | KLCharcoal `#1A252B` | 2.69:1 | Weak for small headings/labels |
| KLGreen-secondary `#407058` | KLCharcoal | 2.74:1 | Weak for footer links |
| Gray `#808080` | KLCharcoal | 3.96:1 | Below 4.5:1 normal-text benchmark |
| KLGreen | compiled panel `#22303A` | 2.33:1 | Weak review-table headings |
| KLWhite `#E5E4E2` | KLCharcoal | 12.30:1 | Strong body-text pairing |
| White `#FFFFFF` | button green `#286048` | 7.35:1 | Strong default button pairing |

The 4.5:1 normal-text and 3:1 large-text comparisons are useful review targets;
they are not a claim that this desktop app has undergone normative web WCAG
certification. [WCAG2ICT](https://www.w3.org/TR/wcag2ict/) is informative guidance
for applying WCAG principles to non-web software, not a new normative standard.
No blanket mobile 44-point rule is imposed on these WPF controls.

**Remedy:** introduce foreground-specific accent/muted tokens with sufficient
contrast while retaining existing brand colors for appropriate fills/artwork.
Update both adapters and audit actual color pairs, not palette names alone.
Preserve white text on green buttons; that pair is not the problem.

**Acceptance:** calculate all enabled text-state pairs after changes; verify
small captions, warnings, footers, hover, selection, and disabled state in Revit.
Run Windows high-contrast testing separately rather than assuming a dark theme
provides high-contrast support.

### GUI-03 — P2: long alert messages do not have a bounded scroll viewport

**Confidence: confirmed layout pattern and isolated WPF reproduction; full alert rendering still unverified.**

The compiled alert is fixed at `440 x 300`, with a `ScrollViewer` inside a
vertical `StackPanel` at `src/KLCode.Wpf/Views/KlaAlertWindow.xaml:40`–`:46`.
That parent measures its children with unbounded vertical space, so merely
setting `VerticalScrollBarVisibility=Auto` does not constrain the message.
The legacy alert is fixed at `440 x 255` and has an unbounded message TextBlock
with no ScrollViewer at `lib/GUI/CustomAlert.xaml:57`–`:59`.

This is reachable with real compiled messages: Family Studio adds up to eight
file/error entries in `BuildRefreshDetails` at
`src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/FamilyStudioWindow.xaml.cs:493`.
Paths and exception text have no suitable fixed upper length.

**Reproduction performed:** in an STA PowerShell process, construct the same
StackPanel → heading plus ScrollViewer → wrapping TextBlock pattern, supply
120 repetitions of a warning/path sentence, and measure/arrange with 330 x 190
available space. The parent actual height became `1635.96`; the viewer reported
`ExtentHeight=1620`, `ViewportHeight=1620`, and `ScrollableHeight=0`.
No Window was created or shown and no Revit API was called. This validates the
layout mechanism, not the final alert's host appearance.

**Remedy:** place heading and ScrollViewer in a bounded Grid with Auto and `*`
rows, and keep dismissal controls in their own fixed/Auto row. Give the legacy
alert an equivalent bounded message region. Consider selectable/copyable details
where long technical failure messages are expected.

**Acceptance:** short, multi-paragraph, long-path, and eight-error alerts retain
visible dismissal controls and allow scrolling to the final character by mouse
and keyboard. Repeat at 100%, 150%, and 200% display scaling.

### GUI-04 — P2: several inputs and per-row checkboxes lack explicit accessible identity

**Confidence: confirmed source omission; actual UI Automation names require live inspection.**

The search box in `lib/GUI/SelectFromDict.xaml:105` is preceded only by an Image;
there is no input label association or AutomationProperties.Name in its loader.
Family Studio's Category/Type/Parameter/Root filter captions are adjacent
TextBlocks at
`src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/FamilyStudioWindow.xaml:76`
onward, without `LabeledBy` relationships. The result-row checkboxes at `:114`
and `:144` have no content or explicit name, and the Startup Importer review
row checkbox at
`src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/Views/StartupImportReviewWindow.xaml:45`
has the same pattern. A control's code identifier is not a user-facing label.

Standard WPF peers provide much accessibility behavior automatically, so absence
of an attached property alone is not proof that every field is unreadable to
a screen reader. These particular controls need inspection because their
meaning is supplied visually by siblings, icons, or data rows.

**Remedy:** use named visible labels and `AutomationProperties.LabeledBy` for
inputs; bind row-checkbox accessible names to family/item identity; give the
icon-adjacent filter an explicit meaningful name. Keep visible and accessible
strings aligned with compiled localization dictionaries. Microsoft discusses
[accessible WPF control naming](https://learn.microsoft.com/accessibility-tools-docs/items/wpf/button_name)
and [UI Automation best practices](https://learn.microsoft.com/en-us/dotnet/framework/ui-automation/accessibility-best-practices).

**Acceptance:** inspect the actual UI Automation tree with Accessibility Insights
or equivalent; record Name, Role, Value, enabled state, and row association.
Use Narrator to distinguish multiple checkboxes and the two Browse buttons
without relying on screen position. Confirm meaningful status/error announcements.

### GUI-05 — P2: the Match Recall gallery preview discards the chrome it intends to review

**Confidence: confirmed code path.**

`KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py:552`
loads the branded `clipboard_window.xaml`, then `:573` assigns `self.Content = panel`.
That replaces the entire root content containing the header, Close button,
footer, and `content_host`. The window remains borderless. The sample panel
contains only text and a ListBox, so the preview no longer exposes its intended
visible Close control or the actual clipboard-content form.

The production RecallWindow correctly assigns `self.content_host.Content`
at `lib/match/clipboard.py:466`. This demonstrates the intended host boundary.

**Remedy:** assign fictional content to `content_host.Content`, preserve the
shell, and distinguish shell-only coverage from full ClipboardContent coverage.
If full content is previewed, use a safe data/presentation adapter whose handlers
cannot save memory files or touch the Revit model.

**Acceptance:** open the Gallery preview, verify header/footer and visible Close,
and compare the actual content host with the production source. No file or model
side effects may occur. Do not call shell-only preview coverage full recall
workflow acceptance.

### GUI-06 — P2: the largest fixed window has no smaller-work-area strategy

**Confidence: confirmed fixed sizing; impact is conditional on display/work area and needs live testing.**

Family Studio requests `1180 x 740` at
`src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/FamilyStudioWindow.xaml:5`.
Its `KlaWindowStyle` sets `ResizeMode=NoResize` at
`src/KLCode.Wpf/Resources/KLCodeControls.xaml:15`. Neither the constructor nor
the style bounds it to the monitor work area. The right detail column is a
fixed 460 units and toolbar/filter rows are fixed height.

A 1920 x 1080 display at 150% scaling has about 1280 x 720 logical units before
taskbar deductions, less than this window's height; at 200% both dimensions are
smaller. This is a concrete fit risk, not evidence that the current user's
monitor clipped the window. Other fixed dialogs need the same acceptance check
but do not all require a wholesale responsive redesign.

**Remedy:** define a documented supported minimum work area and provide bounded
initial sizing plus a resize/scroll strategy for the large browser. Keep primary
actions reachable; allow filters to reflow within a row whose height can grow.
Do not alter approved baseline geometry without validating the resulting layout.

**Acceptance:** every primary action and close path remains reachable at 100%,
125%, 150%, and 200% scaling on the supported minimum work area, including moving
between monitors with different DPI and enlarged text. Long names/paths do not
obscure identity or actions.

### GUI-07 — P3: dormant CreateFromRooms silently substitutes zero after invalid input

**Confidence: confirmed handler behavior; no current production invocation established.**

`lib/GUI/Tools/CreateFromRooms.py:148` filters typed characters with a pattern
that permits repeated decimal points and rejects negative signs, without a
complete final-value validation path. `button_run` at `:164` clears the filter
and closes the dialog before parsing; its bare exception handler at `:180`
silently assigns `offset=0`. Empty/no-selection and pasted-invalid cases can
therefore return a fallback rather than a correctable inline error. The input
is labeled centimeters at `lib/GUI/Tools/CreateFromRooms.xaml:200`.

Current documented use is the Gallery, which uses safe replacement handlers.
This is a reusable-component readiness issue, not a claim that a visible
production command currently creates elements at the wrong elevation.

**Remedy:** validate selection and the complete offset value before closing;
keep the dialog open with a descriptive error; make allowable sign, decimal
separator, and range explicit. Preserve cancellation as cancellation.

**Acceptance:** valid positive/negative values according to the intended policy,
empty text, repeated dots, pasted text, no match, and cancelled selection all
produce an explicit documented outcome. Invalid input cannot silently become zero.

### GUI-08 — P3: the general ComboBox property tables describe a different template

**Confidence: confirmed documentation/implementation discrepancy.**

`DESIGNSYSTEM.md:137`–`:139` describes the ComboBox arrow as `text_white`, its
disabled body as near-black, and its disabled arrow as gray. The general shared
template instead uses `Fill="White"` at
`lib/GUI/Resources/WPF_styles.xaml:342`; its disabled trigger at `:423` changes
only foreground. `DESIGNSYSTEM.md:182` lists item padding `4,3`, while the shared
ComboBoxItem uses `Padding="2"` at `lib/GUI/Resources/WPF_styles.xaml:459`.
The View Range local template has its own behavior and must remain separately
identified; it cannot establish what the shared template does.

**Remedy:** split legacy shared, View Range local, and compiled ComboBox contracts,
record their actual values, and distinguish current implementation from desired
future behavior. Add small source-contract checks where this distinction matters.

**Acceptance:** every listed property resolves to a named template and exact
implementation, including enabled/disabled/hover/selected states. Do not change
runtime styling solely to make an inaccurate historical table pass.

## Design-system contract conflict and test evidence

There is a separate confirmed validation conflict, recorded by the coordinating
repository review rather than counted twice as a GUI finding.
`DESIGNSYSTEM.md:35`–`:38` accurately says the legacy dictionary currently repeats
palette values and the compiled adapter consumes the palette file. However,
`src/KLCode.Wpf/Tests/KLCode.Wpf.Source.Tests/DesignSystemResourceContractTests.cs:77`
asserts that the legacy dictionary merges `KLCode_palette.xaml` and contains no
root brush definitions. At `:86` that assertion fails on the current code.

The coordinating review executed this source test project: **12 passed,
1 failed**, with that assertion as the failure. This is not evidence of a broken
XAML loader; it is a mismatch between the accepted/documented transitional
architecture and an enforced test contract. Decide which contract is intended,
then update implementation or tests through a separately reviewed change.
Consolidation is sensible maintenance, but not automatically an urgent runtime
fix, and must respect IronPython and compiled resource-loading compatibility.

The coordinated Python suite reported **195 tests, 1 skipped, no failures**;
those checks cover source contracts and host-independent behavior. They do not
negate GUI-01 through GUI-08. C# Family Studio Core/Database and Startup Importer
Core/UI tests also passed; see the overall review's validation record for commands
and exact project scope.

## Complete surface inventory and review depth

Depth notation: **D** = XAML plus loader/resource and relevant handler tracing;
**S** = complete source/layout inspection, with shared loader traced;
**R** = parsed/inventoried resource or wrapper, without live or linguistic review.
All dimensions below are WPF device-independent units. Listed paths are exact
repository-relative paths; `:1` identifies the root declaration of each surface.

| Surface / source | Size | Depth | Resource boundary and coverage |
| --- | --- | --- | --- |
| `lib/GUI/SelectFromDict.xaml:1` | 432 x 576 | D | Shared `my_WPF`; canonical collection/filter/all-none behavior traced; GUI-01/04; long-name and keyboard acceptance pending |
| `lib/GUI/CustomAlert.xaml:1` | 440 x 255 | D | Shared dictionary; information/warning code; GUI-02/03 |
| `lib/GUI/FindReplace.xaml:1` | 350 x 253 | D | Shared dictionary; generic preview form and property adapters; no preview of production model changes |
| `lib/GUI/RenameViews.xaml:1` | 350 x 253 | D | `lib/Renaming/BaseClass_FindReplace.py:28` loads shared resources and form; field associations need GUI-04 acceptance |
| `lib/GUI/RenameSheets.xaml:1` | 620 x 253 | D | `lib/GUI/RenameSheets.py:16`; independent name/number fields and injected run handler |
| `lib/GUI/DuplicateSheets.xaml:1` | 800 x 491 | D | `lib/GUI/DuplicateSheets.py:16`; nested checkbox style inherits shared template; options, naming, browser sections inspected |
| `lib/GUI/Tools/CreateFromRooms.xaml:1` | 400 x 406 | D | Shared loader plus nested list overrides; current Gallery-only use; GUI-07 |
| `lib/GUI/_templates/KLCodeMainTemplate.xaml:1` | 432 x 576 | S | Visual authority with outlined wordmark; Gallery template fixture, not a second production selector |
| `lib/match/clipboard_window.xaml:1` | 420 x content height | D | Shared shell; real `ClipboardContent` is injected by `RecallWindow`; GUI-05 concerns Gallery replacement only |
| `KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml:1` | 760 x 430 | D | `forms.WPFWindow`, local full palette/ComboBox templates, runtime shared-wordmark injection; warning contrast and field association checked |
| `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/Script.xaml:1` | 350 x 289 | S | Local experimental form, shared-resource loader, extra case actions; isolation is intentional |
| `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/Script.xaml:1` | 620 x 289 | S | Same prototype boundary, separate name/number input groups; no blanket consolidation request |
| `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml:1` | 432 x 576 | D | Shared dictionary and selector pattern; CSV actions visible; production report/export correctness covered by tools review |
| `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml:1` | 900 x 520 minimum | D | Local palette/DataGrid styles; explicit launcher allowlist and disabled host-dependent entries traced |
| `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml:1` | 360 x 160 | S | Intentionally minimal self-contained Window; safe catalog preview fixture |
| `src/KLCode.Wpf/Views/KlaAlertWindow.xaml:1` | 440 x 300 | D | Compiled shared adapter; kind/icon/title/message handling; GUI-01/02/03 |
| `src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/FamilyStudioWindow.xaml:1` | 1180 x 740 | D | Compiled adapter and tool strings; search, filter, list/grid selection, detail, batch, empty state, warning path; GUI-01/02/04/06 |
| `src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/Views/StartupSourcePickerWindow.xaml:1` | 560 x 470 | D | Compiled adapter; native file picker, validation status, CanReview, explicit default/cancel buttons |
| `src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/Views/StartupImportReviewWindow.xaml:1` | 860 x 640 | D | Compiled adapter; review list, row-action gating, selected-item detail, count, default/cancel buttons; GUI-01/02/04 |
| `src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/Views/BlockingIssuesWindow.xaml:1` | 560 x 520 | D | Compiled adapter; grouped blocking issues, disabled import, copy-report path; variable issue-length acceptance pending |
| `lib/match/clipboard_page.xaml:1` | docked | R | Minimal Page wrapper for `MatchHistoryClipboard`; does not independently define a dialog |
| `lib/match/clipboard_content.xaml:1` | host-sized | D | UserControl shared by docked and recall contexts; locale/icon resources; search, regex, table, check/paste states inspected |
| `lib/customprops/pane_ui.xaml:1` | docked | S | Independent light palette, native editable ComboBox and scrollable dynamic panel; host callbacks belong to separate tools review |

### Resource inventory: remaining 30 XAML sources

| Exact file or enumerated file set | Count | Depth and purpose |
| --- | ---: | --- |
| `lib/GUI/Resources/WPF_styles.xaml` | 1 | D: legacy tokens, all shared templates, focus/disabled/hover/scroll behavior |
| `lib/GUI/Resources/KLCode_palette.xaml` | 1 | D: data-only palette; compiled project links it as `Resources/KLCodePalette.xaml` |
| `src/KLCode.Wpf/Resources/KLCodeControls.xaml` | 1 | D: every compiled style and merged-resource dependency |
| `src/KLCode.Wpf/Resources/KLCodeCompiledTokens.xaml` | 1 | D: surfaces, semantic status colors, font token |
| `src/KLCode.Wpf/Resources/Strings/ResourceDictionary.en_us.xaml` | 1 | R: common chrome strings |
| `src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Resources/Strings/ResourceDictionary.en_us.xaml` | 1 | R plus selected status/label tracing; English fallback only |
| `src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/Resources/Strings/ResourceDictionary.en_us.xaml` | 1 | R plus selected status/validation tracing; English fallback only |
| `lib/match/clipboard.Icons.xaml` | 1 | R: local icon geometries and clear-button style |
| `lib/match/clipboard_ui.ResourceDictionary.{chinese_s,de_de,en_us,es_es,fr_fr,ko,pt_br,ru}.xaml` | 8 | R: each named locale file parsed; no translation certification |
| `lib/customprops/pane_ui.ResourceDictionary.{chinese_s,de_de,en_us,es_es,fr_fr,pt_br,ru}.xaml` | 7 | R: each named locale file parsed; dynamic-field behavior not inferred from strings |
| `checks/locale/Checks.ResourceDictionary.{chinese_s,de_de,en_us,es_es,fr_fr,pt_br,ru}.xaml` | 7 | R: each named locale file parsed; audit framework owns runtime use |

The brace lists above enumerate actual separate files; 23 visual roots plus
30 dictionaries reconcile to 53, with no binary assets or generated build-output
XAML counted as additional authored surfaces.

## Architecture, content, and state review

**Resource loading.** `lib/GUI/WPF_Base.py:36` assigns the legacy dictionary
before `wpf.LoadComponent`. The prototypes currently use this loader too;
historical notes describing their former copied dictionaries were not taken as
current truth. View Range intentionally injects only the shared wordmark after
loading its local dictionary. Compiled resource loading goes through
`ThemeBootstrapper.Apply`; the csproj links the data-only palette into a CLR
resource with a different packaged name. The difference between source filename
and packaged filename is intentional and is not a broken relative-path finding.

**Component reuse.** Action buttons, close buttons, filters, checkboxes, list
styling, footer text, and chrome are centralized within each runtime boundary.
Duplicated palette definitions remain a documented consolidation opportunity.
Blanket replacement of command-local overrides or standard pyRevit/native forms
would ignore intentional runtime and prototype boundaries. The generic legacy
Border/DockPanel styles have broad implicit reach: inspect nested consumers
before changing their defaults.

**Typography and spacing.** Shared legacy buttons explicitly use Arial;
compiled windows default to Segoe UI while compiled buttons use Arial and their
brand uses the bundled Audiowide font. The legacy brand is vector geometry.
These are traceable implementation choices, not evidence of an accidental font
download. Heading/body/caption sizes and spacing are repeated locally rather
than expressed as a full type/spacing token scale. The numerous 10–12-unit
captions, fixed header lanes, fixed name-field widths, and compact 18-unit Close
control need enlarged-text and pointer testing. There is no evidence-based reason
to assign an arbitrary mobile target-size requirement to this desktop application.

**Information hierarchy.** Family Studio has explicit toolbar, filters, results,
detail, batch actions, and empty state. Startup Importer separates source selection,
blocking problems, and actionable review with textual status and disabled actions.
These are meaningful strengths. The dense Duplicate Sheets form combines naming,
browser organization, copied elements, existing-view choices, and duplication
modes; test it with task-based users before deciding whether to split it.
The production-tools review separately covers View Range's missing relative-level
sentinel choices, success reporting after failed level updates, and the meaning
of Reset after Apply. Those are functional correctness findings, not merely
styling differences, and should be read alongside this GUI assessment.

**Feedback and recoverability.** Startup source validation presents text plus
state-dependent color, and its action is bound to `CanReview`; it is not
color-only feedback. Review uses `CanImport`, and the blocking window disables
import while exposing a copy-report button. Family Studio provides empty-state
clear/refresh actions, updates batch counts, and funnels operation failures into
the shared alert. GUI-03 matters because these otherwise useful error paths may
produce long messages. CreateFromRooms is the exception where validation closes
early and suppresses the explanation.

**Interaction consistency.** Source/review importer dialogs explicitly define
default and cancel actions; other forms rely on their visible close buttons and
inherited host/window behavior. This is a keyboard acceptance gap, not proof that
Alt+F4 fails. Family Studio searches on Enter; the search icon is a TextBlock,
not an invokable button. Its tooltip describes searchable fields without saying
Enter, so consider a discoverable search affordance during UX testing. Unavailable
Family Studio modes and type-edit actions are intentionally disabled with tooltips;
do not report them as functioning features or arbitrary dead buttons.

**Docked versus modal theme boundary.** `clipboard_content.xaml` and
`customprops/pane_ui.xaml` intentionally have white backgrounds. Recall hosts
the former inside a dark shell and supplies parent implicit styles, whereas the
docked version does not use the same shell. The Gallery currently substitutes
content and cannot prove this mixed-theme composition is legible. Inspect both
contexts, including inherited TextBlock foreground and GridView headers, before
claiming they are dark-theme compliant or changing shared styles. This remains a
targeted live check, not a confirmed rendered defect in this review.

**Localization.** Compiled English resource dictionaries and locale fallback
are explicit; unsupported requested locales fall back to a complete dictionary.
Legacy custom dialogs retain embedded English strings, while imported/docked
components carry multiple locale files. Do not imply complete translated support.
Any future localization needs text-growth, right-to-left policy, labels, shortcuts,
and numeric-format decisions in addition to translating strings. See Microsoft's
[WPF globalization guidance](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/advanced/wpf-globalization-and-localization-overview).

**Performance.** Family Studio limits result queries to 200; its grid uses a
UniformGrid and will realize those items, while list/detail paths query and bind
synchronously. Limit200 is a protective bound, but the result count does not
identify truncation; query completeness belongs to the tools review. Refresh and
file parsing may be long operations; responsiveness, busy indication, cancellation,
and recovery need host timing measurements. Do not move Revit API work to a
background thread as a generic performance fix.

**Gallery trust boundary.** Registry metadata includes all 20 Window sources.
Five compiled windows are honestly catalog-only. Standard pyRevit selectors,
alerts, file/folder pickers, and progress windows are separate approved patterns.
`lib/ui_gallery/catalog.py` confines discovery to the repository and skips
symlink directories; `classification.py` rejects bindings/resources/events for
generic preview, and `preview.py` then limits it to the one approved fixture.
Incomplete event-name classification is not automatically an arbitrary-XAML
execution vulnerability because the final exact-path allowlist still applies.
Known seeded launchers use explicit handlers; the preview safety model is sound
in the reviewed paths, subject to preserving it during GUI-05 remediation.

## Provisional 10-dimension source audit

Scores use the design-system skill's 0–10 scale as a **source-readiness rubric**:
0 = no established support, 5 = coherent foundation with material gaps,
10 = coherent implementation plus verified acceptance evidence. These are
provisional engineering judgments with stated evidence, not measured visual
quality or accessibility conformance scores. No aggregate score is calculated.

| Dimension | Provisional score | Evidence and next improvement |
| --- | ---: | --- |
| Color consistency | 7 | Shared palettes/adapters dominate; documented duplicates and local exceptions; resolve foreground contrast at `WPF_styles.xaml:11` and `KLCodeControls.xaml:331` before decorative palette changes |
| Typography hierarchy | 6 | Compiled body/header/muted styles are explicit; legacy labels and local sizes remain ad hoc; document a type scale and test small text at `KLCodeControls.xaml:355` |
| Spacing rhythm | 6 | Repeated 24-unit headers, 86-unit edge columns, action-button rules; local 2/5/6/8/10/12/14/16 spacing rather than semantic tokens; validate before consolidating |
| Component consistency | 7 | Shared controls and thin wrappers across 20 surfaces; intentional runtime adapters; Gallery Recall violates shell composition at `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py:573` |
| Responsive/work-area behavior | 3 | Fixed-size forms and bounded lists, but large fixed Family Studio has no fit strategy at `FamilyStudioWindow.xaml:5`; GUI-06 |
| Dark-mode completeness | 6 | Custom dialogs consistently use dark resources; docked/light and native surfaces are deliberate boundaries; check nested Recall inheritance, no light/dark toggle requirement invented |
| Animation | N/A | Only ordinary popup transitions surfaced; no product motion specification or observed animation behavior to rate. Check reduced-animation/high-contrast expectations if custom motion is added |
| Accessibility | 3 | Native controls help; explicit null focus styles, low text contrast, and unlabeled-input risks need GUI-01/02/04; no screen-reader run performed |
| Information density | 6 | Clear browser/review groupings and compact forms; dense Duplicate Sheets and large browser need task and long-content testing, not an assumed redesign |
| Polish/state completeness | 5 | Empty states, disabled actions, statuses, and warnings exist; alert overflow and incomplete preview coverage prevent claiming full polish; GUI-03/05/07 |

There is no evidence for a useful “AI-generated design” diagnosis. Gradients,
radius choices, and branding should be judged against this repository's intent
and actual usability rather than a generic web-design style blacklist.

## Acceptance plan and recommended order

1. **Shared readability and focus:** resolve GUI-01/02 in both resource adapters;
   verify actual UI Automation names for GUI-04 before broad relabeling. Add
   focused source-contract checks and a keyboard/screen-reader acceptance record.
2. **Messages and review fidelity:** fix GUI-03/05; seed long errors, long names,
   empty results, and disabled actions. Preserve the Gallery's no-model-write
   contract and explicitly label partial previews.
3. **Work-area behavior:** validate GUI-06 with the largest browser first, then
   every smaller form. Record monitor dimensions, DPI, host version, text scale,
   screenshot provenance, and operation outcomes.
4. **Component readiness and documentation:** address GUI-07 before promoting a
   CreateFromRooms consumer; correct GUI-08 and reconcile the failing palette
   contract. Introduce token consolidation only through a compatible tested plan.

| Live acceptance area | Minimum scenarios | Required evidence |
| --- | --- | --- |
| Shared legacy GUI | selector empty/one/many/filtered; filter-all-none; rename no-op/cancel; duplicate options | Keyboard traversal and screenshots from actual Revit; no accidental model writes during preview |
| Shared alerts | short, long, Unicode, long path, eight errors; warning/information | Last message line and close controls reachable; scroll extent/viewport verified |
| Compiled Family Studio | list/grid, search Enter, filters, no results, batch, unavailable items, warning | Correct visible/checked/selected distinctions; text identity retained; busy/recovery behavior measured |
| Startup Importer | invalid source/settings, long status, blocking issues, zero/all/subset selection, cancel | Accurate enabled state, all errors readable, no import until intended confirmation |
| Accessibility | Tab/Shift+Tab/arrows/Space/Enter/Escape or documented close; Narrator; high contrast | UIA names/roles/states, visible focus, non-color status, no unreachable primary action |
| Scaling | 100/125/150/200%, smaller work area, mixed monitors, enlarged text | No clipped primary action; fit/scroll behavior; readable names and paths |
| Match and Custom Props | docked and recall hosts, long parameter names, regex error, empty history | Actual nested colors, named icon controls, accessible dynamic fields, bounded scrolling |
| Gallery | each launchable entry, every disabled compiled/native-data entry, fixture preview | Registry-to-window correspondence, visible dismissal, no production side effects |

The review is complete as a source-based design/GUI assessment. The table above
defines the remaining live evidence needed before describing the GUI as visually
or accessibly accepted across supported hosts.
