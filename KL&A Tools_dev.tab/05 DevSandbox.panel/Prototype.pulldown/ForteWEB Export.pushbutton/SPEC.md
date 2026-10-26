# ForteWEB Export

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.forteweb-export` |
| Tool version | `v0.0` |
| Status | Unreleased prototype; live acceptance pending |
| Status/origin | Prototype; KL&A custom tool adapted from a KL&A Dynamo Python script. |
| Main delivery | Unreleased |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/ForteWEB Export.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/ForteWEB Export.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/ForteWEB Export.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/ForteWEB Export.pushbutton/script.py`; `lib/forteweb_export/` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | Unreleased | 10.26.2026 | First DevSandbox version of the Revit to ForteWEB .4wf exporter. | Pending commit on `dev.hangers`; pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Purpose

`ForteWEB Export` writes the selected Revit structural framing members and beam
systems to a Weyerhaeuser ForteWEB project file (`.4wf`) so members do not have
to be re-entered by hand. Each member is cloned from a template `.4wf` that
contains one member of each needed kind (for example `floor_joist`,
`floor_flushbeam`, `floor_dropbeam`, and the `roof_` equivalents).

## Scope and output

- Selection: the current Revit selection; when it is empty the command prompts
  for a pick limited to structural framing with a location line and beam
  systems. Any other selected element stops the export with no file written.
- Name: the member's `Comments`, falling back to `Id <n>` with a warning. Notes
  record the Revit Id and type name.
- Beam systems export one joist per distinct length, named from the beam
  system's `Comments`. Joist spacing is the median centre-to-centre gap and is
  written only for beam-system members.
- Kind: beam-system member or Structural Usage = Joist -> joist; other framing
  bearing on top -> drop beam; framing into the side or hangers -> flush beam;
  otherwise the top of beam is compared with its reference level (within 2"
  -> flush).
- Floor/roof: Shift+Click override, else `auto` uses roof when the reference
  level name contains `ROOF`.
- End supports are searched around each end: hanger family -> hanger; framing
  whose top the beam bears on -> beam; other framing -> hanger; structural
  column or wall -> column or wall. Clear span is between inside support faces.
- Output: the `.4wf` file plus a pyRevit output table of members and a warning
  list (missing names, sloped members, missing supports, custom spacings).

## Settings

Shift+Click stores per-user pyRevit config section `forteweb_export`:
`template_path`, `tolerance_in` (default 0.5"), `hanger_family` (default
`Hangers_Clever_KLAA`), and `system_override` (`auto`, `floor`, `roof`). A
normal click asks for the template only when none is configured or the stored
file no longer exists.

## Implementation inventory

- Entry point: `script.py` (selection, dialogs, settings, report output).
- `lib/forteweb_export/revit_export.py`: Revit API collection and support/kind
  detection (`run_export`, `is_exportable`, `ExportError`).
- `lib/forteweb_export/fourwf.py`: host-independent `.4wf` template parsing and
  writing. `SUPPORT_SOURCE` maps detected support types to template supports
  and is a best guess that must be confirmed in ForteWEB.
- `lib/forteweb_export/workflow.py`: host-independent geometry and decision
  helpers covered by `tests/forteweb_export_test.py`.

## Model and external effects

No Revit transaction is started; the model is not modified. The command writes
only the chosen `.4wf` file and the pyRevit user config.

## Validation boundary

Live Revit 2024+ and ForteWEB acceptance must confirm the `SUPPORT_SOURCE`
mapping, hanger and bearing detection on representative framing, beam-system
spacing, and that ForteWEB opens and designs the exported members.

## Future development

- Confirm and document the template `.4wf` that projects should use.
- Optional tributary width and load (`trib_in`, `loads_psf`) inputs are
  supported by the writer but not yet collected from Revit.
