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
| Width / height | `400 x 550` | WPF device-independent units. |
| Minimum width | `400` | The dialog cannot be narrower. |
| Minimum / maximum height | `550 / 550` | Fixed-height layout. |
| Maximum width | Not set | No stated width maximum. |
| Startup location | `CenterScreen` | Opens in the center of the display. |
| Window style | `None` | No native Windows title bar. |
| Transparency support | `True` | Allows custom borderless chrome; the window itself is fully painted. |
| Taskbar | `True` | Appears as its own taskbar window. |
| Resize mode | Not set | WPF defaults to `CanResize`, but the borderless shell has no normal resize handles. |

The root grid has four rows: a `25` px header, a `45` px filter band, flexible
content, and a `25` px footer.

## Colors

The named colors below come from `WPF_styles.xaml`; the KLName column follows
`DESIGNSYSTEM.md`.

| Use | Value | KLName | Source |
| --- | --- | --- | --- |
| Window and main grid | `#1A252B` | KLCharcoal | Local XAML. |
| Header, footer, list, filter background | `#FF131313` | KLCharcoal-black | Local template. |
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
| `/KLCode` wordmark | Audiowide Regular, 14 px | Local XAML; resolves the repository-local Audiowide font file. |
| Close button | 10 px, Arial | Size is local; Arial comes from the shared Button style. |
| Other buttons | Arial, 8 px corner radius, green hover | Shared Button style. |
| Filter box | 14 px, 22 px high | Local XAML. |
| Other text | No explicit family or size | Inherits the WPF system font. |
| Filter border | 5 px corner radius | Local TextBox style. |
| List/track border | 10 px corner radius | Local list and scrollbar styles. |
| Scroll thumb | 8 px corner radius | Local `TemplateScrollBarThumbVertical` style. |

## Element map

| Area | Element | Key properties | Gallery behavior |
| --- | --- | --- | --- |
| Header | Grid | `25` px high; columns `75`, `*`, `60`; `#FF131313` background | Dragging calls `header_drag`. |
| Branding | TextBlock | `/KLCode`, left aligned, Audiowide Regular, `Margin="5,0,0,0"`; slash is KLGreen | Static text. |
| Header title | `main_title` TextBlock | Centered, KLWhite | Set to `Main template - gallery preview`. |
| Close | Button | `60 x 20`, 10 px | Calls `button_close`. |
| Filter | Search icon, `textbox_filter` TextBox | Text box is 22 px high, 14 px, with a text-changed event | Filters the fictional list by name. |
| Prompt | `text_label` Label | KLGreen | Set to `Select fictional drawing types:`. |
| List | `main_ListBox` | 350 px high, `#FF131313` body, KLCharcoal track, KLGreen thumb, vertical scroll, horizontal scroll disabled | Receives fictional drawing types. |
| List row | CheckBox plus TextBlock | `IsChecked` / `Name` bindings | Displays sample item selection. |
| Secondary actions | `UI_Buttons_all_none` | Centered; two `100 x 20` buttons | Select all or select none. |
| Primary action | `button_main` | `210 x 30` | Relabeled `Close preview`; closes the gallery preview. |
| Footer left | Prototype hyperlink | Medium weight, secondary green | Opens the Outreach Prototype form. |
| Footer center | `footer_version` TextBlock | Centered, gray | Set to `UI Gallery - fictional data only`. |
| Footer right | Outreach hyperlink | Medium weight, secondary green | Opens the existing Microsoft Forms URL. |

## Next path

- [ ] **Fonts:** Review the type hierarchy, sizes, weights, and which elements
  should use the Audiowide display face versus the body font.
- [ ] **Element spacing:** Review row heights, control margins, gaps, alignment,
  and the relative visual weight of the header, filter, list, actions, and
  footer.

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
