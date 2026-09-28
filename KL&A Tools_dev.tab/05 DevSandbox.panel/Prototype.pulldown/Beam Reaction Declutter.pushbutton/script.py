# -*- coding: utf-8 -*-
"""Declutter Reaction structural-framing tags in selected Revit plan views."""
from __future__ import print_function

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
    should_defer_to_other_tag,
)


COMMAND_TITLE = 'Beam Reaction Declutter'
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
        ['Move', 'Reset', 'Cancel'],
        message='Move overlapping reaction tags or clear existing red markers?')
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
        return (box.Min.X, box.Min.Y, box.Max.X, box.Max.Y)
    except Exception:
        return None


def _tagged_beam(document, tag):
    """Return the locally tagged beam and its first tag reference, if usable."""
    try:
        references = tag.GetTaggedReferences()
        if not references:
            return None, None
        reference = references[0]
        beam = document.GetElement(reference.ElementId)
        if beam is None or not isinstance(beam.Location, DB.LocationCurve):
            return None, None
        return beam, reference
    except Exception:
        return None, None


def _tagged_beam_id(document, tag):
    beam, unused_reference = _tagged_beam(document, tag)
    return _element_id_value(beam.Id) if beam is not None else None


def _same_beam_tag(document, reaction_tag, other):
    if not hasattr(other, 'GetTaggedReferences'):
        return False
    reaction_beam_id = _tagged_beam_id(document, reaction_tag)
    other_beam_id = _tagged_beam_id(document, other)
    return reaction_beam_id is not None and reaction_beam_id == other_beam_id


def _beam_data(document, tag):
    """Return (midpoint, direction, tag_head) for a tag's local straight beam."""
    beam, unused_reference = _tagged_beam(document, tag)
    if beam is None:
        return None, None, None
    try:
        curve = beam.Location.Curve
        midpoint = curve.Evaluate(0.5, True)
        direction = curve.Direction.Normalize()
        tag_head = tag.TagHeadPosition
        return midpoint, direction, tag_head
    except Exception:
        return None, None, None


def _beam_verticality(document, tag):
    unused_midpoint, direction, unused_head = _beam_data(document, tag)
    try:
        return abs(direction.Y) if direction is not None else 0.0
    except Exception:
        return 0.0


def _movement_vector(midpoint, beam_direction, tag_head):
    """Project tag-to-midpoint movement onto the beam axis, as in Dynamo."""
    try:
        toward_midpoint = midpoint.Subtract(tag_head)
        if toward_midpoint.GetLength() == 0:
            return None
        dot_product = toward_midpoint.Normalize().DotProduct(beam_direction)
        if abs(dot_product) < 0.000001:
            return None
        return beam_direction.Multiply(dot_product).Normalize()
    except Exception:
        return None


def _move_until_clear(document, view, tag, blocker, move_vector):
    """Move one tag until it clears one blocker.

    Returns ``(cleared, completed_steps, error)`` so a failed Revit movement
    can still be reversed exactly when it happened after an earlier step.
    """
    completed_steps = 0
    try:
        for step_count in range(1, MAX_MOVE_STEPS + 1):
            DB.ElementTransformUtils.MoveElement(
                document, tag.Id, move_vector.Multiply(STEP_DISTANCE_FEET))
            completed_steps = step_count
            current_bounds = _bounds(tag, view)
            blocker_bounds = _bounds(blocker, view)
            if not boxes_overlap(current_bounds, blocker_bounds):
                return True, completed_steps, None
    except Exception as error:
        return False, completed_steps, str(error)
    return False, completed_steps, None


def _restore_tag(document, tag, move_vector, completed_steps):
    """Undo this run's completed movement for a tag after an unresolved case."""
    if completed_steps <= 0:
        return
    reverse = move_vector.Multiply(-STEP_DISTANCE_FEET * completed_steps)
    DB.ElementTransformUtils.MoveElement(document, tag.Id, reverse)


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


def _record(tag, reason=''):
    return (_element_id_value(tag.Id), reason)


def _declutter_tag(document, view, tag, visible_elements):
    """Move one tag, restore it if unresolved, and return a status record."""
    midpoint, beam_direction, tag_head = _beam_data(document, tag)
    move_vector = _movement_vector(midpoint, beam_direction, tag_head)
    if move_vector is None:
        return 'skipped', _record(tag, 'No usable local straight tagged beam or movement direction')

    current_verticality = _beam_verticality(document, tag)
    completed_steps = 0
    found_collision = False
    deferred = False

    try:
        for other in visible_elements:
            if _element_id_value(tag.Id) == _element_id_value(other.Id):
                continue
            if _same_beam_tag(document, tag, other):
                continue

            tag_bounds = _bounds(tag, view)
            other_bounds = _bounds(other, view)
            if tag_bounds is None or other_bounds is None:
                continue
            if not boxes_overlap(tag_bounds, other_bounds):
                continue

            found_collision = True
            if hasattr(other, 'GetTaggedReferences'):
                other_verticality = _beam_verticality(document, other)
                if should_defer_to_other_tag(current_verticality, other_verticality):
                    deferred = True
                    continue

            cleared, step_count, move_error = _move_until_clear(
                document, view, tag, other, move_vector)
            if not cleared:
                _restore_tag(document, tag, move_vector, completed_steps + step_count)
                if move_error:
                    detail = 'Move failed after {} steps; original position restored: {}'.format(
                        step_count, move_error)
                else:
                    detail = 'Could not clear collision within {} steps; original position restored'.format(
                        MAX_MOVE_STEPS)
                return 'unresolved', _record(
                    tag, detail)
            completed_steps += step_count
    except Exception as error:
        try:
            _restore_tag(document, tag, move_vector, completed_steps)
        except Exception:
            pass
        return 'skipped', _record(tag, 'Move failed: {}'.format(error))

    if completed_steps:
        try:
            view.SetElementOverrides(tag.Id, _fresh_marker_override())
        except Exception as error:
            try:
                _restore_tag(document, tag, move_vector, completed_steps)
            except Exception:
                pass
            return 'skipped', _record(tag, 'Could not apply red marker: {}'.format(error))
        return 'moved', _record(tag, '{} movement steps'.format(completed_steps))
    if deferred:
        return 'skipped', _record(tag, 'Deferred to tag on more vertical beam')
    if found_collision:
        return 'skipped', _record(tag, 'No movable collision was found')
    return 'skipped', _record(tag, 'No overlaps found')


def _move_view(document, view):
    result = {
        'view': view,
        'candidates': 0,
        'moved': [],
        'reset': [],
        'unresolved': [],
        'skipped': [],
    }
    tags = _reaction_tags(document, view)
    result['candidates'] = len(tags)
    visible_elements = _visible_elements(document, view)
    for tag in tags:
        status, record = _declutter_tag(document, view, tag, visible_elements)
        result[status].append(record)
    return result


def _reset_view(document, view):
    result = {
        'view': view,
        'candidates': 0,
        'moved': [],
        'reset': [],
        'unresolved': [],
        'skipped': [],
    }
    tags = _reaction_tags(document, view)
    result['candidates'] = len(tags)
    for tag in tags:
        try:
            if not _source_marker_override(view.GetElementOverrides(tag.Id)):
                continue
            view.SetElementOverrides(tag.Id, DB.OverrideGraphicSettings())
            result['reset'].append(_record(tag, 'Red marker cleared'))
        except Exception as error:
            result['skipped'].append(_record(tag, 'Reset failed: {}'.format(error)))
    return result


def _print_report(output, action, results):
    output.print_md('# {}'.format(COMMAND_TITLE))
    output.print_md('**Action:** {}'.format(action))
    output.print_table([
        [
            _view_label(result['view']),
            result['candidates'],
            len(result['moved']),
            len(result['reset']),
            len(result['unresolved']),
            len(result['skipped']),
        ]
        for result in results
    ], columns=['View', 'Candidates', 'Moved', 'Reset', 'Unresolved', 'Skipped'])

    for result in results:
        details = []
        for label in ('moved', 'reset', 'unresolved', 'skipped'):
            for element_id, reason in result[label]:
                details.append([label.title(), element_id, reason])
        if details:
            output.print_md('## {}'.format(_view_label(result['view'])))
            output.print_table(details, columns=['Result', 'ElementId', 'Detail'])
    output.print_md(
        '> Prototype: Reset clears matching red view overrides only; it does not restore tag positions.')


def main():
    document = revit.doc
    output = script.get_output()
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
    with revit.Transaction(transaction_name, doc=document):
        for view in selected_views:
            if action == 'Move':
                results.append(_move_view(document, view))
            else:
                results.append(_reset_view(document, view))
    _print_report(output, action, results)


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
