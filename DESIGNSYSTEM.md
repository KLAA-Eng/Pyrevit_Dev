# KLCode pyRevit Design System

This file records the default visual properties used by the KLCode pyRevit extension.

## Logo Asset

`KLCodeLogo.png` at the repository root is the source KLCode logo asset.

| Property | Value |
| --- | --- |
| Dimensions | `1052 x 576` |
| Format | transparent PNG, `Format32bppArgb` |
| Primary background sample | `#1A252B` |
| Primary green sample | `#307050` |
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

| Theme | File | Foreground | Plain English Color |
| --- | --- | --- | --- |
| Light | `icon.png` | `#34495E` | dark blue-gray |
| Dark | `icon.dark.png` | `#EBEBEB` | light gray |

For new or refreshed Core Tools icons, recolor every non-transparent pixel to the theme foreground while preserving each pixel's alpha channel.

## Shared GUI Colors

Shared WPF GUI styling is defined in `lib/GUI/Resources/WPF_styles.xaml`.

| Token | Value | Plain English Color |
| --- | --- | --- |
| `header_background` | `#1A252B` | logo charcoal |
| `text_white` | `#E5E4E2` | warm off-white |
| `text_gray` | `Gray` | medium gray |
| `text_magenta` | `#307050` | logo green |
| `button_fg_normal` | `White` | white |
| `button_bg_normal` | `#286048` | dark logo green |
| `button_bg_hover` | `#407058` | secondary logo green |
| `border_magenta` | `#286048` | dark logo green |
| `border_blue` | `#307050` | logo green |
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
| `text_red` | `#307050` | logo green |
| `text_magenta` | `#307050` | logo green |
| `input_box_darkblue` | `#1A252B` | logo charcoal |
| `border_main` | `#307050` | logo green |
| `border_secondary` | `#286048` | dark logo green |
| `button_01_background_normal` | `#286048` | dark logo green |
| `button_01_background_hover` | `#407058` | secondary logo green |

The window uses the plain `header_background` color. The decorative rotated color-band grid was removed.
