# Hide Engineering Notes

## Identity

| Field | Value |
| --- | --- |
| Bundle path | `KL&A Tools_dev.tab/02 KL&A Tools.panel/Hide Engineering Notes.pushbutton` |
| Maturity | Beta |
| Last extension release affecting this command | `0.0.9-beta` |
| Maintainer | KL&A Tools |
| Revit versions live-tested | No exact version recorded for this command. |

## Purpose and workflow

This command helps documentation teams hide or unhide KL&A engineering-note
text without deleting it. Click the ribbon button, choose **Hide engineer
notes** or **Unhide engineer notes** in the native Revit dialog, then review the
completion report in the pyRevit output window. Hold Shift while clicking for a
detailed diagnostic report.
Cancelling the dialog exits before a Revit transaction starts.

## Inputs and prerequisites

- An active Revit project document with TextNote instances.
- Text note types whose normalized names begin with `KLAA - ENGINEER'S NOTE`.
  Normalization ignores leading/trailing whitespace, nonbreaking spaces, and
  straight versus curly apostrophes.
- A qualifying direct sheet or a supported view placed on a sheet whose
  **Appears In Sheet List** parameter is enabled.
- Supported view types: Engineering Plan, Floor Plan, Ceiling Plan, Section,
  Elevation, Legend, Drafting View, Detail, Schedule, and Drawing Sheet.

## Outputs and effects

The command changes individual TextNote visibility with `HideElements` or
`UnhideElements` inside one Revit transaction. It changes graphics only; it
does not edit or delete note text, note types, sheets, or views.

The command is best-effort: it changes every valid target it can process and
reports four result classes in its pyRevit output report: changed, already in the requested
state, skipped because not hideable, and failed because a state or write check
raised an error. A failure can therefore leave other valid targets changed.
Shift-click diagnostics identify exclusions and the first reported failures.

## Limits and compatibility

- Text notes in unsupported view types, templates, views not placed on eligible
  sheets, and sheets excluded from the Sheet List are not changed.
- A primary view qualifies when it is placed on an eligible sheet or when a
  dependent view is placed there. Placed dependents are explicitly evaluated.
- The command uses permanent element visibility; users can reverse successful
  changes by choosing the opposite action or by using Revit Undo.
- Revit 2024 and later is the repository design target. This command has no
  recorded exact-version live acceptance claim.

## Validation evidence

| Date | Extension release | Revit version | Scenario | Result | Evidence link or location |
| --- | --- | --- | --- | --- | --- |
| 2026-10-02 | Unreleased | Not run | Static source and bundle review | Pass pending live acceptance | Current change review |

Live Revit acceptance remains required for hide/unhide, Cancel, no matching
notes, already-hidden notes, unhideable notes, state/write failures, each
supported view type, direct sheets, placed primary/dependent views, undo, and
ribbon presentation.

## Release history

| Extension release | Date | Change summary |
| --- | --- | --- |
| `0.0.9-beta` | 2026-10-01 | Released the prior pushbutton implementation with dependent-view handling. |

## Backlog

- Extract deterministic selection and result-classification logic into `lib/`
  with host-independent tests.
- Refactor the command entry point into `main()` only as part of that focused
  structural change.
- Record live Revit acceptance for the broadened view-type support.
