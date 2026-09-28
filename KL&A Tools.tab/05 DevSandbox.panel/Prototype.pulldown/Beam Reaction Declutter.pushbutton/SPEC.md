# Beam Reaction Declutter

## Purpose

`Beam Reaction Declutter` is a Revit 2024+ DevSandbox pyRevit prototype based
on `Beam Rxn Declutter_RVT 25_v0.0.0.02.dyn`. It moves overlapping reaction
tags along their tagged structural-framing beams in selected plan views.

## Inputs and scope

- The user chooses **Move** or **Reset**, then selects one or more non-template
  plan views.
- Candidate tags are `OST_StructuralFramingTags` whose type family name
  contains `Reaction` (case-insensitive).
- Each candidate is checked against every visible non-type element in its view.
  The tag itself and tags attached to the same beam are excluded.

## Move behavior

The tool projects movement onto the tagged beam axis toward its midpoint. It
uses 0.2 ft steps and a maximum of eight steps for each blocking element. When
two beam-related tags overlap, the tag on the more vertical beam takes priority.

If a tag cannot clear every collision within the cap, all movement made by this
run for that tag is reversed and the tag is reported as unresolved. Successful
moves receive a fresh per-view projection-line override in RGB `(254, 0, 0)`.
That replacement intentionally discards any prior element override, matching
the Dynamo source behavior.

## Reset behavior

Reset clears the entire element override in selected views for eligible reaction
tags whose projection-line color is exactly RGB `(254, 0, 0)`. Reset does not
restore tag positions and can clear a manually applied matching red override.

## Output and limits

The pyRevit output window reports counts and element IDs for candidates, moved
tags, reset tags, unresolved/restored tags, and skipped tags in each view.

The command changes the active model in one transaction per selected action. It
does not write files, persist settings, or reproduce the Dynamo shared-drive
usage logger. Live acceptance remains required in Revit 2024 and 2025+ with
representative reaction-tag families, leaders, pinned tags, and overlapping
model/annotation content.
