# KLCode Main Template Reference

`KLCodeMainTemplate.xaml` is the editable Select From Dict baseline for
KLCode custom WPF windows. It is loaded only by the DevSandbox UI Gallery;
production commands continue to use `lib/GUI/SelectFromDict.xaml`.

## Runtime and ownership

The UI Gallery preview loads `WPF_styles.xaml` through
`GUI.forms.my_WPF.add_wpf_resource()` before it loads this XAML. The gallery
then supplies fictional list items and the event handlers. This XAML has no
code-behind and is not a standalone pyRevit command.

| Responsibility | Source |
| --- | --- |
| Shared colors and default control styles | `lib/GUI/Resources/WPF_styles.xaml` |
| Resource loading and basic close, drag, and hyperlink handlers | `lib/GUI/WPF_Base.py` |
| Template layout and local control properties | `lib/GUI/_templates/KLCodeMainTemplate.xaml` |
| Gallery sample data and preview-specific handlers | `UI Gallery.pushbutton/script.py` |

## Window metadata and dimensions

| Property | Value | Effect |
| --- | --- | --- |
| Root | `Window` | Top-level WPF dialog. |
| Title | `KLCode Main Template` | Window metadata. The gallery changes the visible header title separately. |
| Width / height | `432 x 576` | WPF device-independent units. |
| Minimum width | `432` | The dialog cannot be narrower. |
| Minimum / maximum height | `576 / 576` | Fixed-height layout. |
| Maximum width | Not set | No stated width maximum. |
| Startup location | `CenterScreen` | Opens in the center of the display. |
| Window style | `None` | No native Windows title bar. |
| Transparency support | `True` | Allows custom borderless chrome; the window itself is fully painted. |
| Taskbar | `True` | Appears as its own taskbar window. |
| Resize mode | Not set | WPF defaults to `CanResize`, but the borderless shell has no normal resize handles. |

The root grid has four rows: a `24` px header, a `32` px filter band, flexible
content, and a `24` px footer.

## Colors

The named colors below come from `WPF_styles.xaml`; the KLName column follows
`DESIGNSYSTEM.md`.

| Use | Value | KLName | Source |
| --- | --- | --- | --- |
| Window, main grid, header, footer, list, filter background | `#FF131313` | KLCharcoal-black | Local template. |
| Header title and filter icon/text | `text_white` -> `#E5E4E2` | KLWhite | Shared resource. |
| Header slash and selection prompt | `text_green` -> `#33714F` | KLGreen | Shared resource, applied locally. |
| Filter/list border and separator | `border_green_dark` -> `#286048` | KLGreen-dark | Shared resource. |
| Default button fill | `button_bg_normal` -> `#286048` | KLGreen-dark | Shared Button style. |
| Button text | `button_fg_normal` -> `#FFFFFF` | white | Shared Button style. |
| Button hover and Outreach link | `button_bg_hover` -> `#407058` | KLGreen-secondary | Shared resource. |
| Footer version | `text_gray` -> `Gray` | gray | Shared resource. |
| Checkbox mark | `#E5E4E2` | KLWhite | Shared CheckBox template. |
| Unchecked checkbox square | `#FF131313`, 1 px KLGreen border | KLCharcoal-black / KLGreen | Local template. |
| Checked checkbox square | `checkbox_checked_colour` -> `#286048` | KLGreen-dark | Shared token, applied locally. |
| Checkbox hover | `button_bg_hover` -> `#407058` | KLGreen-secondary | Local template. |
| Scrollbar track | `#1A252B` | KLCharcoal | Local template. |
| Scroll thumb | `text_green` -> `#33714F` | KLGreen | Local template. |

`CheckBox Background="#286048"` is retained from Select From Dict, but the
shared CheckBox template paints its own gradient and does not bind that
property. It is therefore not the visible checkbox-square color.

## Fonts and shared visual rules

| Element | Font / visual rule | Source |
| --- | --- | --- |
| `/KLCode` wordmark | Audiowide Regular, 16 px | Local XAML; resolves the repository-local Audiowide font file. |
| Header title | 14 px, KLWhite, 200 px max width, character ellipsis | Local XAML. |
| Close button | 10 px, Arial, 6 px corner radius, green hover | Local Button style for radius; otherwise follows shared Button colors. |
| Secondary buttons | 12 px, Arial, 8 px corner radius, green hover | Size is local; Arial/radius/colors come from shared Button style. |
| Primary button | 14 px, Arial, 8 px corner radius, green hover | Size is local; Arial/radius/colors come from shared Button style. |
| Filter icon | Inline 24 px WPF vector matching `lib/_icons/search_24px_light.svg` | Local XAML; avoids runtime SVG-loader dependency. |
| Filter box | 14 px, 24 px high, 6 px corner radius | Local XAML. |
| Selection prompt | 14 px, KLGreen | Local XAML. |
| List item text | 12 px | Local XAML on the bound CheckBox. |
| Other text | No explicit family or size | Inherits the WPF system font. |
| List/track border | 10 px corner radius | Local list and scrollbar styles. |
| Scroll thumb | 8 px corner radius | Local `TemplateScrollBarThumbVertical` style. |

## Spacing and dimensions

| Element | Value | Effect |
| --- | --- | --- |
| Header band | `24` px high; columns `100`, `*`, `66` | Reserves fixed wordmark and Close zones while allowing the title to center on the full window. |
| Wordmark | `Margin="5,0,0,0"` | Keeps `/KLCode` close to the left edge. |
| Header title | `Grid.Column="0"`, `Grid.ColumnSpan="3"`, `MaxWidth="200"` | Centers on the full 432 px window and ellipsizes before colliding with side controls. |
| Close button | `60 x 18`, centered in the 66 px right column | Leaves roughly 3 px on each side. |
| Filter band | `32` px high | Compact search row. |
| Filter icon | `24 x 24`, `Margin="8,4,6,4"` | Vertically centered with an 8 px left inset and 6 px gap before the box. |
| Filter box | `24` px high, `Margin="0,4,12,4"` | Vertically centered and aligned to the 12 px body right gutter. |
| Body stack | `Margin="12,6,12,6"` | Creates a 408 px inner content width and 484 px inner content height. |
| List | `Height="360"` | Leaves room for the prompt and action buttons in the 496 px body row. |
| Secondary buttons | `108 x 24`, `Margin="6"` | Two compact actions centered in a horizontal row. |
| Primary button | `216 x 32`, `Margin="6"` | Larger primary action centered below the secondary row. |
| Footer band | `24` px high; columns `100`, `*`, `100` | Two-link footer with a centered truncating version/status slot. |
| Footer left link | `Margin="10,0,0,0"` | Left-side Prototype slot. |
| Footer center text | `Margin="4,0"`, stretch alignment, centered text, character ellipsis | Keeps `footer_version` centered and truncates long text within the middle column. |
| Footer right link | `Margin="0,0,10,0"` | Right-side Outreach slot. |

## Element map

| Area | Element | Key properties | Gallery behavior |
| --- | --- | --- | --- |
| Header | Grid | `24` px high; columns `100`, `*`, `66`; `#FF131313` background | Dragging calls `header_drag`. |
| Branding | TextBlock | `/KLCode`, left aligned, Audiowide Regular, 16 px, `Margin="5,0,0,0"`; slash is KLGreen | Static text. |
| Header title | `main_title` TextBlock | Centered across the full window, KLWhite, 14 px, 200 px max width, character ellipsis | Set to `Main template - gallery preview`. |
| Close | Button | `60 x 18`, 10 px, 6 px corner radius, centered in right column | Calls `button_close`. |
| Filter | Inline search vector, `textbox_filter` TextBox | Search vector is 24 px; text box is 24 px high, 14 px, 6 px corner radius, with a text-changed event | Filters the fictional list by name. |
| Prompt | `text_label` Label | KLGreen, 14 px | Set to `Select fictional drawing types:`. |
| List | `main_ListBox` | 360 px high, `#FF131313` body, KLCharcoal track, KLGreen thumb, vertical scroll, horizontal scroll disabled | Receives fictional drawing types. |
| List row | CheckBox plus TextBlock | 16 px checkbox square, 9 px checkmark, 12 px text, `IsChecked` / `Name` bindings | Displays sample item selection. |
| Secondary actions | `UI_Buttons_all_none` | Centered; two `108 x 24` buttons, 12 px text | Select all or select none. |
| Primary action | `button_main` | `216 x 32`, 14 px text | Relabeled `Close preview`; closes the gallery preview. |
| Footer left | Prototype hyperlink | Medium weight, secondary green | Opens the Outreach Prototype form. |
| Footer center | `footer_version` TextBlock | Centered, gray, stretch-aligned, character ellipsis | Set to `UI Gallery - fictional data only`. |
| Footer right | Outreach hyperlink | Medium weight, secondary green | Opens the existing Microsoft Forms URL. |

## Next path

- [ ] **Rendered review:** Open the UI Gallery template preview in pyRevit and
  verify the fixed-size layout with keyboard and pointer interactions.
- [ ] **Shared style review:** Decide whether any template-local styles, such as
  the 6 px Close button radius or inline search vector pattern, should become
  shared GUI conventions.

## Local versus shared cleanup boundary

Keep these in the template when they are specific to the future window:

- Overall dimensions, grid layout, control placement, margins, labels, and
  window-specific event names.
- Purpose-specific controls and content-area behavior.

The shared resource dictionary should own reusable design rules:

- Named color tokens, button styling, typography defaults, checkbox drawing,
  scrollbar-thumb styling, and common control shapes.

The template has local ListBox, ScrollBar, and CheckBox styles so this
experiment stays isolated from existing commands. Promote any of these local
rules only after they are accepted for broader KLCode windows.
