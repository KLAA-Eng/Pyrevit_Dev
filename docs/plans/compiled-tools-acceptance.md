# Family Studio and Startup Importer acceptance follow-up

- Task authority: this plan; no separate tracker is selected.
- Responsible team: KL&A engineering; execution assignee is not yet selected.
- Established: 2026-10-18, during documentation filing on
  `chore/klcode-workspace-setup`, source HEAD `0c418da`.
- State: follow-up work recorded; the checks below have not been executed by
  this documentation pass. This plan does not authorize release or promotion.

## Scope and authoritative contracts

Re-establish current source/build evidence and complete the documented host
acceptance for the supported compiled DevSandbox tools. Command behavior and
acceptance boundaries remain owned by the adjacent specifications:

- [Family Studio validation boundary](<../../KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Family Studio.invokebutton/SPEC.md#validation-boundary>).
- [Startup Importer import contract](<../../KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Startup Importer.invokebutton/SPEC.md#wave-2-import-contract>)
  and [deferred contracts/live gates](<../../KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Startup Importer.invokebutton/SPEC.md#deferred-contracts-and-live-gates>).
- [Living design-system guide](../DESIGNSYSTEM.md).

Views indexing, root/tag/type mutation, vendor integration, placement/splitting,
and links/rebuild proposals in old designs are not added to this effort.
Keep both commands in DevSandbox. Do not create fixtures, seed RVTs, or catalog
content by guessing owner-defined inputs.

## Evidence and unresolved baseline

The [2026-09-01 handoff](../knowledge/family-studio-startup-importer-handoff.md)
reports source tests, Windows compilation, and dual-host packaging as complete,
with live acceptance outstanding. The [compiled-WPF decision record](../knowledge/compiled-wpf-decision.md)
records the adapter boundary and its original matrix.

Later, the [2026-10-05 validation record](../knowledge/reviews/2026-10-05/validation-and-acceptance.md)
reported a failing compiled palette-contract test, and the
[finding register](../knowledge/reviews/2026-10-05/finding-register.md) recorded
Family Studio and Startup Importer correctness findings. These are dated
observations, not a current pass or a current finding disposition. The
[0.0.12 release review](../knowledge/reviews/releases/2026-10-13/release-0.0.12-beta.md)
also carries live-acceptance limits. Reconcile this evidence before claiming
that only visual acceptance remains.

## Task ledger

| ID | Delivered evidence / completion condition | Blockers | State |
| --- | --- | --- | --- |
| CTA-001 | Record current revision, Python and .NET toolchains, focused source/core/database/UI test results, relevant compiled builds, and package contents for both Revit runtime families. Reconcile the historical palette-test failure and affected audit findings with present source; unresolved failures remain explicit blockers. | None; execution needs the documented Windows/.NET/Revit references. | Not run |
| CTA-002 | Record owner-provided disposable projects, local family fixtures, checklist/settings/catalog/seed inputs, exact installed Revit versions, and a host-run checklist linked to the SPEC boundaries. Keep workstation paths and private project content out of Git. | CTA-001; fixture owner and live hosts. | Not run |
| CTA-003 | Record Family Studio assembly loading, FS-1 rendering at 100% and high DPI, keyboard/focus/Close behavior, search/filter/selection, load/place cancellation, batch success/failure rollback, and refresh issues against the owning SPEC. Include screenshots and actual results. | CTA-001, CTA-002. | Not run |
| CTA-004 | Record Startup Importer SI-1/SI-2/SI-3/SI-6 rendering and interaction, valid and invalid intake, blocked IDs, existing-target skips, supported imports, cancellation, and failed transaction rollback against the owning SPEC. Include screenshots and actual results. | CTA-001, CTA-002. | Not run |
| CTA-005 | Link completed evidence from the command SPEC validation records, reconcile remaining limits, and record the owner's acceptance decision. Implementation, host acceptance, and release/promotion remain separate states. | CTA-003, CTA-004; owner review. | Not run |

CTA-003 and CTA-004 have independent execution scopes after their prerequisites.
This plan records dependencies; it does not select automated delegation.

## Verification and recovery

Discover current commands from the [contributor guide](../CONTRIBUTING.md),
[repository test instructions](../../README.md#test-locally), and tool project
files. Historical exact commands and environments are documented in the dated
validation record; check them before reuse. Run focused tests for
`src/KLCode.Wpf`, `src/KLCode.FamilyStudio`, and `src/KLA.ModelStartupImporter`
as applicable, and separately verify the host-specific packaging targets.
Only release work invokes the gates required by the
[release workflow](../../docs.ai/RELEASING.md).

Keep live mutation tests in disposable projects, preserve the create-only and
transaction rollback boundaries, and retain prior known package/source
checkpoints. A failed check stays failed or unavailable in this ledger until
new evidence resolves it; documentation filing does not waive a prerequisite.

## Prior context

The [plan archive](archive/README.md) owns the preserved implementation history.
The [design package](../knowledge/handoffs/family-studio-startup-importer/README.md)
contains the original prototypes. Handoffs link to this ledger for current
task status rather than maintaining another completion list.
