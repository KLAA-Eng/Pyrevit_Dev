# Remaining custom-window component review

This review preserves its `e366db7` baseline. The owner subsequently removed
both legacy rename forms; the [retirement/filter record](2026-10-28-gallery-retirement-and-preview-filter.md)
owns that later change. Its two legacy inventory rows below are historical.

Date: 2026-10-28. Baseline: `e366db7` on `dev.GUI-Clean`, plus the requested
Close-label correction. The source inventory contains 20 standalone Window
XAML files: the main template and the 19 remaining windows reviewed below.
Model Checker has no Window source in this checkout and is not counted.
Recall's nested UserControl was included because its standalone shell hosts it.
Other docked surfaces and native/pyRevit dialogs are outside this review.

The [consolidation plan](../../../plans/custom-window-consolidation.md) owns
task status. [DESIGNSYSTEM.md](../../../DESIGNSYSTEM.md#how-the-code-fits-together)
owns the plain-English implementation explanation. This review identifies
candidate components and migration risks; it does not authorize migration or
change any production command behavior.

## Conclusion

The reference covers a basic search-and-select form, not the full range of
existing form content. The most useful next additions are labeled field/groups,
bounded result/message surfaces, ComboBox/radio/toggle controls, and richer
collection/status/preview treatments. Reuse existing compiled styles where they
fit rather than inventing a second implementation of each component.

Keep the main template compact. Demonstrate additional components in separate
Gallery specimens rather than putting every control into the selection form.
Share appearance and layout; preserve each tool's data rules and lifecycle.

## Findings and incorporation candidates

### CW28-01 — High migration risk: checked-list presentation has a code contract

`SelectFromDict.xaml:133` and `Tools/CreateFromRooms.xaml:177` pass a nested
TextBlock as checkbox content. Their handlers read `sender.Content.Text`
(`SelectFromDict.py:157`, `Tools/CreateFromRooms.py:144`). The foundation's
checkbox instead supplies string content through a shared wrapping template
(`KLCodeFoundation.xaml`, `KlaFoundationCheckBox`). Replacing styles alone is
not proven compatible and can break label lookup or render content incorrectly.

Selection rules also differ: SelectFromDict confirms the canonical collection
(`SelectFromDict.py:184–202`), Steel PSF confirms checked visible rows
(`Steel PSF.pushbutton/script.py:224–233`), and Create from rooms clears checks
outside the current filter (`Tools/CreateFromRooms.py:120–136`).

**Candidate:** shared search/checked-list presentation with an explicit row
content contract. Retain per-tool filtering, all/none, and confirmation policy.
**Validate:** real WPF content binding plus search/check/clear/confirm across
hidden rows and single/multiple selection. Do not normalize behavior silently.

### CW28-02 — High reuse: aligned fields and naming groups are missing

The Find/Replace/Prefix/Suffix form is repeated in `FindReplace.xaml:120–166`,
`RenameViews.xaml:119–165`, `RenameSheets.xaml:122–250`, and
`DuplicateSheets.xaml:160–323`. Core rename has the same fields in compact
command-local layouts. Create from rooms adds a numeric field with a unit label;
Startup source picker repeats read-only path, Browse, and validation status rows.

**Candidate:** labeled input row, group caption/border, four-field naming group,
and read-only path/action/status row. Styles own spacing and text roles; callers
own values, units, validation, callbacks, and actual file picking.
**Validate:** one/two-column variants, long labels/paths, error/disabled states,
tab order, and compatibility with existing named controls/handlers.

### CW28-03 — High value: bounded feedback and multiline readouts need their own roles

`CustomAlert.xaml:57–60` puts heading/message in a StackPanel inside a fixed
440 x 255 window; long content has no scrolling path. The compiled alert has a
ScrollViewer inside a vertical StackPanel (`KlaAlertWindow.xaml:40–47`), which
does not by itself demonstrate a constrained viewport. Blocking issues has
unwrapped issue text while horizontal scrolling is disabled (`:22–25`).
These are source-layout risks, not newly claimed live-render failures.

Core rename uses selectable multiline results and keeps unresolved operations
open (`lib/find_replace/window.py:10–34`). Its fixed expanded heights belong to
that workflow today. The foundation's 32-high input is not an appropriate
multiline result or report control.

**Candidate:** bounded message surface, summary/details result panel, read-only
selectable multiline text, and severity banner/chip styles.
**Validate:** long/newline messages, collapsed empty details, copy/select,
scrolling under constrained height, and existing retry/quiet-success behavior.

### CW28-04 — Required control families: ComboBox, RadioButton, ToggleButton

View Range uses level ComboBoxes (`MainWindow.xaml:337/376/398`); Family Studio
uses filters and segmented radio groups (`FamilyStudioWindow.xaml:48–89`);
DuplicateSheets uses three duplicate-mode RadioButtons (`:795–805`); Recall uses
regex/category toggles (`clipboard_content.xaml:17–54`). Gallery also has local
ComboBox styling. None is covered by the current foundation.

**Candidate:** shared dropdown/popup, exclusive-option, and toggle styles with
the existing actual states. The compiled ComboBox's selection presenter lacks
`IsHitTestVisible="False"` (`KLCodeControls.xaml:165`); test text-area clicks when
choosing an implementation rather than promoting it unchanged.
**Validate:** full-surface opening, keyboard selection, popup scrolling, long
labels, focus, checked/selected, hover, pressed and disabled behavior.

### CW28-05 — Rich collections must separate selection, checking and details

Recall uses ListView/GridView columns (`clipboard_content.xaml:59–99`), Startup
review uses checked multi-column rows plus separate selected-row details
(`StartupImportReviewWindow.xaml:29–87`), and Family Studio supports list/card
views, selected preview and checked batch items (`FamilyStudioWindow.xaml:107–225`).
Gallery has a DataGrid and caller/detail lists (`Gallery.xaml:81–138`). A basic
ListBox with a single `IsChecked` property cannot represent all these roles.

**Candidate:** row/header/cell skins, optional card/thumbnail and preview/empty
states, plus reusable metadata and severity-chip presentations. Keep columns,
item types, query logic, selected detail and checked batch state tool-owned.
**Validate:** selected versus checked state, filtered counts, disabled/non-actionable
rows, missing previews, long cells, and copy/keyboard behavior. DataGrid and
ListView/GridView are separate control families, not interchangeable templates.

### CW28-06 — Action/icon roles need more than the template's two button sizes

Recall has icon-only and icon-plus-label actions with disabled Paste states
(`clipboard_content.xaml:164–200`). View Range has Apply/Reset at 120/130 widths
(`MainWindow.xaml:427–430`); Steel PSF has CSV action rows (`SteelPsfDialog.xaml:108–141`).
Compiled controls already distinguish standard, small, ghost, link and segment
roles (`KLCodeControls.xaml:35–85`).

**Candidate:** approved fixed-width action variants, action-group spacing,
icon/text alignment and accessible icon-only buttons. Preserve current action
placement and select replacement artwork with the owner.
**Validate:** caption fit, disabled icon/text colors, keyboard identity/focus,
paired/three-column groups and default/cancel semantics. Do not force every
workflow into 104/216 widths or use arbitrary per-window overrides.

### CW28-07 — Shared chrome must preserve showing, closing and resizing policy

Current differences are material: FindReplace closes then calls `sys.exit()`
(`FindReplace.py:86–89`); DuplicateSheets closes before its callback (`:36`);
Core rename stays open for some outcomes; View Range is resizable/modeless and
removes host events on close (`script.py:773–778`); Recall persists on Closing
(`clipboard.py:478–489`). Recall content is also used in a docked panel.

**Candidate:** explicit modal/modeless and fixed/resizable shell variants with
caller-owned lifecycle hooks. The new loader correctly does not show a window
or change its DataContext; retain that boundary.
**Validate:** owner, close/cancel, persistence, cleanup, rerun and work-area/DPI
behavior per caller. Create from rooms closes before parsing and falls back to
offset zero (`:164–185`); flag that for separate behavioral work, not a style fix.

### CW28-08 — The compiled adapter remains a separate integration task

The foundation merges `WPF_styles.xaml`, including its legacy handler-named
Header resource (`:270–305`). The C# project currently packages palette/font
(`KLCode.Wpf.csproj:29–33`) and loads its own controls/localization through
`ThemeBootstrapper.cs:23–25`. The Python foundation is therefore not yet a
drop-in compiled resource package. No failed C# build is claimed here.

**Candidate:** extract compatible shared visual resources/assets while keeping
Python and C# event wiring and localization adapters. Build against supported
targets and validate source/template/resource contracts before adoption.
Keep all five compiled Gallery previews deferred as already agreed.

## Complete remaining-window inventory

Paths below are repository-relative; abbreviated command/assembly paths are
unambiguous within the current inventory. Line evidence refers to this baseline.

| Window | Additional body/components or constraint | Evidence |
| --- | --- | --- |
| KL&A list selection | Search/checked-list composite; canonical hidden checks; constructor shows modal | `lib/GUI/SelectFromDict.xaml:123–144`; `.py:65–98,184–202` |
| Custom alert | Icon, severity heading, wrapped message, dismissal | `lib/GUI/CustomAlert.xaml:45–60` |
| Find and replace | Four labeled fields; special close behavior | `lib/GUI/FindReplace.xaml:120–166`; `.py:86–89` |
| Duplicate sheets | Repeated naming groups, option grid, exclusive mode, callback | `lib/GUI/DuplicateSheets.xaml:160–323,548–674,795–805` |
| Create from rooms | Unit-labeled numeric input, single choice and validation | `lib/GUI/Tools/CreateFromRooms.xaml:201`; `.py:120–185` |
| Legacy rename views | Naming group; model-coupled legacy loader | `lib/GUI/RenameViews.xaml:119–165`; `lib/Renaming/BaseClass_FindReplace.py:26–42` |
| Legacy rename sheets | Two naming groups, caller-owned showing/callback | `lib/GUI/RenameSheets.xaml:122–250`; `.py:17,65` |
| Core rename views | Naming group, case actions, result summary/details | `FindReplace - Views.pushbutton/Script.xaml:46–83` |
| Core rename sheets | Two-column naming groups and results | `FindReplace_Sheets.pushbutton/Script.xaml:51–111` |
| View Range | Dropdowns, numeric table/readouts, status, resizable/modeless | `ViewRange.pushbutton/MainWindow.xaml:6,337–430`; `script.py:773–778` |
| Match Recall | Hosted content, clearable/toggle search, multicolumn checked list, icon actions | `lib/match/clipboard_window.xaml`; `clipboard_content.xaml:17–200` |
| Steel PSF | Checked list plus CSV/primary action groups | `Steel PSF.pushbutton/SteelPsfDialog.xaml:108–141`; `script.py:224–233` |
| Family Studio | Segments, filters, rich list/card views, status chips, preview, metadata | `FamilyStudioWindow.xaml:48–89,107–239` |
| Startup source picker | Read-only path/Browse/status groups and gated Review | `StartupSourcePickerWindow.xaml:25–68` |
| Startup review | Summary chips, checked list, selected detail/preview, count-dependent Import | `StartupImportReviewWindow.xaml:18–100`; view model `:53–85` |
| Blocking issues | Warning banner, issue groups/report, Copy, disabled Import | `BlockingIssuesWindow.xaml:16–37` |
| Compiled alert | Semantic icon/message/OK; owner-modal; no normal footer/header Close | `src/KLCode.Wpf/Views/KlaAlertWindow.xaml:9–54`; `.xaml.cs:31–52,75–83` |
| Gallery catalog | ComboBox, DataGrid, caller/details, availability and state controls | `UI Gallery.pushbutton/Gallery.xaml:5,34–65,81–138` |
| Gallery fixture | Minimal native-chrome wrapping text; intentional test exception | `UI Gallery.pushbutton/fixtures/PreviewFixture.xaml:1–8` |

## Recommended next slice

First define the checked-row content contract and add labeled field/naming-group
and bounded result/message specimens. Then add dropdown/radio/toggle families.
These cover more existing forms than adding advanced card/browser controls first.
Keep selection rules and result/close policy explicit in each specimen/caller.
Use the existing Gallery to review the parts before production migration.

## Close-label correction and evidence

The original Close lettering's measured visible center was approximately
`(30.00, 10.15)` inside the 60 x 18 button, whose center is `(30, 9)`. Its centered
13-unit line box plus layout rounding did not optically center the glyphs.
The shared Close content template moves only its text upward by one unit and
binds foreground to the Button so disabled text still follows the shared state.
The visible center now measures `(30.00, 9.15)`, within a quarter unit of center.
Other buttons, control dimensions, body gaps and workflow handlers are unchanged.

- [Updated reference](2026-10-28-components-evidence/main-template-normal.png)
- [Actual Close control rendered at 4x density](2026-10-28-components-evidence/close-control-4x.png)

The isolated WPF probe checks visible glyph bounds, all reference states and
66 existing custom/state constructions. The 9 metadata/loader tests and 49
Gallery tests passed; one Gallery test was skipped for unavailable symlink
privilege. The inventory and review were independently split
between Python/custom and compiled/tooling sources, then reconciled against
all 20 Window sources. Production bodies were not migrated or fixed.

This is a source-backed component review and isolated WPF validation, not live
Revit acceptance. Compiled rendering/builds, actual pointer/keyboard behavior,
ownership, modeless events, Narrator, DPI and mixed-monitor checks remain pending.
