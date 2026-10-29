# PDF Overlay

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.pdf-overlay` |
| Tool version | `v0.0` |
| Status | Unreleased prototype; live acceptance pending |
| Status/origin | Prototype; KL&A custom tool. |
| Main delivery | Unreleased |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/PDF Overlay.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/PDF Overlay.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/PDF Overlay.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/PDF Overlay.pushbutton/script.py`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/PDF Overlay.pushbutton/PdfOverlayPalette.xaml`; `lib/pdf_overlay/`; shared `lib/error_reports.py` and `lib/error_reports_revit.py` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | Unreleased | 10.28.2026 | First DevSandbox PDF overlay: PDF page import with transparent paper and tinted linework, two-point alignment, an opacity, color, and visibility palette, and a member size check against the PDF's text labels. | Pending commit on `dev.pdf-overlay`; pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Purpose

Engineers review member sizes by comparing an analysis or drawing PDF (for
example a RAM member-size map or a printed framing plan) with the Revit
framing. This prototype places one PDF page in the active view as a
see-through, tinted image, fits it to the framing with two picked points, and
lets the user blend or blink the two for review.

## Workflow

1. **Import PDF.** The palette's Page and DPI (100, 150, 200, 300, 400, or 600;
   default 150) choose what to import. A rendered page above 160 million pixels
   is refused with the highest DPI that fits (a 36x24 sheet fits at 400 DPI, not
   600), because rendering holds three full-page copies in memory; an
   out-of-memory failure also asks for a lower DPI. Revit rasterizes the page through
   `ImageType.Create` in a transaction that is rolled back after
   `ImageType.GetImage()` copies the pixels, so no page-only type is left in the
   model. The page is flattened onto white and cached locally. The tool renders
   the overlay PNG and places it in the active view as an imported (embedded)
   image on the Foreground draw layer. The page is centered in the visible
   area at the active view's scale. A PDF printed at the same scale as the view
   is therefore already close in size.
2. **Align (2 Points).** The user picks a point on the PDF image (no snaps),
   then the matching model point (normal snaps), twice. Grid intersections far
   apart give the best fit. The tool fits a similarity transform (scale,
   rotation, offset) that puts both PDF points on their model points. It works
   for a partial page or one printed at any scale, because nothing depends on
   the sheet scale. A rotation within 0.5° of a quarter turn snaps to it, and
   scale and position are then fit evenly between the two picks. Before fitting,
   the tool reads the image's current center and width, so a manual move or
   resize in Revit is respected. Align can be repeated to refine. Esc cancels
   without changes.

   The four clicks are numbered steps. The palette status and the Revit status
   bar name the next click ("Step 2 of 4: click the SAME point IN THE MODEL")
   and confirm the last one. Each click leaves a temporary 1/8-inch (printed)
   circle: blue on the PDF, green in the model. The circles are detail lines
   with per-view color overrides, made and deleted in their own transactions,
   and are removed when Align finishes or is cancelled. If a view cannot take
   detail lines, the circles are skipped and the steps still run.
3. **Review.** The Opacity slider (0–100%, default 60%) and the Color choice
   (Red, Magenta, Blue, Green, or Original) re-render the PNG and reload it into
   the same ImageType. Its instances are re-placed, so alignment is kept. Show
   overlay hides or unhides the overlay in the active view only.

4. **Check Members.** Compares framing sizes, studs, and camber in the active
   view with the labels printed in the PDF (see Member check). Members to
   review are selected in Revit and listed in the pyRevit output window.
   **Revise Selected to PDF** changes the selected members to match their
   labels (see Revise to PDF).

5. **Reuse.** The palette has no overlay list; it works on the overlay
   whose PDF image is selected in Revit. It follows
   `UIApplication.SelectionChanged` (Revit 2023+): selecting an overlay image
   makes it current, a selection without images keeps the current overlay (so
   Check Members selecting framing does not change it), and selecting an image
   that is not an overlay says so. The handler only reads the model and is
   removed when the palette closes. At launch the palette uses a selected
   overlay image, else the newest overlay in the active view. The current
   overlay is named by PDF, page, DPI, import time, and whether it is in the
   active view. **Place in View...** lists the overlays that are not in the
   active view and adds the chosen one at its aligned position. This works in
   any view facing the same way as the one it was aligned in, such as another
   plan view; Revit's Copy and Paste Aligned also works, and the pasted image
   is picked up when selected. **Replace PDF...** loads a revised PDF into the selected
   overlay at the same page and DPI, keeping its alignment, color, and opacity.
   If the new page has a different pixel size, the palette says so, because
   the alignment then only holds near the page center. **Remove** deletes the current
   overlay image and all its placements from the model after a confirmation;
   Revit Undo restores it, and its local files are kept.

The palette is modeless and stays open beside Revit. Actions run through an
`ExternalEvent`, one at a time.

## Member check

The labels come from the PDF's text, not the image. `lib/pdf_overlay/pdftext.py`
is a small standard-library PDF reader that runs under IronPython and CPython.
It handles FlateDecode streams, object streams, incremental updates, simple and
Type0 fonts with ToUnicode maps, Form XObjects, and `/Rotate` and CropBox. It
returns positioned words for the overlay's page. Characters are joined into
words by direction (within 3°), baseline, and gap. Encrypted PDFs, scanned
pages, and text exported as outlines have no readable labels; the check then
says so.

Steel sizes are found with one pattern: W, M, S, HP, C, MC, WT, MT, ST, L, 2L,
and HSS shapes, with decimal or fractional dimensions (`HSS5x5x3/8`). Run-together
labels such as `W12x26W12x19` are split, and each part keeps its own glyph
positions. Sizes compare numerically, so case, `X` vs `x`, leading marks
(`*W18x65`), and `3/8` vs `.375` do not matter.

Each label is placed in the view through the displayed page, the raster size,
and the overlay pose. It goes to the nearest structural framing line in the
active view that is within the overlay's **Match within** tolerance: a
distance in feet from the member line (default 2.5 ft, up to 100) and an angle
from the label's direction (default 15°, up to 45°). The palette edits both,
and they are saved with the overlay and printed in the report. Framing comes from a view-filtered collector, using each member's
location curve and the size parsed from its type name, or failing that, its
family and type names. Labels outside an active crop region are ignored.
Results:

- **Size differs**: the member's Revit size differs from its PDF label.
- **Studs differ** / **Camber differs**: the size matches, but the PDF prints a
  stud count or camber that differs from the member's Number of studs or
  Camber Size (to 1/32 in; an empty camber counts as zero). These are
  compared only when the PDF prints them.
- **PDF labels disagree**: two or more labels with different sizes, studs, or
  camber were assigned to one member.
- **Revit size not recognized**: the type name has no steel size to compare.
- PDF labels with no member nearby (a missing member or loose alignment).
  With **Mark labels with no member nearby** ticked (the default), each one
  gets a review mark in the active view: a circle whose radius is the match
  distance, plus a line through it along the label's direction. The report
  lists them by size and position, each linked to select its mark. Unticked,
  the report counts them by size.
- Members with no PDF label (not checked), listed up to 200.

The review members are selected in Revit and listed with clickable ids in the
pyRevit output window. The only model change is the review marks: detail
lines in the active view, drawn in the `PDF Overlay Marks` line style
(orange, weight 6), which the tool creates once. Every check replaces the
view's marks, and **Clear Marks** removes them. Marks are found by that line
style, so Visibility/Graphics can hide them, and lines drawn by hand in that
style are cleared too. Marking and clearing are one undoable transaction. The check reads the PDF
from its original path at check time. A warning is printed if the PDF page
shape and the imported image differ by more than 2%.

### Studs and camber in labels

Text after a size, in the same word or in up to three following words on its
baseline (each within 1.5 text heights, stopping at the next size), is read
for studs and camber. Studs are a count in parentheses or brackets, `(14)` or
`[14]`; split runs such as `(6,8)` are added together. Camber is `c=` with
inches: `3/4"`, `1"`, `1 1/4"`, `1-1/4"`, or `.75`. Other notes such as
`(HIGH)` or `51K` are ignored. Neither sample PDF (a roof RAM map and a roof
framing plan) prints studs or camber, so the formats follow RAM and plan
conventions. Confirm them with a floor PDF before relying on them.

## Revise to PDF

**Revise Selected to PDF** works on the Revit selection, from one member to
many. Check Members selects every member to review, so it can follow a check
directly; deselect any members to keep. It re-runs the check with the current
tolerances so nothing is stale, then plans a change for each selected member:

- **Size**: the loaded framing type whose name gives the label's size,
  preferring the member's own family. A size that is not loaded is reported,
  not created; load the type, then revise again.
- **Studs**: the built-in Number of studs is set to the PDF count.
- **Camber**: the built-in Camber Size is set to the PDF value: inch text
  such as `3/4"` for a text parameter, or a length for a length parameter.

Studs and camber change only where the PDF prints them; a size-only label
leaves them as they are. Members with no label, disagreeing labels, a size
not recognized, or nothing to change are skipped with a reason, as are
selected elements that are not framing in the view. The palette shows the
counts and asks before changing anything. All changes are one undoable
transaction, with each member in its own sub-transaction, so one failure
leaves that member unchanged and the rest still apply. The report lists each
member as it was and as it is now, and the revised members are selected.

## Rendering

Rendering uses one GDI+ `ColorMatrix` pass: output alpha is
`opacity × (1 − luminance)`, so white paper is fully clear and dark linework is
strongest. A tint replaces the RGB with a constant color; Original keeps the
source colors. Rotation is applied in the same pass on a canvas sized to the
rotated page, so the Revit image always stays axis-aligned and the tool does
not rely on rotating image instances.

## Diagnostics

Startup steps and failures are appended to
`%LOCALAPPDATA%\KLA Tools\PDF Overlay\pdf_overlay.log`, because the pyRevit
output window can render blank. A startup failure also shows the error in an
alert. In pyRevit 6, `wpf` must be taken from `pyrevit.framework`, which loads
the engine's IronPython.Wpf assembly; a bare `import wpf` before that fails with
`No module named _wpf`.

Unexpected failures (loading code, startup, any palette action, or following
the selection, the last once per session) also save an error report with
tool code `PDFO` and the action's name, such as `Check Members` or
`Revise to PDF`. The report id is shown in the palette status or startup
alert and copied to the clipboard for the user to paste into Suggestions/Bugs
Feedback. Reports include the last 40 lines of the log above. See
[Error reports](../../../../docs/knowledge/error-reports.md) for contents,
collection, and `scripts/summarize_error_reports.py`.

## Coordinates

View 2D coordinates are measured from the model origin along the view's
right and up directions, not from the view origin. Every view facing the same
way therefore shares one set of overlay coordinates, which Place in View relies
on. State files from before this change (version 1) used the view origin;
every action re-reads the placed image's center before use, so they keep
working.

## Storage and sharing

For each overlay, three files with the same stem are kept in
`%LOCALAPPDATA%\KLA Tools\PDF Overlay\`: `<stem>_source.png` (page raster),
`<stem>.png` (current overlay), and `<stem>.json` (PDF path, page, DPI, page
size, pose, tint, opacity, import time, and match tolerances). The overlay image is embedded in the model, so
other users see it as last rendered. Only the computer that imported it can
re-style or re-align it. Elsewhere the palette lists it as "no local files" and
asks for a re-import. Deleting the image in Revit (Manage Images) leaves the
local cache files.

## Limits

- Works only in views that accept images (`ImageInstance.IsValidView`): plan,
  ceiling, elevation, section, drafting, and similar 2D views. 3D views are not
  supported.
- The overlay is a raster. Small text sharpness depends on DPI; 300 DPI on a
  large sheet makes a large image and slower opacity updates.
- The pose is stored in the active view's right/up coordinates. Copies of the
  overlay placed in views with a different orientation are not supported.
- Requires Revit PDF import support (`OptionalFunctionalityUtils.IsPDFImportAvailable`).

## Validation

`tests/pdf_overlay_test.py` covers the pose math (pixel/view round trip,
two-point fit with and without the orthogonal snap, coincident-pick
rejection, rotated canvas size), the color matrix (paper drop-out, opacity,
tint, Original), and the cache stem and JSON state round trip. Revit-side
behavior (PDF rasterization, ImageType reload, picking, visibility) needs live
acceptance in Revit 2023–2026 using a RAM member map and a partial printed
roof plan before promotion.
