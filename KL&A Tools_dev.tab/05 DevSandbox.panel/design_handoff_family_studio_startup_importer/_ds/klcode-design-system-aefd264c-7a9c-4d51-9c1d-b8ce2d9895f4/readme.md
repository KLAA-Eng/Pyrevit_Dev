# KLCode — Design System

The design system for **KLCode**, the internal pyRevit extension used by KL&A engineers
inside Autodesk Revit. It is not a website or a consumer app: every surface is a Windows
desktop panel, dialog or ribbon control rendered by WPF inside Revit.

## Sources

Everything here was read from material the team supplied. Nothing was invented from memory.

- **Attached codebase — `KLCode.pyRevit/`** (mounted locally): the extension itself.
  `DESIGNSYSTEM.md` is the repo's own record of the palette ("KLName" colors), icon
  conventions and shared GUI properties — it is the ground truth this system mirrors.
  Also read: `KL&A Tools_dev.tab/**/bundle.yaml`, `lib/_icons/`, `lib/_logos/`,
  `ViewRange.pushbutton/MainWindow.xaml`.
- **Attached codebase — `GUI/`** (mounted locally, a mirror of the repo's canonical `lib/GUI/`):
  `Resources/WPF_styles.xaml` (the shared green theme) and the seven shared window XAMLs —
  `SelectFromDict`, `CustomAlert`, `FindReplace`, `RenameViews`, `RenameSheets`,
  `DuplicateSheets`, `Tools/CreateFromRooms`.
- **GitHub — https://github.com/pyrevitlabs/pyRevit**: the host platform. KLCode is a
  pyRevit extension; `pyrevit.forms` supplies the alert boxes, `WPFWindow`, `WPFPanel` and the
  markdown output window that several tools print to.

Explore the mounted folders directly if you need more than this system captures — the bundle
YAMLs, `DESIGNSYSTEM.md` and the XAML files are the ground truth for any new KLCode surface.

## The two themes

The extension deliberately runs **two visual languages**, and the choice is not cosmetic:

1. **Green theme** (`WPF_styles.xaml`) — solid charcoal `#1A252B` windows, green labels,
   rounded controls, custom scrollbars, and a branded 25px header/footer band. Used for the
   extension's own modal dialogs: pick-a-thing lists, rename dialogs, create-from dialogs and
   the KL&A alert. These are borderless windows (`WindowStyle="None"`) dragged by their
   header.
2. **Native theme** — plain white Revit/WPF, 11px Segoe UI, square corners, system buttons.
   Used for anything that lives *inside* Revit's own furniture: dockable panes (Custom Props,
   Match Properties clipboard) and utility windows (View Range Editor), plus every
   `forms.alert` message box.

**Rule of thumb:** a window the user summons and dismisses gets the green theme; a surface that
sits alongside Revit's own panels stays native. Never mix the two inside one window.

## Window and popup formats

Eleven formats exist in the whole system. Anything new should reuse one of them.

**Green theme — custom WPF, borderless, fixed size**

1. **Filtered checkbox list** — filter, list, Select All/None, primary button, footer. *Select From Dict 400 × 550.*
2. **Filtered list + settings** — filter, short list, bordered settings group, primary button, footer. *Create From Rooms 400 × 460.*
3. **Small form dialog** — label + field rows in one group, white row labels and input text. *Views: Find and Replace 350 × 210; RenameViews base 350 × 235.*
4. **Two-group rename dialog** — two 110-tall groups side by side, 150-wide action button. *Sheets: Find and Replace 620 × 250.*
5. **Multi-group settings dialog** — stacked bordered groups (naming, browser organisation, include toggles, duplicate modes) and a 200 × 30 action button. *Duplicate Sheets 800 × 470.*
6. **Alert dialog** — the one window with a 1px green-dark border; icon roundel (gold `!` Warning / green `i` Information), bold green heading, message, 55px OK band. *KL&A Alert 440 × 255.*

**Native Revit surfaces — white, square, 11–12px**

7. **Dockable pane** (`forms.WPFPanel`) — status line, sections, scrollable body, action row pinned to the bottom. *Custom Props; pyRevit MatchHistory Clipboard.*
8. **Modeless utility window** (`forms.WPFWindow`) — resizable, remembers its position. *Match Properties Recall 420 wide, height-to-content, resize grip; View Range Editor 720 × 380.*

**Host popups — supplied by pyRevit, not styled here**

9. **`forms.alert`** — message box; `sub_msg`, `expanded`, `footer`, `warn_icon`, `ok`, `exitscript`.
10. **Pickers** — `CommandSwitchWindow` (option chips), `ask_for_string`, `SelectFromList` / `select_open_docs`, `select_parameters`, `WarningBar`.
11. **Output window** — markdown/print log, ALL-CAPS headers, `'-' * 100` rules.

DevSandbox prototypes (UI Gallery, Steel PSF, the two Find-and-Replace protos) follow the
SelectFromDict chrome; the repo flags the UI Gallery and View Range Editor as needing a future
theming pass — do not copy their unthemed DataGrid/chrome into new work.

## CONTENT FUNDAMENTALS

**Voice.** Terse, imperative, engineer-to-engineer. The interface tells you what to do next and
what just happened, and nothing else. No marketing register, no personality, no exclamation
marks.

**Person.** Neither "I" nor "you" appears in the UI. Instructions are bare imperatives —
`Select a single text note in the active view first.`, `Open a Revit model or family first.`,
`Model is not workshared.` Results are stated as facts — `Operation cancelled.`,
`5 parameters copied`, `No selection`.

**Casing.**
- Button labels and window titles: Title Case — `Select All`, `Select None`, `Check All`,
  `Uncheck All`, `Toggle All`, `Paste One`, `Paste Box`, `Paste Sel.`, `Apply Changes`,
  `Reset to Original`, `Set Revision On Sheets`.
- Field labels end with a colon: `Find:`, `Replace:`, `Prefix:`, `Suffix:`,
  `Select Elements:`, `Select Type:`, `Additional Settings:`, `Offset from level (cm):`.
- Status and tooltip sentences are sentence case with a full stop only when they are complete
  sentences: `Read-only. Design option membership cannot be changed via the API.` versus
  `Toggle regex / substring search`.
- The legacy pyRevit output window shouts in caps — `SELECTED REVISION ADDED TO THESE SHEETS:`,
  `SEARCH COMPLETED.` — bordered by `'-' * 100` rules. Keep that for output logs only; never in
  a WPF surface.

**Length.** Button labels are one or two words and get abbreviated rather than wrapped:
`Elem Params`, `Filter+Elem`, `Paste Sel.`. Ribbon titles use an explicit `\n` to break onto
two lines (`"About\nKL&A Tools"`). Tooltips carry the real explanation and run to a full
sentence: *"Select a revision from the list of revisions and this script set that revision on
all sheets in the model as an additional revision. Shift+Click bypasses the issued check."*

**Localisation.** Ribbon titles and tooltips ship in eight languages (en_us, ko, fr_fr, ru,
chinese_s, es_es, de_de, pt_br); pane and clipboard strings live in per-locale
`ResourceDictionary` XAML. Never hard-code a user-facing string into markup — put it in the
resource dictionary and reference it.

**Emoji.** Exactly one, deliberately: the 🔍 magnifier that labels the filter box in the green
dialogs. Nothing else — no emoji in tooltips, buttons, alerts or output.

**Unicode glyphs as icons.** Used sparingly where an icon font would be overkill: `↺`
(U+21BA) for the undo button in the Custom Props pane, `✕` for close.

**Vibe.** Quiet, dense, tool-like. Everything on screen is a control or a value. There is no
empty state art, no onboarding, no encouragement.

## VISUAL FOUNDATIONS

**Colour.** Two palettes, one per theme, both recorded as "KLName" colors in the repo's
`DESIGNSYSTEM.md`. The green theme is built on a single dark blue-green charcoal — KLCharcoal
`#1A252B` — that does window, header, footer, field and list backgrounds alike, plus a green
family that does all the work: KLGreen `#33714F` for labels, input borders and icons;
KLGreen-dark `#286048` for button fills, panel borders and checked states; KLGreen-secondary
`#407058` for hover and the footer link. Text is KLWhite platinum `#E5E4E2`, never pure white;
muted text is plain `Gray`. KLOrange `#FF8000` appears only in icons — the "off" counterpart to
green in toggles, and the default icon color for prototype tools. Semantic accents:
warning-gold `#DAA520`, info-green `#3CB371`. The native theme is white with `#F5F5F5`
headers, `#E8E8E8` read-only chips, `#DDDDDD` rules, `#333/#555/#666` inks, LemonChiffon
`#FFFACD` for pending edits and red for warnings.

The legacy magenta palette is long gone, and the repo cleanup renamed the XAML resource keys
to match their values — `text_green`, `border_green`, `border_green_dark`,
`checkbox_checked_colour`, `footer_donate`. Trust the names; there are no lying keys left.
The semantic accents are live in the KL&A alert: warning-gold `#DAA520` colors the `!` Warning
glyph (WPF `Goldenrod`), info-green `#3CB371` the `i` Information glyph (`MediumSeaGreen`).

**Type.** UI text is Segoe UI everywhere (WPF default), with Arial set explicitly on
green-theme buttons and Consolas-class monospace in the pyRevit output window. Sizes: 10, 11,
12, 13, 14 — plus 16 and 22 in the KL&A alert only (heading and icon glyph). Weights: regular,
SemiBold (section headers), Heavy/bold (wordmark, grid headers, alert heading). Nothing else is
ever set larger than 14px — these are dense tool windows, not pages.
**Audiowide** (`assets/fonts/`) exists solely for the logo wordmark — never for UI text.

**Spacing.** Dialog margins run 2 / 5 / 10; native panes run 4 / 6 / 8. Chrome bands are exactly
25px. Controls have fixed pixel heights (18, 20, 22, 25, 28, 30) and fixed widths (60 Close, 100
Select All/None, 200 field, 210 primary button) — they do not stretch to fill.

**Backgrounds.** No photography, no illustration, no texture, no pattern — and since the repo
cleanup, no window wash: the old 20%-alpha diagonal green gradient is retired and every
green-theme window is flat, solid KLCharcoal. The only gradient left in the system is the
checkbox fill. Native surfaces are flat white.

**Corner radii.** 10px on panels, list boxes and scroll tracks; 8px on buttons and the scrollbar
thumb; 5px on text boxes; 3px on the ViewRange plane swatch; 2px on the checkbox bullet and
ComboBox; the KL&A alert icon sits in a 34px circle. Native surfaces: 0 everywhere.

**Cards.** There are none in the web sense. Grouping is a 1px `#286048` border with a 10px
radius, a transparent fill and a green caption above it. No shadow, no tint, no left-accent bar.

**Shadows.** The system has no shadow tokens at all — WPF windows get the OS drop shadow and
nothing else. Depth is communicated by a 1px border and a flat fill change.

**Transparency and blur.** `AllowsTransparency="True"` survives on Select From Dict, Create From
Rooms and the KL&A alert, but their backgrounds are solid — nothing shows through anymore. No
blur anywhere.

**Animation.** Effectively none. WPF `Style.Triggers` swap a colour instantly; there is no
duration, no easing, no fade. The single exception is the ComboBox popup's built-in
`PopupAnimation="Slide"`. Do not add transitions when recreating these surfaces — the snap is
the look.

**Hover states.** Buttons swap fill outright (`#286048` → `#407058`). The checkbox bullet goes
near-black `#131313`. List and ComboBox rows highlight `#4F4F4F`. Native buttons take Revit's
own blue-tinted hover.

**Press states.** There are none. No shrink, no darken, no ripple — a click either opens a
window or runs a transaction.

**Disabled states.** Text drops to `#888888` (ComboBox, list items) or `Gray` (checkbox label);
the checkmark stroke goes `#6C6C6C`; paste buttons simply disable until something is checked.

**Borders.** One weight: 1px. KLGreen `#33714F` for inputs and dropdowns, KLGreen-dark
`#286048` for panels, lists, scroll tracks and the KL&A alert's window edge — the only
green-theme window with a border — `#DDDDDD` for native rules. The single 2px border is the
alert's icon roundel.

**Scrollbars.** Custom and always visible in the green theme: KLGreen-dark track with a 10px
radius and a 3px margin, solid black thumb with an 8px radius.

**Layout rules.** Fixed-size windows (350×210, 400×460, 400×550, 440×255, 720×380) with fixed row
heights; the header band is row 0 at 25px and the footer is the last row at 25px, both pinned.
Content is a single centred column. Nothing is responsive — these windows do not resize except
the View Range Editor and the recall window.

**Imagery.** None. The only raster assets are the button icons and the logo files.

## BRAND

**Logo.** `assets/logos/KLCodeLogo.png` is the primary mark — KLCharcoal and the KLGreen
family are sampled from it. `KLCode_text_1024x256px.svg/.png` is the wordmark lockup;
`C2E` / `E2C` are the code↔Excel tool lockups; the `KLCodeLogo_option-*_ribbon.svg` files are
ribbon-scale logo variants. The wordmark font is **Audiowide** (`assets/fonts/`), logo use only.

**Chrome branding.** Green dialogs carry "KLCode" in Heavy 14px Segoe UI at the left of the
25px header band. The footer band shows the learnrevitapi logo (the template's origin), the
centred gray version string, and an "Outreach" feedback link in KLGreen-secondary.

## ICONOGRAPHY

**Icon library — `assets/icons/lib/`.** 29 reusable 96×96 masters from `lib/_icons/`, each in
four colorways, named `<icon>_<size>px_<color>.png`: `_dark` KLCharcoal `#1A252B`, `_light`
KLWhite `#E5E4E2`, `_green` KLGreen `#33714F`, `_orange` KLOrange `#FF8000`. Convention: light
UI buttons ship `_dark` as `icon.png`; dark UI ships `_light` as `icon.dark.png`; new prototype
scripts start with an `_orange` icon (`drill_32px_orange.png`). Draw new icons to Lucide's
visual language: simple outlines, clear silhouettes, consistent stroke weight. Button-frame
templates (`button*_48px`, `buttonpulldown_64px`) are included. Always use the real PNG — never
redraw one as SVG.

**Ribbon icons.** New and refreshed ribbon buttons draw from the library above — export at the
size the bundle needs (usually 32px). The legacy per-button PNGs in `assets/icons/` (black line
drawings, slate `#34495E` silhouettes) predate the colorway system and are being migrated — do
not base new icons on them.

**Inline icons — Material Design Icons.** The Match Properties clipboard embeds MDI path
geometry in `clipboard.Icons.xaml` and renders it at 15px inside buttons: `tag-multiple`,
`eye-outline`, `filter`, `regex`, `cursor-default`, `crop-free`, `check-all`, plus a close
glyph. (The clipboard itself is a Revit-side surface not recreated in this system.)

**Emoji and unicode.** 🔍 for the filter box; `↺` for undo; `✕` for close. Nothing else.

## Index

**Foundations** — `styles.css` (import entry) and `tokens/`: `colors.css` (KLName palette),
`typography.css` (incl. Audiowide `@font-face`), `spacing.css`, `radii.css`, `effects.css`,
`semantic.css`. Specimen cards live in `guidelines/`.

**Components**

- `components/chrome/` — **WindowFrame**, **WindowHeader**, **WindowFooter**
- `components/forms/` — **Button**, **TextField**, **FieldLabel**, **CheckItem**, **RadioItem**,
  **Select**, **ListPanel**, **FilterField**, **GroupBorder**, **SeparatorLine**
- `ui_kits/ribbon/` — **RibbonPanel**, **RibbonButton**, **RibbonStack**, plus the assembled
  **RibbonTab** screen and the **AlertDialog** `forms.alert` stand-in — they live beside the
  ribbon kit they exist for.

**UI kits**

- `ui_kits/dialogs/` — all seven custom WPF windows: Select From Dict, KL&A Alert,
  Create From Rooms, Views: Find and Replace, RenameViews base, Sheets: Find and Replace,
  Duplicate Sheets
- `ui_kits/ribbon/` — the extension's ribbon tab, pulldowns, smartbutton states, `forms.alert` box
  (host-popup recreations — alert, CommandSwitchWindow, ask_for_string, SelectFromList,
  WarningBar, output window — live inside `ui_kits/dialogs/` as the board's pyRevit standard group)

The native Revit pane surfaces (Custom Props, Match Properties clipboard, View Range Editor)
are deliberately **not** recreated here — they are unthemed Revit-side windows awaiting a KLCode
theming pass (see the repo's UI Gallery audit). Design new work against the green theme.

**Assets** — `assets/logos/` (marks, wordmarks, lockups), `assets/fonts/Audiowide-Regular.ttf`,
`assets/icons/lib/` (the reusable icon library), `assets/icons/` (shipped per-button ribbon
PNGs). Also `SKILL.md` (portable skill wrapper), `thumbnail.html`.

### Intentional additions

- `RibbonPanel` / `RibbonButton` / `RibbonStack` — the repository defines ribbon *content*
  (bundle YAMLs and icons) but not the ribbon chrome, which belongs to Revit. These components
  approximate Revit's ribbon so the extension's buttons can be shown in context. The ribbon tab
  still reads "KL&A Tools" — that is the shipped tab name (`KL&A Tools_dev.tab`).
- `AlertDialog` (in `ui_kits/ribbon/`) — a stand-in for `pyrevit.forms.alert`, which is
  supplied by the host platform rather than this extension. Distinct from the branded KL&A
  alert (`lib/GUI/CustomAlert.xaml`), which is the extension's own and lives in
  `ui_kits/dialogs/CustomAlert.jsx`.
