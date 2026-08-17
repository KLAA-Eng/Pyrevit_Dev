"""Static HTML generation for Detail and Drafting View deliverables."""
from __future__ import unicode_literals

try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote


INVALID_FILENAME_CHARACTERS = set('<>:"/\\|?*')


def render_detail_html(title, jpeg_filename, pdf_filename):
    """Return a UTF-8-ready static page with safe relative artifact links."""
    if not _is_text(title) or not title.strip():
        raise ValueError('Detail title is required.')
    _validate_filename(jpeg_filename)
    _validate_filename(pdf_filename)
    escaped_title = _escape_html(title)
    jpeg_url = quote(jpeg_filename.encode('utf-8'))
    pdf_url = quote(pdf_filename.encode('utf-8'))
    return u'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
</head>
<body>
  <main>
    <h1>{title}</h1>
    <p><a href="{pdf_url}">Open PDF</a></p>
    <img src="{jpeg_url}" alt="Preview of {title}">
  </main>
</body>
</html>
'''.format(title=escaped_title, jpeg_url=jpeg_url, pdf_url=pdf_url)


def _validate_filename(filename):
    if not _is_text(filename) or not filename or filename in ('.', '..'):
        raise ValueError('Artifact filename is invalid.')
    if filename != filename.strip() or any(
            character in INVALID_FILENAME_CHARACTERS or ord(character) < 32
            for character in filename):
        raise ValueError('Artifact filename is invalid.')


def _escape_html(value):
    return value.replace('&', '&amp;').replace('<', '&lt;').replace(
        '>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')


def _is_text(value):
    try:
        return isinstance(value, basestring)
    except NameError:
        return isinstance(value, str)
