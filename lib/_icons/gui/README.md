# Shared in-window icons

This folder owns approved GUI artwork. Ribbon icons remain in the parent folder.
The owner selected the Lucide family, mappings and lighter outline treatment on
2026-10-28. [source.json](source.json) pins the upstream revision and appearance;
[LICENSE.lucide.txt](LICENSE.lucide.txt) retains the upstream attribution/notices.

- `svg/` contains the original approved SVG sources.
- `KLCodeIcons.xaml` is generated framework-native WPF geometry only (one
  `Kla<Role>Geometry` per role) — a leaf with no brushes. Windows need no SVG
  renderer or added runtime package.
- `scripts/generate_gui_icons.py` owns semantic role mappings and generation. It
  also writes the `KlaIcon<Role>` ImageSources into the `generated-icons` block
  of `lib/GUI/Resources/KLCodeFoundation.xaml` (drawn with the foundation's
  `KlaGuiIconPen` and `KlaTextBrush`) and the wordmark geometry in
  `lib/_logos/KLCodeWordmark.xaml`. Run it after changing sources; `--check`
  detects stale generated resources.

`KLCodeFoundation.xaml` merges the geometry and owns the presenter, pen and
ImageSources, bound to tokens (`KlaIconSize`, `KlaIconCanvas`, `KlaIconStroke`,
`KlaTextBrush`, `KlaDisabledTextBrush`). Use `KlaIconSearch` as an Image.Source,
or a foreground-aware presenter:

```xml
<ContentControl Style="{StaticResource KlaGuiIcon}"
                Content="{StaticResource KlaSearchGeometry}"/>
```

The presenter uses 16-unit dimensions and a 24-unit source canvas, with a 1.5
stroke. Foreground inherits from its parent control; disabled icons use the
shared `KlaDisabledTextBrush`. Decorative icons do not intercept clicks or focus.
Do not create per-window copies or replace source SVGs with screenshots.

| Semantic role | Geometry | ImageSource |
| --- | --- | --- |
| Search | KlaSearchGeometry | KlaIconSearch |
| Text/filter mode | KlaTextFilterGeometry | KlaIconTextFilter |
| Regex | KlaRegexGeometry | KlaIconRegex |
| Clear search | KlaClearSearchGeometry | KlaIconClearSearch |
| Read element | KlaReadElementGeometry | KlaIconReadElement |
| Read view filters | KlaReadViewFiltersGeometry | KlaIconReadViewFilters |
| Filter plus element | KlaFilterElementGeometry | KlaIconFilterElement |
| Pick element | KlaPickElementGeometry | KlaIconPickElement |
| Rectangle selection | KlaRectangleSelectionGeometry | KlaIconRectangleSelection |
| Current selection | KlaCurrentSelectionGeometry | KlaIconCurrentSelection |
| List view | KlaListViewGeometry | KlaIconListView |
| Grid view | KlaGridViewGeometry | KlaIconGridView |
| Favorite | KlaFavoriteGeometry | KlaIconFavorite |
| Information | KlaInformationGeometry | KlaIconInformation |
| Warning | KlaWarningGeometry | KlaIconWarning |
| Error/blocking | KlaErrorGeometry | KlaIconError |
| Success | KlaSuccessGeometry | KlaIconSuccess |

Message headings may use feedback symbols where applicable. Existing status
chips retain words and borders. Larger Browse/Reset/Copy/Open Folder actions
remain text-only. Icon artwork does not change a tool's classification or
operation. Compiled hosts package this same dictionary through their adapter.
