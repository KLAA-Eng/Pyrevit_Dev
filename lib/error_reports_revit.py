# -*- coding: utf-8 -*-
"""Write an error report from inside a pyRevit command (host only).

Call ``report_exception`` from an ``except`` block. It gathers the Revit and
extension context, writes the report locally (and to the shared folder when
one is configured), copies the report id to the clipboard, and returns the id
and a message for the user. It never raises.
"""

import os
import sys
import traceback

from error_reports import (
    build_report,
    make_report_id,
    model_name,
    read_log_tail,
    report_folders,
    write_report,
)


FEEDBACK_HINT = 'Paste it into Outreach > Suggestions/Bugs Feedback so the tool can be fixed.'


def gather_context(doc=None):
    """Return extension, Revit, pyRevit, user, and model facts; missing ones are skipped."""
    context = {'user': os.environ.get('USERNAME', '')}
    try:
        import build_info
        context['extension_version'] = build_info.VERSION_LABEL
    except Exception:
        pass
    try:
        from pyrevit import HOST_APP
        context['revit_version'] = HOST_APP.version
        context['revit_build'] = HOST_APP.build
        context['revit_user'] = HOST_APP.username
        doc = doc or HOST_APP.doc
    except Exception:
        pass
    try:
        from pyrevit.versionmgr import get_pyrevit_version
        context['pyrevit_version'] = get_pyrevit_version().get_formatted()
    except Exception:
        pass
    try:
        if doc is not None:
            context['model'] = model_name(doc.PathName or doc.Title)
    except Exception:
        pass
    return context


def copy_to_clipboard(text):
    try:
        from System.Windows import Clipboard
        Clipboard.SetText(text)
        return True
    except Exception:
        return False


def report_exception(tool, tool_code, action, log_path=None, doc=None):
    """Report the exception being handled.

    tool: {'id', 'name', 'version'}. Returns (report id or None, user message).
    """
    try:
        error_type, error, _ = sys.exc_info()
        report_id = make_report_id(tool_code)
        report = build_report(
            report_id, tool, action,
            getattr(error_type, '__name__', str(error_type)), u'{}'.format(error),
            traceback.format_exc(), gather_context(doc), read_log_tail(log_path))
        if not write_report(report, report_folders()):
            return None, 'The error report could not be saved.'
        copied = copy_to_clipboard(report_id)
        return report_id, 'Error report {} saved{}. {}'.format(
            report_id, ' and copied to the clipboard' if copied else '', FEEDBACK_HINT)
    except Exception:
        return None, 'The error report could not be saved.'
