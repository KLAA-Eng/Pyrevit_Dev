# Launch Dynamo Player Prototype

## Purpose

Adds a development-tab pyRevit pushbutton that opens the Dynamo Player bundled
with the current Revit installation.

## Compatibility

The command uses `PostableCommand.DynamoPlayer` when it is available, falls
back to the older `PostableCommand.Playlist`, then to the legacy
`ID_PLAYLIST_DYNAMO` Revit command identifier. It checks `CanPostCommand`
before posting the command.

## Validation

This is an explicitly disposable host-integration spike, so TEST-01's automated
RED/GREEN requirement is not applicable. Validate manually in each supported
Revit version with Dynamo installed:

1. Reload pyRevit and click **Launch Dynamo Player** under DevSandbox > Prototypes.
2. Verify that Dynamo Player opens and no document changes occur.
3. Start it while a Revit command is active and verify the actionable warning.

No graph is selected or run by this prototype.
