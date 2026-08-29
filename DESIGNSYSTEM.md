# KLCode pyRevit Design System

This file records the default visual properties used by the KLCode pyRevit extension.

## Master Design Colors

These are the named colors used across KLCode ribbon icons and WPF GUIs. This table defines the color names used throughout this document; usage guidance belongs in the relevant icon and GUI sections.

| KLName | Value | Description |
| --- | --- | --- |
| KLCharcoal | `#1A252B` | Dark blue-green charcoal. |
| KLGreen | `#33714F` | Deep KLCode green. |
| KLGreen-dark | `#286048` | Dark muted green. |
| KLGreen-secondary | `#407058` | Muted medium green. |
| KLOrange | `#FF8000` | Bright orange. |
| KLWhite | `#E5E4E2` | Soft warm off-white. |
| white | `#FFFFFF` | Pure white. |
| KLGray-medium | `#808080` | Standard medium gray. |
| KLGray-dark | `#FF3F3F3F` | Dark neutral gray. |
| KLCharcoal-gray | `#FF4F4F4F` | Medium-dark charcoal gray. |
| KLGray-scroll | `#505050` | Neutral dark gray. |
| KLGray-disabled | `#888888` | Muted medium-light gray. |
| KLGray-disabled-check | `#FF6C6C6C` | Muted gray. |
| KLCharcoal-black | `#FF131313` | Nearly black charcoal. |
| black | `#000000` | Pure black. |
| KLGreen-transparent-a | `#33286048` | Transparent dark green. |
| KLGreen-transparent-b | `#33307050` | Transparent muted green. |
| KLGreen-checkbox-a | `#88286048` | Semi-transparent dark green. |
| KLGreen-checkbox-b | `#99307050` | Semi-transparent muted green. |
| warning-gold | `#DAA520` | Warm golden yellow. |
| info-green | `#3CB371` | Medium sea green. |

`lib/_logos/KLCodeLogo.png` is the source branding asset used to sample the primary charcoal and green colors.

| Property | Value |
| --- | --- |
| KLCharcoal sample | `#1A252B` |
| KLGreen sample | `#33714F` |
| KLGreen-dark sample | `#286048` |
| KLGreen-secondary sample | `#407058` |

## Icons

KLCode ribbon icons are transparent-background PNGs. Use a single foreground color unless the command clearly needs additional visual detail.

### Live Icon Conventions

| Context | File | Foreground |
| --- | --- | --- |
| Light UI | `icon.png` | `#1A252B` KLCharcoal |
| Dark UI | `icon.dark.png` | `#E5E4E2` KLWhite |

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

## Shared GUI Colors

Shared WPF GUI styling is defined in `lib/GUI/Resources/WPF_styles.xaml`.

| Token | Value | KLName |
| --- | --- | --- |
| `header_background` | `#1A252B` | KLCharcoal |
| `text_white` | `#E5E4E2` | KLWhite |
| `text_gray` | `Gray` | KLGray-medium |
| `text_magenta` | `#33714F` | KLGreen |
| `button_fg_normal` | `White` | white |
| `button_bg_normal` | `#286048` | KLGreen-dark |
| `button_bg_hover` | `#407058` | KLGreen-secondary |
| `border_magenta` | `#286048` | KLGreen-dark |
| `border_blue` | `#33714F` | KLGreen |
| `uncheckbox_checked_colour` | `Gray` | KLGray-medium |
| `checkbox_checked_colour` | `#286048` | KLGreen-dark |
| `footer_donate` | `#407058` | KLGreen-secondary |

## Shared GUI Properties

These values describe the default styles in `lib/GUI/Resources/WPF_styles.xaml`. They apply to windows that load the shared dictionary through `my_WPF.add_wpf_resource()` unless the window defines local resources with the same keys.

### Color Properties

| Control | UI part | XAML property | Implementation value | KLName |
| --- | --- | --- | --- | --- |
| `Button` | default | `Background` | `button_bg_normal` | KLGreen-dark |
| `Button` | default | `Foreground` | `button_fg_normal` | white |
| `Button` | hover state | `Background` | `button_bg_hover` | KLGreen-secondary |
| `TextBlock` | default | `Foreground` | `text_white` | KLWhite |
| `TextBox` | default | `Background` | `header_background` | KLCharcoal |
| `TextBox` | default | `Foreground` | `text_magenta` | KLGreen |
| `TextBox` | default | `BorderBrush` | `border_blue` | KLGreen |
| `Label` | default | `Foreground` | `text_magenta` | KLGreen |
| `CheckBox` | label text | `Foreground` | `White` | white |
| `CheckBox` | checkbox fill gradient start | `Background` | `#99307050` | KLGreen-checkbox-b |
| `CheckBox` | checkbox fill gradient end | `Background` | `#88286048` | KLGreen-checkbox-a |
| `CheckBox` | checkmark | `Stroke` | `#E5E4E2` | KLWhite |
| `CheckBox` | hover checkbox fill | `Background` | `#FF131313` | KLCharcoal-black |
| `ComboBox` | default | `Foreground` | `White` | white |
| `ComboBox` | editable text field | `Background` | `#FF3F3F3F` | KLGray-dark |
| `ComboBox` | editable text field | `Foreground` | `#E5E4E2` | KLWhite |
| `ComboBoxItem` | default | `Foreground` | `White` | white |
| `ComboBoxItem` | highlighted state | `Background` | `#FF4F4F4F` | KLCharcoal-gray |
| `ListBox` | default | `Background` | `header_background` | KLCharcoal |
| `ListBox` | default | `BorderBrush` | `border_magenta` | KLGreen-dark |
| `ScrollBar` | default | `Background` | `border_magenta` | KLGreen-dark |
| `ScrollBar` | default | `Foreground` | `border_magenta` | KLGreen-dark |
| `ScrollBar` | default | `BorderBrush` | `header_background` | KLCharcoal |
| `ScrollBarThumbVertical` | default | `Background` | `Black` | black |

### Layout And Behavior Properties

| Control | UI part | XAML property | Implementation value |
| --- | --- | --- | --- |
| `Button` | default | `TextElement.FontFamily` | `Arial` |
| `Button` | default | `Cursor` | `Hand` |
| `Button` | button border | `CornerRadius` | `8` |
| `TextBox` | default | `VerticalContentAlignment` | `Center` |
| `TextBox` | border style | `CornerRadius` | `5` |
| `Border` | default | `BorderThickness` | `1` |
| `Border` | default | `CornerRadius` | `10` |
| `CheckBox` | checkbox box | `Width` and `Height` | `15 x 15` |
| `CheckBox` | checkbox box | `CornerRadius` | `2` |
| `DockPanel` | default | `Margin` | `2` |
| `ComboBox` | default | `MinWidth` | `120` |
| `ComboBox` | default | `MinHeight` | `20` |
| `ListBox` | default | `ScrollViewer.VerticalScrollBarVisibility` | `Visible` |
| `ListBox` | default | `ScrollViewer.HorizontalScrollBarVisibility` | `Hidden` |
| `ListBox` | border style | `CornerRadius` | `10` |
| `ScrollBar` | default | `Opacity` | `0.9` |
| `ScrollBar` | default | `Margin` | `3` |
| `ScrollBar` | track border | `CornerRadius` | `10` |
| `ScrollBarThumbVertical` | thumb border | `CornerRadius` | `8` |

Selection-style branded windows use `text_white` for the filter label or icon, filter input text, and selection prompt label. Borders and separators remain on KLGreen/KLGreen-dark accents so labels such as `Select stories to review:` stay readable against the KLCharcoal background.

Windows that load shared properties without local resource copies:

| Window | XAML path | Loader path | Notes |
| --- | --- | --- | --- |
| KL&A list selection | `lib/GUI/SelectFromDict.xaml` | `lib/GUI/SelectFromDict.py` | Loads the shared dictionary directly; no copied local palette. |
| KL&A alert | `lib/GUI/CustomAlert.xaml` | `lib/GUI/CustomAlert.py` | Loads the shared dictionary directly; no copied local palette. |
| Find and replace | `lib/GUI/FindReplace.xaml` | `lib/GUI/FindReplace.py` | Loads the shared dictionary directly; no copied local palette. |
| Steel PSF story selection | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml` | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/script.py` | Loads the shared dictionary directly; no copied local palette. |

## Window Defaults Observed

The shared GUI windows follow these conventions where present:

| Property | Implementation value | KLName |
| --- | --- | --- |
| `WindowStartupLocation` | `CenterScreen` | N/A |
| `HorizontalAlignment` | `Center` | N/A |
| `WindowStyle` | `None` | N/A |
| `ResizeMode` | `NoResize` for fixed dialogs | N/A |
| Header row height | `25` | N/A |
| Header background | `header_background` | KLCharcoal |
| Close button size | `60 x 20` | N/A |

Known window backgrounds currently in use:

| Window | Implementation value | KLName |
| --- | --- | --- |
| `lib/GUI/FindReplace.xaml` | `#1A252B` | KLCharcoal |
| `lib/Renaming/GUI_BaseRename.xaml` | `#1A252B` | KLCharcoal |
| `lib/GUI/SelectFromDict.xaml` | `#1A252B` with `#33286048` to `#33307050` gradient grid background | KLCharcoal with KLGreen-transparent-a to KLGreen-transparent-b |
| `lib/GUI/CustomAlert.xaml` | `#1A252B` with `#33286048` to `#33307050` gradient grid background | KLCharcoal with KLGreen-transparent-a to KLGreen-transparent-b |
| `lib/GUI/Tools/CreateFromRooms.xaml` | `#1A252B` with `#33286048` to `#33307050` gradient grid background | KLCharcoal with KLGreen-transparent-a to KLGreen-transparent-b |
| `lib/match/clipboard_window.xaml` | `#1A252B` with `#33286048` to `#33307050` gradient grid background | KLCharcoal with KLGreen-transparent-a to KLGreen-transparent-b |
| `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml` | `#1A252B` with `#33286048` to `#33307050` gradient grid background | KLCharcoal with KLGreen-transparent-a to KLGreen-transparent-b |
| `KL&A Tools_dev.tab/03 Core Tools.panel/duplicate_sheets.pushbutton/Script.xaml` | `header_background` and `main_background` both set to `#1A252B` | KLCharcoal |

## UI Gallery Theme Audit

The DevSandbox UI Gallery catalogs representative KL&A custom, DevSandbox, and standard pyRevit windows in `lib/ui_gallery/launchers.py`. For KL&A custom and DevSandbox entries, use `lib/GUI/SelectFromDict.xaml` as the visual reference: borderless dark chrome, KLCode text branding in the 25 px header, KLCharcoal window background, optional KLGreen-transparent-a to KLGreen-transparent-b gradient, KLGreen-dark/KLGreen/KLGreen-secondary accents, and readable KLWhite text.

Standard pyRevit gallery entries are intentional external references and are not scored for KLCode theme consistency.

| Gallery title | Category | XAML path | Theme status | Notable drift | Recommended future action |
| --- | --- | --- | --- | --- | --- |
| Create from rooms | KL&A custom | `lib/GUI/Tools/CreateFromRooms.xaml` | Reference/aligned | Local copy of the shared palette; checkbox and window gradients match the shared SelectFromDict values. | Keep layout and behavior; sync copied resource values with the shared dictionary when this local copy is refreshed. |
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
| View range editor | KL&A custom | `KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml` | Needs future theming | Uses default resizable WPF chrome, light row/header styling, non-KL `#E8E8E8`, and WPF `Red` warning text instead of KLCode dark chrome. | Restyle as a KLCode tool window while preserving the editable grid and data bindings. |
| UI Gallery | DevSandbox | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml` | Needs future theming | Uses default resizable WPF chrome and unthemed DataGrid controls. | Apply KLCode header/chrome and a dark, readable gallery table in a future UI pass. |
| UI Gallery preview fixture | DevSandbox | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml` | Needs future theming | Intentionally minimal self-contained fixture with default WPF chrome. | Leave plain unless the fixture is promoted to a visual-review artifact; document it as a test exception if unchanged. |

Future KL&A custom windows should use the SelectFromDict chrome and palette by default. Exceptions must be explicit: standard pyRevit dialogs, test fixtures, and tool-specific windows may keep different chrome only when the reason is documented near the launcher or in this design system.

## Local GUI Overrides

Some windows use local resource dictionaries or local aliases instead of relying only on `lib/GUI/Resources/WPF_styles.xaml`. These should stay documented because shared palette changes may need to be copied manually.

### Windows With Local Resources

| Window | XAML path | Relationship |
| --- | --- | --- |
| Create from rooms | `lib/GUI/Tools/CreateFromRooms.xaml` | Loads the shared dictionary, then defines a local copy of the same palette and styles in `Window.Resources`; local values take precedence. |
| Find and replace views | `lib/Renaming/GUI_BaseRename.xaml` | Uses an embedded resource dictionary that mirrors the shared palette. |
| Find and replace sheets | `KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton/Script.xaml` | Uses an embedded resource dictionary that mirrors the shared palette. |
| Find and replace views prototype | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/Script.xaml` | Uses an embedded resource dictionary that mirrors the shared palette. |
| Find and replace sheets prototype | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/Script.xaml` | Uses an embedded resource dictionary that mirrors the shared palette. |
| Duplicate sheets | `KL&A Tools_dev.tab/03 Core Tools.panel/duplicate_sheets.pushbutton/Script.xaml` | Uses command-local aliases documented below. |

### Shared Palette Local Copies

These windows currently carry the same local color-resource keys as `lib/GUI/Resources/WPF_styles.xaml`: `lib/GUI/Tools/CreateFromRooms.xaml`, `lib/Renaming/GUI_BaseRename.xaml`, `KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton/Script.xaml`, `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/Script.xaml`, and `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/Script.xaml`.

| Token | Implementation value | KLName |
| --- | --- | --- |
| `header_background` | `#1A252B` | KLCharcoal |
| `text_white` | `#E5E4E2` | KLWhite |
| `text_gray` | `Gray` | KLGray-medium |
| `text_magenta` | `#33714F` | KLGreen |
| `button_fg_normal` | `White` | white |
| `button_bg_normal` | `#286048` | KLGreen-dark |
| `button_bg_hover` | `#407058` | KLGreen-secondary |
| `border_magenta` | `#286048` | KLGreen-dark |
| `border_blue` | `#33714F` | KLGreen |
| `uncheckbox_checked_colour` | `Gray` | KLGray-medium |
| `checkbox_checked_colour` | `#286048` | KLGreen-dark |
| `footer_donate` | `#407058` | KLGreen-secondary |

### Duplicate Sheets

`KL&A Tools_dev.tab/03 Core Tools.panel/duplicate_sheets.pushbutton/Script.xaml` defines command-local aliases for the shared GUI palette. The aliases below match the colors in `lib/GUI/Resources/WPF_styles.xaml`:

| Token | Implementation value | KLName |
| --- | --- | --- |
| `header_background` | `#1A252B` | KLCharcoal |
| `main_background` | `#1A252B` | KLCharcoal |
| `checkbox_checked_colour` | `#286048` | KLGreen-dark |
| `uncheckbox_checked_colour` | `Gray` | KLGray-medium |
| `text_header_title` | `#E5E4E2` | KLWhite |
| `text_header_item` | `#E5E4E2` | KLWhite |
| `text_white` | `#E5E4E2` | KLWhite |
| `text_darkblue` | `Gray` | KLGray-medium |
| `text_red` | `#33714F` | KLGreen |
| `text_magenta` | `#33714F` | KLGreen |
| `input_box_darkblue` | `#1A252B` | KLCharcoal |
| `border_main` | `#33714F` | KLGreen |
| `border_secondary` | `#286048` | KLGreen-dark |
| `button_01_background_normal` | `#286048` | KLGreen-dark |
| `button_01_background_hover` | `#407058` | KLGreen-secondary |

The window uses the plain `header_background` color. The decorative rotated color-band grid was removed.

## Cleanup Roadmap

The current local resource copies should be consolidated before more tools create their own standalone windows. The goal is to keep reusable KLCode windows in `lib/GUI` and keep tool folders focused on command logic.

Priority cleanup items:

| Priority | Item | Target outcome |
| --- | --- | --- |
| 1 | Remove copied shared palettes from local XAML files where possible. | Windows load `lib/GUI/Resources/WPF_styles.xaml` through `my_WPF.add_wpf_resource()` instead of carrying duplicated `SolidColorBrush` definitions. |
| 2 | Move reusable KLCode windows into `lib/GUI`. | Shared or repeated windows live in the GUI library instead of individual tool bundles. |
| 3 | Keep command bundles as thin launchers. | Tool folders call shared GUI classes and only pass tool-specific data, labels, and handlers. |
| 4 | Define explicit one-off exceptions. | Tool-specific windows may remain local only when they are unique enough to justify it, and the exception should be documented here. |
| 5 | Rename legacy color aliases when refactoring. | Names such as `text_magenta`, `border_blue`, `text_red`, and `input_box_darkblue` are replaced with clearer KLName-aligned resource names during a deliberate cleanup pass. |
| 6 | Re-check the UI Gallery after each consolidation. | `lib/ui_gallery/launchers.py` stays current and continues to show representative windows without palette drift. |

Initial consolidation candidates:

| Window | Current path | Preferred direction |
| --- | --- | --- |
| Create from rooms | `lib/GUI/Tools/CreateFromRooms.xaml` | Move under `lib/GUI` or refactor to load shared styles without a local palette copy. |
| Find and replace views | `lib/Renaming/GUI_BaseRename.xaml` | Move the reusable rename window into `lib/GUI` if it is intended as the shared rename base. |
| Find and replace sheets | `KL&A Tools_dev.tab/03 Core Tools.panel/Rename.pulldown/FindReplace_Sheets.pushbutton/Script.xaml` | Replace local XAML copy with the shared rename GUI pattern where possible. |
| Find and replace views prototype | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/Script.xaml` | Keep prototype-local while testing, then promote useful changes into the shared rename GUI. |
| Find and replace sheets prototype | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/Script.xaml` | Keep prototype-local while testing, then promote useful changes into the shared rename GUI. |
| Duplicate sheets | `KL&A Tools_dev.tab/03 Core Tools.panel/duplicate_sheets.pushbutton/Script.xaml` | Evaluate whether the window can move to `lib/GUI`; keep only command-specific wiring in the tool bundle. |

New KLCode windows should start in `lib/GUI` unless they are explicitly experimental, prototype-only, or tightly coupled to a single command.
