# KLCode Main Template

`KLCodeMainTemplate.xaml` is the working template for a KLCode multi-select
window. It is currently displayed through the DevSandbox UI Gallery with
fictional drawing types. Production commands continue to use
`lib/GUI/SelectFromDict.xaml`.

The template has no code-behind. The UI Gallery supplies the sample data,
sets preview text, loads the search icon, and provides the event handlers.
`GUI.forms.my_WPF` loads the shared WPF resource dictionary before loading this
XAML.

## Window Frame

| Setting | Current value |
| --- | --- |
| Initial size | `432 x 576` |
| Minimum size | `432 x 576` |
| Maximum height | `576` |
| Maximum width | Not set |
| Startup position | Center screen |
| Chrome | Borderless WPF window with transparency enabled |
| Taskbar | Shown |
| Main rows | 24 px header, 32 px filter, flexible body, 24 px footer |

The body begins at the top of its flexible row and uses a `12,6,12,6` margin.

## Header

The header is `24` px high with a `100`, `*`, `66` column layout.

| Part | Current design |
| --- | --- |
| Wordmark | Embedded `/KLCode` outlined geometry in a `94 x 16` Viewbox, left aligned with `Margin="5,0,1,0"`. It has no font or external image dependency. |
| Title | `main_title`, 14 px KLWhite, centered across the full header, 200 px maximum width, character ellipsis. |
| Close button | `60 x 18`, Arial 10 px, 6 px radius, centered in the right column. |
| Dragging | The header calls `header_drag`. |

## Filter and Selection List

The filter row has an 8 px left inset and 12 px right inset. Its columns are a
24 px icon zone, a 6 px gap, and the filter field.

| Part | Current design |
| --- | --- |
| Search icon | `filter_icon`, the native `lib/_icons/search_16px_light.png` bitmap, displayed at `16 x 16` without scaling. |
| Search field | `textbox_filter`, 14 px KLWhite text on a transparent, borderless TextBox. The outer `template_filter_border` supplies a continuous 1 px KLGreen outline, KLCharcoal fill, and 6 px radius. |
| Prompt | `text_label`, 14 px KLWhite label above the list. |
| List | `main_ListBox`, 360 px high, KLCharcoal fill, vertical scrolling only, and a KLGreen-dark outline. |
| List item | A 16 px checkbox with a 9 px KLWhite checkmark and 12 px text. Unchecked boxes have a KLCharcoal fill and 1 px KLGreen outline. |
| Scrollbar | KLCharcoal track with a KLGreen thumb, using 10 px track and 8 px thumb radii. |

Typing in the search field filters the gallery's fictional items by name.

## Actions

The local `TemplateActionButton` style uses Arial, no border, a KLGreen-dark
fill, KLWhite text, and a KLGreen-secondary hover fill.

| Button | Size and placement | Gallery behavior |
| --- | --- | --- |
| Select All | `104 x 26`, 12 px text | Checks every sample item. |
| Select None | `104 x 26`, 12 px text | Clears every sample item. |
| Close preview | `216 x 32`, 14 px text | Closes the gallery preview. |

The two secondary buttons have an 8 px gap and form a centered 216 px-wide
group. All three action buttons use an 8 px radius. The primary action has an
8 px top margin and a 16 px bottom margin before the footer.

## Footer

The footer is `24` px high with `100`, `*`, `100` columns.

| Part | Current design |
| --- | --- |
| Left link | `Prototype`, medium weight and KLGreen-secondary, with a 10 px left inset. |
| Center text | `footer_version`, centered gray text with character ellipsis and 4 px horizontal margins. |
| Right link | `Outreach`, medium weight and KLGreen-secondary, with a 10 px right inset. |

Both links use the shared hyperlink navigation handler and their configured
Microsoft Forms destinations.

## Color Reference

| Token or value | Current use |
| --- | --- |
| `#1A252B` KLCharcoal | Window, header, filter fill, list, scrollbar track, and footer. |
| `text_white` `#E5E4E2` | Header title, selection prompt, search text, list text, and checkbox checkmark. |
| `text_green` `#33714F` | Wordmark slash, filter outline, checkbox outline, and scrollbar thumb. |
| `border_green_dark` and `button_bg_normal` `#286048` | List outline, separator, default action fills, and checked checkbox fill. |
| `button_bg_hover` `#407058` | Action hover state and footer links. |
| `text_gray` `Gray` | Footer center text. |

## UI Gallery Values

The XAML supplies generic defaults. In the UI Gallery preview, the adapter
replaces them with these values and fictional data:

| Element | Gallery value or behavior |
| --- | --- |
| `main_title` | `Main template — gallery preview` |
| `text_label` | `Select fictional drawing types:` |
| `button_main` | `Close preview` |
| `footer_version` | `UI Gallery — fictional data only` |
| `main_ListBox` | Fictional drawing-type rows, with the first item's checkbox checked initially. |

## Editing Scope

Use this XAML for window-specific layout, controls, local templates, and
preview-facing labels. Shared color tokens and baseline WPF styles live in
`lib/GUI/Resources/WPF_styles.xaml`. Keep the outlined header wordmark inline;
it is intentionally self-contained so pyRevit WPF does not need to resolve a
font or load a separate logo bitmap.
