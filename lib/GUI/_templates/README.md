# KLCode reference templates

Open UI Gallery and search `Template -` to review these five windows. They are
reference compositions for future windows, with fictional sample controllers.
They all use the same shell and opt-in shared component resources.

| Reference | Source | Purpose |
| --- | --- | --- |
| Template - Selection | [KLCodeSelectionTemplate.xaml](KLCodeSelectionTemplate.xaml) | Compact filter, checked list, All/None and main action; [detailed guide](KLCodeSelectionTemplate.md) |
| Template - Form | [KLCodeFormTemplate.xaml](KLCodeFormTemplate.xaml) | Compact labeled Find/Replace/Prefix/Suffix group and inline validation; no Sample Preview |
| Template - Message | [KLCodeMessageTemplate.xaml](KLCodeMessageTemplate.xaml) | Information/Warning/Error severity, bounded long message, expandable details and dismissal |
| Template - Options | [KLCodeOptionsTemplate.xaml](KLCodeOptionsTemplate.xaml) | Dropdown, exclusive scope, Include Existing checkbox, numeric unit field and read-only path/Browse row |
| Template - Review | [KLCodeReviewTemplate.xaml](KLCodeReviewTemplate.xaml) | Filtered checkable table, severity chips, splitter, selected-item detail and action group |

The former main template was renamed Selection. The generic FindReplace visual
was adapted into Form; its unused Revit-dependent Python wrapper/export was
retired after caller inspection. Actual Core view/sheet rename commands retain
their own bundled XAML and production behavior.

## Shared code versus example code

`../Resources/KLCodeComponents.xaml` merges the foundation and owns field/group,
dropdown, option, result, status, table and splitter styles. Foundation owns
the shell/basic controls and tokens. `../window_chrome.py` loads Components
before the body and wires only common chrome. `../window_metadata.py` supplies
the caller's title and version; `../Resources/KLCodeChrome.xaml` holds the footer links and labels. The body owns layout and declared event names;
each production controller owns its data, validation and operations. The
production migration uses these same resources through Python/CLR host adapters.
Approved vector icons and their attributed sources live in
[lib/_icons/gui](../../_icons/gui/README.md).

`lib/ui_gallery/template_data.py` owns the five source identities and pure
fictional fixtures; `templates.py` implements the safe example interactions.
Gallery uses both through the explicitly allowlisted custom-preview factory.
No template action modifies a Revit model, reads/writes sample paths, opens
external footer links, or invokes a production command. Browse assigns a new
fictional path. Selection's action opens an informational sample alert; the
other examples report inline or dismiss the window.

## State and interaction contract

Each template offers Normal, Empty, Error, Disabled and Long content. Header
Close stays available when the body is disabled. Form keeps input/sample names
separate and supports validation/reset. Options validates a chosen category
and finite offset. Review distinguishes the selected detail row from checked
items, preserves checks across filtering, and Check All checks eligible items
only in the current filtered view. Hidden checks remain unchanged. Apply Checked
uses the full checked collection, including hidden items. Blocked samples are not user-checkable;
the Error fixture intentionally starts with an invalid blocked check so the
validation/recovery path can be reviewed.
Clear the filter before using Check All to recover an invalid hidden blocked
check in the Error fixture. Row selection only updates the right-hand detail
pane, with its resizable divider. Labelled Ready/Warning/Blocked chips center
within their Status cells through the opt-in `KlaDataGridStatusCell` style.

Form's owner-confirmed compact field role uses Segoe UI 12, 24-high inputs,
60-wide label and 240-wide input columns, 8-unit row gaps and 12-unit group
padding. Colon labels center vertically against the inputs. The reference now
starts at 360 x 352 after removing Sample Preview; Reset/Apply and inline feedback
remain. `KlaCompactFieldLabel` and `KlaCompactFieldInput` are explicit shared
styles, so other templates keep their current standard sizing until reviewed.
Its Edit Naming Rules prompt uses `KlaFoundationPromptLabel`, exactly matching
Selection's Select Elements prompt (Segoe UI 14, normal weight, zero padding).

Message starts with Details collapsed in every state, including Error. It fits
content at its current width between 288 and 640 units high, then scrolls the
message body when the cap is reached. Opening Details reserves its 128-high
readout plus margin, raising the minimum to 424; closing it restores the compact
minimum. It retains user expansion when severity changes. Heading/body colors
stay consistent; heading wording and the banner border distinguish severity.
These size limits are reference defaults for review. `window_chrome.fit_window_height`
is an opt-in helper for chromeless shared-shell windows; the caller invokes it
when content, expansion or width changes. It never shows the window.

Options also uses the compact 24-high field role for category, numeric offset
and read-only path, through opt-in `KlaCompactComboBox`, `KlaCompactFieldInput`
and `KlaCompactReadOnlyField`. Its two section prompts reuse
`KlaFoundationPromptLabel`. Its label column shares Form's 60-unit token, and
Include Existing uses the standard self-labelled checkbox. Offset keeps its
`mm` unit beside the input so its label fits the compact column. Options inputs
still fill the available width; Form's naming inputs remain fixed at 240.

Message severity changes its tone without changing banner geometry. Message
and details have bounded scrolling. Review columns have useful minimum widths;
the table can scroll horizontally at narrow sizes. Existing Search artwork and
native expander/dropdown affordances are reused; replacement artwork remains
an owner choice.

Dimensions and component appearance are an initial review build, not final
acceptance. See the [active plan](../../../docs/plans/custom-window-consolidation.md)
and [template-family verification](../../../docs/knowledge/reviews/design-system/2026-10-28-template-family.md).
The first owner-requested refinement pass is settled; the active plan owns
production migration and live-host acceptance status.

## Validation

Run `scripts/validate_ui_gallery_wpf.ps1` from the repository root. Its optional
OutputDirectory saves actual WPF renders of all 25 states and minimum-size
specimens. The isolated probe checks data binding, sample actions, chrome,
disabled text, column sizing and bounds; no Window is shown. It cannot establish
live pyRevit ownership, pointer/keyboard input, Narrator, DPI or Revit operations.
