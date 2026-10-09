# KLCode Design System

This file records the current visual system used by the KLCode repository. It
covers the legacy IronPython/pyRevit dialogs, their DevSandbox gallery, and
the compiled WPF add-ins. It does not replace host-specific runtime validation.
The source descriptions below were rechecked on 2026-10-08 at
`089da1b7d88e0df9dec2cc127659a24e051b9163`; see the
[design-system reviews](docs/reviews/design-system/README.md) for dated findings
and live-acceptance boundaries.

## Master Design Colors

These are the named colors used across KLCode ribbon icons and WPF GUIs. This table defines the color names used throughout this document; usage guidance belongs in the relevant icon and GUI sections.

| KLName | Value | Description |
| --- | --- | --- |
| KLCharcoal | `#1A252B` | Dark blue-green charcoal |
| KLGreen | `#33714F` | Deep KLCode green |
| KLGreen-dark | `#286048` | Dark muted green |
| KLGreen-secondary | `#407058` | Muted medium green |
| KLOrange | `#FF8000` | Bright orange |
| KLWhite | `#E5E4E2` | Soft warm off-white |
| white | `#FFFFFF` | Pure white |
| gray | `#808080` | medium gray |
| KLGray-dark | `#FF3F3F3F` | Dark neutral gray |
| KLCharcoal-gray | `#FF4F4F4F` | Medium-dark charcoal gray |
| KLGray-scroll | `#505050` | Neutral dark gray |
| KLGray-disabled | `#888888` | Muted medium-light gray |
| KLGray-disabled-check | `#FF6C6C6C` | Muted gray |
| KLCharcoal-black | `#FF131313` | Nearly black charcoal |
| black | `#000000` | Pure black |
| KLGreen-transparent-a | `#33286048` | Transparent dark green |
| KLGreen-transparent-b | `#33307050` | Transparent muted green |
| KLGreen-checkbox-a | `#88286048` | Semi-transparent dark green |
| KLGreen-checkbox-b | `#99307050` | Semi-transparent muted green |
| warning-gold | `#DAA520` | Warm golden yellow |
| info-green | `#3CB371` | Medium sea green |

`lib/GUI/Resources/KLCode_palette.xaml` supplies the named palette consumed by
the compiled-WPF adapter: `src/KLCode.Wpf/KLCode.Wpf.csproj` links it as
`Resources/KLCodePalette.xaml`, which `KLCodeControls.xaml` merges. The legacy
`WPF_styles.xaml` dictionary currently
repeats the same legacy brush values rather than merging that file. The
repository wordmark asset is `lib/_logos/KLCode_text_1024x256px.svg` (with a
PNG export). The palette consolidation decision and test-contract mismatch are
recorded in the [current-state review](docs/reviews/design-system/2026-10-08-current-state-review.md).

| Property | Value |
| --- | --- |
| KLCharcoal sample | `#1A252B` |
| KLGreen sample | `#33714F` |
| KLGreen-dark sample | `#286048` |
| KLGreen-secondary sample | `#407058` |

## Icons

KLCode ribbon icons are transparent-background PNGs. Use a single foreground color unless the command clearly needs additional visual detail.

### Source Assets

Reusable source icons live in `lib/_icons/`. Keep source assets at `96 x 96 px` or smaller. Export command icons at the size needed by the bundle, usually `32 x 32 px` for large ribbon buttons.

Name reusable source icons with a descriptive lowercase icon name, size, and color: `<icon-name>_<size>px_<color>.png`, such as `drill_32px_orange.png`.

| Color name | Color | File reference |
| --- | --- | --- |
| KLOrange | `#FF8000` |  `<icon-name>_<size>px_orange.png` |
| KLGreen | `#33714F` |  `<icon-name>_<size>px_green.png` |
| KLWhite | `#E5E4E2` |  `<icon-name>_<size>px_light.png` |
| KLCharcoal | `#1A252B` |  `<icon-name>_<size>px_dark.png` |

### Standard Sizes

| Size | Use |
| --- | --- |
| `16 x 16 px` | small/stacked controls |
| `24 x 24 px` | medium controls |
| `32 x 32 px` | normal command icons |
| `96 x 96 px` | reusable source/max size |

### Design Reference

Use [Lucide Icons](https://lucide.dev/icons/) as the visual reference for new or refreshed ribbon icons: simple outline shapes, clear silhouettes, and consistent stroke weight.

### Prototype Icons

New prototype scripts should start with `lib/_icons/drill_32px_orange.png` as the default icon. Prototype-only exceptions should stay local to the prototype bundle until they are promoted.

## GUI Colors

`lib/GUI/Resources/WPF_styles.xaml` defines the legacy pyRevit brush keys and
control templates. `lib/GUI/Resources/KLCode_palette.xaml` carries matching
palette keys for compiled WPF, and
`src/KLCode.Wpf/Resources/KLCodeControls.xaml` merges that compiled palette.
The legacy and compiled palette values are currently defined in separate files.

| Token | Value | KLName |
| --- | --- | --- |
| `window_background` | `#1A252B` | KLCharcoal |
| `header_background` | `#1A252B` | KLCharcoal |
| `text_white` | `#E5E4E2` | KLWhite |
| `text_gray` | `Gray` | gray |
| `text_green` | `#33714F` | KLGreen |
| `button_fg_normal` | `White` | white |
| `button_bg_normal` | `#286048` | KLGreen-dark |
| `button_bg_hover` | `#407058` | KLGreen-secondary |
| `border_green_dark` | `#286048` | KLGreen-dark |
| `border_green` | `#33714F` | KLGreen |
| `uncheckbox_checked_colour` | `Gray` | gray |
| `checkbox_checked_colour` | `#286048` | KLGreen-dark |
| `footer_donate` | `#407058` | KLGreen-secondary |

## GUI Properties

`lib/GUI/_templates/KLCodeMainTemplate.xaml` is the visual authority for these values. The shared dictionary exposes its outlined wordmark, compact close control, action buttons, filter field, checkbox, list, and scrollbar treatments. These values apply to windows that load the shared dictionary through `my_WPF.add_wpf_resource()` unless a nested or window-level resource overrides them.

Most reusable dialogs, including the two Find and Replace prototypes, load the shared dictionary through `my_WPF.add_wpf_resource()`. The View Range editor instead uses `forms.WPFWindow` with its own `Window.Resources`; after loading it assigns the shared `KLCodeWordmark` template to `wordmark_host` in Python. The UI Gallery is a separate DevSandbox surface with its own local resources.

### Color Properties

The unqualified `ComboBox` and `ComboBoxItem` rows below describe the legacy
shared styles in `WPF_styles.xaml`. View Range and the compiled WPF adapter have
different templates, summarized under [ComboBox implementation boundaries](#combobox-implementation-boundaries).

| Control | UI part | XAML property | Implementation value | KLName |
| --- | --- | --- | --- | --- |
| `Button` | default | `Background` | `button_bg_normal` | KLGreen-dark |
| `Button` | default | `Foreground` | `button_fg_normal` | white |
| `Button` | hover state | `Background` | `button_bg_hover` | KLGreen-secondary |
| `TextBlock` | default | `Foreground` | `text_white` | KLWhite |
| `TextBox` | default | `Background` | `header_background` | KLCharcoal |
| `TextBox` | default | `Foreground` | `text_white` | KLWhite |
| `TextBox` | default | `BorderBrush` | `border_green` | KLGreen |
| Search filter | icon | `Source` | `lib/_icons/search_16px_light.png` | light search icon |
| Search filter | field | `Style` | `KLCodeFilterTextBox` inside a 1 px KLGreen, 6 px-radius shell | KLCharcoal / KLGreen |
| `Label` | default | `Foreground` | `text_green` | KLGreen |
| `CheckBox` | label text | `Foreground` | `White` | white |
| `CheckBox` | unchecked box | `Background` | `window_background` | KLCharcoal |
| `CheckBox` | unchecked box | `BorderBrush` | `text_green` | KLGreen |
| `CheckBox` | checked box | `Background` | `checkbox_checked_colour` | KLGreen-dark |
| `CheckBox` | checkmark | `Stroke` | `#E5E4E2` | KLWhite |
| `CheckBox` | hover checkbox fill | `Background` | `button_bg_hover` | KLGreen-secondary |
| `ComboBox` | default | `Foreground` | `White` | white |
| `ComboBox` | selector body | `Background` | `header_background` | KLCharcoal |
| `ComboBox` | selector border | `BorderBrush` | `border_green` | KLGreen |
| `ComboBox` | arrow | `Fill` | `White` | white |
| `ComboBox` | disabled selected text | `Foreground` | `#888888`; selector body and arrow have no disabled override | KLGray-disabled |
| `ComboBox` | dropdown body | `Background` | `header_background` | KLCharcoal |
| `ComboBox` | dropdown border | `BorderBrush` | `border_green` | KLGreen |
| `ComboBox` | editable text field | `Background` | `#FF3F3F3F` | KLGray-dark |
| `ComboBox` | editable text field | `Foreground` | `#E5E4E2` | KLWhite |
| `ComboBoxItem` | default | `Foreground` | `White` | white |
| `ComboBoxItem` | highlighted state | `Background` | `#FF4F4F4F` | KLCharcoal-gray |
| `DataGrid` (UI Gallery local override) | default | `Background` | `header_background` | KLCharcoal |
| `DataGrid` (UI Gallery local override) | default | `Foreground` | `text_white` | KLWhite |
| `DataGrid` (UI Gallery local override) | border/grid lines | `BorderBrush`/`HorizontalGridLinesBrush` | `border_green_dark` | KLGreen-dark |
| `DataGrid` (UI Gallery local override) | alternate row | `AlternatingRowBackground` | `#FF131313` | KLCharcoal-black |
| `DataGridColumnHeader` (UI Gallery local override) | default | `Background` | `border_green_dark` | KLGreen-dark |
| `DataGridColumnHeader` (UI Gallery local override) | default | `Foreground` | `text_white` | KLWhite |
| `DataGridCell` (UI Gallery local override) | selected state | `Background` | `button_bg_hover` | KLGreen-secondary |
| `DataGridCell` (UI Gallery local override) | selected state | `Foreground` | `button_fg_normal` | white |
| `ListBox` | default | `Background` | `header_background` | KLCharcoal |
| `ListBox` | default | `BorderBrush` | `border_green_dark` | KLGreen-dark |
| `ScrollBar` | default | `Background` | `window_background` | KLCharcoal |
| `ScrollBar` | default | `Foreground` | `window_background` | KLCharcoal |
| `ScrollBar` | default | `BorderBrush` | `header_background` | KLCharcoal |
| `ScrollBarThumbVertical` | default | `Background` | `text_green` | KLGreen |
| `ContentControl` | header wordmark | `ContentTemplate` | `KLCodeWordmark`; `70 x 12`; `Margin=8,0,0,0` | outlined KLCode wordmark |

### Layout And Behavior Properties

| Control | UI part | XAML property | Implementation value |
| --- | --- | --- | --- |
| `Button` | default | `TextElement.FontFamily` | `Arial` |
| `Button` | default | `Cursor` | `Hand` |
| `Button` | button border | `CornerRadius` | `8` |
| `Button` | compact header close | `Style` | `KLCodeCloseButton`; `60 x 18`; 6 px radius |
| `Button` | action button | `Style` | `KLCodeActionButton`; 8 px radius |
| `TextBox` | default | `VerticalContentAlignment` | `Center` |
| `TextBox` | border style | `CornerRadius` | `5` |
| `Border` | default | `BorderThickness` | `1` |
| `Border` | default | `CornerRadius` | `10` |
| `CheckBox` | checkbox box | `Width` and `Height` | `16 x 16` |
| `CheckBox` | checkbox box | `CornerRadius` | `2` |
| `DockPanel` | default | `Margin` | `2` |
| `ComboBox` | default | `MinWidth` | `120` |
| `ComboBox` | default | `MinHeight` | `20` |
| `ComboBox` | shared toggle template key | `x:Key` | `ComboBoxToggleButton` |
| `ComboBox` | editable text host key | `x:Key` | `ComboBoxTextBox` |
| `ComboBoxItem` | shared item template padding | `Padding` | `2` |
| `DataGrid` | headers shown | `HeadersVisibility` | `Column` |
| `DataGrid` | selection mode | `SelectionMode` | `Single` |
| `DataGrid` | row resize | `CanUserResizeRows` | `False` |
| `DataGridColumnHeader` | header padding | `Padding` | `6,4` |
| `DataGridCell` | cell padding | `Padding` | `6,3` |
| `ListBox` | default | `ScrollViewer.VerticalScrollBarVisibility` | `Visible` |
| `ListBox` | default | `ScrollViewer.HorizontalScrollBarVisibility` | `Hidden` |
| `ListBox` | border style | `CornerRadius` | `10` |
| `ScrollBar` | default | `Opacity` | `0.9` |
| `ScrollBar` | default | `Margin` | `3` |
| `ScrollBar` | track border | `CornerRadius` | `10` |
| `ScrollBarThumbVertical` | thumb border | `CornerRadius` | `8` |

Selection-style branded windows use `text_white` for the filter label or icon, filter input text, and selection prompt label. Borders and separators remain on KLGreen/KLGreen-dark accents so labels such as `Select stories to review:` stay readable against the KLCharcoal background.

The View Range editor uses a command-local dark `ComboBox` template for the Associated Level selectors because shallow brush setters leave the native WPF selector surface light in Revit. The selector body, arrow well, popup border, and `ComboBoxItem` highlight all use KLCode token values.

The DevSandbox UI Gallery uses command-local `DataGrid` styles because table styling is not yet part of the shared WPF dictionary. Its catalog grid keeps the dark KLCharcoal body, KLGreen-dark header/grid lines, KLCharcoal-black alternating rows, and KLGreen-secondary selected cells.

### ComboBox implementation boundaries

| Implementation | Source | Arrow | Disabled behavior | Item padding |
| --- | --- | --- | --- | --- |
| Legacy shared | `lib/GUI/Resources/WPF_styles.xaml` | Literal `White` | Selected text changes to `#888888`; the selector body and arrow have no disabled override. | `2` |
| View Range local | `KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml` | `text_white` | Selector body changes to `#FF131313`; arrow and selected text use `text_gray`. | `4,3` |
| Compiled WPF | `src/KLCode.Wpf/Resources/KLCodeControls.xaml` | `text_green` | Selected text uses `KlaDisabledTextBrush` and selector opacity becomes `0.55`; no separate arrow/body disabled override. | `7,4` |

These are separate source contracts. The View Range values do not describe the
shared legacy template, and none of these source values establishes rendered
behavior in a live Revit host.

### Window Defaults

The shared GUI windows follow these conventions where present:

| Property | Implementation value | KLName |
| --- | --- | --- |
| `WindowStartupLocation` | `CenterScreen` | N/A |
| `HorizontalAlignment` | `Center` | N/A |
| `WindowStyle` | `None` | N/A |
| `ResizeMode` | `NoResize` for fixed dialogs | N/A |
| Header row height | `24` | N/A |
| Header edge columns | `86` | Reserves the title's centered visual lane |
| Search row height | `32` for list-selection windows | N/A |
| Header background | `header_background` | KLCharcoal |
| Close button size | `60 x 18` | N/A |

Command-local windows that use `forms.WPFWindow`, including the View Range editor and UI Gallery, keep the same chrome event names as shared windows: `button_close` for the header close button and `header_drag` for dragging the borderless header.

## Compiled WPF Add-in System

The compiled add-ins use a separate control adapter rather than loading the
IronPython `my_WPF` base class. This is deliberate: the adapter merges its
compiled palette file while keeping compiled-only tokens and WPF control
templates in a CLR-loadable assembly. Its base palette values match the legacy
dictionary, but the two files have not yet been consolidated.

| Layer | Source | Responsibility |
| --- | --- | --- |
| Compiled palette | `lib/GUI/Resources/KLCode_palette.xaml` | Named brush keys matching the legacy palette, such as `header_background`, `text_white`, and `button_bg_normal`. |
| Compiled semantic tokens | `src/KLCode.Wpf/Resources/KLCodeCompiledTokens.xaml` | Compiled-only surface, neutral, informational, warning, blocking, and checkbox tokens. |
| Compiled controls | `src/KLCode.Wpf/Resources/KLCodeControls.xaml` | `KlaWindowStyle`, header, button, input, selection, list, status-chip, and footer styles. |
| Shared compiled alert | `src/KLCode.Wpf/Views/KlaAlertWindow.xaml` | Reusable information and warning dialog used by compiled Revit commands. |

The compiled control adapter embeds the repository-local Audiowide font for
the header wordmark. Compiled windows use `KlaWindowStyle`, giving them the
same borderless dark chrome and shared palette while preserving their own
host-specific bindings and event handlers.

### Compiled WPF Windows

| Window | XAML path | Invoked by | Size | Gallery status |
| --- | --- | --- | --- | --- |
| KL&A compiled alert | `src/KLCode.Wpf/Views/KlaAlertWindow.xaml` | Family Studio and Startup Importer commands | `440 x 300` | Catalog only; requires the compiled Revit host. |
| Family Studio | `src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/FamilyStudioWindow.xaml` | `KLCode.FamilyStudio.Revit.Commands.FamilyStudioCommand` | `1180 x 740` | Catalog only; requires the compiled Revit host. |
| Startup Importer source picker | `src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/Views/StartupSourcePickerWindow.xaml` | `KLA.ModelStartupImporter.Revit.StartupImportCommand` | `560 x 470` | Catalog only; requires the compiled Revit host. |
| Startup Importer review | `src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/Views/StartupImportReviewWindow.xaml` | `KLA.ModelStartupImporter.Revit.StartupImportCommand` | `860 x 640` | Catalog only; requires the compiled Revit host. |
| Startup Importer blocking issues | `src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.UI/Views/BlockingIssuesWindow.xaml` | `KLA.ModelStartupImporter.Revit.StartupImportCommand` | `560 x 520` | Catalog only; requires the compiled Revit host. |

## Windows

**Canonical example:** `lib/GUI/_templates/KLCodeMainTemplate.xaml` is the
visual source for KL&A custom-window styling. Its outlined wordmark, 24 px
borderless header, compact close button, palette, controls, and hover states
are shared through `lib/GUI/Resources/WPF_styles.xaml`. `SelectFromDict.xaml`
remains the production list-selection implementation.

The following 10 user-facing KL&A custom windows use the template header
treatment: five shared GUI windows, Match Properties Recall, View Range, the
two Core Find and Replace windows, and Steel PSF. The two former shared rename
forms remain as legacy gallery previews. The DevSandbox UI Gallery and its
preview fixture are tooling exceptions and are not part of this visual
standardization scope.

### Shared GUI Windows

| Window | XAML path | Loader path | Tools |
| --- | --- | --- | --- |
| KL&A list selection | `lib/GUI/SelectFromDict.xaml` | `lib/GUI/SelectFromDict.py` | `Carbon GWP Pull.pushbutton`; `Concrete Mix Header.pushbutton`; `Create Detail Folders.pushbutton`; `Hide Revision Clouds.pushbutton`; `Highlight Changed Elements.pushbutton`; `Inspect Schedule Header.pushbutton`; `UI Gallery.pushbutton` |
| KL&A alert | `lib/GUI/CustomAlert.xaml` | `lib/GUI/CustomAlert.py` | `UI Gallery.pushbutton` |
| Find and replace | `lib/GUI/FindReplace.xaml` | `lib/GUI/FindReplace.py` | `UI Gallery.pushbutton` |
| Duplicate sheets | `lib/GUI/DuplicateSheets.xaml` | `lib/GUI/DuplicateSheets.py` | `duplicate_sheets.pushbutton`; `UI Gallery.pushbutton` |
| Create from rooms | `lib/GUI/Tools/CreateFromRooms.xaml` | `lib/GUI/Tools/CreateFromRooms.py` | `UI Gallery.pushbutton` |

### Core Rename Windows And Legacy Previews

| Window | XAML path | Loader path | Tools |
| --- | --- | --- | --- |
| Find and replace views | `KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton/Script.xaml` | Same bundle `script.py` | `FindReplace - Views.pushbutton`; `UI Gallery.pushbutton` |
| Find and replace sheets | `KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton/Script.xaml` | Same bundle `script.py` | `FindReplace_Sheets.pushbutton`; `UI Gallery.pushbutton` |
| Legacy view rename form | `lib/GUI/RenameViews.xaml` | `lib/Renaming/BaseClass_FindReplace.py` default loader | `UI Gallery.pushbutton` legacy preview |
| Legacy sheet rename form | `lib/GUI/RenameSheets.xaml` | `lib/GUI/RenameSheets.py` | `UI Gallery.pushbutton` legacy preview |

### One-Off Windows

| Window | XAML path | Loader path | Tools | Reason to remain outside `lib/GUI` |
| --- | --- | --- | --- | --- |
| Match properties recall | `lib/match/clipboard_window.xaml` | `lib/match/clipboard.py` | `UI Gallery.pushbutton` | A modeless content host coupled to the Match Properties workflow and its localized clipboard content. It uses the shared palette but is not a reusable dialog family. |
| View range editor | `KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml` | `KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py` | `ViewRange.pushbutton`; `UI Gallery.pushbutton` | A command-specific, data-bound editor that uses KLCode design tokens locally while keeping pyRevit's command-window loader, bindings, and events. |

### Prototype Windows

| Window | XAML path | Loader path | Tools |
| --- | --- | --- | --- |
| Steel PSF story selection | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml` | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/script.py` | `Steel PSF.pushbutton`; `UI Gallery.pushbutton` |
| UI Gallery | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml` | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py` | `UI Gallery.pushbutton` |
| UI Gallery preview fixture | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml` | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py` | `UI Gallery.pushbutton` |

## UI Gallery source review

The DevSandbox UI Gallery records 20 repository `Window` XAML surfaces: the
14 pyRevit/DevSandbox windows below, the separate main-template preview, and
the five compiled WPF windows cataloged above. The compiled entries require
their Revit host and cannot launch in the IronPython gallery. Standard pyRevit
dialogs are external references, not repository XAML surfaces.

The linked source audit describes 2026-10-08; the rename rows below were
updated for the 2026-10-09 Core promotion. This table does not
establish rendered appearance, keyboard behavior, DPI behavior, or live Revit
acceptance. See the [dated design-system review](docs/reviews/design-system/2026-10-08-current-state-review.md#ui-gallery-theme-audit)
for the full audit, drift notes, and recommended actions.

| Window | Current source status | Detail |
| --- | --- | --- |
| Create from rooms | Shared styles with a local list override | [Audit](docs/reviews/design-system/2026-10-08-current-state-review.md#ui-gallery-theme-audit) |
| KL&A alert | Shared KLCode styles | [Audit](docs/reviews/design-system/2026-10-08-current-state-review.md#ui-gallery-theme-audit) |
| Duplicate sheets | Shared styles with a local checkbox override | [Audit](docs/reviews/design-system/2026-10-08-current-state-review.md#ui-gallery-theme-audit) |
| Find and replace | Shared KLCode styles | [Audit](docs/reviews/design-system/2026-10-08-current-state-review.md#ui-gallery-theme-audit) |
| Find and replace sheets | Promoted Core dialog with shared KLCode styles and a local result panel | [Promotion record](docs/reviews/2026-10-08/find-replace-promotion.md) |
| Legacy sheet rename form | Prior shared presentation retained for historical preview | [Source audit](docs/reviews/design-system/2026-10-08-current-state-review.md#ui-gallery-theme-audit) |
| Find and replace views | Promoted Core dialog with shared KLCode styles and a local result panel | [Promotion record](docs/reviews/2026-10-08/find-replace-promotion.md) |
| Legacy view rename form | Prior shared presentation retained for historical preview | [Source audit](docs/reviews/design-system/2026-10-08-current-state-review.md#ui-gallery-theme-audit) |
| Match properties recall | Shared styles; Gallery preview omits the production chrome | [Audit](docs/reviews/design-system/2026-10-08-current-state-review.md#ui-gallery-theme-audit) |
| KL&A list selection | Production reference for shared list-selection styling | [Audit](docs/reviews/design-system/2026-10-08-current-state-review.md#ui-gallery-theme-audit) |
| Steel PSF story selection | Shared styles in a DevSandbox selector | [Audit](docs/reviews/design-system/2026-10-08-current-state-review.md#ui-gallery-theme-audit) |
| View range editor | Command-local dark resources and ComboBox templates | [Audit](docs/reviews/design-system/2026-10-08-current-state-review.md#ui-gallery-theme-audit) |
| UI Gallery | Command-local palette and DataGrid styles | [Audit](docs/reviews/design-system/2026-10-08-current-state-review.md#ui-gallery-theme-audit) |
| UI Gallery preview fixture | Minimal test fixture without shared KLCode chrome | [Audit](docs/reviews/design-system/2026-10-08-current-state-review.md#ui-gallery-theme-audit) |

## Style Loading And Local GUI Overrides

The visual baseline is `lib/GUI/_templates/KLCodeMainTemplate.xaml`: a `432 x 576` list-selection window with a 24 px borderless header, 86 px edge columns, a `70 x 12` outlined wordmark, a centered title spanning all three columns, and `KLCodeCloseButton`. It also defines the search-icon/filter-shell pattern used by the list-selection variants. `SelectFromDict.xaml` is the production implementation of that pattern.

### Windows that load shared properties without local resource copies

These loaders call `my_WPF.add_wpf_resource()` before `wpf.LoadComponent()`. Their XAML consumes `WPF_styles.xaml` directly and has no local resource dictionary; local layout and workflow content remain deliberate window-level differences.

| Window | XAML path | Loader path |
| --- | --- | --- |
| KL&A list selection | `lib/GUI/SelectFromDict.xaml` | `lib/GUI/SelectFromDict.py` |
| KL&A alert | `lib/GUI/CustomAlert.xaml` | `lib/GUI/CustomAlert.py` |
| Find and replace | `lib/GUI/FindReplace.xaml` | `lib/GUI/FindReplace.py` |
| Find and replace views | `KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace - Views.pushbutton/Script.xaml` | Same bundle `script.py` |
| Find and replace sheets | `KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton/Script.xaml` | Same bundle `script.py` |
| Legacy view rename form | `lib/GUI/RenameViews.xaml` | `lib/Renaming/BaseClass_FindReplace.py` default loader |
| Legacy sheet rename form | `lib/GUI/RenameSheets.xaml` | `lib/GUI/RenameSheets.py` |
| Match properties recall | `lib/match/clipboard_window.xaml` | `lib/match/clipboard.py` |
| Steel PSF story selection | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml` | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/script.py` |

### Local GUI Overrides

These entries are not pure shared-style consumers. Some define local resources at window or nested-control scope; the preview fixture has no shared-style dependency.

| Window | XAML path | Local implementation | Reason |
| --- | --- | --- | --- |
| View range editor | `KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml` | Defines a full local palette and dark `ComboBox`/`ComboBoxItem` templates. Its Python loader retrieves only `KLCodeWordmark` from `WPF_styles.xaml` after `forms.WPFWindow` loads the XAML. | It stays on `forms.WPFWindow`; the selector template prevents Revit from falling back to native light WPF surfaces. |
| Duplicate sheets | `lib/GUI/DuplicateSheets.xaml` | Nested `Grid.Resources` adds a checkbox style based on the shared checkbox style. | Its option grid needs local spacing, font, and alignment without replacing the shared checkbox template. |
| Create from rooms | `lib/GUI/Tools/CreateFromRooms.xaml` | Nested `ListBox.Resources` overrides the scrollbar track colors and list border radius. | Its selection list retains command-specific styling on top of the shared dictionary. |
| UI Gallery | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml` | Independent local palette and `DataGrid` styles; it does not merge `WPF_styles.xaml`. | DevSandbox catalog tooling has table-specific styling not yet shared by another window. |
| UI Gallery preview fixture | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml` | No shared dictionary or KLCode header treatment. | A deliberately minimal preview/test fixture. |

Future user-facing KL&A custom dialogs should start from `KLCodeMainTemplate.xaml` and use `WPF_styles.xaml`. Keep a local resource scope only for a documented command-specific control template or an isolated prototype; promote it into the shared dictionary when a second reusable window needs the same behavior.
