# strHUB qualification tasks

Revision: 1. Date: 10.29.2026. Status: **Draft for task approval**.
Capability: `strhub-revit-ramss-proof`.
Requirements: [approved spec](../SPEC.md).
Design: [approved plan revision 1](plan.md).
Evidence cases: [compatibility design](compatibility.md).

This is the sole task/checkpoint completion authority. All tasks are initially
unchecked; implementation, dependency staging and live probes have not started.
Plan approval authorizes this breakdown, not execution. Task approval is required
before Task 1. At every checkpoint below, present evidence and wait for human
approval before beginning the next group. Do not repeat an already recorded
approval unless the baseline or relevant design changes.

## Execution conventions

All file paths and command working directories below are relative to
`strHUB.pulldown`. Every authored file stays here. Listed files are expected
deliverables, not authorization to modify unrelated files. Routine progress
updates belong here; generated binaries/packages/logs/run outputs belong under
`artifacts/` and are not counted as authored source files. Split any task whose
implementation grows beyond roughly five authored files or a focused session.

Prefer meaningful test-first cases for deterministic behavior; use actual host
evidence for Revit/COM behavior. Do not add tests that merely repeat a trivial
implementation. Tests, builds and probes may expose a real prerequisite failure:
record the evidence and stop dependent work rather than marking a task complete
or silently changing runtimes, dependencies, geometry policy or fork scope.

After each task, record its actual verification command/results, evidence paths,
changed files and unresolved limitations below that task. Completion is not a
runtime compatibility claim unless the relevant live evidence exists. No source
Revit model writes or existing RAM model updates are part of these tasks.

The verification labels below refer to these full command contracts, not shell
aliases. Scripts/projects are created by the prerequisite tasks and must not be
claimed executable before then. Resolve Git/CPython by their discovered installed
paths if PATH is unavailable; do not change the user's global environment.

| Label | Command / host action |
| --- | --- |
| DEPS | `powershell.exe -NoProfile -File .\scripts\prepare-dependencies.ps1 -LockFile .\dependency-lock.json` |
| BUILD | `powershell.exe -NoProfile -File .\scripts\build.ps1 -Configuration Release -RevitApiPath 'C:\Program Files\Autodesk\Revit 2026'` |
| TEST | `powershell.exe -NoProfile -File .\scripts\test.ps1 -Configuration Release` |
| WORKER | `powershell.exe -NoProfile -File .\scripts\qualify.ps1 -Scenario WorkerRuntime -RunId ('worker-' + [guid]::NewGuid().ToString('N'))` |
| SYNTHETIC | `powershell.exe -NoProfile -File .\scripts\qualify.ps1 -Scenario SyntheticBay -RunId ('synthetic-' + [guid]::NewGuid().ToString('N'))` |
| FAILURES | `powershell.exe -NoProfile -File .\scripts\qualify.ps1 -Scenario Failures -RunId ('failures-' + [guid]::NewGuid().ToString('N'))` |
| METADATA | From the extension root: `python -B scripts/check_tool_metadata.py` |
| DIFF | From the extension root: `git diff --check -- 'KL&A Tools_dev.tab/05 DevSandbox.panel/strHUB.pulldown'` |
| HOST | In the actual Revit 2026 host, run the stage supported by DevSandbox > strHUB > Export to RAM SS; retain host/runtime/loaded-path evidence |

## A: local foundation

<a id="task-1"></a>

### Task 1: Lock and stage BHoM dependencies

Dependencies: task approval. Scope: Medium, 3 authored files.
Coverage: Q-01; AC-001, AC-010.

- [ ] Resolve one coherent release set with actual origins, versions, hashes,
  required transitive packages and license/notices; include the required core,
  Localisation, RAM and Revit helper dependencies rather than guessing from
  sibling checkouts.
- [ ] DEPS stages only local host/worker load sets and checks the lock; incomplete
  pins, missing references and hash mismatches fail explicitly. Do not execute
  an upstream installer/build or modify a reference checkout.
- [ ] Generated assets are locally ignored; local path/dataset/discovery gaps
  are reported instead of being hidden by a global BHoM install.

Verification: run DEPS; deliberately test an invalid hash in a disposable copy of
the lock and confirm rejection. Retain the closure/load-set inventory for Q-01.

Files: `dependency-lock.json`, `scripts/prepare-dependencies.ps1`, `.gitignore`.

<a id="task-2"></a>

### Task 2: Establish the isolated build and test harness

Dependencies: Task 1. Scope: Medium, 5 authored files.
Coverage: Q-01; AC-001.

- [ ] Build the pure core as netstandard2.0 and define the net10.0 test project;
  pin its test packages and use the locked local dependencies where applicable.
- [ ] BUILD restores/builds only the implemented approved projects with Release
  configuration, local output/intermediate paths and process-local SDK/NuGet
  caches. Missing required dependencies are failures, not warning suppression.
- [ ] TEST has a reproducible invocation and local results directory. An empty
  scaffold is recorded as having no behavioral tests, never as proof of behavior.

Verification: run BUILD and inspect output/cache paths and framework identities;
inspect TEST's invocation/result handling without inventing passing test evidence.

Files: `Directory.Build.props`, `scripts/build.ps1`, `scripts/test.ps1`,
`src/StrHub.Core/StrHub.Core.csproj`,
`tests/StrHub.Core.Tests/StrHub.Core.Tests.csproj`.

<a id="task-3"></a>

### Task 3: Probe the RAM worker runtime

Dependencies: Tasks 1-2. Scope: Medium, 4 authored files.
Coverage: Q-03; AC-001, AC-009.

- [ ] A net48/x64 worker with an STA entry point reports runtime, actual COM
  registration/server and locked interop identities without Revit references.
- [ ] WorkerRuntime activates, queries and releases DataAccess without creating
  a database or touching user sessions; capture native exception/HRESULT details.
- [ ] Qualification runs use unique owned directories and return explicit
  success/failure evidence; run-ID collisions fail rather than reuse output.

Verification: BUILD, then WORKER in the actual installed RAM 25 environment;
confirm activation-only operation, ownership and release evidence for Q-03.

Files: `src/StrHub.RamWorker/StrHub.RamWorker.csproj`,
`src/StrHub.RamWorker/Program.cs`, `src/StrHub.RamWorker/RamRuntimeProbe.cs`,
`scripts/qualify.ps1`.

<a id="checkpoint-a-worker"></a>

### Preparatory checkpoint: local worker

- [ ] Review Tasks 1-3, dependency closure, output locality and actual worker
  activation/release evidence; do not infer Revit compatibility from this pass.
- [ ] Human approval recorded here before Task 4. If a global install, fork or
  different runtime is required, obtain a decision before dependent work.

Approval/evidence: pending.

## A: transfer boundary

<a id="task-4"></a>

### Task 4: Define the transfer envelope and reporting contract

Dependencies: Tasks 1-3 and local-worker checkpoint. Scope: Medium, 4 authored files.
Coverage: Q-04, Q-10; AC-004, AC-008, AC-009.

- [ ] Versioned envelope records run/lock/source identities, datum and inverse,
  intended connection pairs, mapping references and owned paths. Engineering
  objects remain BHoM payloads, not a duplicate strHUB structural schema.
- [ ] Define structured per-element outcomes and run states; unknown job versions,
  missing identities and absent/partial final results cannot become verified.
- [ ] JSON and human-readable reports share the same underlying result data and
  distinguish no readback, partial output and pending manual verification.

Verification: TEST with valid/malformed envelopes, incomplete/failed outcomes and
report reconciliation cases; BUILD for both consumer framework boundaries.

Files: `src/StrHub.Core/TransferEnvelope.cs`, `src/StrHub.Core/ReportWriter.cs`,
`tests/StrHub.Core.Tests/EnvelopeTests.cs`,
`tests/StrHub.Core.Tests/ReportTests.cs`.

<a id="task-5"></a>

### Task 5: Qualify typed BHoM payload serialization

Dependencies: Task 4. Scope: Medium, 5 authored files.
Coverage: Q-04; AC-001, AC-004.

- [ ] Use BHoM's serializer on representative nodes/bars, sections/materials,
  identifiers/fragments and known coordinates; preserve concrete types, values
  and required references in the worker.
- [ ] Unresolved types, generic fallback objects, identity loss and inconsistent
  dependency identities are explicit failures, not repaired silently.
- [ ] Capture a net10 test-host to net48-worker round trip; label it as a
  test-host result, pending actual Revit-host verification in Task 8.

Verification: BUILD, TEST, and the worker payload probe through the qualification
harness; retain the typed before/after comparison for Q-04.

Files: `src/StrHub.Core/BHoMPayload.cs`, `src/StrHub.Core/StrHub.Core.csproj`,
`src/StrHub.RamWorker/Program.cs`,
`tests/StrHub.Core.Tests/BHoMPayloadTests.cs`, `scripts/qualify.ps1`.

<a id="task-6"></a>

### Task 6: Build the Revit bridge

Dependencies: Tasks 2, 4-5. Scope: Small, 2 authored files.
Coverage: Q-02; AC-001, AC-003.

- [ ] Compile a net10.0-windows/x64 bridge against the installed Revit 2026 API
  and locked BHoM host load set; do not redistribute Revit API binaries.
- [ ] Expose a runtime/helper diagnostic entry point which records actual loaded
  paths/identities and does not open a transaction or invoke RAM model writes.
- [ ] Report assembly collisions and incompatible helper calls clearly; do not
  replace assemblies already resident in Revit or silently change pins.

Verification: BUILD and inspect references/output. Actual host loading remains
pending Task 7; a successful compile is not a Q-02 pass.

Files: `src/StrHub.Revit/StrHub.Revit.csproj`, `src/StrHub.Revit/RevitBridge.cs`.

<a id="checkpoint-a-boundary"></a>

### Preparatory checkpoint: boundary readiness

- [ ] Review Tasks 4-6, typed round-trip evidence and framework/load boundaries.
- [ ] Human approval recorded here before installing/loading the local command
  in Task 7; retain explicit limits of the test-host evidence.

Approval/evidence: pending.

## A: actual Revit host

<a id="task-7"></a>

### Task 7: Add the pyRevit diagnostic entry point

Dependencies: Tasks 4-6 and boundary-readiness checkpoint. Scope: Medium, 5 authored files.
Coverage: Q-02; AC-001, AC-003.

- [ ] Create the local pulldown/command bundle with matching titles, v0.0,
  versioned tooltip, author and adjacent operational SPEC referencing the parent
  qualification spec; keep IronPython 2.7 compatibility.
- [ ] The thin command loads the bridge by verified local path and runs its
  current diagnostic stage on the valid Revit API thread, reporting unavailable
  later stages without pretending to export.
- [ ] Demonstrate BHoM object construction and the selected required Revit helper
  calls in the actual host, with no source transaction or RAM model creation.

Verification: METADATA, BUILD, then HOST in a fresh Revit 2026 session; retain
actual runtime/helper results and any incompatible-call details for Q-02.

Files: `bundle.yaml`, `Export to RAM SS.pushbutton/script.py`,
`Export to RAM SS.pushbutton/bundle.yaml`, `Export to RAM SS.pushbutton/SPEC.md`,
`src/StrHub.Revit/RevitBridge.cs`.

<a id="task-8"></a>

### Task 8: Prove the actual host-to-worker BHoM round trip

Dependencies: Tasks 3-7. Scope: Medium, up to 4 authored files.
Coverage: Q-02, Q-04; AC-001, AC-004.

- [ ] Emit a clearly labeled synthetic typed BHoM probe package from the actual
  Revit host and process it with the isolated worker using the same lock.
- [ ] Preserve required engineering types, coordinates, identity fragments and
  metadata through serialization in both real processes; no Revit objects cross.
- [ ] Capture both load manifests and comparison evidence; no database/model
  writes occur in this serialization-only case.

Verification: BUILD, HOST probe and worker round trip; review Q-02/Q-04 evidence,
including type-loss and mismatched-lock rejection results.

Files: `src/StrHub.Revit/SerializationProbe.cs`,
`src/StrHub.Revit/RevitBridge.cs`, `src/StrHub.RamWorker/Program.cs`,
`scripts/qualify.ps1`.

<a id="checkpoint-a"></a>

### Checkpoint A: runtime qualification

- [ ] Q-01 through Q-04 have actual evidence for the approved local host/worker
  route; all required type/discovery and local-path limitations are resolved.
- [ ] Review pins, reuse exceptions and runtime failures; a required fork or
  deployment change returns to a human decision, not an implicit workaround.
- [ ] Human approval recorded here before Task 9 and target-write experiments.

Approval/evidence: pending.

## B: owned RAM creation

<a id="task-9"></a>

### Task 9: Bootstrap an explicitly owned RAM database

Dependencies: Tasks 3-4, 8 and Checkpoint A. Scope: Medium, 5 authored files.
Coverage: Q-05; AC-008, AC-009.

- [ ] Validate a unique owned run path and use minimal native DataAccess bootstrap
  to create/close the database at that exact path; verify the resulting file
  before any active BHoM adapter receives it.
- [ ] Reject collisions and unowned/missing adapter paths. Never invoke the
  adapter's default-path fallback or clean unrelated sidecars.
- [ ] Save/close/reopen the owned empty database and capture before/after path
  and release evidence; retain partial owned output on failure.

Verification: TEST for ownership/collision rules; BUILD and owned target probe
via the qualification harness. Inspect the relevant default path without changing
pre-existing files; Q-05 fails on uncontrolled output.

Files: `src/StrHub.Core/OwnedRun.cs`,
`tests/StrHub.Core.Tests/OutputOwnershipTests.cs`,
`src/StrHub.RamWorker/RamDatabase.cs`, `src/StrHub.RamWorker/Program.cs`,
`scripts/qualify.ps1`.

<a id="task-10"></a>

### Task 10: Verify the fixture's catalogue section mappings

Dependencies: Task 9. Scope: Medium, 5 authored files.
Coverage: Q-06; AC-002, AC-005, AC-006.

- [ ] Resolve actual AISC catalogue labels for the agreed fixture against RAM 25;
  record source/target labels, supporting size evidence and applicable steel
  defaults with the certified software/lock identity.
- [ ] Missing, ambiguous or substituted sections block rather than relying on
  the adapter's section/material creation stubs or default guesses.
- [ ] Provide pure mapping validation usable by preflight and the worker;
  catalogue inspection only touches an owned probe model when one is required.

Verification: TEST for valid/missing/ambiguous mappings, BUILD, and RAM catalogue
query/UI evidence for the actual fixture mapping values.

Files: `src/StrHub.Core/SectionMapping.cs`,
`tests/StrHub.Core.Tests/SectionMappingTests.cs`,
`src/StrHub.RamWorker/RamSectionCatalog.cs`,
`src/StrHub.RamWorker/Program.cs`, `fixtures/section-map.json`.

<a id="task-11"></a>

### Task 11: Push the synthetic bay through BHoM

Dependencies: Tasks 5, 9-10. Scope: Medium, 4 authored files.
Coverage: Q-05, Q-06; AC-006, AC-009.

- [ ] Construct the known synthetic BHoM bay in SI with four columns, four beams,
  a positive story above the base datum and the verified section mappings.
- [ ] Use the explicit owned bootstrap and BHoM RAM push path; capture events,
  returned object IDs, save/close outcomes and member-level errors.
- [ ] Successful Push/save remains pending independent verification. Partial
  output is retained as incomplete; no result is declared verified at this stage.

Verification: BUILD and SYNTHETIC; inspect the owned RAM output and captured
events/counts without treating them as sufficient saved-model fidelity evidence.

Files: `src/StrHub.RamWorker/SyntheticBay.cs`,
`src/StrHub.RamWorker/RamExport.cs`, `src/StrHub.RamWorker/Program.cs`,
`scripts/qualify.ps1`.

<a id="checkpoint-b-target"></a>

### Preparatory checkpoint: owned target

- [ ] Review Tasks 9-11, explicit-path behavior, fixture section mappings and
  synthetic push results; confirm no uncontrolled fallback/cleanup occurred.
- [ ] Human approval recorded here before independent readback work. Preserve
  failures as evidence rather than bypassing missing mappings or altered axes.

Approval/evidence: pending.

## B/C: independent target and source observations

<a id="task-12"></a>

### Task 12: Read the saved RAM model independently

Dependencies: Tasks 9-11 and owned-target checkpoint. Scope: Medium, 5 authored files.
Coverage: Q-06, Q-07; AC-006, AC-007.

- [ ] Reopen the actual saved model and query native story/member coordinates,
  classifications, IDs and assigned sections, retaining original units.
- [ ] Compare actual target records against independent expected records;
  detect missing/extra members, wrong levels/sections and meaningful direction
  or identity changes. BHoM Pull is not the sole verification oracle.
- [ ] Unreadable files or unavailable fields are explicit limitations/failures;
  include a manual RAM orientation/connectivity review path where needed.

Verification: BUILD, TEST with representative reconciliation mismatches, and
SYNTHETIC save/reopen/native readback; retain raw and normalized results.

Files: `src/StrHub.RamWorker/RamReadback.cs`,
`src/StrHub.RamWorker/Program.cs`, `src/StrHub.Core/Reconciliation.cs`,
`tests/StrHub.Core.Tests/ReconciliationTests.cs`, `scripts/qualify.ps1`.

<a id="task-13"></a>

### Task 13: Measure numeric precision and propose the readback bound

Dependencies: Task 12. Scope: Medium, 4 authored files.
Coverage: Q-07; AC-004, AC-007.

- [ ] Repeat controlled write/save/reopen comparisons with distinguishable
  nonzero/asymmetric coordinates, recording the unit chain and all signed and
  Euclidean residuals without filtering failed members.
- [ ] Separate numeric residuals from scale/datum mistakes, snapping and other
  systematic adapter alterations; propose a small justified bound in explicit
  units, not the unapproved 1 mm or the connectivity tolerance.
- [ ] Comparison code requires a reviewed bound before verified status; document
  the proposal and supporting evidence for the following human checkpoint.

Verification: BUILD, TEST with unit/threshold/error cases, and repeated
SYNTHETIC runs; retain the complete precision study and proposed bound.

Files: `src/StrHub.Core/NumericComparison.cs`,
`tests/StrHub.Core.Tests/NumericComparisonTests.cs`, `scripts/qualify.ps1`,
`artifacts/evidence/numeric-bound.md` (curated evidence).

<a id="task-14"></a>

### Task 14: Extract the accepted physical axes from Revit

Dependencies: Tasks 6-8 and Checkpoint A. Scope: Medium, 4 authored files.
Coverage: Q-08; AC-003, AC-004.

- [ ] Read stored beam location curves and derive vertical column axes from
  insertion X/Y and base/top levels plus offsets; do not use analytical curves,
  solid extents or end-extension adjustments.
- [ ] Apply only the chosen datum translation and explicit unit conversion,
  retain source measurements/identities, and document BHoM helpers reused or
  deliberately avoided. Invalid/missing constraints are reported.
- [ ] Demonstrate the rule on a reviewed Revit fixture whose analytical geometry
  and end adjustments differ; perform no source transaction or RAM writes.

Verification: BUILD, TEST for deterministic axis/datum/unit rules, and HOST
physical-axis preview; independently inspect actual fixture endpoints/constraints.

Files: `src/StrHub.Revit/PhysicalAxes.cs`, `src/StrHub.Revit/RevitBridge.cs`,
`src/StrHub.Core/GeometryRules.cs`,
`tests/StrHub.Core.Tests/GeometryRulesTests.cs`.

<a id="checkpoint-b-readback"></a>

### Preparatory checkpoint: readback and numeric-bound review

- [ ] Review Tasks 12-14: independent target records, numeric study and proof
  that physical-axis extraction ignores differing analytical/end-adjusted data.
- [ ] Human accepts or revises the proposed numeric readback bound and its scope;
  record the value, units and evidence reference here. This approval does not
  authorize geometry movement. If evidence is insufficient, remain pending.
- [ ] Human approval recorded here before Task 15. Carry this bound forward
  without asking again unless the relevant baseline or evidence changes.

Numeric bound / units / approval reference: pending.
Approval/evidence: pending.

## C: complete source preview

<a id="task-15"></a>

### Task 15: Validate the selected bay and intended connections

Dependencies: Tasks 4, 10, 14 and numeric-bound review checkpoint. Scope: Medium, 4 authored files.
Coverage: Q-08, Q-10; AC-002, AC-005, AC-011.

- [ ] Validate every selected object, exactly four eligible beams/four columns,
  one-story geometry, steel classification, constraints, verified section
  mappings and target representability; collect all detected blockers.
- [ ] Test explicitly intended connection pairs with inclusive 3D distance
  <= 0.003175 m; report missing/ambiguous/out-of-tolerance partners and do not
  infer connections from unrelated nearby objects or move/merge geometry.
- [ ] Block unsupported geometry/story offsets before target writes; maintain
  separate numeric readback and connectivity policies.

Verification: TEST with boundary distances just below/at/above 1/8 inch, reversed
endpoints, invalid constraints/mappings and unrelated nearby members; BUILD.

Files: `src/StrHub.Core/Preflight.cs`, `src/StrHub.Core/Connectivity.cs`,
`tests/StrHub.Core.Tests/PreflightTests.cs`,
`tests/StrHub.Core.Tests/ConnectivityTests.cs`.

<a id="task-16"></a>

### Task 16: Present and serialize the no-write source preview

Dependencies: Tasks 4-5, 7, 10, 14-15. Scope: Medium, 5 authored files.
Coverage: Q-08; AC-002, AC-003, AC-005.

- [ ] The command accepts the actual selection/base level and shows a complete
  per-element preflight report, source/transformed axes and mapping decisions.
- [ ] Construct BHoM bars from the accepted axes using compatible helpers and
  serialize a versioned package only when preflight passes; preserve identity
  and intended-connection metadata without a competing engineering schema.
- [ ] This stage creates no RAM model or active adapter; blocked/preview-only
  outcomes and current command capabilities are stated accurately in metadata.

Verification: BUILD, TEST, METADATA and HOST with valid and blocked selections;
inspect generated input/report data and confirm no RAM model was created.

Files: `Export to RAM SS.pushbutton/script.py`,
`Export to RAM SS.pushbutton/bundle.yaml`, `Export to RAM SS.pushbutton/SPEC.md`,
`src/StrHub.Revit/RevitBridge.cs`, `src/StrHub.Revit/TransferJob.cs`.

<a id="checkpoint-b"></a>

### Checkpoint B: target/source readiness

- [ ] B and C have evidence: controlled owned target creation, actual catalogue
  assignments, independent readback, reviewed numeric bound and physical-source
  preview with complete preflight reporting.
- [ ] Review any remaining reuse/adapter gaps and actual target-connectivity
  evidence method; no silent fork, snapping or missing-type workaround.
- [ ] Human approval recorded here before Task 17 and real source transfer.

Approval/evidence: pending.

## D: complete one-way transfer

<a id="task-17"></a>

### Task 17: Execute a validated transfer job in the worker

Dependencies: Tasks 4-5, 9-13, 15-16 and Checkpoint B. Scope: Medium, 5 authored files.
Coverage: Q-09; AC-005 through AC-009.

- [ ] Worker validates job version, lock/identity/units, mapping evidence and
  owned destination before model creation, using the shared pure rules.
- [ ] Execute the qualified bootstrap/push/save/reopen/readback route and return
  reconciled per-member results, native IDs and captured events; unverified
  manual fields or missing approvals prevent verified status.
- [ ] Reject malformed/colliding jobs before writes; retain actual partial output
  on later failure and never open an existing user model as an export target.

Verification: BUILD, TEST with malformed/partial jobs, and synthetic jobs through
the same execution entry point; inspect final/pending/failed result states.

Files: `src/StrHub.RamWorker/Program.cs`,
`src/StrHub.RamWorker/RamJobRunner.cs`, `src/StrHub.Core/JobValidation.cs`,
`tests/StrHub.Core.Tests/JobValidationTests.cs`, `scripts/qualify.ps1`.

<a id="task-18"></a>

### Task 18: Orchestrate the owned worker from the command

Dependencies: Tasks 16-17. Scope: Medium, 5 authored files.
Coverage: Q-09, Q-10; AC-008, AC-009.

- [ ] After successful preflight and user continuation, start the verified local
  worker executable with explicit arguments and owned paths, without shell
  interpolation or Revit objects crossing processes.
- [ ] Handle progress, bounded waiting, cancellation and missing/crashed-worker
  results honestly; prevent overlapping exports and leave user RAM sessions
  untouched. Do not run Revit API operations on the worker thread/process.
- [ ] Present saved/pending/failed/verified distinctions and artifact links;
  changing from preview to export is reflected in command metadata/SPEC.

Verification: BUILD, METADATA and HOST with a controlled job, cancellation and
missing-result scenario; inspect process/path identities and report states.

Files: `src/StrHub.Revit/WorkerClient.cs`, `src/StrHub.Revit/RevitBridge.cs`,
`Export to RAM SS.pushbutton/script.py`,
`Export to RAM SS.pushbutton/bundle.yaml`, `Export to RAM SS.pushbutton/SPEC.md`.

<a id="task-19"></a>

### Task 19: Verify the real selected bay in saved RAM output

Dependencies: Tasks 12-18. Scope: Medium, up to 3 authored evidence/document files.
Coverage: Q-09; AC-002, AC-003, AC-004, AC-006, AC-007, AC-011.

- [ ] Run the selected eight-member Revit fixture through the complete path and
  trace source document/UniqueIds to expected/actual target member records.
- [ ] Saved/reopened RAM output contains the intended four columns/four beams,
  story and exact mapped sections; coordinates satisfy the reviewed numeric
  bound and the 1/8 inch proximity checks without hidden movement.
- [ ] Inspect fixture orientations and actual intended RAM connections in the
  UI/query evidence. Keep status pending until required manual evidence and
  review exist; record discrepancies rather than accepting partial fidelity.

Verification: HOST end-to-end export, independent native readback and manual RAM
inspection. Retain the source/target comparisons and explicit manual observations.

Files: `artifacts/evidence/end-to-end.md`, `artifacts/evidence/manifest.json`,
`Export to RAM SS.pushbutton/SPEC.md`; generated run assets remain under artifacts.

<a id="checkpoint-c"></a>

### Checkpoint C: transfer acceptance

- [ ] Review Tasks 17-19 and the actual saved/reopened RAM model; account for
  every selected member, numeric difference, section/orientation and connection.
- [ ] Record manual acceptance and whether the run may be marked VERIFIED;
  unresolved discrepancies remain failed/pending and must not be hidden.
- [ ] Human approval recorded here before Task 20 and final failure qualification.

Approval/evidence: pending.

## E: negative cases and final qualification

<a id="task-20"></a>

### Task 20: Prove invalid inputs block before target writes

Dependencies: Tasks 15-19 and Checkpoint C. Scope: Medium, up to 4 authored files.
Coverage: Q-10; AC-002, AC-005, AC-011.

- [ ] Exercise wrong counts/categories, missing/ambiguous section mappings,
  unsupported geometry/offsets, invalid constraints and ambiguous/out-of-range
  connections with complete per-element reasons.
- [ ] For host-negative cases, confirm the actual command creates no RAM model
  or active model-writing adapter; do not equate pure-rule tests with host proof.
- [ ] Retain representative negative-case evidence without editing the user's
  source project or introducing automatic geometry repair.

Verification: TEST and HOST on separately prepared negative fixture cases;
capture before/after model-file inventory and report outcomes.

Files: `tests/StrHub.Core.Tests/PreflightTests.cs`,
`tests/StrHub.Core.Tests/ConnectivityTests.cs`, `scripts/qualify.ps1`,
`artifacts/evidence/negative-inputs.md`.

<a id="task-21"></a>

### Task 21: Qualify failure, cancellation and repeat-run lifecycle

Dependencies: Tasks 17-20. Scope: Medium, up to 5 authored files.
Coverage: Q-10; AC-008, AC-009.

- [ ] Define and exercise Failures scenarios for activation/execution/readback
  failure, cancellation, output collision, absent final result and bounded wait;
  use only owned test processes/assets and record injected versus actual failures.
- [ ] Preserve existing partial files with FAILED/incomplete diagnostics, release
  owned resources where possible, and never terminate/manipulate a user RAM
  session or delete unrelated sidecars to make a case pass.
- [ ] A second export creates a fresh run, preserves prior assets, and demonstrates
  resource/file-lock recovery; any residual lock is reported honestly.

Verification: BUILD, TEST where applicable, FAILURES and actual HOST/RAM repeat
runs; retain process/file observations and truthful final states.

Files: `src/StrHub.RamWorker/Program.cs`,
`src/StrHub.RamWorker/RamJobRunner.cs`, `src/StrHub.Revit/WorkerClient.cs`,
`scripts/qualify.ps1`, `tests/StrHub.Core.Tests/LifecycleTests.cs`.

<a id="task-22"></a>

### Task 22: Assemble the qualification and reuse evidence

Dependencies: Tasks 1-21 and all preceding checkpoints. Scope: Medium, 4 authored files.
Coverage: Q-01 through Q-10; AC-001 through AC-011.

- [ ] Link actual results for every acceptance criterion and compatibility case,
  including executed commands, exact versions/pins, numeric-bound approval,
  source/target identities, manual observations and remaining limitations.
- [ ] Document BHoM APIs reused, native glue and exceptions, and whether the
  evidence supports no fork or requires a separate minimal-fix proposal.
  Do not imply that a fork or production release has been authorized.
- [ ] Update command validation/history with honest unreleased/live-test evidence;
  keep task completion here and avoid duplicating status in the plan or discovery.

Verification: TEST, BUILD, METADATA and DIFF; review evidence links against every
AC/Q ID and confirm authored files remain inside strHUB. No main delivery or
broader version compatibility is claimed.

Files: `artifacts/evidence/manifest.json`, `artifacts/evidence/qualification.md`,
`artifacts/evidence/bhom-reuse.md`, `Export to RAM SS.pushbutton/SPEC.md`.

<a id="checkpoint-d"></a>

### Checkpoint D: final qualification review

- [ ] Review the full evidence package, unresolved defects and the exact scope
  proved on the selected installed pairing; static tests alone are insufficient.
- [ ] Human accepts the first proof or requests fixes. Future model reuse,
  additional software, reverse transfers and production deployment remain
  separate decisions.
- [ ] Record final task/qualification outcome and remaining work here. Do not
  mark the overall capability complete while required evidence remains absent.

Approval/evidence: pending.

## Approval record and implementation handoff

Spec and plan revision 1 are approved. Task breakdown revision 1: pending human
approval. Implementation has not started; the first executable work after task
approval is Task 1, followed in dependency order by Tasks 2-3 and the local-worker
checkpoint. Approval of this task document does not preapprove later checkpoints.

Carry [SPEC.md](../SPEC.md), [plan.md](plan.md), this task authority and
[compatibility.md](compatibility.md) together into implementation or a new session.
Preserve framework targets, physical-axis rules, 1/8 inch connectivity tolerance,
the separate numeric-bound review, fresh-file policy and incomplete-output
retention. No merge, release, publication, global installation or maintained
fork is authorized by task approval.
