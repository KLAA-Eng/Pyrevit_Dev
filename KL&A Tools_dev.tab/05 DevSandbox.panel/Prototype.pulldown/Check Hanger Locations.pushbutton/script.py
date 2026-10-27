# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Check Hanger\nLocations"
__version__ = "v0.0"

from pyrevit import DB, EXEC_PARAMS, forms, revit, script

from hanger_check.classify import (
    DEFAULT_HANGER_FAMILY,
    PLAN_REACH_FT,
    ROLE_BOTH,
    ROLE_SUPPORTED,
    ROLE_SUPPORTING,
    STATUS_OK,
    VERTICAL_REACH_FT,
    classify_hanger,
    flag_shared_ends,
    matches_family,
    member_roles,
)


COMMAND_TITLE = 'Check Hanger Locations'
PROBLEM_KEY = 'problem'
COLORS = {
    ROLE_SUPPORTED: (0, 67, 255),
    ROLE_SUPPORTING: (255, 255, 0),
    ROLE_BOTH: (0, 176, 80),
    PROBLEM_KEY: (206, 1, 1),
}


def _stop(message):
    forms.alert(message, title=COMMAND_TITLE, warn_icon=True)
    script.exit()


def _id_value(element_id):
    return element_id.Value if hasattr(element_id, 'Value') else element_id.IntegerValue


def _xyz(point):
    return (point.X, point.Y, point.Z)


def _is_hanger(element):
    return (isinstance(element, DB.FamilyInstance)
            and isinstance(element.Location, DB.LocationPoint)
            and matches_family(element.Symbol.FamilyName, DEFAULT_HANGER_FAMILY))


def _hangers(doc, view):
    """Selected hangers, else every hanger visible in the active view."""
    selected = [doc.GetElement(i) for i in revit.uidoc.Selection.GetElementIds()]
    hangers = [e for e in selected if _is_hanger(e)]
    if hangers:
        return hangers, 'selection'
    collector = DB.FilteredElementCollector(doc, view.Id).OfClass(DB.FamilyInstance)
    return [e for e in collector if _is_hanger(e)], 'active view'


def _framing_near(doc, point, element_ids):
    low = DB.XYZ(point.X - PLAN_REACH_FT, point.Y - PLAN_REACH_FT, point.Z - VERTICAL_REACH_FT)
    high = DB.XYZ(point.X + PLAN_REACH_FT, point.Y + PLAN_REACH_FT, point.Z + VERTICAL_REACH_FT)
    collector = (DB.FilteredElementCollector(doc)
                 .OfCategory(DB.BuiltInCategory.OST_StructuralFraming)
                 .WhereElementIsNotElementType()
                 .WherePasses(DB.BoundingBoxIntersectsFilter(DB.Outline(low, high))))
    members = []
    for framing in collector:
        if isinstance(framing.Location, DB.LocationCurve):
            curve = framing.Location.Curve
            element_ids[_id_value(framing.Id)] = framing.Id
            members.append({'id': _id_value(framing.Id),
                            'start': _xyz(curve.GetEndPoint(0)),
                            'end': _xyz(curve.GetEndPoint(1))})
    return members


def _solid_fill_id(doc):
    for pattern in DB.FilteredElementCollector(doc).OfClass(DB.FillPatternElement):
        if pattern.GetFillPattern().IsSolidFill:
            return pattern.Id
    return None


def _override(rgb, solid_fill_id):
    color = DB.Color(*rgb)
    settings = DB.OverrideGraphicSettings()
    settings.SetProjectionLineColor(color)
    settings.SetCutLineColor(color)
    if solid_fill_id is not None:
        settings.SetSurfaceForegroundPatternId(solid_fill_id)
        settings.SetSurfaceForegroundPatternColor(color)
    return settings


def _is_check_color(settings):
    try:
        color = settings.ProjectionLineColor
        return color.IsValid and (color.Red, color.Green, color.Blue) in COLORS.values()
    except Exception:
        return False


def _apply_colors(doc, view, hanger_results, roles, element_ids):
    solid_fill_id = _solid_fill_id(doc)
    with revit.Transaction('Check hanger locations colors', doc=doc):
        for member_id, role in roles.items():
            view.SetElementOverrides(element_ids[member_id],
                                     _override(COLORS[role], solid_fill_id))
        for hanger_id, result in hanger_results.items():
            if result['status'] != STATUS_OK:
                view.SetElementOverrides(element_ids[hanger_id],
                                         _override(COLORS[PROBLEM_KEY], solid_fill_id))


def _clear_colors(doc, view):
    """Shift+Click: reset overrides that use one of this command's check colors."""
    cleared = 0
    with revit.Transaction('Clear hanger check colors', doc=doc):
        for element in (DB.FilteredElementCollector(doc, view.Id)
                        .WhereElementIsNotElementType()):
            if _is_check_color(view.GetElementOverrides(element.Id)):
                view.SetElementOverrides(element.Id, DB.OverrideGraphicSettings())
                cleared += 1
    forms.alert('Cleared hanger check colors from {} element(s) in "{}".'.format(
        cleared, view.Name), title=COMMAND_TITLE)


def _link(output, element_ids, value):
    return output.linkify(element_ids[value]) if value is not None else '-'


def _print_report(output, view, source, hanger_results, colored, element_ids):
    problems = [i for i, r in hanger_results.items() if r['status'] != STATUS_OK]
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('**Hangers checked:** {} ({}) | **Problems:** {} | **View:** {}'.format(
        len(hanger_results), source, len(problems), view.Name))
    if colored:
        output.print_md('Colors: supported member = blue, supporting member = yellow, '
                        'both = green, hanger with a problem = red.')
    else:
        output.print_md('Graphics overrides are not allowed in this view; nothing was colored.')
    if problems:
        output.print_md('Select problem hangers: {}'.format(
            output.linkify([element_ids[i] for i in problems])))
    rows = []
    for hanger_id in sorted(hanger_results, key=lambda i: (hanger_results[i]['status'] == STATUS_OK, i)):
        result = hanger_results[hanger_id]
        rows.append([_link(output, element_ids, hanger_id), result['status'],
                     _link(output, element_ids, result['supported']),
                     _link(output, element_ids, result['supporting']),
                     '; '.join(result['notes']) or '-'])
    output.print_table(rows, columns=['Hanger', 'Status', 'Supported member',
                                      'Supporting member', 'Notes'])


def main():
    doc = revit.doc
    view = revit.active_view
    if doc.IsFamilyDocument:
        _stop('Open a project model and run the command again.')
    if EXEC_PARAMS.config_mode:
        _clear_colors(doc, view)
        return

    hangers, source = _hangers(doc, view)
    if not hangers:
        _stop('No "{}" hanger families were selected or visible in the active view.'.format(
            DEFAULT_HANGER_FAMILY))

    results, element_ids = {}, {}
    for hanger in hangers:
        point = hanger.Location.Point
        element_ids[_id_value(hanger.Id)] = hanger.Id
        results[_id_value(hanger.Id)] = classify_hanger(
            _xyz(point), _framing_near(doc, point, element_ids))
    flag_shared_ends(results)

    colored = view.AreGraphicsOverridesAllowed()
    if colored:
        _apply_colors(doc, view, results, member_roles(results), element_ids)
    _print_report(script.get_output(), view, source, results, colored, element_ids)


if __name__ == '__main__':
    main()
