# KLCode pyRevit Design System

This file records the default visual properties used by the KLCode pyRevit extension.

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

`lib/_logos/KLCodeLogo.png` is the source branding asset used to sample the primary charcoal and green colors.

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

Shared WPF GUI styling is defined in `lib/GUI/Resources/WPF_styles.xaml`.

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
| `ComboBox` | arrow | `Fill` | `text_white` | KLWhite |
| `ComboBox` | disabled selector body | `Background` | `#FF131313` | KLCharcoal-black |
| `ComboBox` | disabled arrow | `Fill` | `text_gray` | gray |
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
| `ComboBox` | local dark template key | `x:Key` | `ComboBoxToggleButton` |
| `ComboBox` | editable text host key | `x:Key` | `ComboBoxTextBox` |
| `ComboBoxItem` | item template padding | `Padding` | `4,3` |
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

## Windows

**Canonical example:** `lib/GUI/_templates/KLCodeMainTemplate.xaml` is the
visual source for KL&A custom-window styling. Its outlined wordmark, 24 px
borderless header, compact close button, palette, controls, and hover states
are shared through `lib/GUI/Resources/WPF_styles.xaml`. `SelectFromDict.xaml`
remains the production list-selection implementation.

The following 12 user-facing KL&A custom windows use the template header
treatment: the seven Shared GUI Windows, Match Properties Recall, View Range,
the two Find and Replace prototypes, and Steel PSF. The DevSandbox UI Gallery
and its preview fixture are tooling exceptions and are not part of this visual
standardization scope.

### Shared GUI Windows

| Window | XAML path | Loader path | Tools |
| --- | --- | --- | --- |
| KL&A list selection | `lib/GUI/SelectFromDict.xaml` | `lib/GUI/SelectFromDict.py` | `Carbon GWP Pull.pushbutton`; `Concrete Mix Header.pushbutton`; `Create Detail Folders.pushbutton`; `Hide Revision Clouds.pushbutton`; `Highlight Changed Elements.pushbutton`; `Inspect Schedule Header.pushbutton`; `UI Gallery.pushbutton` |
| KL&A alert | `lib/GUI/CustomAlert.xaml` | `lib/GUI/CustomAlert.py` | `UI Gallery.pushbutton` |
| Find and replace | `lib/GUI/FindReplace.xaml` | `lib/GUI/FindReplace.py` | `UI Gallery.pushbutton` |
| Find and replace views | `lib/GUI/RenameViews.xaml` | `lib/Renaming/BaseClass_FindReplace.py` | `FindReplace - Views.pushbutton`; `UI Gallery.pushbutton` |
| Find and replace sheets | `lib/GUI/RenameSheets.xaml` | `lib/GUI/RenameSheets.py` | `FindReplace_Sheets.pushbutton`; `UI Gallery.pushbutton` |
| Duplicate sheets | `lib/GUI/DuplicateSheets.xaml` | `lib/GUI/DuplicateSheets.py` | `duplicate_sheets.pushbutton`; `UI Gallery.pushbutton` |
| Create from rooms | `lib/GUI/Tools/CreateFromRooms.xaml` | `lib/GUI/Tools/CreateFromRooms.py` | `UI Gallery.pushbutton` |

### One-Off Windows

| Window | XAML path | Loader path | Tools | Reason to remain outside `lib/GUI` |
| --- | --- | --- | --- | --- |
| Match properties recall | `lib/match/clipboard_window.xaml` | `lib/match/clipboard.py` | `UI Gallery.pushbutton` | A modeless content host coupled to the Match Properties workflow and its localized clipboard content. It uses the shared palette but is not a reusable dialog family. |
| View range editor | `KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml` | `KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/script.py` | `ViewRange.pushbutton`; `UI Gallery.pushbutton` | A command-specific, data-bound editor that uses KLCode design tokens locally while keeping pyRevit's command-window loader, bindings, and events. |

### Prototype Windows

| Window | XAML path | Loader path | Tools |
| --- | --- | --- | --- |
| Find and replace views | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/Script.xaml` | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/script.py` | `FindReplace - Views-proto.pushbutton`; `UI Gallery.pushbutton` |
| Find and replace sheets | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/Script.xaml` | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/script.py` | `FindReplace_Sheets-proto.pushbutton`; `UI Gallery.pushbutton` |
| Steel PSF story selection | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml` | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/script.py` | `Steel PSF.pushbutton`; `UI Gallery.pushbutton` |
| UI Gallery | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml` | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py` | `UI Gallery.pushbutton` |
| UI Gallery preview fixture | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml` | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/script.py` | `UI Gallery.pushbutton` |

## UI Gallery Theme Audit

The DevSandbox UI Gallery catalogs representative KL&A custom, DevSandbox, and standard pyRevit windows in `lib/ui_gallery/launchers.py`. For the 12 user-facing KL&A custom windows, use `lib/GUI/_templates/KLCodeMainTemplate.xaml` as the visual reference: borderless dark chrome, the outlined KLCode wordmark in the 24 px header, KLCharcoal window background, KLGreen-dark/KLGreen/KLGreen-secondary accents, and readable KLWhite text. The template is also a separate gallery preview entry, not a thirteenth user-facing window.

Standard pyRevit gallery entries, the UI Gallery shell, and its preview fixture are intentional tooling/external references and are not scored for KLCode theme consistency.

Audit scope: all 14 window XAML files listed in the Shared GUI Windows, One-Off Windows, and Prototype Windows tables above. Each is represented once below.

| Gallery title | Category | XAML path | Theme status | Notable drift | Recommended future action |
| --- | --- | --- | --- | --- | --- |
| Create from rooms | KL&A custom | `lib/GUI/Tools/CreateFromRooms.xaml` | Reference/aligned with local list override | Loads shared styles through `my_WPF`, uses a solid KLCharcoal window background, and locally overrides its `ListBox`/scrollbar resources. | Keep layout and behavior; update shared control values in `WPF_styles.xaml`, then retain only its list-specific override. |
| KL&A alert | KL&A custom | `lib/GUI/CustomAlert.xaml` | Reference/aligned | Alert-specific icon, heading, and OK button are preserved inside SelectFromDict-style dark chrome. | Keep aligned with the shared palette when alert states are expanded. |
| Duplicate sheets | KL&A custom | `lib/GUI/DuplicateSheets.xaml` | Reference/aligned with local checkbox override | Large command-specific form uses shared styles whose resource keys map to the named design tokens, plus a nested checkbox style for its option grid. | Keep command handlers in the bundle and presentation in `lib/GUI`. |
| Find and replace | KL&A custom | `lib/GUI/FindReplace.xaml` | Reference/aligned | Compact rename form uses the solid KLCharcoal header/body and shared KLCode resources. | Keep as a compact aligned variant. |
| Find and replace sheets | KL&A custom | `lib/GUI/RenameSheets.xaml` | Reference/aligned | Production sheet rename presentation loads the shared dictionary; command behavior remains in its bundle. | Keep handlers and Revit transactions in the command bundle. |
| Find and replace sheets prototype | KL&A custom | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/Script.xaml` | Explicit prototype exception | Prototype behavior remains isolated, but its XAML now consumes the shared dictionary directly. | Promote deliberate behavior changes into `lib/GUI/RenameSheets.xaml`; do not sync opportunistically. |
| Find and replace views | KL&A custom | `lib/GUI/RenameViews.xaml` | Reference/aligned | Shared rename base now loads `WPF_styles.xaml` through `my_WPF`. | Keep production view rename presentation in `lib/GUI`. |
| Find and replace views prototype | KL&A custom | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/Script.xaml` | Explicit prototype exception | Prototype behavior remains isolated, but its XAML now consumes the shared dictionary directly. | Promote deliberate behavior changes into `lib/GUI/RenameViews.xaml`; do not sync opportunistically. |
| Match properties recall | KL&A custom | `lib/match/clipboard_window.xaml` | Reference/aligned | Modeless clipboard content is hosted inside SelectFromDict-style dark chrome and loads the shared palette directly. | Keep the content host pattern so command content does not replace the KLCode shell. |
| KL&A list selection | KL&A custom | `lib/GUI/SelectFromDict.xaml` | Reference/aligned | This is the reference theme for list-selection windows. | Keep as the base for future selection-style custom windows. |
| Steel PSF story selection | KL&A custom | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml` | Reference/aligned | Closely follows SelectFromDict list-selection chrome with a solid KLCharcoal background; footer is prototype-specific. | Keep aligned with SelectFromDict when Steel PSF controls change. |
| View range editor | KL&A custom | `KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml` | Reference/aligned with local dictionary | Uses SelectFromDict-style dark chrome and local KLCode token resources while preserving pyRevit's `forms.WPFWindow` loading path for this command-specific editor. Python applies the shared `KLCodeWordmark` template after XAML loading. The Associated Level selectors use a full local dark `ComboBox`/`ComboBoxItem` template so the selector body and popup do not fall back to native light WPF styling. | Keep command-specific behavior in the bundle; promote only reusable styles into `WPF_styles.xaml` when another command needs them. |
| UI Gallery | DevSandbox | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml` | Reference/aligned | Uses SelectFromDict-style dark chrome, local KLCode token resources, and a KLCharcoal/KLGreen dark DataGrid treatment for catalog rows. | Keep gallery-only DataGrid styling local unless another KLCode table view adopts the same pattern. |
| UI Gallery preview fixture | DevSandbox | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml` | Needs future theming | Uses a KLCharcoal window background but remains an intentionally minimal fixture with default WPF chrome and text styling. | Leave plain unless the fixture is promoted to a visual-review artifact; document it as a test exception if unchanged. |

## Style Loading And Local GUI Overrides

The visual baseline is `lib/GUI/_templates/KLCodeMainTemplate.xaml`: a `432 x 576` list-selection window with a 24 px borderless header, 86 px edge columns, a `70 x 12` outlined wordmark, a centered title spanning all three columns, and `KLCodeCloseButton`. It also defines the search-icon/filter-shell pattern used by the list-selection variants. `SelectFromDict.xaml` is the production implementation of that pattern.

### Windows that load shared properties without local resource copies

These loaders call `my_WPF.add_wpf_resource()` before `wpf.LoadComponent()`. Their XAML consumes `WPF_styles.xaml` directly and has no local resource dictionary; local layout and workflow content remain deliberate window-level differences.

| Window | XAML path | Loader path |
| --- | --- | --- |
| KL&A list selection | `lib/GUI/SelectFromDict.xaml` | `lib/GUI/SelectFromDict.py` |
| KL&A alert | `lib/GUI/CustomAlert.xaml` | `lib/GUI/CustomAlert.py` |
| Find and replace | `lib/GUI/FindReplace.xaml` | `lib/GUI/FindReplace.py` |
| Find and replace views | `lib/GUI/RenameViews.xaml` | `lib/Renaming/BaseClass_FindReplace.py` |
| Find and replace sheets | `lib/GUI/RenameSheets.xaml` | `lib/GUI/RenameSheets.py` |
| Match properties recall | `lib/match/clipboard_window.xaml` | `lib/match/clipboard.py` |
| Steel PSF story selection | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml` | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/script.py` |
| Find and replace views prototype | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/Script.xaml` | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/script.py` |
| Find and replace sheets prototype | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/Script.xaml` | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/script.py` |

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
