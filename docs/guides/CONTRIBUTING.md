# Contributing to KL&A Tools

This guide explains how every team member contributes safely to the pyRevit
extension. It is written for contributors who may not write code as well as
technical maintainers.

## Roles and access

Everyone may access the GitHub repository, create a topic branch, open a pull
request, review documentation, report an issue, and provide validation
evidence. The technical owner and backup reviewer alone may merge pull
requests, prepare releases, and create or push release tags.

`dev` and `main` are protected branches. Direct pushes to either branch are not
allowed.

## Day-to-day change flow

1. Start from current `dev` and create a short-lived topic branch.
2. Make one focused change. Read the affected command's `SPEC.md` and
   `bundle.yaml` before changing a command.
3. Update `SPEC.md` for every new or materially changed user-facing command.
4. Run the narrowest relevant automated or static checks, then record the
   result in the pull request.
5. Perform and record live Revit validation when the change affects behavior,
   compatibility, UI, transactions, graphics, Excel, files, or external tools.
6. Open a pull request into `dev`. State the affected tools, user impact,
   evidence, known limits, and rollback considerations.
7. The technical owner or backup reviewer reviews and merges the approved pull
   request into `dev`.

## Revit support and validation

The extension targets Revit 2024 and later. A release may claim support only
for exact Revit versions where the changed behavior has live evidence. Prior
evidence can carry forward only when the relevant command did not change.

Automated tests and static checks are valuable but do not prove host behavior.
Live validation must cover the relevant model transaction, native dialog,
external application, file output, and user workflow boundary. Independent
non-developer feedback is encouraged but is not a mandatory release gate.

## Command specifications

Use the adjacent `SPEC.md` as the team-facing command contract. It explains
the workflow, inputs, effects, limitations, requirements, compatibility,
validation evidence, release history, and backlog. Use the DevSandbox command
template for a new command. Do not make migration-only edits to older specs;
bring them up to the current template when their command changes materially.

## Release flow

Only a controlled `dev` to `main` pull request produces a release. The release
preparation includes the semantic version, channel, generated build metadata,
changelog entry, validation evidence, and exact release tag. Beta is the
default channel; promotion to stable is explicit. Follow [RELEASING.md](../../RELEASING.md)
for the complete procedure.

## Where to find help

- Team policy and plain-language navigation: the KLCode Standards Notion page.
- Command behavior and validation: the adjacent `SPEC.md`.
- Python and pyRevit code shape: [SCRIPTS.md](SCRIPTS.md) and
  [COMMENTS.md](COMMENTS.md).
- Published release record: [CHANGELOG.md](../../CHANGELOG.md).
