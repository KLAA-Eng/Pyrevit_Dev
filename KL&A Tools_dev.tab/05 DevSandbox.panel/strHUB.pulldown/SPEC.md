# strHUB: Revit to RAM SS qualification proof

Status: **Draft for human approval**. Date: 10.29.2026.
This specification captures the user's seven interview decisions. Approval
confirms the shared scope and exclusions below; planning and implementation
remain separately gated. [DISCOVERY.md](DISCOVERY.md) owns research evidence,
source revisions, known adapter limitations, and interview history.

## Objective

Enable a KL&A structural engineer to export one selected, simple steel framing
bay from Revit to a new RAM Structural System file using BHoM wherever practical.
Prove compatibility and the agreed transfer properties on the installed software
before expanding the exporter. A successful API call alone is insufficient:
the saved model must reopen and its actual contents must match the source.

This is one capability: `strhub-revit-ramss-proof`. Multiple destinations,
reverse transfers, and synchronization are future scope, not additional modules
in this specification.

## Identity

| Field | Value |
| --- | --- |
| Work area | `KL&A Tools_dev.tab/05 DevSandbox.panel/strHUB.pulldown` |
| Planned command | `Export to RAM SS.pushbutton`, under this pulldown; not created yet |
| Tool ID | `devsandbox.strhub-export-ramss` (reserved for that command) |
| Path aliases | Planned development path above; no historical or release path exists |
| Version inputs | Planned command `script.py`, `bundle.yaml`, and its owned Python/compiled helpers; exact list finalized with implementation |
| Tool version | `v0.0` (planned) |
| Status/origin | Unreleased KL&A DevSandbox prototype using BHoM dependencies; no upstream source vendored |
| Maintainer | KL&A |
| Revit versions live-tested | None |

When the command is created, its adjacent `SPEC.md` must own its command metadata
and operational contract and reference this qualification spec for acceptance
requirements. Keep each requirement in one authoritative location. The bundle
and script titles must match; the bundle owns author and versioned tooltip.

## Agreed scope and source geometry

- Manually select four vertical steel columns and four straight, horizontal
  steel beams forming a single-story rectangular bay in the active project.
  Use standard AISC catalogue sections and the required Revit levels.
- Read beams from their stored physical `LocationCurve.Curve` endpoints.
  Derive vertical column axes from insertion X/Y and base/top level elevations
  plus their respective offsets.
- Do not source geometry from analytical members, solid extents, end extensions,
  cutback adjustments, or an automatic geometry-repair procedure.
- Choose a Revit base level as RAM Z=0. Preserve Revit internal X/Y and axes;
  subtract the chosen base elevation from exported Z. Convert units explicitly.
  Record the transformation and its inverse; change export data only.
- Preflight every selected element. If selected geometry cannot be represented
  faithfully or a section mapping is unverified, report all detected blockers
  and stop before RAM model writes. Do not silently substitute a size, flatten
  a member, or present a partial transfer as success.
- Initial host pairing: Revit 2026 `26.5.0.55` (installed .NET 10 runtime) and
  RAM SS `25.00.02.42`, using the installed pyRevit IronPython attachment.

## Development policy and draft assumptions

Item 1 is accepted for initial development. The remaining details are proposed
for review; the numeric tolerance and failed-output policy remain under discussion.

1. Each export uses a unique owned run directory and a new RAM file; existing
   models are never overwritten or updated. Cancellation before export writes
   no RAM model. The user accepted this for initial development only; future
   update/reuse behavior must be reconsidered when that capability is specified.
2. A run that fails after writing begins retains its owned output and diagnostics
   as incomplete. No cross-application atomic rollback is promised.
3. Readback coordinates and story elevations need an agreed numeric comparison
   threshold after unit normalization. **1 mm absolute was an initial proposal,
   not an accepted limit or a measured RAM precision.** The threshold is under
   discussion. It must accommodate only numeric/file precision and cannot
   authorize deliberate snapping, node merging, or geometry changes.
4. The proof qualifies member axes, beam/column classification, story placement,
   catalogue section assignment, and the fixture's section orientation. Source
   steel material/grade and applicable RAM defaults are reported; material
   mechanical properties, design settings, and analysis results are not qualified.
5. All authored files, dependency staging, test assets, logs, and transfer outputs
   stay under this pulldown. External host-managed caches/licensing data may be
   produced by Revit/RAM and must be identified if relevant; they are not strHUB
   output destinations. Any required deployment outside this area needs a new
   scope decision and applicable tool approval.

The proposed failed-output policy applies only after an export has begun writing.
A preflight-blocked attempt creates no RAM model. If an export fails after
creating some objects or saving a partial file, retain whatever owned model
files exist alongside diagnostics identifying the run as `FAILED`/incomplete.
An invalid or unreadable file is not promised to be recoverable. Retention is
for diagnosis, not permission to use the file as a completed transfer or to
resume writing into it. No partial model is created just to illustrate a failure.
Existing user files/sessions remain unaffected.

## User workflow, inputs, and effects

1. Open the agreed fixture in Revit and select its eight framing elements.
2. Invoke the prototype, choose its base level, and review the reported software
   versions and proposed output location.
3. Review preflight results: source axes, stories, steel classification, section
   mappings, and unsupported conditions. Continue only when no blocker remains.
4. Export to the new owned RAM file and verify the actual saved model through
   readback and RAM's UI. Display the final status and output/report locations.

Prerequisites: an active Revit project; the selected fixture; installed/licensed
RAM SS with functioning DataAccess; a pinned, compatible BHoM dependency set;
and writable output space inside strHUB. Capture missing prerequisites as
diagnostic failures rather than assuming compatibility from installation alone.

Source Revit documents, analytical associations, and existing RAM files remain
unchanged. The tool may load .NET assemblies, start an owned worker if justified
by the later plan, activate RAM DataAccess, and create owned model/report files.
Release only external resources it owns; never terminate a user's existing RAM
session to recover from a failure.

The report records software/runtime and loaded assembly identities, dependency
revisions, run ID, source document identity/available path, element UniqueIds,
source and transformed axes, base level and translation, section mappings,
source steel material/grade and target defaults, expected/actual counts,
warnings/blockers/errors, readback differences, and retained output paths.
Each selected element has a traceable outcome. Machine-readable transfer data
uses a documented version and retains source-to-target identity information.
This is preparation for future identity work, not a round-trip guarantee.

Final states are `CANCELLED`, `BLOCKED` (preflight), `FAILED` (execution or
verification), and `VERIFIED`. Only verified saved/reopened output earns the
last state. Partial output is visibly incomplete and never reported as verified.

## BHoM reuse and compatibility requirements

BHoM's object model is the common engineering representation. Reuse its
available engines, serialization, Revit helpers, and RAM adapter where their
behavior satisfies this contract. Keep RAM-specific mappings separate from
source extraction; do not introduce a competing universal structural schema.

The stock Revit bar converter's analytical preference and physical-axis
adjustments do not satisfy the agreed geometry rule. The RAM adapter's default
file creation path, section-creation stubs, snapping behavior, and partial-success
behavior likewise require qualification and control. A report must expose these
gaps rather than conceal them with successful return values.

Test the actual .NET 10/pyRevit host and RAM 25 interface. A csproj target, COM
registration, or success on another Revit/RAM version is not sufficient. Pin a
coherent BHoM dependency set rather than mixing local main and public develop
assemblies. Record any assembly conflicts and reproduce failures in an owned test.

Prefer upstream dependencies plus configuration/composition. A fork is justified
only by a reproduced required behavior that cannot reasonably be supplied through
supported configuration or a wrapper. Record the reproducer, minimal change,
alternatives, pinned upstream base, and maintenance implications before adopting
one. Preserve licenses and notices and review distribution requirements before
shipping upstream or modified binaries. No fork or global installation is
approved by this draft.

## Success criteria

All criteria are required. Automated evidence and host evidence are distinct.

| ID | Condition/trigger | Observable result | Evidence |
| --- | --- | --- | --- |
| AC-001 | Run compatibility qualification on the selected pairing | Exact host, engine, architecture, dependency and assembly identities recorded; required BHoM operations and RAM DataAccess work in the chosen runtime arrangement. Failures prevent a compatibility claim. | Live host probe and retained diagnostics. |
| AC-002 | Preflight the eight selected fixture members | Exactly four eligible columns and four eligible beams, valid geometry/levels, and verified section mappings. Every selected object has a reported outcome; no unrelated or linked elements enter the transfer. | Selection report, pure validation tests, live fixture. |
| AC-003 | A beam has associated analytical geometry or physical end adjustments differing from its stored location line | Exported geometry uses the stored physical line. Column endpoints use the accepted insertion/level/offset rule. No Revit transaction or source modification occurs. | Deliberately differing source fixture, captured endpoint comparisons, source inspection. |
| AC-004 | Use a nonzero Revit base-level elevation | X/Y and axes preserved; Z translated by exactly the chosen datum before unit conversion. Forward and inverse transformations and SI/RAM units are recorded and consistent. | Pure transform/unit tests and live readback. |
| AC-005 | A selected member is curved/sloped, has unresolved constraints/mapping, or would require deliberate snapping to a RAM story | All detected blockers reported with element identity and reason; no RAM model is created or modified for that blocked attempt. No default section/material guess is presented as verified. | Negative preflight tests and host boundary evidence. |
| AC-006 | Export a valid bay | New model contains four columns, four beams, and the intended story arrangement. Base Z=0 is handled as the datum, without duplicate/unintended stories. Each member has the intended catalogue section. | RAM queries, saved/reopened model and UI review. |
| AC-007 | Read back the saved/reopened file | Endpoint and story-elevation differences meet the agreed numeric comparison threshold (under discussion; 1 mm was an initial proposal). Classifications and mapped section labels match exactly; fixture section orientations are manually checked. No extra, missing, or substituted members. No verified status until a threshold is agreed. | Source/target comparison report and RAM UI evidence. |
| AC-008 | Start another run or encounter an existing output path | Use a distinct owned output, or block the collision; preserve prior runs and user files. No model appears at the adapter's uncontrolled default path. | Filesystem checks plus live repeat-run evidence. |
| AC-009 | Cancel, fail COM activation, or fail during creation/readback | Actionable status/error reported; owned resources released; any partial model retained and labeled incomplete. No verified status and no loss of user-owned sessions/files. | Failure scenarios and lifecycle diagnostics. |
| AC-010 | Review the finished qualification | All required criteria have linked evidence; BHoM reuse and exceptions are documented; compatibility/fidelity limits are stated. Any required fork has an explicit evidence-backed decision. | Human review of the evidence package. |

## Testing strategy

- Host-independent tests cover unit/datum transforms and their inverse, member
  eligibility, complete preflight reporting, section-map validation, output-path
  ownership, and reconciliation of expected/actual results. Use meaningful
  cases, including reversed endpoints and values that expose feet/metres/inches
  mistakes; do not duplicate implementation details in tests.
- Host tests prove assembly loading, actual Revit extraction, DataAccess
  activation, new-file ownership, save/reopen, and assigned catalogue sections.
  Include a source member with deliberately different analytical geometry.
- Use representative negative cases for unsupported geometry, missing section
  mapping, output collision, cancellation, and execution failure. Test a
  second run to expose resource/file locks.
- Keep the fixture and evidence manifest under strHUB. Record actual source
  family/type/section names and orientations with evidence; do not invent
  catalogue mappings in the spec. Live support claims require the exact host
  versions listed above to pass.

## Tech stack and project structure

The command adapter stays compatible with IronPython 2.7/pyRevit. BHoM is a
.NET dependency, not a Python-only replacement model. A compiled helper and/or
worker may be used if supported by qualification. Its target framework,
in-process versus worker placement, BHoM release pins, and dependency loading
strategy remain planning decisions. CPython is allowed for development checks
and host-independent tests, not as an implicit command-runtime migration.

Everything below is relative to `strHUB.pulldown`; only the two Markdown
documents exist at specification time:

```text
SPEC.md                         Initial qualification requirements
DISCOVERY.md                    Research evidence and interview history
Export to RAM SS.pushbutton/    Planned command bundle and adjacent SPEC
lib/                           Planned reusable/testable local helpers
src/                           Compiled source, if justified by the plan
tests/                         Host-independent checks
scripts/                       Isolated development/qualification entry points
artifacts/                     Owned build, dependency, fixture, run/evidence outputs
tasks/                         Later approved plan and task authority
```

Shared helpers remain local to this work area while the user's placement
constraint applies. Do not edit extension-root helpers, CI, release metadata,
generated `lib/build_info.py`, or reference checkouts to implement this proof.

## Commands

Run repository-level checks from the extension root with Git and CPython
configured on PATH (the inspection shell currently resolves them by absolute
installed paths):

```powershell
git diff --check -- 'KL&A Tools_dev.tab/05 DevSandbox.panel/strHUB.pulldown'
python -B scripts/check_tool_metadata.py
dotnet --list-sdks
dotnet --list-runtimes
```

Once the planned local tests exist, their development command is:

```powershell
python -B -m unittest discover -s 'KL&A Tools_dev.tab/05 DevSandbox.panel/strHUB.pulldown/tests' -p 'test_*.py'
```

There is no strHUB build or live-probe executable yet. The plan must provide the
exact executable commands, project paths, configurations, and output overrides
for its selected runtime before tasks are approved. Stock upstream post-build
targets copy to ProgramData/add-in folders and must not be run as an isolated
strHUB build. Live user entry point: Revit > KL&A Tools_dev > DevSandbox >
strHUB > Export to RAM SS (after implementation and reload).

## Code style

Follow the repository's Python/pyRevit and comment guides. Keep the command thin;
put deterministic logic in local helpers. Use explicit imports, ordinary
functions/values, and explicit file/resource ownership. No f-strings,
annotations, dataclasses, or CPython-only dependencies in IronPython command paths.

An existing style example from the Excel COM Smoke Test command:

```python
def _prepare_paths(paths):
    """Create only the owned per-run folder; never overwrite a prior run."""
    if not (_is_owned_path(paths, paths['workbook_path']) and
            _is_owned_path(paths, paths['csv_path'])):
        raise RuntimeError('Smoke-test path ownership check failed.')
```

This is a style excerpt, not strHUB implementation. New command scripts contain
only `__title__` and pure `__version__` metadata assignments; author/tooltip stay
in `bundle.yaml`. Compiled code follows existing .NET conventions and the actual
qualified runtime. Preserve BHoM public types instead of copying upstream source
into superficially renamed local classes.

## Boundaries and exclusions

**Always:** preserve source models and physical axes; report every selected
element; preflight before target writes; reconcile saved output; pin dependencies;
keep authored output under strHUB; record compatibility and reuse evidence.

**Ask first:** changes to agreed geometry/fidelity policy or scope; additional
software versions; global deployment; adoption of a maintained upstream fork;
new external services; changes outside strHUB. Routine reversible implementation
within separately approved tasks does not need repeated permission.

**Never:** silently use analytical lines or geometry repair; overwrite existing
RAM files; change the Revit model; hide unsupported data behind defaults; call
partial creation a verified transfer; claim support based only on metadata or
COM registration; copy upstream assets/code without license review.

Excluded: linked models, curved/sloping/brace members, multistory columns,
multiple stories/bays, slabs, walls, foundations, loads/combinations, releases,
supports, analysis/design execution and results, production-wide family mapping,
arbitrary material-property transfer, shared/site-coordinate modes, updates to
existing RAM models, reverse transfers, and round-trip conflict resolution.
The eight-member proof is not production-readiness or engineering design approval.

## Open technical decisions and approval

Interview rounds 1-2 established the transfer scope. The user subsequently
accepted a new file per run for initial development, requested more discussion
of numeric tolerance, and requested an explanation of retained failed output.
The latter two policies must be resolved before this draft is approved, or be
given an explicit approval checkpoint before verification. No numeric threshold
has been accepted. The following are for the later plan/qualification evidence:

- Coherent BHoM release/revisions and a complete local dependency closure.
- Physical-axis extraction/composition mechanism, preserving maximum BHoM reuse.
- Runtime placement, .NET targets, COM threading/lifetime, and assembly isolation.
- Controlled new-model creation that avoids the RAM adapter's default-path fallback.
- Fixture-specific section mappings and a reliable independent readback path.
- Whether any demonstrated blocker requires a minimal upstream change/fork.

Approve this spec before a technical plan is written. Approve that plan before
tasks, and tasks before product/probe implementation. A failed compatibility
prerequisite requires an evidence-backed revision, not an implicit scope change.

## Validation evidence and tool version history

| Date | Extension release | Revit version | Scenario | Result | Evidence |
| --- | --- | --- | --- | --- | --- |
| 10.29.2026 | `0.0.14` dev checkout | Installed 2026 build inspected | Read-only source/host/COM registration discovery | Findings recorded; no live BHoM export tested | [DISCOVERY.md](DISCOVERY.md) |

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| `v0.0` | Unreleased | 10.29.2026 | Planned first DevSandbox qualification proof; command not implemented | No main delivery or implementation commit exists; draft requirements only |

## Future work

After this proof is verified, choose the next scope explicitly: broader physical
member/family coverage, stories and offsets, additional RAM objects, another
software adapter, or reverse transfer. Define persistent identity and conflict
semantics before claiming round-trip synchronization. Decompose independently
deliverable capabilities before specifying that expanded initiative.
