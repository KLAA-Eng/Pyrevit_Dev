# -*- coding: utf-8 -*-
"""Host-independent overlay color and transparency settings."""

from collections import OrderedDict


# Rec. 601 luma weights: dark linework becomes opaque, white paper clear.
LUMA_WEIGHTS = (0.299, 0.587, 0.114)
DEFAULT_TINT = 'Red'
DEFAULT_OPACITY = 60
TINTS = OrderedDict([
    ('Red', (220, 0, 0)),
    ('Magenta', (200, 0, 200)),
    ('Blue', (0, 90, 255)),
    ('Green', (0, 150, 60)),
    ('Original', None),
])


def clamp_opacity(percent):
    """Return an integer opacity percent between 0 and 100."""
    try:
        value = int(round(float(percent)))
    except (TypeError, ValueError):
        return DEFAULT_OPACITY
    return max(0, min(100, value))


def tint_rgb(name):
    """Return the RGB tuple for a tint name, or None to keep source colors."""
    if name not in TINTS:
        name = DEFAULT_TINT
    return TINTS[name]


def color_matrix(tint, opacity_percent):
    """Return a 5x5 GDI+ ColorMatrix (row-vector convention) as nested lists.

    Output alpha is opacity * (1 - luminance), so paper drops out and line
    darkness sets line strength. A tint replaces RGB with a constant color;
    None keeps the source RGB.
    """
    opacity = clamp_opacity(opacity_percent) / 100.0
    matrix = [[0.0] * 5 for _ in range(5)]
    for row, weight in enumerate(LUMA_WEIGHTS):
        matrix[row][3] = -opacity * weight
    matrix[4][3] = opacity
    matrix[4][4] = 1.0
    if tint is None:
        for index in range(3):
            matrix[index][index] = 1.0
    else:
        for index, channel in enumerate(tint):
            matrix[4][index] = channel / 255.0
    return matrix


def apply_color_matrix(matrix, rgba):
    """Apply a matrix to one 0-1 RGBA pixel, clamped like GDI+ (for tests)."""
    vector = list(rgba) + [1.0]
    result = []
    for column in range(4):
        value = sum(vector[row] * matrix[row][column] for row in range(5))
        result.append(max(0.0, min(1.0, value)))
    return tuple(result)
