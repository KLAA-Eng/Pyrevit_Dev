# Releasing KL&A Tools

This is the authoritative release workflow. Start here when asked to release an
extension version; the contributor guide and agent instructions link here.
Supporting command-version rules are in [TOOL_VERSIONING.md](TOOL_VERSIONING.md).
The [delivery ledger](tool-version-delivery-ledger.md) records release commits;
the root [changelog](../../CHANGELOG.md) records user-facing release notes.

## Responsibility and authorization

Ordinary contributions use topic branches and PRs into `dev`. The designated
release owner may prepare releases, repair release checks, synchronize `main`,
and prepare the next development version directly on `dev`. Do not push directly
to `main` or change branch protections to make a release possible.

The owner personally reviews and merges the `dev` to `main` PR. An assistant may
prepare the PR and perform explicitly authorized tagging, publication, and
post-release work. When the owner reports the merge, verify it and resume that
authorized work. Carry the approved version, channel, scope, and next development
version across handoffs; do not ask again for already granted authorization.
Stop for a new decision, a failed prerequisite, or a tool permission restriction.

## Identities and evidence

- `version.json` is the human-edited extension identity: numeric `MAJOR.MINOR.PATCH`,
  channel `dev`, `beta`, or `stable`, and an ISO date.
- `lib/build_info.py` is generated. Never edit it by hand.
- `dev` is an unpublished development identity such as `v0.0.11-dev`.
  It receives no Git tag or GitHub release. Its date records synchronization or
  development preparation.
- A beta uses an annotated `vX.Y.Z-beta` tag and a GitHub **Pre-release**.
  Stable uses `vX.Y.Z` and requires explicit promotion. Preserve legacy tags.
- About displays a **Version identity** and **Metadata source commit**. The source
  commit is the HEAD when metadata was generated, not the eventual squash-merge
  commit or the loaded checkout's current HEAD. The ledger records verified
  release commit/tag evidence; About does not require Git inside Revit.

`MAJOR` signals a breaking workflow/platform change; `MINOR` a compatible
feature; `PATCH` a compatible fix. Confirm the intended release version/channel
and next development version at the start rather than infer them from tool versions.
Tool versions advance once for meaningful changes delivered to main; consult
their SPEC history and listed shared version inputs, including DevSandbox.

## Ribbon layouts

Development uses `KL&A Tools_dev.tab`; the released tree on `main` uses
`KL&A Tools.tab`. Exactly one must exist in a checkout. Both retain the same
bundle hierarchy. Tests resolve the active layout rather than hard-code one.

During release preparation on `dev`, use:

```powershell
git mv -- "KL&A Tools_dev.tab" "KL&A Tools.tab"
```

After the released main result is merged back into `dev`, restore:

```powershell
git mv -- "KL&A Tools.tab" "KL&A Tools_dev.tab"
```

Review directory-rename conflicts explicitly. Keep SPEC path aliases for both
layouts and historical names; update current-path references and README links
when transitioning. A layout-only rename does not increment tool versions.

## 1. Prepare on dev

1. Confirm the checkout is clean or identify and preserve unrelated work. Fetch
   origin, verify the branch and alignment of local/remote `dev`, and review the
   complete `origin/main` to `dev` delta. Record any unresolved scope decision.
2. Confirm the release version, channel, next development version, and who will
   merge. Merge current `origin/main` into `dev` if needed; resolve only reviewed
   synchronization conflicts.
3. Use the production ribbon layout. Review every affected tool's SPEC and shared
   version inputs. Convert delivered planned rows to the release identifier/date,
   remove `Status: Unreleased` from matching tooltips, and retain historical rows.
   Keep live-validation limits separate from delivery status.
4. Add the release to `CHANGELOG.md`: channel/tag, affected commands, user-visible
   changes, actual live evidence or **no new live Revit claim**, known limits,
   and the previous published rollback tag. Update README release-status references.
5. Add a ledger row for the release with `Pending merge` and `Pending publication`;
   record intended tag and delivery date. Do not invent the future squash SHA.
6. Set `version.json` to the release version/channel/date and generate metadata:

   ```powershell
   .\.venv-rvt26\Scripts\python.exe scripts\generate_build_info.py
   ```

   The PowerShell generator remains available with `-RepoRoot` when Python is
   unavailable. Both anchor Git queries to the intended repository.
7. Run the consolidated check:

   ```powershell
   .\.venv-rvt26\Scripts\python.exe scripts\release_check.py
   ```

   This runs full discovery, the visible-command metadata audit, working/staged
   whitespace checks, and extension version/build/changelog/ledger consistency.
   It is read-only apart from ordinary test temporary files and Python caches.
   Preserve its actual counts and skip reasons; do not hard-code a previous test
   count as the expected number. It does not prove live Revit or Excel behavior.
8. Review the complete diff, commit only release-owned changes, and push `dev`.
   Check the complete release delta for whitespace too:

   ```powershell
   git diff --check origin/main...dev
   ```

## 2. Validate and hand off the release PR

Open a `dev` to `main` PR titled **Release X.Y.Z beta** (or stable). Include:

- Approved version/channel and affected tools, including shared-helper consumers.
- Release-check results and any existing skips; relevant live evidence.
- Precise limitations, rollback tag, and owner review/merge handoff.

Betas may proceed with passing automated checks and explicitly recorded live
testing limits. Claim compatibility only for exact environments with relevant
live evidence. Stable promotion requires live acceptance for the changed
workflow, transactions, UI, Excel/files, and other affected boundaries.
Independent non-developer feedback is welcome.

The owner personally merges the PR. Do not tag the development preparation
commit. If the PR head changes after validation, recheck the new scope and checks.

## 3. Verify main, tag, and publish

1. Fetch origin after the owner merges. Verify the PR's actual merge result,
   exact `origin/main` SHA, production layout, release identity, and approved tree.
   Squash merges create new commits; verify content rather than require dev-head
   ancestry. Stop if main contains unexpected work.
2. Create an annotated tag on that explicit verified SHA, then push only that tag:

   ```powershell
   git tag -a vX.Y.Z-beta VERIFIED_MAIN_SHA -m "Release X.Y.Z beta"
   git push origin vX.Y.Z-beta
   git ls-remote --tags origin vX.Y.Z-beta "vX.Y.Z-beta^{}"
   ```

   Require the remote peeled tag to match the verified SHA. If the tag already
   exists, verify it instead of replacing it; stop on a mismatch.
3. Publish **KL&A Tools X.Y.Z beta** on GitHub from that existing tag, using the
   changelog's user-facing notes and **Pre-release** label. Stable uses its stable
   title/tag without that label. Use authenticated CLI/API tooling when available;
   otherwise use the signed-in browser. Do not guess success from an attempted
   sign-in, push, or publish.
4. Verify the GitHub release title, channel label, tag, target commit, notes,
   and publication URL. Record evidence for the ledger.
5. Use the team's configured extension installation/distribution method. Reload
   pyRevit and inspect About's version identity, channel/date, metadata source
   commit, and loaded extension path. Verify the production extension path.
   If no live host is available, record **About/loaded-path verification pending**;
   do not infer that Revit is closed from an unavailable automation surface.
   Beta publication/synchronization can finish with this recorded follow-up.
   Required stable live acceptance must precede stable publication.

## 4. Synchronize and prepare the next dev cycle

1. Return to clean, aligned `dev`; merge the verified `origin/main` release
   result into it. Resolve only synchronization conflicts and retain release content.
2. Restore `KL&A Tools_dev.tab`. Resolve the ledger's pending row with the verified
   main SHA, PR/release links, tag evidence, and verification date. These records
   are completed on dev because the squash SHA cannot be embedded in its own commit.
3. Set `version.json` to the agreed next numeric version, `channel: "dev"`, and
   synchronization date. Regenerate build metadata. Leave the next version only
   under **Unreleased** in the changelog; keep the published release as the latest
   release entry. Update README identity/current-layout links.
4. Run the release check, including local delivery evidence:

   ```powershell
   .\.venv-rvt26\Scripts\python.exe scripts\release_check.py --delivery X.Y.Z
   ```

   This additionally checks the resolved ledger entry and annotated tag against
   local Git objects. External publication/remote verification remains step 3.
5. Review, commit, and push directly to `dev` as release owner. Fetch and verify
   remote dev contains the verified main release and has the next dev identity.
   Verify no next-version dev tag or GitHub release exists.
6. Report the release URL/tag/SHA, resulting dev SHA/identity, validation evidence,
   and any precise pending live verification.

## Completion and recovery

Completion requires a verified main result, remote annotated tag/peeled SHA,
published release page, resolved ledger evidence, synchronized remote dev,
next dev metadata, and recorded live-verification status.

On failure, identify the last verified phase and resume there. Inspect existing
PRs/tags/releases before retrying. Never republish, retag, force-push, or discard
unrelated changes as a shortcut. Fix a published documentation discrepancy on
dev and record its evidence; preserve the existing release tag unless the owner
explicitly directs a different recovery.
