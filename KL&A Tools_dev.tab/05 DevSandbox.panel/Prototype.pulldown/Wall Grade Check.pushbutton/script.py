# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Wall Grade Check"
__version__ = "v0.0"

import datetime
import os
import re
import traceback
from collections import OrderedDict

LOG_PATH = os.path.join(os.environ.get('LOCALAPPDATA') or os.environ.get('TEMP') or '.',
                        'KLA Tools', 'Wall Grade Check', 'wall_grade_check.log')


def log(message):
    try:
        folder = os.path.dirname(LOG_PATH)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with open(LOG_PATH, 'a') as log_file:
            log_file.write('{:%Y-%m-%d %H:%M:%S} {}\n'.format(datetime.datetime.now(), message))
    except Exception:
        pass


TOOL = {'id': 'devsandbox.wall-grade-check', 'name': 'Wall Grade Check', 'version': __version__}
TOOL_CODE = 'WGC'


def report_error(action):
    """Save an error report for the exception being handled; return the user message."""
    try:
        from error_reports_revit import report_exception
    except Exception:
        log('error reports unavailable:\n' + traceback.format_exc())
        return 'Details are in {}.'.format(LOG_PATH)
    report_id, message = report_exception(TOOL, TOOL_CODE, action, LOG_PATH)
    log('error report: {}'.format(report_id))
    return message


from pyrevit import DB, forms, revit, script
from System.Collections.Generic import List

from pdf_overlay.pdftext import PdfError, read_pdf_page_text
from pdf_overlay.state import (
    default_cache_root,
    describe_overlay,
    load_state,
    overlay_paths,
    stem_from_image_name,
)
from wall_grade import ghost, pdf_grade
from wall_grade.profile import (
    CLOSE,
    LINE_OFFSET_FEET,
    OK,
    OVER,
    PROBE_OFFSET_FEET,
    build_profile,
    clamp_clearance,
    exterior_offset,
    flagged_runs,
    format_feet_inches,
    format_inches,
    min_clearance,
    no_data_ranges,
    note_text,
    segments,
    stations,
)


COMMAND_TITLE = 'Wall Grade Check'
SOURCE_REVIT = 'Grade from Revit topography'
SOURCE_PDF = 'Grade from PDF grading plan'
CLEAR = 'Clear review lines'

# Line styles (subcategories of Lines): name -> (RGB, projection line weight).
STYLES = {
    OK: ('KLA Grade Review', (0, 90, 255), 2),
    CLOSE: ('KLA Grade Review - Clearance', (255, 140, 0), 6),
    OVER: ('KLA Grade Review - Over Top', (220, 0, 0), 8),
}
TEXT_TYPE_NAME = 'KLA Grade Review'
TOPO_CATEGORY_NAMES = ('OST_Toposolid', 'OST_Topography')
TEXT_RGB = (220, 0, 0)
NOTE_RISE_FEET = 0.5
RAY_CLEARANCE_FEET = 500.0
WALL_PROBE_INSIDE_FEET = 1.0 / 12.0
FOUNDATION_FUNCTIONS = (2, 3)  # WallFunction: Foundation, Retaining
# Grade labels further than this from the walls' top elevations are not grade.
RANGE_BELOW_FEET = 30.0
RANGE_ABOVE_FEET = 10.0

UP = DB.XYZ.BasisZ
DOWN = DB.XYZ.BasisZ.Negate()

logger = script.get_logger()


class UserError(Exception):
    """A problem the user can fix; shown without an error report."""


# -- Walls and their sampled exterior face ------------------------------------------

def _wall_function(wall):
    param = wall.WallType.get_Parameter(DB.BuiltInParameter.FUNCTION_PARAM)
    return param.AsInteger() if param is not None else None


def collect_walls(uidoc):
    """Return (walls, skipped names): selected walls, else foundation walls in view."""
    doc = uidoc.Document
    selected = [doc.GetElement(element_id) for element_id in uidoc.Selection.GetElementIds()]
    if selected:
        candidates = [element for element in selected if isinstance(element, DB.Wall)]
    else:
        candidates = [wall for wall in DB.FilteredElementCollector(doc, uidoc.ActiveView.Id).OfClass(DB.Wall)
                      if _wall_function(wall) in FOUNDATION_FUNCTIONS]
    walls, skipped = [], []
    for wall in candidates:
        location = wall.Location
        if wall.WallType.Kind != DB.WallKind.Basic or not isinstance(location, DB.LocationCurve):
            skipped.append((wall, 'Stacked, curtain, or unlocated wall'))
            continue
        if not isinstance(location.Curve, (DB.Line, DB.Arc)):
            skipped.append((wall, 'Wall path is not a line or arc'))
            continue
        walls.append(wall)
    return walls, skipped


def _horizontal(vector):
    flat = DB.XYZ(vector.X, vector.Y, 0.0)
    return flat.Normalize() if flat.GetLength() > 1e-9 else flat


def wall_path(wall):
    """Return station dicts along the wall's exterior face.

    Each has chainage, x, y (exterior face), nx, ny (exterior normal), probe
    (point just outside the face), line (where the grade line is drawn), and
    inside (point within the wall for its top).
    """
    curve = wall.Location.Curve
    length = curve.Length
    chainages = stations(length)
    offset = exterior_offset(wall.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).AsInteger(),
                             wall.Width)
    inside = min(wall.Width / 2.0, WALL_PROBE_INSIDE_FEET)

    def right_normal(parameter):
        tangent = _horizontal(curve.ComputeDerivatives(parameter, True).BasisX)
        return DB.XYZ(tangent.Y, -tangent.X, 0.0)

    # Wall.Orientation points to the exterior; turn the curve's right side to match.
    side = 1.0 if right_normal(0.5).DotProduct(wall.Orientation) >= 0 else -1.0
    path = []
    for chainage in chainages:
        parameter = chainage / length if length > 0 else 0.0
        point = curve.Evaluate(parameter, True)
        normal = right_normal(parameter).Multiply(side)
        face = DB.XYZ(point.X, point.Y, 0.0) + normal.Multiply(offset)
        path.append({
            'chainage': chainage,
            'x': face.X, 'y': face.Y, 'nx': normal.X, 'ny': normal.Y,
            'probe': face + normal.Multiply(PROBE_OFFSET_FEET),
            'line': face + normal.Multiply(LINE_OFFSET_FEET),
            'inside': face - normal.Multiply(inside),
        })
    return path


# -- Ray casting -------------------------------------------------------------------

def ray_view(uidoc):
    """Return a non-template 3D view for ray casting: the active one, else {3D}."""
    active = uidoc.ActiveView
    if isinstance(active, DB.View3D) and not active.IsTemplate:
        return active
    for view in DB.FilteredElementCollector(uidoc.Document).OfClass(DB.View3D):
        if not view.IsTemplate and view.Name in ('{3D}', '{3D - ' + uidoc.Application.Application.Username + '}'):
            return view
    for view in DB.FilteredElementCollector(uidoc.Document).OfClass(DB.View3D):
        if not view.IsTemplate:
            return view
    raise UserError('Grade and wall tops are found in a 3D view. Open or create a 3D view first.')


def _hit_z(intersector, point, top_z):
    origin = DB.XYZ(point.X, point.Y, top_z)
    hit = intersector.FindNearest(origin, DOWN)
    if hit is None:
        return None
    return top_z - hit.Proximity


def wall_tops(wall, path, view3d):
    """Return top of wall at each station, from the wall's own faces seen from above."""
    box = wall.get_BoundingBox(None)
    top_z = box.Max.Z + RAY_CLEARANCE_FEET
    intersector = DB.ReferenceIntersector(wall.Id, DB.FindReferenceTarget.Face, view3d)
    tops = [_hit_z(intersector, station['inside'], top_z) for station in path]
    # A wall hidden in the ray view gives no hits; fall back to its box.
    return [box.Max.Z if top is None else top for top in tops], all(top is None for top in tops)


def topo_intersector(view3d):
    categories = List[DB.BuiltInCategory]()
    for name in TOPO_CATEGORY_NAMES:
        category = getattr(DB.BuiltInCategory, name, None)
        if category is not None:
            categories.Add(category)
    intersector = DB.ReferenceIntersector(DB.ElementMulticategoryFilter(categories),
                                          DB.FindReferenceTarget.Face, view3d)
    intersector.FindReferencesInRevitLinks = True
    return intersector


def revit_grades(path, tops, intersector):
    top_z = max(tops) + RAY_CLEARANCE_FEET
    return [_hit_z(intersector, station['probe'], top_z) for station in path]


# -- PDF overlays ----------------------------------------------------------------------

class PdfSource(object):
    """An aligned PDF Overlay: its state, the plan view basis, and its grade labels."""

    def __init__(self, image_type, state, view):
        self.image_type = image_type
        self.state = state
        self.view = view
        self.page_text = None

    @property
    def label(self):
        return u'{}  (aligned in {})'.format(describe_overlay(self.state, True).rsplit(u' · ', 1)[0],
                                              self.view.Name)

    def labels_in_model(self, elevation_range):
        """Return grade labels with x, y in model feet."""
        if self.page_text is None:
            try:
                self.page_text = read_pdf_page_text(self.state['pdf_path'], self.state['page'])
            except (IOError, OSError):
                raise UserError(u'The overlay PDF was not found:\n{}'.format(self.state['pdf_path']))
            except PdfError as error:
                raise UserError(u'The overlay PDF text could not be read: {}'.format(error))
        right, up = self.view.RightDirection, self.view.UpDirection
        labels = pdf_grade.elevation_labels(self.page_text, self.state['pose'],
                                            self.state['page_size'], elevation_range)
        for label in labels:
            vx, vy = label['x'], label['y']
            label['x'] = right.X * vx + up.X * vy
            label['y'] = right.Y * vx + up.Y * vy
        return labels


def find_pdf_sources(doc):
    """Return PDF overlays with local files that are placed in a plan-like view."""
    cache_root = default_cache_root()
    sources = []
    for image_type in DB.FilteredElementCollector(doc).OfClass(DB.ImageType):
        stem = None
        for getter in (lambda: image_type.Path, lambda: DB.Element.Name.GetValue(image_type)):
            try:
                stem = stem or stem_from_image_name(getter())
            except Exception:
                pass
        if not stem:
            continue
        try:
            state = load_state(overlay_paths(cache_root, stem)['state'])
        except (IOError, OSError, ValueError):
            continue
        for instance in DB.FilteredElementCollector(doc).OfClass(DB.ImageInstance):
            if instance.GetTypeId() != image_type.Id:
                continue
            view = doc.GetElement(instance.OwnerViewId)
            if view is not None and abs(view.ViewDirection.Z) > 0.9999:
                sources.append(PdfSource(image_type, state, view))
                break
    return sources


def _usgs_key(doc):
    return 'usgs_' + re.sub(r'\W', '_', doc.Title or 'model')


def _survey_usgs(doc, level):
    """Return the level's elevation from the Survey Point, if the survey is set up."""
    point = DB.BasePoint.GetSurveyPoint(doc)
    value = level.ProjectElevation - point.Position.Z + point.SharedPosition.Z
    return value if abs(value - level.ProjectElevation) > 1.0 else None


def ask_usgs_reference(doc):
    """Ask for a level and its USGS elevation; return (internal Z, USGS elevation).

    The last answer is remembered per model; with none, a set-up Survey Point
    supplies the starting value.
    """
    levels = sorted(DB.FilteredElementCollector(doc).OfClass(DB.Level),
                    key=lambda level: level.ProjectElevation)
    if not levels:
        raise UserError('The model has no levels to tie the USGS elevations to.')
    config = script.get_config()
    saved_name, saved_value = '', ''
    saved = config.get_option(_usgs_key(doc), '')
    if saved and '|' in saved:
        saved_name, saved_value = saved.rsplit('|', 1)
    by_label = OrderedDict()
    for level in levels:
        by_label[u'{}  ({})'.format(level.Name, format_feet_inches(level.Elevation))] = level
    level = None
    if len(levels) == 1:
        level = levels[0]
    else:
        ordered = sorted(by_label, key=lambda label: by_label[label].Name != saved_name)
        picked = forms.SelectFromList.show(
            ordered, title='Level to tie to USGS (e.g. T/SLAB or Level 1)', multiselect=False)
        if not picked:
            script.exit()
        level = by_label[picked]
    if level.Name == saved_name:
        default = saved_value
    else:
        survey = _survey_usgs(doc, level)
        default = '{:.2f}'.format(survey) if survey is not None else ''
    while True:
        text = forms.ask_for_string(
            default=default, title=COMMAND_TITLE,
            prompt=u'USGS elevation of {} (feet, e.g. 5432.50 or 5432\'-6"):'.format(level.Name))
        if text is None:
            script.exit()
        usgs = pdf_grade.parse_elevation(text)
        if usgs is not None:
            break
        forms.alert('Enter the elevation in feet, such as 5432.50 or 5432\'-6".', title=COMMAND_TITLE)
        default = text
    config.set_option(_usgs_key(doc), u'{}|{}'.format(level.Name, text.strip()))
    script.save_config()
    return level, (level.ProjectElevation, usgs)


def pdf_grades(path, labels, origin):
    samples = pdf_grade.project_labels(path, labels)
    values = pdf_grade.interpolate([station['chainage'] for station in path], samples)
    return [None if value is None else pdf_grade.to_internal(value, *origin) for value in values], samples


# -- Drawing -----------------------------------------------------------------------------

def _line_styles(doc):
    """Return {status: GraphicsStyle}, creating missing styles (in a transaction)."""
    categories = doc.Settings.Categories
    lines = categories.get_Item(DB.BuiltInCategory.OST_Lines)
    existing = dict((sub.Name, sub) for sub in lines.SubCategories)
    styles = {}
    for status, (name, rgb, weight) in STYLES.items():
        style = existing.get(name)
        if style is None:
            style = categories.NewSubcategory(lines, name)
            style.LineColor = DB.Color(*rgb)
            style.SetLineWeight(weight, DB.GraphicsStyleType.Projection)
        styles[status] = style.GetGraphicsStyle(DB.GraphicsStyleType.Projection)
    return styles


def _existing_style_ids(doc):
    lines = doc.Settings.Categories.get_Item(DB.BuiltInCategory.OST_Lines)
    names = set(name for name, _, _ in STYLES.values())
    return set(sub.GetGraphicsStyle(DB.GraphicsStyleType.Projection).Id.ToString()
               for sub in lines.SubCategories if sub.Name in names)


def _text_type(doc):
    for text_type in DB.FilteredElementCollector(doc).OfClass(DB.TextNoteType):
        if DB.Element.Name.GetValue(text_type) == TEXT_TYPE_NAME:
            return text_type
    base = doc.GetElement(doc.GetDefaultElementTypeId(DB.ElementTypeGroup.TextNoteType))
    text_type = base.Duplicate(TEXT_TYPE_NAME)
    color = text_type.get_Parameter(DB.BuiltInParameter.LINE_COLOR)
    if color is not None:
        color.Set(TEXT_RGB[0] + TEXT_RGB[1] * 256 + TEXT_RGB[2] * 65536)
    return text_type


def notes_allowed(view):
    if isinstance(view, DB.View3D):
        return view.IsLocked
    return view.ViewType in (DB.ViewType.FloorPlan, DB.ViewType.CeilingPlan, DB.ViewType.EngineeringPlan,
                             DB.ViewType.AreaPlan, DB.ViewType.Section, DB.ViewType.Elevation,
                             DB.ViewType.Detail)


def _point(station, z):
    line = station['line']
    return DB.XYZ(line.X, line.Y, z)


def draw_wall(doc, result, styles, text_type, view):
    """Draw one wall's grade segments and flag notes; return the note count."""
    path, points = result['path'], result['profile']
    is_line = isinstance(result['wall'].Location.Curve, DB.Line)
    tolerance = doc.Application.ShortCurveTolerance
    shared_plane = None
    for first, second, status in segments(points):
        start = _point(path[first], points[first]['grade'])
        end = _point(path[second], points[second]['grade'])
        if start.DistanceTo(end) < tolerance:
            continue
        normal = _horizontal(DB.XYZ(end.Y - start.Y, start.X - end.X, 0.0))
        if is_line and shared_plane is not None:
            plane = shared_plane
        else:
            plane = DB.SketchPlane.Create(doc, DB.Plane.CreateByNormalAndOrigin(normal, start))
            if is_line:
                shared_plane = plane
        curve = doc.Create.NewModelCurve(DB.Line.CreateBound(start, end), plane)
        curve.LineStyle = styles[status]
    notes = 0
    if text_type is not None:
        for run in result['runs']:
            station = path[run['worst']]
            point = points[run['worst']]
            position = _point(station, point['grade'] + NOTE_RISE_FEET)
            DB.TextNote.Create(doc, view.Id, position, note_text(point['clearance']), text_type.Id)
            notes += 1
    return notes


# -- Ghosted topography (active 3D view only) --------------------------------------------

def _topo_categories(doc):
    """Return [(name, Category)] for the topography categories in this Revit version."""
    found = []
    for name in TOPO_CATEGORY_NAMES:
        built_in = getattr(DB.BuiltInCategory, name, None)
        category = DB.Category.GetCategory(doc, built_in) if built_in is not None else None
        if category is not None:
            found.append((name, category))
    return found


def ghost_view(doc, view, state):
    """Show topography see-through and halftone in view; record originals in state.

    Returns a reason text when the view cannot be ghosted, else ''.
    """
    if not isinstance(view, DB.View3D) or view.IsTemplate:
        return 'Topography is ghosted only in a 3D view; open the 3D view and run again to see it.'
    key = ghost.doc_key(doc.PathName, doc.Title)
    changed = False
    for name, category in _topo_categories(doc):
        if not view.IsCategoryOverridable(category.Id):
            continue
        overrides = view.GetCategoryOverrides(category.Id)
        ghost.remember(state, key, view.UniqueId, name, overrides.Transparency,
                       overrides.Halftone, view.GetCategoryHidden(category.Id))
        overrides.SetSurfaceTransparency(ghost.GHOST_TRANSPARENCY)
        overrides.SetHalftone(True)
        view.SetCategoryOverrides(category.Id, overrides)
        if view.CanCategoryBeHidden(category.Id):
            view.SetCategoryHidden(category.Id, False)
        changed = True
    if not changed:
        return 'Topography could not be ghosted in this view (its view template may control visibility).'
    return ''


def restore_views(doc, recorded):
    """Put back the recorded topography settings; return the views restored."""
    categories = dict(_topo_categories(doc))
    restored = 0
    for view_id, settings in recorded.items():
        view = doc.GetElement(view_id)
        if not isinstance(view, DB.View):
            continue
        for name, original in settings.items():
            category = categories.get(name)
            if category is None or not view.IsCategoryOverridable(category.Id):
                continue
            overrides = view.GetCategoryOverrides(category.Id)
            overrides.SetSurfaceTransparency(int(original.get('transparency', 0)))
            overrides.SetHalftone(bool(original.get('halftone', False)))
            view.SetCategoryOverrides(category.Id, overrides)
            if view.CanCategoryBeHidden(category.Id):
                view.SetCategoryHidden(category.Id, bool(original.get('hidden', False)))
        restored += 1
    return restored


def draw_strip(doc, result, view):
    """Add a see-through grade strip outside the wall (PDF source); return it or None."""
    path, points = result['path'], result['profile']
    edge = [None if point['grade'] is None else
            (station['line'].X, station['line'].Y, point['grade'])
            for station, point in zip(path, points)]
    normals = [(station['nx'], station['ny']) for station in path]
    quads = ghost.strip_quads(edge, ghost.STRIP_WIDTH_FEET, normals)
    if not quads:
        return None
    builder = DB.TessellatedShapeBuilder()
    builder.OpenConnectedFaceSet(False)
    for quad in quads:
        corners = List[DB.XYZ]([DB.XYZ(*corner) for corner in quad])
        builder.AddFace(DB.TessellatedFace(corners, DB.ElementId.InvalidElementId))
    builder.CloseConnectedFaceSet()
    builder.Target = DB.TessellatedShapeBuilderTarget.Mesh
    builder.Fallback = DB.TessellatedShapeBuilderFallback.Salvage
    builder.Build()
    shape = DB.DirectShape.CreateElement(doc, DB.ElementId(DB.BuiltInCategory.OST_GenericModel))
    shape.ApplicationId = ghost.STRIP_APP_ID
    shape.ApplicationDataId = ghost.STRIP_DATA_ID
    shape.SetShape(builder.GetBuildResult().GetGeometricalObjects())
    shape.Name = 'Wall Grade Check - PDF grade'
    if isinstance(view, DB.View3D):
        overrides = DB.OverrideGraphicSettings()
        overrides.SetSurfaceTransparency(ghost.STRIP_TRANSPARENCY)
        overrides.SetHalftone(True)
        view.SetElementOverrides(shape.Id, overrides)
    return shape


def _strip_ids(doc):
    return [shape.Id for shape in DB.FilteredElementCollector(doc).OfClass(DB.DirectShape)
            if shape.ApplicationId == ghost.STRIP_APP_ID and shape.ApplicationDataId == ghost.STRIP_DATA_ID]


def clear_review(doc):
    """Delete review lines, notes, and grade strips, and un-ghost topography.

    Returns (elements deleted, views restored).
    """
    style_ids = _existing_style_ids(doc)
    ids = [curve.Id for curve in DB.FilteredElementCollector(doc).OfClass(DB.CurveElement)
           if curve.LineStyle is not None and curve.LineStyle.Id.ToString() in style_ids]
    text_type_ids = set(text_type.Id.ToString()
                        for text_type in DB.FilteredElementCollector(doc).OfClass(DB.TextNoteType)
                        if DB.Element.Name.GetValue(text_type) == TEXT_TYPE_NAME)
    ids += [note.Id for note in DB.FilteredElementCollector(doc).OfClass(DB.TextNote)
            if note.GetTypeId().ToString() in text_type_ids]
    ids += _strip_ids(doc)
    state_path = ghost.default_state_path()
    state = ghost.load(state_path)
    recorded = ghost.take(state, ghost.doc_key(doc.PathName, doc.Title))
    restored = 0
    if ids or recorded:
        with revit.Transaction('Wall Grade Check - Clear', doc=doc):
            if ids:
                doc.Delete(List[DB.ElementId](ids))
            restored = restore_views(doc, recorded)
        ghost.save(state_path, state)
    return len(ids), restored


# -- Workflow -----------------------------------------------------------------------------

def ask_choice(options, message):
    choice = forms.CommandSwitchWindow.show(options, message=message)
    if not choice:
        script.exit()
    return choice


def sample_walls(walls, view3d):
    """Return [(wall, path, tops, tops_missing)] for each wall."""
    sampled = []
    for wall in walls:
        path = wall_path(wall)
        tops, tops_missing = wall_tops(wall, path, view3d)
        sampled.append((wall, path, tops, tops_missing))
    return sampled


def analyse(sampled, limit_feet, grade_source):
    """Build each wall's profile; grade_source(path, tops) returns (grades, samples)."""
    results = []
    for wall, path, tops, tops_missing in sampled:
        grades, samples = grade_source(path, tops)
        chainages = [station['chainage'] for station in path]
        profile = build_profile(chainages, grades, tops, limit_feet)
        results.append({
            'wall': wall, 'path': path, 'profile': profile, 'runs': flagged_runs(profile),
            'tops_missing': tops_missing, 'samples': samples,
        })
    return results


def report(output, results, skipped, source_text, limit_inches, notes_note):
    output.print_md('## Wall Grade Check')
    output.print_md('{}. Flags grade closer than {:g}" to the top of wall, and grade at or '
                    'above it.'.format(source_text, limit_inches))
    if notes_note:
        output.print_md(notes_note)
    rows = []
    for result in results:
        wall, profile = result['wall'], result['profile']
        lowest = min_clearance(profile)
        flags = []
        for run in result['runs']:
            label = 'Over top' if run['status'] == OVER else 'Clearance'
            flags.append('{} {:.1f}-{:.1f} ft: {}'.format(label, run['start'], run['end'],
                                                         note_text(run['clearance'])))
        gaps = ['{:.1f}-{:.1f} ft'.format(start, end) for start, end in no_data_ranges(profile)]
        notes = []
        if result['tops_missing']:
            notes.append('Wall not seen in the 3D view; top from its bounding box')
        if result['samples'] is not None:
            notes.append('{} PDF label(s) used'.format(len(result['samples'])))
        rows.append([
            output.linkify(wall.Id),
            DB.Element.Name.GetValue(wall.WallType),
            '{:.1f}'.format(wall.Location.Curve.Length),
            ('-' if lowest is None else
             (format_inches(lowest) + (' above' if lowest < 0 else ''))),
            '<br>'.join(flags) or 'None',
            ', '.join(gaps) or 'None',
            '; '.join(notes),
        ])
    output.print_table(table_data=rows,
                       columns=['Wall', 'Type', 'Length (ft)', 'Min clearance', 'Flags',
                                'No grade', 'Notes'],
                       title='Walls')
    if skipped:
        output.print_table(table_data=[[output.linkify(wall.Id), reason] for wall, reason in skipped],
                           columns=['Wall', 'Skipped because'], title='Skipped')


def run():
    uidoc = revit.uidoc
    doc = uidoc.Document
    view = uidoc.ActiveView
    output = script.get_output()

    choice = ask_choice([SOURCE_REVIT, SOURCE_PDF, CLEAR], 'Wall Grade Check: choose an action.')
    if choice == CLEAR:
        count, restored = clear_review(doc)
        forms.alert('Deleted {} review line(s), note(s), and grade strip(s); restored topography in '
                    '{} view(s).'.format(count, restored), title=COMMAND_TITLE)
        return

    walls, skipped = collect_walls(uidoc)
    if not walls:
        raise UserError('Select foundation walls, or open a view that shows walls whose type '
                        'Function is Foundation or Retaining.')
    view3d = ray_view(uidoc)

    clearance_text = forms.ask_for_string(
        default='8', prompt='Flag grade closer than this to the top of wall (inches):',
        title=COMMAND_TITLE)
    if clearance_text is None:
        script.exit()
    limit_inches = clamp_clearance(clearance_text)
    limit_feet = limit_inches / 12.0
    sampled = sample_walls(walls, view3d)

    if choice == SOURCE_REVIT:
        intersector = topo_intersector(view3d)

        def grade_source(path, tops):
            return revit_grades(path, tops, intersector), None
        source_text = 'Grade from Revit topography (Toposolids and Topography, links included) ' \
                      'seen in 3D view "{}"'.format(view3d.Name)
    else:
        sources = find_pdf_sources(doc)
        if not sources:
            raise UserError('No aligned PDF Overlay was found. Import the grading plan with PDF Overlay '
                            'in a plan view and align it first.')
        if len(sources) == 1:
            source = sources[0]
        else:
            by_label = dict((item.label, item) for item in sources)
            picked = forms.SelectFromList.show(sorted(by_label), title='Grading plan overlay',
                                               multiselect=False)
            if not picked:
                script.exit()
            source = by_label[picked]
        level, origin = ask_usgs_reference(doc)
        # Plausible grade range in USGS, from the walls' tops.
        all_tops = [top for _, _, tops, _ in sampled for top in tops]
        low = pdf_grade.to_reported(min(all_tops) - RANGE_BELOW_FEET, *origin)
        high = pdf_grade.to_reported(max(all_tops) + RANGE_ABOVE_FEET, *origin)
        labels = source.labels_in_model((low, high))

        def grade_source(path, tops):
            return pdf_grades(path, labels, origin)
        source_text = u'Grade from {} labels in {} (USGS; {} = USGS {:.2f})'.format(
            len(labels), os.path.basename(source.state['pdf_path']), level.Name, origin[1])

    notes_note = []
    state_path = ghost.default_state_path()
    ghost_state = ghost.load(state_path)
    # One undo step: ghost first, so topography hidden in this 3D view is shown
    # again before grade is read through it, then draw.
    group = DB.TransactionGroup(doc, 'Wall Grade Check - Draw')
    group.Start()
    try:
        with revit.Transaction('Wall Grade Check - Ghost Topography', doc=doc):
            ghost_reason = ghost_view(doc, view, ghost_state)
        results = analyse(sampled, limit_feet, grade_source)
        log('analysed {} wall(s)'.format(len(results)))
        with revit.Transaction('Wall Grade Check - Draw Lines', doc=doc):
            styles = _line_styles(doc)
            text_type = _text_type(doc) if notes_allowed(view) else None
            notes = sum(draw_wall(doc, result, styles, text_type, view) for result in results)
            strips = 0
            if choice == SOURCE_PDF:
                strips = sum(1 for result in results if draw_strip(doc, result, view) is not None)
        group.Assimilate()
    except BaseException:
        if group.HasStarted() and not group.HasEnded():
            group.RollBack()
        raise
    if not ghost_reason:
        ghost.save(state_path, ghost_state)
        notes_note.append('Topography is ghosted in this 3D view until **Clear review lines**.')
    else:
        notes_note.append(ghost_reason)
    if strips:
        notes_note.append('{} see-through PDF grade strip(s) {:g} ft wide show grade outside the walls '
                          '(Generic Models; removed by Clear).'.format(strips, ghost.STRIP_WIDTH_FEET))
    if text_type is None and any(result['runs'] for result in results):
        notes_note.append('Flag notes need a plan, section, or elevation view, or a locked 3D view. '
                          'Flagged runs are still drawn in orange and red.')
    report(output, results, skipped, source_text, limit_inches, '  \n'.join(notes_note))

    flagged = [result['wall'].Id for result in results if result['runs']]
    if flagged:
        uidoc.Selection.SetElementIds(List[DB.ElementId](flagged))
    log('drew {} wall(s), {} note(s), {} flagged'.format(len(results), notes, len(flagged)))


def main():
    log('--- start')
    try:
        run()
    except UserError as error:
        forms.alert(u'{}'.format(error), title=COMMAND_TITLE)
    except Exception as error:
        log('failed:\n' + traceback.format_exc())
        forms.alert(u'Wall Grade Check failed:\n{}\n\n{}'.format(error, report_error('Draw')),
                    title=COMMAND_TITLE, warn_icon=True)


if __name__ == '__main__':
    main()
