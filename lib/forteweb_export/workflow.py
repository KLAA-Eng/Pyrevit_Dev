"""Host-independent decisions used by the ForteWEB Export prototype."""

from __future__ import division

import math


DEFAULT_HANGER_FAMILY = 'Hangers_Clever_KLAA'
DEFAULT_TOLERANCE_IN = 0.5
SYSTEM_OVERRIDES = ('auto', 'floor', 'roof')


def plan_closest(px, py, ax, ay, bx, by):
    """Closest point on segment AB to P in plan -> (x, y, dist)."""
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    t = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    cx, cy = ax + t * dx, ay + t * dy
    return cx, cy, math.hypot(px - cx, py - cy)


def fmt_ftin(inches):
    feet = int(inches // 12)
    return "%d' %.2f\"" % (feet, inches - feet * 12)


def structural_system(level_name, override='auto'):
    """'floor' or 'roof': explicit override, else a level name containing ROOF."""
    override = (override or 'auto').lower()
    if override in ('floor', 'roof'):
        return override
    return 'roof' if level_name and 'roof' in level_name.lower() else 'floor'


def median_spacing_in(offsets_ft):
    """Centre-to-centre spacing (in) = median gap between sorted joist offsets (ft)."""
    offsets = sorted(offsets_ft)
    gaps = sorted(b - a for a, b in zip(offsets, offsets[1:]) if b - a > 1e-3)
    if not gaps:
        return None
    return round(gaps[len(gaps) // 2] * 12.0, 2)


def clear_span_in(start_support, end_support):
    """Distance between the inside faces of two supports positioned along the beam."""
    return ((end_support['s'] - end_support['width'] / 2.0)
            - (start_support['s'] + start_support['width'] / 2.0))


def beam_kind(bearing_on_top, framing_into_side, top_below_level_in=None, level_name=None):
    """Return (flushbeam|dropbeam, reason) from framing counts or level offset."""
    if bearing_on_top or framing_into_side:
        kind = 'dropbeam' if bearing_on_top > framing_into_side else 'flushbeam'
        return kind, '%d bearing on top / %d framing into side' % (
            bearing_on_top, framing_into_side)
    if top_below_level_in is None:
        return 'flushbeam', 'no framing found, no level - assumed flush'
    kind = 'flushbeam' if top_below_level_in <= 2.0 else 'dropbeam'
    return kind, 'no framing found; top of beam %.2f" below level %s' % (
        top_below_level_in, level_name)


def system_member_labels(base, lengths):
    """Label one exported joist per distinct length, longest first."""
    ordered = sorted(set(lengths), reverse=True)
    if len(ordered) == 1:
        return [(ordered[0], base)]
    return [(length, '%s - %d' % (base, number)) for number, length in enumerate(ordered, 1)]


def parse_tolerance(text):
    """Return a positive tolerance in inches, or None for invalid input."""
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None
