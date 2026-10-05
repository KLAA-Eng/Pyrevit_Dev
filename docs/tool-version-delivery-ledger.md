# Tool-Version Delivery Ledger

This is the canonical record of **mainline extension deliveries** used when
calculating independent command versions. It is not a replacement for the
extension [CHANGELOG.md](../CHANGELOG.md): that file is the concise release
summary, while this ledger supplies the release boundaries used by each
command's `SPEC.md` version history.

## How to use this ledger

- A released tool-version row names one `Main delivery` value from this table.
  A command increments at most once per delivery, even if the release contains
  several related commits.
- Compare file snapshots at adjacent main deliveries. Do not use development
  commit ancestry alone: the repository includes both merge and squash-style
  releases.
- `Unreleased` is reserved for a next planned command version on `dev`; it is
  not a delivery and is intentionally absent from this table.
- Keep a command's aliases and version inputs in its `SPEC.md`. This lets the
  release review account for renames and shared helper changes.

## Mainline deliveries

| Main delivery | Main commit | Delivery date | Extension version | Tag / release evidence | Delivery form |
| --- | --- | --- | --- | --- | --- |
| `0.0.0.beta` | `484924b` | 07.16.2026 | `0.0.0.beta` | Initial versioned baseline; no tag | Direct main snapshot |
| `0.0.1.beta` | `78b2aee` | 08.13.2026 | `0.0.1.beta` | PR #8; version bump `114c09e` | PR merge |
| `0.0.2.beta` | `ca09b3f` | 08.13.2026 | `0.0.2.beta` | PR #9; version bump `d0cdc9d` | PR merge |
| `0.0.3.beta` | `d1e0c69` | 08.13.2026 | `0.0.3.beta` | PR #13; version bump `1918b4b` | PR merge |
| `0.0.4.beta` | `1f3dd23` | 08.17.2026 | `0.0.4.beta` | PR #14; tag `v0.0.4.beta` peels to `a397195` | PR merge |
| `0.0.5.beta` | `8cd45f8` | 08.20.2026 | `0.0.5.beta` | Release #15; no tag | Squash-style release |
| `0.0.6beta` | `300f8d4` | 09.15.2026 | `0.0.6beta` | Release #17; tag `v0.0.6beta` | Squash-style release |
| `0.0.7` | `2c4a3b2` | 09.28.2026 | `0.0.7` | Release #18; tag `v0.0.7-beta` | Squash-style release |
| `0.0.8` | `34c41bc` | 09.28.2026 | `0.0.8` | Release #19; tag `v0.0.8-beta` | Squash-style release |
| `0.0.9` | `d7185d2` | 10.01.2026 | `0.0.9` | Release #20; tag `v0.0.9-beta` | Squash-style release |

## Release-preparation handoff

Before a `dev` to `main` release, convert every affected command's planned
row from `Unreleased` to the new delivery identifier, replace `Status:
Unreleased` in its tooltip with the intended delivery date, and add the new
row here. After merge, verify the actual main commit and release tag evidence.
The root changelog records the release summary; command specifications retain
the detailed tool-version history.
