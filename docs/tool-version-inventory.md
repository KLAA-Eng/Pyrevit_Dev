# Tool Version Inventory

This inventory covers every visible runnable command in `KL&A Tools_dev.tab`,
including `05 DevSandbox.panel`. Versions were reconstructed from the mainline
release snapshots in the [Tool-Version Delivery Ledger](tool-version-delivery-ledger.md),
not from development commit counts. `Planned` means meaningful work exists on
`dev` but has not reached `main`.

The adjacent `SPEC.md` is the authoritative command-level record: it contains
all version rows, path aliases, version inputs, and delivery evidence.

## Production and shared tools

| Command | Current tool version | Delivery / status | Status/origin |
| --- | --- | --- | --- |
| General Notes / Typical Details | `v1.0` | `0.0.0.beta` | Maintained KL&A custom |
| Launch Revit Standards | `v1.0` | `0.0.0.beta` | Maintained KL&A custom |
| Carbon GWP Pull | `v1.0` | Planned | KL&A; pending production promotion; delivered DevSandbox history `v0.0`–`v0.1` |
| Hide/Unhide Engineering Notes | `v1.1` | Planned | Maintained KL&A custom |
| Copy Legends to Other Documents | `v1.0.pyRevit` | `0.0.0.beta` | Special unchanged pyRevit import |
| Duplicate Sheets | `v1.0` | `0.0.6beta` | Maintained KL&A EF Tools adaptation |
| Highlight 2D | `v1.0` | `0.0.1.beta` | Maintained KL&A pyRevit adaptation |
| Find and Replace in Views | `v1.2.EFTools` | `0.0.0.beta` | Special unchanged EF Tools import |
| Find and Replace in Sheets | `v1.0` | `0.0.6beta` | Maintained KL&A EF Tools adaptation |
| Find All Revised Sheets | `v1.0.pyRevit` | `0.0.0.beta` | Special unchanged pyRevit import |
| Find All Revision Clouds | `v1.0` | `0.0.7` | Maintained KL&A pyRevit adaptation |
| Hide/Unhide Revision Clouds | `v1.0` | `0.0.7` | Maintained KL&A custom |
| Toggle off Revision Schedule | `v1.0` | `0.0.7` | Maintained KL&A pyRevit adaptation |
| Toggle on Revision Schedule | `v1.0` | `0.0.7` | Maintained KL&A pyRevit adaptation |
| Show View Range | `v1.0` | `0.0.6beta` | Maintained KL&A pyRevit adaptation |
| Who Did That? | `v1.0.pyRevit` | `0.0.0.beta` | Special unchanged pyRevit import |
| About KL&A Tools | `v1.1` | `0.0.1.beta` | Maintained KL&A custom |
| Prototype Request | `v1.0` | `0.0.4.beta` | Maintained KL&A internal derivative |
| Suggestions | `v1.0` | `0.0.0.beta` | Maintained KL&A custom |

## DevSandbox prototypes

| Command | Current tool version | Delivery / status | Status/origin |
| --- | --- | --- | --- |
| Launch Dynamo Player | `v0.0` | `0.0.4.beta` | KL&A prototype |
| Beam Reaction Declutter | `v0.0` | `0.0.7` | KL&A prototype |
| Concrete Mix Header | `v0.1` | Planned | KL&A prototype; delivered baseline `v0.0` in `0.0.6beta` |
| Create Detail Folders | `v0.0` | `0.0.4.beta` | KL&A prototype |
| Element Takeoff | `v0.0` | `0.0.0.beta` | KL&A prototype |
| Excel COM Smoke Test | `v0.0` | Planned | KL&A prototype; not yet delivered to main |
| Find and Replace in Views Prototype | `v0.0` | `0.0.6beta` | KL&A EF Tools adaptation |
| Find and Replace in Sheets Prototype | `v0.0` | `0.0.6beta` | KL&A EF Tools adaptation |
| Highlight Changed Elements | `v0.1` | `0.0.3.beta` | KL&A prototype |
| Inspect Schedule Header | `v0.0` | `0.0.6beta` | KL&A prototype |
| Launch Dynamo Script | `v0.0` | `0.0.0.beta` | KL&A prototype |
| Open Keynote File | `v0.0` | `0.0.5.beta` | KL&A prototype |
| Steel PSF | `v0.5` | Planned | KL&A prototype; delivered `v0.0`–`v0.4` |
| UI Gallery | `v0.3` | `0.0.6beta` | KL&A prototype |
| Family Studio | `v0.0` | `0.0.7` | KL&A prototype |
| Startup Importer | `v0.0` | `0.0.7` | KL&A prototype |
| Trial | `v0.0` | `0.0.6beta` | KL&A prototype |

## Totals and scope

- 36 visible command bundles audited.
- 15 maintained production/shared commands.
- 4 special unchanged imports with source-qualified versions.
- 17 DevSandbox prototypes; three currently have planned unreleased work.
- Two production commands also have planned unreleased versions.

`version.json`, generated `lib/build_info.py`, release tags, and the root
`CHANGELOG.md` remain extension-release artifacts. Tool versions are released
per command at a mainline delivery and are documented in the central ledger and
adjacent specifications.
