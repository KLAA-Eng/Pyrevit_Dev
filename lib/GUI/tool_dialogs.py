"""Tool-facing adapters for the standard dialogs; callers own model operations."""
from __future__ import unicode_literals

import sys

from GUI import dialogs
from GUI.dialogs.models import ActionChoice


def _owner(owner):
    if owner is not None:
        return owner
    # Keep modal dialogs owned by Revit, as the native helpers were.
    from pyrevit.api import AdWindows
    return AdWindows.ComponentManager.ApplicationWindow


def _title(title):
    if title:
        return title
    # Match pyRevit's caller-title default without importing the host at import time.
    from pyrevit import EXEC_PARAMS
    return EXEC_PARAMS.command_name or 'KL&A Tools'


def alert(msg, title=None, sub_msg=None, expanded=None, footer='', ok=True,
          cancel=False, yes=False, no=False, retry=False, warn_icon=True,
          exitscript=False, version=None, owner=None):
    """Return the legacy positive/negative boolean while showing a shared dialog.

    An OK-only stop exits after acknowledgement. For multi-button prompts,
    exitscript exits only after a negative response, matching pyRevit's alert.
    """
    title = _title(title)
    owner = _owner(owner)
    severity = 'warning' if warn_icon else 'information'
    body = '\n\n'.join(part for part in (sub_msg, footer) if part)
    just_ok = ok and not any((cancel, yes, no, retry))
    if just_ok:
        message = '\n\n'.join(part for part in (msg, body) if part)
        result = dialogs.show_message(title, message, severity=severity,
                                      details=expanded or '', version=version,
                                      owner=owner)
        positive = result.action == 'ok'
    else:
        buttons = []
        if yes:
            buttons.append('yes')
        elif ok:
            buttons.append('ok')
        if no:
            buttons.append('no')
        if retry:
            buttons.append('retry')
        if cancel:
            buttons.append('cancel')
        result = dialogs.choose_action(title, [], prompt=msg, content=body,
                                       buttons=tuple(buttons), severity=severity,
                                       details=expanded or '', version=version,
                                       owner=owner)
        positive = (not result.is_cancelled and result.value is not None
                    and result.value['key'] in ('ok', 'yes', 'retry'))
    if exitscript and (just_ok or not positive):
        sys.exit()
    return positive


def choose(options, title, prompt='Choose an Action', content='', version=None,
           owner=None):
    """Return the original action text, or None for Cancel/Close/Escape.

    Small tool menus use command links. An old explicit Cancel row becomes the
    standard Cancel button and is never returned as an executable action.
    """
    choices = [ActionChoice(option, option) for option in options if option != 'Cancel']
    result = dialogs.choose_action(_title(title), choices, prompt=prompt,
                                   content=content, buttons=('cancel',),
                                   version=version, owner=_owner(owner))
    if result.is_cancelled or result.value is None:
        return None
    return result.value['key'] if result.value['kind'] == 'command' else None


def ask_text(default='', prompt='', title=None, version=None, owner=None):
    """Return accepted text including blank text, or None on cancellation."""
    result = dialogs.ask_text(_title(title), prompt, default=default,
                              required=False, version=version, owner=_owner(owner))
    return None if result.is_cancelled else result.value
