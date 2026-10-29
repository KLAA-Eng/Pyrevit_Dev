"""Host-independent caller identity for the shared shell.

The footer destinations and chrome labels are data in
``lib/GUI/Resources/KLCodeChrome.xaml`` (read by the shell template in both
hosts); this class carries only what the caller supplies. The normalisation
vectors in ``window_metadata_vectors.json`` are shared with the C# adapter's tests.
"""
from __future__ import unicode_literals

import re


class WindowMetadata(object):
    """Supply a caller's title and pure version; never infer a tool identity."""
    def __init__(self, title, version=None):
        self.Title = (title or '').strip()
        version = (version or '').strip()
        version = re.sub(r'^version\s*[:=]?\s*', '', version, flags=re.IGNORECASE)
        self.VersionText = ('v' + version.lstrip('vV') if re.match(r'^[vV]?\d+\.\d+', version) else '')
