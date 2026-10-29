# Implementation plan: strHUB Revit to RAM SS proof

Revision: 1. Date: 10.29.2026. Status: **Approved for task breakdown**.
Approval: the user stated, "i approve the plan create the tasks dpocument".
Capability: `strhub-revit-ramss-proof`.
Requirements: [approved SPEC.md](../SPEC.md).
Source evidence: [DISCOVERY.md](../DISCOVERY.md).
Qualification design: [compatibility.md](compatibility.md).

## Outcome and authority

Deliver the agreed eight-member steel-bay proof on installed Revit 2026
`26.5.0.55` and RAM SS `25.00.02.42`. Preserve physical axes and the chosen datum,
verify the saved/reopened model, and retain incomplete output with diagnostics.
Connectivity uses 1/8 inch; numeric readback comparison has its own measured,
reviewed bound. The spec owns these requirements; this plan owns their proposed
technical realization, sequence, risks, and approval decisions.

All paths below are relative to `strHUB.pulldown` unless stated otherwise.
There was no previous local plan or task list to replace. This document contains
slice design; [todo.md](todo.md) is the sole authority for task/checkpoint
completion. The index below links to its stable anchors without duplicating
completion checklists.

## Approved architecture

```text
Revit / pyRevit IronPython command
    -> Revit bridge: collect physical axes and build BHoM objects
    -> preflight and source preview
    -> versioned job folder: BHoM payload + run/source metadata
    -> owned x64 STA RAM worker
         -> create new owned RAM database at the explicit path
         -> BHoM RAM adapter pushes levels and bars
         -> reopen and independently query actual RAM contents
    -> reconciliation report and manual RAM review
```

The process boundary is the BHoM representation plus transfer metadata. Revit
objects never cross it. RAM-specific mapping is applied at the target boundary;
a future destination can consume the same engineering objects without adopting
RAM's story/layout types as a universal schema. No plugin registry, generalized
sync service, or second software adapter is needed for this proof.

| Component / proposed project | Target and responsibility | Boundary |
| --- | --- | --- |
| `Export to RAM SS.pushbutton` | IronPython 2.7; pyRevit context, selection, base-level choice, preflight preview, status/output links | Thin command; no duplicate geometry engine |
| `src/StrHub.Revit/StrHub.Revit.csproj` | `net10.0-windows`, x64; Revit 2026 extraction, selected BHoM Revit helpers, BHoM object construction | All Revit API access stays on the valid Revit API thread; no source transaction |
| `src/StrHub.Core/StrHub.Core.csproj` | `netstandard2.0`; numeric transforms, eligibility, intended-connection checks, path ownership, report reconciliation | No Revit or RAM COM dependencies; no replacement structural object model |
| `src/StrHub.RamWorker/StrHub.RamWorker.csproj` | `net48`, x64 executable with STA entry point; BHoM RAM adapter, database ownership, raw target inspection | Own process and COM lifetime; no Revit API references |
| `tests/StrHub.Core.Tests/StrHub.Core.Tests.csproj` | `net10.0`; host-independent behavioral tests | Does not claim to prove COM, Revit, or target connectivity |
| `scripts/` | Local dependency staging, isolated build/test entry points, worker qualification scenarios | Does not install global BHoM or modify reference checkouts |

These framework choices are the plan's recommendation, not runtime evidence.
The worker gives the inspected net472 RAM adapter a .NET Framework host and
keeps its COM/dependency lifetime outside Revit's .NET 10 process. This adds a
serialization and deployment boundary; that boundary must pass qualification.
Shared pure logic targets netstandard2.0 to serve both hosts. Microsoft's
[targeting guidance](https://learn.microsoft.com/en-us/dotnet/standard/library-guidance/cross-platform-targeting)
supports that compatibility choice but does not guarantee dependency behavior.
The COM registration inspected is apartment-threaded; use an STA entry point
and keep owned COM operations on that thread, following
[Microsoft's STA guidance](https://learn.microsoft.com/en-us/dotnet/api/system.stathreadattribute?view=netframework-4.8).

Use the worker route first. Do not build an in-process RAM implementation in
parallel. If qualification disproves this route, record the exact blocker and
review a narrow alternative rather than silently changing runtimes or forking.

## Dependency and loading strategy

Prefer official BHoM release binaries with matching schema/engine/adapter versions.
The local main checkouts describe a candidate 9.3-era set, while public RAM
develop differed during discovery. Resolve an actual coherent release and record
exact tags/commits, download URLs, assembly identities, SHA-256 hashes, transitive
packages, and notices in a local `dependency-lock.json` before using its binaries.
Do not label a guessed release number as a verified dependency set.

Required closure includes core oM/engines, Structure/Geometry/Spatial/Physical
types and helpers actually used, serialization and its packages, adapter modules,
RAM toolkit/interop/Localisation, and Revit 2026 helpers needed for conversion.
Core BHoM and Localisation were not among the inspected sibling source checkouts;
their absence is a provisioning gap, not evidence that they are optional.

Stage dependencies under `artifacts/dependencies/`, with separate host and worker
load sets from the same lock. Load only the closure needed by each process from
explicit local paths. Detect conflicting loaded assembly identities in Revit;
do not attempt to replace an assembly already resident in that session. Use a
fresh Revit session when changing pins. Qualify BHoM reflection/type discovery
and any dataset lookup against local paths; loading every installed toolkit or
calling default ProgramData discovery is not the intended setup.

The inspected `LoadAllAssemblies` accepts an explicit folder, and the serializer
offers `ToJson`/`FromJson`. Test these actual facilities before introducing
replacement infrastructure. Do not assume that custom paths for one loader
also redirect dataset, settings, or versioning lookups.

Do not run upstream solution builds with their deployment targets. If suitable
release binaries are unavailable, assess a source-build recipe against licenses,
references and post-build effects before executing it. A need to change runtime
behavior or install outside strHUB returns to a decision checkpoint.

## Geometry, mapping, and transfer contract

The bridge reads stored beam curves directly and constructs the accepted
point-located column axes. Use BHoM geometry/section/material/orientation helpers
where they preserve the contract; do not call the stock bar converter and trust
its analytical preference or axis adjustments. Build BHoM bars from the exact
accepted axes, preserving source identifiers. Each substituted helper or avoided
conversion gets a short reason in the reuse record.

Preflight validates all eight selections, source constraints, one-story placement,
steel classification, verified AISC catalogue mappings, and intended connections.
Only the approved Z datum translation and unit conversions are allowed. In
particular, an endpoint gap accepted by the connectivity check does not permit
the RAM adapter to relocate a beam or column. Block unsupported offsets or
story assignments instead of letting its snapping behavior repair them.

Use BHoM serialization for the engineering payload. A small strHUB envelope
records format version, run ID, dependency-lock identity, source document and
element identities, datum/inverse, intended connection pairs, mapping references,
and output paths. Source-axis measurements are evidence, not a second structural
schema. Reject unknown job versions, type loss, unmatched element identities,
or inconsistent units; do not deserialize silently into generic fallback objects.

The worker receives only a complete preflight-passed job, rechecks its ownership
and schema, and creates a new model inside its unique run directory. Use the
installed DataAccess API for the minimal explicit-path database bootstrap,
close it, verify it exists, then pass that owned existing path to `RAMAdapter`.
This avoids the inspected constructor's nonexistent-path fallback. The bootstrap
is a narrow native operation; model transfer remains with the BHoM adapter.
The API's behavior and side effects must pass qualification before this approach
is relied upon. Never pass a missing path to an active adapter as a shortcut.

Push the intended levels/bars through the pinned adapter and capture all BHoM
events, object IDs and exceptions. Its successful return is not final status.
Reopen the model in a separate read phase and inspect raw RAM story/member
coordinates, classifications and assigned catalogue sections. Keep raw units
in the evidence and normalize in the independent comparison logic. BHoM Pull
may be compared as supplemental evidence, but must not be the sole oracle for
the conversion being tested. Check the fixture's orientations and actual
connectivity in RAM's UI when API evidence is insufficient.

Each run stores its input, provenance, reports, raw readback and any model files
under `artifacts/runs/<unique-run-id>/`. Use `CANCELLED`, `BLOCKED`, `FAILED`,
and `VERIFIED` as defined by the spec. Before verification is complete, a saved
file is pending verification, never implicitly successful. A timeout, crash or
absent result means incomplete/failed, not verified. Retain existing failed
assets; do not rename or delete live RAM sidecars in an attempt to repair them.
Prevent overlapping exports and never terminate a user's RAM process.

## Dependency graph and approved slices

```text
A: pinned local dependencies + runtime/serialization proof
       |                         |
       v                         v
B: owned synthetic RAM proof    C: selected Revit bay -> dry-run package
       |                         |
       +------------+------------+
                    v
D: selected bay -> saved RAM -> independent verification
                    |
                    v
E: failure/repeat-run acceptance and evidence review
```

| Slice | Delivered, independently inspectable behavior | Prerequisites / evidence |
| --- | --- | --- |
| A — local runtime proof | Reproducible local dependency staging/build, minimal bridge loads in the actual Revit host, worker activates/releases DataAccess, typed BHoM payload survives both runtimes | Lock and load manifests; compatibility cases Q-01 through Q-04; no source-model writes |
| B — owned target proof | A known synthetic BHoM bay becomes a new owned RAM model, then saves/reopens with independently checked sections/coordinates | A; Q-05 through Q-07; demonstrates controlled bootstrap, actual section mapping and measured precision |
| C — physical source preview | The selected Revit bay yields BHoM objects plus a complete preflight report without creating RAM model files | A; Q-08; raw physical axes, datum, section mappings and intended connections can be reviewed |
| D — real one-way transfer | C's package passes through B's qualified target route and produces a reconciled saved/reopened model | B and C; reviewed numeric bound; Q-09; all eight members traceable |
| E — failure and repeat-run acceptance | Invalid inputs block safely; cancellation/partial failure remain explicit; a second run preserves prior files and releases owned resources | D; Q-10; final evidence against AC-001 through AC-011 |

Checkpoint A reviews runtime placement, dependency pins and local portability
before further adapter integration. Checkpoint B reviews B and C evidence,
including the proposed numeric readback bound, before a real transfer can earn
verified status. Checkpoint C reviews D's actual RAM model and discrepancies.
Checkpoint D reviews E and the full acceptance package. The detailed task phase
will place these human checkpoints after groups of roughly two or three focused
tasks; no slice above is intended as one oversized implementation task.

B and C can be reasoned about independently after A. All Revit API work is
serialized on its valid host thread; COM operations stay on the worker's STA
thread. Host tests and RAM model writes are sequential. No parallel agent work
is required by this plan.

## Task index

Task and checkpoint authority: [todo.md](todo.md). The additional preparatory
checkpoints below split the approved slices into focused review groups; they
do not change the architecture or acceptance requirements.

| Group | Dependency-ordered tasks | Human checkpoint |
| --- | --- | --- |
| A: local foundation | [1: dependencies](todo.md#task-1), [2: build harness](todo.md#task-2), [3: worker activation](todo.md#task-3) | [Local worker](todo.md#checkpoint-a-worker) |
| A: transfer boundary | [4: envelope/report contract](todo.md#task-4), [5: BHoM payload](todo.md#task-5), [6: Revit bridge](todo.md#task-6) | [Boundary readiness](todo.md#checkpoint-a-boundary) |
| A: actual host | [7: diagnostic command](todo.md#task-7), [8: host/worker round trip](todo.md#task-8) | [A: runtime qualification](todo.md#checkpoint-a) |
| B: owned RAM creation | [9: bootstrap](todo.md#task-9), [10: section mappings](todo.md#task-10), [11: synthetic push](todo.md#task-11) | [Owned target](todo.md#checkpoint-b-target) |
| B/C: independent observations | [12: native readback](todo.md#task-12), [13: precision study](todo.md#task-13), [14: physical axes](todo.md#task-14) | [Readback and numeric-bound review](todo.md#checkpoint-b-readback) |
| C: complete source preview | [15: preflight](todo.md#task-15), [16: dry-run package](todo.md#task-16) | [B: target/source readiness](todo.md#checkpoint-b) |
| D: complete transfer | [17: worker job execution](todo.md#task-17), [18: command orchestration](todo.md#task-18), [19: real-bay verification](todo.md#task-19) | [C: transfer acceptance](todo.md#checkpoint-c) |
| E: failure/repeat acceptance | [20: invalid inputs](todo.md#task-20), [21: lifecycle failures](todo.md#task-21), [22: final evidence](todo.md#task-22) | [D: final qualification](todo.md#checkpoint-d) |

## Planned files and commands

The files/projects/scripts below do not exist yet. They are proposed deliverables
for the later task phase; the command contracts must be implemented and checked
there. This planning turn does not run a build, probe or export.

Author source, local build configuration, dependency lock, bundle metadata and
tests only under this work area. Put generated dependencies, fixtures, build
intermediates, caches and results under `artifacts/`; a local ignore file should
exclude generated contents while keeping a small curated evidence manifest.
Build wrappers set process-local `DOTNET_CLI_HOME`, `NUGET_PACKAGES`, and
`NUGET_HTTP_CACHE_PATH` below `artifacts/` and specify local build/intermediate
paths. Do not change machine or user environment configuration. Stop if a
dependency requires deployment outside the approved area.

From `strHUB.pulldown`, the planned development commands are:

```powershell
powershell.exe -NoProfile -File .\scripts\prepare-dependencies.ps1 -LockFile .\dependency-lock.json
powershell.exe -NoProfile -File .\scripts\build.ps1 -Configuration Release -RevitApiPath 'C:\Program Files\Autodesk\Revit 2026'
powershell.exe -NoProfile -File .\scripts\test.ps1 -Configuration Release
powershell.exe -NoProfile -File .\scripts\qualify.ps1 -Scenario WorkerRuntime -RunId worker-runtime-001
powershell.exe -NoProfile -File .\scripts\qualify.ps1 -Scenario SyntheticBay -RunId synthetic-bay-001
```

`prepare-dependencies.ps1` must verify locked downloads/hashes/notices and stage
only local paths. It must fail if the lock is incomplete. `build.ps1` restores
and builds the explicit projects in the architecture table for Release/x64,
with the bridge referencing the installed Revit API without redistributing it.
The worker remains net48; the core remains netstandard2.0; tests remain net10.0.
Output goes to `artifacts/build/` with deterministic project/framework separation.
Use supported [dotnet build output controls](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-build)
and local project properties, rather than upstream post-build deployment.
`test.ps1` runs the focused .NET tests with results below `artifacts/test-results/`;
only add Python tests for meaningful command-boundary behavior if needed.
`qualify.ps1` uses a new probe run directory, refuses run-ID collisions, and
does not open Revit documents or change a user's active model. Add further
scenario names only with defined evidence contracts.

Live host entry is the planned pyRevit command. During A/C it may report
diagnostics or preflight only; its metadata must accurately describe that stage.
It must not offer an unqualified export as verified. Revit extraction and final
RAM UI acceptance are host checks, not claims made by the CLI test wrapper.

From the extension root, after command metadata exists:

```powershell
python -B scripts/check_tool_metadata.py
git diff --check -- 'KL&A Tools_dev.tab/05 DevSandbox.panel/strHUB.pulldown'
```

The inspection environment currently resolves Git/CPython by absolute paths;
use those discovered executables or configure the invocation shell, without
assuming PATH has changed. Record the exact executed commands and versions in
qualification evidence.

## Risks, decisions, and recovery

| Risk | Impact | Planned response |
| --- | --- | --- |
| No coherent portable BHoM dependency closure | Blocks all integration | Qualify locked binaries and local path discovery first; do not hide gaps with a global installer |
| Revit helpers cannot load/use required APIs in the actual .NET 10 host | Blocks source helper reuse | Isolate the failing call; reuse compatible engines/types with explicit native extraction where possible; review any reduced reuse or upstream change |
| Serializer loses concrete types, references, or identity fragments | Invalid transfer boundary | Typed round-trip assertions in both processes; block on unresolved/downgraded types |
| RAM 25 behavior differs from old interop assumptions | Incorrect output or activation failure | Minimal worker and synthetic-bay experiments before product integration; retain raw native evidence |
| RAM constructor/bootstrap creates or cleans files outside the run | Violates output ownership | Explicit native bootstrap + verified existing path; before/after inspection; stop on any uncontrolled destination |
| Adapter reports success despite skipped objects, altered axes, or ignored section labels | False verified status | Reconcile independent native readback, BHoM events and manual RAM checks |
| 1/8 inch proximity is confused with numeric precision or native connectivity | False matches or hidden movement | Separate checks, reports and tests; no automatic merging; actual RAM connectivity evidence |
| Worker hangs, database remains locked, or another RAM session is active | Failed/incomplete run | Bounded wait and explicit failure state; release owned references; preserve evidence; no termination or manipulation of user sessions |
| Required fix demands a maintained fork | Extra maintenance and license obligations | Minimal reproducer and reuse/configuration alternatives; human decision before adoption; no automatic fork |

Rollback for this prototype is to disable/remove its local command/dependency
outputs after owned resources close. No Revit source transaction is required,
and no existing RAM model is updated. Retained failed output is intentionally
not rollback. Cleanup of owned development assets is a separate explicit action.

## Approval and handoff

Spec: approved by the user's statement, "I approve the spec. Create the plan
documents." Plan revision 1 and its compatibility design: approved by the
user's statement, "i approve the plan create the tasks dpocument".
Detailed task breakdown revision 1: [todo.md](todo.md), pending task approval.
Implementation: not started.

The architecture, slice order and checkpoints are approved for task breakdown.
The task breakdown must receive its own approval before code, dependency
installation, COM activation or model-write experiments. Preserve all human
checkpoints when handing work to a later session.
