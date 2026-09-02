# Handoff: Family Studio & Startup Importer — KLCode green-theme windows + feature expansion

## Overview

Two KLCode DevSandbox tools get a full UI pass **and** a feature expansion:

- **Family Studio** — today an unthemed native WPF `Window` built in code
  (`FamilyStudioWindow.cs`). Re-skin it to the KLCode green theme and grow it from a
  flat list browser into a faceted catalog browser with Views mode, a grid view,
  inline type editing, tagging, batch actions, a duplicate/variant resolver, an
  in-app library-root editor, and a themed refresh flow.
- **Startup Importer** — today two native `OpenFileDialog`s plus a `TaskDialog`
  review (`StartupImportCommand.cs`). Replace that with real green-theme windows:
  a checklist+settings picker, a review window with a live seed preview and
  per-item placement targeting, a blocking-issues state, a placement/split screen
  with a live extents preview, an Update-Links sync manager, and themed
  success/error alerts.

Both tools stay **DevSandbox** and keep every governance boundary already written
into their `PLAN.md`/`SPEC.md` (see **Boundaries** at the end — read it before you
build; several requested surfaces are intentionally *concepts*, not shippable claims).

## About the design files

The two `.dc.html` files in this bundle are **design references** — HTML prototypes
that show the intended look, layout, copy, and interaction of each window. They are
**not** production code to copy.

Your target is the **existing repo**: `KLCode.pyRevit/`, a pyRevit extension whose
UI is **WPF rendered inside Autodesk Revit**, built in C#. Recreate these designs in
that environment:

- Family Studio is a WPF `Window` (`src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/FamilyStudioWindow.cs`).
  Move it to **XAML + a ViewModel** (the PLAN already names `FamilyStudioViewModel`,
  `FamilyDetailViewModel`, and a `KLCode.FamilyStudio.UI` project with `Views/`,
  `ViewModels/`, `Resources/`). Style it with the shared green theme
  (`lib/GUI/Resources/WPF_styles.xaml`), the same resource dictionary the shipped
  green dialogs use.
- Startup Importer's review is a `TaskDialog`
  (`src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.Revit/StartupImportCommand.cs`).
  Replace it with WPF windows in the planned `KLA.ModelStartupImporter.UI` project.

Do **not** ship the HTML, and do **not** hand-roll colors — bind to `WPF_styles.xaml`
brushes/styles so these windows match the rest of the extension exactly.

## Fidelity

**High-fidelity.** Final colors, type, spacing, radii, copy, and interaction are all
here and all drawn from the KLCode design system. Recreate pixel-for-pixel in WPF
using the green-theme resource dictionary. Where a value below is a hex literal, it
corresponds to a named brush in `WPF_styles.xaml` (mapping in **Design Tokens**) —
bind the brush, don't paste the hex.

## The green-theme chrome (every window shares this)

Borderless WPF window (`WindowStyle="None"`, `AllowsTransparency="True"`,
`ResizeMode="NoResize"`), solid flat `#1A252B`, dragged by its header. No shadows in
markup (the OS supplies the window drop shadow), no gradients except the checkbox
fill, no animation.

- **Header band** — 24–25px, `Grid` with columns `120px | 1fr | 66px`.
  - Left, col 1: brand lockup `/KLCode` — the `/` in KLGreen `#33714F`, `KLCode` in
    KLWhite `#E5E4E2`, font **Audiowide** 16px (`assets/fonts/Audiowide-Regular.ttf`;
    logo use only — never for UI text). `margin-left:5px`.
  - Center, spanning all cols: window title, Segoe UI 14px `#E5E4E2`, centered,
    ellipsis, `max-width: calc(100% - 212px)`.
  - Right, col 3: **Close** button, 60×18, `#286048` fill, 8px radius, Arial 10px
    `#FFFFFF`, hover `#407058`. (Some sub-windows and alerts omit Close.)
- **Footer band** — 24–25px, `Grid` `1fr | 1fr | 1fr`, Segoe UI 12px: left link
  "Prototype" (`#407058`, underlined), center "Version: 2.0" (`#808080`), right link
  "Outreach" (`#407058`, underlined).
- **Group border** ("card") — 1px `#286048`, 10px radius, transparent fill, with a
  green caption (`#33714F`, 12px) notched over the top-left of the border
  (caption sits on the `#1A252B` bg with `padding:0 5px`). No shadow, no tint, no
  left-accent bar.
- **Buttons** — `#286048` fill, 8px radius, Arial, `#FFFFFF` text, hover swaps whole
  fill to `#407058` (no easing). Heights are fixed: 18 (Close), 20 (small), 22
  (toolbar), 28 (action bar), 30 (primary). Widths fixed where the DS specifies:
  60 Close, 100 Select All/None, 150/180/200 primary, 210 in the classic dialog.
  Disabled = `opacity .45`, `cursor:default`.
- **Text input** — `#1A252B` fill, 1px `#33714F` border, 5px radius, Segoe UI 13px
  `#E5E4E2`, no outline.
- **ComboBox / dropdown** — `#1A252B` fill, 1px `#33714F` border, **2px** radius,
  12px `#E5E4E2`, a `#33714F` `▾` at the right. Popup uses WPF's built-in
  `PopupAnimation="Slide"` (the one allowed motion).
- **Checkbox bullet** — 15×15, 2px radius, checked fill is the only gradient in the
  system: `linear-gradient(to top right, rgba(48,112,80,.9), rgba(40,96,72,.85))`
  with a white check; unchecked is transparent with a 1px `#3d5049` border. Hover
  bullet goes near-black `#131313`.
- **List rows** — hover highlight `#4F4F4F`; selected row a green tint
  `rgba(51,113,79,.28)`.
- **Scrollbars** — always visible; track `#286048` 10px radius with 3px margin,
  thumb solid black 8px radius.
- **Status chips** — 1px border + matching text, 8px radius, 10–11px:
  Approved / present / OK = info-green `#3CB371`; Draft / warning / changed =
  warning-gold `#DAA520`; blocking / broken / "off" = KLOrange `#FF8000`;
  neutral / skipped = `#808080` on `#3d5049`.

**Voice for all copy:** terse, imperative, engineer-to-engineer. No "I"/"you", no
marketing, no exclamation marks. Button/title = Title Case; field labels end in a
colon; status sentences are sentence case. The only emoji anywhere is 🔍 in the
filter box.

---

# TOOL 1 — FAMILY STUDIO

Design file: `Family Studio.dc.html` (open in a browser; canvas pans/zooms; six
labeled windows FS-1…FS-6). Source today: `FamilyStudioWindow.cs` (list + detail,
built imperatively). Repo plan for the expanded shell: `KLCode.FamilyStudio.UI`
(`FamilyStudioViewModel`, `FamilyDetailViewModel`).

## FS-1 — Main Browser  *(the primary screen; interactive in the prototype)*

**Purpose:** search/browse the local SQLite catalog, inspect a family or view, and
load / place / batch-load it. Replaces the current single-column list + text-blob
detail with a faceted browser.

**Window:** 1180 × 740. Layout top-to-bottom: header (24) → toolbar → filter row →
body split → action bar → footer (24).

**Toolbar** (`padding:8px 10px 6px`, `flex`, `gap:8px`, `align-items:center`):
1. **Families / Views** segmented toggle — 1px `#286048` border, 8px radius,
   overflow hidden; active segment `#286048`/`#FFF`, inactive transparent/`#9db3a8`;
   each 22px tall, Arial 12px. *(Views mode is the Axiom v7 headline feature — the
   catalog also stores `content_kind='drafting_view'`; see Boundaries.)*
2. **Search field** — flex:1, 22px, `#1A252B`, 1px `#33714F`, 5px radius; 🔍 13px
   then an input, placeholder `Search name, category, type, parameter, tag…`.
3. **This Project / Library** segmented scope toggle (same style as #1). Scopes the
   search to families/views already in the open model vs. the configured library.
4. **≣ List / ▦ Grid** segmented view-mode toggle (same style).
5. **Refresh Library** button — 22px, padding `0 10px`.

**Filter row** (`padding:0 10px 8px`, wrap): label+ComboBox pairs, each label Segoe
12px `#E5E4E2` ending in a value the combo shows:
- `Category:` combo 150w → "All categories"
- `Type:` combo 130w → "All types"
- `Parameter:` combo 130w → "All parameters"
- `Root:` combo 190w → "All configured roots"
- a **Duplicates / variants** checkbox (14px bullet + label)
- a **Clear Filters** text link (`#407058`).
Combos are 20px tall, 2px radius. These are the exact facets already in
`FamilyCatalogFilterOptions` / `FamilySearchQuery`.

**Body split** — `Grid` `1fr | 460px`, `padding:0 10px`.

*Left — results panel:*
- caption row: left `Families`/`Views` in `#33714F` 12px; right count `#808080` 12px
  (`9 families`, `6 views`).
- results container: 1px `#286048`, 10px radius, `#1A252B`, `padding:5px`,
  vertical scroll.
- **List mode** rows: `flex`, `gap:8px`, 6px pad, 8px radius, selected bg
  `rgba(51,113,79,.28)`. Each row = a **checkbox** (batch select; 15px bullet), a
  two-line text block (name `#FFFFFF` 12px ellipsis; sub `#808080` 11px = category ·
  type for families / category · file for views), and an optional **flag chip** on
  the right (sibling count in KLOrange `#FF8000`, or `!` in gold `#DAA520` for a
  preview/index issue). Clicking the row selects (drives detail); clicking the
  checkbox toggles batch membership (independent).
- **Grid mode**: 3-column `grid`, `gap:8px`. Each card = 1px border (`#286048`, or
  `#33714F` + faint green fill when selected), 10px radius, 6px pad; a 4:3 preview
  box (`#10171b`, 1px `#286048`, 3px radius) with the batch checkbox top-right and
  the flag chip top-left; then name `#FFFFFF` 11px and category `#808080` 10px.
- The preview boxes are **placeholders** in the prototype (a monospace glyph label).
  In-product they render the cached PNG preview
  (`%LOCALAPPDATA%\KLCode\FamilyStudio\Thumbnails`, 4:3, produced by Refresh Library).

*Right — detail / preview pane* (`overflow-y:auto`, `flex column`, `gap:8px`):
- 4:3 preview box (1px `#286048`, 10px radius) — the selected type's cached preview.
- family name — `#E5E4E2` 14px, weight 600.
- chip row: **status** chip (Approved=`#3CB371` / Draft=`#DAA520`), plus category and
  discipline chips (`#808080` text, 1px `#33714F`, 8px radius).
- **Type group** (bordered, caption "Type"): a ComboBox of type names, then three
  buttons **Duplicate · Rename · Edit Type…** (each 20px, flex:1), then a
  key/value list of that type's Revit **type parameters** (11px; key `#808080`,
  value `#E5E4E2`, right-aligned). *(Inline duplicate/rename/edit type = Axiom
  feature; wire to a Revit transaction. Keep instance-parameter definitions visibly
  separate from type-parameter values, as the current tool already does.)*
- **Tags group** (bordered, caption "Tags"): tag chips (`#22303a` fill, 1px
  `#286048`, 8px radius, each with a `✕` remove), plus a dashed **+ Add tag** chip
  (`#407058`, 1px dashed `#33714F`). Tags are local SQLite (`family_tags`) — not a
  shared approval system.
- meta block (11px `#808080`, values `#9db3a8`): Path, Modified · Revit version,
  Catalog check (Unique in `#3CB371`, else `#DAA520`).

**Action bar** (`padding:8px 10px`, flex, gap:8): **Load** · **Load & Place** ·
**Batch Load (n)** (disabled until ≥1 checkbox; label shows count) · spacer · **★
Favorite** · **Copy Path** · **Open Folder**. All 28px. These map 1:1 to the current
`RunSelected`, `ToggleFavorite`, `CopyPath`, `OpenFolder`; **Batch Load** is new —
iterate the checked set through the load service inside one transaction group.

### FS-2 — Duplicate & Variant Resolver
640 × 520. Opened from the "3" sibling flag or the Duplicates filter. Intro line
states the counts (e.g. "3 files share this family name. 2 are byte-identical; 1 is a
same-name variant"). A scroll list of candidate rows, each a bordered group with a
**radio** (2px square, `#33714F` border, filled dot for the chosen authoritative
copy), the path, and a status chip: **AUTHORITATIVE** (`#286048`), **EXACT
DUPLICATE** (gold `#DAA520`), **VARIANT — DIFFERENT BYTES** (orange `#FF8000`), plus a
meta line (Modified · Revit version · SHA · sibling/diff note). Action bar:
**Compare Params** (left) · spacer · **Mark Authoritative** (200×30 primary).
**Non-destructive only** — never deletes, renames, overwrites, or auto-selects
(SPEC boundary). "Mark Authoritative" records a local preference, nothing more.

### FS-3 — Library Roots · Config Editor
640 × 470. In-app editor over the operator-owned JSON
(`%APPDATA%\KLCode\FamilyStudio\library.json`, shown as a subline). Scroll list of
root cards, each: an **enabled** checkbox, the root path (`#FFFFFF` 12px), a validity
chip (`VALID · 1,284 rfa` green / `DISABLED` gold / `UNREACHABLE` gold-bordered), and
a meta line (Discipline, Default status, Last scan). A disabled root is `opacity .65`;
an unreachable root uses a gold border + inline gold warning. Action bar: **+ Add
Root…** · **Validate All** · spacer · **Save to JSON**. Must **not** introduce shared
root administration or put operator paths in Git — it only edits the local JSON.

### FS-4 — Refresh Library · Progress + Summary
Two 440 × 300 windows shown side by side.
- **Progress:** intro ("runs in the background; Revit stays responsive"), a per-root
  progress bar (track `#10171b`/1px `#286048`/8px radius; fill `#33714F`), a counts
  line (`Seen 842 · updated 61 · skipped 779 · preview issues 2` with updated in
  `#3CB371`, issues in `#DAA520`), a monospace live file log (`#9db3a8` on `#10171b`),
  and a **Cancel** button (200×30). The refresh service already takes a cancellation
  token.
- **Summary:** this is the **KL&A Alert** format — the one window with a 1px `#286048`
  border. 34px icon roundel (2px `#DAA520` ring, gold `!` 22px), bold green heading
  ("Refresh complete — 2 issues"), message body listing per-file issues (preview
  render failed → prior preview retained; no prior preview → indexed without one),
  and a 55px OK band (top border `#286048`) with a 200×30 **OK**.

### FS-5 — Empty Result State
700 × 360. Header + the search field showing the query, then a bordered panel filling
the body with centered copy: "No families match this search." + a muted explanation
naming the query, and two buttons **Clear Filters** / **Refresh Library**. (The DS has
no empty-state art — text only.)

### FS-6 — Web Catalog Connector  *(concept — vendor-neutral)*
700 × 520. A gold-bordered banner states the rule up front: results come from a
configured manufacturer endpoint and are **placed directly — never copied into the
Family Studio local catalog, nothing redistributed**, governed by each vendor's
license. A vendor ComboBox ("Simpson Strong-Tie"), a search field, a live
`● Connected` indicator (`#3CB371`), a 3-col result grid of vendor parts (4:3
placeholder + name + "latest"), and a footer **Place in Model**. **This is a design
concept, not a shippable feature** — see Boundaries; the Simpson track is
research-only and there is no supported catalog API.

## Family Studio — state & data

ViewModel state: `mode` (Families|Views), `viewMode` (List|Grid), `scope`
(Project|Library), `searchText`, the four facet selections + duplicates flag,
`selectedId`, `checkedIds` (batch set), `selectedTypeIndex`. Everything reads from the
existing `IFamilyRepository` (`Search`, `GetFilterOptions`, `GetDetail`,
`GetFavorites`, `GetRecent`, `SetFavorite`, `RecordUse`) — add repository methods for
Views (`content_kind='drafting_view'`), tag add/remove, batch load, and
authoritative-copy preference. Load/Place go through `IFamilyLoadService` and
`KlaFamilyLoadOptions` (default: keep project values). Refresh stays the explicit
Revit metadata/preview pass; the desktop indexer stays filesystem-only.

---

# TOOL 2 — STARTUP IMPORTER

Design file: `Startup Importer.dc.html` (windows SI-1…SI-6). Source today:
`StartupImportCommand.cs` (two `OpenFileDialog`s → `TaskDialog` review → `TaskDialog`
result). Host-independent parsing/matching already exists in
`KLA.ModelStartupImporter.Core` (`StartupDocumentReader`, `ImportPlanBuilder`,
`ContentCatalog`, `JsonStartupSettingsProvider`, review classification). Build the new
UI in the planned `KLA.ModelStartupImporter.UI`.

### SI-1 — Checklist & Settings Picker
560 × 470. Replaces the two native `OpenFileDialog`s with one green-theme window.
Three bordered groups:
- **Startup Checklist** — a read-only path field + **Browse…** (70×22), then a green
  validity line: `● Valid · 6-column contract found on sheet "Checklist" · SHA-256
  4a9f…c2`. (Reuse the `.docx`/`.xlsx` reader + hash.)
- **Settings JSON** — path field + **Browse…**, then a meta block: resolved **Seed
  model** path with a reachability chip, **Catalog** file + version. (From
  `JsonStartupSettingsProvider`.)
- **Destination** — states the active project name (read-only fact).
Footer action row: muted note "Nothing is created until you review." · **Cancel** ·
**Review Import →** (150×30 primary).

### SI-2 — Review · item picker with live preview  *(centerpiece; replaces the TaskDialog)*
860 × 640. A summary chip strip (matched `#3CB371`, already-present `#808080`,
unchecked `#808080`, and a right-aligned `Catalog 2026.08 · SHA…` chip). Body is a
`Grid` `1fr | 300px`:
- **Item table** (bordered, 10px radius): sticky header row on `#22303a`
  (`#33714F` 11px, weight 600) with columns `26 | 78 | 1fr | 96 | 104` =
  checkbox / **Item ID** (Consolas 11px) / **Title** / **Category** / **Status**.
  Rows are the checklist items; selected row tinted `rgba(51,113,79,.22)`. Status is
  a chip: **Matched** (`#3CB371`), **Existing** (`#808080`; skipped, never
  overwritten), **Unchecked** (`#808080`). Checkbox reflects selected-for-import.
  These are exactly `ImportPlanBuilder`'s classes (Matches / ExistingMatches /
  SkippedItems).
- **Preview / targeting** column: caption ("Selected · D-001"), a 4:3 seed-view
  preview placeholder, the title, then a **Placement target** group — a **Drafting
  View / Sheet** segmented toggle and the resolved new-view name + "Source scale &
  content preserved · native, editable", then a **requires** line naming the catalog's
  `requiredTextTypeNames` / `requiredLineStyleNames` with a present/absent chip.
Action bar: **Select All** · **Select None** · muted "6 will be created · full
rollback on any failure" · spacer · **Cancel** · **Import 6 Items** (180×30).

### SI-3 — Review · blocking issues
560 × 520. When unknown/duplicate ids exist. Gold banner (`!` + "Resolve the checklist
issues before importing."). Then bordered groups: **unknown ids** (orange `#FF8000`
border, Consolas list of id · title), **duplicate ids** (gold border, "selected 3× …
all excluded from matches"), and an info group ("4 items still importable"). Action
bar: **Copy Issue Report** · spacer · **Import blocked** (disabled, `.45`). Unknown and
duplicate ids block Import (SPEC).

### SI-4 — Placement & Split · live extents  *(from Axiom Office Importer; concept-level for schedules/notes)*
720 × 520. For a note/schedule placement. `Grid` `250px | 1fr`:
- **Controls** column: **Target** group (Sheet/Drafting-View segmented + a target
  ComboBox), **Split** group (Columns stepper `3`, Spill-to-sheets `Auto`, a
  "Keep link to source doc" checkbox), **Text mapping** group (exact point-size map,
  e.g. `Word 10 pt → 3/32"`, `12 pt → 1/8"`; bold/italic/underline preserved).
- **Live extents preview**: a `#0d1418` panel drawing a mini sheet (title block, a
  dashed print-margin, and 3 content columns) where columns that fit are green
  (`#407058`) and the overflow column is orange (`#FF8000`) labeled "spills →", with a
  caption "3 columns fit · col 3 spills to S-002 · paste stays within border". This
  mirrors Axiom's live-extents paste. Action bar: note · **Cancel** · **Place**.

### SI-5 — Update Startup Links · sync manager
720 × 480. Manages the stored source→import links. Intro line explains link + hash
drift detection. A table (`26 | 1fr | 110 | 130` = checkbox / group+source /
items / status): each import group shows its name, source file + SHA subline, item
count, and a status chip — **Up to date** (`#3CB371`), **Source changed**
(`#DAA520`), **Link broken** (`#FF8000`, with "source file not found" subline).
Action bar: **Browse… relink** · muted "1 changed · 1 broken" · spacer · **Close** ·
**Rebuild Selected** (180×30). This is the planned `Update Startup Links` /
`LinkMetadataStore` behavior — **concept-level**: Extensible-Storage identity/version
and rebuild semantics are deferred (see Boundaries).

### SI-6 — Import Summary & Error
Two 440 × 300 **KL&A Alert** windows (1px `#286048` border, 34px roundel, 55px button
band):
- **Success** (info): green `i` roundel (2px `#3CB371`, italic serif `i`), heading
  "Import complete", body "Created items: 6 / Skipped existing: 2 / Catalog version:
  2026.08" + "A source link was stored on each new view", buttons **Open First View**
  / **OK**.
- **Error** (warning): gold `!` roundel, heading "Checklist could not be read", body
  naming the row + bad value (`Row 12 … "maybe"` in Consolas gold) and the accepted
  values, "Nothing was imported.", single **OK** (200×30). Maps to the current
  `IsExpectedInputFailure` path.

## Startup Importer — state & data

ViewModel state: picked checklist path + validity/hash, picked settings path + resolved
seed/catalog/version, the parsed `StartupDocumentModel`, the `ImportPlan`
classification, per-item selected-for-import set, per-item placement target
(view|sheet) + split settings, and the review's blocking flag. Import runs in one
transaction group with full rollback (existing `RevitStartupImportService`). The
Update-Links manager reads stored `LinkMetadata`, recomputes the checklist hash, and
flags changed/broken/current per group.

---

## Design Tokens  (hex → `WPF_styles.xaml` brush)

Bind brushes; the hex is for reference only.

| Token | Hex | Use |
|---|---|---|
| KLCharcoal | `#1A252B` | every window/header/footer/field/list bg |
| KLGreen (`text_green` / `border_green`) | `#33714F` | labels, input borders, icons, `/` in mark |
| KLGreen-dark (`border_green_dark` / `checkbox_checked_colour`) | `#286048` | button fill, panel/list borders, checked state, scroll track |
| KLGreen-secondary (`footer_donate`) | `#407058` | button hover, footer links |
| KLWhite | `#E5E4E2` | body text (never pure white) |
| Pure white | `#FFFFFF` | button text, list-item names |
| Gray | `#808080` | muted text, version string |
| KLOrange | `#FF8000` | "off"/blocking/variant chips, sibling flag |
| Warning-gold | `#DAA520` | `!` warning glyph, changed/draft chips |
| Info-green | `#3CB371` | `i` info glyph, valid/approved/up-to-date chips |
| (derived) panel-inner | `#10171b` / `#0d1418` | preview boxes, progress track, extents canvas |
| (derived) chip-neutral border | `#3d5049` | unchecked checkbox border, neutral chip |
| (derived) header-row / tag fill | `#22303a` | table header rows, tag chips |
| (derived) subvalue ink | `#9db3a8` | path/value text inside muted lines |

**Radii:** panels/lists/scroll-track 10px · buttons/scroll-thumb 8px · text box 5px ·
checkbox/ComboBox 2px · alert roundel 50% (34px). **Native surfaces: 0** (not used
here — everything is green theme).

**Type:** Segoe UI for all UI (10/11/12/13/14; 16 & 22 only in the alert heading/
glyph). Arial on buttons. Consolas/monospace for ids, hashes, file logs, the extents
labels. Audiowide only for the `/KLCode` mark. Weights: regular, SemiBold (section/
grid headers), Bold/Heavy (wordmark, alert heading).

**Spacing:** dialog margins 2 / 5 / 10; chrome bands 24–25px; control heights 18/20/
22/25/28/30; fixed widths 60/100/150/180/200/210. Nothing stretches to fill; nothing
is responsive (fixed-size windows).

**Motion:** none. Instant color swaps on hover. The only allowed animation is the
ComboBox popup's built-in `PopupAnimation="Slide"`.

## Assets

- **Font:** `assets/fonts/Audiowide-Regular.ttf` (logo mark only).
- **Logo:** `assets/logos/KLCodeLogo.png`, wordmark lockups (Audiowide).
- **Icons:** the reusable library `assets/icons/lib/` (29 × 96px masters, four
  colorways `_dark`/`_light`/`_green`/`_orange`, named `<icon>_<size>px_<color>.png`).
  Draw any new glyph to **Lucide**'s visual language (simple outline, consistent
  stroke); export the needed colorway PNG — **never redraw an icon as SVG**.
  The prototype uses CSS placeholder boxes and unicode `▾ ✕ ★ ≣ ▦` where a real icon
  would go — swap in the library PNG in-product. Only 🔍 (filter) is a literal glyph
  the DS keeps.
- **Previews:** family/view/seed preview boxes are placeholders in the prototype;
  in-product they are the cached PNGs from Refresh Library
  (`%LOCALAPPDATA%\KLCode\FamilyStudio\Thumbnails`, 4:3).

## Files in this bundle

- `Family Studio.dc.html` — FS-1…FS-6 (FS-1 interactive: toggles + selection wired).
- `Startup Importer.dc.html` — SI-1…SI-6 (SI-2 table rows data-driven).
- Open either in a browser; the canvas pans (drag) and zooms. These are the visual
  source of truth alongside this README.

## Repo touchpoints (where to build)

- Family Studio shell → `src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/Views/`
  (today `FamilyStudioWindow.cs`), plus the planned `KLCode.FamilyStudio.UI`
  (`Views/`, `ViewModels/`, `Resources/`). Repository: `IFamilyRepository` /
  `SqliteFamilyRepository`. Load: `IFamilyLoadService` / `KlaFamilyLoadOptions`.
- Startup Importer UI → planned `KLA.ModelStartupImporter.UI`; command entry
  `StartupImportCommand.cs`; core parsing/matching in
  `KLA.ModelStartupImporter.Core`; import in `RevitStartupImportService`.
- Shared green theme → `lib/GUI/Resources/WPF_styles.xaml` (bind, don't fork).
- Both tools stay in `KL&A Tools_dev.tab/05 DevSandbox.panel/` until the live-Revit
  gates in each `PLAN.md` pass.

## Boundaries — read before building  *(from the tools' own PLAN.md / SPEC.md)*

These are **hard governance limits**, not oversights in the design:

1. **Simpson / Web Catalog Connector (FS-6) is research-only and vendor-neutral.**
   No supported Simpson catalog API exists. Do **not** bulk-crawl, download RFAs,
   bypass controls, capture credentials, redistribute content, or add any vendor
   result to the Family Studio local catalog. Ship it only as the generic,
   place-direct concept shown, if at all.
2. **Duplicate/variant handling is non-destructive.** Never delete, rename, overwrite,
   merge, or auto-select a family. "Mark Authoritative" is a local preference only.
3. **Library roots stay operator-owned JSON.** The in-app editor edits that local file;
   no shared root administration, no operator paths in Git.
4. **Favorites, recent, tags are local SQLite** — not a company approval/curation
   system.
5. **Desktop indexer stays filesystem-only.** Only the explicit Revit **Refresh
   Library** opens family documents and renders previews.
6. **Startup import is create-only with full rollback.** Unknown/duplicate ids block;
   existing targets are skipped, never overwritten; any post-transaction-group failure
   rolls the whole run back.
7. **Update Startup Links (SI-5) and Placement/Split (SI-4) are concept-level.**
   Extensible-Storage identity/version, created-element tracking, rebuild semantics,
   multi-column note/schedule splitting, and PDF intake are **deferred** in the repo —
   design them, but gate implementation behind owner-defined catalog/seed/identity
   contracts and live-Revit validation.
8. **Two themes never mix.** Everything here is the green theme (summoned/dismissed
   windows). Don't pull native-white Revit chrome into these surfaces.
9. **No hard-coded user-facing strings.** Put copy in the per-locale
   `ResourceDictionary` (the extension ships 8 languages); reference it.
10. **DevSandbox gate.** Neither tool promotes out of `05 DevSandbox.panel` until the
    Windows packaging + live Revit 2024/2025 validation in each `PLAN.md` passes.
