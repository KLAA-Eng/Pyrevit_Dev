# -*- coding: utf-8 -*-
from __future__ import print_function

__title__ = "Beam Reaction\nDeclutter"
__version__ = "v0.1"

import traceback

from pyrevit import DB, forms, revit, script

from GUI.forms import select_from_dict
from beam_reaction_declutter.workflow import (
    MARKER_COLOR,
    MAX_MOVE_STEPS,
    STEP_DISTANCE_FEET,
    boxes_overlap,
    is_marker_color,
    is_reaction_family,
    same_beam_mover,
    shortest_clear_choice_for_views,
    steps_to_clear_views,
    should_defer_to_other_tag,
)


COMMAND_TITLE = 'Beam Reaction Declutter'
MOVE_ACTIVE_ACTION = 'Move (Active View)'
MOVE_SHEETS_ACTION = 'Move (Select Sheets)'
CLEAR_ACTION = 'Clear Matching Red Overrides'
MINIMUM_REVIT_VERSION = 2024
STRUCTURAL_BLOCKER_CATEGORIES = (
    'OST_StructuralFraming', 'OST_StructuralColumns',
)
REFERENCE_ANNOTATION_CATEGORIES = (
    'OST_SectionBox', 'OST_Grids', 'OST_CLines', 'OST_Elev',
    'OST_Sections', 'OST_Levels', 'OST_PlanRegion',
    'OST_VolumeOfInterest',
)


def _stop(message):
    forms.alert(message, title=COMMAND_TITLE, warn_icon=True)
    script.exit()


def _element_id_value(element_id):
    """Return an ElementId's integer value across Revit 2024+ builds."""
    if element_id is None:
        return None
    for property_name in ('Value', 'IntegerValue'):
        try:
            return int(getattr(element_id, property_name))
        except Exception:
            pass
    return None


def _is_supported_revit_version(document):
    try:
        return int(document.Application.VersionNumber) >= MINIMUM_REVIT_VERSION
    except (TypeError, ValueError):
        return False


def _view_label(view):
    return '{} [Id {}]'.format(view.Name, _element_id_value(view.Id))


def _is_eligible_plan_view(view):
    if not isinstance(view, DB.ViewPlan) or getattr(view, 'IsTemplate', False):
        return False
    try:
        return bool(view.AreGraphicsOverridesAllowed())
    except Exception:
        return False


def _eligible_plan_views(document):
    """Return non-template plan views that can accept element overrides."""
    return [view for view in DB.FilteredElementCollector(document).OfClass(DB.ViewPlan)
            if _is_eligible_plan_view(view)]


def _select_action():
    choice = forms.CommandSwitchWindow.show(
        [MOVE_ACTIVE_ACTION, MOVE_SHEETS_ACTION, CLEAR_ACTION, 'Cancel'],
        message='Move reaction tags in the active view or on selected sheets, or clear red overrides?')
    if not choice or choice == 'Cancel':
        return None
    return choice


def _select_plan_views(document):
    views = _eligible_plan_views(document)
    if not views:
        _stop('No eligible non-template plan views were found.')

    options = {}
    for view in views:
        label = _view_label(view)
        options[label] = view
    selected = select_from_dict(
        options,
        title=COMMAND_TITLE,
        label='Select plan views to process:',
        button_name='Process Selected Views',
        version='DevSandbox Prototype',
        SelectMultiple=True,
    )
    return selected or []


def _unique_plan_views(views):
    """Process a placed plan view only once when several sheets include it."""
    unique = {}
    for view in views:
        if _is_eligible_plan_view(view):
            unique[_element_id_value(view.Id)] = view
    return [unique[key] for key in sorted(unique)]


def _plan_views_on_sheet(document, sheet):
    return _unique_plan_views(
        document.GetElement(view_id) for view_id in sheet.GetAllPlacedViews())


def _active_plan_views(document):
    active = document.ActiveView
    if _is_eligible_plan_view(active):
        return [active]
    if isinstance(active, DB.ViewSheet):
        views = _plan_views_on_sheet(document, active)
        if views:
            return views
        _stop('The active sheet has no eligible plan views.')
    _stop('Open an eligible plan view or a sheet containing plan views.')


def _select_sheet_plan_views(document):
    sheets = [sheet for sheet in
              DB.FilteredElementCollector(document).OfClass(DB.ViewSheet)
              if not sheet.IsPlaceholder]
    if not sheets:
        _stop('No project sheets were found in the active model.')
    options = {
        '{} - {} [Id {}]'.format(sheet.SheetNumber, sheet.Name,
                               _element_id_value(sheet.Id)): sheet
        for sheet in sheets
    }
    selected = select_from_dict(
        options,
        title=COMMAND_TITLE,
        label='Select sheets containing plan views:',
        button_name='Move Tags on Selected Sheets',
        version='DevSandbox Prototype',
        SelectMultiple=True,
    )
    if not selected:
        return []
    views = _unique_plan_views(
        view for sheet in selected for view in _plan_views_on_sheet(document, sheet))
    if not views:
        _stop('The selected sheets have no eligible plan views.')
    return views


def _category_id(element):
    try:
        return _element_id_value(element.Category.Id)
    except Exception:
        return None


def _is_structural_framing_tag(element):
    try:
        return _category_id(element) == int(DB.BuiltInCategory.OST_StructuralFramingTags)
    except Exception:
        return False


def _reaction_tags(document, view):
    tags = []
    collector = DB.FilteredElementCollector(document, view.Id).WhereElementIsNotElementType()
    for element in collector:
        if not _is_structural_framing_tag(element):
            continue
        try:
            tag_type = document.GetElement(element.GetTypeId())
            family_name = tag_type.FamilyName if tag_type else None
        except Exception:
            family_name = None
        if is_reaction_family(family_name):
            tags.append(element)
    return sorted(tags, key=lambda tag: _element_id_value(tag.Id) or -1)


def _built_in_category_ids(names):
    ids = set()
    for name in names:
        try:
            ids.add(int(getattr(DB.BuiltInCategory, name)))
        except Exception:
            pass
    return ids


def _is_conflict_element(element, structural_ids, reference_ids, detail_id):
    """Keep drawn annotations and structural members, not view controls."""
    category_id = _category_id(element)
    if category_id is None:
        return False
    if category_id in structural_ids or category_id == detail_id:
        return True
    if category_id in reference_ids:
        return False
    try:
        return element.Category.CategoryType == DB.CategoryType.Annotation
    except Exception:
        return False


def _visible_elements(document, view):
    structural_ids = _built_in_category_ids(STRUCTURAL_BLOCKER_CATEGORIES)
    reference_ids = _built_in_category_ids(REFERENCE_ANNOTATION_CATEGORIES)
    detail_ids = _built_in_category_ids(('OST_DetailComponents',))
    detail_id = next(iter(detail_ids)) if detail_ids else None
    collector = DB.FilteredElementCollector(
        document, view.Id).WhereElementIsNotElementType()
    return [element for element in collector if _is_conflict_element(
        element, structural_ids, reference_ids, detail_id)]


def _bounds(element, view):
    """Return an element's 2D view bounds or None when Revit cannot provide it."""
    try:
        box = element.get_BoundingBox(view)
        if box is None:
            return None
        horizontal = []
        vertical = []
        for x in (box.Min.X, box.Max.X):
            for y in (box.Min.Y, box.Max.Y):
                for z in (box.Min.Z, box.Max.Z):
                    point = box.Transform.OfPoint(DB.XYZ(x, y, z))
                    horizontal.append(point.DotProduct(view.RightDirection))
                    vertical.append(point.DotProduct(view.UpDirection))
        return (min(horizontal), min(vertical), max(horizontal), max(vertical))
    except Exception:
        return None


def _tagged_beam(document, tag):
    """Return a single local straight beam, or the reason it is unsupported."""
    try:
        references = list(tag.GetTaggedReferences())
        if len(references) != 1:
            return None, 'Requires exactly one tagged beam reference'
        reference = references[0]
        beam = document.GetElement(reference.ElementId)
        if beam is None or isinstance(beam, DB.RevitLinkInstance):
            return None, 'Linked or missing local tagged beam'
        if _category_id(beam) != int(DB.BuiltInCategory.OST_StructuralFraming):
            return None, 'Tagged reference is not a local structural-framing beam'
        if not isinstance(beam.Location, DB.LocationCurve):
            return None, 'Tagged beam has no usable location curve'
        curve = beam.Location.Curve
        if not isinstance(curve, DB.Line) or not curve.IsBound:
            return None, 'Curved or unbounded tagged beam is unsupported'
        return beam, None
    except Exception:
        return None, 'Could not inspect tagged beam reference'


def _tag_data(document, view, tag):
    """Return the tag's beam geometry projected into its plan view."""
    beam, reason = _tagged_beam(document, tag)
    if beam is None:
        return None, reason
    try:
        curve = beam.Location.Curve
        midpoint = curve.Evaluate(0.5, True)
        beam_direction = curve.Direction.Normalize()
        right = view.RightDirection
        up = view.UpDirection
        axis = right.Multiply(beam_direction.DotProduct(right)).Add(
            up.Multiply(beam_direction.DotProduct(up)))
        if axis.GetLength() < 0.000001:
            return None, 'Tagged beam has no direction in this plan view'
        axis = axis.Normalize()
        head = tag.TagHeadPosition
        offset = head.Subtract(midpoint).DotProduct(axis)
        return {
            'beam_id': _element_id_value(beam.Id),
            'midpoint': midpoint,
            'axis': axis,
            'head_offset': offset,
            'center_distance': abs(offset),
        }, None
    except Exception:
        return None, 'Could not read beam or tag-head geometry'


def _beam_verticality(view, data):
    try:
        return abs(data['axis'].DotProduct(view.UpDirection))
    except Exception:
        return 0.0


def _tag_is_pinned(tag):
    try:
        return bool(tag.Pinned)
    except Exception:
        return True


def _tag_has_leader(tag):
    try:
        return bool(tag.HasLeader)
    except Exception:
        return True


def _fresh_marker_override():
    override = DB.OverrideGraphicSettings()
    override.SetProjectionLineColor(DB.Color(*MARKER_COLOR))
    return override


def _source_marker_override(override):
    try:
        color = override.ProjectionLineColor
        return is_marker_color(int(color.Red), int(color.Green), int(color.Blue))
    except Exception:
        return False


def _blocker_bounds(document, view, tag, visible_elements, beam_id):
    """Return the tag box and eligible conflict boxes except its own beam."""
    tag_bounds = _bounds(tag, view)
    blockers = []
    tag_id = _element_id_value(tag.Id)
    for other in visible_elements:
        other_id = _element_id_value(other.Id)
        if other_id == tag_id or other_id == beam_id:
            continue
        other_bounds = _bounds(other, view)
        if other_bounds is not None:
            blockers.append((other, other_bounds))
    return tag_bounds, blockers


def _end_subtransaction(subtransaction, commit):
    expected = DB.TransactionStatus.Committed if commit else DB.TransactionStatus.RolledBack
    actual = subtransaction.Commit() if commit else subtransaction.RollBack()
    if actual != expected:
        raise RuntimeError('Tag subtransaction ended with status {}'.format(actual))


def _move_tag(document, view, tag, visible_elements, beam_id, vector,
              view_contexts=None):
    """Commit only a verified clear move and marker for this tag."""
    contexts = view_contexts or [(view, visible_elements, beam_id)]
    subtransaction = DB.SubTransaction(document)
    try:
        if subtransaction.Start() != DB.TransactionStatus.Started:
            raise RuntimeError('Could not start tag subtransaction')
        try:
            try:
                DB.ElementTransformUtils.MoveElement(document, tag.Id, vector)
            except Exception as error:
                _end_subtransaction(subtransaction, False)
                document.Regenerate()
                return False, 'Move failed: {}'.format(error)

            # Geometry-derived bounding boxes can be stale inside a transaction.
            # A regeneration failure must escape and abort the whole action.
            document.Regenerate()
            for check_view, check_visible, check_beam_id in contexts:
                tag_bounds, blockers = _blocker_bounds(
                    document, check_view, tag, check_visible, check_beam_id)
                if tag_bounds is None or any(
                        boxes_overlap(tag_bounds, bounds) for unused_other, bounds in blockers):
                    _end_subtransaction(subtransaction, False)
                    document.Regenerate()
                    return False, 'Collision remains at the final position'

            try:
                for marker_view, unused_visible, unused_beam_id in contexts:
                    marker_view.SetElementOverrides(tag.Id, _fresh_marker_override())
                    if not _source_marker_override(marker_view.GetElementOverrides(tag.Id)):
                        raise RuntimeError('Exact red marker was not applied')
            except Exception as error:
                _end_subtransaction(subtransaction, False)
                document.Regenerate()
                return False, 'Could not apply red marker: {}'.format(error)
            _end_subtransaction(subtransaction, True)
            return True, ''
        except Exception:
            if subtransaction.GetStatus() == DB.TransactionStatus.Started:
                _end_subtransaction(subtransaction, False)
            raise
    finally:
        subtransaction.Dispose()


def _declutter_tag(document, view, tag, visible_elements, candidate_ids,
                   shared_contexts=None):
    """Plan one move that clears every selected view showing this tag."""
    inputs = shared_contexts if shared_contexts is not None else [
        (view, visible_elements, candidate_ids)]
    analyses = []
    for current_view, current_visible, current_candidates in inputs:
        data, unsupported_reason = _tag_data(document, current_view, tag)
        beam_id = data['beam_id'] if data is not None else None
        tag_bounds, blockers = _blocker_bounds(
            document, current_view, tag, current_visible, beam_id)
        if tag_bounds is None:
            return 'unresolved', 'No view bounding box for this tag'
        analyses.append({
            'view': current_view,
            'visible': current_visible,
            'candidates': current_candidates,
            'data': data,
            'reason': unsupported_reason,
            'beam_id': beam_id,
            'bounds': tag_bounds,
            'blockers': blockers,
            'overlapping': [(other, bounds) for other, bounds in blockers
                            if boxes_overlap(tag_bounds, bounds)],
        })
    if not any(item['overlapping'] for item in analyses):
        return 'clear', ''
    for item in analyses:
        if item['data'] is None:
            return 'unsupported', item['reason']
    if _tag_has_leader(tag):
        return 'unsupported', 'Leader-on tag is unsupported'
    if _tag_is_pinned(tag):
        return 'unresolved', 'Tag is pinned'

    same_beam_conflict = False
    for item in analyses:
        current_view = item['view']
        data = item['data']
        current_verticality = _beam_verticality(current_view, data)
        for other, unused_bounds in item['overlapping']:
            if not hasattr(other, 'GetTaggedReferences'):
                continue
            other_data, unused_reason = _tag_data(document, current_view, other)
            if other_data is None:
                continue
            other_id = _element_id_value(other.Id)
            if other_data['beam_id'] == item['beam_id']:
                same_beam_conflict = True
                other_movable = (other_id in item['candidates'] and
                                 not _tag_has_leader(other) and
                                 not _tag_is_pinned(other))
                if not same_beam_mover(
                        data['center_distance'], other_data['center_distance'],
                        _element_id_value(tag.Id), other_id,
                        other_movable=other_movable,
                        other_pinned=_tag_is_pinned(other)):
                    return 'deferred', 'Center or fixed same-beam tag kept stationary'
            elif (other_id in item['candidates'] and
                  not _tag_has_leader(other) and not _tag_is_pinned(other)):
                if should_defer_to_other_tag(
                        current_verticality,
                        _beam_verticality(current_view, other_data)):
                    return 'deferred', 'Deferred to tag on more vertical beam'

    axis = analyses[0]['data']['axis']
    view_boxes = []
    for item in analyses:
        current_view = item['view']
        step_vector = (
            axis.DotProduct(current_view.RightDirection) * STEP_DISTANCE_FEET,
            axis.DotProduct(current_view.UpDirection) * STEP_DISTANCE_FEET,
        )
        view_boxes.append((
            item['bounds'],
            [bounds for unused_other, bounds in item['blockers']],
            step_vector,
        ))
    head_offset = analyses[0]['data']['head_offset']
    if same_beam_conflict:
        away_sign = 1 if head_offset >= 0 else -1
        signed_steps = shortest_clear_choice_for_views(view_boxes, away_sign)
    else:
        if abs(head_offset) < 0.000001:
            return 'unresolved', 'No direction toward the beam midpoint'
        direction_sign = -1 if head_offset > 0 else 1
        steps = steps_to_clear_views(view_boxes, direction_sign)
        signed_steps = direction_sign * steps if steps is not None else None

    if signed_steps is None:
        return 'unresolved', 'Could not clear all blockers within {} steps'.format(
            MAX_MOVE_STEPS)
    vector = axis.Multiply(STEP_DISTANCE_FEET * signed_steps)
    move_contexts = [(item['view'], item['visible'], item['beam_id'])
                     for item in analyses]
    moved, reason = _move_tag(
        document, view, tag, visible_elements, analyses[0]['beam_id'], vector,
        view_contexts=move_contexts)
    return ('moved', '') if moved else ('unresolved', reason)


def _move_view(document, view):
    return _move_views(document, [view])[0]


def _move_views(document, views):
    """Process shared tags once across every selected parent/dependent view."""
    view_data = []
    tag_contexts = {}
    for view in views:
        tags = _reaction_tags(document, view)
        visible_elements = _visible_elements(document, view)
        candidate_ids = set(_element_id_value(tag.Id) for tag in tags)
        view_data.append((view, tags, visible_elements))
        for tag in tags:
            tag_id = _element_id_value(tag.Id)
            tag_contexts.setdefault(tag_id, []).append(
                (tag, view, visible_elements, candidate_ids))

    outcomes = {}
    for tag_id in sorted(tag_contexts):
        contexts = tag_contexts[tag_id]
        tag, view, visible_elements, candidate_ids = contexts[0]
        shared = [(current_view, current_visible, current_candidates)
                  for unused_tag, current_view, current_visible, current_candidates
                  in contexts]
        outcomes[tag_id] = _declutter_tag(
            document, view, tag, visible_elements, candidate_ids, shared)

    results = []
    for view, tags, visible_elements in view_data:
        issues = []
        for tag in tags:
            tag_id = _element_id_value(tag.Id)
            status, reason = outcomes[tag_id]
            data, unused_reason = _tag_data(document, view, tag)
            beam_id = data['beam_id'] if data is not None else None
            tag_bounds, blockers = _blocker_bounds(
                document, view, tag, visible_elements, beam_id)
            remains = tag_bounds is None or any(
                boxes_overlap(tag_bounds, bounds) for unused_other, bounds in blockers)
            if status == 'moved' and remains:
                raise RuntimeError(
                    'Moved tag {} still overlaps after view processing'.format(tag_id))
            if remains:
                label = 'Unsupported' if status == 'unsupported' else 'Unresolved'
                issues.append((label, tag_id, reason or 'Overlap remains'))
        results.append({'view': view, 'issues': issues})
    return results


def _clear_view(document, view):
    issues = []
    for tag in _reaction_tags(document, view):
        try:
            if not _source_marker_override(view.GetElementOverrides(tag.Id)):
                continue
        except Exception as error:
            issues.append(('Failed', _element_id_value(tag.Id),
                           'Could not inspect view override: {}'.format(error)))
            continue
        subtransaction = DB.SubTransaction(document)
        try:
            if subtransaction.Start() != DB.TransactionStatus.Started:
                raise RuntimeError('Could not start clear subtransaction')
            try:
                view.SetElementOverrides(tag.Id, DB.OverrideGraphicSettings())
                if _source_marker_override(view.GetElementOverrides(tag.Id)):
                    raise RuntimeError('Matching red override remains after clearing')
            except Exception as error:
                _end_subtransaction(subtransaction, False)
                issues.append(('Failed', _element_id_value(tag.Id),
                               'Could not clear red override: {}'.format(error)))
            else:
                _end_subtransaction(subtransaction, True)
        except Exception:
            if subtransaction.GetStatus() == DB.TransactionStatus.Started:
                _end_subtransaction(subtransaction, False)
            raise
        finally:
            subtransaction.Dispose()
    return {'view': view, 'issues': issues}


def _print_report(action, results):
    if not any(result['issues'] for result in results):
        return
    output = script.get_output()
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('**Action:** {}'.format(action))
    for result in results:
        if result['issues']:
            output.print_md('## {}'.format(_view_label(result['view'])))
            output.print_table(result['issues'],
                               columns=['Result', 'Element ID', 'Reason'])


def _process_action(document, action, selected_views):
    """Run one action and verify Revit's commit before disposing the transaction."""
    results = []
    transaction_name = '{} - {}'.format(COMMAND_TITLE, action)
    transaction = DB.Transaction(document, transaction_name)
    try:
        if transaction.Start() != DB.TransactionStatus.Started:
            raise RuntimeError('Revit could not start the {} transaction'.format(action))
        if action in (MOVE_ACTIVE_ACTION, MOVE_SHEETS_ACTION):
            results = _move_views(document, selected_views)
        else:
            for view in selected_views:
                results.append(_clear_view(document, view))
        commit_status = transaction.Commit()
        if commit_status != DB.TransactionStatus.Committed:
            raise RuntimeError('Revit did not commit the {} transaction: {}'.format(
                action, commit_status))
        return results
    except Exception:
        if transaction.GetStatus() == DB.TransactionStatus.Started:
            rollback_status = transaction.RollBack()
            if rollback_status != DB.TransactionStatus.RolledBack:
                raise RuntimeError('Revit could not roll back the {} transaction: {}'.format(
                    action, rollback_status))
        raise
    finally:
        transaction.Dispose()


def main():
    document = revit.doc
    if document is None or document.IsFamilyDocument:
        _stop('Open a Revit project model and run the command again.')
    if not _is_supported_revit_version(document):
        _stop('This prototype requires Revit {} or newer.'.format(MINIMUM_REVIT_VERSION))

    action = _select_action()
    if action is None:
        return
    if action == MOVE_ACTIVE_ACTION:
        selected_views = _active_plan_views(document)
    elif action == MOVE_SHEETS_ACTION:
        selected_views = _select_sheet_plan_views(document)
    else:
        selected_views = _select_plan_views(document)
    if not selected_views:
        return

    results = _process_action(document, action, selected_views)
    _print_report(action, results)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        output = script.get_output()
        output.print_md('# {}'.format(COMMAND_TITLE))
        output.print_md('The command stopped before it could finish.')
        output.print_md('```')
        output.print_md(traceback.format_exc())
        output.print_md('```')
        forms.alert(
            'Beam Reaction Declutter stopped. Review the pyRevit output window for details.',
            title=COMMAND_TITLE,
            warn_icon=True)
