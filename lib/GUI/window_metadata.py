"""Host-independent caller identity and shared footer destinations."""
from __future__ import unicode_literals

import re


PROTOTYPE_URI = 'https://forms.cloud.microsoft/r/HjuggSZqyU'
OUTREACH_URI = ('https://forms.microsoft.com/Pages/ResponsePage.aspx?'
                'id=Bfmd9K3MFkqVWdMqprbPvvfxx29Ur-NGhLTDKxuFAqVUMU1OMUpRWDRKUDBMNEFEMlQ2SEJJNFdCUi4u')


class WindowMetadata(object):
    """Supply a caller's title and pure version; never infer a tool identity."""
    def __init__(self, title, version=None):
        self.Title = (title or '').strip()
        version = (version or '').strip()
        version = re.sub(r'^version\s*[:=]?\s*', '', version, flags=re.IGNORECASE)
        self.VersionText = ('v' + version.lstrip('vV') if re.match(r'^[vV]?\d+\.\d+', version) else '')
        self.PrototypeUri = PROTOTYPE_URI
        self.OutreachUri = OUTREACH_URI
