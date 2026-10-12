# Beam Reaction Declutter promotion review

**Tool ID:** `devsandbox.beam-reaction-declutter`
**Current location:** `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Beam Reaction Declutter.pushbutton`
**Target location:** `KL&A Tools_dev.tab/02 KL&A Tools.panel/Beam Reaction Declutter.pushbutton`
**Review state:** Pre-move acceptance in progress. No live result or signoff is implied by an empty cell.

## Agreed gate

Keep the command in Prototype until the focused and full repository checks,
Revit 2024/2025/2026 scenarios, and the owner's human review have passed.
Use disposable model copies. Record the exact Revit build, pyRevit loaded
extension path, model copy, plan view, and Reaction tag family for each run.
After signoff, move the command to the KL&A Tools panel on `dev`, then repeat
the affected static checks and ribbon launch test in all three versions.

An expected pinned, unsupported, or eight-step-cap outcome passes when the tag
remains unchanged and the failure-only report identifies it accurately. A
false success, unintended displacement, missing failure, unexpected graphics
loss, or failed transaction blocks promotion.

## Baseline static checks — 2026-10-08

| Check | Result |
| --- | --- |
| Focused Beam Reaction tests | 11 tests; passed. |
| Full test discovery | 206 tests; passed; 1 skip. |
| Visible-command metadata | 36 bundles; 0 errors. |
| Consolidated release check | 1 unrelated whitespace gate failure in `FindReplace - Views-proto.pushbutton/script.py:133` on the current `dev` HEAD. Preserve this separate work. |
| Beam Reaction live baseline | Pending in Revit 2024, 2025, and 2026. |

## Prototype update review before live testing

| Finding | Prototype change | Remaining verification |
| --- | --- | --- |
| Post-move collision bounds may be stale. | The command regenerates before checking final view bounds. | Revit 2024/2025/2026 host measurement pending. |
| Failed restoration can still commit displacement. | Each move and marker is verified in a tag subtransaction; failed work rolls back. Fatal regeneration or transaction failure aborts the action. | Live Undo and failure behavior pending. |
| Same-beam tags and the tagged beam need new collision rules. | The tagged beam is excluded as its tag's blocker; other same-beam tags are included. Center/end priority and shortest clear movement are applied. | Controlled same-beam cases pending. |
| Candidate boundaries are too broad for production. | Move requires one local straight beam reference; leader-on and pinned tags remain unchanged when overlapped. | Linked, curved, multi-reference, leader, and pinned host cases pending. |
| Movement and result rules need revision. | Total cap is eight steps per tag; final position must clear all blockers; output contains only remaining issues. | Controlled cap and report cases pending. |
| Rotated-plan priority is uncertain. | Bounds, movement, and beam verticality use plan-view axes. | Rotated-plan host case pending. |

## Updated static checks — 2026-10-08

| Check | Result |
| --- | --- |
| Focused Beam Reaction tests | 27 passed. |
| Full test discovery | 222 tests: 219 passed, 1 skipped, 2 unrelated FindReplace window-background failures. |
| Visible-command metadata | 36 bundles; 0 errors. |
| Consolidated release check | Two remaining gates fail: the FindReplace window-background tests above and unrelated release-delta whitespace in `FindReplace - Views-proto.pushbutton/script.py:133`. Prototype working-tree and new-file whitespace pass. |

## View-selection update — 2026-10-09

The initial popup offers Move (Active View), Move (Select Sheets), Clear Matching
Red Overrides, and Cancel. Active View runs an eligible plan directly or the
eligible plan views placed on an active sheet. Select Sheets opens a multi-sheet
picker and collects eligible placed plan views. Repeated view IDs are processed
once. Clear keeps the existing plan-view picker. A sheet scope with no eligible
plan views stops before a transaction.

The owner chose one move per shared tag across selected parent/dependent views.
The command plans against all selected views showing that tag, uses one eight-step
budget, verifies final clearance and exact-red overrides in each, and rolls back
the shared tag if any view fails. Host behavior remains to be verified.

| Check | Result |
| --- | --- |
| Focused Beam Reaction tests | 37 passed. |
| Full test discovery | 234 tests: 231 passed, 1 skipped, 2 FindReplace window-background failures. |
| Visible-command metadata | 36 bundles; 0 errors. |
| Consolidated release check | Two unrelated FindReplace gates remain: window-background tests and the `FindReplace - Views-proto.pushbutton/script.py:133` release-delta whitespace. Beam Reaction whitespace passes. |

## Revit transaction finding — 2026-10-09

A user-provided pyRevit output screenshot showed `Exception: The managed object
is not valid` at the post-`with` `transaction.status` check. The installed
pyRevit wrapper disposes its Revit transaction in `__exit__`, so that status
read occurred after disposal. The screenshot does not establish whether the
preceding model changes committed. The command now uses an explicit Revit
transaction, checks the status returned by `Commit()` before disposal, and
rolls back if processing fails while the transaction is still started. Focused
regression tests cover successful commit, processing rollback, and commit
failure. Revit 2024 retest and model-state review are pending.

| Check after transaction fix | Result |
| --- | --- |
| Focused Beam Reaction tests | 40 passed. |
| Full test discovery | 237 tests: 234 passed, 1 skipped, 2 FindReplace window-background failures. |
| Visible-command metadata | 36 bundles; 0 errors. |
| Consolidated release check | Still fails only the two unrelated FindReplace gates recorded above; Beam Reaction whitespace passes. |

## Revit 2024 conflict finding — 2026-10-09

In Revit 2024 build 24.3.50.51, test model
`TEST MODEL_R24_Updated_LocalDump_LoganMaddenKL&A`, active dependent plan
`HIGH ROOF FRAMING PLAN - ZONE C` (Id 471660), the owner's Move output listed
unresolved tags without a successful move. A read-only MCP inspection found
89 Reaction candidate tags in the End/Start KLAA14Tag families. The old all-elements
conflict rule considered oversized boxes from section boxes, cameras, view
controls, floors, and grids. One section-box box measured about 240 by 245 ft;
one camera box measured about 2,623 by 1,400 ft. A read-only simulation found
no tag clearable within eight steps under that rule. This is a conflict-policy
failure, not evidence of a failed transaction. No model changes were made during
the investigation.

The owner chose annotations and structural members as blockers. The prototype
now includes annotation content, detail items, structural framing, and columns;
it excludes view/datum controls and nonstructural model categories. A read-only
pre-change approximation found some possible clears under narrower rules; the
actual revised command, its red markers, and remaining reports still require a
live run in a disposable Revit 2024 model and acceptance in 2025/2026.

Read-only import of the revised command in Revit 2024 found 429 eligible
conflict elements among 628 collected elements in this plan. A dry run of the
command's single-view planner on the baseline model found 64 tags already
clear under the revised rule, 2 deferred, 15 capped, and 8 candidate moves:
2459357, 2459377, 2459386, 2459401, 2459407, 2459419, 2459461, and
2459462. Of the sample tags from the owner's output, tag 2459342 has no
remaining eligible conflict and should leave the report without moving. The
dry run does not establish final moves: preceding moves can change later
collisions, and Revit must verify bounds after regeneration. No revised
command run or model mutation has been performed through MCP.

| Check after conflict-policy change | Result |
| --- | --- |
| Focused Beam Reaction tests | 41 passed. |
| Full repository test discovery | 238 tests: 237 passed, 1 skipped. |
| Visible-command metadata | 34 bundles; 0 errors. |
| Beam Reaction diff whitespace | Passed. |
| Revit 2024 revised Move | Pending owner rerun and visual review. |

## Live environment record

| Revit version/build | Model copy and plan view | Reaction tag family | Loaded extension path | Reviewer/date |
| --- | --- | --- | --- | --- |
| 2024 / pending | Pending | Pending | Pending | Pending |
| 2025 / pending | Pending | Pending | Pending | Pending |
| 2026 / pending | Pending | Pending | Pending | Pending |

## Controlled scenarios

Record **Pass**, **Fail**, or **Not run** in each version column, with a short
evidence note or screenshot/output reference. Compare actual tag positions and
visible overlaps with the report; a count alone is insufficient.

| Scenario | Revit 2024 | Revit 2025 | Revit 2026 | Evidence / finding |
| --- | --- | --- | --- | --- |
| Move or Clear completes without a disposed-transaction status error; check tag positions and Undo state after the run. | Not run | Not run | Not run | Prior 2024 attempt stopped at the post-transaction status check; retest pending. |
| Move (Active View) runs an eligible active plan without opening a second picker. | Not run | Not run | Not run | |
| Move (Active View) on a sheet processes its placed plan views and stops without changes if none are eligible. | Not run | Not run | Not run | |
| Move (Select Sheets) accepts multiple sheets, ignores non-plan placements, and processes each distinct placed plan view once. | Not run | Not run | Not run | |
| Parent and dependent plan views placed across selected sheets handle shared tags according to the agreed single-run rule. | Not run | Not run | Not run | |
| An active parent/dependent plan checks only that active view; inspect unselected related views for shared-tag effects. | Not run | Not run | Not run | |
| One blocker clears at the first valid step; moved tag receives exact red marker. | Not run | Not run | Not run | |
| Multiple blockers resolve without creating a new overlap; total movement is at most eight 0.2 ft steps. | Not run | Not run | Not run | |
| A tag that cannot clear within the cap returns to its original position and appears in failure-only output. | Not run | Not run | Not run | |
| A pinned tag stays unchanged and is reported; other eligible tags continue. | Not run | Not run | Not run | |
| Same-beam center Reaction tag stays fixed while end Reaction tag takes the shortest clear path. | Not run | Not run | Not run | |
| Same-beam equal-distance and equal-direction ties follow the agreed deterministic rules. | Not run | Not run | Not run | |
| A non-Reaction tag on the same beam blocks a movable end Reaction tag; a center Reaction tag stays fixed if it cannot resolve the conflict. | Not run | Not run | Not run | |
| The tagged beam itself is not a blocker; drawn annotations and structural framing/columns remain blockers, while view controls and nonstructural model bounds are excluded. | Not run | Not run | Not run | |
| Leader-on, linked, curved, and multiple-reference tags stay unchanged and are reported as unsupported. | Not run | Not run | Not run | |
| Rotated plan view uses the visible beam/tag relationship correctly. | Not run | Not run | Not run | |
| A repeat Move rechecks an already moved tag within the same eight-step total cap for that run. | Not run | Not run | Not run | |
| Move replaces prior per-view overrides with exact red; Clear Matching Red Overrides removes exact red without restoring position. | Not run | Not run | Not run | |
| Clear Matching Red Overrides can remove manually applied exact red and does not remove a different red. | Not run | Not run | Not run | |
| An all-success run has no detailed report; failed or unresolved tags show only view, element ID, and reason. | Not run | Not run | Not run | |
| Revit Undo restores a successful Move or Clear action. | Not run | Not run | Not run | |
| Cancelled action/view selection and non-project or unsupported Revit context make no model changes. | Not run | Not run | Not run | |

Inject movement, marker, regeneration, and rollback failures in automated tests;
do not deliberately corrupt a live project to test a fatal Revit failure.

## Pre-move review

| Gate | Result / evidence |
| --- | --- |
| Focused command tests and full repository suite | 41 focused tests pass; 238 full-suite tests: 237 passed, 1 skipped. Rerun the gate after any further change and before promotion. |
| Metadata, tool version, SPEC, and path aliases | Metadata passes; prototype v0.1 is Unreleased. Final path alias revision waits for relocation. |
| Transaction, regeneration, final-overlap, and failure-report review | Source review and focused tests pass; live host behavior pending. |
| Complete source diff and unrelated-change preservation | Prototype-only source diff reviewed; FindReplace work left untouched. |
| Live scenarios in all three Revit versions | Pending. |
| Owner review and dated signoff | Pending. |

## Post-move verification

| Gate | Result / evidence |
| --- | --- |
| KL&A Tools panel layout and command launch in Revit 2024/2025/2026 | Pending. |
| Focused tests, full repository checks, metadata, and whitespace | Pending. |
| Final diff, SPEC path aliases, tooltip, and planned production version | Pending. |

**Owner decision:** Pending.
**Decision date:** Pending.
**Remaining limitations:** Pending review.
