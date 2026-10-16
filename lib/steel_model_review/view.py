"""Review-view scope, severity aggregation, and Revit graphics adapter.

The DB namespace is injected; planning uses only serializable report records.
Only a view created by this session is passed to the mutation helpers.
"""

from steel_model_review.reporting import SEVERITY_ORDER


PALETTE = {'Critical': (220, 40, 40), 'Error': (200, 30, 120),
           'Warning': (245, 155, 30), 'Not evaluated': (145, 85, 190),
           'Information': (45, 125, 200), 'Context': (185, 185, 185)}
KINDS = ('beam', 'column', 'wall')


def scope_members(snapshot):
    """Include extracted steel/concrete review members, never grids/host floors."""
    return dict((m['uid'], m) for m in snapshot.get('members', [])
                if m.get('kind') in KINDS)


def color_plan(snapshot, rows):
    """Aggregate filtered open results; only pair checks color both participants.

    A receiving support is context, not automatically responsible for an
    endpoint error. Pass and accepted findings leave neutral context graphics.
    """
    plan = dict((uid, 'Context') for uid in scope_members(snapshot))
    for row in rows:
        severity = row['severity']
        if row['status'] == 'Accepted exception' or severity == 'Pass':
            continue
        uids = [row['uid']]
        if row['check'] in ('SMR-04', 'SMR-06'):
            uids.extend(r['uid'] for r in row['related'])
        for uid in uids:
            if uid in plan and SEVERITY_ORDER[severity] < SEVERITY_ORDER.get(plan[uid], 99):
                plan[uid] = severity
    return plan


def _ids(db, elements):
    from System.Collections.Generic import List
    return List[db.ElementId]([e.Id for e in elements])


def create(document, db, phase_id=None):
    """Create an independent isometric view inside the caller's transaction."""
    types = [t for t in db.FilteredElementCollector(document).OfClass(db.ViewFamilyType)
             if t.ViewFamily == db.ViewFamily.ThreeDimensional]
    if not types:
        raise ValueError('No 3D view family type is available.')
    view = db.View3D.CreateIsometric(document, types[0].Id)
    # Revit's generated name is unique; never adopt an existing view by name.
    view.Name = 'KLA Model Checker - ' + view.Name
    view.ViewTemplateId = db.ElementId.InvalidElementId
    view.DisplayStyle = db.DisplayStyle.FlatColors
    view.AreAnnotationCategoriesHidden = True
    view.AreImportCategoriesHidden = True
    view.AreAnalyticalModelCategoriesHidden = True
    view.IsSectionBoxActive = False
    if phase_id is not None:
        view.get_Parameter(db.BuiltInParameter.VIEW_PHASE).Set(db.ElementId(phase_id))
    return view


def isolate(document, db, view, snapshot):
    """Persist checked-member visibility in the dedicated view only.

    Native phase, design-option, workset, and group visibility still applies;
    the controller reports members absent from the view's visible collector.
    """
    members = scope_members(snapshot)
    if not members:
        raise ValueError('The report contains no extracted beams, columns, or walls.')
    allowed = set(int(c) for c in (db.BuiltInCategory.OST_StructuralFraming,
                                  db.BuiltInCategory.OST_StructuralColumns,
                                  db.BuiltInCategory.OST_Walls))
    for category in document.Settings.Categories:
        if view.CanCategoryBeHidden(category.Id):
            view.SetCategoryHidden(category.Id, int(category.Id.Value) not in allowed)
    hide, unhide, blocked = [], [], []
    for element in db.FilteredElementCollector(document).WhereElementIsNotElementType():
        if element.Category is None or int(element.Category.Id.Value) not in allowed:
            continue
        if element.UniqueId in members:
            if element.IsHidden(view):
                unhide.append(element)
        elif not element.IsHidden(view):
            if element.CanBeHidden(view):
                hide.append(element)
            else:
                blocked.append(element.Id.Value)
    if blocked:
        raise ValueError('Review isolation is blocked by unhideable unchecked elements: {0}'.format(
            ', '.join(str(value) for value in blocked[:10])))
    if unhide:
        view.UnhideElements(_ids(db, unhide))
    if hide:
        view.HideElements(_ids(db, hide))


def apply_colors(document, db, view, plan):
    """Assign solid surface/cut fills and lines in the dedicated review view."""
    fills = [f for f in db.FilteredElementCollector(document).OfClass(db.FillPatternElement)
             if f.GetFillPattern().IsSolidFill and
             f.GetFillPattern().Target == db.FillPatternTarget.Drafting]
    if not fills:
        raise ValueError('A drafting solid-fill pattern is required for review colors.')
    styles = {}
    for severity, rgb in PALETTE.items():
        color = db.Color(*rgb)
        style = db.OverrideGraphicSettings()
        style.SetProjectionLineColor(color)
        style.SetCutLineColor(color)
        style.SetSurfaceForegroundPatternId(fills[0].Id)
        style.SetSurfaceForegroundPatternColor(color)
        style.SetSurfaceForegroundPatternVisible(True)
        style.SetCutForegroundPatternId(fills[0].Id)
        style.SetCutForegroundPatternColor(color)
        style.SetCutForegroundPatternVisible(True)
        styles[severity] = style
    missing = 0
    for uid, severity in plan.items():
        element = document.GetElement(uid)
        if element is None:
            missing += 1
        else:
            view.SetElementOverrides(element.Id, styles[severity])
    return missing


def visibility_summary(document, db, view, snapshot):
    """Report visibility limits instead of claiming hidden members are visible."""
    wanted = set(scope_members(snapshot))
    visible = set(e.UniqueId for e in db.FilteredElementCollector(document, view.Id)
                  .WhereElementIsNotElementType() if e.UniqueId in wanted)
    absent = len(wanted - visible)
    text = 'Review view: {0} of {1} checked members available in view.'.format(
        len(visible), len(wanted))
    if absent:
        text += (' {0} absent: inspect phase, design options, worksets, or deleted elements.'
                 .format(absent))
    return text
