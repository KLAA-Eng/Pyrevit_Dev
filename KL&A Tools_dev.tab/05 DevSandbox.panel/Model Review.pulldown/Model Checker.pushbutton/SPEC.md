# Model Checker

## Identity

| Field | Value |
| --- | --- |
| Tool ID | steel-model-review |
| Status/origin | KL&A original DevSandbox implementation; unreleased and awaiting live Revit acceptance. |
| Maturity | DevSandbox prototype. |
| Tool version | `v0.0` |
| Bundle path | `KL&A Tools_dev.tab/05 DevSandbox.panel/Model Review.pulldown/Model Checker.pushbutton` |
| Path aliases | Current bundle path above; former design name Steel Model Review, never delivered as a command. |
| Version inputs | `bundle.yaml`; `script.py`; `review.xaml`; `script.md`; `icon.png`; `icon.dark.png`; parent pulldown icons; this SPEC; `lib/steel_model_review/*.py`. |
| Maintainer | KL&A; individual owner to be assigned. |
| Revit design target | Revit 2024 and later; no exact version has live acceptance evidence. |
| Specification date | 2026-10-16 |

This is the authoritative adjacent specification for Model Checker. The user
requested a runnable tool in a new dropdown beside Prototypes. Model Review
contains the command, findings browser, and companion comments-only script.md.
No live Revit acceptance or SDS2 export evidence is claimed by this prototype.

### Current implementation boundary

All six checks, phase/option choices, reviewed material overrides, configurable
inch tolerances, result filtering, Select/Zoom, explicit grid-pair assignment,
session exceptions, and cancellation are implemented. Close the browser to
correct the model manually; invoke Model Checker again to open the previous
report or run a fresh review. Reports and exceptions stay in Revit session
memory, without model or external-file writes.

Model Review uses the existing KL&A cube ribbon icon; Model Checker uses the
existing search icon with light/dark theme variants. The findings browser shows
descriptive check names, member/support names and IDs, and the filtered result
count. Search includes both member and support identities. Measurements are
labeled as Offset or Overlap length and retain eight decimal places in inches.
An aligned column is described as aligned; off-grid wording is reserved for
nonzero discrepancies. Filtering clears details from the previous selection.

The reviewed beam implementation now uses versioned Member, Relationship, and
Check Result records. Snapshots retain source geometry once, relationship
evidence separately, and result references for browsing and exceptions. A new
session-cache schema prevents reuse of older reports/acceptances under new rules.
The browser shows relationship categories and readable Revit join/offset evidence.

Girder, Splice, and Corner/End classify finite reference relationships in plan;
they do not establish a designed connection or a vertical Pass. Exact targets
take precedence over unrelated near misses; multiple actual relationships are
retained as a joint group. Revit end-join participants and permission corroborate
geometry without overriding it. Column-axis offsets and approached finite
section-face diagnostics are separate. Recognized I-section web/flange labels
require section metadata and actual face evidence; other faces stay generic.
Face measurements currently use the reference endpoint and are informational,
because physical cut-end acceptance remains an open policy.

SMR-05 reports verified floor/roof bottom-face work-plane references as
Information; matching elevation alone is insufficient. SMR-06 reports an
Interior Crossing Error when finite beam reference spans cross internally and
their local section vertical intervals overlap. Separated-elevation plan
crossings are informational; unavailable local elevations are Not evaluated.
This is a section-envelope test, not a general solid boolean clash solver.
Critical/Warning mapping for crossing errors and attachment severity remain open.
Splice and Corner/End vertical expectations remain explicitly Not evaluated.
Z-offsets, justification, and join cutbacks are preserved as source facts; the
actual SDS2 transfer of these values is still awaiting detailing-team evidence.

Original family solid geometry supplies planar section boundaries in world
coordinates. Curved face boundaries, multi-solid families, sloping columns,
curved grids, and walls with unresolved side faces/openings have limited or no
evaluation and are reported accordingly. An endpoint check can evaluate while
its vertical check remains Not evaluated. Cross-type coincident geometry is a
Warning pending section equivalence, rather than a proven exact duplicate.
Pass outcomes are retained and available through the severity filter.

Global extraction coverage and per-check evaluated/unresolved member counts
are reported. Counts can overlap when only one end evaluates. Issue-resolution
history and physical cut-end gap/penetration measurements are deferred. Normal
uncut steel overlap is not treated as a clash.

## Purpose and workflow

Review the modeling quality of a fabrication/detailing Revit steel model
before its intended export to SDS2. Identify actionable geometry discrepancies
and support relationships that need a person's review. This tool does not
certify export compatibility, connection design, or structural adequacy.

One command runs six independently selectable checks across the whole model:

1. Beam endpoints and their potential supports.
2. Vertical mismatches at supported beam ends.
3. Column alignment to grids.
4. Duplicate members and suspicious partial overlaps.
5. Floor/roof bottom-face work-plane associations.
6. Interior beam crossings, distinct from duplicate members.

### Confirmed decisions

- The intended downstream application is SDS2.
- Steel reference endpoints reach support reference lines or axes; physical
  setbacks, cutbacks, and copes are generally completed in SDS2.
- Eligible supports are steel beams, steel columns, and concrete walls.
- Beam-to-beam framing normally aligns at top of steel.
- A beam supported by a concrete wall terminates at the wall face.
- Some projects intentionally contain off-grid columns.
- Review scope is the whole model, independent of current selection or view.
- Nonzero offsets smaller than 1/16 inch are Critical. Offsets at or above
  1/16 inch are Warning. Effectively zero is Pass.
- Missing supports and exact duplicates are Critical; ambiguous supports are
  Warning. Numerical noise must not create Critical findings.

### Implementation defaults to calibrate

The following make the design implementable but are proposed defaults, not
additional user-confirmed office standards. Show them in settings and the run
summary. Calibrate against representative export models before release.

| Setting | Proposed initial value or policy |
| --- | --- |
| Numerical zero tolerance | 0.000001 inch. |
| Boundary comparison tolerance | Same as numerical zero tolerance. |
| Support candidate search distance | 12 inches horizontally and vertically. |
| Near-duplicate comparison distance | 1/16 inch. |
| Plan parallel-angle tolerance | 0.01 degrees; configurable proposed default. |
| Grid review mode | Review nearest eligible intersection; intentional offsets can be accepted individually. |
| Linked models | Excluded from initial evaluation; report links as excluded coverage. |
| Phase | User confirms the intended export phase before running. |
| Design options | Main model plus one explicitly chosen option per relevant option set; report included options. |
| Exceptions | Session-only accepted findings with a required reason; durable storage deferred. |
| Report export | Deferred; the initial result is an in-session findings browser. |

The search distance locates candidates; it is not an acceptance tolerance.
Do not silently enlarge it or invent a support outside it. A missing-support
finding means no eligible candidate was found within the declared search.

### Reviewer workflow

1. Open the project and launch Model Checker.
2. Confirm export phase, option scope, enabled checks, and settings. All six
   checks default on. The dialog states that review covers the whole host model.
3. Choose grid review mode: nearest intersection, explicit expected grid pairs,
   or disabled for this project. Disabling is recorded as Not run.
4. Run the review with progress and cancellation available.
5. Review counts and coverage, then filter findings by check, severity, member,
   level, and review status. Critical findings sort first.
6. Select and zoom to the member and candidate support or grid pair. Review
   measured discrepancies and why the candidate was identified.
7. Accept intentional conditions with a reason, or close the browser and correct
   the model manually. Assign explicit grid pairs from column grid findings.
8. Rerun after corrections. Previous findings are a snapshot, not live results.

## Inputs and prerequisites

- An active project document containing structural framing and columns.
- Steel classification from structural material and available material data,
  with explicit user-reviewed family/type overrides when necessary.
- Concrete wall classification from structural/material evidence. Composite
  or unclassifiable walls require review rather than guessed classification.
- Reference curves, instance transforms, section dimensions or usable geometry,
  levels, grids, offsets, rotations, phase, and design-option information.
- Model coordinates are compared in one consistent coordinate system.
- Unit conversion occurs once at the host boundary; settings use explicit
  units and results offer inch measurements regardless of model display units.

Do not identify steel solely from a family name or exclude unknown materials
silently. Report unknown and unsupported elements in coverage. Steel braces,
joists, trusses, fabrication parts, concrete columns, and other support types
are outside the first version unless explicitly classified into a supported
beam/column representation during future implementation.

## Check definitions

### SMR-01: Beam endpoints

Evaluate both ends of each eligible beam separately. Use the reference curve
for plan topology and placed original geometry for section elevations. Preserve
raw instance offsets, justification, original reference endpoints and instance
transforms; do not manually double-apply offsets to already placed geometry.
Physical cut-end diagnostics and exporter-specific offset interpretation remain
outside the implemented acceptance rules.

Find candidates using a spatial index, then perform finite geometry checks:

- Steel beam: endpoint plan position relative to the supporting beam reference
  line over its finite span. Resolve vertical compatibility separately in SMR-02.
- Steel column: endpoint plan position relative to the column reference axis,
  with the candidate's finite vertical extent checked in SMR-02.
- Concrete wall: endpoint plan position relative to the approached physical
  side face over the wall's finite extent. Use the relevant bearing face, not
  the wall location line. Ambiguous faces remain a review item.

Do not accept an intersection of infinitely extended lines outside the support
span. Exclude the reviewed member itself. Deduplicate candidate identities.
Classify endpoint-to-interior nonparallel framing as Girder connection,
collinear opposite-running endpoint pairs as Splice connection, and angled
endpoint pairs as Corner/End. Parallel side-by-side members are not splices.
Use numerical zero for the finite endpoint region and the declared plan angle
tolerance for parallel directions. Splice shortfalls may target a finite facing
endpoint; infinitely extended nonparallel spans cannot establish support.

An actual plan target (including a finite column-face target) takes precedence
over unrelated near misses. Retain multiple actual relationships as a joint
group; do not invent a unique force-transfer direction. Multiple near misses
or unresolved wall faces produce Warning. A close member at another floor is
not a confirmed support just because plan geometry aligns. Search still checks
finite vertical envelopes; detailed vertical evaluation remains separate.

Read LocationCurve.ElementsAtJoin at each beam end, joining permission, and
available setback reference. Keep empty versus failed queries distinct. No join
is created, removed, reordered, or enabled. These API paths require live host
acceptance; no participant query alone proves correct geometry or export behavior.

Report Column Axis separately from the approached Column Web Face, Column
Flange Face, or generic Column Section Face. Face diagnostics measure reference
endpoint-to-face distance, not a physical cut-end error. Unresolved face geometry
is Not evaluated; no axis-aligned bounding box substitutes for a section face.

With a unique candidate, classify the horizontal endpoint discrepancy under
the common offset rule. Show signed along-beam shortfall/overshoot and lateral
miss where meaningful, plus the scalar distance used for severity. With no
candidate, produce Critical and show the search limits. Cantilevers can be
accepted with a reviewer reason; do not infer design intent automatically.

Physical overlap with a valid support is not itself an error: steel connection
end preparation is generally downstream. Unexpected shortfalls or overshoots
are measured against the required reference target. Retain physical end gap or
penetration as explanatory evidence when reliably available. This version is
not a general solid-clash or connection-clearance checker.

### SMR-02: Vertical mismatches

Evaluate each resolved girder/column/wall relationship, including a unique
near-miss candidate. Splice and Corner/End vertical rules are pending review and
return Not evaluated. If no support can be resolved, show Not evaluated with
the SMR-01 reason rather than reporting a zero discrepancy.

- Beam to beam: compare top-of-steel elevations at the actual framing station.
  Different section depths may have different centerline elevations and still
  pass. Account for slope, rotation, and instance offsets; do not use only
  reference level or nominal section depth where it gives an incorrect top.
- Beam to column: check that the beam's end section has a plausible vertical
  relationship to the finite column extent. Do not require beam top of steel
  to equal column top. A beam framed into a column shaft can pass.
- Beam to concrete wall: default to bearing with the beam underside at the
  local wall top at the approached face. This bearing interpretation is a
  proposed default; embedded/side-supported conditions need an exception or
  future explicit support profile.

For vertical intervals, an overlapping compatible interval has zero separation;
otherwise use the distance to the nearest admissible interval boundary. Wall
bearing uses signed underside-to-wall-top difference. Report both sign and
absolute magnitude; severity uses absolute magnitude.

Where the relevant surface, section envelope, or support relationship cannot
be determined reliably, return Not evaluated with a reason. Do not fabricate
an elevation from a bounding box. Sloping or rotated cases may be evaluated
only when local geometry is reliable; otherwise report the coverage limit.

### SMR-03: Column grid alignment

Measure the column reference axis at its base reference elevation in plan.
The first version targets vertical columns and straight grid intersections.
Sloping columns, curved grids, and unresolved multi-segment grids are Not
evaluated unless their handling is implemented and validated explicitly.

In nearest-intersection mode, find the nearest valid intersection of two
nonparallel eligible grid lines. Grid datum lines may be extended in plan:
their drawn extents are not physical support boundaries. Show both grid names,
the expected intersection, offsets to each line, and the planar distance to
the intersection. That planar distance drives severity. Avoid unstable pairs
of almost parallel lines; report no reliable pair instead of an arbitrary point.

An explicit expected grid pair overrides nearest-intersection selection for
that column. Equally plausible intersections produce Warning for ambiguity.
No reliable pair produces a coverage/review item, not a false Pass.

Use language such as 'Off-grid column: review intended location.' Off-grid
does not establish an error. Intentional conditions retain their measured
severity and can be marked Accepted exception. The project may disable this
check entirely without disabling the other checks.

### SMR-04: Duplicates and partial overlaps

Compare eligible steel beams and columns, including members of different
types. Phase and option filtering happens before comparison. Do not compare
mutually exclusive options as if both members will be exported.

- Exact duplicate: coincident occupied member placement within numerical zero
  tolerance, matching span/extent and section placement. Reversed beam endpoint
  order must still match. Classify Critical; include type differences.
- Near duplicate: matching overlapping extents and nearly coincident placement
  within the near-duplicate comparison distance, but not exact. Apply the
  common offset rule to maximum corresponding placement discrepancy.
- Partial overlap: collinear members with positive overlapping length but
  different extents. Classify Warning for review; display overlap length.

Use orientation, section justification, cross-section position, and rotation
to distinguish adjacent or built-up members. Ordinary crossing beams and
normal beam-column intersections are not duplicates. A shared endpoint alone
is not a partial overlap. Uncertain section equivalence is a Warning candidate,
not a proven exact duplicate. Deduplicate unordered pairs; group exact
duplicates only when all members meet the same equivalence criteria.

### SMR-05: Floor/roof bottom-face work planes

Resolve the beam's HostFace and any work-plane metadata, identify the target
floor/roof, and compare its stable face reference with GetBottomFaces for that
same host. Report Floor Bottom Work Plane, Roof Bottom Work Plane, Other Work
Plane, No Bottom-face Attachment Found, or Unresolved. A top/side face, matching
plane name, geometric contact, or independent coincident plane does not establish
bottom-face association. API failures and linked targets are Not evaluated.
Other outcomes are Information while severity policy is pending. Absence of a
returned host-face reference is reported as absence of detected evidence, not
proof that every possible constraint has been inspected. No work plane is created.

### SMR-06: Interior crossings

Use spatial envelope overlap to find finite nonparallel beam pairs; require the
intersection strictly inside both spans. Emit one unordered pair. Resolve local
original section intervals at the plan intersection: overlapping/touching
intervals produce an Interior Crossing Error, positive separation produces
Separated Plan Crossing Information, and unavailable geometry produces Not
evaluated. This explicit Error category has no approved Critical/Warning mapping.
Endpoint connections and collinear partial overlaps are handled by their own
checks. A clean member retains a Pass outcome for reference-span crossing review.

## Severity and result states

Let epsilon be the numerical zero tolerance and T be 1/16 inch. Compare
unrounded measurements. Normalize values within epsilon of zero to zero, and
values within the boundary comparison tolerance of T to T before classifying.
Require valid positive tolerances much smaller than T.

| Condition | Result |
| --- | --- |
| Absolute offset at or below epsilon | Pass. |
| Nonzero offset below T after normalization | Critical. |
| Offset at or above T after normalization | Warning. |
| No eligible support inside configured search | Critical. |
| Exact duplicate | Critical. |
| Ambiguous relationship or partial overlap | Warning. |
| Required data/geometry cannot be evaluated | Not evaluated, with reason. |
| Interior Crossing error | Error; Critical/Warning tier pending. |
| Bottom-face attachment, column-face diagnostic, separated plan crossing | Information; no approved error policy. |
| Disabled check | Not run. |

This smaller-offset/higher-severity ordering is intentional and user-confirmed.
Do not reverse it. Severity does not change when a reviewer accepts a finding.
For multiple measurements, retain separate findings or their separate
classifications; overall severity is Critical if any component is Critical.
Do not classify only the largest measurement, because that could hide a
Critical small offset behind a Warning large offset.

Evaluation states, severity, and review status are separate fields. Review
statuses are Open and Accepted exception. Future issue-resolution history may
mark an issue No longer detected only after equivalent complete evaluation;
skipped or excluded elements cannot be called resolved. The current report
contains the latest run's outcomes without labeling disappeared issues resolved.

## Outputs and effects

The findings browser includes run identity/time, model identity, tool version,
settings, scope, included phases/options, completeness, and coverage counts.
Report eligible, evaluated, excluded, unsupported, and failed elements by
check. Show Critical, Warning, and Accepted exception counts separately.
No findings is not a successful review when checks were skipped or incomplete.
Do not present a single quality percentage or an automatic 'ready for SDS2'
certification.

Each finding contains a stable check ID, model/element identity, beam end if
applicable, candidate support identities, family/type, level, measured values
and units, expected relationship, severity, reason, and review status. Include
enough decimal precision to reveal nonzero offsets smaller than 1/16 inch.
Do not display a Critical discrepancy as rounded zero.

Select/Zoom operates on the current document and verifies that elements still
exist. Geometry changes make results stale; require a rerun before treating
them as current. Exception matching uses model identity, stable element
identities, check/end identity, settings, and version fingerprints of relevant
members, types, materials/assets, levels, grids, phases, and options. Any
detected model/settings change conservatively invalidates all carried acceptance.

The review is read-only with respect to model data. It does not move members,
join geometry, edit parameters, delete duplicates, create connection objects,
change saved view graphics, export to SDS2, or invoke an exporter. Selection
and navigation are the initial review aids. Exceptions live in session memory.

Cancel preserves any prior complete report and clearly labels the current
run Cancelled/incomplete. Never represent partial results as a complete scan.
An element-level error is recorded and allows independent checks to continue;
a document/context failure stops the run with an explicit reason.

Unexpected failures show the execution stage and final exception message in
the dialog. Expand its details to read the complete traceback and Python
runtime version. Diagnostics are also sent directly to pyRevit output, with
stdout fallback, independently of the logger. A blank output window must not
be the only place a reviewer is told to find the error.

## Architecture and limits

- Keep the command adapter thin: host context, extraction, UI, and navigation.
- Place unit conversion contracts, normalized data records, finite geometry
  comparisons, severity, duplicate matching, and report logic in host-independent
  helpers under `lib/steel_model_review/` where practical.
- Access host APIs only through the appropriate Revit execution context; do
  not pass live document objects to background geometry workers.
- Use spatial filtering instead of unrestricted all-pairs member comparisons.
  Preserve deterministic ordering and never silently truncate findings.
- Initial guaranteed geometry scope is straight, reliably classified framing,
  vertical columns, straight grids, and concrete walls with resolvable bearing
  faces. Other cases must be explicitly evaluated or counted as Not evaluated.
- Whole model means the complete eligible host export scope across all views
  and levels; phase/option exclusions must be visible. Linked content is a
  documented first-version limitation, not secretly included.
- Keep future command paths compatible with the repository IronPython target.
- Before selecting version-specific APIs, inspect installed Revit/pyRevit and
  consult official documentation. This design commits to no unverified API call.
- Verify how the actual SDS2 export workflow interprets reference curves,
  offsets, justification, and wall bearing before claiming downstream benefit.

### API reference review

Revit 2024, 2025, and 2026 installation folders were found. The installed Revit
2024 RevitAPI.xml was consulted for structural material classification, original
family geometry, wall side faces, structural wall material layers, phases, and
element version identities. A subsequent reported failure identified pyRevit
6.5.3.26176+2017, IronPython 2.7.12 (IPY2712PR), and Revit 2024.3.40. A standalone
probe using the installed IronPython engine and Revit 2024 API accepted the
name/ID access and class filters in isolation. The subsequent live traceback
showed that the running command's Name descriptor has no GetValue method.
The helper now reads element.Name and uses SYMBOL_NAME_PARAM for types whose
Name getter is hidden. The isolated probe did not reproduce this host binding
difference and does not prove the complete workflow.
No upstream code or assets were copied.

- [Autodesk: original family geometry and its coordinate transform](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/d28a0880-bff8-1acc-ddf1-ce3205f2e8b3.htm).
- [Autodesk: structural material classification](https://help.autodesk.com/cloudhelp/2020/ENU/Revit-API/files/Revit_API_Developers_Guide/Revit_Geometric_Elements/Material/Revit_API_Revit_API_Developers_Guide_Revit_Geometric_Elements_Material_General_Material_Information_html.html).
- [Autodesk: wall side-face access](https://blog.autodesk.io/accessing-the-exterior-face-of-a-wall-programmatically/).
- [pyRevit: IronPython forms, selection dialogs, and cancellable progress](https://docs.pyrevitlabs.io/reference/pyrevit/forms/_ipy/).

## Acceptance scenarios

| ID | Scenario | Expected result |
| --- | --- | --- |
| A01 | Endpoint exactly at a valid steel target | Endpoint Pass. |
| A02 | Endpoint differs only within epsilon | Pass; no numerical-noise finding. |
| A03 | Endpoint misses by 1/32 inch | Critical. |
| A04 | Endpoint misses by exactly 1/16 inch | Warning. |
| A05 | Endpoint misses by 1/8 inch inside candidate search | Warning with candidate evidence. |
| A06 | Values just around T inside/outside boundary tolerance | Stable boundary normalization, then specified severity. |
| A07 | No eligible support inside search | Critical with search limits. |
| A08 | Two plausible supports | Warning ambiguity; no automatic support assignment. |
| A09 | Different beam depths, same top elevation | Vertical Pass. |
| A10 | Top-of-steel differs by 1/32 or 1/8 inch | Critical or Warning respectively. |
| A11 | Beam frames into finite column shaft | No column-top equality error. |
| A12 | Candidate only intersects an extended beam line | Not accepted as a finite support. |
| A13 | Beam terminates at concrete bearing face | Endpoint Pass; vertical bearing checked separately. |
| A14 | Beam stops at wall centerline rather than required face | Offset finding with correct face evidence. |
| A15 | Steel geometry overlaps its valid support | No clash finding solely from uncut geometry. |
| A16 | Column is exactly on expected grid intersection | Pass. |
| A17 | Column is off-grid by 1/32 or 1/8 inch | Critical or Warning; may accept intentional offset. |
| A18 | Explicit grid pair differs from nearest pair | Explicit expectation controls. |
| A19 | Grid check disabled | Not run; other checks still run. |
| A20 | Exact duplicates, including reversed beam endpoints | Critical, one unordered pair/group. |
| A21 | Nearly coincident duplicates displaced 1/32 inch | Critical near-duplicate finding. |
| A22 | Collinear partial overlap | Warning with overlap length. |
| A23 | Adjacent built-up members or ordinary crossing beams | No proven exact-duplicate finding. |
| A24 | Missing material, curved member, unresolved top geometry | Not evaluated with reason; no false Pass. |
| A25 | Members hidden in active view | Included when eligible in declared whole-model scope. |
| A26 | Linked members or mutually exclusive options | Exclusions/included option scope clearly reported. |
| A27 | Accept cantilever, then move member or change settings | Prior acceptance invalidated. |
| A28 | Cancel or encounter extraction failure | Incomplete coverage visible; no complete-review claim. |
| A29 | 1/32 inch horizontal miss and 1/8 inch vertical miss | Separate Critical and Warning; overall Critical. |
| A30 | Review, navigate, accept exception, rerun | Model data remains unchanged. |
| A31 | Exact girder match and an unrelated nearby beam | Exact relationship retained; no false ambiguity. |
| A32 | Collinear facing endpoints, including reversed order | Splice connection; vertical policy Not evaluated. |
| A33 | Angled endpoint pair | Corner/End; vertical policy Not evaluated. |
| A34 | Multiple actual member roles at a joint | Separate linked relationships retained. |
| A35 | Column reference endpoint and approached web/flange face | Separate axis offset and informational face distance. |
| A36 | Floor/roof bottom-face reference versus top/independent plane | Only matching source bottom face produces bottom-plane association. |
| A37 | Interior pair crossing with overlapping or separated elevations | Error or Information respectively; unavailable sections Not evaluated. |
| A38 | Empty/failed end-join query or disallowed join | Evidence retained independently from geometric classification. |
| A39 | Zero/absent common or end-specific z offsets | Distinct raw parameter states; no guessed SDS2 mapping. |

Host-independent tests should exercise the severity boundaries, finite geometry,
support ambiguity, duplicate pairing, exception invalidation, and report coverage.
Live tests must cover extraction, offsets/justification, wall faces, phase/options,
navigation, cancellation, and representative model size. Record timings and
member counts during calibration; no performance target is claimed yet.

## Validation evidence

| Date | Extension release | Revit version | Scenario | Result | Evidence |
| --- | --- | --- | --- | --- | --- |
| 2026-10-15 | Not applicable | Not run | Design discussion | Requirements captured; no implementation validation. | This SPEC and companion CDD outline. |
| 2026-10-16 | Unreleased | 2024.3.40 | User attempted Model Checker using pyRevit 6.5.3.26176+2017 | Failed; generic dialog and blank output. Original traceback unavailable. Direct failure diagnostics added; active-document rerun required. | User screenshots and local Revit journal. |
| 2026-10-16 | Unreleased | 2024.3.40 | Rerun with detailed failure reporting | Failed while choosing export phase: Name descriptor lacks GetValue. Helper corrected; successful live rerun still pending. | User-provided expanded traceback, host.py name helper. |

The reported Revit attempt failed; no successful live acceptance or SDS2 export
validation is claimed. Acceptance scenarios are requirements, not passing tests.

Host-independent validation on 2026-10-16: 83 rule/session, mocked-host,
failure-diagnostic, reporting, and connection-record tests passed;
repository metadata validator checked 35 visible commands with zero errors.
Python compilation and isolated XAML loading/rendering passed. All 11 command
and helper files also compiled with the installed IronPython 2.7 engine.
Live Revit acceptance remains pending. Tests are in `tests/steel_model_review_test.py` and
`tests/steel_model_review_host_test.py`, and
`tests/steel_model_review_command_test.py`. Reporting tests are in
`tests/steel_model_review_reporting_test.py`. An isolated .NET WPF render of
review.xaml with synthetic findings was visually inspected on 2026-10-16.
These checks do not prove extraction, IronPython WPF binding, navigation, or
live Revit behavior. Reload pyRevit and run a fresh review to validate the icons
and report changes in Revit.
New relationship, join-evidence, bottom-face and crossing fixtures are in
`tests/steel_model_review_connections_test.py`. The beam redesign is not yet
accepted live in Revit and has no SDS2 transfer validation.

## Tool version history

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| `v0.0` | Unreleased | 10.16.2026 | Whole-model review; classified beam relationships, separate record contracts, column-face diagnostics, bottom-face work planes, interior crossings, and readable findings. | Baseline c994742 on dev.model-checker plus pending implementation changes; no main delivery exists. |

## Backlog and implementation decisions

- Evaluate BHoM as a future optional dependency for schema conversion,
  interoperability, and shared geometry/comparison capabilities. Keep the adopted
  Member -> Relationship -> Check Result records independent of BHoM now;
  assess licensing, SI/inch conversion, .NET deployment, and Revit-version evidence
  before adding a dependency. No documented SDS2 adapter was found in this review.
- Complete live ElementsAtJoin and bottom-face work-plane fixtures, including
  rotated I/HSS columns, sloping hosts and Revit 2024 IronPython binding.
- Investigate the detailing team's actual SDS2 importer/exporter and z-offset
  transfer using paired source/import fixtures; determine crossing severity,
  bottom-face attachment policy, column physical cut-end criteria, and vertical
  expectations for Splice and Corner/End relationships.
- Calibrate epsilon, support search bounds, duplicate distance, wall bearing
  interpretation, and grid expectation controls using representative projects.
- Confirm material classification and necessary family/type overrides.
- Validate WPF findings and navigation in the installed pyRevit engine.
- Review support-candidate ambiguity, vertical evaluation coverage, and
  intentional overlap examples with the user before changing check policies.
- Add issue-resolution history and optional physical cut-end diagnostics.
- Validate actual SDS2 export behavior and document the exporter/version used.
- Consider durable project exceptions, exported reports, linked supports,
  curved geometry, and more detailed physical clash checks after the prototype.
- Column continuity, connection objects, connection design, automated fixes,
  analytical connectivity, and additional modeling-data checks are deferred.
