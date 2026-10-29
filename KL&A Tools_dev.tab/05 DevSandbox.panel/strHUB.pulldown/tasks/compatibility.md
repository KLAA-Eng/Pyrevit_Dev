# strHUB compatibility and fidelity qualification design

Revision: 1. Date: 10.29.2026. Status: **Approved with plan revision 1**.
Parent design and approval authority: [plan.md](plan.md).
Requirements: [SPEC.md](../SPEC.md).
Observed baseline and pinned source evidence: [DISCOVERY.md](../DISCOVERY.md).

This document defines experiments and evidence, not completed results or a
second task checklist. No runtime probe, dependency restore or model export
has run. [todo.md](todo.md) owns detailed task/checkpoint completion; its
separate approval is still required before implementation.

## Qualification boundary

Target the installed Revit 2026 `26.5.0.55` / .NET 10 / pyRevit IronPython
attachment and RAM SS `25.00.02.42`. Record actual versions again at test time.
Treat an update or dependency-pin change as a changed baseline and rerun the
affected cases. Support for other Revit/RAM versions is not inferred.

The approved runtime design is a net10.0-windows Revit bridge and a
net48/x64/STA RAM worker, sharing pure netstandard2.0 logic and the same pinned
BHoM engineering representation. A failed case supplies evidence for a design
decision; it does not authorize an automatic runtime switch, global install,
geometry repair, or fork.

## Experiment matrix

| ID | Question / controlled experiment | Required evidence and pass condition | Stop or decision on failure |
| --- | --- | --- | --- |
| Q-01 | Can a coherent BHoM set run from local staged dependencies? | Complete lock with origins/hashes/notices, resolved transitive references and local discovery paths; no required global BHoM install or deployment side effects | Resolve missing closure or review the deployment constraint; do not mix releases |
| Q-02 | Can the bridge use BHoM in the actual Revit host? | Loaded paths/identities; construct required BHoM geometry/structure objects and exercise selected Revit helper calls on the API thread; no Revit transaction | Identify the first failing dependency/API/helper; assess native geometry extraction plus remaining BHoM reuse |
| Q-03 | Can the worker activate and release RAM 25 DataAccess? | x64/STA process evidence; exact registered coclass/server identity, successful minimal activation/query/release, no database creation in this activation-only case | Capture exception/HRESULT and actual interop identity; distinguish licensing, registration, runtime and API failure |
| Q-04 | Do typed BHoM objects survive host/worker serialization? | Lines, nodes, bars, section/material types, identifiers/fragments and datum metadata retain expected concrete types, values and references; no generic fallback accepted | Fix registration/load/serialization use; no parallel strHUB engineering schema as a workaround |
| Q-05 | Can a new model be created at exactly the owned path? | Native explicit-path bootstrap creates the intended file; adapter receives the verified existing file; save/close/reopen succeeds; only owned model/sidecars are touched | Stop before using active adapter with a nonexistent path; investigate bootstrap or source API contract |
| Q-06 | Can BHoM push the agreed standard sections and story frame? | Known synthetic bay: four columns/four beams, intended story, actual assigned catalogue sections, captured material/defaults and fixture orientations; successful save/reopen | Treat stubs, warnings, skipped objects and label changes as failures; determine mapping correction versus adapter defect |
| Q-07 | What numeric differences actually arise? | Independent raw readback, expected coordinates, normalized differences, unit trace and repeated results; proposed bound reviewed before verified status | Reject systematic scale/datum/snapping errors; never increase a bound to hide them |
| Q-08 | Does extraction obey the physical-line rule? | Selected real fixture with deliberately different analytical geometry and end adjustments; reported beam/column axes match the accepted physical rule; correct nonzero datum; complete preflight with no RAM model writes | Correct extraction/composition; do not alter associations or call a misleading fallback |
| Q-09 | Does a real selected bay survive the whole path? | Source IDs through target IDs; four columns/four beams; reopened coordinates within reviewed numeric bound; actual section/orientation/story and intended connectivity checked | Mark the run failed/incomplete with exact discrepancies; no partial verified result |
| Q-10 | Are failures, retries and ownership honest? | Bad selection/mapping/geometry blocks before model creation; cancellation and failures retain appropriate diagnostics/files; repeat run preserves prior output; owned resources release | Fix lifecycle or status/report handling before final acceptance; leave user sessions/files untouched |

Q-02 and Q-03 test different hosts. A pass in one does not qualify the other.
Q-04 is essential to the worker route. Q-06 is not satisfied by BHoM Push
returning objects; it needs actual target assignments. Q-09 cannot be satisfied
until Q-07's numeric-bound review and actual RAM connectivity checks are complete.

## Test fixtures

Use two clearly distinguished fixture sources:

- **Synthetic BHoM fixture:** known points and bars with explicit SI values,
  one positive story elevation above the base datum, known supported AISC
  catalogue mappings, recorded steel/default assumptions, and known orientation.
  It isolates RAM/bootstrap/serialization behavior from Revit extraction.
- **Revit fixture:** an engineer-reviewed one-story rectangular bay with four
  physical vertical columns and four physical straight horizontal beams. Record
  the actual family/type names, levels/offsets, raw line endpoints, column
  insertion/constraint data, rotations, intended joints, and section mappings.
  Prepare analytical geometry and end adjustments that differ from the physical
  location-line rule so the test detects the wrong source.

Store the fixture source/evidence under `artifacts/fixtures/`. Do not invent
family/catalogue mappings in the plan or edit a user's source project to create
a convenient test. Select a suitable fixture before host acceptance. Any later
fixture authoring automation must preserve the approved source-model boundary.

Include simple zero and nonzero X/Y values, a nonzero source base elevation,
reversed beam endpoints, and asymmetric coordinates that expose axis swaps and
feet/metres/inches mistakes. Compare against independently recorded source
measurements. Changing a fixture for a precision study must be recorded rather
than quietly replacing a failing case.

## Numeric precision and connectivity

Record the complete conversion chain: native Revit length values to SI BHoM
values to RAM native values and independently normalized readback. For each
point, retain source, intended target, actual target, signed coordinate deltas,
Euclidean endpoint difference and relevant story-elevation difference. Compare
the expected axis as a directed member for orientation; only normalize reversed
endpoints where that does not conceal an orientation or identity mismatch.

Repeat controlled write/save/reopen/readback runs to distinguish consistent
quantization from intermittent errors. An origin-only test is insufficient:
use multiple distinguishable coordinate values. If an API reports a documented
precision, capture the exact version's supporting documentation as well as
measurements. Separate datum/scale mistakes and deliberate adapter snapping
from numerical residuals. Report maximum errors without filtering failed members.

Propose a small justified absolute numeric bound in explicit units, document its
scope and evidence, and obtain the spec's review before `VERIFIED` is possible.
The earlier 1 mm suggestion is not a default. The **1/8 inch / 3.175 mm**
connectivity tolerance must never supply this numeric bound.

For connectivity, explicitly list the intended beam-end/column-top pairs. Use
inclusive 3D endpoint distance <= 0.003175 m after normalization. Test just
below, exactly at and just above that boundary, as well as missing/ambiguous
partners and nearby unrelated objects. This check moves no geometry and does
not create shared nodes. Confirm the intended connections actually exist in
RAM using an appropriate native query or manual UI evidence; if not queryable,
record that limitation and the manual method. Do not claim that a proximity
test establishes native support/connectivity.

## Evidence package and states

Each experiment gets a unique owned directory under `artifacts/probes/`;
each end-to-end export gets one under `artifacts/runs/`. Never reuse an existing
run ID. Suggested package contents are:

```text
manifest.json       Run/case identity, baseline, lock hash, commands and stage
input.json          Versioned job envelope and BHoM payload references
source.json         Independently captured source measurements and identities
events.json         BHoM/native errors, warnings and relevant operation results
readback.json       Actual native target data, including original units and IDs
report.json         Per-member outcomes, comparisons and final state
report.html         Human-readable diagnostics and discrepancy tables
model.rss           When a model was actually created; retain related owned files
```

Exact filenames may be finalized with tasks, but the evidence meanings must
remain distinct. Do not manufacture missing outputs just to fill the package.
Reports must say when readback did not occur, a file could not be reopened,
mapping/orientation was unverified, or manual connectivity review is pending.
An interrupted run without a final result remains incomplete and cannot be
promoted to verified based solely on an existing RSS file.

Before target writes, `BLOCKED` means no RAM model was created for that attempt.
After target writes, creation/save/readback failure means `FAILED`; preserve the
existing owned files and diagnostics, without claiming atomic rollback or
recoverability. Cancellation before writes is `CANCELLED`. Save completion is
an intermediate state, not `VERIFIED`. Final verification requires all applicable
criteria, the reviewed numeric bound, and the agreed manual RAM checks.

Do not leak test files into the adapter's default ProgramData destination.
Observe the relevant default path before and after controlled experiments to
detect unexpected creation, but never clean up an unrelated pre-existing model
or sidecar to make the test pass. Report any out-of-scope side effect and stop.

## Reuse, wrapper, or fork decision

Record the actual BHoM entry points exercised, dependencies loaded, and operations
performed natively. Known narrow glue candidates are physical-axis extraction,
explicit new-file bootstrap, validated section-name mapping, status reconciliation,
and independent native readback. They do not require duplicating the BHoM schema.

If a required case fails, capture the smallest reproducer and its actual baseline.
First test whether supported parameters, a different coherent released dependency
set, or wrapper composition solves it within the spec. Avoid patching private
adapter internals by reflection. If a source change is required, propose the
minimal patch with upstream base, license/notices, test, maintenance ownership
and contribution path. Human approval precedes adoption of a maintained fork.
An unsuccessful qualification is a useful finding, not a reason to claim success
or widen scope silently.

## Acceptance mapping

| Spec criterion | Primary evidence cases |
| --- | --- |
| AC-001 runtime compatibility | Q-01, Q-02, Q-03, Q-04 |
| AC-002 complete source preflight | Q-08, Q-10 |
| AC-003 physical geometry/source preservation | Q-08, Q-09 |
| AC-004 datum and units | Q-04, Q-07, Q-08, Q-09 |
| AC-005 blocked unsupported inputs | Q-08, Q-10 |
| AC-006 actual target members/sections/stories | Q-05, Q-06, Q-09 |
| AC-007 independent saved/reopened verification | Q-06, Q-07, Q-09 |
| AC-008 fresh owned files and repeat runs | Q-05, Q-10 |
| AC-009 honest failures and resource lifetime | Q-03, Q-05, Q-10 |
| AC-010 human evidence/reuse review | Review Q-01 through Q-10 and any fork proposal |
| AC-011 proximity plus actual connectivity | Q-08, Q-09, Q-10 plus boundary tests |

The task authority records pass/fail evidence links and checkpoint
approvals. This design document does not record execution as complete.
