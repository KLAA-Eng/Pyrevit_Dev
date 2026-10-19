# Agent reference documentation

The repository's only agent instruction file is [root AGENTS.md](../AGENTS.md).
Use this index for documentation ownership and release governance.
[docs/README.md](../docs/README.md) maps contributor guides, active plans, and
durable knowledge. Coding guides, reviews, and handoffs are filed under
`docs/knowledge/`; prior plans are filed under `docs/plans/archive/`.

## Documentation ownership and routing

Each fact has one authoritative owner. Update that owner when behavior or work
changes, and link to it from other documents. KLCode workflows use these project
locations rather than creating a parallel documentation structure.

| Role | Authoritative owner and location |
| --- | --- |
| Command behavior | The command's adjacent `SPEC.md` owns its behavior contract, limits, and acceptance criteria. Keep specifications beside their bundles. |
| Tasks and completion | One named plan in [docs/plans/](../docs/plans/README.md), or an explicitly selected tracker, owns each effort's tasks, blockers, completion status, and acceptance decisions. If a tracker owns tasks, the plan links to it. |
| Durable knowledge | [docs/knowledge/](../docs/knowledge/README.md) holds reusable research, domain vocabulary, coding guides, onboarding, and verification references. Contributor and design-system guides remain in `docs/`. |
| Handoffs | New `docs/knowledge/<topic>-handoff.md` documents summarize verified progress and link to the owning SPEC, plan or tracker, decisions, and evidence. They are dated snapshots, not a second task ledger. |
| Historical evidence | Dated records under [docs/knowledge/reviews/](../docs/knowledge/reviews/README.md) own the checks, findings, and review outcomes for their recorded baseline. Current plans link to that evidence when applicable. |
| Significant decisions | A named `docs/knowledge/<topic>-decision.md` record owns consequential design rationale, with an owner, date, status, alternatives, and consequences. Plans and handoffs link to it; successor records preserve and supersede earlier decisions. |
| Release governance | [RELEASING.md](RELEASING.md) owns release procedure; [TOOL_VERSIONING.md](TOOL_VERSIONING.md) owns tool-version policy; the [delivery ledger](releasing/tool-version-delivery-ledger.md) owns main-delivery evidence. |

The Family Studio and Startup Importer plans are preserved in the
[plan archive](../docs/plans/archive/README.md). Their command-level `PLAN.md`
files are navigation pointers. The [compiled-tools follow-up plan](../docs/plans/compiled-tools-acceptance.md)
owns the remaining verification tasks; archived status statements and the
handoff snapshot do not declare current completion. The original design assets
remain together in the [design reference package](../docs/knowledge/handoffs/family-studio-startup-importer/README.md).

For another resumed effort, verify prior claims against current source and
select one active plan or tracker. Preserve old evidence and explicitly link
superseded task/status sections to that authority.

## Folder map

| Location | What to use it for |
| --- | --- |
| [docs/plans/](../docs/plans/README.md) | Active implementation plans and the selected task authority for each effort. |
| [docs/knowledge/](../docs/knowledge/README.md) | Durable knowledge, significant decisions, and new handoff snapshots. |
| [Python and pyRevit guide](../docs/knowledge/python-pyrevit.md) | Python and pyRevit command structure. |
| [Comment guide](../docs/knowledge/python-comments.md) | Comments, docstrings, and command documentation style. |
| [RELEASING.md](RELEASING.md) | Authoritative extension release workflow. |
| [TOOL_VERSIONING.md](TOOL_VERSIONING.md) | Independent command versions and metadata rules. |
| [releasing/tool-version-delivery-ledger.md](releasing/tool-version-delivery-ledger.md) | Mainline delivery evidence used by command version histories. |
| [2026-10-05 technical review](../docs/knowledge/reviews/2026-10-05/README.md) | Comprehensive technical audit, finding register, validation plan, and evidence files. |
| [Design-system reviews](../docs/knowledge/reviews/design-system/README.md) | Dated GUI and design-system source reviews. |
| [Release and promotion reviews](../docs/knowledge/reviews/releases/README.md) | Dated tool-promotion and release review records. |
| [Plan archive](../docs/plans/archive/README.md) | Prior V1 and green-window implementation plans, retained as historical context. |
| [Compiled-tools handoff](../docs/knowledge/family-studio-startup-importer-handoff.md) | Recorded 2026-09-01 source/build evidence and remaining live checks. |
| [Compiled-WPF decision](../docs/knowledge/compiled-wpf-decision.md) | Recorded adapter decision, alternatives, and historical validation matrix. |
| [Design reference package](../docs/knowledge/handoffs/family-studio-startup-importer/README.md) | Original HTML prototypes, design notes, and supporting assets. |

Read the relevant command's adjacent `SPEC.md` and current source before using
a dated review or handoff as implementation guidance. Historical branch names,
paths, and baselines describe the repository at the time of review; findings
and plans are evidence, not automatic authorization to change code.
