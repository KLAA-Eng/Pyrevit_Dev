# Model Checker: comment-driven implementation outline.
# This file contains comments only; it is not an executable command.
# Contract: SPEC.md in this directory, updated 2026-10-16.
# Read the complete specification before implementing any phase below.

# Working logic review: 2026-10-16.
# Baseline implementation committed as c994742 on dev.model-checker.
# Review SMR-01, SMR-02, SMR-03, and SMR-04 in that order with the user.
# Record agreed logic and implementation changes in this comments-only file.
# User authorized executable implementation of the reviewed beam workflow.
# Implementation now includes separate Member/Relationship/CheckResult records,
# classified endpoints, read-only joins/offset evidence, column-face diagnostics,
# bottom-face work planes (SMR-05), and interior crossings (SMR-06).
# SPEC.md describes that implementation; unagreed policies remain explicit.
# BHoM is a future optional addition; no runtime dependency has been introduced.
# Review status: beam categories and separate column targets confirmed; join API,
# floor/roof association, z-offset transfer, SDS2 routes, and BHoM investigated.
# Live host/export evidence and remaining policy decisions are still pending.
# SMR-02 column review confirmed: full-depth shaft containment and a separate
# column-top bearing check are implemented, with independent result categories.
# Tangent confirmed: dedicated 3D review view with modeless report interaction.
# User selected colors that follow report filters; all checked members stay context.

# Identity and implementation boundaries.
# Use the Model Checker command with stable ID steel-model-review.
# Use the Model Review dropdown beside Prototypes in DevSandbox.
# Keep the authoritative SPEC beside this command.
# Set matching script and bundle titles and the planned prototype version.
# Keep author and versioned help in bundle metadata per repository policy.
# Inspect installed Revit and pyRevit versions before choosing host APIs.
# Verify version-specific behavior against official documentation.
# Keep command paths compatible with the repository IronPython target.
# Put deterministic comparisons in host-independent library helpers.
# INVARIANT: Do not edit member geometry/data or run an SDS2 export.
# Authorized writes are limited to the dedicated review view and its graphics.

# Establish the review context.
# Require an active project document and record its stable model identity.
# Explain that this is a whole-model review for fabrication/detailing geometry.
# Read all eligible levels and views through document-wide collection.
# Do not restrict collection to the active view or current selection.
# Ask the reviewer to confirm the intended export phase and option scope.
# Include the main model and chosen compatible design options only.
# Declare linked content excluded and report the coverage consequence.
# Preserve the previous complete report until a new run completes.

# Configure checks and expectations.
# Enable beam endpoints, vertical mismatches, grids, and duplicates by default.
# Offer nearest-intersection, explicit-grid-pair, and disabled grid modes.
# Explain that off-grid columns may represent intentional design conditions.
# Show the confirmed top-of-steel and concrete-wall-face conventions.
# Show the proposed underside-to-wall-top bearing interpretation separately.
# Show numerical zero, boundary tolerance, support search, and duplicate range.
# Label defaults requiring calibration as proposed rather than office standards.
# Validate positive distances and explicit units before starting the run.
# Require numerical tolerances to remain much smaller than 1/16 inch.
# Record all settings and enabled checks in the run identity.

# Establish result contracts.
# Create separate evaluation state, severity, and reviewer-status fields.
# Record Open or Accepted exception without changing measured severity.
# Use Not evaluated for missing or unsupported evidence, never a false Pass.
# Use Not run for disabled checks.
# Retain raw measurements and the normalized values used for classification.
# Store stable element identities alongside navigation IDs and display labels.
# Associate each result with its check ID and beam end where applicable.

# Extract normalized member records.
# Collect candidate structural framing, columns, concrete walls, and grids.
# Filter phase and design-option membership before comparing geometry.
# Classify steel and concrete from trustworthy material evidence.
# Offer explicit reviewed family/type overrides for unclassified content.
# Do not treat family naming alone as proof of material.
# Record excluded categories and unknown classifications in coverage.
# Capture reference curves, transforms, offsets, justification, and rotations.
# Read names directly; use the built-in type-name parameter for hidden getters.
# Do not require GetValue on IronPython's Name descriptor.
# Capture local section geometry and finite physical extents where reliable.
# Keep raw reference placement distinct from effective physical geometry.
# Convert coordinates and settings into one documented comparison unit system.
# Keep live host objects inside the supported Revit execution context.
# Record extraction failures by element and continue independent work.
# Mark unsupported curves, columns, grids, or wall faces with clear reasons.

# Build candidate indexes.
# Index finite beam spans, column extents, wall faces, and grid intersections.
# Expand search envelopes by the configured horizontal and vertical distances.
# Retain explicit identities to exclude self-matches and duplicate candidates.
# Use spatial filtering to avoid an unrestricted all-pairs model comparison.
# Preserve deterministic ordering regardless of collection order.
# Check cancellation between coherent extraction and comparison batches.

# Apply the common offset classifier.
# INVARIANT: Smaller nonzero offsets have the higher confirmed severity.
# Use absolute unrounded discrepancy for offset severity.
# Normalize values within numerical zero tolerance to zero and return Pass.
# Normalize values near 1/16 inch using the boundary comparison tolerance.
# Return Critical for remaining nonzero offsets below 1/16 inch.
# Return Warning for offsets at or above 1/16 inch.
# Preserve signs separately to explain shortfall, overshoot, or elevation.
# Preserve classifications of separate components before aggregating severity.
# Return overall Critical when any component is Critical.
# Never allow a larger Warning offset to conceal a smaller Critical offset.

# Evaluate SMR-01 beam endpoints.
# Current executable behavior for review, not a proposed policy change:
# Read both endpoints directly from the beam's straight LocationCurve.
# Do not substitute physical cutback or cope endpoints for those reference ends.
# Instance offsets and justification are not separately applied to these XY targets.
# Use the declared phase/options and eligible extracted host members only.
# Default candidate distance is 12 inches horizontally and vertically.
# Test horizontal distance from endpoint to target against that search distance.
# Test vertical separation from the beam end section to support bounds as well.
# Fall back to endpoint Z for this search if the beam section is unavailable.
# For beams, project the endpoint onto the support's finite reference span.
# Reject projections outside that span, including beyond a support endpoint.
# For columns, use the vertical reference axis as the plan target.
# For walls, intersect the beam approach line with the two finite side faces.
# Use the first approached face when both forward crossings can be resolved.
# Otherwise retain a nearby finite wall-face projection as ambiguous.
# Remove the reviewed beam itself; spatial queries yield each support once.
# Keep every candidate passing these tests; do not rank candidates by distance.
# Return Critical if no candidate remains and Warning if more than one remains.
# Also return Warning for a single ambiguous wall or parallel-beam candidate.
# The current parallel-beam test checks plan direction, not actual collinearity.
# It can mark side-by-side parallel beams ambiguous, not just end-to-end beams.
# For one unambiguous candidate, measure straight-line XY distance to its target.
# Apply the common offset severity to that distance, not to signed components.
# Report signed along-beam distance: positive shortfall, negative overshoot.
# Report signed lateral miss separately; both components remain explanatory.
# A nearby candidate has not yet passed the separate SMR-02 vertical check.
# No or ambiguous support makes SMR-02 Not evaluated for that beam end.
# The report includes the end number, related identities, reason, and offset.
# Accepting an intentional cantilever requires a reason and preserves severity.
# Physical cut-end gap/penetration is deferred in the executable prototype.
# SMR-01 review update: user requirements captured 2026-10-16.
# Treat a beam endpoint intersecting another beam as a connection relationship.
# Distinguish girder connections from splice connections in the checker.
# Revisit column connection logic rather than retaining axis-only reasoning as final.
# The baseline description above is historical. The reviewed categories and
# evidence strategy below are now implemented with live-host acceptance pending.
# The interpretation and proposed details below still need user review.
# Do not equate a checker connection relationship with a designed steel connection.

# Revit evidence reviewed for this discussion.
# Installed reference: C:/Program Files/Autodesk/Revit 2024/RevitAPI.xml.
# Previously identified runtime: Revit 2024.3.40 and pyRevit 6.5.3.26176+2017.
# LocationCurve.ElementsAtJoin exposes participants at a location-curve end.
# StructuralFramingUtils.IsJoinAllowedAtEnd reports permission to join only.
# Permission does not establish that any particular other member is connected.
# StructuralFramingUtils.GetEndReference reads the setback reference for an
# eligible joined non-concrete framing end; handle unavailable references explicitly.
# Join permission, location-line join, setback reference, physical cutback, and
# an explicitly modeled steel connection are separate pieces of evidence.
# Record existing join information read-only; do not enable, disable, or edit joins.
# Validate actual join-reporting behavior on Revit beam-to-body and end-to-end
# examples before using it as a reliable discriminator in the host adapter.
# Autodesk reference: location-line joining and disallow-join behavior.
# https://help.autodesk.com/cloudhelp/2024/ENU/Revit-StructEng/files/GUID-D870523D-97D3-40FD-A8FC-FED23A7CA254.htm
# Autodesk reference: location curve join participants.
# https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/9dd6eb99-f105-a05f-dc1b-dfde17b8768c.htm
# Autodesk reference: framing end-reference/setback utilities.
# https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/93d93c87-dfa2-12d5-dcb0-13d5cb0c0696.htm
# Autodesk's Revit 2024 automation examples distinguish beam-to-beam, collinear
# beam-end-to-end, and column web/flange situations; use these as conceptual
# references, without adopting the automation's analytical-model prerequisites.
# https://help.autodesk.com/cloudhelp/2024/ENU/RevitDynamoSteel/files/Library-Based_Connection_Design_Automation/RevitDynamoSteel_Library_Based_Connection_Design_Automation_Use_Connection_Automation_to_Place_Steel_Connections_with_Ranges_of_Applicability_html.html

# Dynamo reference inspected as data only; the graph was not executed or changed.
# File: C:/Users/ai_lmadden/Dev/dynamo/dev.dynamo/Revit 2024/Beam Rxn Checker_RVT 24.dyn
# Internal graph name: Beam Rxn Checker_RVT 24_v1.01.0.
# SHA256: 3E9FDFF416DB299A243C0ABF268B9E3104601721D641E7E8A8FACC66A51C842E.
# Matching Python node: 8befdae656ce4809b4fcff7a964c297d.
# The graph filters a framing set using Structural Usage value 3 in the group
# titled Filter for Girders, and constructs finite girder and column lines.
# Girder trim node: 4dee7e371b7d443ba6a99441b931c68e.
# Its input interval is 0.001 to 0.999, excluding 0.1 percent at each end.
# Interpreted purpose: distinguish a girder's interior from its end regions.
# That purpose is inferred from the graph; no separate splice classifier was found.
# Beam and girder paths translate location curves using z Offset Value and a
# plane-normal Z factor. Column lines use location, Base Level, Base Offset,
# and Length. These constructions need validation for justification and slope.
# The Python node tests start and end separately against each finite candidate.
# It first rejects points outside an expanded XY bounding rectangle.
# It then uses 3D cross-product collinearity and dot-product span limits.
# It returns candidate family/type labels separately for each beam end.
# Ideas to retain: finite endpoint-on-member testing and separate end results.
# Adaptation limits: preserve each candidate's element ID, exclude self explicitly,
# and do not collapse different same-type members into a set of type labels.
# Replace raw cross-product tolerance with a length-normalized distance in inches;
# the graph's cross product and dot tests use quantities with squared-length units.
# Do not inherit its literal 1e-6 tolerance without establishing Dynamo units.
# Use a physical endpoint-region tolerance instead of percentage-based trimming;
# otherwise the excluded length changes with the receiving beam's length.
# Do not inherit the reaction graph's W-family/name filters or tag-color writes.

# Replacement beam relationship logic: classifications confirmed by user.
# Evidence strategy, tolerances, and joint resolution remain proposed details.
# Find finite geometric relationships first, then use existing Revit join evidence
# to corroborate them or expose disagreement. Never use join permission as proof.
# Keep actual intersections separate from near misses found by the search radius.
# An unrelated nearby candidate must not make a unique exact intersection ambiguous.
# Preserve multiple actual relationships at a common joint as a joint group;
# do not invent a unique force-transfer direction when the geometry cannot show it.
# Girder connection: a beam end meets the interior of a nonparallel
# receiving beam. The receiving beam is the girder for this relationship.
# Do not require its Structural Usage parameter to say Girder; show that value
# as corroborating metadata or a mismatch for review, not a geometry override.
# Perpendicular and skew nonparallel framing use this geometric category;
# the angular tolerance distinguishing collinear cases remains to be agreed.
# Splice connection: two distinct beam endpoints meet, their axes are
# collinear, and their spans continue away from the common end in opposite directions.
# Parallel side-by-side members are not splice connections.
# Coincident positive-length overlaps remain SMR-04 review cases.
# Noncollinear endpoint-to-endpoint meetings are classified exactly as Corner/End.
# An interior-to-interior crossing is classified as Interior Crossing, an error
# type distinct from endpoint connections and from collinear partial overlaps.
# Crossing error severity and plan-only versus 3D detection still need decisions.
# Record plan crossings at separated elevations distinctly; do not silently
# equate a different-floor projection crossing with an actual member intersection.
# Add spatially filtered member-pair evaluation; endpoint-only iteration cannot
# detect an interior crossing. Emit one result per unordered pair and location.
# Keep endpoint identity and receiving-member station so the report can explain
# whether each relationship is end-to-body, end-to-end, or unresolved.
# Proposed report fields: connection type, member/end, receiving member/end or
# station, angle, horizontal miss, vertical result, and Revit join evidence.
# Plan topology and SMR-02 elevation checks must remain distinguishable so a
# vertical discrepancy does not disappear as a generic missing-support finding.
# Plan-only versus full 3D intersection is not yet agreed. Define the elevation
# screening for other floors and treatment of different-depth beams explicitly.
# A plan match alone must not be labeled a fully validated 3D connection.
# Near-miss classification, exact-match tolerance, endpoint-region tolerance,
# angular tolerance, joint grouping, and splice elevation expectations are open.

# Column connection redesign: user confirmed checking axis AND web/flange faces.
# Report Column Axis, Column Web Face, and Column Flange Face separately.
# For HSS and other sections, use Column Section Face or Unresolved Face rather
# than labeling every face as a W-section web or flange.
# Keep axis and face evidence independently available, including when a member
# has a reference endpoint at the axis but a physical end at a face.
# Do not require one endpoint representation to coincide with both targets.
# Resolve local section orientation and rotation to identify actual finite faces;
# an axis-aligned bounding box cannot distinguish a rotated web from a flange.
# Record whether each measured point came from the reference line, effective
# placed section, or physical cut end. The chosen point for each face rule,
# numerical limits, and whether a category is informational/error remain open.
# Do not assume proximity to a column axis proves the required connection.
# Discuss web center/reference planes versus actual physical faces and how
# justification affects each target; preserve separate axis results either way.
# Confirmed: require full-depth containment for shaft framing; evaluate top bearing
# separately. Partial overlap alone cannot pass. Physical bearing adequacy is pending.
# Discuss column rotation, W/HSS sections, and beams meeting above column extent.
# Discuss whether collinear beam ends over a column represent a splice, separate
# supported spans, or an explicitly unresolved joint without additional evidence.
# Do not require both beam ends and the column axis to share the same elevation.
# The finite vertical-column line in Dynamo is a useful reference, not a decided
# replacement for the column web/flange, face, or bearing rules.

# ElementsAtJoin investigation: documentation-backed, not live-host validated.
# The installed Revit 2024 API documents an indexed LocationCurve property.
# Candidate IronPython read form: beam.Location.get_ElementsAtJoin(end_index).
# Inspect both end indices, 0 and 1, for every eligible straight beam.
# Record each returned participant's UniqueId, numeric ID, category, and queried end.
# Remove self references and duplicate participants when building relationships.
# Preserve the raw participant list/order for diagnostics without giving order
# structural meaning; reading this property does not identify Girder or Splice.
# Query both members for comparison; do not assume reciprocal results or that a
# beam receiving another at midspan must list that beam at its own endpoints.
# An empty result means no end-join participants were returned by this query;
# it does not prove no geometric relationship exists. Query failure is separate.
# A returned participant is Revit join evidence, not proof of correct elevation,
# steel section contact, structural force transfer, or an SDS2 connection object.
# IsJoinAllowedAtEnd records join permission separately from participants.
# GetEndReference records a valid framing setback reference separately, when
# available; do not interpret it automatically as the uncut reference endpoint.
# JoinGeometryUtils information, if recorded, is a separate geometry-join channel.
# Never set ElementsAtJoin: the setter only rearranges existing participants.
# Do not open a transaction, regenerate, alter joins, or move test members as
# part of the eventual diagnostic read. Prepare fixture geometry separately.
# Proposed host probe output: member/end, reference XYZ, join allowed, returned
# participants, end-reference target, geometry relationship, and query failures.
# Proposed join validation fixtures, each in the installed IronPython/Revit host:
# J01: perpendicular beam end at the interior of a continuous girder.
# J02: collinear endpoints meeting; also reverse one member's endpoint order.
# J03: angled endpoints meeting, expected Corner/End.
# J04: interior crossings, with coincident and clearly separated elevations.
# J05: identical endpoint placement with Allow Join versus Disallow Join.
# J06: different depths with aligned tops and differing reference elevations.
# J07: lateral/vertical justification, common and independent end z offsets.
# J08: column axis, web-face, flange-face, rotated column, and common joint.
# J09: beam-system member, cutback/coped member, and a member with explicit steel
# connection geometry. Compare supported evidence without assuming equivalence.
# For each fixture, inspect both ends of every member and independently verify
# reference geometry; save raw results and exact host version before deciding
# whether join evidence can select among otherwise ambiguous candidates.
# No live probe has run in this review; documentation review is not acceptance.

# Additional requested check: floor/roof bottom-face work-plane attachment.
# User clarified scope: determine whether the beam is attached to the work plane
# referencing the BOTTOM face of a floor or roof. Generic hosting is insufficient.
# Implemented as SMR-05; outcomes are informational pending severity policy.
# Detect and report the relationship and its evidence before judging correctness.
# Report Floor Bottom Work Plane and Roof Bottom Work Plane separately.
# Other Work Plane, No Bottom-face Attachment Found, and Unresolved remain
# distinct outcomes; attachment presence is not yet assigned an error severity.
# Read FamilyInstance.Host and HostFace; resolve the target's category and ID.
# HostFace can expose the geometry face underlying a work plane and can be null
# when no underlying geometry reference is present. A Level host is not a roof.
# Verify the beam's actual work-plane/placement relationship and its referenced
# face; a generic face-host relationship should retain its precise evidence type.
# Installed Revit 2024 API: HostObjectUtils.GetBottomFaces(host) supplies bottom
# face references for supported compound hosts including floors and roofs.
# Compare the resolved source face with the bottom-face references of that SAME
# floor/roof. Matching only elevation, normal, or a work-plane name is insufficient.
# Preserve the face identity and work-plane reference chain for diagnostics;
# face-reference comparison and engine binding still require live validation.
# A top/side face of the correct floor/roof does not qualify as its bottom face.
# An independently created reference plane at the same elevation does not prove
# attachment to the floor/roof bottom. Geometric contact alone also does not.
# A face-based sketch plane can have an explicit reference relationship to its
# source face; investigate that existing relationship read-only, without creating
# a sketch plane or imposing a new constraint as part of this check.
# A work plane extends beyond the source face's boundary; association alone does
# not establish bearing/contact or require the entire beam inside the floor outline.
# Installed Revit 2024 API: BeamSystem.BeamBelongsTo(beam) returns its beam system;
# GetBeamIds supports checking membership. System membership alone does not
# establish a floor/roof bottom-face work plane. Keep a demonstrated indirect
# parent reference distinct from a direct beam work-plane attachment.
# Examine SuperComponent where applicable; truss-chord attachment is a distinct
# supported Revit concept, not proof that an ordinary beam has an Attach Top flag.
# Investigate GetGeneratingElementIds on suitable current instance geometry as
# supplementary evidence. Autodesk documents roof-extension relationships, but
# its wall example is not a guarantee of coverage for structural framing.
# Do not use original unjoined geometry to infer current attachment provenance.
# Null host, empty geometry provenance, unsupported parent, and failed lookup
# must remain distinguishable from a verified lack of bottom-face association.
# Geometric touching/intersection alone does not prove a parametric attachment.
# Preserve host identity/category, bottom-face reference, work-plane identity,
# parent path, direct/indirect association, and evidence source in the relationship.
# Cover floor and roof bottom planes, top/side planes, sloping/multiple bottom faces,
# independent coincident planes, level-only placement, contact without hosting,
# beam-system/truss parents, unavailable face references, and unsupported hosts.
# Do not fabricate one horizontal underside for sloped or shape-edited hosts.
# Linked targets remain outside initial host-model evaluation and need coverage.
# Confirm whether detecting this attachment is informational or an export-risk
# finding before assigning severity; do not require all beams to be attached.
# Autodesk bottom-face reference (also checked in installed Revit 2024 API XML):
# https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/34737312-04d0-3550-6a42-5020c4ea2284.htm
# Autodesk HostFace reference:
# https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/e795508b-bb6a-4f76-e282-57aa6f7074e5.htm
# Autodesk geometry-provenance reference:
# https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/112590d2-de20-dd1f-ae05-df7dfb3b410f.htm
# Autodesk truss attachment reference:
# https://help.autodesk.com/cloudhelp/2024/ENU/Revit-StructEng/files/GUID-A77B218C-3EC7-4D60-AA69-B23CA115F5C4.htm

# Z-offset investigation: explicitly open; no export-mapping assumption approved.
# Preserve raw location-curve endpoints, level/start/end elevation offsets,
# z Justification, yz Justification mode, common z Offset Value, independent
# start/end z offsets, cross-section rotation, and effective physical geometry.
# Record absent/inapplicable parameters separately from numeric zero.
# Do not double-apply offsets already represented by the extracted geometry.
# Local section z and global Z can differ on sloping/rotated members.
# Do not declare every nonzero z offset an error before its intended export
# representation is established with the detailing team and a transfer fixture.
# Detailing-team questions prepared; recipient/channel requested, not contacted:
# 1. Which exact Revit/SDS2 versions, exporter/plugin build, import command, and
#    file format do you use: SDS2 XML roundtripping, IFC, CIS/2, SDNF, or another tool?
# 2. Does this route transfer reference axes, offset-adjusted member lines,
#    physical solids, or combinations? Where do z offsets and justification land?
# 3. Do common versus independent end offsets, start/end level offsets, slopes,
#    rotation, cutbacks, copes, and host/roof constraints arrive differently?
# 4. Which Revit modeling conventions do you require for column axis/face targets,
#    girder connections, splices, and corner/end joints before transfer?
# 5. Can you supply one small source model, its transfer file, importer settings,
#    warnings, and measured imported end coordinates/top elevations as evidence?
# Proposed transfer fixture: zero, positive, and negative common z offset;
# different end offsets; changed justification; unequal-depth aligned tops;
# slope/rotation; floor/roof association; column face/axis; cutback/coped ends.
# Compare intended physical position and member identity before and after import.
# Record SDS2 workline/end positions, top of steel, section orientation and shape
# mapping, preserving units and shared-coordinate transforms for each route.

# SDS2 import research: official public documentation reviewed 2026-10-16.
# Verified route A: SDS2 supplies a Revit-side Autodesk Revit toolbox plug-in.
# Its current downloads include Revit 2024; it requires suitable Revit content.
# SDS2's Import Model from Revit command consumes the plug-in's XML interchange
# and supports initial import and later member-change synchronization.
# The documentation distinguishes member transfer from connection transfer and
# references Revit SDS2 Roundtripping and SDS2 Connect for connection workflows.
# Project/job identity is tracked across exchanges; this is not arbitrary XML.
# Confirm installed builds and entitlement with the team/vendor rather than
# assuming the documentation's legacy product names define today's packaging.
# Verified route B: SDS2's own Import Model supports IFC2x3, CIS/2, and SDNF and
# can create editable members. Shape matching and import settings affect results.
# Revit offers IFC export, so a neutral-file route need not involve a separate
# third-party converter. IFC export and XML roundtripping are different workflows.
# Some other supported input formats produce reference models rather than
# editable beams/columns. Do not infer IFC4 import from SDS2's IFC4 export support.
# No reviewed source establishes preservation of every Revit z-offset mode,
# framing join, floor/roof association, or our connection labels for either route.
# Research identifies supported routes; no importer was installed or transfer run.
# Native roundtripping workflow and constraints:
# https://techsupport.sds2.com/main/Topics/revit_in.htm
# Current plug-in listing, Revit 2024 download, and content requirements:
# https://sds2.com/sds2-toolbox-details/revit/
# Version matching and installation FAQ:
# https://techsupport.sds2.com/main/faq.htm
# Neutral-file importer, editable/reference distinctions, shape mapping/options:
# https://techsupport.sds2.com/main/Import/dsgnmain.htm
# Revit IFC capability:
# https://help.autodesk.com/cloudhelp/2026/ENU/Revit-DocumentPresent/files/GUID-6708CFD6-0AD7-461F-ADE8-6527423EC895.htm

# BHoM assessment: useful schema/architecture reference; no dependency added.
# BHoM separates object definitions (oM), calculation Engines, application
# Adapters, and UI. This maps well to our records, pure rules, host adapter,
# and findings browser; it can guide organization without changing the runtime.
# Physical Beam has location-curve and framing-property concepts. Structural Bar
# is an analytical two-node element with section, orientation, releases, and
# local end offsets; its analytical Offset is not automatically Revit z Offset.
# The Revit conversion matrix distinguishes physical Beam/Column objects from
# analytical Bars. Prefer physical-member semantics for this detailing review.
# Revit identifiers/fragments and configurable comparison/hashing offer useful
# patterns for model provenance, rerun comparison, and exception invalidation.
# JSON schemas can support explicit serialized contracts; validating a schema
# does not validate connection geometry or certify fabrication/import readiness.
# BHoM uses SI/metres; our normalized checker uses inches, requiring an explicit
# tested conversion boundary if BHoM objects or Engines are introduced later.
# Revit_Toolkit lists Revit 2024 among supported versions and provides conversion
# utilities plus a listener/adapter route. Integration adds versioned .NET/toolkit
# deployment and compatibility work; it does not replace Revit host execution rules.
# No documented SDS2 adapter or complete checker matching these office rules was
# found in the reviewed official toolkit/docs sources; do not infer one exists.
# User decision: adopt Member -> Relationship -> Check Result records now as
# the local design contract. The executable snapshot now uses this structure.
# Evaluate a BHoM dependency as a future addition; add none at this stage.
# Adopted local schema, not a claim of exact BHoM types or field compatibility:
# MemberRecord: source model/IDs, reference line, physical geometry, local section,
# material/type, phase/option, level, raw offsets/justification, and raw host facts.
# RelationshipRecord: participant IDs/ends/stations, relationship category, target
# kind (axis/web/flange/section face/floor bottom plane/roof bottom plane), geometry
# measurements, work-plane/face reference chains, and join evidence.
# CheckResult: check ID, error type, evaluation state, severity, member relationship,
# units/tolerances, reason/evidence, review status, and run/settings fingerprints.
# Keep source facts, inferred relationships, and reviewer decisions separate.
# Member records retain source facts once. Relationship records reference member
# identities and external target identities such as a floor/roof plus bottom face.
# Check Results reference the member/relationship identities being evaluated,
# rather than duplicating or mutating their source geometry and evidence.
# Organizational value: explicit toolkit ownership, documented contracts, review
# teams, versioning, and shared fixtures. Follow our existing repository controls;
# BHoM's own merge-team rules are a reference, not governance for this extension.
# Reviewed code is LGPL-3.0; any later dependency or code reuse needs a deliberate
# license/deployment review. No BHoM source was copied or installed in this work.
# Architecture:
# https://bhom.xyz/documentation/Basics/BHoM-Toolkits/
# Physical Beam and analytical Bar definitions:
# https://github.com/BHoM/BHoM/blob/develop/Physical_oM/Elements/Beam.cs
# https://github.com/BHoM/BHoM/blob/develop/Structure_oM/Elements/Bar.cs
# Revit capability and compatibility:
# https://github.com/BHoM/Revit_Toolkit
# https://bhom.xyz/documentation/Guides-and-Tutorials/Visual-Programming-with-BHoM/Revit%20Toolkit/Pull/Conversion%20from%20Revit/
# Units, schema, comparison, identity, and ownership references:
# https://bhom.xyz/documentation/BHoM_oM/BHoM-Units-conventions/
# https://bhom.xyz/documentation/BHoM_oM/JSONSchema/
# https://bhom.xyz/documentation/Guides-and-Tutorials/Visual-Programming-with-BHoM/Diffing%20and%20Hashing/Configuring-Revit-objects-comparison-(RevitComparisonConfig)/
# https://bhom.xyz/documentation/Guides-and-Tutorials/Visual-Programming-with-BHoM/Revit%20Toolkit/Revit%20Adapter/BHoM%20vs%20Revit%20Identity/
# https://bhom.xyz/documentation/Contributing/Best-practices/Merge-Teams/

# Earlier intended implementation outline, retained as baseline context.
# Where it conflicts with the redesign notes, resolve the open decision before
# changing executable rules or updating the implemented contract in SPEC.md.
# Visit both ends of every eligible beam.
# Search only eligible steel beams, steel columns, and concrete walls.
# For steel beam candidates, measure plan miss to the finite reference span.
# For steel columns, measure plan miss to the column reference axis.
# For concrete walls, identify the approached finite physical side face.
# Do not substitute a wall location line or centerline for its required face.
# Do not accept an intersection outside a finite supporting beam or wall.
# Retain candidates requiring vertical evaluation rather than declaring support.
# Reject self-matches and retain evidence for every plausible candidate.
# Treat unresolved end-to-end framing as ambiguous support direction.
# Return Warning if multiple candidates remain plausible.
# Return Critical when no eligible support exists within the declared search.
# Explain that a search failure is not proof of absence beyond search bounds.
# For a unique candidate, classify the endpoint plan discrepancy.
# Show along-member shortfall or overshoot and lateral discrepancy if reliable.
# Keep physical gap or penetration as supporting evidence when available.
# Do not flag normal uncut overlap with a valid steel support as a clash.
# Allow intentional cantilevers to be accepted with a reviewer reason.

# Evaluate SMR-02 vertical mismatches.
# Evaluate each resolved actual relationship or unique near-miss from SMR-01.
# Missing or ambiguous support returns Not evaluated with its resolution reason.
# At beam-to-beam framing stations, compare local top-of-steel elevations.
# Account for different depths, instance offsets, slope, and section rotation.
# Do not compare centerline elevations as a substitute for top alignment.
# For Column Shaft, require the full local beam depth within original-solid
# finite column extent. Partial overlap fails, including protrusion at either end.
# Measure the greater protrusion: negative below base, positive above top; on a
# tie use positive. Preserve both signed boundary differences in the details.
# Contained shaft framing passes without requiring column-top equality.
# If the underside is at/above the column upper extent within numerical zero,
# classify Column Top Bearing and measure underside minus local column top.
# Missing local top geometry is Not evaluated; do not infer bearing from bounds.
# Partial upper overlap with underside below column top stays a shaft failure.
# Keep axis, faces, shaft, and bearing categories separately linked to results.
# Cap plates, seats, nonuniform cuts, and physical bearing area remain future work.
# For wall bearing, compare beam underside to local wall top at the face.
# Treat embedded or side-supported wall conditions as explicit review cases.
# Preserve signed elevation differences and classify their absolute values.
# Invalidate old session reports and acceptances when acceptance rules change.
# Return Not evaluated when local section or support geometry is unreliable.
# Do not fabricate a top elevation from a coarse bounding box.

# Evaluate SMR-03 column grid alignment.
# Respect disabled mode and report the check as Not run.
# Restrict initial guaranteed evaluation to vertical columns and straight grids.
# Locate each column reference axis at its base reference elevation in plan.
# Build eligible intersections from nonparallel grid datum lines.
# Permit datum extension in plan while rejecting unstable near-parallel pairs.
# Apply an explicit expected grid pair before considering nearest intersections.
# Otherwise choose the nearest unambiguous valid grid intersection.
# Return Warning when equally plausible expectations remain unresolved.
# Return a coverage review item when no reliable grid pair exists.
# Measure planar distance to the expected intersection for severity.
# Also display both grid names and separate offsets to each grid line.
# Describe the result as a review of intended column location.
# Allow acceptance of intentional offsets without changing measured severity.

# Evaluate SMR-04 duplicate members.
# Compare eligible steel beams and columns within the declared export scope.
# Exclude mutually exclusive design options before pair generation.
# Canonicalize beam endpoint order for placement comparison.
# Compare finite extents, orientation, section placement, and justification.
# Compare members across type boundaries and report type differences.
# Return Critical for proven exact duplicates within numerical zero tolerance.
# Measure maximum corresponding placement discrepancy for near duplicates.
# Apply the common classifier within the configured near-duplicate distance.
# Report collinear positive partial overlaps as Warning with overlap length.
# Do not treat a shared endpoint as positive overlapping length.
# Do not classify ordinary crossing members as duplicates.
# Distinguish adjacent built-up members from coincident member placement.
# Treat uncertain section equivalence as a Warning candidate.
# Deduplicate unordered member pairs and group only equivalent exact matches.

# Assemble the report.
# Include run identity, time, model identity, settings, phase, and options.
# Count eligible, evaluated, excluded, unsupported, and failed elements by check.
# Show Critical, Warning, and accepted-exception counts separately.
# Include check IDs, element identities, ends, supports, types, and levels.
# Explain expected relationships and show actual measured discrepancies.
# Display enough decimal precision that a Critical offset never looks zero.
# Label overlap length separately from offset, and describe aligned columns as aligned.
# Display descriptive check labels, searchable member/support IDs, and filtered counts.
# Offer filters for severity, check, level, member, and review status.
# Sort Critical findings first and use stable secondary ordering.
# Expose incomplete coverage even when no geometric findings were generated.
# Do not present an automatic SDS2-ready certification or quality percentage.
# Do not truncate findings silently on large models.

# Navigate and record reviewer decisions.
# Resolve current elements before each Select or Zoom action.
# Explain when an element was deleted or cannot be navigated to.
# Create/reuse a tool-created isometric review view identified by stored UniqueId.
# Never adopt a user's view by matching its name. Recreate a deleted review view.
# Include extracted steel beams/columns and concrete walls; exclude grids, links,
# floor/roof hosts, and identity-only failed extraction records from view scope.
# Set report phase and persist category/element isolation in that view only.
# Report visible versus requested member counts; phase filters, design options,
# and worksets can restrict visibility without changing document-wide checking.
# Fail isolation if unchecked members cannot be hidden; roll back failed writes.
# Show filtered open severities with surface/cut fills and line colors:
# Critical red, Error magenta, Warning orange, Not evaluated purple, Information
# blue. All other checked members stay gray context, including Pass/accepted.
# Highest open severity wins. Pair errors color both participants; endpoint
# errors color the owning beam without assigning blame to its receiving support.
# Accepting one finding removes only its contribution; reopening restores it.
# Keep the report modeless with persistent-engine ExternalEvent requests.
# Coalesce filter updates, apply changed colors only, and guard document identity.
# Select/Zoom, accept/reopen, grid assignment, and rerun keep the report open.
# Colors update when Revit is idle; source geometry is recalculated only on rerun.
# Mark source changes stale, but exclude the tool's own view-write transactions.
# Preserve prior complete report/view on cancellation; create none for partial runs.
# Closing report/document unsubscribes handlers and disposes queued event access.
# The review view persists in Revit after closing and is saved with the project.
# Require a reason before marking an intentional condition Accepted exception.
# Keep exceptions in session memory for the initial version.
# Key acceptance to model, stable element identities, check, end, and geometry.
# Invalidate acceptance when relevant geometry or comparison settings change.
# Mark a report stale after model changes and require a rerun for current use.
# Only mark prior findings No longer detected after equivalent complete review.
# Do not treat excluded or unsupported elements as resolved findings.

# Handle cancellation and failures.
# Stop cleanly at cancellation boundaries and label partial results incomplete.
# Keep the prior complete report accessible with its original run identity.
# Record element-level errors without silently discarding failed coverage.
# Stop on invalid document context and report the actual reason.
# Include the execution stage and complete traceback in failure dialog details.
# Write diagnostics directly to output without relying on the runtime logger.
# Release event resources; do not leave handlers attached to a closed report.

# Verify the implementation before delivery.
# Map SPEC acceptance scenarios A01 through A50 to evidence.
# Test zero, 1/32 inch, 1/16 inch, 1/8 inch, and boundary normalization.
# Test finite targets, ambiguous candidates, and reference versus physical ends.
# Test different beam depths with aligned tops and valid column-shaft framing.
# Test wall-face targeting and the proposed bearing interpretation in Revit.
# Test off-grid exceptions and explicit grid pairs on representative projects.
# Test reversed duplicate endpoints and intentional adjacent member placement.
# Test mixed Critical and Warning measurements without severity masking.
# Test coverage, cancellation, stale results, and acceptance invalidation.
# Validate offsets, justification, phases, options, and navigation live in Revit.
# Record model size and timing to calibrate settings and responsiveness.
# Verify downstream assumptions using the actual SDS2 export workflow.
# Record exact tested host versions and remaining acceptance limits.
# Review the final diff and record remaining live acceptance before delivery.
