# Launch Dynamo Player Prototype

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.launch-dynamo-player` |
| Tool version | `v0.0` |
| Status | Released |
| Status/origin | Prototype; KL&A custom tool. |
| Main delivery | 0.0.4.beta |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Launch Dynamo Player.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Launch Dynamo Player.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Launch Dynamo Player.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Launch Dynamo Player.pushbutton/script.py` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | 0.0.4.beta | 08.17.2026 | First main delivery of the Dynamo Player launcher with availability checks. | 1f3dd23 |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

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
