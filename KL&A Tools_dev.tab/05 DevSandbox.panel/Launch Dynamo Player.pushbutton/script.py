# -*- coding: utf-8 -*-
"""Open the Dynamo Player that is installed with the running Revit version."""
from pyrevit import HOST_APP, forms
from Autodesk.Revit.UI import PostableCommand, RevitCommandId


COMMAND_TITLE = 'Launch Dynamo Player'
LEGACY_COMMAND_ID = 'ID_PLAYLIST_DYNAMO'
POSTABLE_COMMAND_NAMES = ('DynamoPlayer', 'Playlist')


def _get_dynamo_player_command_id():
    for command_name in POSTABLE_COMMAND_NAMES:
        command = getattr(PostableCommand, command_name, None)
        if command is not None:
            return RevitCommandId.LookupPostableCommandId(command)
    return RevitCommandId.LookupCommandId(LEGACY_COMMAND_ID)


uiapp = HOST_APP.uiapp
command_id = _get_dynamo_player_command_id()

if command_id is None:
    forms.alert(
        'Dynamo Player is not available in this Revit installation.',
        title=COMMAND_TITLE,
        warn_icon=True,
        exitscript=True,
    )

if not uiapp.CanPostCommand(command_id):
    forms.alert(
        'Dynamo Player cannot be started right now. Finish the active Revit command and try again.',
        title=COMMAND_TITLE,
        warn_icon=True,
        exitscript=True,
    )

uiapp.PostCommand(command_id)
