# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Column Base Plate QC"
__version__ = "v0.0"

import datetime
import json
import math
import os
import traceback

# The pyRevit output window can render blank, so errors are also written to a
# log file that is readable without Revit.
LOG_PATH = os.path.join(os.environ.get('LOCALAPPDATA') or os.environ.get('TEMP') or '.',
                        'KLA Tools', 'Column Base Plate QC', 'baseplate_qc.log')


def log(message):
    try:
        folder = os.path.dirname(LOG_PATH)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with open(LOG_PATH, 'a') as log_file:
            log_file.write('{:%Y-%m-%d %H:%M:%S} {}\n'.format(datetime.datetime.now(), message))
    except Exception:
        pass


try:
    from Autodesk.Revit.Exceptions import OperationCanceledException
    from pyrevit import DB, HOST_APP, UI, forms, script
    from pyrevit.compat import get_elementid_value_func
    # pyrevit.framework loads the engine's IronPython.Wpf assembly that backs wpf.
    from pyrevit.framework import wpf
    from System.Collections.Generic import List
    from System.Windows.Interop import WindowInteropHelper

    from GUI.WPF_Base import my_WPF
    from baseplate_qc.details import describe, read_type_details
    from baseplate_qc.layout import layout_plate, parse_column_size
    from baseplate_qc.schedule import (
        SCHEDULE_TITLE,
        edge_distance,
        format_inches,
        normalize_mark,
        normalize_text,
        read_base_plate_schedule,
        read_edge_distances,
    )
except Exception:
    log('import failed:\n' + traceback.format_exc())
    raise


COMMAND_TITLE = 'Column Base Plate QC'
MARK_PARAMETER = 'Column Base Plate Type'
# Group types named with this prefix are the tool's drawings; Clear deletes them.
GROUP_PREFIX = 'KLA BP QC - '
OK_RGB = (0, 90, 255)
ISSUE_RGB = (230, 0, 0)
COLUMN_RGB = (128, 128, 128)
LINE_WEIGHT = 5
# A wall counts as the column's support when its height range is within this
# many feet of the column base.
WALL_Z_REACH = 2.0
# Column size parameters (depth, width) tried when the type name is not an HSS size.
SIZE_PARAMETERS = (('d', 'bf'), ('Depth', 'Width'), ('h', 'b'))


get_elementid_value = get_elementid_value_func()


class UserError(Exception):
    """A problem the user can fix; shown as the palette status."""


# -- Schedule ----------------------------------------------------------------------

def _element_name(element):
    try:
        return element.Name
    except Exception:
        return DB.Element.Name.__get__(element)


def find_schedule_views(doc):
    """Return [(view, [text notes])] for views whose text includes the schedule title."""
    by_view = {}
    for note in DB.FilteredElementCollector(doc).OfClass(DB.TextNote):
        by_view.setdefault(get_elementid_value(note.OwnerViewId), []).append(note)
    found = []
    for notes in by_view.values():
        if any(SCHEDULE_TITLE in normalize_text(note.Text) for note in notes):
            view = doc.GetElement(notes[0].OwnerViewId)
            if view is not None:
                found.append((view, notes))
    found.sort(key=lambda item: _element_name(item[0]))
    return found


def note_cells(view, notes):
    """Return schedule-reader cells for text notes, in the view's right/up coordinates."""
    cells = []
    for note in notes:
        box = note.get_BoundingBox(view)
        if box is None:
            continue
        xs, ys = [], []
        for corner in (box.Min, box.Max):
            xs.append(corner.DotProduct(view.RightDirection))
            ys.append(corner.DotProduct(view.UpDirection))
        cells.append({'text': note.Text, 'xmin': min(xs), 'xmax': max(xs),
                      'ymin': min(ys), 'ymax': max(ys)})
    return cells


def view_geometry(view):
    """Return (polylines, arcs, dimension segments, sources) drawn in a view.

    Points are in the view's right/up coordinates. Detail lines, detail
    components, filled regions, and imported CAD all give their curves;
    groups are skipped because their members are collected on their own.
    sources describe each element read, for troubleshooting.
    """
    doc = view.Document
    right, up = view.RightDirection, view.UpDirection
    to_2d = lambda point: (point.DotProduct(right), point.DotProduct(up))
    polylines, arcs, dims, sources = [], [], [], []

    def add_curve(curve):
        try:
            points = [to_2d(point) for point in curve.Tessellate()]
        except Exception:
            return
        if len(points) > 1:
            polylines.append(points)
        if isinstance(curve, DB.Arc):
            sweep = curve.GetEndParameter(1) - curve.GetEndParameter(0) if curve.IsBound else 2 * math.pi
            arcs.append({'center': to_2d(curve.Center), 'radius': curve.Radius, 'sweep': abs(sweep)})

    def walk(geometry):
        for item in geometry or []:
            if isinstance(item, DB.Curve):
                add_curve(item)
            elif isinstance(item, DB.PolyLine):
                polylines.append([to_2d(point) for point in item.GetCoordinates()])
            elif isinstance(item, DB.GeometryInstance):
                walk(item.GetInstanceGeometry())

    options = DB.Options()
    options.View = view
    for element in DB.FilteredElementCollector(doc, view.Id).WhereElementIsNotElementType():
        if isinstance(element, (DB.TextNote, DB.Group)) or element.OwnerViewId != view.Id:
            continue
        counts = (len(polylines), len(arcs), len(dims))
        try:
            if isinstance(element, DB.Dimension):
                dims.extend(_dimension_segments(element, to_2d))
            elif isinstance(element, DB.FilledRegion):
                for loop in element.GetBoundaries():
                    for curve in loop:
                        add_curve(curve)
            else:
                walk(element.get_Geometry(options))
        except Exception:
            log('geometry skipped for {}:\n{}'.format(get_elementid_value(element.Id), traceback.format_exc()))
        box = element.get_BoundingBox(view)
        category = element.Category.Name if element.Category is not None else ''
        symbol = doc.GetElement(element.GetTypeId())
        sources.append({'id': get_elementid_value(element.Id), 'class': element.GetType().Name,
                        'category': category, 'type': _element_name(symbol) if symbol is not None else '',
                        'box': [to_2d(box.Min), to_2d(box.Max)] if box is not None else None,
                        'polylines': [counts[0], len(polylines)], 'arcs': [counts[1], len(arcs)],
                        'dims': [counts[2], len(dims)]})
    return polylines, arcs, dims, sources


def _dimension_segments(dimension, to_2d):
    line = dimension.Curve
    if not isinstance(line, DB.Line):
        return []
    direction = to_2d(line.Direction)
    equal = bool(getattr(dimension, 'AreSegmentsEqual', False))
    segments = list(dimension.Segments) if dimension.NumberOfSegments > 1 else [dimension]
    return [{'value': segment.Value, 'text': segment.ValueOverride or '', 'origin': to_2d(segment.Origin),
             'direction': direction, 'equal': equal}
            for segment in segments if segment.Value is not None]


def read_schedule(doc, view_id):
    """Return the schedule, anchor rod edge distances, and detail types from the schedule view.

    Returns {'entries', 'edges', 'types' {key: definition}, 'type_problems'
    {key: reason}, 'problems' [str]}.
    """
    view = doc.GetElement(view_id) if view_id is not None else None
    if view is None:
        raise UserError('No base plate schedule view. Click Refresh, or place the schedule text in the model.')
    notes = [note for note in DB.FilteredElementCollector(doc, view.Id).OfClass(DB.TextNote)
             if note.OwnerViewId == view.Id]
    cells = note_cells(view, notes)
    entries, problems = read_base_plate_schedule(cells)
    edges = read_edge_distances(cells)
    if not edges:
        problems.append('No anchor rod requirements table found; built-in edge distances are used.')
    polylines, arcs, dims, sources = view_geometry(view)
    types, type_problems = read_type_details(cells, polylines, arcs, dims)
    if not types and not type_problems:
        problems.append('No TYPE A, TYPE B, ... detail labels found.')
    if not entries or not edges or type_problems or not types:
        path = dump_view(view, cells, polylines, arcs, dims, sources)
        if path:
            problems.append('The view\'s text and linework were written to {} for '
                            'troubleshooting.'.format(path))
    return {'entries': entries, 'edges': edges, 'types': types, 'type_problems': type_problems,
            'problems': problems}


def _ascii(value):
    """Return value with text made ASCII (other characters as \\uXXXX).

    IronPython's json writer fails on symbol-font characters such as the
    diameter glyph.
    """
    if isinstance(value, dict):
        return dict((_ascii(key), _ascii(item)) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return [_ascii(item) for item in value]
    if isinstance(value, basestring):
        return ''.join(char if ord(char) < 128 else '\\u{:04x}'.format(ord(char)) for char in value)
    return value


def dump_view(view, cells, polylines, arcs, dims, sources):
    """Write the view's text, linework, and dimensions so an unreadable schedule can be diagnosed."""
    path = os.path.join(os.path.dirname(LOG_PATH), 'schedule_view.json')
    try:
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        data = _ascii({'view': _element_name(view), 'cells': cells, 'polylines': polylines,
                       'arcs': arcs, 'dims': dims, 'sources': sources})
        with open(path, 'w') as dump:
            json.dump(data, dump)
        return path
    except Exception:
        log('schedule dump failed:\n' + traceback.format_exc())
        return None


# -- Model -------------------------------------------------------------------------

def _xy(point):
    return (point.X, point.Y)


def column_point(column):
    location = column.Location
    if isinstance(location, DB.LocationPoint):
        return location.Point
    if isinstance(location, DB.LocationCurve):
        curve = location.Curve
        start, end = curve.GetEndPoint(0), curve.GetEndPoint(1)
        return start if start.Z <= end.Z else end
    return None


def column_mark(column):
    for element in (column, column.Document.GetElement(column.GetTypeId())):
        parameter = element.LookupParameter(MARK_PARAMETER) if element is not None else None
        if parameter is not None and parameter.HasValue:
            value = parameter.AsString() if parameter.StorageType == DB.StorageType.String \
                else parameter.AsValueString()
            if value and value.strip():
                return value.strip()
    return None


def column_size(column):
    """Return a parse_column_size dict and the type label for a column."""
    symbol = column.Document.GetElement(column.GetTypeId())
    label = '{} {}'.format(symbol.FamilyName, _element_name(symbol)) if symbol is not None else ''
    size = parse_column_size(label)
    if size is None and symbol is not None:
        for depth_name, width_name in SIZE_PARAMETERS:
            depth = symbol.LookupParameter(depth_name) or column.LookupParameter(depth_name)
            width = symbol.LookupParameter(width_name) or column.LookupParameter(width_name)
            if depth is not None and width is not None and depth.AsDouble() > 0 and width.AsDouble() > 0:
                size = {'shape': 'rect', 'depth': depth.AsDouble() * 12, 'width': width.AsDouble() * 12}
                break
    return size, label


def collect_walls(doc):
    """Return wall dicts for nearest_wall, each with its height range (feet)."""
    walls = []
    for wall in DB.FilteredElementCollector(doc).OfClass(DB.Wall):
        location = wall.Location
        box = wall.get_BoundingBox(None)
        if not isinstance(location, DB.LocationCurve) or box is None:
            continue
        try:
            points = [_xy(point) for point in location.Curve.Tessellate()]
        except Exception:
            continue
        walls.append({'id': wall.Id, 'points': points, 'width': wall.Width,
                      'zmin': box.Min.Z, 'zmax': box.Max.Z})
    return walls


def supporting_walls(walls, base_z):
    return [wall for wall in walls
            if wall['zmin'] - WALL_Z_REACH <= base_z <= wall['zmax'] + WALL_Z_REACH]


# -- Drawing -----------------------------------------------------------------------

def _overrides(rgb):
    settings = DB.OverrideGraphicSettings()
    settings.SetProjectionLineColor(DB.Color(*rgb))
    settings.SetProjectionLineWeight(LINE_WEIGHT)
    return settings


def _model(view, xy):
    return DB.XYZ(xy[0], xy[1], view.Origin.Z)


def _polygon_curves(view, points):
    closed = list(points) + [points[0]]
    return [DB.Line.CreateBound(_model(view, a), _model(view, b)) for a, b in zip(closed, closed[1:])]


def _circle(view, center, radius):
    return DB.Arc.Create(_model(view, center), radius, 0.0, 2.0 * math.pi, DB.XYZ.BasisX, DB.XYZ.BasisY)


def draw_plate(doc, view, column, result, text_type_id):
    """Draw one layout as a detail group; return its group type id."""
    color = _overrides(ISSUE_RGB if result['issues'] else OK_RGB)
    gray = _overrides(COLUMN_RGB)
    ids = List[DB.ElementId]()

    def add(curve, settings):
        detail = doc.Create.NewDetailCurve(view, curve)
        view.SetElementOverrides(detail.Id, settings)
        ids.Add(detail.Id)

    for curve in _polygon_curves(view, result['plate']):
        add(curve, color)
    for center, radius in result['rods']:
        add(_circle(view, center, radius), color)
    shape = result['column']
    if isinstance(shape, list):
        for curve in _polygon_curves(view, shape):
            add(curve, gray)
    elif shape is not None:
        add(_circle(view, shape[0], shape[1]), gray)
    options = DB.TextNoteOptions(text_type_id)
    options.HorizontalAlignment = DB.HorizontalTextAlignment.Left
    note = DB.TextNote.Create(doc, view.Id, _model(view, result['label']), result['text'], options)
    view.SetElementOverrides(note.Id, color)
    ids.Add(note.Id)

    group = doc.Create.NewGroup(ids)
    group.GroupType.Name = '{}{} - {} - {}'.format(
        GROUP_PREFIX, result['mark'], get_elementid_value(column.Id), get_elementid_value(view.Id))
    return group.GroupType.Id


def qc_group_type_ids(doc, view=None):
    """Return the tool's group type ids, all of them or only those placed in view."""
    if view is None:
        return [group_type.Id for group_type in DB.FilteredElementCollector(doc).OfClass(DB.GroupType)
                if _element_name(group_type).startswith(GROUP_PREFIX)]
    ids = []
    for group in DB.FilteredElementCollector(doc, view.Id).OfClass(DB.Group):
        if group.OwnerViewId == view.Id and _element_name(group.GroupType).startswith(GROUP_PREFIX):
            if group.GroupType.Id not in ids:
                ids.append(group.GroupType.Id)
    return ids


def delete_group_types(doc, type_ids, name):
    """Delete group types (and so their groups) in one transaction; return the count."""
    live = [type_id for type_id in type_ids if doc.GetElement(type_id) is not None]
    if not live:
        return 0
    transaction = DB.Transaction(doc, name)
    transaction.Start()
    try:
        doc.Delete(List[DB.ElementId](live))
        transaction.Commit()
    except Exception:
        transaction.RollBack()
        raise
    return len(live)


def draw_view(doc, view, schedule):
    """Replace the view's base plate drawing; return (rows, group type ids, flagged column ids)."""
    walls = collect_walls(doc)
    text_type_id = doc.GetDefaultElementTypeId(DB.ElementTypeGroup.TextNoteType)
    columns = DB.FilteredElementCollector(doc, view.Id) \
        .OfCategory(DB.BuiltInCategory.OST_StructuralColumns).WhereElementIsNotElementType().ToElements()
    rows, type_ids, flagged = [], [], []
    transaction = DB.Transaction(doc, 'Column Base Plate QC - Draw')
    transaction.Start()
    try:
        old = qc_group_type_ids(doc, view)
        if old:
            doc.Delete(List[DB.ElementId](old))
        for column in columns:
            row, type_id = _draw_column(doc, view, column, schedule, walls, text_type_id)
            rows.append(row)
            if type_id is not None:
                type_ids.append(type_id)
            if row['issues']:
                flagged.append(column.Id)
        transaction.Commit()
    except Exception:
        transaction.RollBack()
        raise
    return rows, type_ids, flagged


def _draw_column(doc, view, column, schedule, walls, text_type_id):
    row = {'column': column.Id, 'mark': '', 'plate': '', 'orientation': '', 'issues': []}
    mark = column_mark(column)
    if not mark:
        row['issues'].append('No {} value.'.format(MARK_PARAMETER))
        return row, None
    row['mark'] = mark
    entry = schedule['entries'].get(normalize_mark(mark))
    if entry is None:
        row['issues'].append('{} is not in the base plate schedule.'.format(mark))
        return row, None
    if not entry['length'] or not entry['width']:
        row['issues'].append('{} has no readable plate size in the schedule.'.format(mark))
        return row, None
    definition = schedule['types'].get(entry['type'])
    if definition is None:
        row['issues'].append('Not drawn: {}'.format(schedule['type_problems'].get(
            entry['type'], 'no TYPE {} detail was found.'.format(entry['type']))))
        return row, None
    point = column_point(column)
    if point is None:
        row['issues'].append('Column has no location.')
        return row, None
    size, label = column_size(column)
    box = column.get_BoundingBox(None)
    base_z = box.Min.Z if box is not None else point.Z
    hand = column.HandOrientation if isinstance(column, DB.FamilyInstance) else None
    result = layout_plate(entry, definition, edge_distance(entry['rod_diameter'], schedule['edges']),
                          _xy(point), size, _xy(hand) if hand is not None else None,
                          supporting_walls(walls, base_z))
    result['mark'] = normalize_mark(mark)
    if size is None:
        result['issues'].append('Column size not read from "{}"; column outline not drawn.'.format(label))
    row['plate'] = 'Type {} ({}) {} x {}, {} rods'.format(
        entry['type'], describe(definition).split(' plate')[0], format_inches(entry['length']),
        format_inches(entry['width']), format_inches(entry['rod_diameter']))
    row['orientation'] = 'Along wall' if result['axis_source'] == 'wall' else 'Column axis'
    row['issues'] = result['issues']
    return row, draw_plate(doc, view, column, result, text_type_id)


def _mark_order(mark):
    """Sort BP2 before BP10."""
    digits = ''.join(char for char in mark if char.isdigit())
    return (mark.rstrip('0123456789'), int(digits) if digits else 0, mark)


def report(output, view, rows, problems):
    output.print_md('## Column Base Plate QC: {}'.format(_element_name(view)))
    for problem in problems:
        output.print_md('- Schedule: {}'.format(problem))
    flagged = [row for row in rows if row['issues']]
    if not flagged:
        output.print_md('All {} base plates drawn with no issues.'.format(len(rows)))
        return
    table = [[output.linkify(row['column']), row['mark'], row['plate'], row['orientation'],
              '<br>'.join(row['issues'])] for row in flagged]
    output.print_table(table, columns=['Column', 'Mark', 'Plate', 'Orientation', 'Issues'],
                       title='{} of {} columns to review'.format(len(flagged), len(rows)))


# -- Palette -----------------------------------------------------------------------

class ActionHandler(UI.IExternalEventHandler):
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
        except UserError as error:
            self.palette.set_status(str(error))
        except Exception as error:
            log('action failed:\n' + traceback.format_exc())
            self.palette.set_status(u'Failed: {}\nDetails are in {}.'.format(error, LOG_PATH))

    def GetName(self):
        return COMMAND_TITLE


class BasePlateQcPalette(my_WPF):
    def __init__(self, handler, action_event, output):
        self.handler = handler
        self.action_event = action_event
        # Captured at launch; pyRevit binds output to the running command.
        self.output = output
        self.schedule_views = []
        # (document, group type id) for each drawing made while this is open.
        self.drawn = []
        self.add_wpf_resource()
        wpf.LoadComponent(self, os.path.join(os.path.dirname(__file__), 'BasePlateQcPalette.xaml'))
        WindowInteropHelper(self).Owner = HOST_APP.proc_window
        self.Closed += self.palette_closed

    def run(self, action, status):
        if self.handler.action is not None:
            self.set_status('Busy with the previous action; try again in a moment.')
            return
        self.set_status(status)
        self.handler.action = action
        self.action_event.Raise()

    def set_status(self, message):
        self.status_text.Text = message

    def load_schedule_views(self, doc):
        self.schedule_views = [(view.Id, _element_name(view)) for view, _ in find_schedule_views(doc)]
        self.schedule_list.Items.Clear()
        for _, name in self.schedule_views:
            self.schedule_list.Items.Add(name)
        if self.schedule_views:
            self.schedule_list.SelectedIndex = 0
        else:
            self.schedule_text.Text = ('No view has text reading "{}". The schedule must be text notes '
                                       '(not an imported drawing).'.format(SCHEDULE_TITLE))

    def selected_schedule_view(self):
        index = self.schedule_list.SelectedIndex
        return self.schedule_views[index][0] if 0 <= index < len(self.schedule_views) else None

    def show_schedule_summary(self, doc):
        schedule = read_schedule(doc, self.selected_schedule_view())
        entries = schedule['entries']
        lines = ['{} marks read: {}.'.format(len(entries), ', '.join(sorted(entries, key=_mark_order)) or 'none')]
        lines.append('Edge distances from the anchor rod table.' if schedule['edges']
                     else 'Built-in edge distances.')
        for key in sorted(schedule['types']):
            lines.append('TYPE {}: {}.'.format(key, describe(schedule['types'][key])))
        for key in sorted(schedule['type_problems']):
            lines.append('Left out: {}'.format(schedule['type_problems'][key]))
        lines.extend(schedule['problems'])
        self.schedule_text.Text = '\n'.join(lines)

    # Buttons --------------------------------------------------------------------

    def button_refresh(self, sender, e):
        def action(uiapp):
            doc = uiapp.ActiveUIDocument.Document
            self.load_schedule_views(doc)
            self.set_status('Found {} schedule view(s).'.format(len(self.schedule_views)))
        self.run(action, 'Looking for the base plate schedule...')

    def schedule_selected(self, sender, e):
        if self.selected_schedule_view() is None:
            return

        def action(uiapp):
            self.show_schedule_summary(uiapp.ActiveUIDocument.Document)
            self.set_status('')
        self.run(action, 'Reading the schedule...')

    def button_draw(self, sender, e):
        schedule_view_id = self.selected_schedule_view()

        def action(uiapp):
            uidoc = uiapp.ActiveUIDocument
            doc, view = uidoc.Document, uidoc.ActiveView
            if not isinstance(view, DB.ViewPlan):
                raise UserError('Open a plan view first.')
            schedule = read_schedule(doc, schedule_view_id)
            if not schedule['entries']:
                raise UserError('No base plates read from the schedule. ' + ' '.join(schedule['problems']))
            rows, type_ids, flagged = draw_view(doc, view, schedule)
            self.drawn.extend((doc, type_id) for type_id in type_ids)
            if flagged:
                uidoc.Selection.SetElementIds(List[DB.ElementId](flagged))
            report(self.output, view, rows, schedule['problems'] + sorted(schedule['type_problems'].values()))
            self.set_status('Drew {} base plates; {} columns to review are selected and listed in the '
                            'report.'.format(len(type_ids), len(flagged)))
        self.run(action, 'Drawing base plates...')

    def button_clear_view(self, sender, e):
        def action(uiapp):
            uidoc = uiapp.ActiveUIDocument
            doc = uidoc.Document
            count = delete_group_types(doc, qc_group_type_ids(doc, uidoc.ActiveView),
                                       'Column Base Plate QC - Clear View')
            self.set_status('Cleared {} base plates from the active view.'.format(count))
        self.run(action, 'Clearing...')

    def button_clear_all(self, sender, e):
        def action(uiapp):
            doc = uiapp.ActiveUIDocument.Document
            count = delete_group_types(doc, qc_group_type_ids(doc), 'Column Base Plate QC - Clear All')
            self.set_status('Cleared {} base plates from all views.'.format(count))
        self.run(action, 'Clearing...')

    def palette_closed(self, sender, e):
        if not self.delete_on_close_check.IsChecked or not self.drawn:
            return
        drawn, self.drawn = self.drawn, []

        def action(uiapp):
            by_doc = []
            for doc, type_id in drawn:
                if not doc.IsValidObject:
                    continue  # The model was closed first.
                match = next((item for item in by_doc if item[0].Equals(doc)), None)
                if match is None:
                    by_doc.append((doc, [type_id]))
                else:
                    match[1].append(type_id)
            for doc, type_ids in by_doc:
                delete_group_types(doc, type_ids, 'Column Base Plate QC - Delete on Close')
        # Run even if an earlier action is still queued; the window is gone.
        self.handler.action = action
        self.action_event.Raise()


def main():
    handler = ActionHandler()
    palette = BasePlateQcPalette(handler, UI.ExternalEvent.Create(handler), script.get_output())
    handler.palette = palette
    palette.load_schedule_views(HOST_APP.uiapp.ActiveUIDocument.Document)
    palette.Show()


try:
    main()
except Exception as error:
    log('startup failed:\n' + traceback.format_exc())
    forms.alert(u'Column Base Plate QC could not start:\n{}\n\nDetails are in {}.'.format(error, LOG_PATH),
                title=COMMAND_TITLE, warn_icon=True)
