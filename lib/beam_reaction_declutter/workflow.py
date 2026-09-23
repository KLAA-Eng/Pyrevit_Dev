"""Pure geometry and classification rules for Beam Reaction Declutter.

The pyRevit command adapts Revit elements and bounding boxes into these small,
host-independent rules so they can be covered without starting Revit.
"""

OVERLAP_TOLERANCE = 0.01
STEP_DISTANCE_FEET = 0.2
MAX_MOVE_STEPS = 8
MARKER_COLOR = (254, 0, 0)


def is_reaction_family(family_name):
    """Return True when a tag family name follows the Dynamo Reaction rule."""
    if family_name is None:
        return False
    try:
        return 'reaction' in family_name.lower()
    except Exception:
        return False


def boxes_overlap(first, second, tolerance=OVERLAP_TOLERANCE):
    """Return True when two (min_x, min_y, max_x, max_y) boxes overlap.

    This mirrors the Dynamo graph's two-dimensional, view-bounding-box test.
    Missing boxes are deliberately non-overlapping so their owners can be
    reported by the Revit adapter instead of producing a false collision.
    """
    if first is None or second is None:
        return False

    return not (
        first[2] - tolerance < second[0] or
        first[0] + tolerance > second[2] or
        first[3] - tolerance < second[1] or
        first[1] + tolerance > second[3]
    )


def translate_box(bounds, vector):
    """Return bounds translated by an (x, y) vector without changing input."""
    return (
        bounds[0] + vector[0],
        bounds[1] + vector[1],
        bounds[2] + vector[0],
        bounds[3] + vector[1],
    )


def steps_to_clear_overlap(bounds, blocker, step_vector,
                           max_steps=MAX_MOVE_STEPS):
    """Return the step count needed to clear a blocker, or None when capped.

    The Revit adapter still re-reads each live bounding box after a move. This
    pure calculation supplies deterministic coverage for the cap and tolerance
    rules used by that adapter.
    """
    if not boxes_overlap(bounds, blocker):
        return 0

    current = bounds
    for step_count in range(1, max_steps + 1):
        current = translate_box(current, step_vector)
        if not boxes_overlap(current, blocker):
            return step_count
    return None


def should_defer_to_other_tag(current_verticality, other_verticality):
    """Return True when the other beam is more vertical in the view plane."""
    return current_verticality < other_verticality


def is_marker_color(red, green, blue):
    """Return True only for the Dynamo graph's exact red reset marker."""
    return (red, green, blue) == MARKER_COLOR
