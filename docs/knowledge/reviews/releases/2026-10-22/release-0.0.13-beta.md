# 0.0.13 beta release review

- Review date: 2026-10-22
- Approved identity: 0.0.13 beta; next development identity: 0.0.14 dev.
- Owner: user confirmed release ownership and will personally merge the PR.
- Baseline: main `8b83e6a0a2698bdeaa91084d7326de193a595b23`; development `2026d02f5c951d8f3be357e0d3052b55f669cb23` plus release preparation.

## Reviewed delivery

Carbon GWP Pull v1.1 saves successfully refreshed post-processing workbooks and
refuses read-only opens. Shared Excel loading validates an Office 16 interop
assembly, supports an already loaded namespace, and preserves macro-security
typing. Shared-helper consumers Concrete Mix Header v0.2 and Steel PSF v0.6
advance once for this delivery. Excel COM Smoke Test v0.2 expands assembly and
startup diagnostics. Documentation organization and the production ribbon
rename preserve command behavior.

## Validation and limits

The consolidated release check passed: 260 tests, one skip, 34 visible bundles,
zero metadata errors, and zero failed gates. Whitespace checks passed. This is
host-independent validation.

Existing command SPEC evidence records complete disposable Excel smoke passes
on affected Revit 2025 and 2026 workstations on 2026-10-22. Release preparation
adds no new live Revit claim. Carbon workbook refresh, persisted values, chart
placement, transactions, undo, and reopening remain pending, as do tool-specific
Concrete Mix Header and Steel PSF acceptance and prior beta limits.

Rollback: `v0.0.12-beta`. About/loaded-path verification pending.

## Publication and synchronization

The owner merged [PR #26](https://github.com/KLAA-Eng/Pyrevit_Dev/pull/26) as
`9fa18cd6378f816776929156e4865b7d7af82e6a`. Its tree exactly matched the
validated preparation at `a7e63fd`. The remote annotated `v0.0.13-beta`
(tag object `aee90b2325c8adb28acd3031541a9201ef7ac200`) peels to that main
commit. The [GitHub prerelease](https://github.com/KLAA-Eng/Pyrevit_Dev/releases/tag/v0.0.13-beta)
was verified on 2026-10-22 with the approved title, Pre-release label, tag,
commit, notes, acceptance limits, and rollback tag.

The main result was merged back into master-dev, the development ribbon restored,
and 0.0.14-dev metadata generated. The resolved ledger and delivery check
record this release. About/loaded-path verification and the live acceptance
limits above remain pending. No 0.0.14 development tag or release is intended.
