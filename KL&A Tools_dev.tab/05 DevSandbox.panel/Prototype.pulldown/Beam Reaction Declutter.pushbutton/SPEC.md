# Beam Reaction Declutter

| Field | Value |
| --- | --- |
| Tool ID | `devsandbox.beam-reaction-declutter` |
| Tool version | `v0.1` |
| Status | Unreleased |
| Status/origin | Prototype; KL&A custom tool. |
| Main delivery | 0.0.7 |
| Path aliases | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Beam Reaction Declutter.pushbutton`; `KL&A Tools.tab/05 DevSandbox.panel/Prototype.pulldown/Beam Reaction Declutter.pushbutton` |
| Version inputs | `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Beam Reaction Declutter.pushbutton/bundle.yaml`; `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Beam Reaction Declutter.pushbutton/script.py`; `lib/beam_reaction_declutter/` |

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| v0.0 | 0.0.7 | 09.28.2026 | First main delivery of Move/Reset reaction-tag decluttering. | 2c4a3b2 |
| v0.1 | Unreleased | 10.08.2026 | Planned same-beam decluttering, bounded moves, rollback safety, and failure-only reporting. | Pending next main delivery. |

Versions reconstruct meaningful main-release deliveries. Intermediate dev work
is grouped into its delivered snapshot; meaningful changes absent from current
main are planned and explicitly Unreleased. Dates use MM.DD.YYYY.

## Purpose

`Beam Reaction Declutter` is a Revit 2024+ DevSandbox pyRevit prototype based
on `Beam Rxn Declutter_RVT 25_v0.0.0.02.dyn`. It moves overlapping reaction
tags along their tagged structural-framing beams in selected plan views. The
current planned update adds same-beam tag handling and safer failure behavior;
live acceptance remains pending.

## Inputs and scope

- The user chooses **Move** or **Clear Matching Red Overrides**, then selects one or more non-template
  plan views.
- Candidate tags are `OST_StructuralFramingTags` whose type family name
  contains `Reaction` (case-insensitive).
- Move accepts candidate tags with exactly one local, straight structural-framing
  beam reference and no visible leader. Pinned tags and unsupported references
  remain unchanged when they overlap another element.
- Each candidate is checked against every visible non-type element in its view.
  Its own beam and the tag itself are excluded. Other tags on the same beam,
  including non-Reaction tags, are blockers.

## Move behavior

The tool projects movement onto the tagged beam axis in the selected plan view.
For ordinary blockers it moves toward the beam midpoint. For same-beam tag
conflicts it keeps the tag nearer the midpoint stationary and searches both
directions for the shortest clear move of the end tag. A pinned tag stays fixed;
equal-distance reaction tags use ElementId as a stable tie-breaker, and an
equal-length movement search favors the outer beam end. Non-Reaction tags stay
fixed. For different-beam tag conflicts, the more vertical beam still takes
priority, measured relative to the view.

Movement uses 0.2 ft increments with a total cap of eight steps (1.6 ft) per tag
per run. The selected final position must clear every visible blocker; moving
past a beam endpoint is allowed within the cap. An unresolved move or failed
marker application rolls back that tag's subtransaction, leaving its position
and overrides unchanged. A fatal regeneration, rollback, or transaction failure
aborts the selected-view run. Successful moves receive a fresh per-view
projection-line override in RGB `(254, 0, 0)`. That replacement intentionally
discards any prior element override, matching the Dynamo source behavior.

## Clear Matching Red Overrides behavior

Clear Matching Red Overrides clears the entire element override in selected
views for eligible reaction tags whose projection-line color is exactly RGB
`(254, 0, 0)`. It does not restore tag positions and can clear a manually
applied matching red override.

## Output and limits

The pyRevit output window opens only when a tag remains overlapped, cannot be
evaluated, or a matching red override cannot be cleared. It lists the affected
view, tag ElementId, and reason. Successful moves and clears have no detailed
report. Safe skips and the eight-step cap are expected outcomes when the tag
stays unchanged and the report is accurate.

The command changes the active model in one transaction per selected action. It
does not write files, persist settings, or reproduce the Dynamo shared-drive
usage logger. Live acceptance remains required in Revit 2024, 2025, and 2026
using the controlled cases and a representative project recorded in
`docs/reviews/2026-10-08/beam-reaction-declutter-promotion.md`. The prototype
stays in DevSandbox until the owner's review and the pre-move gate pass.
