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
