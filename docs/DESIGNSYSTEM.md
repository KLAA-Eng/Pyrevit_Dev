# KLCode Design System

This is the working reference for KLCode colors, artwork, WPF components and
window construction. Use it to choose a resource, understand its appearance and
assemble a window. The linked XAML files own executable values and templates;
this guide explains their intended use and the shared design rules.

The nine Python tool windows, four standard opt-in dialog bodies, five reference templates, Gallery and five
compiled window classes use `KlaWindowShell`. PreviewFixture retains its
standalone test chrome. Native/pyRevit dialogs and Recall's docked panel have
separate host presentation; the standalone Recall body uses the shared system.
The fifth opt-in body is a floating Command Switch using shared colors/styles
with its own compact layout. Text omits the standard footer by design.

- [Master design colors](#master-design-colors)
- [GUI colors and resource keys](#gui-colors-and-resource-keys)
- [Icons: GUI and ribbon](#icons)
- [GUI components and style selection](#gui-components-and-style-selection)
- [Window geometry and spacing](#window-geometry-and-spacing)
- [Architecture and resource ownership](#architecture-and-resource-ownership)
- [Host and keyboard contracts](#host-and-keyboard-contracts)
- [Reusable dialogs](#reusable-dialogs)
- [Creating a window](#creating-a-window)
- [Validation](#validation)

The [consolidation plan](plans/custom-window-consolidation.md) owns tasks and
acceptance status. The [template guide](../lib/GUI/_templates/README.md) owns
the five reference implementations. Dated checks and renders live in
[design-system reviews](knowledge/reviews/design-system/README.md), including
the [Windows verification and Revit checklist](knowledge/reviews/design-system/2026-10-29-gui-architecture-windows.md).
The [archived long form](knowledge/reviews/design-system/2026-10-29-designsystem-archive.md)
preserves earlier implementations; use this guide for current instructions.

## Master design colors

Brand names describe the visual palette. In a WPF window, select a resource by
its role rather than copying a hex value. Ribbon PNG exports use the brand
colors directly. KLOrange is a ribbon/prototype convention; the shared GUI
palette does not define an orange brush.

| Color name | Hex | Current use |
| --- | --- | --- |
| KLCharcoal | `#1A252B` | Window, chrome, input and list backgrounds; dark ribbon artwork variant |
| KLGreen | `#33714F` | Input borders, wordmark slash, scrollbar thumbs; green ribbon artwork |
| KLGreen-dark | `#286048` | Standard action fills, checked fills, section/list/grid borders |
| KLGreen-secondary | `#407058` | Standard action/dropdown hover fills and footer links |
| KLWhite | `#E5E4E2` | Body text, ordinary icons, wordmark letters; light ribbon artwork variant |
| White | `#FFFFFF` | Text on accent-filled buttons and selected segments |
| Muted text | `#B5C2BD` | Captions and secondary information |
| Gray | `#808080` | Footer version text |
| KLOrange | `#FF8000` | Orange ribbon artwork and default DevSandbox prototype icon |

The footer restores its original green links and gray version text through
dedicated roles. Other muted GUI text uses `#B5C2BD`; the compatibility key
`text_gray` also resolves to that color. Use the footer roles for footer text.

## GUI colors and resource keys

### Palette brushes

[KLCode_palette.xaml](../lib/GUI/Resources/KLCode_palette.xaml) owns these
brushes. The same dictionary is used by Python and compiled WPF.

| Resource key | Hex | Intended use |
| --- | --- | --- |
| `KlaWindowBrush` | `#1A252B` | Window/chrome surface, fields and lists |
| `KlaTextBrush` | `#E5E4E2` | Body text, labels, ordinary icon stroke; footer hover |
| `KlaTextMutedBrush` | `#B5C2BD` | Secondary captions |
| `KlaFooterLinkBrush` | `#407058` | Prototype and Outreach footer links at rest |
| `KlaFooterVersionBrush` | `#808080` | Centered caller-version footer text |
| `KlaTextOnAccentBrush` | `#FFFFFF` | Text on accent-filled actions and selected segments |
| `KlaAccentBrush` | `#286048` | Standard buttons, checked boxes and selected segments |
| `KlaAccentHoverBrush` | `#407058` | Standard action/dropdown hover background |
| `KlaBorderBrush` | `#33714F` | Input/dropdown outlines, wordmark slash, scrollbar thumbs |
| `KlaBorderStrongBrush` | `#286048` | Section/list outlines, grid lines and segment groups |

### State and component brushes

[KLCodeFoundationTokens.xaml](../lib/GUI/Resources/KLCodeFoundationTokens.xaml)
owns these semantic brushes. Choose the role appropriate to the state or
component, even when two roles currently have the same color.

| Resource key | Hex | Intended use |
| --- | --- | --- |
| `KlaFocusBrush` | `#E5E4E2` | Keyboard focus underline or field border |
| `KlaPressedBrush` | `#204D3A` | Pressed buttons/options and selected table cells |
| `KlaDisabledFillBrush` | `#303C40` | Disabled action/dropdown fill |
| `KlaDisabledTextBrush` | `#A6B0AD` | Disabled control text and foreground-aware icons |
| `KlaComponentSurfaceBrush` | `#22303A` | Secondary actions, grid headers and hover surfaces |
| `KlaComponentBorderBrush` | `#52675D` | Banner/readout borders and splitter |
| `KlaMutedBrush` | `#B5C2BD` | Component information text and read-only field text |
| `KlaInfoBrush` | `#A3C3E8` | Information borders/chips |
| `KlaReadyBrush` | `#91C8A6` | Ready/success borders/chips |
| `KlaWarningBrush` | `#E8C66A` | Warning borders/chips |
| `KlaErrorBrush` | `#E89E96` | Error/blocked borders/chips |
| `KlaPreviewSurfaceBrush` | `#10171B` | Compiled Family Studio preview surface |

Pair status colors with words such as Ready, Warning or Blocked. Message
severity uses heading wording and a border; body/heading text remains readable.
Disabled controls use explicit brushes rather than stacked opacity reductions.

```xml
<Border Style="{StaticResource KlaStatusWarning}">
    <TextBlock Text="Warning" Style="{StaticResource KlaStatusText}"/>
</Border>
```

### Compatibility keys

Existing windows can retain these names. New markup should prefer the role
keys above. Brush aliases bind their color to the canonical brush; they are
separate brush instances rather than a promise of object identity.

| Existing key | Canonical role |
| --- | --- |
| `header_background` | `KlaWindowBrush` |
| `text_white` | `KlaTextBrush` |
| `text_gray` | `KlaTextMutedBrush` |
| `text_green`, `border_green` | `KlaBorderBrush` |
| `button_fg_normal` | `KlaTextOnAccentBrush` |
| `button_bg_normal` | `KlaAccentBrush` |
| `button_bg_hover` | `KlaAccentHoverBrush` |
| `border_green_dark` | `KlaBorderStrongBrush` |
| `KlaPanelBrush` | `KlaComponentSurfaceBrush` |
| `KlaMutedTextBrush`, `KlaSubtleTextBrush` | `KlaMutedBrush` |
| `KlaBlockingBrush` | `KlaErrorBrush` |

`Kla*Style` names in the [compiled adapter](../src/KLCode.Wpf/Resources/KLCodeControls.xaml)
are compatibility styles based on the same shared controls. They do not define
a second palette or set of control templates.

## Icons

### In-window GUI icons

Use the approved semantic roles in the **[GUI icon catalog](../lib/_icons/gui/README.md)**.
That catalog owns the complete 17-role key table, from Search and Favorite to
Information, Warning, Error and Success. Original SVGs, the pinned revision in
[source.json](../lib/_icons/gui/source.json), and
[license notices](../lib/_icons/gui/LICENSE.lucide.txt) stay together.

Ordinary GUI icons render at 16 WPF units, using a 24-unit source canvas and
1.5-unit source stroke. Keep the full source canvas; tightly cropped geometry
would change the apparent size of different symbols. Use semantic resources
instead of per-window file paths or copied geometry.

| Need | Choose | Behavior |
| --- | --- | --- |
| Icon inside a button, toggle or stateful control | `KlaGuiIcon` + a `Kla<Role>Geometry` resource | Inherits foreground; the style uses `KlaDisabledTextBrush` when disabled |
| Fixed-color artwork required as an `Image.Source` | `KlaIcon<Role>` DrawingImage | Uses the shared `KlaGuiIconPen` with `KlaTextBrush`; does not inherit the Image/parent foreground or automatically recolor when disabled |

Use the presenter for an interactive icon that must follow control state:

```xml
<Button Style="{StaticResource KlaIconButton}"
        AutomationProperties.Name="Clear search">
    <ContentControl Style="{StaticResource KlaGuiIcon}"
                    Content="{StaticResource KlaClearSearchGeometry}"/>
</Button>
```

For an icon/text action, let both children follow the button's foreground:

```xml
<Button Style="{StaticResource KlaIconTextButton}">
    <StackPanel Orientation="Horizontal">
        <ContentControl Style="{StaticResource KlaGuiIcon}"
                        Content="{StaticResource KlaReadElementGeometry}"
                        Margin="{StaticResource KlaPairGap}"/>
        <TextBlock Text="Read Element" VerticalAlignment="Center"
                   Foreground="{Binding Foreground, RelativeSource={RelativeSource AncestorType=Button}}"/>
    </StackPanel>
</Button>
```

Avoid a local `Foreground` on the presenter when its disabled style should
choose the color. Decorative presenters do not take focus or intercept clicks;
the containing action needs an accessible name. A fixed-color search image is
also available:

```xml
<Image Source="{StaticResource KlaIconSearch}"
       Width="{StaticResource KlaIconSize}" Height="{StaticResource KlaIconSize}"
       Focusable="False" IsHitTestVisible="False"/>
```

Message headings may use the feedback symbols. Status chips keep their words
and borders. Larger Browse, Reset, Copy and Open Folder actions remain text-only.
An icon does not change the tool's behavior or classification.

### Generating artwork and the wordmark

[generate_gui_icons.py](../scripts/generate_gui_icons.py) generates three outputs:

- [KLCodeIcons.xaml](../lib/_icons/gui/KLCodeIcons.xaml): geometry-only resources.
- The `generated-icons` block in [Foundation](../lib/GUI/Resources/KLCodeFoundation.xaml): DrawingImage resources.
- [KLCodeWordmark.xaml](../lib/_logos/KLCodeWordmark.xaml): wordmark geometry and drawing offset from the repository SVG.

Edit attributed SVG sources and the generator's role mappings, then run
`python -B scripts/generate_gui_icons.py`. Use `--check` to detect stale outputs.
Do not hand-edit generated XAML. The shared wordmark template uses the generated
geometry at 70 x 12; its Path drawing transform preserves the former rendering.
No runtime SVG renderer is required.

### Ribbon assets

Ribbon artwork uses transparent-background PNGs in [lib/_icons](../lib/_icons/).
Keep a single foreground color unless the command needs additional detail.
Lucide's simple outline shapes are the established visual reference; the
in-window catalog's pinned sources and generation pipeline remain separate
from ribbon PNG exports.

Name reusable PNG assets `<icon-name>_<size>px_<color>.png`, for example
`drill_32px_orange.png`.

| Filename suffix | Brand color | Hex |
| --- | --- | --- |
| `_orange.png` | KLOrange | `#FF8000` |
| `_green.png` | KLGreen | `#33714F` |
| `_light.png` | KLWhite | `#E5E4E2` |
| `_dark.png` | KLCharcoal | `#1A252B` |

| Export size | Intended use |
| --- | --- |
| 16 x 16 px | Small/stacked ribbon controls |
| 24 x 24 px | Medium controls |
| 32 x 32 px | Normal command icons |
| 96 x 96 px | Reusable source/export maximum |

New DevSandbox prototypes start with
[drill_32px_orange.png](../lib/_icons/drill_32px_orange.png). Keep prototype-only
exceptions local to the bundle until promotion. Preserve the established
pyRevit bundle layout and icon metadata; a GUI migration does not authorize a
ribbon redesign or replacement of source assets.

## GUI components and style selection

[KLCodeComponents.xaml](../lib/GUI/Resources/KLCodeComponents.xaml) is the shared
loader entry point. The following keys are available to both Python and compiled
windows; compiled consumers can also use their existing adapter aliases.

### Actions and choices

| Style | Control | Dimensions | Use |
| --- | --- | --- | --- |
| `KlaButton` | Button | 104 x 28 | Standard action |
| `KlaButtonPrimary` | Button | 216 x 32 | Main action; font size 14 |
| `KlaButtonSecondary` | Button | 104 x 28 | Secondary action on component surface |
| `KlaLinkButton` | Button | 104 x 28 | Text action, transparent at rest; Favorites/Recent/Clear Filters |
| `KlaGhostButton` | Button | 104 x 28 | Outlined action, such as Cancel beside the main action |
| `KlaIconTextButton` | Button | 128 x 28 | Approved icon plus caption |
| `KlaIconButton` | Button | 28 x 28 | Icon-only action with an accessible name |
| `KlaButtonClose` | Button | 60 x 18 | Header Close; the shell supplies it |
| `KlaRadioButton` | RadioButton | Minimum height 28 | Exclusive choices with circular indicators |
| `KlaSegmentButton` | RadioButton | Height 28; width fits content | Exclusive toolbar segments inside a bordered group |
| `KlaToggle` | ToggleButton | 104 x 28 | Persistent on/off option |

`KlaFoundationButton`, `KlaFoundationMainButton` and `KlaSecondaryButton` remain
valid existing names. The role aliases above are preferred for new markup.
Preserve workflow action placement when migrating a window. If a localized
caption cannot fit its role, review a shared variant and render it; do not
silently shrink fonts or invent a per-window button size.

### Fields, text and collections

| Style | Control | Use |
| --- | --- | --- |
| `KlaInput` | TextBox | Standard 32-high input |
| `KlaInputCompact` | TextBox | Compact 24-high form input |
| `KlaTextPromptInput` | TextBox | 36-high input, FontSize 24, centered Segoe UI Bold; opt-in Text prompt only |
| `KlaFilter` | TextBox | 24-high search/filter; font size 14 |
| `KlaReadOnlyField` / `KlaCompactReadOnlyField` | TextBox | Read-only field, standard 32 or compact 24 high |
| `KlaMultilineReadout` | TextBox | Wrapped read-only output, minimum height 64, bounded by the caller with scrolling |
| `KlaComboBox` / `KlaCompactComboBox` | ComboBox | Standard 32 or compact 24 high; minimum width 104; popup maximum height 260 |
| `KlaLabel` / `KlaCompactFieldLabel` | Label | Ordinary label / vertically centered compact field label |
| `KlaPromptLabel` | Label | 14-unit, normal-weight section prompt with a label target |
| `KlaSectionHeading` / `KlaPromptText` | TextBlock | Wrapped 14-unit heading / normal-weight prompt text |
| `KlaInfoText` | TextBlock | Muted wrapped information |
| `KlaCheck` | CheckBox | Checked/unchecked/indeterminate indicator with wrapped caption |
| `KlaList` / `KlaListItem` | ListBox / ListBoxItem | Checked-list host and native WPF row behavior |
| `KlaDataGrid` | DataGrid | Shared read-only review table with shared header, row and cell styles |
| `KlaDataGridStatusCell` | DataGridCell | Centered status content |
| `KlaSection` / `KlaBanner` | Border | Bordered field group / information banner |
| `KlaStatusChip`, `KlaStatusReady`, `KlaStatusWarning`, `KlaStatusError` | Border | Neutral/ready/warning/error chip; use `KlaStatusText` for its caption |
| `KlaSplitter` | GridSplitter | Review-pane divider; minimum size and keyboard increment 4 |
| `KlaLink` | Hyperlink | Footer-like link styling; the caller/adapter owns navigation |

A bare TextBox or ComboBox takes the compact 24-high implicit style. A bare
CheckBox takes the shared checkbox style. Other controls require an explicit
style. Prefer explicit keys in new bodies so the intended role is visible.
The named `KlaDataGrid` is read-only; an editable table needs a deliberate
workflow design rather than an assumption that this style supplies editing.

For a labeled compact field, use a Label target and an automation name:

```xml
<Label Content="Prefix:" Target="{Binding ElementName=input_prefix}"
       Style="{StaticResource KlaCompactFieldLabel}"/>
<TextBox x:Name="input_prefix" Style="{StaticResource KlaInputCompact}"
         AutomationProperties.Name="Name prefix"/>
```

These two elements belong in the caller's layout; the full naming composition
below supplies their aligned columns and rows.

### Shared body compositions

`KlaFieldRows` and `KlaFilteredCheckList` are fixed layout recipes implemented
as ItemsControl styles with Grid ItemsPanels. Their direct items remain the
window's named controls. Keep event handlers, bindings and item templates in
the window body; placing them inside a new ControlTemplate would change their
namescope and controller access.

| Composition | Direct-item placement | Existing uses |
| --- | --- | --- |
| `KlaFieldRows` | Labels in column 0, inputs in column 1; four rows at 0/2/4/6, separated by 8-unit gaps | Form, Find/Replace Views and Sheets, Duplicate Sheets |
| `KlaFilteredCheckList` | Filter 0, prompt 2, expanding list 4, secondary content 6, main action 8 | Selection reference, SelectFromDict, Create From Rooms, Steel PSF |

Naming columns are 60/240; each field row is 24 high. Wrap the naming group in
`KlaSection` for its 12-unit inset. Secondary checklist content may contain
several action/settings rows, as Steel PSF does. These recipes share layout,
not selection, filtering, validation or confirmation behavior.

The [five references](../lib/GUI/_templates/README.md) provide complete examples:
Selection, Form, Message, Options and Review. Use Gallery's fictional states to
inspect them without invoking production operations.

## Window geometry and spacing

All WPF dimensions below are device-independent units. Ribbon export sizes are
pixels. Tool-specific window bounds and minimum sizes belong to the window;
repeated control dimensions belong to shared roles/tokens.

| Part | Rule / resource |
| --- | --- |
| Window | Segoe UI 12; charcoal background; borderless transparent style |
| Header/footer | Each 24 high, `KlaChromeRow` |
| Header columns | 86 / flexible / 86, `KlaHeaderSideColumn` |
| Header artwork/title | 70 x 12 wordmark; centered 14-unit title, ellipsis without tooltip |
| Header Close | 60 x 18, font size 10; glyph placement through `KlaCloseGlyphLift` |
| Footer columns | 100 / flexible / 100, `KlaFooterSideColumn` |
| Footer content | Prototype/Outreach links green (`KlaFooterLinkBrush`), caller's pure version gray (`KlaFooterVersionBrush`); links turn white on hover/focus |
| Body inset | 16 horizontally and 8 below header/above footer, `KlaBodyInset` |
| Typography | Body 12, title/prompts/main action 14; constant labels use Title Case |
| Corners/borders | Card 8, input 6, chip 4, checkbox 2; hairline 1 |
| Checkbox list | Ordinary single-line rows measure 20 high with a 4-unit box/text gap; long captions wrap |
| List selection | Native WPF ListBoxItem template retains its blue hover/selection; it is an intentional current exception to the green table styling |
| Scrollbars | Shared vertical/horizontal templates; `KlaList` keeps its vertical bar visible, while `KlaDataGrid` and standalone Recall use Auto where specified |
| Grid spacing | Header padding 8,6 (`KlaHeaderCellInset`); cell padding 8,4 (`KlaCompactInset`) |

The [current Python footer render](knowledge/reviews/design-system/2026-10-29-footer-color-evidence/selection.png)
and [compiled footer render](knowledge/reviews/design-system/2026-10-29-footer-color-evidence/compiled-source-picker.png)
show the owner-requested original green links and gray version text.

Use `KlaFoundationWindow` or its `KlaWindow` alias for the window and
`KlaWindowShell` for the named `window_shell` ContentControl. The shell supplies
the header/footer and body inset. Do not copy chrome into a new body.
The foundation defaults to NoResize; a resizable borderless window explicitly
uses `ResizeMode="CanResizeWithGrip"` and needs minimum-size/overflow review.

### Typed spacing resources

The spacing scale is 4 / 8 / 12 / 16 / 24. That scale does not imply a
`KlaGridSpace` resource exists for every value. WPF rows/columns, margins and
control sizes require different resource types.

| Resource | Type | Value / use |
| --- | --- | --- |
| `KlaGridSpace4`, `KlaGridSpace8`, `KlaGridSpace16` | GridLength | Existing spacer rows/columns: 4, 8 and 16 |
| `KlaChromeRow`, `KlaControlRow`, `KlaCompactRow`, `KlaFilterRow` | GridLength | Rows of 24, 32, 28 and 24 respectively |
| `KlaCompactFieldRow` | GridLength | Compact naming row, 24 |
| `KlaCompactFieldLabelColumn`, `KlaCompactFieldInputColumn` | GridLength | Naming columns, 60 and 240 |
| `KlaPairGap` | Thickness | `0,0,8,0`, between related horizontal controls |
| `KlaBodyInset` | Thickness | `16,8,16,8`, shell body padding |
| `KlaSectionPadding` | Thickness | 12, field-group inset |
| `KlaCompactInset` | Thickness | `8,4`, compact component/cell padding |
| `KlaInputPadding` | Thickness | `8,0`, input/button text padding |
| `KlaControlHeight`, `KlaCompactHeight`, `KlaCompactFieldHeight` | Double | Control heights of 32, 28 and 24 |

`KlaGridSpace12` and `KlaGridSpace24` are not currently defined. If a new shared
layout needs one, add a correctly typed token and verify its consumers. Do not
pass a Thickness to a RowDefinition or assume a Double resource substitutes for
a GridLength. Keep Foundation/Components free of numeric layout literals;
consumer Margin/Padding drift is reported separately by the scale checker.
SharedPrimitives currently retains literal scrollbar/wordmark dimensions and
is exempt from that numeric check. Changing a token still needs review against
these design rules, even when all controls continue to match the token.

## Architecture and resource ownership

XAML resources define values, appearance and reusable layout. Python/C# adapters
load the resources and connect common chrome. Each tool owns its data, workflow,
showing/dismissal semantics and Revit operations.

| Source | Responsibility / dependencies |
| --- | --- |
| [Palette](../lib/GUI/Resources/KLCode_palette.xaml) | Brand role brushes and legacy color aliases |
| [Foundation tokens](../lib/GUI/Resources/KLCodeFoundationTokens.xaml) | Typed dimensions/fonts/insets and semantic component/state brushes |
| [Shared primitives](../lib/GUI/Resources/KLCodeSharedPrimitives.xaml) | Merges Palette and generated wordmark; defines wordmark/footer-link/scrollbar presentation |
| [Chrome data](../lib/GUI/Resources/KLCodeChrome.xaml) | Footer URIs and default English labels |
| [Generated GUI geometry](../lib/_icons/gui/KLCodeIcons.xaml) | Geometry-only leaf dictionary |
| [Foundation](../lib/GUI/Resources/KLCodeFoundation.xaml) | Merges Primitives, Tokens, Chrome and Geometry; owns shell/basic styles, icon presenter/pen and generated images |
| [Components](../lib/GUI/Resources/KLCodeComponents.xaml) | Merges Foundation; adds field groups, compositions, options, states, tables, aliases and implicit-style policy |
| [Command Switch styles](../lib/GUI/Resources/KLCodeCommandSwitch.xaml) | Merges Components; opt-in floating command/toggle pills using existing semantic colors |
| [Compiled controls](../src/KLCode.Wpf/Resources/KLCodeControls.xaml) | Merges Components and supplies existing C# style names through BasedOn |
| Window body XAML | Named controls, bindings, events and tool-specific arrangement |
| Host/tool controller | Ownership, workflow, validation, lifetime and model/application actions |

Palette and FoundationTokens own concrete brand, state and component colors.
Other shared dictionaries reference those brushes; templates also use Transparent
for intentionally empty fills/borders. Generated geometry supplies artwork.
The resource graph follows the dependencies above, rather than a rule that each
file merges the immediately preceding row. Compiled projects link the canonical
files as WPF Pages; they do not copy them into a separate theme implementation.

## Host and keyboard contracts

### Python and pyRevit

[load_window](../lib/GUI/window_chrome.py) accepts
`(window, xaml_path, title, version=None, navigate=None, close_handler=None)`.
It merges Components before loading body XAML. It uses the window's callable
`load_xaml` when present, otherwise `wpf.LoadComponent`. It does not show the
window, replace its DataContext or perform a model operation.

The resource cache belongs to the loaded Python module/engine; do not assume
all pyRevit engines in a Revit process share one instance. Within that module,
windows merge the same dictionary instance. Treat shared resources as shared
presentation, and keep tool-specific data/strings in the window's own scope.

Supply the caller's `__title__` and pure `__version__`, such as `v1.3`. A missing
or invalid version leaves the center footer empty. The loader does not infer
the extension version. [WindowMetadata](../lib/GUI/window_metadata.py) carries
identity only; [shared test vectors](../lib/GUI/window_metadata_vectors.json)
cover its formatting rules in both languages. The shell reserves its Tag for
this metadata; body Content/DataContext remain caller-owned.

Close calls the optional caller close handler or `window.Close()`. Header drag
and footer navigation are connected by the adapter. A Gallery presenter passes
`navigate(uri)` to simulate navigation; an ordinary caller uses OS navigation.
`fit_window_height(window)` is an optional measurement helper: it clamps the
content height to the caller's MinHeight/MaxHeight and does not show the window.
`window._kla_chrome.hide_footer()` collapses that shell instance's footer and
named footer row. Text uses it; resources and other windows are unaffected.

Installed pyRevit `6.5.3.26176+2017` exposes
`load_xaml(self, xaml_source, literal_string=False, handle_esc=True, set_owner=True)`.
The current adapter's positional call retains host initialization and ownership,
and also retains pyRevit's Escape handler. This is a known boundary: the host
handler can close a WPFWindow before the shared adapter's caller close policy
runs. A simulated installed-handler order reproduced that sequence. Do not
claim identical custom-cancel behavior across bare WPF and pyRevit subclasses
until the adapter contract is corrected and checked in the host.

### Compiled WPF

[ThemeBootstrapper.Apply](../src/KLCode.Wpf/ThemeBootstrapper.cs) merges shared
controls followed by common locale strings before InitializeComponent.
Tool-specific strings are merged through ApplyToolStrings.
[WindowChrome.Attach](../src/KLCode.Wpf/WindowChrome.cs) connects the named shell
parts with the caller's title/version and optional close callback. The C#
controller retains its DataContext, model services and modal/modeless lifetime.

The shell reads Close/Prototype/Outreach labels through DynamicResource; a later
locale dictionary can override them. The common adapter currently ships English
as its available fallback. Recall's English/German/Korean body-caption checks
do not establish those translations for every tool. Footer destinations are
typed Uri resources in Chrome data. Packaged add-ins must be rebuilt for their
target runtime to consume changed linked XAML; source smoke tests do not update
the deployed DLLs.

### Keyboard and accessibility

| Interaction | Contract and current boundary |
| --- | --- |
| Tab | Body is declared before chrome to support body-first traversal, then Close and footer links. Initial focus and complete traversal still need live-host acceptance. |
| Enter | Explicit `IsDefault="True"` identifies a default action. The visual primary style does not set it. Find/Replace Views, Find/Replace Sheets and Steel PSF currently omit it on their main actions. |
| Escape | Shared adapters request the Close policy. Python WPFWindow subclasses also retain the host handler described above. |
| Cancel | Use an explicit caller cancellation policy; `IsCancel="True"` is a WPF dialog setting, not a substitute for validating modeless/custom-close behavior. |
| Focus | Visible marks/borders must not move layout; footer focus changes color without changing text weight. |
| Disabled body | Disable the body so header Close remains usable. Use semantic disabled brushes; verify both text and interactive icons. |
| Names and labels | Give inputs/actions meaningful AutomationProperties.Name values; connect Label.Target to its field. Name the containing action when its icon is decorative. |
| Long content | Bound and scroll long text/lists, retain readable labels and check minimum sizes, DPI/work-area placement and keyboard reachability in Revit. |

These are source contracts and known implementation limits. They do not mark
the owner's live Revit review complete.

## Reusable dialogs

Use [GUI.dialogs](../lib/GUI/dialogs/README.md) for prepared-data dialogs.
The five opt-in bodies do not migrate existing commands or their pyRevit calls.

| Need | Modal API | Result |
| --- | --- | --- |
| Message notice and optional details | `show_message(title, message, ...)` | `ok` or `cancel` action |
| Grouped searchable single/multiple selection | `select_items(title, items, ...)` | `accept` with original payload(s), or `cancel` |
| Sheets, revisions, open documents | `select_sheets`, `select_revisions`, `select_open_documents` | Read-only collection followed by selection; explicit document/context required |
| Floating Command Switch | `command_switch(title, choices, switches=..., ...)` | `accept` with command key/switch states, or `cancel` |
| Existing Action choice (future redesign) | `choose_action(title, choices, ...)` | Existing highlighted-row/Continue contract retained |
| Text with optional validation | `ask_text(title, prompt, ...)` | `accept` with raw text, including blank, or `cancel` |

```python
from GUI.dialogs import SelectionItem, select_items

rows = [SelectionItem('first', 'Example', first_payload),
        SelectionItem('second', 'Example', second_payload)]
result = select_items(__title__, rows, version=__version__, owner=owner_handle)
if result.action == 'accept':
    selected_payloads = result.value
```

Importing the package is host-free. Factories lazily load WPF and return unshown
bare WPF windows; modal helpers call ShowDialog and return `DialogResult`.
Supply the owner and caller version. No import/factory infers or queries the
current document. Specialized modal helpers explicitly call separate read-only
collectors before showing UI. Existing CustomAlert/SelectFromDict remain unchanged.

Close/Cancel cancel. Selection requires Select, with Enter/double-click acceptance
disabled in both checkbox modes. Text Enter validates/accepts; Message Enter
acknowledges OK. The existing Action choice default remains deferred. Command
Switch Enter chooses a focused command or sole enabled search match while search
is focused; Escape clears search before cancelling. Other dialogs Escape cancel.
These bare windows do not inherit
pyRevit WPFWindow's competing Escape handler. The earlier host boundary and
missing defaults in existing tools remain separate. Actual keyboard, owner/modal
lifetime and DPI still require live acceptance.

Selection uses stable keys for duplicate labels, clones checks, preserves input
order and hidden checks, and excludes disabled rows. All/None affects visible
eligible rows only. Single selection enforces exclusive checking; highlighting
alone does not check a row. No first row is checked implicitly. Text preserves
raw input; required/validator failures remain inline. Validators return an error
string or None. Inspect result.action explicitly: accepted blank and Cancel
are different outcomes.

Bodies reuse the shared shell, buttons/fields/lists, status brushes, icon
geometry and green/gray footer roles. Opt-in `KlaDialogCheck` presents a label
and description using the existing checkbox template; `KlaDialogDescription`
handles secondary/disabled text; `KlaDialogListItem` disables unavailable rows.
Message/details overflow is bounded and scrollable. Initial Message height fits
content; manual width changes no longer force a new height. Deferred Details
measurement grows the bottom and protects the message viewport until capped.
Text removes only its footer row and uses the larger Segoe UI Bold field,
content-fitting prompt/error height and single-line entry. Command Switch is a
compact, fixed-width, content-height floating panel without header/footer. Its
buttons choose immediately, toggles remain visible during filtering, corner x
cancels, and blank panel clicks leave it open.

Search **Shared dialog** in Gallery for Sheets, Revisions, Open Documents, List
Single, List Multiple, Message, Text, Command Switch and existing Action choice.
All nine entries have five fictional states. The collectors are never called
by Gallery. See [API examples](../lib/GUI/dialogs/README.md) and
[refinement verification](knowledge/reviews/design-system/2026-10-29-dialog-refinement.md).

## Creating a window

Start from the [reference templates](../lib/GUI/_templates/README.md). Keep
`window_shell` as a ContentControl using `KlaWindowShell`; put only workflow
content inside it. The following body illustrates the loading contract; the
handler is supplied by the Python example below.

```xml
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Width="360" Height="240" Style="{StaticResource KlaWindow}">
    <ContentControl x:Name="window_shell" Style="{StaticResource KlaWindowShell}">
        <Grid x:Name="window_body">
            <Grid.RowDefinitions>
                <RowDefinition Height="Auto"/>
                <RowDefinition Height="{StaticResource KlaGridSpace8}"/>
                <RowDefinition Height="{StaticResource KlaCompactFieldRow}"/>
                <RowDefinition Height="*"/>
                <RowDefinition Height="{StaticResource KlaControlRow}"/>
            </Grid.RowDefinitions>
            <Label Content="Name:" Target="{Binding ElementName=name_input}"
                   Style="{StaticResource KlaLabel}"/>
            <TextBox x:Name="name_input" Grid.Row="2"
                     Style="{StaticResource KlaInputCompact}"
                     AutomationProperties.Name="Example name"/>
            <Button Grid.Row="4" Content="Apply" Click="apply_example"
                    Style="{StaticResource KlaButtonPrimary}" IsDefault="True"/>
        </Grid>
    </ContentControl>
</Window>
```

```python
from pyrevit import forms  # Initializes the installed WPF support.
from System.Windows import Window
from GUI.window_chrome import load_window

class ExampleWindow(Window):
    def __init__(self, body_path, title, version):
        self.result = None
        load_window(self, body_path, title, version)

    def apply_example(self, sender, args):
        self.result = self.name_input.Text
        self.Close()

# body_path is the example XAML path; identity comes from the command.
window = ExampleWindow(body_path, __title__, __version__)
window.ShowDialog()
# The caller decides what to do with window.result.
```

For a compiled window, merge ThemeBootstrapper resources before
InitializeComponent, then call
`WindowChrome.Attach(this, window_shell, title, version)`. Follow an existing
compiled view for tool strings and service injection.

1. Read the command's adjacent SPEC and preserve workflow/lifetime contracts.
2. Choose explicit shared roles, typed spacing and a suitable reference body.
3. Keep named workflow controls and handlers in the window's namescope.
4. Supply identity, accessible labels and explicit default/cancel semantics.
5. Add an allowlisted Gallery adapter and fictional states where appropriate;
   source discovery alone must not grant execution permission. Five compiled
   Gallery entries remain deferred under the separate Gallery plan.
6. Update the command SPEC and run the relevant checks below. Actual Revit
   operations remain the controller's responsibility and need host evidence.

## Validation

| Tier | What it establishes | Limits |
| --- | --- | --- |
| CPython source/unit tests | Metadata, adapter boundaries with fakes, resource/caller contracts, deterministic fixtures and generated artwork | No rendered WPF or Revit behavior; the caller scanner does not prove every dynamic route |
| Icon generation check | Generated resources match the attributed source/generator | Does not establish interactive state or visual suitability by itself |
| UI scale checker | Numeric-layout discipline in Foundation/Components; advisory off-scale consumer Margin/Padding values | Primitives is exempt; it is not a complete UI/accessibility or token-value approval check |
| IronPython/WPF probes | Real XAML/bindings/layout, fictional state interactions, overflow, icon presentation, scrollbar geometry and wordmark pixels | Windows are constructed/rendered without live Revit ownership, pointer/keyboard/DPI or production operations |
| C# source tests | Resource and packaging-source contracts | Cannot establish runtime loading; the Windows smoke checks are a separate tier |
| C# desktop smoke, net48 and net8.0-windows | Actual compiled window construction/rendering against fictional providers | No deployed Revit DLL acceptance, real load/import/database actions or live keyboard review |
| Live Revit | Ownership, focus, drag, default/cancel behavior, DPI/work area, accessibility and real workflows | Record exact host/version and outcomes under GUI-08; owner review remains pending |

Many geometry probes read expected dimensions from the same tokens used by the
controls. That verifies consistent consumption, but a token edit must also be
checked against the approved dimensions in this guide and inspected in renders.
Do not interpret a green source/probe suite as complete design acceptance.

Run the applicable commands from the repository root:

```powershell
python -B scripts/generate_gui_icons.py --check
python -B scripts/check_ui_scale.py
python -B -m unittest discover -s tests -p "*test.py"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate_ui_gallery_wpf.ps1 -OutputDirectory <tmp>
dotnet test src/KLCode.Wpf/Tests/KLCode.Wpf.Source.Tests --no-restore
dotnet run --project src/KLCode.Wpf/Tests/KLCode.Wpf.Desktop.Smoke --framework net48 --no-restore -- <tmp>
dotnet run --project src/KLCode.Wpf/Tests/KLCode.Wpf.Desktop.Smoke --framework net8.0-windows --no-restore -- <tmp>
```

Replace `<tmp>` with a writable evidence directory. The probes default to the
installed IronPython engine location and the .NET commands require restored
dependencies. Run focused checks for ordinary changes and broaden them when
shared resources or host behavior change. The
[latest Windows record](knowledge/reviews/design-system/2026-10-29-gui-architecture-windows.md)
contains measured results, representative renders and the owner's host checklist;
the [active plan](plans/custom-window-consolidation.md) remains the task authority.
