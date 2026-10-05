# Trial URL Button

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.trial` |
| Tool version | `v0.0` |
| Status | Released |
| Status/origin | Prototype; KL&A custom tool. |
| Main delivery | 0.0.6beta |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Trial.urlbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Trial.urlbutton`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Trial.urlbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Trial.urlbutton/bundle.yaml` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | 0.0.6beta | 09.15.2026 | First main delivery of the configured Microsoft Forms trial URL button. | 300f8d4 |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Bundle reference

extension: .urlbutton
requires:
    - bundle.yaml         # includes bundle metadata e.g. tooltip message

optional:
    - icon.png            # for Revit UI icons
    - tooltip.png         # for Revit UI button tooltip image
    - tooltip.mp4         # for Revit UI button tooltip video


## URL-Button Bundle

URL Bundles open the URL link specified in the bundle file, in the default browser. They are great for creating intranet shortcut buttons.
