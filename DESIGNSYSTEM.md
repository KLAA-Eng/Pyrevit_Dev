# KLCode pyRevit Design System

This file records the default visual properties used by the KLCode pyRevit extension.

## Ribbon Icons

Default ribbon command icons are transparent-background PNGs with a single visible foreground color.

| Theme | File | Foreground | Plain English Color |
| --- | --- | --- | --- |
| Light | `icon.png` | `#34495E` | dark blue-gray |
| Dark | `icon.dark.png` | `#EBEBEB` | light gray |

For new or refreshed Core Tools icons, recolor every non-transparent pixel to the theme foreground while preserving each pixel's alpha channel.

## Shared GUI Colors

Shared WPF GUI styling is defined in `lib/GUI/Resources/WPF_styles.xaml`.

| Token | Value | Plain English Color |
| --- | --- | --- |
| `header_background` | `#0F0F2D` | very dark navy |
| `text_white` | `#E5E4E2` | warm off-white |
| `text_gray` | `Gray` | medium gray |
| `text_magenta` | `#6FA287` | muted green |
| `button_fg_normal` | `White` | white |
| `button_bg_normal` | `#39385D` | muted indigo |
| `button_bg_hover` | `#4C9566` | medium green |
| `border_magenta` | `#3F7F57` | deep green |
| `border_blue` | `#6FA287` | muted green |
| `uncheckbox_checked_colour` | `Gray` | medium gray |
| `checkbox_checked_colour` | `#3F7F57` | deep green |
| `footer_donate` | `#4C9566` | medium green |

## Shared GUI Properties

| Control | Property | Value | Plain English Color |
| --- | --- | --- | --- |
| `Button` | `TextElement.FontFamily` | `Arial` | N/A |
| `Button` | `Background` | `button_bg_normal` | muted indigo |
| `Button` | `Foreground` | `button_fg_normal` | white |
| `Button` | `Cursor` | `Hand` | N/A |
| `Button` | `CornerRadius` | `8` | N/A |
| `Button` | hover `Background` | `button_bg_hover` | medium green |
| `TextBlock` | `Foreground` | `text_white` | warm off-white |
| `TextBox` | `Background` | `header_background` | very dark navy |
| `TextBox` | `Foreground` | `text_magenta` | muted green |
| `TextBox` | `BorderBrush` | `border_blue` | muted green |
| `TextBox` | `VerticalContentAlignment` | `Center` | N/A |
| `TextBox` | border `CornerRadius` | `5` | N/A |
| `Border` | `BorderThickness` | `1` | N/A |
| `Border` | `CornerRadius` | `10` | N/A |
| `Label` | `Foreground` | `text_magenta` | muted green |
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
| `ComboBox` | editable text `Foreground` | `#7FB38F` | soft green |
| `ComboBoxItem` | `Foreground` | `White` | white |
| `ComboBoxItem` | highlighted background | `#FF4F4F4F` | charcoal gray |
| `ListBox` | `Background` | `header_background` | very dark navy |
| `ListBox` | `BorderBrush` | `border_magenta` | deep green |
| `ListBox` | vertical scrollbar | `Visible` | N/A |
| `ListBox` | horizontal scrollbar | `Hidden` | N/A |
| `ListBox` | border `CornerRadius` | `10` | N/A |
| `ScrollBar` | `Background` | `border_magenta` | deep green |
| `ScrollBar` | `Foreground` | `border_magenta` | deep green |
| `ScrollBar` | `BorderBrush` | `header_background` | very dark navy |
| `ScrollBar` | `Opacity` | `0.9` | N/A |
| `ScrollBar` | `Margin` | `3` | N/A |
| `ScrollBar` | track `CornerRadius` | `10` | N/A |
| `ScrollBarThumbVertical` | `Background` | `Black` | black |
| `ScrollBarThumbVertical` | `CornerRadius` | `8` | N/A |

## Window Defaults Observed

The shared GUI windows follow these conventions where present:

| Property | Value | Plain English Color |
| --- | --- | --- |
| `WindowStartupLocation` | `CenterScreen` | N/A |
| `HorizontalAlignment` | `Center` | N/A |
| `WindowStyle` | `None` | N/A |
| `ResizeMode` | `NoResize` for fixed dialogs | N/A |
| Header row height | `25` | N/A |
| Header background | `header_background` | very dark navy |
| Close button size | `60 x 20` | N/A |

Known window backgrounds currently in use:

| Window | Background | Plain English Color |
| --- | --- | --- |
| `lib/GUI/FindReplace.xaml` | `#181735` | very dark indigo |
| `lib/GUI/SelectFromDict.xaml` | `#080326` with a `#332E5C40` to `#336FA287` gradient grid background | very dark navy with translucent purple and green gradient |

## Local GUI Overrides

`KL&A Tools_dev.tab/03 Core Tools.panel/duplicate_sheets.pushbutton/Script.xaml` defines command-local GUI resources instead of using only the shared style dictionary. Its local colors include:

| Token | Value | Plain English Color |
| --- | --- | --- |
| `header_background` | `#0F0F2D` | very dark navy |
| `main_background` | `Aqua` | bright cyan |
| `checkbox_checked_colour` | `#FE6584` | bright pink |
| `checkbox_unchecked_colour` | `Aqua` | bright cyan |
| `text_header_title` | `White` | white |
| `text_header_item` | `White` | white |
| `text_white` | `White` | white |
| `text_darkblue` | `#383660` | muted indigo |
| `text_red` | `#FE6584` | bright pink |
| `text_magenta` | `#EE82EE` | violet |
| `input_box_darkblue` | `#383660` | muted indigo |
| `border_main` | `DodgerBlue` | bright blue |
| `border_secondary` | `#EE82EE` | violet |
| `button_01_background_normal` | `#EE82EE` | violet |
| `button_01_background_hover` | `#EE82EE` | violet |
