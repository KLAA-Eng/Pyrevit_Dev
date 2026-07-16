# Releasing

This repo uses one human-edited version source:

- `version.json`

`lib/build_info.py` is generated from `version.json`. Do not edit `lib/build_info.py` by hand.

## Bump The Version

1. Edit `version.json`.
2. Update:
   - `version`
   - `channel`
   - `release_date`

Example:

```json
{
  "version": "0.4.1",
  "channel": "stable",
  "release_date": "2026-07-16"
}
```

## Regenerate Build Metadata

Run:

```powershell
C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy Bypass -File .\scripts\generate_build_info.ps1
```

This rewrites `lib/build_info.py` from `version.json`.

## Commit

Commit both files:

- `version.json`
- `lib/build_info.py`

## Tag The Release

If this is a real release, create the matching tag:

```powershell
git tag -a v0.4.1 -m "Release v0.4.1"
git push origin v0.4.1
```

Replace `0.4.1` with the version from `version.json`.

## Verify In Revit

1. Reload pyRevit.
2. Open `KL&A Tools > Outreach > About KL&A Tools`.
3. Confirm:
   - version
   - Git tag
   - Git SHA
   - loaded extension path

The loaded extension path is the key support check. It confirms which `.extension` folder pyRevit actually loaded.
