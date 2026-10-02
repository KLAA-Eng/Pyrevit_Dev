# Tool Version Inventory

Audited October 2, 2026. This inventory covers every runnable command under
`KL&A Tools_dev.tab` except the `05 DevSandbox.panel` hierarchy. It records
only source-declared command versions; it does not infer a command version
from `version.json`, a release tag, or a command's modification history.

## Requested convention

Command versions use `vMAJOR.MINOR` formatting (for example, `v1.0`) and are
independent of the extension's release version. An extension-release value may
still be documented separately as release history.

## Findings

| Ribbon command | Runtime command version | Formatting assessment | Notes |
| --- | --- | --- | --- |
| Launch Gen Notes Typ Details | Not declared | Missing | No `__version__` or `Version:` metadata in `script.py`. |
| Launch Revit Standards | Not declared | Missing | No `__version__` or `Version:` metadata in `script.py`. |
| Carbon GWP Pull | `v1.0` | Conforms | Updated in this change; the SPEC separately retains its last extension release. |
| Hide Engineering Notes | `0.0.9-beta` | Does not conform | Matches the extension release rather than the requested independent command format. |
| Copy Legends to Other Documents | Not declared | Missing | No `__version__` or `Version:` metadata in `script.py`. |
| Duplicate Sheets | Not declared | Missing | No `__version__` or `Version:` metadata in `script.py`. |
| Override 2D | Not declared | Missing | No `__version__` or `Version:` metadata in `script.py`. |
| ViewRange | Not declared | Missing | No `__version__` or `Version:` metadata in `script.py`. |
| Who Did That | Not declared | Missing | No `__version__` or `Version:` metadata in `script.py`. |
| FindReplace - Views | `Version: 1.2` | Does not conform | Uses a prose prefix and omits the requested `v` prefix. |
| FindReplace Sheets | `Version: 1.1` | Does not conform | Uses a prose prefix and omits the requested `v` prefix. |
| Find All Revised Sheets | Not declared | Missing | No `__version__` or `Version:` metadata in `script.py`. |
| Find All Revision Clouds On Views | Not declared | Missing | No `__version__` or `Version:` metadata in `script.py`. |
| Hide Revision Clouds | Not declared | Missing | No `__version__` or `Version:` metadata in `script.py`. |
| Remove Revision From Sheets | Not declared | Missing | No `__version__` or `Version:` metadata in `script.py`. |
| Set Revision On Sheets | Not declared | Missing | No `__version__` or `Version:` metadata in `script.py`. |
| About KL&A Tools | Not declared | Not applicable | Deliberately displays generated extension build information from `lib/build_info.py`; it has no tool-version declaration. |
| Prototype | Not declared | Missing | No `__version__` or `Version:` metadata in `script.py`. |
| Suggestions | Not declared | Missing | No `__version__` or `Version:` metadata in `script.py`. |

## Totals

- 19 commands audited.
- 1 command conforms to the requested `vMAJOR.MINOR` convention: Carbon GWP
  Pull.
- 3 commands declare a version in a different format: Hide Engineering Notes,
  FindReplace - Views, and FindReplace Sheets.
- 14 commands have no runtime command-version declaration.
- 1 command is intentionally extension-information-only: About KL&A Tools.

## Scope and follow-up

No command other than Carbon GWP Pull was changed by this audit. In particular,
`version.json` remains the extension release authority and `lib/build_info.py`
was not regenerated.

The current command-authoring guidance in `docs/guides/COMMENTS.md` still
states that `__version__` records the last extension release affecting a
command. That policy conflicts with the independent command-version convention
documented here and should be revised in a separately scoped standards change
before versioning the remaining commands.
