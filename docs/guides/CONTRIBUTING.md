# Contributing to KL&A Tools

This guide explains how every team member contributes safely to the pyRevit
extension. It is written for contributors who may not write code as well as
technical maintainers.

## Roles and access

Everyone may access the GitHub repository, create a topic branch, open a pull
request, review documentation, report an issue, and provide validation
evidence. The technical owner and backup reviewer alone may merge pull
requests, prepare releases, and create or push release tags.

Ordinary contributors use PRs into `dev`. The release owner may prepare releases
and the next development cycle directly on `dev`. Releases reach `main` only
through a `dev` to `main` PR personally merged by the release owner; never push
directly to `main`. See the [release workflow](../releasing/RELEASING.md).

## Day-to-day change flow

1. Start from current `dev` and create a short-lived topic branch.
2. Make one focused change. Read the affected command's `SPEC.md` and
   `bundle.yaml` before changing a command.
3. Update `SPEC.md` for every new or materially changed user-facing command.
   Record meaningful development work as the next planned tool version. During
   release preparation, convert it to the matching main-delivery version,
   tooltip date, and SPEC history row together.
4. Run the narrowest relevant automated or static checks, then record the
   result in the pull request.
5. Record relevant live Revit evidence and remaining acceptance limits for
   changed behavior. Beta releases may retain documented limits; stable promotion
   requires relevant live acceptance as defined in the release workflow.
6. Open a pull request into `dev`. State the affected tools, user impact,
   evidence, known limits, and rollback considerations.
7. The technical owner or backup reviewer reviews and merges the approved pull
   request into `dev`.

## Revit support and validation

The extension targets Revit 2024 and later. A release may claim support only
for exact Revit versions where the changed behavior has live evidence. A beta may
proceed with documented testing limits and passing release checks. Prior
evidence can carry forward only when the relevant command did not change.

Automated tests and static checks are valuable but do not prove host behavior.
Live validation must cover the relevant model transaction, native dialog,
external application, file output, and user workflow boundary. Independent
non-developer feedback is encouraged but is not a mandatory release gate.

## Command specifications

Use the adjacent `SPEC.md` as the team-facing command contract. It explains
the workflow, inputs, effects, limitations, requirements, compatibility,
validation evidence, release history, and backlog. Use the DevSandbox command
template for a new command. All visible commands, including DevSandbox, must
record Tool ID, Path aliases, Version inputs, Tool version, Status/origin, and
a history with Version, Main delivery, Date, Meaningful change, and Git
evidence. Follow
[Tool version rules](../releasing/TOOL_VERSIONING.md) for the exact metadata and version rules.

Run `python scripts/check_tool_metadata.py` to check visible command metadata.
Its host-independent tests run with
`python -m unittest discover -s tests -p tool_metadata_test.py`.

## Release flow

Follow the authoritative [release workflow](../releasing/RELEASING.md) for
preparation, checks, the owner's merge, tagging, GitHub publication, live
verification, and the next development cycle. It defines roles, beta/stable gates,
and extension identity; this guide does not maintain a second release checklist.

## Where to find help

- Team policy and plain-language navigation: the KLCode Standards Notion page.
- Command behavior and validation: the adjacent `SPEC.md`.
- Python and pyRevit code shape: [SCRIPTS.md](SCRIPTS.md) and
  [COMMENTS.md](COMMENTS.md).
- Published release record: [CHANGELOG.md](../../CHANGELOG.md).
