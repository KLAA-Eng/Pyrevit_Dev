# KLCode Design System

The shared presentation of every KLCode window: the nine Python tool windows, five reference templates, Gallery and five
compiled add-in windows all run on `KlaWindowShell` with one chain of XAML dictionaries. The static PreviewFixture retains its test chrome. This file owns the rules and the
layering; the [consolidation plan](plans/custom-window-consolidation.md) owns task status; the
[template guide](../lib/GUI/_templates/README.md) owns the reference implementations; dated evidence lives in
[knowledge/reviews/design-system](knowledge/reviews/design-system/README.md). The long-form history is archived as
[2026-10-29-designsystem-archive.md](knowledge/reviews/design-system/2026-10-29-designsystem-archive.md).
The Claude design-system artifact mirrors this repository; its *Repo cleanup list* records drift it finds.

## Layers

Each dictionary merges only the ones above it. Nothing is referenced upward, and only the first two may spell a colour.

| Layer | File | Holds | May contain |
| --- | --- | --- | --- |
| Palette | `lib/GUI/Resources/KLCode_palette.xaml` | Role brushes (`KlaWindowBrush`, `KlaTextBrush`, `KlaTextMutedBrush`, `KlaTextOnAccentBrush`, `KlaAccentBrush`, `KlaAccentHoverBrush`, `KlaBorderBrush`, `KlaBorderStrongBrush`) and the 2019 snake_case aliases | Colour literals |
| Primitives | `KLCodeSharedPrimitives.xaml` | Footer-link style, the wordmark template (geometry from `lib/_logos/KLCodeWordmark.xaml`), the orientation-aware scrollbar | Brush references only |
| Tokens | `KLCodeFoundationTokens.xaml` | Typed values: `GridLength` rows / columns, `Thickness` insets and gaps, `CornerRadius`, sizes, fonts, state and component brushes | Numbers and colours (the only other place) |
| Chrome data | `KLCodeChrome.xaml` | Footer URIs (`KlaPrototypeUri`, `KlaOutreachUri`) and default labels (`CloseLabel`, `PrototypeLabel`, `OutreachLabel`) | Strings and URIs |
| Icons | `lib/_icons/gui/KLCodeIcons.xaml` (generated) | One `Kla<Role>Geometry` per approved Lucide role | Geometry only |
| Foundation | `KLCodeFoundation.xaml` | `KlaFoundationWindow`, `KlaWindowShell`, buttons, labels, input, filter, checkbox, list, link; the `KlaGuiIcon` presenter, `KlaGuiIconPen` and the generated `KlaIcon<Role>` images | Tokens and brushes by name; one template per control |
| Components | `KLCodeComponents.xaml` | Section, prompt, compact fields, `KlaFieldRows` and `KlaFilteredCheckList` compositions, readout, dropdown, radio, segment, toggle, link and ghost buttons, chips, banner, table, splitter; implicit TextBox / ComboBox / CheckBox; the compiled brush names; role-named aliases | Tokens and brushes by name |
| Compiled aliases | `src/KLCode.Wpf/Resources/KLCodeControls.xaml` | `Kla*Style` keys that are `BasedOn` the shared styles | No templates, no literals |

Tokens are every number or colour the rules below name; styles set properties and `BasedOn`; templates draw one control type
and template-bind what a style may set; window bodies hold layout and `x:Name`s. `scripts/check_ui_scale.py` keeps the
foundation and components free of numeric literals and reports consumer margins off the spacing scale.

## Approved rules

| Role | Rule |
| --- | --- |
| Identity | KLCharcoal `#1A252B` ground, KLGreen family, the outlined wordmark at 70×12 (`KlaWordmarkWidth` / `Height`) in every header |
| Chrome | Header and footer `KlaChromeRow` 24 high; side columns `KlaHeaderSideColumn` 86 / `KlaFooterSideColumn` 100; shared composition, never copied markup |
| Header | Wordmark left, centred 14-unit title with ellipsis and no tooltip, `Close` 60×18 at 10 (`KlaClose*`), glyph placement measured through `KlaCloseGlyphLift` |
| Footer | Prototype and Outreach links and the caller's pure `vX.X` version, all `KlaTextMutedBrush` (8.5:1); links underline, hover KLWhite; a missing version leaves the centre empty |
| Keyboard | Body first in Tab order, then Close, then the links; Escape closes through the adapter; Enter runs the one `IsDefault` main action; focus marks never move layout |
| Typography | Segoe UI; `KlaBodyFontSize` 12 for body and controls, `KlaTitleFontSize` 14 for title, prompts, headings and the main action; constant labels in Title Case |
| Buttons | Fixed roles: standard 104×28 (`KlaButtonWidth` × `KlaCompactHeight`), main 216×32, icon-text 128×28, icon 28×28, link and ghost 104×28 on the surface; `KlaRadiusCard` 8; never per-window sizes |
| Controls | Input 32 (`KlaControlHeight`), compact 28, compact field and filter 24; `KlaRadiusControl` 6; dropdown `MinWidth` = button width, popup `KlaDropDownMaxHeight` 260 |
| Spacing | 4 / 8 / 12 / 16 / 24 via `KlaGridSpace*`, `KlaPairGap`, `KlaSectionPadding`, `KlaCompactInset`; body inset `KlaBodyInset` 16 / 8 |
| Lists and tables | Checkbox rows 20 high with a 4-unit box gap (`KlaCheckSize` 16, `KlaRadiusCheck` 2); the always-visible KLCode scrollbar; grid header 8,6 and cells 8,4 |
| Icons | Lucide roles from `lib/_icons/gui`, `KlaIconSize` 16 on a `KlaIconCanvas` 24 with `KlaIconStroke` 1.5, foreground inherited, disabled `KlaDisabledTextBrush`; never a file path or a per-window copy |
| States | Hover `KlaAccentHoverBrush`, pressed `KlaPressedBrush`, disabled `KlaDisabledFillBrush` / `KlaDisabledTextBrush` with no opacity stacking, focus `KlaFocusBrush` as a 2-unit mark or border |
| Status | Chips keep a word and a border: `KlaReadyBrush`, `KlaWarningBrush`, `KlaErrorBrush`, `KlaInfoBrush`; colour is never the only signal |

## Hosts

- **Python (pyRevit).** `GUI.window_chrome.load_window(window, xaml, title, version)` merges one shared `KLCodeComponents.xaml`
  instance per process, loads the body (through the host's `load_xaml` when the window is a pyRevit `WPFWindow`), and binds
  Close, Escape, drag and the footer links. `version` is the tool's `__version__` or `None`; `title` is required.
  `GUI.window_metadata.WindowMetadata` carries identity only. Bodies and workflow stay caller-owned.
- **Compiled (C#).** `KLCode.Wpf.csproj` links the same dictionaries as Pages; `ThemeBootstrapper.Apply` merges
  `KLCodeControls.xaml` then `Strings/ResourceDictionary.<locale>.xaml`; `WindowChrome.Attach(window, shell, title, version)`
  binds the same parts. Labels are `DynamicResource`, so the locale dictionary overrides `KLCodeChrome.xaml` with no adapter code.
- **Shared data.** `lib/GUI/window_metadata_vectors.json` is the version rule's test vectors for both suites.

## Adding a window

1. Start from a template in `lib/GUI/_templates/` (Selection, Form, Message, Options, Review) and keep only the body inside
   `window_shell` / `window_body`; see the [Selection guide](../lib/GUI/_templates/KLCodeSelectionTemplate.md).
2. Use styles by role name (`KlaButton`, `KlaButtonPrimary`, `KlaInputCompact`, `KlaFilter`, `KlaCheck`, `KlaList`, …) and rows
   from `KlaGridSpace*`; no literal sizes, gaps or colours.
3. Give every input `AutomationProperties.Name`, mark the one main action `IsDefault`, and let the adapter own Close and Escape.
4. Add a Gallery adapter and a production-probe case, an adjacent `SPEC.md`, and run `python scripts/check_ui_scale.py`.

Use `KlaFieldRows` for the four compact naming rows: label/input columns 0/1,
row pairs 0/2/4/6. Use `KlaFilteredCheckList` for the filter/prompt/list/secondary
actions/main action in rows 0/2/4/6/8. Both are `ItemsControl` compositions with
shared Grid panels. Declare named controls and handlers as direct items so their
window namescope survives. A secondary-actions item can hold multiple rows.

## Validation

| Tier | What it proves | Where |
| --- | --- | --- |
| CPython tests | Adapter contracts, caller identity (`gui_caller_identity_test`), template contracts (`gui_foundation_contract_test`), token discipline (`gui_token_scale_test`), artwork generation (`gui_icons_test`) | `tests/` |
| IronPython + WPF probes | Real layout: chrome heights, gaps, scroll ranges, glyph centring, de / ko captions, icon stroke; values read from the tokens | `scripts/validate_ui_*_wpf.py` (Windows) |
| C# contract and smoke | Dictionary layering and literal-free rules; every compiled window constructs against forbidding fakes | `src/KLCode.Wpf/Tests` |
| Live Revit (GUI-08) | Ownership, DPI, drag, real tool operations | Owner will review; [Windows evidence and checklist](knowledge/reviews/design-system/2026-10-29-gui-architecture-windows.md) |
