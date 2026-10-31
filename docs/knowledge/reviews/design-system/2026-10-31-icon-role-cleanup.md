# GUI icon role cleanup — 2026-10-31

Baseline: `f80ac94`. The owner reorganised the generated GUI icon roles in
[generate_gui_icons.py](../../../../scripts/generate_gui_icons.py); the
[icon catalog](../../../../lib/_icons/gui/README.md) lists the result.

- Keys are now `klgeo<Role>` (geometry, `KLCodeIcons.xaml`) and `klicon<Role>`
  (DrawingImage, the Foundation `generated-icons` block), replacing
  `Kla<Role>Geometry` and `KlaIcon<Role>`.
- Severity and chevron roles are renamed: InfoAlert, WarnAlert, ErrorAlert,
  SuccessAlert, ChevRight, ChevDown; Family Studio's are List, Grid, Fav.
- Roles used only by the dormant Match recall window carry a Future prefix:
  FutureFilterList, FutureRegex, FutureClearSearch, FutureTags, FutureRead,
  FutureFilterFunnel, FuturePointer, FutureRectSelect.
- Merged and removed: Error (circle-x) into ErrorAlert, so the compiled alert and
  the Startup Importer's blocking issues now draw octagon-alert; the unused
  Success role and circle-check; FutureCurrentSelection into SuccessAlert (both
  check-check). 19 roles over 19 SVGs.

Every consumer was moved to the new keys: the shared dialogs and Details
styles, CustomAlert, SelectFromDict, the Review template, Steel PSF, the dormant
windows, the compiled alert, Startup Importer and Family Studio windows, the
Gallery alert preview, the Windows probes, tests and docs.

Verification (macOS): regeneration and `--check` pass; every `klgeo` / `klicon`
key referenced in the repository is defined by the generated files; 433 Python
tests with the one existing macOS path-case failure; every XAML file parses;
C# source contracts 17 of 17; scale lint and metadata audit clean.

Limits: nothing was rendered. The compiled add-ins compile the icon dictionary
in, so they need a rebuild to pick up the new keys; packaged DLLs are unchanged.
Run `validate_ui_production_wpf.py`, `validate_ui_message_variants_wpf.py`,
`validate_ui_dialogs_wpf.py` and the Gallery probe on Windows.

## Geometry is the only icon form

The generator no longer writes `klicon<Role>` ImageSources, and the Foundation
loses its `generated-icons` block, the markers and the image-only
`KlaGuiIconPen`. Only `kliconSearch` had consumers: SelectFromDict, the Review
template, Create From Rooms, Steel PSF and compiled Family Studio drew the
filter-box search mark as an `Image`. Each is now a `KlaGuiIcon` presenter with
`klgeoSearch`, so the mark follows the surrounding foreground (KLWhite in these
windows, the same colour as before) and turns gray when disabled. The compiled
smoke test checks the Search geometry instead of the image; the production
probe asserts no `klicon` resource exists. `generate_gui_icons.py` has two
outputs: `KLCodeIcons.xaml` and the wordmark.

Verification (macOS): regeneration and `--check` pass; all 19 `klgeo` keys
referenced in the repository resolve; every XAML file parses; 432 Python tests
with the one existing macOS path-case failure; C# source contracts 17 of 17; the
Windows smoke project builds. Not rendered; the five windows' filter rows should
be compared with their earlier renders on Windows.

## Final key prefix and file name

The owner then set the geometry key prefix to `klicon<Role>` (the image form it
once named no longer exists) and renamed the generated dictionary to
`lib/_icons/gui/klIcons.xaml`. Every consumer, the Foundation merge, the
compiled `KLCode.Wpf` page link and its source contract, the probes, tests and
docs follow. All 19 generated keys are referenced and every reference resolves;
432 Python tests with the one existing macOS path-case failure; C# source
contracts 17 of 17; the Windows smoke project builds.

## The KLCode logo moves into klIcons.xaml

The wordmark dictionary `lib/_logos/KLCodeWordmark.xaml` existed only because
the shared primitives needed the logo without the rest of the foundation. The
generator now writes the logo into `klIcons.xaml` with `klcLogo` keys
(`klcLogoSlash`, `klcLogoLetters`, `klcLogoOrigin`, `klcLogoCanvasWidth`,
`klcLogoCanvasHeight`), and the shared primitives' DataTemplate is `klcLogo`.
`KLCodeSharedPrimitives.xaml` merges `klIcons.xaml` once; the Foundation gets it
through the primitives instead of merging it a second time. The old file, its
compiled page link and the generator's second output are gone. The header's
layout tokens are renamed to match: `klcLogoWidth` / `klcLogoHeight` (70 x 12). Verification: 25 generated keys, every reference resolves; 432
Python tests with the one existing macOS failure; C# source contracts 17 of 17;
the Windows smoke project builds. Not rendered.

## klcLogo.svg at 128 x 18

The logo source is now `lib/_logos/klcLogo.svg` (1024 x 146 view box; the
outlines sit in one group with a slight non-uniform scale and offset). The
generator takes the canvas from the view box and writes the group transform,
unrounded, as `klcLogoTransform` (a MatrixTransform replacing `klcLogoOrigin`);
it refuses rotation or skew and checks the transformed outlines stay inside the
view box. `klIcons.xaml` now lives in `lib/GUI/Resources` (owner move); the
compiled page link and source contract follow. The `klcLogo` template and the
`klcLogoWidth` / `klcLogoHeight` tokens are 128 x 18; at that size the 1024 x 146
artwork fits 126.2 x 18, centred. `KlaHeaderSideColumn` widens from 86 to 136
(8 inset + 128) so the logo is not clipped and the title stays centred; the
centred title area of every shell window shrinks by 100, to 74 in the 346-wide
KLC-Rename. The production probe now compares the template with a direct render
of klcLogo.svg at 128 x 18. Verification as before: 24 generated keys resolve;
432 Python tests with the one existing macOS failure; C# source contracts 17 of
17; smoke project builds. Not rendered.
