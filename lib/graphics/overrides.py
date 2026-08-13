"""Shared graphic override settings for pyRevit commands."""


def create_red_projection_override(db):
    """Create fresh settings with the standard red projection-line color."""
    settings = db.OverrideGraphicSettings()
    settings.SetProjectionLineColor(db.Color(255, 0, 0))
    return settings


def safe_override_property(override_settings, property_name, default=None):
    """Read an OverrideGraphicSettings property without leaking Revit API errors."""
    try:
        return getattr(override_settings, property_name)
    except Exception:
        return default


def is_valid_override_color(color):
    """Return True only for readable, explicitly assigned Revit colors."""
    if color is None:
        return False
    try:
        return bool(color.IsValid)
    except Exception:
        return False


def is_red_override_color(color):
    """Return True for a readable red Revit color."""
    if not is_valid_override_color(color):
        return False
    try:
        return (
            _color_channel(color, 'Red', 'red') == 255 and
            _color_channel(color, 'Green', 'green') == 0 and
            _color_channel(color, 'Blue', 'blue') == 0
        )
    except Exception:
        return False


def override_has_red_line(override_settings):
    """Return True when projection or cut line overrides are the standard red."""
    for property_name in ('ProjectionLineColor', 'CutLineColor'):
        if is_red_override_color(safe_override_property(override_settings, property_name)):
            return True
    return False


def override_has_existing_graphics(override_settings, db):
    """Return True when readable element override graphics are already assigned."""
    for property_name in (
        'ProjectionLineColor',
        'CutLineColor',
        'SurfaceForegroundPatternColor',
        'SurfaceBackgroundPatternColor',
        'CutForegroundPatternColor',
        'CutBackgroundPatternColor',
    ):
        if is_valid_override_color(safe_override_property(override_settings, property_name)):
            return True

    invalid_element_id = getattr(db.ElementId, 'InvalidElementId', None)
    for property_name in (
        'ProjectionLinePatternId',
        'CutLinePatternId',
        'SurfaceForegroundPatternId',
        'SurfaceBackgroundPatternId',
        'CutForegroundPatternId',
        'CutBackgroundPatternId',
    ):
        pattern_id = safe_override_property(override_settings, property_name)
        if pattern_id is not None and not _same_value(pattern_id, invalid_element_id):
            return True

    invalid_pen = getattr(db.OverrideGraphicSettings, 'InvalidPenNumber', -1)
    if safe_override_property(override_settings, 'ProjectionLineWeight', invalid_pen) != invalid_pen:
        return True
    if safe_override_property(override_settings, 'CutLineWeight', invalid_pen) != invalid_pen:
        return True

    undefined_detail = getattr(db.ViewDetailLevel, 'Undefined', None)
    detail_level = safe_override_property(override_settings, 'DetailLevel', undefined_detail)
    if undefined_detail is not None and detail_level != undefined_detail:
        return True

    if safe_override_property(override_settings, 'Halftone', False):
        return True
    return safe_override_property(override_settings, 'Transparency', 0) != 0


def _color_channel(color, api_name, fallback_name):
    value = getattr(color, api_name, None)
    if value is None:
        value = getattr(color, fallback_name)
    return value


def _same_value(left, right):
    try:
        return left == right
    except Exception:
        return False
