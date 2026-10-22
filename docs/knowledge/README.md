# Durable knowledge

Use this folder for reusable research, domain vocabulary, onboarding,
verification references, significant decisions, and new handoff snapshots.
Follow the [documentation ownership table](../../docs.ai/README.md#documentation-ownership-and-routing).
Link existing standards and evidence rather than copying them into this tree.

Use descriptive filenames such as `<topic>.md`, `<topic>-decision.md`, and
`<topic>-handoff.md`. Create documents only when there is useful knowledge to
preserve.

Significant decision records identify the owner, date, status, context,
alternatives, decision, rationale, and consequences. Distinguish proposals from
accepted decisions. Preserve superseded records and link their successors;
routine implementation details do not require a separate decision record.

Handoffs record their date and source revision or working state, summarize
verified results and limitations, and link the authoritative SPEC, plan or
tracker, decisions, and evidence. Include the next concrete action and unresolved
questions. On resume, verify consequential claims against current source and
the [active plan or tracker](../plans/README.md); update task status only there.

## Filed knowledge

| Source | Owns |
| --- | --- |
| [Python and pyRevit guide](python-pyrevit.md) | Living command structure and IronPython-compatible Python conventions. |
| [Comment guide](python-comments.md) | Living comments, docstrings, and command-documentation conventions. |
| [Design-system guide](../DESIGNSYSTEM.md) | Living UI tokens, resources, and component inventory. |
| [Review archive](reviews/README.md) | Dated audits, release reviews, promotion reviews, and their evidence. |
| [Compiled-WPF decision](compiled-wpf-decision.md) | Recorded compiled adapter rationale, alternatives, and source-checkpoint validation. |
| [Compiled-tools handoff](family-studio-startup-importer-handoff.md) | The 2026-09-01 implementation snapshot; follow its linked plan for task status. |
| [Design reference package](handoffs/family-studio-startup-importer/README.md) | Original Family Studio and Startup Importer prototypes, design notes, and assets. |

The [plan archive](../plans/archive/README.md) preserves the corresponding
proposals and execution baselines. Dated evidence retains its observation
date, revision, and limits after filing; moving it does not refresh its claims.
