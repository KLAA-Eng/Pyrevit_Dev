# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "PDF Overlay"
__version__ = "v0.0"

import datetime
import math
import os
import traceback
import uuid

# The pyRevit output window can render blank, so startup steps and errors are
# also written to a log file that is readable without Revit.
LOG_PATH = os.path.join(os.environ.get('LOCALAPPDATA') or os.environ.get('TEMP') or '.',
                        'KLA Tools', 'PDF Overlay', 'pdf_overlay.log')


def log(message):
    try:
        folder = os.path.dirname(LOG_PATH)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with open(LOG_PATH, 'a') as log_file:
            log_file.write('{:%Y-%m-%d %H:%M:%S} {}\n'.format(datetime.datetime.now(), message))
    except Exception:
        pass


log('--- start')
try:
    from Autodesk.Revit.Exceptions import InvalidOperationException, OperationCanceledException
    from pyrevit import DB, HOST_APP, UI, forms, script
    # pyrevit.framework loads the engine's IronPython.Wpf assembly that backs wpf.
    from pyrevit.framework import wpf
    from System import Action, TimeSpan
    from System.Collections.Generic import List
    from System.Windows.Interop import WindowInteropHelper
    from System.Windows.Threading import DispatcherPriority, DispatcherTimer

    from GUI.WPF_Base import my_WPF
    from pdf_overlay import raster
    from pdf_overlay.geometry import (
        fit_pose,
        image_size_feet,
        initial_feet_per_pixel,
        make_pose,
        marker_radius_feet,
        max_dpi_for_page,
        page_pixels_allowed,
        rotated_canvas_size,
        view_to_pixel,
    )
    from pdf_overlay.state import (
        clamp_tolerance,
        default_cache_root,
        describe_overlay,
        load_state,
        make_state,
        overlay_paths,
        overlay_stem,
        save_state,
        stem_from_image_name,
    )
    from pdf_overlay.style import DEFAULT_OPACITY, DEFAULT_TINT, TINTS, clamp_opacity, tint_rgb
    from pdf_overlay.members import (
        CONFLICT,
        DEFAULT_TOLERANCE_DEGREES,
        DEFAULT_TOLERANCE_FEET,
        MATCH,
        MISMATCH,
        UNREADABLE,
        label_mark,
        match_members,
        parse_size,
        size_labels,
        sort_labels,
    )
    from pdf_overlay.pdftext import PdfError, read_pdf_page_text
except Exception:
    log('import failed:\n' + traceback.format_exc())
    raise
log('imports ok')


COMMAND_TITLE = 'PDF Overlay'
DPI_CHOICES = (100, 150, 200, 300, 400, 600)
DEFAULT_DPI = 150
OPACITY_DELAY_MS = 400
CACHE_ROOT = default_cache_root()
# 'None' is a Python keyword, so the enum member is read by name.
NO_SNAPS = getattr(UI.Selection.ObjectSnapTypes, 'None')
PDF_MARK_RGB = (0, 90, 255)
MODEL_MARK_RGB = (0, 160, 60)
MARK_LINE_WEIGHT = 8

logger = script.get_logger()


class Overlay(object):
    """One overlay ImageType in a document and its local cache state."""

    def __init__(self, image_type, stem):
        self.image_type = image_type
        self.stem = stem
        self.paths = overlay_paths(CACHE_ROOT, stem)
        self.state = None
        self.error = None
        self.in_view = False
        try:
            self.state = load_state(self.paths['state'])
        except (IOError, OSError, ValueError) as error:
            self.error = 'Local overlay files are missing on this computer; import the PDF again.'
            logger.debug('PDF Overlay state %s: %s', self.paths['state'], error)

    @property
    def created(self):
        """Import time as text; older overlays fall back to their state file time."""
        if self.state is None:
            return ''
        if self.state.get('created'):
            return self.state['created']
        try:
            stamp = os.path.getmtime(self.paths['state'])
        except OSError:
            return ''
        return datetime.datetime.fromtimestamp(stamp).strftime('%Y-%m-%dT%H:%M:%S')

    @property
    def label(self):
        if self.state is None:
            return '{} (no local files)'.format(self.stem)
        return describe_overlay(self.state, self.in_view, self.created)


# -- Revit helpers -----------------------------------------------------------

# View 2D coordinates are measured from the model origin along the view's
# right/up axes, so every view facing the same way (all plan views of a
# level stack, for example) shares one set of overlay coordinates.

def _to_view_2d(view, point):
    return (point.DotProduct(view.RightDirection), point.DotProduct(view.UpDirection))


def _to_model(view, xy):
    depth = view.Origin.DotProduct(view.ViewDirection)
    return (view.RightDirection.Multiply(xy[0]) + view.UpDirection.Multiply(xy[1])
            + view.ViewDirection.Multiply(depth))


def _same_orientation(view_a, view_b):
    return (view_a.RightDirection.DotProduct(view_b.RightDirection) > 0.9999 and
            view_a.UpDirection.DotProduct(view_b.UpDirection) > 0.9999)


def _visible_center(uidoc, view):
    for ui_view in uidoc.GetOpenUIViews():
        if ui_view.ViewId == view.Id:
            corners = ui_view.GetZoomCorners()
            return _to_view_2d(view, (corners[0] + corners[1]).Divide(2.0))
    return (0.0, 0.0)


def _image_type_name(image_type):
    for getter in (lambda: image_type.Path, lambda: DB.Element.Name.GetValue(image_type)):
        try:
            stem = stem_from_image_name(getter())
        except Exception:
            stem = None
        if stem:
            return stem
    return None


def find_overlays(doc):
    overlays = []
    for image_type in DB.FilteredElementCollector(doc).OfClass(DB.ImageType):
        stem = _image_type_name(image_type)
        if stem:
            overlays.append(Overlay(image_type, stem))
    return overlays


def order_overlays(overlays, doc, view):
    """Mark overlays placed in view; list those first, newest import first."""
    valid_view = view is not None and DB.ImageInstance.IsValidView(view)
    for overlay in overlays:
        overlay.in_view = valid_view and bool(overlay_instances(doc, overlay.image_type, view))
    overlays.sort(key=lambda overlay: overlay.created, reverse=True)
    overlays.sort(key=lambda overlay: not overlay.in_view)
    return overlays


def overlay_instances(doc, image_type, view=None):
    collector = (DB.FilteredElementCollector(doc, view.Id) if view is not None
                 else DB.FilteredElementCollector(doc))
    return [instance for instance in collector.OfClass(DB.ImageInstance)
            if instance.GetTypeId() == image_type.Id]


def _active_overlay_view(uidoc):
    view = uidoc.ActiveView
    if view is None or not DB.ImageInstance.IsValidView(view):
        raise UserError('Open a plan, ceiling, elevation, section, or drafting view first.')
    return view


def _overlay_document(uiapp, overlay):
    """Return the active document, refusing an overlay listed from another model."""
    doc = uiapp.ActiveUIDocument.Document
    if not overlay.image_type.IsValidObject or not overlay.image_type.Document.Equals(doc):
        raise UserError('The overlay list is out of date for this model; click Refresh.')
    return doc


def _image_options(path, dpi):
    options = DB.ImageTypeOptions(path, False, DB.ImageTypeSource.Import)
    options.Resolution = dpi
    return options


def _apply_pose(instance, view, state):
    pose = state['pose']
    width, height = image_size_feet(pose, state['page_size'])
    instance.DrawLayer = DB.DrawLayer.Foreground
    # Set both sides: a reload after rotating changes the image's aspect ratio.
    instance.LockProportions = False
    instance.Width = width
    instance.Height = height
    instance.LockProportions = True
    instance.SetLocation(_to_model(view, pose['center']), DB.BoxPlacement.Center)


def _sync_pose_from_instance(instance, view, state):
    """Adopt the instance's current center and width, in case it was moved in Revit."""
    pose = state['pose']
    canvas_width = rotated_canvas_size(state['page_size'][0], state['page_size'][1], pose['rotation'])[0]
    center = _to_view_2d(view, instance.GetLocation(DB.BoxPlacement.Center))
    state['pose'] = make_pose(center, instance.Width / float(canvas_width), pose['rotation'])


def _render(paths, state):
    source = raster.load_bitmap(paths['source'])
    try:
        overlay = raster.render_overlay(source, state['pose']['rotation'],
                                        tint_rgb(state['tint']), state['opacity'])
    finally:
        source.Dispose()
    try:
        raster.save_png(overlay, paths['overlay'])
    finally:
        overlay.Dispose()


class UserError(Exception):
    """A problem the user can fix; shown in the palette without a traceback."""


# -- Actions (run inside the Revit API context) ------------------------------

def _rasterize_page(doc, pdf_path, page, dpi, source_path):
    """Save a PDF page as the overlay source PNG; return its pixel size."""
    if not DB.OptionalFunctionalityUtils.IsPDFImportAvailable():
        raise UserError('PDF import is not available in this Revit installation.')
    # Let Revit rasterize the page, copy the pixels, then roll the type back out.
    transaction = DB.Transaction(doc, 'PDF Overlay - Read Page')
    transaction.Start()
    try:
        options = _image_options(pdf_path, dpi)
        options.PageNumber = page
        page_type = DB.ImageType.Create(doc, options)
        page_image = page_type.GetImage()
        if page_image is None:
            raise UserError('Revit could not read page {} of that PDF.'.format(page))
        width, height = page_image.Width, page_image.Height
        if not page_pixels_allowed(width, height):
            page_image.Dispose()
            raise UserError('Page {} at {} DPI is too large ({} x {} px). Use {} DPI or lower.'.format(
                page, dpi, width, height, max_dpi_for_page(width, height, dpi)))
        try:
            source = raster.flatten_on_white(page_image)
        finally:
            page_image.Dispose()
    finally:
        transaction.RollBack()
    try:
        raster.save_png(source, source_path)
        return (source.Width, source.Height)
    finally:
        source.Dispose()


def import_pdf(uiapp, pdf_path, page, dpi):
    uidoc = uiapp.ActiveUIDocument
    doc = uidoc.Document
    view = _active_overlay_view(uidoc)
    paths = overlay_paths(CACHE_ROOT, overlay_stem(pdf_path, page, uuid.uuid4().hex[:8]))
    page_size = _rasterize_page(doc, pdf_path, page, dpi, paths['source'])
    pose = make_pose(_visible_center(uidoc, view), initial_feet_per_pixel(view.Scale, dpi))
    state = make_state(pdf_path, page, dpi, page_size, pose, DEFAULT_TINT, DEFAULT_OPACITY,
                       datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    _render(paths, state)
    save_state(paths['state'], state)

    transaction = DB.Transaction(doc, 'PDF Overlay - Place')
    transaction.Start()
    try:
        image_type = DB.ImageType.Create(doc, _image_options(paths['overlay'], dpi))
        placement = DB.ImagePlacementOptions(_to_model(view, pose['center']), DB.BoxPlacement.Center)
        instance = DB.ImageInstance.Create(doc, view, image_type.Id, placement)
        _apply_pose(instance, view, state)
        transaction.Commit()
    except Exception:
        transaction.RollBack()
        raise
    return paths


def refresh_overlay(uiapp, overlay, pose=None):
    """Re-render the overlay PNG, reload its ImageType, and re-place instances."""
    doc = _overlay_document(uiapp, overlay)
    state = overlay.state
    if pose is not None:
        state['pose'] = pose
    else:
        # Re-read the placed image, which may have moved in Revit.
        instances = overlay_instances(doc, overlay.image_type)
        if instances:
            _sync_pose_from_instance(instances[0], doc.GetElement(instances[0].OwnerViewId), state)
    _render(overlay.paths, state)
    transaction = DB.Transaction(doc, 'PDF Overlay - Update')
    transaction.Start()
    try:
        overlay.image_type.ReloadFrom(_image_options(overlay.paths['overlay'], state['dpi']))
        for instance in overlay_instances(doc, overlay.image_type):
            _apply_pose(instance, doc.GetElement(instance.OwnerViewId), state)
        transaction.Commit()
    except Exception:
        transaction.RollBack()
        raise
    save_state(overlay.paths['state'], state)


def place_in_view(uiapp, overlay):
    """Place an existing overlay in the active view at its aligned position."""
    uidoc = uiapp.ActiveUIDocument
    doc = _overlay_document(uiapp, overlay)
    view = _active_overlay_view(uidoc)
    if overlay_instances(doc, overlay.image_type, view):
        raise UserError('This overlay is already in the active view.')
    state = overlay.state
    placed = overlay_instances(doc, overlay.image_type)
    if placed:
        source_view = doc.GetElement(placed[0].OwnerViewId)
        if not _same_orientation(source_view, view):
            raise UserError('The overlay was aligned in a view facing another way; '
                            'place it in a plan view, or import the PDF again here.')
        _sync_pose_from_instance(placed[0], source_view, state)
    transaction = DB.Transaction(doc, 'PDF Overlay - Place in View')
    transaction.Start()
    try:
        placement = DB.ImagePlacementOptions(_to_model(view, state['pose']['center']),
                                             DB.BoxPlacement.Center)
        instance = DB.ImageInstance.Create(doc, view, overlay.image_type.Id, placement)
        _apply_pose(instance, view, state)
        transaction.Commit()
    except Exception:
        transaction.RollBack()
        raise
    save_state(overlay.paths['state'], state)


def replace_pdf(uiapp, overlay, pdf_path):
    """Load a revised PDF into an overlay, keeping its alignment, page, and DPI.

    Returns a warning when the new page has a different size, since the
    alignment then only holds near the page center.
    """
    doc = _overlay_document(uiapp, overlay)
    state = overlay.state
    placed = overlay_instances(doc, overlay.image_type)
    if placed:
        _sync_pose_from_instance(placed[0], doc.GetElement(placed[0].OwnerViewId), state)
    old_size = tuple(state['page_size'])
    new_size = _rasterize_page(doc, pdf_path, state['page'], state['dpi'], overlay.paths['source'])
    state['pdf_path'] = pdf_path
    state['page_size'] = [new_size[0], new_size[1]]
    refresh_overlay(uiapp, overlay, state['pose'])
    if abs(new_size[0] - old_size[0]) > 2 or abs(new_size[1] - old_size[1]) > 2:
        return ('The new page is a different size ({} x {} px, was {} x {}); '
                'check the alignment and run Align if needed.').format(
                    new_size[0], new_size[1], old_size[0], old_size[1])
    return None


def remove_overlay(uiapp, overlay):
    """Delete the overlay's image and every placement from the model."""
    doc = _overlay_document(uiapp, overlay)
    transaction = DB.Transaction(doc, 'PDF Overlay - Remove')
    transaction.Start()
    try:
        doc.Delete(overlay.image_type.Id)
        transaction.Commit()
    except Exception:
        transaction.RollBack()
        raise


def _add_marker(doc, view, point, rgb):
    """Draw a temporary colored circle at a picked point; return its id or None."""
    center = _to_model(view, _to_view_2d(view, point))
    transaction = DB.Transaction(doc, 'PDF Overlay - Pick Marker')
    transaction.Start()
    try:
        circle = DB.Arc.Create(center, marker_radius_feet(view.Scale), 0.0, 2.0 * math.pi,
                               view.RightDirection, view.UpDirection)
        curve = doc.Create.NewDetailCurve(view, circle)
        overrides = DB.OverrideGraphicSettings()
        overrides.SetProjectionLineColor(DB.Color(*rgb))
        overrides.SetProjectionLineWeight(MARK_LINE_WEIGHT)
        view.SetElementOverrides(curve.Id, overrides)
        transaction.Commit()
        return curve.Id
    except Exception:
        transaction.RollBack()
        log('pick marker skipped:\n' + traceback.format_exc())
        return None


def _clear_markers(doc, marker_ids):
    marker_ids = [marker_id for marker_id in marker_ids if marker_id is not None]
    if not marker_ids:
        return
    transaction = DB.Transaction(doc, 'PDF Overlay - Clear Pick Markers')
    transaction.Start()
    try:
        doc.Delete(List[DB.ElementId](marker_ids))
        transaction.Commit()
    except Exception:
        transaction.RollBack()
        log('pick marker cleanup failed:\n' + traceback.format_exc())


ALIGN_STEPS = (
    u'Step 1 of 4: click a point ON THE PDF (a grid intersection works best).',
    u'✓ PDF point 1 set (blue circle).\nStep 2 of 4: click the SAME point IN THE MODEL.',
    u'✓ Model point 1 set (green circle).\nStep 3 of 4: click a second point ON THE PDF, far from the first.',
    u'✓ PDF point 2 set (blue circle).\nStep 4 of 4: click the SAME point IN THE MODEL.',
    u'✓ All 4 points set. Fitting the PDF...',
)
ALIGN_PROMPTS = (
    'PDF Overlay step 1 of 4: click a point ON THE PDF. Esc cancels.',
    'PDF Overlay step 2 of 4: click the SAME point IN THE MODEL. Esc cancels.',
    'PDF Overlay step 3 of 4: click a second point ON THE PDF, far from the first. Esc cancels.',
    'PDF Overlay step 4 of 4: click the SAME point IN THE MODEL. Esc cancels.',
)


def align_overlay(uiapp, overlay, progress):
    uidoc = uiapp.ActiveUIDocument
    doc = _overlay_document(uiapp, overlay)
    view = _active_overlay_view(uidoc)
    instances = overlay_instances(doc, overlay.image_type, view)
    if not instances:
        raise UserError('This overlay is not placed in the active view.')
    instance = instances[0]
    if instance.IsHidden(view):
        raise UserError('Show the overlay before aligning it.')
    state = overlay.state
    _sync_pose_from_instance(instance, view, state)

    pixels, targets, marker_ids = [], [], []
    try:
        for step, prompt in enumerate(ALIGN_PROMPTS):
            on_pdf = step % 2 == 0
            progress(ALIGN_STEPS[step])
            try:
                if on_pdf:
                    point = uidoc.Selection.PickPoint(NO_SNAPS, prompt)
                else:
                    point = uidoc.Selection.PickPoint(prompt)
            except InvalidOperationException as error:
                raise UserError('Revit would not start picking: {}'.format(error))
            marker_ids.append(_add_marker(doc, view, point, PDF_MARK_RGB if on_pdf else MODEL_MARK_RGB))
            if on_pdf:
                pixels.append(view_to_pixel(state['pose'], state['page_size'], _to_view_2d(view, point)))
            else:
                targets.append(_to_view_2d(view, point))
        progress(ALIGN_STEPS[-1])
    finally:
        _clear_markers(doc, marker_ids)
    try:
        pose = fit_pose(state['page_size'], pixels, targets)
    except ValueError as error:
        raise UserError(str(error))
    refresh_overlay(uiapp, overlay, pose)
    return pose


def set_overlay_visibility(uiapp, overlay, visible):
    uidoc = uiapp.ActiveUIDocument
    doc = _overlay_document(uiapp, overlay)
    view = _active_overlay_view(uidoc)
    ids = List[DB.ElementId]([instance.Id for instance in overlay_instances(doc, overlay.image_type, view)])
    if ids.Count == 0:
        raise UserError('This overlay is not placed in the active view.')
    transaction = DB.Transaction(doc, 'PDF Overlay - Show' if visible else 'PDF Overlay - Hide')
    transaction.Start()
    try:
        if visible:
            view.UnhideElements(ids)
        else:
            view.HideElements(ids)
        transaction.Commit()
    except Exception:
        transaction.RollBack()
        raise



# -- Member check ------------------------------------------------------------

STATUS_LABELS = {
    MISMATCH: 'Size differs',
    CONFLICT: 'PDF labels disagree',
    UNREADABLE: 'Revit size not recognized',
}
MAX_UNLABELLED_ROWS = 200
# Review marks are detail lines in their own line style, so the tool can find
# and clear them, and Visibility/Graphics can hide them.
MARK_STYLE_NAME = 'PDF Overlay Marks'
MARK_STYLE_RGB = (255, 120, 0)
MARK_STYLE_WEIGHT = 6


def _member_size(doc, element):
    """Return (size text, parse_size key or None) from the member's type."""
    symbol = doc.GetElement(element.GetTypeId())
    type_name = DB.Element.Name.GetValue(symbol) if symbol is not None else ''
    family_name = getattr(symbol, 'FamilyName', '') or ''
    for text in (type_name, family_name + ' ' + type_name):
        parsed = parse_size(text)
        if parsed:
            return parsed[1], parsed[0]
    return (type_name or family_name or '?'), None


def collect_members(doc, view):
    """Return framing visible in view as 2D member lines for matching."""
    members = []
    collector = (DB.FilteredElementCollector(doc, view.Id)
                 .OfCategory(DB.BuiltInCategory.OST_StructuralFraming)
                 .WhereElementIsNotElementType())
    for element in collector:
        curve = getattr(getattr(element, 'Location', None), 'Curve', None)
        if curve is None:
            continue
        start = _to_view_2d(view, curve.GetEndPoint(0))
        end = _to_view_2d(view, curve.GetEndPoint(1))
        if math.hypot(end[0] - start[0], end[1] - start[1]) < 0.01:
            continue  # Seen end-on in this view.
        size, key = _member_size(doc, element)
        members.append({'id': element.Id, 'size': size, 'key': key, 'start': start, 'end': end})
    return members


def _crop_rect(view):
    """Return the active crop region as a view-space rectangle, or None."""
    if not view.CropBoxActive:
        return None
    box = view.CropBox
    corners = [_to_view_2d(view, box.Transform.OfPoint(point)) for point in (box.Min, box.Max)]
    xs, ys = [corner[0] for corner in corners], [corner[1] for corner in corners]
    return (min(xs), min(ys), max(xs), max(ys))


def check_members(uiapp, overlay):
    """Compare framing sizes in the active view with the overlay's PDF labels."""
    uidoc = uiapp.ActiveUIDocument
    doc = _overlay_document(uiapp, overlay)
    view = _active_overlay_view(uidoc)
    instances = overlay_instances(doc, overlay.image_type, view)
    if not instances:
        raise UserError('This overlay is not placed in the active view.')
    state = overlay.state
    _sync_pose_from_instance(instances[0], view, state)
    try:
        page_text = read_pdf_page_text(state['pdf_path'], state['page'])
    except (IOError, OSError):
        raise UserError('The PDF is no longer at {}.'.format(state['pdf_path']))
    except PdfError as error:
        raise UserError('Could not read the PDF text: {}'.format(error))

    labels = size_labels(page_text, state['pose'], state['page_size'])
    if not labels:
        raise UserError('No steel size labels (like W12x26) were found as text in this PDF page.')
    crop = _crop_rect(view)
    outside = 0
    if crop is not None:
        inside = [label for label in labels
                  if crop[0] <= label['center'][0] <= crop[2] and crop[1] <= label['center'][1] <= crop[3]]
        outside = len(labels) - len(inside)
        labels = inside
    members = collect_members(doc, view)
    result = match_members(labels, members, state['tolerance_feet'], state['tolerance_degrees'])
    save_state(overlay.paths['state'], state)
    result.update({'labels': len(labels), 'members': len(members), 'outside': outside,
                   'tolerance': (state['tolerance_feet'], state['tolerance_degrees']),
                   'aspect_warning': _aspect_warning(page_text, state['page_size'])})
    return result


def _mark_style(doc):
    """Return the review-mark line style, creating it if needed (in a transaction)."""
    categories = doc.Settings.Categories
    lines = categories.get_Item(DB.BuiltInCategory.OST_Lines)
    style = next((sub for sub in lines.SubCategories if sub.Name == MARK_STYLE_NAME), None)
    if style is None:
        style = categories.NewSubcategory(lines, MARK_STYLE_NAME)
        style.LineColor = DB.Color(*MARK_STYLE_RGB)
        style.SetLineWeight(MARK_STYLE_WEIGHT, DB.GraphicsStyleType.Projection)
    return style.GetGraphicsStyle(DB.GraphicsStyleType.Projection)


def _mark_ids(doc, view):
    ids = []
    for curve in DB.FilteredElementCollector(doc, view.Id).OfClass(DB.CurveElement):
        style = curve.LineStyle
        if style is not None and style.Name == MARK_STYLE_NAME:
            ids.append(curve.Id)
    return ids


def update_marks(doc, view, labels, radius):
    """Replace this view's review marks with one mark per label.

    Returns (cleared count, [(label, [mark element ids])]). An empty labels
    list only clears.
    """
    marks = []
    transaction = DB.Transaction(doc, 'PDF Overlay - Review Marks')
    transaction.Start()
    try:
        old = _mark_ids(doc, view)
        if old:
            doc.Delete(List[DB.ElementId](old))
        if labels:
            style = _mark_style(doc)
            for label in labels:
                mark = label_mark(label, radius)
                ids = []
                try:
                    circle = DB.Arc.Create(_to_model(view, mark['center']), mark['radius'], 0.0,
                                           2.0 * math.pi, view.RightDirection, view.UpDirection)
                    line = DB.Line.CreateBound(_to_model(view, mark['line'][0]),
                                               _to_model(view, mark['line'][1]))
                    for curve in (circle, line):
                        detail = doc.Create.NewDetailCurve(view, curve)
                        detail.LineStyle = style
                        ids.append(detail.Id)
                except Exception:
                    log('review mark skipped:\n' + traceback.format_exc())
                marks.append((label, ids))
        transaction.Commit()
    except Exception:
        transaction.RollBack()
        raise
    return len(old), marks


def _aspect_warning(page_text, page_size):
    width, height = page_text.display_size()
    pdf_aspect = width / height
    raster_aspect = float(page_size[0]) / page_size[1]
    if abs(pdf_aspect / raster_aspect - 1.0) > 0.02:
        return ('The PDF page shape ({:.3f}) differs from the imported image ({:.3f}); '
                'label positions may be off.').format(pdf_aspect, raster_aspect)
    return None


def report_member_check(output, overlay, result, marks=None):
    """Print the review list to the pyRevit output window; return ids to select.

    marks: [(label, [mark ids])] for the labels with no member nearby, or
    None when they were not marked.
    """
    rows = result['rows']
    review = [row for row in rows if row['status'] != MATCH]
    matched = len(rows) - len(review)
    output.print_md('## PDF member check: {}'.format(os.path.basename(overlay.state['pdf_path'])))
    output.print_md(
        '{} size labels read; {} labelled members match, **{} need review**, '
        '{} labels found no member, {} members in the view had no label.'.format(
            result['labels'], matched, len(review), len(result['unmatched_labels']),
            len(result['unlabelled'])))
    output.print_md('Labels matched to members within {:g} ft and {:g} degrees.'.format(
        *result['tolerance']))
    if result['outside']:
        output.print_md('{} labels outside the crop region were ignored.'.format(result['outside']))
    if result['aspect_warning']:
        output.print_md('**Warning:** ' + result['aspect_warning'])
    if review:
        output.print_table(
            table_data=[[output.linkify(row['id']), row['revit'], row['pdf'],
                         STATUS_LABELS.get(row['status'], row['status'])] for row in review],
            columns=['Member', 'Revit size', 'PDF size', 'Review'],
            title='Members to review')
    if marks:
        output.print_table(
            table_data=[[output.linkify(ids, title=label['text']) if ids else label['text'],
                         'Orange circle = {:g} ft match window'.format(result['tolerance'][0])]
                        for label, ids in marks],
            columns=['PDF size (click to select its mark)', 'Mark'],
            title='PDF labels with no member nearby (missing members or loose alignment)')
    elif result['unmatched_labels']:
        counts = {}
        for label in result['unmatched_labels']:
            counts[label['text']] = counts.get(label['text'], 0) + 1
        output.print_table(
            table_data=[[text, count] for text, count in sorted(counts.items())],
            columns=['PDF size', 'Labels'],
            title='PDF labels with no member nearby (missing members or loose alignment)')
    if result['unlabelled']:
        shown = result['unlabelled'][:MAX_UNLABELLED_ROWS]
        output.print_table(
            table_data=[[output.linkify(member['id']), member['size']] for member in shown],
            columns=['Member', 'Revit size'],
            title='Members with no PDF label (not checked)')
        if len(result['unlabelled']) > len(shown):
            output.print_md('...and {} more.'.format(len(result['unlabelled']) - len(shown)))
    return [row['id'] for row in review]


# -- Palette -----------------------------------------------------------------

class OverlayActionHandler(UI.IExternalEventHandler):
    """Runs one queued palette action in Revit's API context."""

    def __init__(self):
        self.action = None
        self.palette = None

    def Execute(self, uiapp):
        action, self.action = self.action, None
        if action is None:
            return
        try:
            action(uiapp)
        except OperationCanceledException:
            self.palette.set_status('Cancelled; nothing changed.')
        except MemoryError:
            log('out of memory:\n' + traceback.format_exc())
            self.palette.set_status('Out of memory. Try a lower DPI.')
        except UserError as error:
            self.palette.set_status(str(error))
        except Exception as error:
            log('action failed:\n' + traceback.format_exc())
            self.palette.set_status('Failed: {}'.format(error))

    def GetName(self):
        return COMMAND_TITLE


class PdfOverlayPalette(my_WPF):
    def __init__(self, handler, action_event, output):
        self.handler = handler
        self.action_event = action_event
        # Captured at launch; pyRevit binds output to the running command.
        self.output = output
        self.current = None
        self._loading = False
        self.add_wpf_resource()
        wpf.LoadComponent(self, os.path.join(os.path.dirname(__file__), 'PdfOverlayPalette.xaml'))
        WindowInteropHelper(self).Owner = HOST_APP.proc_window
        for dpi in DPI_CHOICES:
            self.dpi_list.Items.Add(str(dpi))
        self.dpi_list.SelectedItem = str(DEFAULT_DPI)
        for name in TINTS:
            self.tint_list.Items.Add(name)
        self.opacity_timer = DispatcherTimer()
        self.opacity_timer.Interval = TimeSpan.FromMilliseconds(OPACITY_DELAY_MS)
        self.opacity_timer.Tick += self.opacity_settled
        # Clicking a PDF overlay image in Revit makes it the palette's overlay.
        self.uiapp = HOST_APP.uiapp
        self._selection_handler = self.selection_changed
        self.uiapp.SelectionChanged += self._selection_handler
        self.Closed += self.palette_closed

    # Queueing ---------------------------------------------------------------

    def run(self, action, status):
        if self.handler.action is not None:
            self.set_status('Busy with the previous action; try again in a moment.')
            return
        self.set_status(status)
        self.handler.action = action
        self.action_event.Raise()

    def set_status(self, message):
        self.status_text.Text = message

    def show_progress(self, message):
        """Show a status message immediately, even while Revit waits for a pick."""
        self.set_status(message)
        self.Dispatcher.Invoke(Action(lambda: None), DispatcherPriority.Render)

    def selected_overlay(self):
        return self.current

    def _usable_overlay(self):
        overlay = self.selected_overlay()
        if overlay is None:
            self.set_status('Click a PDF overlay in the view first, or Import PDF.')
        elif overlay.state is None:
            self.set_status(overlay.error)
            overlay = None
        return overlay

    # Current overlay and controls -----------------------------------------------

    def pick_current(self, uiapp, select_stem=None):
        """Choose the overlay to work on: a given one, the selected image, the
        previous one, or else the newest overlay in the active view."""
        uidoc = uiapp.ActiveUIDocument
        doc = uidoc.Document
        overlays = order_overlays(find_overlays(doc), doc, uidoc.ActiveView)
        stems = [select_stem, self._selected_stem(doc, uidoc.Selection.GetElementIds()),
                 self.current.stem if self.current else None]
        chosen = None
        for stem in stems:
            chosen = next((overlay for overlay in overlays if stem and overlay.stem == stem), None)
            if chosen:
                break
        if chosen is None:
            chosen = next((overlay for overlay in overlays if overlay.in_view), None)
        self.set_current(chosen, uidoc)

    @staticmethod
    def _selected_stem(doc, element_ids):
        """Return the overlay stem of the first selected image, '' for a non-overlay image."""
        for element_id in element_ids:
            element = doc.GetElement(element_id)
            if isinstance(element, DB.ImageInstance):
                return _image_type_name(doc.GetElement(element.GetTypeId())) or ''
        return None

    def set_current(self, overlay, uidoc):
        self.current = overlay
        self.overlay_name.Text = overlay.label if overlay else 'None: click a PDF overlay in the view.'
        self.show_controls(uidoc)

    def selection_changed(self, sender, args):
        """Follow Revit's selection when it includes a PDF overlay image."""
        try:
            doc = args.GetDocument()
            stem = self._selected_stem(doc, args.GetSelectedElements())
            if stem is None:
                return  # Nothing image-like selected; keep the current overlay.
            if stem == '':
                self.set_status('That image is not a PDF overlay from this tool.')
                return
            self.pick_current(self.uiapp, stem)
        except Exception:
            log('selection follow failed:\n' + traceback.format_exc())

    def palette_closed(self, sender, e):
        try:
            self.uiapp.SelectionChanged -= self._selection_handler
        except Exception:
            log('selection unsubscribe failed:\n' + traceback.format_exc())

    def show_controls(self, uidoc):
        overlay = self.selected_overlay()
        state = overlay.state if overlay else None
        self._loading = True
        try:
            self.opacity_slider.Value = state['opacity'] if state else DEFAULT_OPACITY
            self.opacity_text.Text = '{}%'.format(int(self.opacity_slider.Value))
            self.tint_list.SelectedItem = state['tint'] if state else DEFAULT_TINT
            visible = True
            view = uidoc.ActiveView
            if overlay is not None and view is not None and DB.ImageInstance.IsValidView(view):
                instances = overlay_instances(uidoc.Document, overlay.image_type, view)
                visible = not any(instance.IsHidden(view) for instance in instances)
            self.visible_check.IsChecked = visible
            self.tolerance_feet_box.Text = '{:g}'.format(
                state['tolerance_feet'] if state else DEFAULT_TOLERANCE_FEET)
            self.tolerance_angle_box.Text = '{:g}'.format(
                state['tolerance_degrees'] if state else DEFAULT_TOLERANCE_DEGREES)
        finally:
            self._loading = False
        if overlay is None:
            self.set_status('Click a PDF overlay in the view to work on it, or pick a page and DPI '
                            'and Import PDF. Place in View reuses one from another view.')
        elif overlay.error:
            self.set_status(overlay.error)
        elif not overlay.in_view:
            self.set_status('This overlay is not in the active view. Click it in a view that shows it, '
                            'or use Place in View.')
        else:
            self.set_status('Ready. Replace PDF loads a revised file into this overlay.')

    def button_import(self, sender, e):
        try:
            page = int(self.page_box.Text.strip())
            if page < 1:
                raise ValueError
        except ValueError:
            self.set_status('Page must be a whole number of 1 or more.')
            return
        dpi = int(self.dpi_list.SelectedItem or DEFAULT_DPI)
        pdf_path = forms.pick_file(file_ext='pdf', title='Select PDF to overlay')
        if not pdf_path:
            return

        def action(uiapp):
            paths = import_pdf(uiapp, pdf_path, page, dpi)
            self.pick_current(uiapp, os.path.splitext(os.path.basename(paths['overlay']))[0])
            self.set_status('Placed at the view scale in the middle of the view. '
                            'Click Align (2 Points) to fit it to the framing.')
        self.run(action, 'Importing page {} at {} DPI...'.format(page, dpi))

    def button_align(self, sender, e):
        overlay = self._usable_overlay()
        if overlay is None:
            return

        def action(uiapp):
            pose = align_overlay(uiapp, overlay, self.show_progress)
            self.set_status('Aligned. Rotation {:.2f} deg. Run Align again to refine.'.format(
                math.degrees(pose['rotation'])))
        self.run(action, ALIGN_STEPS[0])

    def button_place(self, sender, e):
        def action(uiapp):
            uidoc = uiapp.ActiveUIDocument
            doc = uidoc.Document
            elsewhere = [overlay for overlay in order_overlays(find_overlays(doc), doc, uidoc.ActiveView)
                         if not overlay.in_view and overlay.state is not None]
            if not elsewhere:
                self.set_status('Every overlay in this model is already in this view.')
                return
            labels = [overlay.label for overlay in elsewhere]
            choice = forms.SelectFromList.show(labels, title='Place overlay in this view',
                                               button_name='Place', multiselect=False)
            if not choice:
                self.set_status('Nothing placed.')
                return
            overlay = elsewhere[labels.index(choice)]
            place_in_view(uiapp, overlay)
            self.pick_current(uiapp, overlay.stem)
            self.set_status('Placed in this view at its aligned position.')
        self.run(action, 'Finding overlays in other views...')

    def button_replace(self, sender, e):
        overlay = self._usable_overlay()
        if overlay is None:
            return
        pdf_path = forms.pick_file(file_ext='pdf', title='Select the revised PDF',
                                   init_dir=os.path.dirname(overlay.state['pdf_path']))
        if not pdf_path:
            return

        def action(uiapp):
            warning = replace_pdf(uiapp, overlay, pdf_path)
            self.pick_current(uiapp, overlay.stem)
            self.set_status(warning or 'Loaded {} into the overlay; alignment kept.'.format(
                os.path.basename(pdf_path)))
        self.run(action, 'Loading the revised PDF (page {}, {} DPI)...'.format(
            overlay.state['page'], overlay.state['dpi']))

    def button_remove(self, sender, e):
        overlay = self.selected_overlay()
        if overlay is None:
            self.set_status('Click the PDF overlay to remove in the view first.')
            return
        if not forms.alert('Remove "{}" and all its placements from the model?'.format(overlay.label),
                           title=COMMAND_TITLE, ok=False, yes=True, no=True):
            return

        def action(uiapp):
            remove_overlay(uiapp, overlay)
            self.current = None
            self.pick_current(uiapp)
            self.set_status('Overlay removed. Undo in Revit brings it back.')
        self.run(action, 'Removing overlay...')

    def _read_tolerances(self, overlay):
        """Store the palette's tolerance fields on the overlay; return an error or None."""
        try:
            feet = float(self.tolerance_feet_box.Text.strip())
            degrees = float(self.tolerance_angle_box.Text.strip())
        except ValueError:
            return 'Tolerance must be numbers: feet and degrees.'
        if feet <= 0 or degrees <= 0:
            return 'Tolerance must be greater than zero.'
        overlay.state['tolerance_feet'] = clamp_tolerance(feet, DEFAULT_TOLERANCE_FEET, 100.0)
        overlay.state['tolerance_degrees'] = clamp_tolerance(degrees, DEFAULT_TOLERANCE_DEGREES, 45.0)
        return None

    def button_check(self, sender, e):
        overlay = self._usable_overlay()
        if overlay is None:
            return
        error = self._read_tolerances(overlay)
        if error:
            self.set_status(error)
            return

        draw_marks = bool(self.mark_check.IsChecked)

        def action(uiapp):
            result = check_members(uiapp, overlay)
            uidoc = uiapp.ActiveUIDocument
            unmatched = sort_labels(result['unmatched_labels']) if draw_marks else []
            _, marks = update_marks(uidoc.Document, uidoc.ActiveView, unmatched,
                                    result['tolerance'][0])
            review_ids = report_member_check(self.output, overlay, result, marks or None)
            uidoc.Selection.SetElementIds(List[DB.ElementId](review_ids))
            status = ('{} member(s) to review are selected'.format(len(review_ids))
                      if review_ids else 'No size differences found')
            if marks:
                status += '; {} label(s) with no member are marked in orange'.format(len(marks))
            self.set_status(status + '. See the report window.')
        self.run(action, 'Reading PDF labels and checking members...')

    def button_clear_marks(self, sender, e):
        def action(uiapp):
            uidoc = uiapp.ActiveUIDocument
            view = _active_overlay_view(uidoc)
            cleared, _ = update_marks(uidoc.Document, view, [], 0.0)
            self.set_status('Cleared {} review mark line(s) from this view.'.format(cleared)
                            if cleared else 'No review marks in this view.')
        self.run(action, 'Clearing review marks...')

    def opacity_changed(self, sender, e):
        self.opacity_text.Text = '{}%'.format(int(self.opacity_slider.Value))
        if self._loading:
            return
        # Wait for the slider to settle; each change re-renders the image.
        self.opacity_timer.Stop()
        self.opacity_timer.Start()

    def opacity_settled(self, sender, e):
        self.opacity_timer.Stop()
        self.restyle(opacity=clamp_opacity(self.opacity_slider.Value))

    def tint_selected(self, sender, e):
        if not self._loading and self.tint_list.SelectedItem:
            self.restyle(tint=str(self.tint_list.SelectedItem))

    def restyle(self, opacity=None, tint=None):
        overlay = self._usable_overlay()
        if overlay is None:
            return

        def action(uiapp):
            if opacity is not None:
                overlay.state['opacity'] = opacity
            if tint is not None:
                overlay.state['tint'] = tint
            refresh_overlay(uiapp, overlay)
            self.set_status('Updated: {} at {}% opacity.'.format(
                overlay.state['tint'], overlay.state['opacity']))
        self.run(action, 'Updating overlay...')

    def visibility_changed(self, sender, e):
        if self._loading:
            return
        overlay = self.selected_overlay()
        if overlay is None:
            return
        visible = bool(self.visible_check.IsChecked)

        def action(uiapp):
            set_overlay_visibility(uiapp, overlay, visible)
            self.set_status('Overlay shown.' if visible else 'Overlay hidden in the active view.')
        self.run(action, '')


def main():
    handler = OverlayActionHandler()
    palette = PdfOverlayPalette(handler, UI.ExternalEvent.Create(handler), script.get_output())
    log('palette loaded')
    handler.palette = palette
    palette.pick_current(HOST_APP.uiapp)
    log('current overlay: {}'.format(palette.current.stem if palette.current else None))
    palette.Show()
    log('palette shown')


try:
    main()
except Exception as error:
    log('startup failed:\n' + traceback.format_exc())
    forms.alert('PDF Overlay could not start:\n{}\n\nDetails: {}'.format(error, LOG_PATH),
                title=COMMAND_TITLE, warn_icon=True)
