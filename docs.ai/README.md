# Agent reference documentation

The repository's only agent instruction file is [root AGENTS.md](../AGENTS.md).
Use this folder when a task needs a specific coding standard, release procedure,
review record, or implementation handoff. [docs/README.md](../docs/README.md)
maps the human-facing documentation.

## Folder map

| Location | What to use it for |
| --- | --- |
| [SCRIPTS.md](SCRIPTS.md) | Python and pyRevit command structure. |
| [COMMENTS.md](COMMENTS.md) | Comments, docstrings, and command documentation style. |
| [RELEASING.md](RELEASING.md) | Authoritative extension release workflow. |
| [TOOL_VERSIONING.md](TOOL_VERSIONING.md) | Independent command versions and metadata rules. |
| [releasing/tool-version-delivery-ledger.md](releasing/tool-version-delivery-ledger.md) | Mainline delivery evidence used by command version histories. |
| [reviews/2026-10-05/](reviews/2026-10-05/README.md) | Comprehensive technical audit, finding register, validation plan, and evidence files. |
| [reviews/design-system/](reviews/design-system/README.md) | Dated GUI and design-system source reviews. |
| [reviews/reviews/](reviews/reviews/README.md) | Dated tool-promotion and release review records. |
| [handoffs/design_handoff_family_studio_startup_importer/](handoffs/design_handoff_family_studio_startup_importer/README.md) | Implementation plans, status notes, HTML design references, and their assets. |

Read the relevant command's adjacent `SPEC.md` and current source before using
a dated review or handoff as implementation guidance. Historical branch names,
paths, and baselines describe the repository at the time of review; findings
and plans are evidence, not automatic authorization to change code.
