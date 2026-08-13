"""Shared graphic override settings for pyRevit commands."""


def create_red_projection_override(db):
    """Create fresh settings with the standard red projection-line color."""
    settings = db.OverrideGraphicSettings()
    settings.SetProjectionLineColor(db.Color(255, 0, 0))
    return settings
