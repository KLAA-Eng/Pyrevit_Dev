# -*- coding: utf-8 -*-
"""Render and manage the Revit-owned Carbon GWP summary image.

The drawing and Revit API calls live here rather than in the deterministic
workbook helpers.  Imports of ``System.Drawing`` are intentionally delayed so
this module remains importable by the CPython unit-test suite.
"""
from __future__ import print_function

from .chart import (
    CHART_WIDTH_INCHES,
    GWP_CHART_UNIT,
    chart_canvas_height_inches,
    chart_total,
    format_chart_amount,
    format_chart_detail,
)


MANAGED_CHART_SCHEMA_GUID = '0f65c38a-f7a0-4214-af07-20f387f52faa'
CHART_DEFINITIONS = {
    'gwp': {
        'image_type_name': 'KLCode Carbon GWP Summary',
        'marker': 'KLCode Carbon GWP Summary',
        'display_name': 'Carbon GWP',
    },
    'volume': {
        'image_type_name': 'KLCode Carbon Material Volume Summary',
        'marker': 'KLCode Carbon Material Volume Summary',
        'display_name': 'Carbon material volume',
    },
}
CHART_DPI = 300.0
CHART_WIDTH_PIXELS = int(round(CHART_WIDTH_INCHES * CHART_DPI))
CHART_WIDTH_FEET = CHART_WIDTH_INCHES / 12.0


def _points_to_pixels(points):
    """Convert a physical point size to the equivalent bitmap pixel size."""
    return int(round(float(points) * CHART_DPI / 72.0))


def _chart_definition(chart_kind):
    """Return the explicit ownership definition for a managed chart kind."""
    try:
        return CHART_DEFINITIONS[chart_kind]
    except KeyError:
        raise ValueError('Unknown Carbon chart kind: {}'.format(chart_kind))


def _load_drawing_api():
    """Load the built-in Windows drawing assemblies only inside Revit."""
    import clr
    clr.AddReference('System.Drawing')
    from System.Drawing import (
        Bitmap, Color, ColorTranslator, Font, FontStyle, Graphics, GraphicsUnit, Pen,
        Rectangle, RectangleF, SolidBrush, StringAlignment, StringFormat,
    )
    from System.Drawing.Imaging import ImageFormat
    from System.Drawing.Drawing2D import SmoothingMode
    from System.Drawing.Text import TextRenderingHint
    return {
        'Bitmap': Bitmap,
        'Color': Color,
        'ColorTranslator': ColorTranslator,
        'Font': Font,
        'FontStyle': FontStyle,
        'Graphics': Graphics,
        'GraphicsUnit': GraphicsUnit,
        'Pen': Pen,
        'Rectangle': Rectangle,
        'RectangleF': RectangleF,
        'SolidBrush': SolidBrush,
        'StringAlignment': StringAlignment,
        'StringFormat': StringFormat,
        'ImageFormat': ImageFormat,
        'SmoothingMode': SmoothingMode,
        'TextRenderingHint': TextRenderingHint,
    }


def _draw_text(graphics, text, font, brush, rectangle, alignment, drawing):
    """Draw text into a rectangle with a horizontal alignment."""
    text_format = drawing['StringFormat']()
    text_format.Alignment = alignment
    text_format.LineAlignment = drawing['StringAlignment'].Center
    graphics.DrawString(text, font, brush, rectangle, text_format)
    text_format.Dispose()


def render_chart_png(slices, image_path, center_caption='Total GWP', unit=GWP_CHART_UNIT):
    """Render a white landscape doughnut chart and legend to a PNG file.

    Args:
        slices: Valid chart-slice dictionaries from ``chart_slices_from_export_rows``.
        image_path: Destination PNG path.
        center_caption: Title displayed above the total inside the doughnut.
        unit: Unit displayed below the total and in legend amounts.

    Raises:
        ValueError: The caller did not provide any valid positive slices.

    The function creates a PNG at ``image_path`` and disposes every drawing
    resource before returning or raising.
    """
    if not slices:
        raise ValueError('At least one positive value is required to render a chart.')

    drawing = _load_drawing_api()
    # Each entry beyond six gains 0.65in of vertical room. The guard keeps
    # unusually long future legends readable rather than allowing text to
    # overlap if a workbook contains a very large material list.
    # The line rectangles include the font's normal System.Drawing leading, so
    # glyph ascenders and descenders remain inside the image at sheet scale.
    name_line_height = 80.0
    detail_line_height = 72.0
    internal_line_gap = _points_to_pixels(2)
    entry_gap = _points_to_pixels(14)
    legend_height = (
        ((name_line_height + internal_line_gap + detail_line_height) * len(slices)) +
        (entry_gap * max(len(slices) - 1, 0)))
    planned_height = int(round(chart_canvas_height_inches(len(slices)) * CHART_DPI))
    canvas_height = max(planned_height, int(round(legend_height + 150.0)))

    bitmap = drawing['Bitmap'](CHART_WIDTH_PIXELS, canvas_height)
    bitmap.SetResolution(CHART_DPI, CHART_DPI)
    graphics = drawing['Graphics'].FromImage(bitmap)
    graphics.Clear(drawing['Color'].White)
    graphics.SmoothingMode = drawing['SmoothingMode'].AntiAlias
    graphics.TextRenderingHint = drawing['TextRenderingHint'].AntiAliasGridFit

    # Use pixel units after converting the approved physical point sizes. Point
    # units would be DPI-scaled by System.Drawing a second time at 300dpi.
    legend_name_font = drawing['Font'](
        'Segoe UI Semibold', _points_to_pixels(16), drawing['FontStyle'].Regular,
        drawing['GraphicsUnit'].Pixel)
    legend_detail_font = drawing['Font'](
        'Segoe UI', _points_to_pixels(14), drawing['FontStyle'].Regular,
        drawing['GraphicsUnit'].Pixel)
    center_total_font = drawing['Font'](
        'Segoe UI', _points_to_pixels(26), drawing['FontStyle'].Bold,
        drawing['GraphicsUnit'].Pixel)
    center_unit_font = drawing['Font'](
        'Segoe UI Semibold', _points_to_pixels(20), drawing['FontStyle'].Regular,
        drawing['GraphicsUnit'].Pixel)
    center_caption_font = drawing['Font'](
        'Segoe UI Semibold', _points_to_pixels(20), drawing['FontStyle'].Regular,
        drawing['GraphicsUnit'].Pixel)
    dark_brush = drawing['SolidBrush'](drawing['Color'].FromArgb(45, 45, 45))
    white_brush = drawing['SolidBrush'](drawing['Color'].White)
    left_margin = 0.375 * CHART_DPI
    center_x = left_margin + (2.0 * CHART_DPI)
    center_y = canvas_height / 2.0
    outer_radius = 2.0 * CHART_DPI
    inner_radius = outer_radius * 0.60
    # IronPython's System.Drawing overload binder on the target host selects
    # FillPie(Brush, Rectangle, Single, Single), not the RectangleF overload.
    # Keep these integer bounds for pie/ellipse geometry; text still uses
    # RectangleF for its alignment and wrapping overloads.
    chart_rect = drawing['Rectangle'](
        int(round(center_x - outer_radius)),
        int(round(center_y - outer_radius)),
        int(round(outer_radius * 2)),
        int(round(outer_radius * 2)))
    total = chart_total(slices)

    try:
        start_angle = -90.0
        for item in slices:
            sweep_angle = (item['value'] / total) * 360.0
            fill_brush = drawing['SolidBrush'](
                drawing['ColorTranslator'].FromHtml(item['color']))
            try:
                graphics.FillPie(fill_brush, chart_rect, start_angle, sweep_angle)
            finally:
                fill_brush.Dispose()
            start_angle += sweep_angle

        graphics.FillEllipse(
            white_brush,
            drawing['Rectangle'](
                int(round(center_x - inner_radius)),
                int(round(center_y - inner_radius)),
                int(round(inner_radius * 2)),
                int(round(inner_radius * 2))))
        # Keep title and unit 0.10in (30px at 300dpi) from the 26pt total so
        # the three-line stack is vertically balanced around the centered value.
        _draw_text(
            graphics, center_caption, center_caption_font, dark_brush,
            drawing['RectangleF'](center_x - 350, center_y - 195, 700, 100),
            drawing['StringAlignment'].Center, drawing)
        _draw_text(
            graphics, '{:,}'.format(int(round(total))), center_total_font, dark_brush,
            drawing['RectangleF'](center_x - 350, center_y - 65, 700, 130),
            drawing['StringAlignment'].Center, drawing)
        _draw_text(
            graphics, unit, center_unit_font, dark_brush,
            drawing['RectangleF'](center_x - 350, center_y + 95, 700, 100),
            drawing['StringAlignment'].Center, drawing)

        # Keep category information in a fixed legend rather than floating it
        # around the chart. The 3in column begins 1/4in beyond the doughnut.
        legend_x = left_margin + (4.0 * CHART_DPI) + (0.25 * CHART_DPI)
        legend_width = CHART_WIDTH_PIXELS - legend_x - (0.25 * CHART_DPI)
        legend_top = (canvas_height - legend_height) / 2.0
        swatch_size = int(round(0.25 * CHART_DPI))
        for index, item in enumerate(slices):
            row_y = legend_top + (index * (
                name_line_height + internal_line_gap + detail_line_height + entry_gap))
            swatch_brush = drawing['SolidBrush'](
                drawing['ColorTranslator'].FromHtml(item['color']))
            try:
                graphics.FillRectangle(
                    swatch_brush,
                    drawing['Rectangle'](
                        int(legend_x),
                        int(row_y + ((name_line_height - swatch_size) / 2.0)),
                        swatch_size,
                        swatch_size))
            finally:
                swatch_brush.Dispose()
            _draw_text(
                graphics, item['display_label'], legend_name_font, dark_brush,
                drawing['RectangleF'](
                    legend_x + swatch_size + 18, row_y,
                    legend_width - swatch_size - 18, name_line_height),
                drawing['StringAlignment'].Near, drawing)
            _draw_text(
                graphics, format_chart_detail(item, total, unit), legend_detail_font, dark_brush,
                drawing['RectangleF'](
                    legend_x + swatch_size + 18,
                    row_y + name_line_height + internal_line_gap,
                    legend_width - swatch_size - 18, detail_line_height),
                drawing['StringAlignment'].Near, drawing)
        bitmap.Save(image_path, drawing['ImageFormat'].Png)
    finally:
        legend_name_font.Dispose()
        legend_detail_font.Dispose()
        center_total_font.Dispose()
        center_unit_font.Dispose()
        center_caption_font.Dispose()
        dark_brush.Dispose()
        white_brush.Dispose()
        graphics.Dispose()
        bitmap.Dispose()


def _element_id_value(element_id):
    """Return an integer Revit element id across supported Revit releases."""
    for property_name in ('Value', 'IntegerValue'):
        try:
            return int(getattr(element_id, property_name))
        except Exception:
            pass
    return None


def _chart_schema(db):
    """Return the dedicated marker schema used to recognize only this chart."""
    import System
    storage = db.ExtensibleStorage
    schema_guid = System.Guid(MANAGED_CHART_SCHEMA_GUID)
    schema = storage.Schema.Lookup(schema_guid)
    if schema is not None:
        return schema
    builder = storage.SchemaBuilder(schema_guid)
    builder.SetSchemaName('KLCodeCarbonGwpSummaryChart')
    builder.SetReadAccessLevel(storage.AccessLevel.Public)
    builder.SetWriteAccessLevel(storage.AccessLevel.Public)
    builder.AddSimpleField('generator_marker', System.String)
    return builder.Finish()


def _is_managed_chart(image_instance, schema, marker):
    """Return whether an image instance carries this command's marker."""
    import System
    try:
        entity = image_instance.GetEntity(schema)
        return entity.IsValid() and entity.Get[System.String](
            'generator_marker') == marker
    except Exception:
        return False


def _mark_managed_chart(image_instance, schema, db, marker):
    """Attach a marker so reruns never adopt a user-created image by name."""
    import System
    entity = db.ExtensibleStorage.Entity(schema)
    entity.Set[System.String]('generator_marker', marker)
    image_instance.SetEntity(entity)


def _managed_instances(document, target_sheet, db, chart_kind):
    """Return owned instances on the target sheet and reject ambiguous reuse."""
    definition = _chart_definition(chart_kind)
    schema = _chart_schema(db)
    target_id = _element_id_value(target_sheet.Id)
    matching = []
    elsewhere = []
    for image_instance in db.FilteredElementCollector(document).OfClass(db.ImageInstance):
        if not _is_managed_chart(image_instance, schema, definition['marker']):
            continue
        if _element_id_value(image_instance.OwnerViewId) == target_id:
            matching.append(image_instance)
        else:
            elsewhere.append(image_instance)
    if elsewhere:
        raise ValueError(
            'The managed {} image type is placed outside SYNC TO CENTRAL. '
            'Refusing to update an ambiguous chart.'.format(
                definition['display_name']))
    if len(matching) > 1:
        raise ValueError(
            'Multiple managed {} charts were found on SYNC TO CENTRAL.'.format(
                definition['display_name']))
    return matching


def managed_chart_exists(document, target_sheet, db, chart_kind='gwp'):
    """Return whether exactly one managed chart already exists on the sheet.

    Ambiguous image ownership remains an error rather than being silently
    treated as a first-run placement.

    Args:
        document: Active Revit project document.
        target_sheet: Required ``SYNC TO CENTRAL`` sheet.
        db: Autodesk Revit DB API namespace.
        chart_kind: Managed chart identifier.

    Returns:
        ``True`` when exactly one owned image exists on the target sheet.

    Raises:
        ValueError: Managed image ownership is ambiguous.
    """
    return bool(_managed_instances(document, target_sheet, db, chart_kind))


def _image_type_options(image_path, db):
    """Return Revit options that embed the generated PNG in the project."""
    # Revit ImageTypeOptions accepts a local file and explicitly distinguishes
    # imported and linked image data. Source: https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/7dda4131-548f-7c39-4dcd-ba9b85846018.htm
    return db.ImageTypeOptions(image_path, False, db.ImageTypeSource.Import)


def _box_top_left(box, db):
    """Return the top-left sheet point of a Revit bounding box."""
    return db.XYZ(box.Min.X, box.Max.Y, 0.0)


def _box_top_right(box, db):
    """Return the top-right sheet point of a Revit bounding box."""
    return db.XYZ(box.Max.X, box.Max.Y, 0.0)


def _box_bottom_left(box, db):
    """Return the bottom-left sheet point of a Revit bounding box."""
    return db.XYZ(box.Min.X, box.Min.Y, 0.0)


def titleblock_top_right(document, target_sheet, db):
    """Return the unique titleblock's top-right point on the target sheet.

    Args:
        document: Active Revit project document.
        target_sheet: Required ``SYNC TO CENTRAL`` sheet.
        db: Autodesk Revit DB API namespace.

    Returns:
        Revit ``XYZ`` point at the titleblock's top-right corner.

    Raises:
        ValueError: The sheet does not have exactly one usable titleblock.
    """
    titleblocks = list(
        db.FilteredElementCollector(document, target_sheet.Id)
        .OfCategory(db.BuiltInCategory.OST_TitleBlocks)
        .WhereElementIsNotElementType())
    if len(titleblocks) != 1:
        raise ValueError(
            'Expected exactly one titleblock on SYNC TO CENTRAL; found {}.'.format(
                len(titleblocks)))
    box = titleblocks[0].get_BoundingBox(target_sheet)
    if box is None:
        raise ValueError('The SYNC TO CENTRAL titleblock does not have a sheet bounding box.')
    return _box_top_right(box, db)


def image_bottom_left(image_instance, target_sheet, db):
    """Return a placed image's bottom-left point on the target sheet.

    Args:
        image_instance: Placed Revit ``ImageInstance`` to inspect.
        target_sheet: Sheet that owns the image.
        db: Autodesk Revit DB API namespace.

    Returns:
        Revit ``XYZ`` point at the image bounding box's bottom-left corner.

    Raises:
        ValueError: Revit cannot provide an image bounding box.

    Regenerates the image document before reading its bounding box.
    """
    image_instance.Document.Regenerate()
    box = image_instance.get_BoundingBox(target_sheet)
    if box is None:
        raise ValueError('The managed chart does not have a sheet bounding box.')
    return _box_bottom_left(box, db)


def _move_image_top_left(document, image_instance, target_sheet, point, db):
    """Move a chart image so its bounding-box top-left matches ``point``."""
    document.Regenerate()
    box = image_instance.get_BoundingBox(target_sheet)
    if box is None:
        raise ValueError('The managed chart does not have a sheet bounding box.')
    current = _box_top_left(box, db)
    offset = db.XYZ(
        point.X - current.X,
        point.Y - current.Y,
        point.Z - current.Z)
    db.ElementTransformUtils.MoveElement(document, image_instance.Id, offset)


def create_or_reload_chart(document, target_sheet, point, image_path, db, chart_kind='gwp'):
    """Create the managed imported image or reload it in place.

    The caller must open a Revit transaction. Imported images embed their PNG
    data in the project. The image is then aligned to the supplied sheet point.

    Args:
        document: Active Revit project document with an open transaction.
        target_sheet: Required ``SYNC TO CENTRAL`` sheet.
        point: Revit ``XYZ`` location for the chart's top-left corner.
        image_path: Generated PNG to import or reload.
        db: Autodesk Revit DB API namespace.
        chart_kind: Managed chart identifier.

    Returns:
        Tuple ``('created' or 'updated', ImageInstance)``.

    Raises:
        ValueError: Existing chart ownership or placement is ambiguous.
    """
    definition = _chart_definition(chart_kind)
    options = _image_type_options(image_path, db)
    try:
        instances = _managed_instances(document, target_sheet, db, chart_kind)
        if instances:
            image_instance = instances[0]
            image_type = document.GetElement(image_instance.GetTypeId())
            type_instances = []
            for candidate in db.FilteredElementCollector(document).OfClass(db.ImageInstance):
                if _element_id_value(candidate.GetTypeId()) == _element_id_value(image_type.Id):
                    type_instances.append(candidate)
            if len(type_instances) != 1:
                raise ValueError(
                    'The managed {} image type is shared by other images. '
                    'Refusing to update an ambiguous chart.'.format(
                        definition['display_name']))
            image_type.ReloadFrom(options)
            image_instance.LockProportions = True
            image_instance.Width = CHART_WIDTH_FEET
            _move_image_top_left(document, image_instance, target_sheet, point, db)
            return 'updated', image_instance
        # Revit creates an ImageType first, then an ImageInstance in the target
        # view. Source: https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/0f4cd250-7925-6714-3e08-2bd7c0266252.htm
        image_type = db.ImageType.Create(document, options)
        try:
            image_type.Name = definition['image_type_name']
        except Exception:
            raise ValueError(
                'The generated {} image could not be marked for safe updates.'.format(
                    definition['display_name']))
        placement = db.ImagePlacementOptions(point, db.BoxPlacement.TopLeft)
        image_instance = db.ImageInstance.Create(document, target_sheet, image_type.Id, placement)
        image_instance.LockProportions = True
        image_instance.Width = CHART_WIDTH_FEET
        _mark_managed_chart(image_instance, _chart_schema(db), db, definition['marker'])
        _move_image_top_left(document, image_instance, target_sheet, point, db)
        return 'created', image_instance
    finally:
        try:
            options.Dispose()
        except Exception:
            pass
