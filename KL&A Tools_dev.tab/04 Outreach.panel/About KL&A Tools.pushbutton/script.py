# -*- coding: utf-8 -*-
"""Show extension build and load-path details for support and release verification."""

import os

from pyrevit import forms

try:
    import pyrevit
except Exception:
    pyrevit = None

from lib import build_info


def find_extension_root(path):
    current = os.path.abspath(path)
    while current and not current.lower().endswith(".extension"):
        parent = os.path.dirname(current)
        if parent == current:
            return os.path.abspath(path)
        current = parent
    return current


def get_pyrevit_version():
    if pyrevit is None:
        return "unknown"

    for attr_name in ("VERSION_STRING", "__version__"):
        value = getattr(pyrevit, attr_name, None)
        if value:
            return str(value)

    version_mgr = getattr(pyrevit, "versionmgr", None)
    if version_mgr:
        try:
            return str(version_mgr.get_pyrevit_version())
        except Exception:
            pass

    return "unknown"


def get_revit_build():
    app = __revit__.Application
    version_number = getattr(app, "VersionNumber", "") or ""
    sub_version = getattr(app, "SubVersionNumber", "") or ""
    build_parts = [part for part in (version_number, sub_version) if part]
    return " | ".join(build_parts) or "unknown"


def main():
    app = __revit__.Application
    extension_root = find_extension_root(__file__)

    lines = [
        "Extension: KL&A Tools",
        "Version: {0}".format(build_info.VERSION),
        "Channel: {0}".format(getattr(build_info, "CHANNEL", "unknown") or "unknown"),
        "Release Date: {0}".format(getattr(build_info, "RELEASE_DATE", "unknown") or "unknown"),
        "Git Tag: {0}".format(getattr(build_info, "GIT_TAG", "unknown") or "unknown"),
        "Git SHA: {0}".format(getattr(build_info, "GIT_SHA", "unknown") or "unknown"),
        "Build Date: {0}".format(getattr(build_info, "BUILD_DATE", "unknown") or "unknown"),
        "Loaded Extension Path: {0}".format(extension_root),
        "pyRevit Version: {0}".format(get_pyrevit_version()),
        "Revit Version: {0}".format(getattr(app, "VersionName", "unknown") or "unknown"),
        "Revit Build: {0}".format(get_revit_build()),
    ]

    forms.alert("\n".join(lines), title="About KL&A Tools")


if __name__ == "__main__":
    main()
