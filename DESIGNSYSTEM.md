# KLCode pyRevit Design System

This file records the default visual properties used by the KLCode pyRevit extension.

## Logo Asset

`KLCodeLogo.png` at the repository root is the source KLCode logo asset.

| Property | Value |
| --- | --- |
| Dimensions | `1052 x 576` |
| Format | transparent PNG, `Format32bppArgb` |
| Primary background sample | `#1A252B` |
| Primary green sample | `#33714F` |
| Dark green sample | `#286048` |
| Secondary green sample | `#407058` |

The logo is a wide wordmark/banner with a dark blue-green background, white `KLC` lettering, green accent mark, and green/gray pixel motif. Do not place this wide source asset directly into the standard 25 px GUI headers; create a cropped or header-safe logo variant before replacing the current text branding.

## Ribbon Icons

Default ribbon command icons are transparent-background PNGs with a single visible foreground color.

Create standard ribbon icons as square `32 x 32 px` PNGs at `96 DPI`. This is
the native large-ribbon size used by Revit; pyRevit scales the asset for
smaller controls (including 16 px stacked buttons and the Quick Access
Toolbar). Keep source assets at or below `96 x 96 px`, since pyRevit warns that
larger icons increase ribbon load time.

  - 16 × 16 — stacked/small controls and Quick Access Toolbar
  - 24 × 24 — medium pyRevit use
  - 32 × 32 — normal large ribbon buttons
  - 96 × 96 — max icon size

| Theme | File | Foreground | Plain English Color |
| --- | --- | --- | --- |
| Light | `icon.png` | `#34495E` | dark blue-gray |
| Dark | `icon.dark.png` | `#EBEBEB` | light gray |
| Default orange | `lib/_icons/square_96px_orange.png` | `#FF8000` | KLCode orange |
| Default green | `lib/_icons/square_96px_green.png` | `#33714F` | logo green |

### Icon Design Reference

[Lucide Icons](https://lucide.dev/icons/) is the visual reference for new and
refreshed ribbon icons. Use its simple, consistent icon language as design
inspiration while creating the required pyRevit PNG assets described above.

## Shared GUI Colors

Shared WPF GUI styling is defined in `lib/GUI/Resources/WPF_styles.xaml`.

| Token | Value | Plain English Color |
| --- | --- | --- |
| `header_background` | `#1A252B` | logo charcoal |
| `text_white` | `#E5E4E2` | warm off-white |
| `text_gray` | `Gray` | medium gray |
| `text_magenta` | `#33714F` | logo green |
| `button_fg_normal` | `White` | white |
| `button_bg_normal` | `#286048` | dark logo green |
| `button_bg_hover` | `#407058` | secondary logo green |
| `border_magenta` | `#286048` | dark logo green |
| `border_blue` | `#33714F` | logo green |
| `uncheckbox_checked_colour` | `Gray` | medium gray |
| `checkbox_checked_colour` | `#286048` | dark logo green |
| `footer_donate` | `#407058` | secondary logo green |

The charcoal and green values are sampled from `KLCodeLogo.png`. `#E5E4E2`, `White`, and `Gray` are retained for contrast and existing text readability.

## Shared GUI Properties

| Control | Property | Value | Plain English Color |
| --- | --- | --- | --- |
| `Button` | `TextElement.FontFamily` | `Arial` | N/A |
| `Button` | `Background` | `button_bg_normal` | dark logo green |
| `Button` | `Foreground` | `button_fg_normal` | white |
| `Button` | `Cursor` | `Hand` | N/A |
| `Button` | `CornerRadius` | `8` | N/A |
| `Button` | hover `Background` | `button_bg_hover` | secondary logo green |
| `TextBlock` | `Foreground` | `text_white` | warm off-white |
| `TextBox` | `Background` | `header_background` | logo charcoal |
| `TextBox` | `Foreground` | `text_magenta` | logo green |
| `TextBox` | `BorderBrush` | `border_blue` | logo green |
| `TextBox` | `VerticalContentAlignment` | `Center` | N/A |
| `TextBox` | border `CornerRadius` | `5` | N/A |
| `Border` | `BorderThickness` | `1` | N/A |
| `Border` | `CornerRadius` | `10` | N/A |
| `Label` | `Foreground` | `text_magenta` | logo green |
| `CheckBox` | `Foreground` | `White` | white |
| `CheckBox` | checkbox size | `15 x 15` | N/A |
| `CheckBox` | checkbox `CornerRadius` | `2` | N/A |
| `CheckBox` | checkmark stroke | `#E5E4E2` | warm off-white |
| `CheckBox` | hover background | `#FF131313` | near black |
| `DockPanel` | `Margin` | `2` | N/A |
| `ComboBox` | `MinWidth` | `120` | N/A |
| `ComboBox` | `MinHeight` | `20` | N/A |
| `ComboBox` | `Foreground` | `White` | white |
| `ComboBox` | editable text `Background` | `#FF3F3F3F` | dark gray |
| `ComboBox` | editable text `Foreground` | `#E5E4E2` | warm off-white |
| `ComboBoxItem` | `Foreground` | `White` | white |
| `ComboBoxItem` | highlighted background | `#FF4F4F4F` | charcoal gray |
| `ListBox` | `Background` | `header_background` | logo charcoal |
| `ListBox` | `BorderBrush` | `border_magenta` | dark logo green |
| `ListBox` | vertical scrollbar | `Visible` | N/A |
| `ListBox` | horizontal scrollbar | `Hidden` | N/A |
| `ListBox` | border `CornerRadius` | `10` | N/A |
| `ScrollBar` | `Background` | `border_magenta` | dark logo green |
| `ScrollBar` | `Foreground` | `border_magenta` | dark logo green |
| `ScrollBar` | `BorderBrush` | `header_background` | logo charcoal |
| `ScrollBar` | `Opacity` | `0.9` | N/A |
| `ScrollBar` | `Margin` | `3` | N/A |
| `ScrollBar` | track `CornerRadius` | `10` | N/A |
| `ScrollBarThumbVertical` | `Background` | `Black` | black |
| `ScrollBarThumbVertical` | `CornerRadius` | `8` | N/A |

Selection-style branded windows, including `SelectFromDict` and the `CreateFromRooms` copy, use `text_white` for the filter magnifier icon, filter input text, and selection prompt label. Borders and separators remain on the logo-green accent colors so labels such as `Select stories to review:` stay readable against the dark logo-charcoal background.

## Window Defaults Observed

The shared GUI windows follow these conventions where present:

| Property | Value | Plain English Color |
| --- | --- | --- |
| `WindowStartupLocation` | `CenterScreen` | N/A |
| `HorizontalAlignment` | `Center` | N/A |
| `WindowStyle` | `None` | N/A |
| `ResizeMode` | `NoResize` for fixed dialogs | N/A |
| Header row height | `25` | N/A |
| Header background | `header_background` | logo charcoal |
| Close button size | `60 x 20` | N/A |

Known window backgrounds currently in use:

| Window | Background | Plain English Color |
| --- | --- | --- |
| `lib/GUI/FindReplace.xaml` | `#1A252B` | logo charcoal |
| `lib/GUI/SelectFromDict.xaml` | `#1A252B` with a `#33286048` to `#33307050` gradient grid background | logo charcoal with translucent logo-green gradient |

## UI Gallery Theme Audit

The DevSandbox UI Gallery catalogs representative custom windows in `lib/ui_gallery/launchers.py`. For KL&A custom and DevSandbox entries, use `lib/GUI/SelectFromDict.xaml` as the visual reference: borderless dark chrome, KLCode text branding in the 25 px header, `#1A252B` charcoal window background, optional translucent logo-green gradient, `#286048`/`#33714F`/`#407058` accents, and readable `#E5E4E2` text.

Standard pyRevit gallery entries are intentional external references and are not scored for KLCode theme consistency.

| Gallery title | Category | XAML path | Theme status | Notable drift | Recommended future action |
| --- | --- | --- | --- | --- | --- |
| Create from rooms | KL&A custom | `lib/GUI/Tools/CreateFromRooms.xaml` | Reference/aligned | Local copy of the shared palette; checkbox gradient now matches the shared SelectFromDict values. | Keep layout and behavior; sync copied resource values with the shared dictionary when this local copy is refreshed. |
| KL&A alert | KL&A custom | `lib/GUI/CustomAlert.xaml` | Reference/aligned | Alert-specific icon, heading, and OK button are preserved inside SelectFromDict-style dark chrome. | Keep aligned with the shared palette when alert states are expanded. |
| Duplicate sheets | KL&A custom | `KL&A Tools_dev.tab/03 Core Tools.panel/duplicate_sheets.pushbutton/Script.xaml` | Mostly aligned with local overrides | Uses command-local aliases that match the shared palette, but has a larger tool-specific form and custom token names. | Keep local aliases documented; only normalize token naming if the window is later refactored. |
| Find and replace | KL&A custom | `lib/GUI/FindReplace.xaml` | Reference/aligned | Compact rename form uses the charcoal header/body and shared KLCode resources; it does not use the SelectFromDict list gradient because it is not a selection window. | Keep as a compact aligned variant. |
| Find and replace sheets | KL&A custom | `KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton/Script.xaml` | Mostly aligned with local overrides | Uses copied KLCode resources and command-specific fields; verify copied values before future palette changes. | Keep behavior; update copied resources only when syncing all rename windows. |
| Find and replace sheets prototype | KL&A custom | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/Script.xaml` | Mostly aligned with local overrides | Prototype copy follows the KLCode layout but may contain local resource drift from production copies. | Keep prototype-local XAML; sync palette deliberately when production rename windows are refreshed. |
| Find and replace views | KL&A custom | `lib/Renaming/GUI_BaseRename.xaml` | Mostly aligned with local overrides | Shared rename base uses the KLCode header and footer but carries an embedded resource dictionary instead of relying only on `WPF_styles.xaml`. | Preserve as the rename base; consider dictionary deduplication only in a separate refactor. |
| Find and replace views prototype | KL&A custom | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/Script.xaml` | Mostly aligned with local overrides | Prototype-local copy intentionally avoids changing shared rename GUI behavior. | Keep prototype-local XAML and sync palette only when the prototype is intentionally refreshed. |
| Match properties recall | KL&A custom | `lib/match/clipboard_window.xaml` | Reference/aligned | Modeless clipboard content is hosted inside SelectFromDict-style dark chrome. | Keep the content host pattern so command content does not replace the KLCode shell. |
| KL&A list selection | KL&A custom | `lib/GUI/SelectFromDict.xaml` | Reference/aligned | This is the reference theme for list-selection windows. | Keep as the base for future selection-style custom windows. |
| Steel PSF story selection | KL&A custom | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml` | Reference/aligned | Closely follows SelectFromDict list-selection chrome and gradient; footer is prototype-specific. | Keep aligned with SelectFromDict when Steel PSF controls change. |
| View range editor | KL&A custom | `KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml` | Needs future theming | Uses default resizable WPF chrome, light table rows, and red warning text instead of KLCode dark chrome. | Restyle as a KLCode tool window while preserving the editable grid and data bindings. |
| UI Gallery | DevSandbox | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml` | Needs future theming | Uses default resizable WPF chrome and unthemed DataGrid controls. | Apply KLCode header/chrome and a dark, readable gallery table in a future UI pass. |
| UI Gallery preview fixture | DevSandbox | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml` | Needs future theming | Intentionally minimal self-contained fixture with default WPF chrome. | Leave plain unless the fixture is promoted to a visual-review artifact; document it as a test exception if unchanged. |

Future KL&A custom windows should use the SelectFromDict chrome and palette by default. Exceptions must be explicit: standard pyRevit dialogs, test fixtures, and tool-specific windows may keep different chrome only when the reason is documented near the launcher or in this design system.

## Local GUI Overrides

`KL&A Tools_dev.tab/03 Core Tools.panel/duplicate_sheets.pushbutton/Script.xaml` defines command-local aliases for the shared GUI palette. The aliases below match the colors in `lib/GUI/Resources/WPF_styles.xaml`:

| Token | Value | Plain English Color |
| --- | --- | --- |
| `header_background` | `#1A252B` | logo charcoal |
| `main_background` | `#1A252B` | logo charcoal |
| `checkbox_checked_colour` | `#286048` | dark logo green |
| `uncheckbox_checked_colour` | `Gray` | medium gray |
| `text_header_title` | `#E5E4E2` | warm off-white |
| `text_header_item` | `#E5E4E2` | warm off-white |
| `text_white` | `#E5E4E2` | warm off-white |
| `text_darkblue` | `Gray` | medium gray |
| `text_red` | `#33714F` | logo green |
| `text_magenta` | `#33714F` | logo green |
| `input_box_darkblue` | `#1A252B` | logo charcoal |
| `border_main` | `#33714F` | logo green |
| `border_secondary` | `#286048` | dark logo green |
| `button_01_background_normal` | `#286048` | dark logo green |
| `button_01_background_hover` | `#407058` | secondary logo green |

The window uses the plain `header_background` color. The decorative rotated color-band grid was removed.
