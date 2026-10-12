# Design-system current-state review

Review date: 2026-10-08. Source baseline:
`089da1b7d88e0df9dec2cc127659a24e051b9163`.

This review records the UI Gallery source audit moved from
[DESIGNSYSTEM.md](../../../DESIGNSYSTEM.md), plus findings and follow-up actions
verified against the current Python, XAML, and C# repository state. It is a
source review: no live Revit window, WPF rendering, keyboard navigation, DPI, or
screen-reader acceptance is claimed.

The [2026-10-05 design-system and GUI review](../2026-10-05/design-system-and-gui.md)
is a separate historical baseline with broader GUI and accessibility findings.
Its finding register and evidence stay in that dated folder.

## UI Gallery Theme Audit

The DevSandbox UI Gallery catalogs representative KL&A custom, DevSandbox,
compiled add-in, and standard pyRevit windows in `lib/ui_gallery/launchers.py`.
For the 12 user-facing KL&A custom windows, use
`lib/GUI/_templates/KLCodeMainTemplate.xaml` as the visual reference:
borderless dark chrome, the outlined KLCode wordmark in the 24 px header,
KLCharcoal window background, KLGreen-dark/KLGreen/KLGreen-secondary accents,
and KLWhite text resources. The template is also a separate gallery preview
entry, not a thirteenth user-facing window. The five compiled WPF windows are
in the [compiled catalog](../../../DESIGNSYSTEM.md#compiled-wpf-windows) and
remain disabled in the gallery because their constructors require compiled
Revit host state.

Standard pyRevit entries are external references and are not scored for KLCode
theme consistency. The Gallery shell and its preview fixture are tooling rows
in the audit, outside the 12 user-facing KL&A custom windows.

The gallery registry currently contains 20 repository Window XAML surfaces:
the 14 pyRevit/DevSandbox windows audited below, the separate main-template
preview, and the five compiled WPF windows in the linked catalog. Each surface
has one gallery entry; only host-independent previews are launchable from the
IronPython gallery.

Statuses below describe source structure and resource loading at the recorded
baseline. They do not certify rendered appearance or interaction in Revit.

| Gallery title | Category | XAML path | Source status | Source observation | Recommended future action |
| --- | --- | --- | --- | --- | --- |
| Create from rooms | KL&A custom | `lib/GUI/Tools/CreateFromRooms.xaml` | Source-aligned with local list override | Loads shared styles through `my_WPF`, uses a solid KLCharcoal window background, and locally overrides its `ListBox`/scrollbar resources. | Keep layout and behavior; update shared control values in `WPF_styles.xaml`, then retain only its list-specific override. |
| KL&A alert | KL&A custom | `lib/GUI/CustomAlert.xaml` | Source-aligned | Alert-specific icon, heading, and OK button are preserved inside SelectFromDict-style dark chrome. | Keep aligned with the shared palette when alert states are expanded. |
| Duplicate sheets | KL&A custom | `lib/GUI/DuplicateSheets.xaml` | Source-aligned with local checkbox override | Large command-specific form uses shared styles whose resource keys map to the named design tokens, plus a nested checkbox style for its option grid. | Keep command handlers in the bundle and presentation in `lib/GUI`. |
| Find and replace | KL&A custom | `lib/GUI/FindReplace.xaml` | Source-aligned | Compact rename form uses the solid KLCharcoal header/body and shared KLCode resources. | Keep as a compact aligned variant. |
| Find and replace sheets | KL&A custom | `lib/GUI/RenameSheets.xaml` | Source-aligned | Production sheet rename presentation loads the shared dictionary; command behavior remains in its bundle. | Keep handlers and Revit transactions in the command bundle. |
| Find and replace sheets prototype | KL&A custom | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace_Sheets-proto.pushbutton/Script.xaml` | Shared-style prototype | The XAML uses shared window/header brushes and an initially collapsed result panel with scrollable details; its loader merges `WPF_styles.xaml`. | Complete live visual and Revit acceptance in the [promotion review](../2026-10-08/find-replace-promotion.md) before copying accepted behavior into `lib/GUI/RenameSheets.xaml`. |
| Find and replace views | KL&A custom | `lib/GUI/RenameViews.xaml` | Source-aligned | Shared rename base now loads `WPF_styles.xaml` through `my_WPF`. | Keep production view rename presentation in `lib/GUI`. |
| Find and replace views prototype | KL&A custom | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/FindReplace - Views-proto.pushbutton/Script.xaml` | Shared-style prototype | The XAML uses shared window/header brushes and an initially collapsed result panel with scrollable details; its loader merges `WPF_styles.xaml`. | Complete live visual and Revit acceptance in the [promotion review](../2026-10-08/find-replace-promotion.md) before copying accepted behavior into `lib/GUI/RenameViews.xaml`. |
| Match properties recall | KL&A custom | `lib/match/clipboard_window.xaml` | Shared-style production window; preview gap | Production hosts modeless clipboard content inside shared KLCode chrome, but the Gallery preview discards that chrome, as recorded in [GUI-05](../2026-10-05/design-system-and-gui.md#gui-05--p2-the-match-recall-gallery-preview-discards-the-chrome-it-intends-to-review). | Make the Gallery preview use the production chrome before treating it as visual review evidence. |
| KL&A list selection | KL&A custom | `lib/GUI/SelectFromDict.xaml` | Source-aligned | This is the reference theme for list-selection windows. | Keep as the base for future selection-style custom windows. |
| Steel PSF story selection | KL&A custom | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Steel PSF.pushbutton/SteelPsfDialog.xaml` | Source-aligned | Closely follows SelectFromDict list-selection chrome with a solid KLCharcoal background; footer is prototype-specific. | Keep aligned with SelectFromDict when Steel PSF controls change. |
| View range editor | KL&A custom | `KL&A Tools_dev.tab/03 Core Tools.panel/ViewRange.pushbutton/MainWindow.xaml` | Local-source variant | Uses local KLCode token resources with pyRevit's `forms.WPFWindow` loader. Python assigns the shared `KLCodeWordmark` template after XAML loading; local `ComboBox`/`ComboBoxItem` templates specify dark selector and popup surfaces. | Keep command-specific behavior in the bundle; move a style into `WPF_styles.xaml` only when another reusable window needs it, then verify in Revit. |
| UI Gallery | DevSandbox | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/Gallery.xaml` | Source-aligned | Uses SelectFromDict-style dark chrome, local KLCode token resources, and a KLCharcoal/KLGreen dark DataGrid treatment for catalog rows. | Keep gallery-only DataGrid styling local unless another KLCode table view adopts the same pattern. |
| UI Gallery preview fixture | DevSandbox | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/fixtures/PreviewFixture.xaml` | Intentional fixture exception | Uses a KLCharcoal background and otherwise minimal WPF chrome and text styling. | Keep its test-only purpose explicit; review styling if it becomes a user-facing or visual-acceptance surface. |

## Source findings and follow-up

### ComboBox contracts and GUI-08

The [October 5 GUI-08 finding](../2026-10-05/design-system-and-gui.md#gui-08--p3-the-general-combobox-property-tables-describe-a-different-template)
remained reproducible at this review baseline. The shared
`lib/GUI/Resources/WPF_styles.xaml` template uses a literal `White` arrow, changes
only selected text to `#888888` when disabled, and gives its item template
`Padding="2"`. The dark disabled selector, gray arrow, and `4,3` item padding
belong to the View Range command-local templates. The compiled WPF adapter has
its own `KlaComboBoxStyle` and `7,4` item padding.

The current guide now names all three implementations separately. This resolves
the documentation mismatch in this pass; it does not change the runtime styles
or establish live rendered behavior. Keep the historical GUI-08 finding in the
October 5 report as evidence of that baseline.

### Palette consolidation contract

`lib/GUI/Resources/WPF_styles.xaml` still defines its legacy brush values
locally. `src/KLCode.Wpf/Resources/KLCodeControls.xaml` merges
`lib/GUI/Resources/KLCode_palette.xaml` through the
`KLCode.Wpf.csproj` link named `Resources/KLCodePalette.xaml`. The source
test in
`src/KLCode.Wpf/Tests/KLCode.Wpf.Source.Tests/DesignSystemResourceContractTests.cs`
still asserts that the legacy dictionary merges the palette, which conflicts
with the current source. The [October 5 review](../2026-10-05/design-system-and-gui.md#design-system-contract-conflict-and-test-evidence)
records the test result at its baseline. Decide whether to consolidate the
dictionaries or revise the test contract in a separate implementation change,
then validate both IronPython and compiled WPF resource loading.

### Current catalog and host boundary

The repository has 20 `Window` XAML sources and one Gallery record for each.
The Gallery registry keeps `KL&A Tools.tab` as the stable command path alias;
the active development checkout and the paths in this table use
`KL&A Tools_dev.tab`. The five compiled records have `can_launch=False` because
they need the compiled Revit host. The main template is a separate preview;
standard pyRevit dialogs are external references.

Both Find and Replace prototypes changed after the October 5 review: their
window and header backgrounds now use shared brush keys, and each has a
collapsed outcome panel that expands for issues or a no-change result. The
[October 8 promotion review](../2026-10-08/find-replace-promotion.md) records
the static checks and pending Revit/visual acceptance. No result here closes
that acceptance gate. Other October 5 GUI findings remain in their original
report for separate follow-up.

## Validation at this baseline

| Check | Result |
| --- | --- |
| UI Gallery launcher and catalog tests | 10 tests run; passed with 1 skip. |
| Window-background source tests | 9 tests run; 2 fail because `tests/window_backgrounds_test.py` still expects literal `#1A252B` on the two Find and Replace prototype roots, while both XAML files now use `{StaticResource window_background}`. This is a test expectation mismatch with the current source, not a rendered WPF result. |
| New review links and audit tables | All local Markdown link targets exist; 14 rows remain in both the detailed and condensed source audits. |
| Live Revit/WPF acceptance | Pending. |

The window-background failures occur in `test_all_documented_windows_use_kl_charcoal`
and `test_kl_a_custom_windows_use_the_template_header_treatment`. Align those
source checks with resource resolution in a separate test change. This review
does not change tests or production XAML.
