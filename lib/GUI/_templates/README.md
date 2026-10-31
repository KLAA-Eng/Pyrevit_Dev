# KLCode reference templates

Open UI Gallery and search `Template -` to review these two reference windows.
They use the shared shell and component resources with fictional controllers.

| Reference | Source | Purpose |
| --- | --- | --- |
| Template - Options | [KLC-OptionsTemp.xaml](KLC-OptionsTemp.xaml) | Category, scope, Include Existing, offset and read-only path/Browse fields |
| Template - Review | [KLC-ReviewTemp.xaml](KLC-ReviewTemp.xaml) | Filtered checked table, status chips, selected detail and action group |

Form was removed at the owner's request. Naming rules now have the actual shared
[KLC-Rename dialog](../dialogs/RenameDialog.xaml). Earlier Selection and Message
templates were also removed; use the shared [Selection](../dialogs/SelectionDialog.xaml)
and [Message](../dialogs/MessageDialog.xaml) implementations. The
[shared dialog API guide](../dialogs/README.md) owns those public interfaces.

## Shared components and ownership

[KLCodeComponents.xaml](../Resources/KLCodeComponents.xaml) owns field groups,
dropdowns, options, results, status chips, tables and splitters. Foundation owns
the shell, basic controls and tokens. [window_chrome.py](../window_chrome.py)
loads these resources before the body and wires common chrome.
[window_metadata.py](../window_metadata.py) supplies caller title/version values.
The body owns layout and declared events; the controller owns data and actions.
Approved icons and attribution live in the [GUI icon catalog](../../_icons/gui/README.md).

`KlaFieldRows` retains the four-row naming composition used by KLC-Rename.
`KlaFilteredCheckList` provides filter, prompt, expanding list and action rows.
Both accept direct named items with `Grid.Row`/`Grid.Column` assignments.

[template_data.py](../../ui_gallery/template_data.py) owns the two explicit source
identities and fictional fixtures; [templates.py](../../ui_gallery/templates.py)
implements safe example interactions. Browse assigns a fictional path. No
reference action opens external links, modifies a model or accesses sample files.

## States and interactions

Both templates offer Normal, Empty, Error, Disabled and Long content. Close stays
available when the body is disabled. Options validates category and finite offset;
its 24-high category/offset/path fields use the compact component roles and its
section prompts use `KlaFoundationPromptLabel`. The offset unit remains beside
its input. Include Existing uses the standard self-labelled checkbox.

Review keeps selected detail separate from checked rows. Checks survive filtering;
Check All affects visible eligible rows only. Apply Checked uses the complete
checked collection, including hidden checks. Blocked samples cannot be checked.
The Error fixture starts with an invalid blocked check to exercise recovery;
clear the filter and use Check All to recover. Ready/Warning/Blocked chips center
within `KlaDataGridStatusCell` cells. The table supports horizontal overflow and
the detail divider can resize.

## Validation

Run `scripts/validate_ui_gallery_wpf.ps1` from the repository root. Optional
OutputDirectory saves actual WPF renders of all ten reference states and
minimum-size specimens. The probe checks binding, actions, chrome, disabled text,
columns and bounds. It does not establish live Revit ownership, physical input,
Narrator, DPI or model operations. The [active plan](../../../docs/plans/custom-window-consolidation.md)
owns current acceptance; [earlier template evidence](../../../docs/knowledge/reviews/design-system/2026-10-28-template-family.md)
records the historical three-template baseline.
