# PDF Overlay

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.pdf-overlay` |
| Tool version | `v0.0` |
| Status | Unreleased prototype; live acceptance pending |
| Status/origin | Prototype; KL&A custom tool. |
| Main delivery | Unreleased |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/PDF Overlay.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/PDF Overlay.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/PDF Overlay.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/PDF Overlay.pushbutton/script.py`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/PDF Overlay.pushbutton/PdfOverlayPalette.xaml`; `lib/pdf_overlay/` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | Unreleased | 10.28.2026 | First DevSandbox PDF overlay: PDF page import with transparent paper and tinted linework, two-point alignment, and an opacity, color, and visibility palette. | Pending commit on `dev.pdf-overlay`; pending next main delivery. |

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

1. **Import PDF.** The palette's Page and DPI (100, 150, 200, or 300; default
   150) choose what to import. Revit rasterizes the page through
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
3. **Review.** The Opacity slider (0–100%, default 60%) and the Color choice
   (Red, Magenta, Blue, Green, or Original) re-render the PNG and reload it into
   the same ImageType. Its instances are re-placed, so alignment is kept. Show
   overlay hides or unhides the overlay in the active view only.

The palette is modeless and stays open beside Revit. Actions run through an
`ExternalEvent`, one at a time.

## Rendering

Rendering uses one GDI+ `ColorMatrix` pass: output alpha is
`opacity × (1 − luminance)`, so white paper is fully clear and dark linework is
strongest. A tint replaces the RGB with a constant color; Original keeps the
source colors. Rotation is applied in the same pass on a canvas sized to the
rotated page, so the Revit image always stays axis-aligned and the tool does
not rely on rotating image instances.

## Storage and sharing

For each overlay, three files with the same stem are kept in
`%LOCALAPPDATA%\KLA Tools\PDF Overlay\`: `<stem>_source.png` (page raster),
`<stem>.png` (current overlay), and `<stem>.json` (PDF path, page, DPI, page
size, pose, tint, and opacity). The overlay image is embedded in the model, so
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
