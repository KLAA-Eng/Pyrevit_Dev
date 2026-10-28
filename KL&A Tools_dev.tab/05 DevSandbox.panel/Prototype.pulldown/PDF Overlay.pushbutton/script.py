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
        default_cache_root,
        load_state,
        make_state,
        overlay_paths,
        overlay_stem,
        save_state,
        stem_from_image_name,
    )
    from pdf_overlay.style import DEFAULT_OPACITY, DEFAULT_TINT, TINTS, clamp_opacity, tint_rgb
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
        try:
            self.state = load_state(self.paths['state'])
        except (IOError, OSError, ValueError) as error:
            self.error = 'Local overlay files are missing on this computer; import the PDF again.'
            logger.debug('PDF Overlay state %s: %s', self.paths['state'], error)

    @property
    def label(self):
        if self.state is None:
            return '{} (no local files)'.format(self.stem)
        return '{}  p{}'.format(os.path.basename(self.state['pdf_path']), self.state['page'])


# -- Revit helpers -----------------------------------------------------------

def _view_basis(view):
    return view.Origin, view.RightDirection, view.UpDirection


def _to_view_2d(view, point):
    origin, right, up = _view_basis(view)
    offset = point - origin
    return (offset.DotProduct(right), offset.DotProduct(up))


def _to_model(view, xy):
    origin, right, up = _view_basis(view)
    return origin + right.Multiply(xy[0]) + up.Multiply(xy[1])


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
    return sorted(overlays, key=lambda overlay: overlay.label.lower())


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

def import_pdf(uiapp, pdf_path, page, dpi):
    uidoc = uiapp.ActiveUIDocument
    doc = uidoc.Document
    view = _active_overlay_view(uidoc)
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

    paths = overlay_paths(CACHE_ROOT, overlay_stem(pdf_path, page, uuid.uuid4().hex[:8]))
    try:
        raster.save_png(source, paths['source'])
        page_size = (source.Width, source.Height)
    finally:
        source.Dispose()
    pose = make_pose(_visible_center(uidoc, view), initial_feet_per_pixel(view.Scale, dpi))
    state = make_state(pdf_path, page, dpi, page_size, pose, DEFAULT_TINT, DEFAULT_OPACITY)
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
    def __init__(self, handler, action_event):
        self.handler = handler
        self.action_event = action_event
        self.overlays = []
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
        index = self.overlay_list.SelectedIndex
        if 0 <= index < len(self.overlays):
            return self.overlays[index]
        return None

    def _usable_overlay(self):
        overlay = self.selected_overlay()
        if overlay is None:
            self.set_status('Import a PDF or pick an overlay first.')
        elif overlay.state is None:
            self.set_status(overlay.error)
            overlay = None
        return overlay

    # List and controls --------------------------------------------------------

    def load_overlays(self, uiapp, select_stem=None):
        uidoc = uiapp.ActiveUIDocument
        previous = self.selected_overlay()
        select_stem = select_stem or (previous.stem if previous else None)
        self.overlays = find_overlays(uidoc.Document)
        self._loading = True
        try:
            self.overlay_list.Items.Clear()
            selected = 0 if self.overlays else -1
            for index, overlay in enumerate(self.overlays):
                self.overlay_list.Items.Add(overlay.label)
                if overlay.stem == select_stem:
                    selected = index
            self.overlay_list.SelectedIndex = selected
        finally:
            self._loading = False
        self.show_controls(uidoc)

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
        finally:
            self._loading = False
        if overlay is None:
            self.set_status('No overlays in this model yet. Pick a page and DPI, then Import PDF.')
        elif overlay.error:
            self.set_status(overlay.error)

    def button_refresh(self, sender, e):
        self.run(self.load_overlays, 'Refreshing...')

    def overlay_selected(self, sender, e):
        if not self._loading:
            self.run(lambda uiapp: self.show_controls(uiapp.ActiveUIDocument), '')

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
            self.load_overlays(uiapp, os.path.splitext(os.path.basename(paths['overlay']))[0])
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
    palette = PdfOverlayPalette(handler, UI.ExternalEvent.Create(handler))
    log('palette loaded')
    handler.palette = palette
    palette.load_overlays(HOST_APP.uiapp)
    log('overlays listed: {}'.format(len(palette.overlays)))
    palette.Show()
    log('palette shown')


try:
    main()
except Exception as error:
    log('startup failed:\n' + traceback.format_exc())
    forms.alert('PDF Overlay could not start:\n{}\n\nDetails: {}'.format(error, LOG_PATH),
                title=COMMAND_TITLE, warn_icon=True)
