# Shared in-window icons

This folder owns approved GUI artwork. Ribbon icons remain in the parent folder.
The owner selected the Lucide family, mappings and lighter outline treatment on
2026-10-28. [source.json](source.json) pins the upstream revision and appearance;
[LICENSE.lucide.txt](LICENSE.lucide.txt) retains the upstream attribution/notices.

- `svg/` contains the original approved SVG sources.
- `KLCodeIcons.xaml` is generated framework-native WPF geometry only (one
  `klgeo<Role>` per role) — a leaf with no brushes. Windows need no SVG
  renderer or added runtime package.
- `scripts/generate_gui_icons.py` owns semantic role mappings and generation. It
  also writes the wordmark geometry in `lib/_logos/KLCodeWordmark.xaml`. Run it
  after changing sources; `--check` detects stale generated resources.

`KLCodeFoundation.xaml` merges the geometry and owns the presenter, bound to
tokens (`KlaIconSize`, `KlaIconCanvas`, `KlaIconStroke`, `KlaDisabledTextBrush`).
The presenter is the only way to draw a GUI icon: it follows its parent's
foreground and turns gray when disabled. There are no fixed-color ImageSources
(removed 2026-10-31).

```xml
<ContentControl Style="{StaticResource KlaGuiIcon}"
                Content="{StaticResource klgeoSearch}"/>
```

The presenter uses 16-unit dimensions and a 24-unit source canvas, with a 1.5
stroke. Foreground inherits from its parent control; disabled icons use the
shared `KlaDisabledTextBrush`. Decorative icons do not intercept clicks or focus.
Do not create per-window copies or replace source SVGs with screenshots.
See the [design-system usage examples](../../../docs/DESIGNSYSTEM.md#in-window-gui-icons)
for icon-only and icon/text actions, fixed-color images and accessible naming.

| Semantic role | Geometry | Status |
| --- | --- | --- |
| Search | klgeoSearch | Shared dialogs and live windows |
| Group / sheet set | klgeoGroup | Shared dialogs |
| Information | klgeoInfoAlert | Shared dialogs, CustomAlert, compiled alert |
| Warning | klgeoWarnAlert | Shared dialogs, CustomAlert, compiled alert |
| Error | klgeoErrorAlert | Shared dialogs, compiled alert, Startup Importer blocking issues |
| Success | klgeoSuccessAlert | Shared dialogs; the recall window's current-selection action |
| Collapsed Details | klgeoChevRight | Shared dialogs |
| Expanded Details | klgeoChevDown | Shared dialogs |
| List view | klgeoList | Compiled Family Studio |
| Grid view | klgeoGrid | Compiled Family Studio |
| Favorite | klgeoFav | Compiled Family Studio |
| Text/filter mode | klgeoFutureFilterList | Future |
| Regex | klgeoFutureRegex | Future |
| Clear search | klgeoFutureClearSearch | Future |
| Read element (tags) | klgeoFutureTags | Future |
| Read view filters | klgeoFutureRead | Future |
| Filter plus element | klgeoFutureFilterFunnel | Future |
| Pick element | klgeoFuturePointer | Future |
| Rectangle selection | klgeoFutureRectSelect | Future |

The **Future** prefix marks roles used only by the Match recall window in
`lib/GUI/_future/match`, which no tool opens. Give a role its plain name again
when a live window adopts it. A role with no consumer is removed with its SVG.

Message headings may use feedback symbols where applicable. Existing status
chips retain words and borders. Larger Browse/Reset/Copy/Open Folder actions
remain text-only. Icon artwork does not change a tool's classification or
operation. Compiled hosts package this same dictionary through their adapter.

Shared Message uses [Octagon Alert](https://lucide.dev/icons/octagon-alert) and
[Check Check](https://lucide.dev/icons/check-check) through its own error/success
roles. Since 2026-10-31 the error role also serves the compiled alert and the Startup Importer's blocking issues; Circle X is retired.
Information and Warning retain Info and Triangle Alert. Message severity symbols
render at 24 units in the severity color; Details uses 16-unit
[Right](https://lucide.dev/icons/chevron-right)/[Down](https://lucide.dev/icons/chevron-down)
chevrons for collapsed/expanded state. All 19 roles retain the existing pinned
source revision and license; the default presenter remains 16 units.

The Group role uses [Lucide Layers-2](https://lucide.dev/icons/layers-2), chosen
for the owner-requested shared-selector group dropdown on 2026-10-29. Its stack
of sheets distinguishes grouping from Search while using the same presenter
size, canvas and stroke. The [source SVG](https://github.com/lucide-icons/lucide/blob/be09619c1c1124ad09c19fc3e87ee3b939409bbd/icons/layers-2.svg)
comes from the existing pinned revision. It contains two paths, requires no
transform or renderer changes, and is covered by the retained Lucide ISC notice.
The original SVG keeps its upstream stroke attribute; generated WPF uses the
existing 1.5-unit token pen rather than that attribute.
