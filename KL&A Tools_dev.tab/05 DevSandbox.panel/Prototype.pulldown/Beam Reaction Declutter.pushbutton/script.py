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
    shortest_clear_choice,
    steps_to_clear_all,
    should_defer_to_other_tag,
)


COMMAND_TITLE = 'Beam Reaction Declutter'
CLEAR_ACTION = 'Clear Matching Red Overrides'
MINIMUM_REVIT_VERSION = 2024


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


def _eligible_plan_views(document):
    """Return non-template plan views that can accept element overrides."""
    views = []
    for view in DB.FilteredElementCollector(document).OfClass(DB.ViewPlan):
        if getattr(view, 'IsTemplate', False):
            continue
        try:
            if not view.AreGraphicsOverridesAllowed():
                continue
        except Exception:
            continue
        views.append(view)
    return views


def _select_action():
    choice = forms.CommandSwitchWindow.show(
        ['Move', CLEAR_ACTION, 'Cancel'],
        message='Move overlapping reaction tags or clear exact-red view overrides?')
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


def _visible_elements(document, view):
    return list(DB.FilteredElementCollector(document, view.Id).WhereElementIsNotElementType())


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
    """Return the tag box and all other visible boxes except its own beam."""
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


def _move_tag(document, view, tag, visible_elements, beam_id, vector):
    """Commit only a verified clear move and marker for this tag."""
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
            tag_bounds, blockers = _blocker_bounds(
                document, view, tag, visible_elements, beam_id)
            if tag_bounds is None or any(
                    boxes_overlap(tag_bounds, bounds) for unused_other, bounds in blockers):
                _end_subtransaction(subtransaction, False)
                document.Regenerate()
                return False, 'Collision remains at the final position'

            try:
                view.SetElementOverrides(tag.Id, _fresh_marker_override())
                if not _source_marker_override(view.GetElementOverrides(tag.Id)):
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


def _declutter_tag(document, view, tag, visible_elements, candidate_ids):
    """Return an outcome without leaving a failed tag partially displaced."""
    data, unsupported_reason = _tag_data(document, view, tag)
    beam_id = data['beam_id'] if data is not None else None
    tag_bounds, blockers = _blocker_bounds(
        document, view, tag, visible_elements, beam_id)
    if tag_bounds is None:
        return 'unresolved', 'No view bounding box for this tag'
    overlapping = [(other, bounds) for other, bounds in blockers
                   if boxes_overlap(tag_bounds, bounds)]
    if not overlapping:
        return 'clear', ''
    if data is None:
        return 'unsupported', unsupported_reason
    if _tag_has_leader(tag):
        return 'unsupported', 'Leader-on tag is unsupported'
    if _tag_is_pinned(tag):
        return 'unresolved', 'Tag is pinned'

    same_beam_conflict = False
    current_verticality = _beam_verticality(view, data)
    for other, unused_bounds in overlapping:
        if not hasattr(other, 'GetTaggedReferences'):
            continue
        other_data, unused_reason = _tag_data(document, view, other)
        if other_data is None:
            continue
        other_id = _element_id_value(other.Id)
        if other_data['beam_id'] == beam_id:
            same_beam_conflict = True
            other_movable = (other_id in candidate_ids and
                             not _tag_has_leader(other) and
                             not _tag_is_pinned(other))
            if not same_beam_mover(
                    data['center_distance'], other_data['center_distance'],
                    _element_id_value(tag.Id), other_id,
                    other_movable=other_movable,
                    other_pinned=_tag_is_pinned(other)):
                return 'deferred', 'Center or fixed same-beam tag kept stationary'
        elif other_id in candidate_ids and not _tag_has_leader(other) and not _tag_is_pinned(other):
            if should_defer_to_other_tag(
                    current_verticality, _beam_verticality(view, other_data)):
                return 'deferred', 'Deferred to tag on more vertical beam'

    axis = data['axis']
    step_vector = (
        axis.DotProduct(view.RightDirection) * STEP_DISTANCE_FEET,
        axis.DotProduct(view.UpDirection) * STEP_DISTANCE_FEET,
    )
    all_bounds = [bounds for unused_other, bounds in blockers]
    if same_beam_conflict:
        away_sign = 1 if data['head_offset'] >= 0 else -1
        signed_steps = shortest_clear_choice(
            tag_bounds, all_bounds, step_vector, away_sign)
    else:
        if abs(data['head_offset']) < 0.000001:
            return 'unresolved', 'No direction toward the beam midpoint'
        direction_sign = -1 if data['head_offset'] > 0 else 1
        directed_step = (step_vector[0] * direction_sign,
                         step_vector[1] * direction_sign)
        steps = steps_to_clear_all(tag_bounds, all_bounds, directed_step)
        signed_steps = direction_sign * steps if steps is not None else None

    if signed_steps is None:
        return 'unresolved', 'Could not clear all blockers within {} steps'.format(
            MAX_MOVE_STEPS)
    vector = axis.Multiply(STEP_DISTANCE_FEET * signed_steps)
    moved, reason = _move_tag(
        document, view, tag, visible_elements, beam_id, vector)
    return ('moved', '') if moved else ('unresolved', reason)


def _move_view(document, view):
    tags = _reaction_tags(document, view)
    visible_elements = _visible_elements(document, view)
    candidate_ids = set(_element_id_value(tag.Id) for tag in tags)
    outcomes = {}
    for tag in tags:
        outcomes[_element_id_value(tag.Id)] = _declutter_tag(
            document, view, tag, visible_elements, candidate_ids)

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
            raise RuntimeError('Moved tag {} still overlaps after view processing'.format(tag_id))
        if remains:
            label = 'Unsupported' if status == 'unsupported' else 'Unresolved'
            issues.append((label, tag_id, reason or 'Overlap remains'))
    return {'view': view, 'issues': issues}


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


def main():
    document = revit.doc
    if document is None or document.IsFamilyDocument:
        _stop('Open a Revit project model and run the command again.')
    if not _is_supported_revit_version(document):
        _stop('This prototype requires Revit {} or newer.'.format(MINIMUM_REVIT_VERSION))

    action = _select_action()
    if action is None:
        return
    selected_views = _select_plan_views(document)
    if not selected_views:
        return

    results = []
    transaction_name = '{} - {}'.format(COMMAND_TITLE, action)
    with revit.Transaction(transaction_name, doc=document) as transaction:
        for view in selected_views:
            if action == 'Move':
                results.append(_move_view(document, view))
            else:
                results.append(_clear_view(document, view))
    if transaction.status != DB.TransactionStatus.Committed:
        raise RuntimeError('Revit did not commit the {} transaction'.format(action))
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
