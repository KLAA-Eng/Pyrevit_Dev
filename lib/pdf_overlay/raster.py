# -*- coding: utf-8 -*-
"""System.Drawing rendering for PDF overlays (pyRevit host only)."""

import math
import os

import clr
clr.AddReference('System.Drawing')

from System import Array, Single
from System.Drawing import Bitmap, Color, Graphics, GraphicsUnit, Rectangle
from System.Drawing.Drawing2D import CompositingQuality, InterpolationMode, PixelOffsetMode
from System.Drawing.Imaging import ColorMatrix, ImageAttributes, ImageFormat, PixelFormat
from System.IO import File, MemoryStream

from .geometry import rotated_canvas_size
from .style import color_matrix


def load_bitmap(path):
    """Load a bitmap without keeping the file locked."""
    stream = MemoryStream(File.ReadAllBytes(path))
    try:
        image = Bitmap(stream)
        try:
            return Bitmap(image)
        finally:
            image.Dispose()
    finally:
        stream.Dispose()


def save_png(bitmap, path):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    bitmap.Save(path, ImageFormat.Png)


def flatten_on_white(image):
    """Return an opaque copy of image on white paper.

    The overlay alpha comes from luminance, so a transparent page background
    (which may carry black RGB) must become white before rendering.
    """
    page = Bitmap(image.Width, image.Height, PixelFormat.Format32bppArgb)
    graphics = Graphics.FromImage(page)
    try:
        graphics.Clear(Color.White)
        graphics.DrawImage(image, Rectangle(0, 0, image.Width, image.Height),
                           0, 0, image.Width, image.Height, GraphicsUnit.Pixel)
    finally:
        graphics.Dispose()
    return page


def _image_attributes(tint, opacity):
    rows = [Array[Single]([float(value) for value in row])
            for row in color_matrix(tint, opacity)]
    attributes = ImageAttributes()
    attributes.SetColorMatrix(ColorMatrix(Array[Array[Single]](rows)))
    return attributes


def render_overlay(source, rotation, tint, opacity):
    """Return a transparent-paper, tinted copy of source rotated by rotation.

    rotation is counterclockwise in radians as seen in the Revit view. GDI+
    works with y down, so the same visual turn is a negative angle there.
    """
    width, height = source.Width, source.Height
    canvas_width, canvas_height = rotated_canvas_size(width, height, rotation)
    canvas = Bitmap(canvas_width, canvas_height, PixelFormat.Format32bppArgb)
    attributes = _image_attributes(tint, opacity)
    graphics = Graphics.FromImage(canvas)
    try:
        graphics.Clear(Color.Transparent)
        graphics.InterpolationMode = InterpolationMode.HighQualityBicubic
        graphics.PixelOffsetMode = PixelOffsetMode.HighQuality
        graphics.CompositingQuality = CompositingQuality.HighQuality
        graphics.TranslateTransform(canvas_width / 2.0, canvas_height / 2.0)
        graphics.RotateTransform(-math.degrees(rotation))
        graphics.TranslateTransform(-width / 2.0, -height / 2.0)
        graphics.DrawImage(source, Rectangle(0, 0, width, height),
                           0, 0, width, height, GraphicsUnit.Pixel, attributes)
    finally:
        graphics.Dispose()
        attributes.Dispose()
    return canvas
