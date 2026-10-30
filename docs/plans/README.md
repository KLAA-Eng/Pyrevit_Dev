# Active plans

Use `docs/plans/<topic>.md` for new plans and resumed efforts that need a
durable breakdown. Small, obvious changes do not require a plan document.
Follow the [documentation ownership table](../../docs.ai/README.md#documentation-ownership-and-routing).

Each effort names one task authority: its plan's task ledger or an explicitly
selected tracker. If a tracker owns tasks, link it from the plan and keep task
completion there.

A plan records its goal and scope, links to the owning command `SPEC.md` files,
and identifies dependencies, significant decisions, verification, and recovery
where relevant. Its task ledger uses stable task IDs and records delivered
behavior, related acceptance criteria, blockers, status, completion conditions,
and evidence links. Distinguish implementation complete, locally verified,
live Revit acceptance, and remote integration.

For resumed work, verify prior claims against current source, link earlier
plans or handoff packages, and mark their task/status sections as superseded
by the selected authority. Preserve prior evidence. Handoffs belong in
[knowledge](../knowledge/README.md) and link back to the active authority.

## Plan index

| Plan | Role |
| --- | --- |
| [Compiled-tools acceptance](compiled-tools-acceptance.md) | Task authority for re-establishing current evidence and completing Family Studio/Startup Importer host acceptance. |
| [Section Detailer](section-detailer.md) | Task authority for the DevSandbox tool that overlays detail components on a live section. |
| [Historical plans](archive/README.md) | Prior V1 and green-window plans; retained for rationale and provenance, not independent completion tracking. |
