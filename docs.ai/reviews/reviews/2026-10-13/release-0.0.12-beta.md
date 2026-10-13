# 0.0.12 beta release review

- **Review date:** 2026-10-13
- **Release identity:** `0.0.12`, beta; intended tag `v0.0.12-beta`
- **Comparison:** `origin/main` at `ea6219c3a45dcf93e7ba80f2d02c9a54f48409b4` through `master-dev` at `9570018c510f2eefd6cf9b6b17831384d29a4522` plus this preparation
- **Owner handoff:** The designated release owner reviews and personally merges the `master-dev` to `main` PR. Tag and publish only after verifying the merged `main` result.

## Reviewed delivery

- Hide/Unhide Revision Clouds reports each selected sheet whose schedule changed and which selected revisions were added or removed. It distinguishes those results from additional-revision edits and reports unreadable schedule state. Command source, bundle, SPEC, and focused tests changed in `9b1ca77` and `9570018`.
- Excel COM Smoke Test reports the first short-name interop assembly lookup error and the identity and location of a loaded assembly. A lookup failure is diagnostic; existing fallback and temporary-file cleanup behavior remain governed by the command's SPEC. Command source, bundle, and SPEC changed in `25c3e39`.
- Contributor and agent documentation moved to `docs/` and `docs.ai/`. The metadata checker was repaired to use the moved delivery ledger. The production ribbon layout is `KL&A Tools.tab`.
- The two affected command versions advance once for delivery `0.0.12`: Core Revision Clouds to `v1.1` and the DevSandbox Excel diagnostic to `v0.1`. No other command version advances for documentation, tests, or layout changes.

## Validation and limits

- The consolidated release check passed on the prepared working tree: 248 tests, one existing skip, 34 visible command bundles with zero metadata errors, and zero failed gates. Working, staged, and release-delta whitespace checks passed.
- There is **no new live Revit or Excel claim**. The revision schedule report still needs comparison with visible titleblock entries after Hide and Unhide in representative models, including clouds on sheets and placed views, unchanged sheets, cancellation, and already-correct states. The Excel diagnostic still needs runs in the intended Revit and Excel hosts.
- The prior `0.0.11-beta` live-acceptance limits remain open. The previous published rollback tag is `v0.0.11-beta`.

This is a beta preparation record. After the owner merge, verify the exact main tree, annotated tag and remote peeled SHA, published prerelease page, installed extension path, and About dialog. Resolve the pending ledger row on `master-dev` while preparing `0.0.13-dev`.
