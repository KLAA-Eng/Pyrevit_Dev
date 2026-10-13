# 0.0.11 beta release review

- **Review date:** 2026-10-12
- **Release identity:** `0.0.11`, beta; intended tag `v0.0.11-beta`
- **Comparison:** `origin/main` at `74eccba29c1a8a8b6443baab0caf9a2f5ccf66e8` through release preparation commit `3638bfc7cbacf421ccdde5023ca05400d57d7c5c` and this review record on `dev`
- **Owner handoff:** The designated release owner reviews and merges the `dev` to `main` PR. The tag and prerelease are created only after verifying the merged `main` tree.

## Reviewed delivery

- **Core rename:** Views and Sheets use the promoted workflows, with case conversion, unchecked pickers without element IDs, exact-value conflict handling, and in-dialog results. The shared `lib/find_replace/` workflow and selection helper are included in the version inputs. See the adjacent command SPECs and [promotion review](../2026-10-08/find-replace-promotion.md).
- **Beam Reaction Declutter:** The DevSandbox prototype adds active-view and selected-sheet scopes, same-beam collision handling, bounded movement, and transaction failure protection. See its adjacent SPEC and [promotion review](../2026-10-08/beam-reaction-declutter-promotion.md).
- **ViewRange:** The editor changes table labels, text sizes, alignment, and spacing. Its adjacent SPEC records the intended layout and validation boundary.
- **UI Gallery:** The current Core rename windows are previewed; the prior forms remain labeled as legacy. Its adjacent SPEC records the launcher and safe-preview boundaries.
- **Release support:** The release check now handles both ribbon layouts. About KL&A Tools distinguishes version identity from the metadata source commit. The `0.0.10` delivery history remains intact.

The five changed command versions are recorded once for main delivery `0.0.11` in their SPEC histories. The production `KL&A Tools.tab` layout contains 34 visible bundles; the hidden template remains an unreleased example.

## Validation and limits

- `scripts/release_check.py` passed on the prepared commit: 238 tests, one existing skip, 34 visible command bundles with zero metadata errors, and zero failed gates.
- The release check includes working, staged, and `origin/main...HEAD` whitespace checks plus version/build/changelog/ledger consistency. Generated `lib/build_info.py` identifies `v0.0.11-beta` and its source commit.
- There is **no new live Revit or Excel claim**. Core rename transactions and dialogs, ViewRange rendering, UI Gallery previews, and Beam Reaction Declutter movement and Reset behavior still need representative host acceptance. The prototype remains in DevSandbox. Carbon GWP Pull retains its documented Excel COM limits.
- Previous published rollback tag: `v0.0.10-beta`.

This is a beta preparation record. After owner merge, verify the exact main tree, annotated tag and peeled SHA, published prerelease page, installed path, and About dialog. Record the verified delivery evidence on `dev` during synchronization to `0.0.12-dev`.

## Publication verification

PR #23 was owner-merged on 2026-10-12 as `ea6219c3a45dcf93e7ba80f2d02c9a54f48409b4`. The main tree matched the prepared release tree. The remote annotated `v0.0.11-beta` tag peeled to that commit, and the [GitHub prerelease](https://github.com/KLAA-Eng/Pyrevit_Dev/releases/tag/v0.0.11-beta) displayed the expected title, beta label, tag, commit, and notes. A Revit 2024.3.50 MCP listener responded, but its own extension path did not establish which KL&A Tools copy Revit had loaded. A pyRevit reload and manual About/loaded-path inspection remain pending.
