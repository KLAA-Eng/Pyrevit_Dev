# Independent Tool Versions and Metadata

Every visible command, including DevSandbox, follows this standard. The
extension release in `version.json` remains independent and authoritative for
extension packaging and releases; follow [RELEASING.md](RELEASING.md).

## Version decisions

Tool versions describe meaningful command changes delivered to `main`, not the
number of development commits. Reconstruct history by comparing adjacent main
release snapshots in the [Tool-Version Delivery Ledger](tool-version-delivery-ledger.md).
This is essential because a squash release can deliver `dev` content without
preserving the original development commit as a mainline ancestor.

| Command status | First delivered version | Later version rule |
| --- | --- | --- |
| KL&A-maintained production command | `v1.0` | One minor increment for each meaningful main delivery affecting the command. |
| KL&A DevSandbox prototype | `v0.0` | One `v0.x` minor increment for each meaningful main delivery; promotion to production establishes `v1.0`. |
| Imported command with unchanged functionality | Evidenced source version, e.g. `v1.2.EFTools` | Remains special until a KL&A functional change. |
| First KL&A functional change to an import | `v1.0` or `v0.0` | Preserve upstream provenance in the SPEC, then follow the local lifecycle. |

A main delivery changes a tool when the release alters its user-observable
behavior, correctness, safety, compatibility, generated output, performance,
or workflow. A meaningful change to a listed shared helper also counts.
Formatting, metadata normalization, tests, documentation, release packaging,
and path-only relocations do not increment a version. A major increment is
reserved for an intentional, documented breaking redesign.

Each version table row is one delivery even when that release contains several
related changes. A command may have only one row per main delivery. Preserve a
single tool identity and path aliases through moves or renames.

### Planned versions on `dev`

When meaningful work exists on `dev` but is absent from the latest main
delivery, show the **next planned** version now. Add `Status: Unreleased` to
the bundle tooltip and use the latest meaningful development-change date in
`MM.DD.YYYY` form. Keep all pending changes under that one planned version.
Before the `dev` to `main` release, convert the row to the new delivery
identifier and replace the status with the intended delivery date. Verify the
merged main commit afterward as described by the central ledger.

## Script and bundle ownership

Python command scripts retain these two literal metadata assignments:

```python
__title__ = "Room Readiness Audit"
__version__ = "v1.0"
```

The version contains no label, date, or extension release channel. Do not assign
`__author__` or `__doc__` in command scripts. Function and class docstrings
remain normal code documentation. Other required pyRevit execution settings are
unaffected by this metadata rule.

`bundle.yaml` owns the matching title, author attribution, and tooltip. Preserve
existing execution settings and other metadata. A localized title uses `en_us`
for the script-title comparison; preserve other translations. Use a literal YAML
block (`|`) for the tooltip to retain line breaks:

```yaml
title: Room Readiness Audit
author: KL&A
tooltip: |
  Version: v1.1
  Date: 10.02.2026
  Status: Unreleased
  _____________________________________________________________________
  Description:

  Inspect rooms in the active model and report missing Department values.
  This command does not modify the model.
  _____________________________________________________________________
  How-to:

  -> Open a project and click the button.
  -> Review the pyRevit output report.
  _____________________________________________________________________
  Last update:
  - [10.02.2026] v1.1 - Planned correction for Department validation.
```

For a released command, omit `Status: Unreleased`; `Date` is the main-delivery
date from the ledger. The tooltip displays only the current version's compact
summary. It must not include an Author line. For URL and compiled commands
without `script.py`, the SPEC tool version supplies the version that the bundle
tooltip displays.

## Adjacent SPEC and Git evidence

Every `SPEC.md` identity section includes:

- `Tool ID` — stable lower-case identifier that survives a bundle rename.
- `Path aliases` — current and historical bundle paths needed to trace delivery
  snapshots.
- `Version inputs` — command files plus owned/shared helpers whose meaningful
  changes affect this command.
- `Tool version` and `Status/origin`.

Maintain a `Tool version history` table:

| Version | Main delivery | Date | Meaningful change | Git evidence |
| --- | --- | --- | --- | --- |
| `v1.0` | `0.0.7` | 09.28.2026 | Delivered the initial maintained workflow. | `2c4a3b2`; delivery snapshot diff. |
| `v1.1` | `Unreleased` | 10.02.2026 | Planned safety correction. | `abc1234`; pending next main delivery. |

For released rows, `Main delivery` must be an identifier in the central ledger
and the date must match it. For a planned row, it must be `Unreleased`, and the
tooltip must use `Status: Unreleased`. Record a compact user-impact summary;
the root [CHANGELOG.md](../../CHANGELOG.md) remains the concise extension-release
summary rather than a duplicate tool history.

## Static validation

Run `python scripts/check_tool_metadata.py`. It scans visible command bundle
directories in `KL&A Tools_dev.tab` or `KL&A Tools.tab`, including DevSandbox.
Underscore-prefixed directories are excluded because pyRevit hides templates.
The canonical `_Templates/_Template.pushbutton` is checked separately by the
focused tests so new commands start with conforming metadata.

The check verifies title equality, pure tool versions, matching tooltip and
SPEC versions, bundle authors, valid `MM.DD.YYYY` dates, release-ledger
references, unreleased-status rules, required tooltip sections, prohibited
script metadata, and SPEC identity/history fields. It supports scalar, English
localized, and literal-block metadata forms without importing Revit or requiring
a YAML package. It cannot classify a change as meaningful or prove live Revit
behavior; release review establishes those facts.
