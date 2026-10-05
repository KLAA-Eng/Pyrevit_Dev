# Releasing KL&A Tools

This procedure controls every release from protected `dev` into protected
`main`. Only the designated technical owner or backup reviewer may merge the
release pull request or create and push a release tag.

## Release authority

`version.json` is the one human-edited extension version source.
`lib/build_info.py` is generated from it and must never be edited by hand.
`CHANGELOG.md` is the canonical release record.

Use numeric semantic versions for every new release:

- `MAJOR` — a breaking user workflow, compatibility, or platform change.
- `MINOR` — a new compatible tool or meaningful compatible feature.
- `PATCH` — a compatible fix or small maintenance improvement.

The release channel is separate. Releases are `beta` by default and become
`stable` only through explicit promotion by the technical owner or backup.
Use `vMAJOR.MINOR.PATCH-beta` tags for beta releases and
`vMAJOR.MINOR.PATCH` tags for stable releases. Existing legacy tags remain
unchanged.

Example beta release:

```json
{
  "version": "0.1.0",
  "channel": "beta",
  "release_date": "2026-09-28"
}
```

## Development identity

`dev` is an untagged, unpublished development identity, not a release channel.
After a published beta or stable release is synchronized back into `dev`, advance
`version.json` to the next numeric version with `"channel": "dev"` and
regenerate `lib/build_info.py`. About will display the fallback identity as
`vMAJOR.MINOR.PATCH-dev`, but that identifier must not receive a Git tag or a
GitHub release. Keep the latest published beta or stable release as the most
recent changelog release.

## Prepare the release on dev

1. Confirm the release contains only reviewed work already merged into `dev`.
2. Review the affected command `SPEC.md` files. New or materially changed
   commands must document their workflow, effects, compatibility, validation,
   release history, and backlog.
3. Record the release in `CHANGELOG.md`: version, date, channel, affected
   tools, user-facing changes, fixes, known limits, tested Revit range, and
   rollback tag.
4. Update `version.json` with the numeric version, channel, and release date.
5. Regenerate build metadata:

   ```powershell
   C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy Bypass -File .\scripts\generate_build_info.ps1
   ```

6. Commit `version.json`, `lib/build_info.py`, and `CHANGELOG.md` with the
   release preparation.

## Validate the release

Every release pull request must state the affected tools and include the
applicable evidence:

- Focused host-independent checks for deterministic logic, where practical.
- Static or audit checks appropriate to the changed bundles and metadata.
- Live Revit evidence for each Revit version the changed command claims to
  support. The design target is Revit 2024 and later; a release may claim only
  versions explicitly tested for its changed behavior.
- A `SPEC.md` update when the command's workflow, output, effects, limits,
  dependencies, or validation boundary changed.

Automated checks do not prove Revit transactions, native dialogs, Excel COM,
file outputs, or user workflow. Independent non-developer testing is welcomed
but is not a required release gate.

## Merge, tag, and verify

1. Open the controlled `dev` to `main` pull request. The technical owner or
   backup reviewer reviews and merges it only after all release evidence is
   complete.
2. Fetch `origin/main` and verify the exact merged commit.
3. Create and push the matching annotated tag on that `main` commit. Use the
   channel-specific tag format above.
4. Deploy through the established distribution process.
5. Reload pyRevit and open **KL&A Tools > Outreach > About KL&A Tools**.
   Confirm the extension version, channel, Git tag, Git SHA, and loaded
   extension path. The loaded path is the decisive support check: it confirms
   which `.extension` folder Revit is using.
