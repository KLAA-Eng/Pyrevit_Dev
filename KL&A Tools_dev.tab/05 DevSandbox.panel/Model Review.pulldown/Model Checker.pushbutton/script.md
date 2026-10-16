# Model Checker: comment-driven implementation outline.
# This file contains comments only; it is not an executable command.
# Contract: SPEC.md in this directory, updated 2026-10-16.
# Read the complete specification before implementing any phase below.

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
# INVARIANT: Review must not modify model data or run an SDS2 export.

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
# Require a unique support or unique near-miss candidate from SMR-01.
# Otherwise return Not evaluated and reference the support-resolution reason.
# At beam-to-beam framing stations, compare local top-of-steel elevations.
# Account for different depths, instance offsets, slope, and section rotation.
# Do not compare centerline elevations as a substitute for top alignment.
# For beam-to-column framing, compare the beam end to finite column extent.
# Permit framing into the column shaft without requiring column-top equality.
# For wall bearing, compare beam underside to local wall top at the face.
# Treat embedded or side-supported wall conditions as explicit review cases.
# Use zero separation for compatible overlapping vertical intervals.
# Otherwise measure distance to the nearest admissible interval boundary.
# Preserve signed elevation differences and classify their absolute values.
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
# Offer filters for severity, check, level, member, and review status.
# Sort Critical findings first and use stable secondary ordering.
# Expose incomplete coverage even when no geometric findings were generated.
# Do not present an automatic SDS2-ready certification or quality percentage.
# Do not truncate findings silently on large models.

# Navigate and record reviewer decisions.
# Resolve current elements before each Select or Zoom action.
# Explain when an element was deleted or cannot be navigated to.
# Use selection and navigation without saved graphic overrides or new views.
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
# Release temporary resources without changing model data.

# Verify the implementation before delivery.
# Map SPEC acceptance scenarios A01 through A30 to evidence.
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
