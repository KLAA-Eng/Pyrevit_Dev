# KLCode Design System

This guide describes the GUI implementation in the extension as reviewed on
2026-11-17. Use it to select a dialog, assemble a window, choose shared resources
and understand the host boundaries. Resource names and values below follow the
current source, including the WPF baseline adopted in November.

Executable styles and values belong to the [resource dictionaries](../lib/GUI/Resources/).
The [shared-dialog SPEC](../lib/GUI/dialogs/SPEC.md) owns dialog requirements;
the [API guide](../lib/GUI/dialogs/README.md) owns detailed arguments and examples.
Where an older guide or review differs from current markup, inspect the source
before reusing its key names or dimensions. Dated reviews describe their own
baselines, not a second implementation standard.

The [consolidation plan](plans/custom-window-consolidation.md) owns tasks,
authorization and live acceptance. This document does not declare those tasks
complete. [Review records](knowledge/reviews/design-system/README.md) preserve
design decisions and verification evidence.

- [System scope and choosing a window](#system-scope-and-choosing-a-window)
- [Architecture and resource ownership](#architecture-and-resource-ownership)
- [Master design colors](#master-design-colors)
- [GUI colors and resource keys](#gui-colors-and-resource-keys)
- [Window geometry and spacing](#window-geometry-and-spacing)
- [GUI components and style selection](#gui-components-and-style-selection)
- [Icons](#icons)
- [Reusable dialogs](#reusable-dialogs)
- [Host and keyboard contracts](#host-and-keyboard-contracts)
- [Creating a window](#creating-a-window)
- [WPF Studio and Gallery](#wpf-studio-and-gallery)
- [Validation](#validation)

## System scope and choosing a window

The shared system covers Python WPF dialogs and bespoke windows, reference
templates, UI Gallery and compiled WPF source. Most standalone bodies use
`klcWindow` and `klcWindowShell`. Command Switch uses the floating styles instead
of the shell. PreviewFixture is a tooling exception with its own test chrome.
Native Revit/Windows dialogs, pyRevit's own demonstrations and docked panels
retain their host presentation.

| Location or entry point | Purpose and current use |
| --- | --- |
| [GUI.dialogs](../lib/GUI/dialogs/) | Six reusable families: Message, Selection, Text Entry, Action Choice, Command Switch and Rename; the primary layout references |
| [GUI.tool_dialogs](../lib/GUI/tool_dialogs.py) | Tool-facing notices, confirmations, small menus and text prompts, with compatibility return values |
| [GUI.tool_selectors](../lib/GUI/tool_selectors.py) | Tool-facing sheet, revision, document, view and named-item selection with explicit model inputs |
| [GUI.selection_compat](../lib/GUI/selection_compat.py) | Implementation behind `GUI.forms.select_from_dict`; retains its legacy defaults and list result |
| [GUI/_templates](../lib/GUI/_templates/README.md) | Options and Review compositions for more complex windows |
| Tool XAML | Bespoke workflows such as Duplicate Sheets, View Range and Steel PSF; use shared roles with local layout/styles |
| [GUI/_superseded](../lib/GUI/_superseded/) | Legacy CustomAlert and SelectFromDict surfaces retained for reference/Gallery/tests; active compatibility calls now use shared Selection |
| [GUI/_future](../lib/GUI/_future/README.md) | Dormant Create From Rooms and Match/Recall surfaces; Gallery previews do not imply production adoption |
| [src](../src/) | Compiled alert, Family Studio and Startup Importer windows using the same linked resources |

Both Find/Replace commands now use shared Rename. Their duplicate naming XAML
and inline-result controller were retired. Rules are collected before model
execution; unchanged, partial or failed outcomes use Action Choice with Details
and Edit and Retry. Rules survive retry, and successful elements are excluded
from partial retries. Clean success finishes quietly. See the
[adoption record](knowledge/reviews/design-system/2026-11-09-shared-dialog-adoption.md)
for the delivered scope and evidence.

Prefer an existing dialog when its result and interaction match the workflow.
Use Options or Review for a richer composition, or retain a bespoke window
when it owns a distinct workflow or modeless lifetime. Native file/folder
pickers and progress/selection overlays remain separate facilities.

## Architecture and resource ownership

### How the code fits together

| Source | Responsibility |
| --- | --- |
| [KLCodeTokens.xaml](../lib/GUI/Resources/KLCodeTokens.xaml) | Palette, font sizes, typed dimensions, spacing, radii, footer destinations and default Close label |
| [klIcons.xaml](../lib/GUI/Resources/klIcons.xaml) | Generated geometry and the self-contained `klcLogo` template; no palette brushes |
| [KLCodeFoundation.xaml](../lib/GUI/Resources/KLCodeFoundation.xaml) | Merges Tokens and icons; base control templates, inherited window text, scrollbars and icon presenter |
| [KLCodeComponents.xaml](../lib/GUI/Resources/KLCodeComponents.xaml) | Merges Foundation; public role styles, variants, implicit controls, shared shell and repeated layouts |
| [window_chrome.py](../lib/GUI/window_chrome.py) | Loads resources/body, attaches metadata, Close/Escape, header drag and footer navigation |
| [window_metadata.py](../lib/GUI/window_metadata.py) | Caller title and pure tool-version formatting |
| [KLCodeControls.xaml](../src/KLCode.Wpf/Resources/KLCodeControls.xaml) | Compiled compatibility styles over the same resource chain |
| Window body | Named controls, bindings, declared events and workflow arrangement |
| Controller / host adapter | Data, validation, ownership, showing/closing, persistence and model operations |

New bodies consume Components styles rather than Foundation implementation keys.
Existing compiled aliases may base directly on Foundation. The shared shell's
`Tag` is reserved for `WindowMetadata`; its `Content` and workflow `DataContext`
remain caller-owned. A TextBox's `Tag` has a different role: watermark text.

The Python resource cache belongs to the loaded module/engine. Windows using
that module merge the same dictionary instance; do not mutate it for one tool
or assume every pyRevit engine shares it. Put tool data, strings and new local
styles in the window's resources.

The November baseline establishes WPF Studio XAML as the presentation baseline.
Further edits to shared Components, Foundation or Tokens require the separate
owner decision recorded in the [plan](plans/custom-window-consolidation.md).
Reuse existing roles and keep new styles local unless that shared change has
been authorized.

### Key prefixes mark reach

The dictionaries organize keys by consumption, not by alternate themes:

| Prefix | Intended reach |
| --- | --- |
| `klc`, `kla`, `Kla` | Shared-dialog resources or their dependencies |
| `x` | Other windows: tools, templates, Gallery or compiled hosts |
| `xx` | Dormant `_future` consumers |
| `xxx` | No consumer; deletion candidates |

These are maintenance conventions, not a guarantee that every key has already
been renamed to match its current reach. For example, all five sized icon
presenters currently use `klcIcon<size>`, including unused sizes. Generated
geometry keeps `klicon<Role>` names; dormant artwork uses `kliconFuture<Role>`.
Use the actual key in source rather than deriving one from the convention.

## Master design colors

Brand names identify the visual palette. WPF markup selects semantic brush
resources; ribbon PNGs use the brand colors directly.

| Color | Hex | Use |
| --- | --- | --- |
| KLCharcoal | `#1A252B` | Window, chrome, fields and lists; dark ribbon variant |
| KLGreen | `#33714F` | Input borders, logo slash, scrollbar thumbs; green ribbon variant |
| KLGreen-dark | `#286048` | Actions, checked fills, section/list borders and grid lines |
| KLGreen-secondary | `#407058` | Action/dropdown hover and footer links |
| KLWhite | `#E5E4E2` | Body text, ordinary icons and logo letters; light ribbon variant |
| White | `#FFFFFF` | Text on accent-filled controls |
| Muted | `#B5C2BD` | Secondary information |
| Gray | `#808080` | Version, watermarks and disabled text |
| KLOrange | `#FF8000` | Ribbon/prototype artwork; no shared GUI orange brush |

## GUI colors and resource keys

All brushes below are defined in Tokens. Equal colors retain separate roles so
a future role change does not accidentally recolor unrelated components.

| Resource | Value | Role |
| --- | --- | --- |
| `klcBackgroundColor` | `#1A252B` | Window, field and list surface |
| `klcTextColor` | `#E5E4E2` | Main text, inherited icon stroke and footer hover |
| `klcColorGreen` | `#33714F` | Input outline, logo slash, scroll thumb and checked switch track |
| `KlaBorderStrongBrush` | `#286048` | Section/list borders and grid lines |
| `KlaAccentBrush` | `#286048` | Standard action and checked/selected fills |
| `KlaAccentHoverBrush` | `#407058` | Action/dropdown hover |
| `KlaTextOnAccentBrush` | `White` | Text on accent fills |
| `klcTextColorMuted` | `#B5C2BD` | Secondary captions and Details |
| `klcTextColorWaterMark` | `#808080` | Empty-field watermark |
| `klcTextColorDisabled` | `#808080` | Disabled text and icons; unchecked switch track |
| `KlaFocusBrush` | `#E5E4E2` | Field/dropdown focus and focused table-cell border |
| `KlaPressedBrush` | `#204D3A` | Pressed controls and selected table cells |
| `KlaDisabledFillBrush` | `#303C40` | Disabled control fill |
| `KlaComponentSurfaceBrush` | `#22303A` | Secondary controls, grid headers and hover surfaces |
| `KlaComponentBorderBrush` | `#52675D` | Secondary-control/readout borders and splitter |
| `klcInfo` | `#A3C3E8` | Information severity |
| `klcSuccessColor` | `#91C8A6` | Success/Ready severity |
| `klcWarningColor` | `#E8C66A` | Warning severity |
| `klcErrorColor` | `#E89E96` | Error/Blocked severity and validation |
| `klcFooterLinkColor` | `#407058` | Footer links at rest |
| `klcFooterVersionColor` | `#808080` | Caller-version footer |
| `xPreviewSurfaceBrush` | `#10171B` | Family Studio preview surface |

Retired names such as `klcBorderColor`, `KlaMutedBrush` and
`KlaDisabledTextBrush` are not current brush keys. There is no compatibility
palette to restore. Compiled `Kla*Style` keys are style adapters, not another
palette.

Pair severity colors with words. Message colors its heading, symbol and border;
its body remains ordinary text. Review chips keep Ready/Warning/Blocked labels:

```xml
<Border Style="{StaticResource xStatusTagChip}" Tag="{Binding Status}">
    <TextBlock Style="{StaticResource xStatusText}" Text="{Binding Status}"/>
</Border>
```

## Window geometry and spacing

WPF dimensions are device-independent units (1/96 inch), not export pixels.
At 150% Windows scaling, 16 units occupy 24 physical pixels. Window bounds
belong to each body; reusable dimensions belong to typed shared resources.

### Custom window foundation

| Part | Current implementation |
| --- | --- |
| Base window | Segoe UI 12, charcoal, `WindowStyle=None`, transparency enabled, layout rounding and pixel snapping; `NoResize` by default |
| Shell | `klcWindowShell` on the named `window_shell` ContentControl |
| Header/footer | `klcChromeHeight`: 24 each |
| Header | Left logo, centered title, right Close; title has symmetric 110-unit margins and character ellipsis, without a tooltip |
| Logo | `klcLogoWidth` / `klcLogoHeight`: 98 x 14 |
| Close | `klcButtonClose`: 48 x 16, font 12, default `CloseLabel` caption |
| Chrome edge inset | `klcHeadFootMargin`: `4,0,4,0` |
| Footer | Prototype left, caller version centered, Outreach right; version font 14 and symmetric 110-unit margins |
| Body margin | `klcBodyMargin`: `16,16,16,8` |
| Resizing | Set `CanResizeWithGrip` explicitly where needed; establish minimum bounds and overflow behavior |

Message, Text Entry and Action Choice collapse the footer and its reserved row.
Message and Text Entry also hide the center title while retaining `Window.Title`
and Close. Selection, Rename, reference templates and bespoke tool windows
retain the shell footer. Command Switch has no shell, header or footer.

`klcWindowFloating` is transparent and has no taskbar entry. Its
`klcBorderFloating` surface has a 16-unit outer margin, 12-unit padding,
16-unit corners and no border. The current style **does include a subtle black
shadow**: blur 20, opacity 0.12, depth 0. Earlier no-shadow review notes describe
the previous baseline.

### Typography and shape

| Role | Token / current value |
| --- | --- |
| Body | `klcFontSizeBody`: 12 |
| Ordinary buttons, input, Details, footer version | `klcFontSizeButton`, `klcFontSizeTextBox`, `klcFontSizeDetails`, `klcFontSizeShellVersion`: 14 |
| Main action, shell title, heading | `klcFontSizeButtonLarge`, `klcFontSizeShellTitle`, `klcFontSizeHeading`: 16 |
| Message severity heading | `klcFontSizeMessage`: 22, SemiBold |
| Text Entry | `klcFontSizeTextPrompt`: 24, SemiBold, centered |
| Border | `klcBorderHairline`: Thickness 1 |
| Corners | Check 4; input/button 8; switch track 6; command pill 12; floating panel 16; status chip 4 |

Use Title Case for constant captions. Choose wrapping based on the role:
`klcTextBlockHeading` is explicitly non-wrapping; long headings need a deliberate
local variant or layout, not an assumption that every heading wraps.

### Typed spacing resources

The general spacing scale is 4 / 8 / 12 / 16 / 24. Match the resource's WPF type
to the target property; a GridLength is not a Thickness or Double.

| Resource | Type | Value / purpose |
| --- | --- | --- |
| `klcBodySpaceSmall`, `klcBodySpaceNormal`, `klcBodySpaceLarge` | GridLength | 4 / 8 / 12 spacer rows or columns |
| `klcBodyRowNormal`, `klcChromeHeight` | GridLength | 24 compact row / chrome band |
| `klcRenameLabelColumn`, `klcRenameInputColumn` | GridLength | 48 / 200 naming columns |
| `klcStackGapVertSmall`, `klcStackGapVert` | Thickness | `0,4,0,0` / `0,8,0,0` above stacked or collapsible content |
| `klcStackGapBelow`, `klcStackGapHoriz` | Thickness | `0,0,0,8` / `8,0,0,0` |
| `KlaActionTopGap` | Thickness | `0,8,0,0` above a stacked action |
| `KlaIconTextGap` | Thickness | `0,0,4,0` after a small icon |
| `klcSectionPadding` | Thickness | 12 inside a field group |
| `KlaCompactInset` | Thickness | `8,4` component/cell inset |
| `klcPadTextBoxInput` | Thickness | `8,0,0,4` input text padding; native TextBoxView applies it |
| `KlaCommandLinkPadding`, `KlaCommandArrowInset` | Thickness | 8 / `0,4,8,0` inside command links |
| `KlaCommandPillGap`, `klcCommandPillPanelInset` | Thickness | `0,0,8,8` item gap / `0,0,-8,-8` trailing-gap compensation |
| `KlaOpticalTextInset`, `klcSwitchCaptionInset` | Thickness | `0,0,0,2` / `0,0,0,3` optical text adjustments |
| `xHeaderCellInset` | Thickness | `8,6` grid header inset |

Use `Auto` for rows holding actions or collapsible validation. A 36-high main
action must not sit in a fixed 24- or 32-high row. Keep long content bounded
and preserve access to actions at minimum size. Layout recipes and special
optical insets do not justify inventing arbitrary per-window spacing.

## GUI components and style selection

### Actions and choices

| Components style | Control | Current dimensions / role |
| --- | --- | --- |
| `klcButton` | Button | 104 x 28, font 14; standard action |
| `klcButtonDouble` | Button | 216 x 36, font 16; primary action |
| `klcButtonSec` | Button | 104 x 28; component fill and hairline component border |
| `klcButtonClose` | Button | Compact shell Close |
| `KlaCommandLink` | Button | Full width, minimum height 40; arrow, wrapping label and optional description |
| `klcButtonCommand` | Button | Auto width, height 28, font 12; immediate Command Switch pill |
| `klcToggleCommand` | ToggleButton | Height 28, font 12; track/thumb plus caption, no hover fill change |
| `xLinkButton`, `xGhostButton` | Button | 104 x 28; transparent text action / outlined variant |
| `xRadioButton`, `xSegmentButton` | RadioButton | Exclusive circular choices / 28-high segments |
| `xxToggle` | ToggleButton | 104 x 28 option for dormant windows |
| `xxIconButton`, `xxIconTextButton` | Button | 28 x 28 / 128 x 28 dormant icon actions |

Button variants reuse the Foundation button template. Its local resource hooks
are `klcButtonHoverBrush`, `klcButtonDisabledBrush` and
`klcButtonBorderShape`; variants may also set border properties. Do not copy
the control template merely to change a surface or radius.

Text captions go in `Content`, not a nested TextBlock. The template renders
string content as wrapping, centered AccessText. A tool-supplied caption goes
through `GUI.window_chrome.access_text` so literal underscores survive. A
window-owned caption can deliberately declare an access key. Shared default
captions belong in string resources; an explicit Content value overrides the
style default.

Fixed action widths are roles, not a promise that every translated caption
fits. Inspect long/localized captions; small menus use auto-width command pills
or wrapping command links. Preserve workflow action placement when migrating.
The primary visual style does not imply `IsDefault=True`.

### Fields, text and collections

| Components style | Control | Current role |
| --- | --- | --- |
| `klcTextBox` | TextBox | Standard 24-high input, font 14, default `[ENTER TEXT]` watermark |
| `klcTextBoxFilter` | TextBox | Same input with `[TYPE TO FILTER]` watermark |
| `klcTextBoxPrompt` | TextBox | 36-high Text Entry field, font 24 SemiBold, centered |
| `klcTextBoxReadout` | TextBox | Auto-height read-only wrapping body; transparent, selectable and scrollable |
| `klcTextBoxReadoutSmall` | TextBox | Read-only wrapping multiline output, font 12, minimum height 64, section padding and muted border |
| `klcTextBlockHeading`, `klcTextBlockHeadMessage` | TextBlock | 16 SemiBold no-wrap heading / 22 SemiBold severity heading |
| `klcTextBlockFeedback` | TextBlock | Error-colored validation, polite live announcement, collapsed when Text is empty |
| `klcTextBlockMuted`, `klcTextBlockMutedDisabled` | TextBlock | Secondary information / disabled-aware variant |
| `klcLabelCentered`, `klcLabelHeading` | Label | Centered field caption / 16 SemiBold input heading |
| `KlaComboBox`, `klcComboBoxFilter` | ComboBox | 32-high base alias / 24-high filter, popup maximum 240 |
| `klcCheckBox`, `KlaCheck` | CheckBox | Shared check style / compatibility alias |
| `klcCheckBoxSelection` | CheckBox | Selection row label and optional description |
| `KlaList`, `KlaDialogListItem` | ListBox / ListBoxItem | Checked-list host / row disabled when `CanSelect=False` |
| `klcBorder`, `xBorderMessage` | Border | Shared field-group surface / component-border variant |
| `klcExpanderDetails` | Expander | Muted 14-unit Details heading with right/down chevron |
| `klcLink`, `klcLinkFooter` | Hyperlink | Green help link / bold footer link |
| `xReadOnlyField`, `xCompactReadOnlyField` | TextBox | Muted read-only field; both currently use 24-high input geometry |
| `xDataGrid`, `xDataGridStatusCell`, `xDataGridText` | Table parts | Read-only review grid, centered status cell, foreground-aware text |
| `xStatusChip`, `xStatusWarning`, `xStatusError` | Border | Neutral/warning/error chips; `xStatusText` supplies caption style |
| `xTableStatusChip`, `xStatusTagChip` | Border | Centered table chip / color selected by Ready, Warning or Blocked Tag |
| `xSplitter` | GridSplitter | Review divider, minimum size and keyboard increment 4 |

Bare TextBox, ComboBox and CheckBox controls take the shared implicit styles.
Other controls require explicit styles. Prefer explicit keys in new bodies so
their role is visible. The grid is read-only; editable tables require a separate
interaction design. Native ListBoxItem hover/selection remains a blue WPF
exception; highlighting and checking are distinct states.

### Choosing TextBlock, Label or TextBox

Use TextBlock for headings and display-only information. Use Label with
`Target` when a caption names one focusable control. Use TextBox for input and
a read-only TextBox for output the user may need to copy.

A targeted Label supplies the input's accessible name and optional Alt access
key. Avoid overriding that name on the input unless repeated captions need
context, such as Rename's Sheet Name find versus Sheet Number find. Group
headings name several controls and use TextBlock. Icon-only actions and inputs
without a Label need an explicit accessible name.

```xml
<Label Content="Prefix:" Target="{Binding ElementName=input_prefix}"
       Style="{StaticResource klcLabelCentered}"/>
<TextBox x:Name="input_prefix" Style="{StaticResource klcTextBox}" Tag=""/>
```

TextBox `Tag` is watermark content. The Foundation template shows it whenever
Text is empty, including while focused; it is never input data. A local Tag
overrides the role's default. Do not add a separate watermark TextBlock or an
extra content-host margin: TextBoxView already applies Padding.

Keep list rows as list items/checks. Putting focusable read-only TextBoxes in
every row changes click and keyboard behavior. If row copying is needed,
provide a deliberate Copy interaction; the read-only DataGrid already supports
native Ctrl+C for selected rows.

### Shared body compositions

`klcRenameRows` places direct named items in 48/200 columns, with 24-high rows
at indices 0/2/4/6 and 8-unit gaps. `xFilteredCheckList` provides filter,
prompt, expanding list, secondary content and main action at rows 0/2/4/6/8.
Its action row is Auto. These ItemsControl layouts preserve direct controls in
the window's namescope; they do not own workflow validation or selection logic.

The [Options and Review templates](../lib/GUI/_templates/README.md) demonstrate
rich layouts and fictional controllers. Review separates selected detail from
checked rows, preserves hidden checks, applies Check All only to visible
eligible rows and prevents blocked rows from being checked. Form and separate
Message/Selection templates are retired. Use the actual dialog bodies instead.

## Icons

### In-window GUI icons

The [GUI icon catalog](../lib/_icons/gui/README.md),
[source manifest](../lib/_icons/gui/source.json), SVGs and
[Lucide license](../lib/_icons/gui/LICENSE.lucide.txt) preserve provenance.
The generated dictionary currently contains these 19 semantic geometries:

| Use | Geometry key |
| --- | --- |
| Search / grouping | `kliconSearch`, `kliconGroup` (Layers-2) |
| Information / warning | `kliconInfoAlert`, `kliconWarnAlert` |
| Error / success | `kliconErrorAlert` (Octagon Alert), `kliconSuccessAlert` (Check Check) |
| Details collapsed / expanded | `kliconChevRight`, `kliconChevDown` |
| Family Studio list / grid / favorite | `kliconList`, `kliconGrid`, `kliconFav` |
| Dormant filter / regex / clear | `kliconFutureFilterList`, `kliconFutureRegex`, `kliconFutureClearSearch` |
| Dormant element / view-filter actions | `kliconFutureTags`, `kliconFutureRead`, `kliconFutureFilterFunnel` |
| Dormant pick / rectangle selection | `kliconFuturePointer`, `kliconFutureRectSelect` |

Use a sized Components presenter: `klcIcon12`, `klcIcon16`, `klcIcon24`,
`klcIcon32` or `klcIcon48`. Shared search/group/Details use 16; severity uses 32.
`xIcon` remains an unsized compatibility presenter. New markup chooses the
size style instead of setting Width/Height on each icon.

```xml
<ContentControl Style="{StaticResource klcIcon16}"
                Content="{StaticResource kliconSearch}"/>
```

The presenter inherits foreground and uses `klcTextColorDisabled` when disabled.
Avoid local foreground on stateful action icons unless intentionally overriding
that behavior. Decorative icons neither take focus nor intercept clicks. Name
their containing action; let an icon/text action's caption follow its button's
foreground.

Artwork uses a 24-unit canvas (`KlaIconCanvas`) with a 2-unit grid stroke
(`klcIconStroke`). Stroke scales with presenter size: about 1.33 units at 16,
2.67 at 32. The owner-adjusted SVG geometry fills this canvas with a small
stroke margin; the manifest's historical 1.5 source-stroke note is not the
current WPF pen width. The generator requires a `0 0 24 24` viewBox and simple
supported SVG elements. Bake transforms and remove editor metadata before
regeneration.

### Logo and generated resources

[generate_gui_icons.py](../scripts/generate_gui_icons.py) emits geometry plus
the `klcLogo` DataTemplate from [klcLogo.svg](../lib/_logos/klcLogo.svg).
The logo retains its 1024 x 146 source canvas/transform and uses dynamic green
and text brushes. The shell sizes it through the 98 x 14 logo tokens. No runtime
SVG renderer or fixed-color icon ImageSource is required.

Edit source SVGs/mappings, run the generator, and check its output:

```powershell
python -B scripts/generate_gui_icons.py
python -B scripts/generate_gui_icons.py --check
```

Do not hand-edit or run a formatter over generated `klIcons.xaml`; generation
checks require byte equality. Format handwritten resources with an explicit
file list that excludes it. Retain attribution when replacing artwork.

### Ribbon assets

Ribbon artwork lives under [lib/_icons/ribbon](../lib/_icons/ribbon/), with
transparent exports in `png/` and editable sources in `svg/`.
Use a single foreground color unless more detail is necessary. Reusable names
follow `<icon-name>_<size>px_<color>.png`; suffixes are `orange` (`#FF8000`),
`green` (`#33714F`), `light` (`#E5E4E2`) and `dark` (`#1A252B`). Export sizes
are 16, 24 and 32 pixels for controls, with additional 96-pixel PNG exports.
Existing editable SVG sources use 128-pixel names. New DevSandbox prototypes start with
[drill_32px_orange.png](../lib/_icons/ribbon/png/drill_32px_orange.png).
Preserve established bundle icon metadata and source assets.

## Reusable dialogs

### Direct API and results

`GUI.dialogs` imports without WPF or Revit. Factories lazily construct unshown
bare WPF windows; modal helpers call ShowDialog and return `DialogResult`.
Use the host UI thread. Supply caller title/version and a shown WPF owner or
native handle. Direct factories do not infer Revit ownership or an active model.

| Family | Factory | Modal helper / accepted result |
| --- | --- | --- |
| Message | `create_message` | `show_message`: action `ok`, value None |
| Selection | `create_selection`, `create_list_single`, `create_list_multiple` | `select_items`, `select_one`, `select_many`: action `accept`, original payload or list |
| Sheet/revision/document selection | `create_sheet_selector`, `create_revision_selector`, `create_document_selector` | `select_sheets`, `select_revisions`, `select_open_documents`: collect read-only rows, then select |
| Text Entry | `create_text_prompt` | `ask_text`: action `accept`, raw text |
| Action Choice | `create_choice` | `choose_action`: action/key/checkbox snapshot |
| Command Switch | `create_command_switch` | `command_switch`: action `accept`, command key and switch states |
| Rename | `create_rename` | `rename`: action `accept`, rename rules or case request |

Inspect `result.action` and `result.value` explicitly. Accepted blank text,
empty optional selection and a selected None payload can be valid outcomes.
Ordinary unaccepted closure returns `cancel` with None. Action Choice preserves
distinct `accept`, `cancel` and `close` outcomes; `is_cancelled` covers its last
two outcomes. No direct API exits the script, runs commands, persists settings
or changes a model.

```python
from GUI.dialogs import SelectionItem, select_many

rows = [SelectionItem('first', 'Typical Detail', first_payload),
        SelectionItem('second', 'Typical Detail', second_payload)]
result = select_many(__title__, rows, version=__version__, owner=owner_handle)
if result.action == 'accept':
    selected_payloads = result.value
```

### Family behavior

**Message** is an OK-only severity notice with optional collapsed Details.
The body and details are selectable read-only text. The initial width is 432,
minimum height 240 and maximum height 640. It fits initial content; subsequent
width changes preserve manual height. Details growth is measured after the
template transition and reversed on collapse, protecting content until capped.

**Selection** uses stable unique keys, allows duplicate labels, clones check
state and retains original payload identity and order. Search matches labels
and descriptions; group and search filters intersect. Hidden checks survive;
All/None affects visible eligible rows only. Single mode enforces exclusive
checking and hides batch actions. Highlighting is not checking. Generic rows
start unchecked unless explicitly supplied otherwise. Select is explicit;
list/filter Enter and double-click do not accept. Search and optional Group
are 24 high, preceded by 16-unit icons. Width starts at 432 and is bounded
432–512; height is bounded 420–620 in current XAML. Do not assume the retired
template's fixed 576 initial height.

Read-only [collectors](../lib/GUI/dialogs/collectors.py) run in valid Revit API
context before the dialog opens. Direct sheet collection excludes placeholders
by default and groups saved sheet sets over shared row identities. Revisions
include issued and unissued rows unless filtered. Document collection excludes
linked and active documents by default and requires an explicit active-document
argument unless active inclusion is requested. Prepared-data factories do no
model query. Callers own document lifetime and later operations.

**Text Entry** has a 432-wide content-fitting layout with a 36-high, 24-unit
SemiBold input. `[ENTER TEXT]` is a watermark, never returned input. Its prompt
is the input's accessible name; neither prompt nor center title is visible.
OK validates required/optional caller rules and returns raw text. Editing clears
feedback; validators return an error string or None. Programming exceptions
propagate. Current rows use 4-unit spacers around validation/action content.

**Action Choice** presents up to four immediate command links, optional body,
severity, Details, checkbox and help, plus selected standard buttons. Width
starts at 420 with minimum 248; height fits up to 640. Empty optional sections
reserve no content. Standard buttons are OK, Yes, No, Retry, Cancel and Close.
Default focus follows the configured action with enabled-action fallback;
unknown defaults fail at construction. Enter activates actions. The current
controller leaves Space to WPF, so it activates focused buttons and toggles
the checkbox or Details toggle. Values are snapshots with `kind`, `key` and `checked`.
No is an accepted button result, not cancellation. An explicit Cancel always
permits dismissal. With cancellation disabled, chrome Close is hidden and
Escape/Alt+F4 are blocked; code/owner/system closure still returns `close`.

**Command Switch** is a floating panel starting at width 480, with maximum
width 752 in XAML. Commands are immediate wrapping pills; optional toggle
pills remain visible during filtering. It has no corner Close, Continue action,
navigation footer or status line. Typing enters search; Escape clears search
before cancelling. Outside click/deactivation cancels, including over the
disabled modal owner. A drag past the system threshold moves the panel without
activating a control. Blank clicks inside stay open. Context-menu capture is
handled separately. Its controller fits content height; the current body has
no scrolling wrapper or finite MaxHeight declaration, so do not promise the
older 500-unit scroll cap. Result value is `{'command': key, 'switches': {...}}`.

**Rename** accepts one or two `RenameField` groups. `view_fields()` supplies
View Name; `sheet_fields()` supplies Sheet Number and Sheet Name. The layout
fits visible groups using `klcRenameRows`. At most one field supports the
shared Uppercase/Lowercase pair. Rename returns an operation plus entered rules;
case actions return `upper` or `lower` and a field key. An entirely blank rule
request remains open with inline feedback. The dialog does no preview or model
mutation. Find/Replace controllers own transactions and safe retry afterward.

### Tool-facing compatibility boundaries

Use the direct API for a new workflow that can inspect explicit results. Existing
tools use these adapters to preserve their established calling contracts:

| Adapter | Contract that differs from the direct API |
| --- | --- |
| `GUI.tool_dialogs.alert` | OK-only notices use Message; multi-button prompts use Action Choice. Returns a Boolean; OK/Yes/Retry are positive. `exitscript` preserves the legacy exit policy |
| `GUI.tool_dialogs.choose` | Returns original action text or None. An explicit Cancel menu row becomes the Cancel button |
| `GUI.tool_dialogs.ask_text` | Returns accepted text, including `''`, or None on cancel |
| `GUI.tool_selectors` | Requires explicit documents/application where relevant; returns original objects or lists, with None on cancel. Defaults ownership lazily to Revit |
| `GUI.forms.select_from_dict` | Delegates through `selection_compat`; returns a list even in single mode, and `[]` on cancel/empty acceptance |

`selection_compat` sorts truthy keys, deduplicates list inputs, preserves caller
captions and checks the first row when `initial_checked_names=None`. An explicit
empty initial collection checks none. This first-row default does not apply to
the direct Selection API. Its current signature has no owner argument and does
not supply one to the factory; do not infer Revit ownership from other adapters.

Tool sheet selection includes placeholders by its legacy default and keeps
sheet-number ordering. Revision filtering remains caller-owned. View selection
can offer the existing current-selection confirmation before opening the full
list. These defaults must not be copied indiscriminately to direct collectors.
No upstream pyRevit module is patched.

## Host and keyboard contracts

### Python and pyRevit

`load_window(window, xaml_path, title, version=None, navigate=None,
close_handler=None)` merges Components before loading the body. It calls the
window's `load_xaml` if present, otherwise `wpf.LoadComponent`. It attaches
chrome without showing the window or replacing DataContext.

Pass the command's `__title__` and pure `__version__` (for example `v1.3`).
Missing/invalid version metadata leaves the version field empty; no extension
version is inferred. `WindowMetadata` and its shared
[test vectors](../lib/GUI/window_metadata_vectors.json) own formatting.

Header Close calls the supplied handler or `window.Close()`. Escape follows
that policy unless a dialog replaces the route. Header drag calls DragMove.
Footer navigation uses the OS unless `navigate(uri)` is supplied; Gallery
simulates it. `fit_window_height` measures within the caller's MinHeight and
MaxHeight. `window._kla_chrome.hide_footer()` collapses only that instance's
footer and row.

Retained `pyrevit.forms.WPFWindow` subclasses have an additional boundary:
`load_window` invokes the host loader without overriding its Escape/ownership
defaults. The pyRevit Escape handler can close the window before a custom
Close policy runs. Shared dialogs use bare WPF Window classes and do not inherit
that competing handler. Check installed pyRevit behavior and the actual host
when working on retained custom windows; local handler simulation is not host
acceptance.

### Compiled WPF windows

[ThemeBootstrapper.Apply](../src/KLCode.Wpf/ThemeBootstrapper.cs) loads shared
controls then common locale strings before InitializeComponent. ApplyToolStrings
adds the tool dictionary afterward. [WindowChrome.Attach](../src/KLCode.Wpf/WindowChrome.cs)
binds the shell to caller identity and optional close policy. Compiled projects
link canonical shared XAML as WPF Pages; controllers retain their own services,
DataContext and modal/modeless lifetime.

The common locale catalog currently falls back to English. The shell's Close
caption is a DynamicResource; Prototype and Outreach captions are currently
literal Runs in the shared shell. Do not promise locale-dictionary overrides
for those two captions or translations for every tool based on dormant Recall
locale files.

Shared source adoption does not replace deployed plugin DLLs. Rebuild and verify
the matching target/host to consume linked-resource changes. Desktop smoke tests
with fake ports establish source construction, not deployed Revit behavior.

### Keyboard and accessibility

Shell content is declared before chrome for body-first traversal, then Close
and links. Text, Selection, Rename and Command Switch use neutral body
focus where specified by their controllers; Action Choice focuses its default.
Inputs retain focus borders. Buttons, checks, radios, toggles and Details
toggles suppress focus adorners but remain keyboard operable.

| Family | Enter | Space | Escape / Close |
| --- | --- | --- | --- |
| Message | OK | Focused button | Cancel |
| Selection | No accept from list/filter; focused buttons, ComboBox and links retain Enter | Focused checkbox/button | Cancel |
| Text Entry | Validate and accept | Focused button; otherwise ordinary input | Cancel |
| Action Choice | Focused action/Details/help or default action | Normal WPF activation of focused buttons, checkbox and Details | Escape cancels if permitted; Close returns distinct `close` |
| Command Switch | Focused command, or sole enabled match while search is focused; toggle Enter never chooses a command | Focused toggle/command | Clear search, then cancel; outside dismissal cancels |
| Rename | Submit from fields; focused case/action button keeps its action | Focused button or ordinary field input | Cancel |

Set explicit default/cancel semantics rather than deriving them from styling.
Disable the body, not the whole shell, when Close must remain available. Check
disabled text and icons, long captions, minimum sizes, keyboard reachability,
work-area placement and DPI in the host.

Retain these owner-selected accessibility deviations when maintaining the
current baseline; they are not a claim of full accessibility compliance:

- Buttons/checks/radios/toggles/command links/Details have no visible keyboard
  focus indicator (Focus Visible). Field outlines remain.
- Footer links are about 2.74:1 and version/watermark gray about 3.96:1 against
  charcoal. Small text can fall below the usual 4.5:1 text-contrast threshold.
- Text Entry's visible title and prompt are absent; its accessible name carries
  the prompt. Message also omits the center title.
- Command Switch tracks use gray/green and thumb position. Checked green against
  the pill surface is about 2.33:1, below a 3:1 control-state contrast threshold.
  Evaluate the actual current gray track rather than the older muted-track value.
- Disabled controls use gray plus disabled automation state; inactive components
  are exempt from the ordinary contrast requirement.

Historical decisions are in the plan and shared SPEC. Current source changes,
including the floating shadow, gray switch track and ordinary Action Choice
Space activation, supersede older descriptions. The shared SPEC/API guide still
describe Enter-only Action Choice activation; that text has not caught up with
`choice_window.py` and Studio's routed-Space checks. This guide records the
current implementation without changing that separate contract. Physical input,
Narrator, host ownership and DPI remain separate acceptance evidence.

## Creating a window

First read the command's adjacent SPEC and choose a matching shared dialog.
When a bespoke body is needed, load Components before XAML and use the shared
shell. Keep named controls/events in the body and deterministic logic in `lib/`.

```xml
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Width="432" SizeToContent="Height"
        Style="{StaticResource klcWindow}">
    <ContentControl x:Name="window_shell" Style="{StaticResource klcWindowShell}">
        <StackPanel>
            <Label Content="Name:" Target="{Binding ElementName=name_input}"
                   Style="{StaticResource klcLabelCentered}"/>
            <TextBox x:Name="name_input" Style="{StaticResource klcTextBox}"/>
            <Button Content="Apply" Click="apply_example" IsDefault="True"
                    Margin="{StaticResource KlaActionTopGap}"
                    Style="{StaticResource klcButtonDouble}"/>
        </StackPanel>
    </ContentControl>
</Window>
```

```python
from pyrevit import forms  # Initializes the installed WPF support.
from System.Windows import Window
from System.Windows.Interop import WindowInteropHelper
from GUI.window_chrome import load_window

class ExampleWindow(Window):
    def __init__(self, body_path, title, version, owner_handle):
        self.result = None
        load_window(self, body_path, title, version)
        WindowInteropHelper(self).Owner = owner_handle

    def apply_example(self, sender, args):
        self.result = self.name_input.Text
        self.Close()

# body_path and a native System.IntPtr owner_handle come from the caller.
window = ExampleWindow(body_path, __title__, __version__, owner_handle)
window.ShowDialog()
# The caller validates/uses window.result and owns subsequent model operations.
```

For a modeless workflow, preserve its ExternalEvent, subscription and cleanup
contracts; do not run model operations directly from arbitrary WPF events. For
compiled bodies, apply resources before InitializeComponent and attach chrome
afterward using the existing compiled adapter pattern.

Supply identity, accessible labels, validation and explicit dismissal behavior.
Add fictional Gallery coverage through an allowlisted adapter where appropriate;
source discovery alone does not permit executing a production controller.
Materially changed tool behavior also requires its adjacent SPEC update.

## WPF Studio and Gallery

The sibling `.dev.KLCodeWPF` workspace is the Windows XAML editing and preview
environment. Its README owns the complete workflow. Open `KLCodeWPF.sln` in
Visual Studio, build x64, then use the designer or F5 preview picker. Views are
editable working copies; generated handlers and preview attributes belong only
to the workspace. Designer samples and interactive previews use fictional data,
not an Autodesk model.

1. Save edits in Studio. Run Check before Apply.
2. Apply validates the batch, detects concurrent source edits, protects existing
   names/events, strips preview attributes and backs up originals.
3. After extension-side changes, Refresh imports source. It refuses to overwrite
   unapplied preview edits. Reopen the solution when inventory changes.
4. Build and verify after synchronization. Never copy preview attributes or
   generated C# scaffolding into production XAML.

The six shared families have named JSONC setups under DesignerSamples. The
designer's active setup and F5's chosen setup are separate selections. Gallery
retains its own fixtures. Message, Selection and Rename previews instantiate
actual shared factories/controllers; their actions remain simulations.

UI Gallery groups shared families with Variant beside State. Selection has
Sheets, Revisions, Open Documents, List Single and List Multiple. Message has
With/Without Details; Rename has Views, Sheets and Generic; Command Switch has
Commands only and Commands with toggles. Action Choice covers command, Details,
checkbox, full-content and standard-button combinations. Options and Review
remain template entries. Family variants expose empty, error/severity, disabled
and long-content fixtures as applicable. Compiled Gallery previews remain a
separate deferred capability; source smoke/designer surfaces are different proof.

## Validation

For a documentation edit, verify links, key names, values and examples against
current source and inspect `git diff`. Runtime changes require the relevant
behavior/layout evidence. Do not rerun every historical probe merely because
it exists: several still encode retired resource names or dimensions.

| Check | Establishes | Does not establish |
| --- | --- | --- |
| Focused CPython tests | Deterministic models, metadata, compatibility and fake-host boundaries | Rendered WPF or real model effects |
| Icon generator `--check` | Generated output matches source and generator | Visual/interactive suitability |
| `check_ui_scale.py` | Numeric-layout policy and reported consumer spacing | Approved token values, complete UI consistency or accessibility |
| Studio Build / Verify | Current presentation baseline, designer/runtime construction and fictional Gallery states | Revit ownership, physical input or model operations |
| Studio adapter/modal probes | Real WPF results and interactions using fictional objects | Real transaction/host recovery |
| C# source tests and desktop smoke | Packaging/source contracts and construction with fake ports | Deployed DLL and matching-Revit acceptance |
| Live Revit review | Actual ownership, focus, drag, DPI, model workflows and lifecycle | Other untested hosts/models |

Some layout probes derive expectations from the same tokens as the controls.
They prove consistent consumption, not that an edited token still matches the
intended design. Inspect renders and independent dimensions after a value change.

Useful repository commands (choose the checks relevant to the change):

```powershell
python -B scripts/generate_gui_icons.py --check
python -B scripts/check_ui_scale.py
python -B -m unittest discover -s tests -p "gui_selection_compat_test.py"
python -B -m unittest discover -s tests -p "gui_tool_selectors_test.py"
python -B -m unittest discover -s tests -p "find_replace*test.py"
dotnet test src/KLCode.Wpf/Tests/KLCode.Wpf.Source.Tests --no-restore
```

The scale checker currently flags shared literals such as the shell's 110-unit
margins; its strict policy should not be described as a clean baseline without
running it. `_future` is excluded from consumer reporting. Sized icon presenter
dimensions are an explicit exception.

In the sibling Studio workspace, use `Workspace.ps1 Build` / `Verify`,
`Test-SelectionAdapter.ps1 -Wpf`, `Test-ToolDialogs.ps1 -Wpf` and
`Test-FindReplaceDialog.ps1` for the current adoption baseline.
`Test-DialogSamples.ps1` checks designer/interactive setups and
`Test-Sync.ps1` checks transfer protections. Use the workspace README for exact
invocation and evidence destinations. Shared-resource compiled regressions also
use the desktop smoke project targeting net48 and net8.0-windows with installed
dependencies.

The repository's `validate_ui_gallery_wpf.ps1` and specialized WPF scripts are
additional probes. Inspect their assertions against the current baseline before
using them as evidence. Optional shown-window focus probes establish bounded
fictional-window behavior, not physical Revit keyboard/pointer routing.

The [November 6 baseline record](knowledge/reviews/design-system/2026-11-06-wpf-baseline-adoption.md)
and [November 9 adoption record](knowledge/reviews/design-system/2026-11-09-shared-dialog-adoption.md)
document the latest delivered local checks. GUI-08 and GUI-54 in the owning plan
retain live acceptance: representative model transactions/retries, revision
filters, View Range ExternalEvent/close cleanup, Duplicate Sheets operations,
actual owner/focus and DPI. Record host/version and observed outcomes there;
local test success does not close those tasks.
