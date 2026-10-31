# ForteWEB Export

## Identity

| Field | Value |
| --- | --- |
| Bundle path | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/ForteWEB Export.pushbutton` |
| Tool ID | `devsandbox.forteweb-export` |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/ForteWEB Export.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/ForteWEB Export.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/ForteWEB Export.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/ForteWEB Export.pushbutton/script.py`; `lib/forteweb_export/` |
| Maturity | Prototype |
| Tool version | `v0.0` |
| Status/origin | Prototype; KL&A custom tool adapted from a KL&A Dynamo Python script. Unreleased prototype; live acceptance pending. |
| Maintainer | KL&A |
| Revit versions live-tested | None yet |

## Purpose and workflow

`ForteWEB Export` writes the selected Revit structural framing members and beam
systems to a Weyerhaeuser ForteWEB project file (`.4wf`) so members do not have
to be re-entered by hand. Each member is cloned from a template `.4wf` that
contains one member of each needed kind (for example `floor_joist`,
`floor_flushbeam`, `floor_dropbeam`, and the `roof_` equivalents).

1. Select framing members or beam systems, or select nothing and pick them
   when prompted (click Finish).
2. Click the command. The first time, or when the stored template no longer
   exists, pick the template `.4wf`.
3. Choose where to save the `.4wf` (the default name is the model title).
4. Review the output table and warnings, then confirm supports in ForteWEB.

Shift+Click opens the settings instead of exporting (see Settings).

### Scope and detection

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

## Inputs and prerequisites

- A Revit model with structural framing members (with a location line) or
  beam systems, selected or picked.
- Member `Comments` for ForteWEB names; reference level, Structural Usage,
  and width parameters (`b`, `bf`, `Width`, `B`, `Beam Width`,
  `Nominal Width`; 3.5" when none) for kind, support, and span detection.
- Hanger families whose family name contains the configured hanger family
  name (default `Hangers_Clever_KLAA`) near member ends.
- A template `.4wf` (JSON) with one member of each kind to be exported. The
  template that projects should use is not yet confirmed (see Backlog).

### Settings

Shift+Click stores per-user pyRevit config section `forteweb_export`:
`template_path`, `tolerance_in` (default 0.5"), `hanger_family` (default
`Hangers_Clever_KLAA`), and `system_override` (`auto`, `floor`, `roof`). A
normal click asks for the template only when none is configured or the stored
file no longer exists. In the settings flow, cancelling the template pick
with no template configured leaves settings unchanged; an invalid tolerance
(not a positive number) keeps the previous value with an alert.

### Implementation inventory

- Entry point: `script.py` (selection, dialogs, settings, report output).
- `lib/forteweb_export/revit_export.py`: Revit API collection and support/kind
  detection (`run_export`, `is_exportable`, `ExportError`).
- `lib/forteweb_export/fourwf.py`: host-independent `.4wf` template parsing and
  writing. `SUPPORT_SOURCE` maps detected support types to template supports
  and is a best guess that must be confirmed in ForteWEB.
- `lib/forteweb_export/workflow.py`: host-independent geometry and decision
  helpers covered by `tests/forteweb_export_test.py`.

## Outputs and effects

### Model and external effects

No Revit transaction is started; the model is not modified. The command writes
only the chosen `.4wf` file and the pyRevit user config.

- The `.4wf` is a JSON array (project header plus one detail record per
  member) built from the template, written as ASCII-escaped JSON in UTF-8 to
  the path chosen in the save dialog, replacing any file there. Design
  results, solutions, and connector and report output are cleared so
  ForteWEB designs the members again.
- The template file is only read.
- The pyRevit output shows the written path, a table of members (Name, Revit
  Id, Kind, Clear span, Spacing, Start support, End support, How kind was
  set), and a warning list (missing names, sloped members, missing supports,
  custom spacings, unreadable beam-system spacing, joists outside a beam
  system, and members skipped for a clear span of zero or less).
- Cancelling the member pick, the template pick, or the save dialog ends the
  command with no file written. A bad selection, no exportable members, or a
  template without a needed member kind stops with an alert before the file
  is opened, so no file is written.

## Limits and compatibility

- Sloped members use their plan length, with a warning to set the pitch in
  ForteWEB.
- Members with no support found at an end keep the template support with
  bearing at the member end (3.5" width), with a warning.
- Members whose computed clear span is zero or less are left out with a
  warning; when no member remains the export stops.
- Joists not in a beam system keep the template spacing; non-standard
  spacings (other than 12/16/19.2/24/32) are written as custom spacing with a
  warning.
- Tributary width and loads are not collected from Revit (see Backlog).
- `SUPPORT_SOURCE` support mapping is unconfirmed (see Implementation
  inventory).
- Revit 2024 and later is the repository design target; no Revit version has
  live evidence yet.

## Validation evidence

| Date | Extension release | Revit version | Scenario | Result | Evidence link or location |
| --- | --- | --- | --- | --- | --- |
| 10.30.2026 | `0.0.14-dev` | None (CPython) | `tests/forteweb_export_test.py` `.4wf` writer and workflow rules | Pass | Local run on `dev.hangers` |

Automated checks do not prove Revit transactions or the user workflow; live
acceptance is pending.

### Validation boundary

Live Revit 2024+ and ForteWEB acceptance must confirm the `SUPPORT_SOURCE`
mapping, hanger and bearing detection on representative framing, beam-system
spacing, and that ForteWEB opens and designs the exported members.

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | Unreleased | 10.26.2026 | First DevSandbox version of the Revit to ForteWEB .4wf exporter. | Pending commit on `dev.hangers`; pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Backlog

- Confirm and document the template `.4wf` that projects should use.
- Optional tributary width and load (`trib_in`, `loads_psf`) inputs are
  supported by the writer but not yet collected from Revit.
- Live Revit and ForteWEB acceptance (see Validation boundary).
