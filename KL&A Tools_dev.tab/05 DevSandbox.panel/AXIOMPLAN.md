# Axiom Plan — Windows/Revit DevSandbox Validation

- Repository / branch / evidence commit: `KLCode.pyRevit` / `dev.axiom-trials` / `c91dccf` (`family studio and startup importer`)
- Status: **next**. This plan is execution-ready for packaging and smoke testing; model mutation for Startup Importer remains **blocked** pending the owner decisions listed below.
- Outcome: package the two compiled DevSandbox commands on a Windows Revit workstation, prove their current safe behavior in Revit 2024 and one Revit 2025+ host, select and run bounded pilot inputs, and produce a promotion decision backed by retained evidence.
- Owner: KL&A Revit tools owner for pilot inputs, expected behavior, and promotion decision; Windows/Revit operator for local build and live-test evidence.
- Non-goals: do not promote either command to a production panel, commit generated binaries, modify a production model, invent a seed RVT/catalog/Extensible Storage identity, or expand the Startup Importer beyond its read-only preflight contract.

## Current facts and invariants

- `Startup Importer.invokebutton` resolves `KLA.ModelStartupImporter.Revit.dll`; its source MVP parses `.docx`/`.xlsx`, hashes the input, and reports a read-only import plan. See [SPEC.md](Startup%20Importer.invokebutton/SPEC.md).
- `Family Studio.invokebutton` resolves `KLCode.FamilyStudio.Revit.dll`; the desktop indexer catalogs `.rfa` metadata without opening files through the Revit API, while the Revit command performs the load/place workflow. See [SPEC.md](Family%20Studio.invokebutton/SPEC.md).
- Revit 2024 requires the versioned `*_2024.dll` (`net48`); Revit 2025+ uses the unsuffixed .NET 8 DLL. The bundle metadata must remain unchanged unless a live-resolution defect proves a specific change is required.
- The existing CPython suite has one known failing test: `tests/custom_alert_integration_test.py` still uses `KL&A Tools.tab`, but this checkout uses `KL&A Tools_dev.tab`. Fixing this is a separate, small prerequisite to claiming a fully green repository test gate.

## Acceptance criteria

1. On Windows, both Revit 2024 and one supported Revit 2025+ version compile against their matching installed Autodesk API directories and package all expected runtime dependencies into their owned `.invokebutton/bin/` directories.
2. In each host, pyRevit reloads the extension and launches both visible DevSandbox commands without assembly-resolution errors; evidence records the host version, loaded extension path, selected assembly file, and outcome.
3. Startup Importer processes agreed valid, invalid, cancel, and zero-selected checklist fixtures as a read-only preflight, preserving the active model unchanged.
4. Family Studio indexes a non-production pilot `.rfa` library and successfully searches, loads, and (where placement is valid) places an agreed pilot family in disposable Revit models.
5. The owner explicitly accepts or rejects promotion from DevSandbox based on the recorded evidence and remaining risks.

## Dependencies, risks, and decision gates

| Dependency / risk | Owner and required action | Impact / safe containment |
| --- | --- | --- |
| Windows machine with Revit 2024 and a 2025+ host, matching SDKs, pyRevit, and repository checkout | Windows/Revit operator verifies paths and records exact versions before build | No Windows API references or host validation means no runnable-command or promotion claim. Keep commands in DevSandbox. |
| Revit API paths | Windows/Revit operator supplies the actual `RevitApiPath` / `RevitApiDir` values | Builds intentionally fail closed when assemblies are absent. Do not substitute API DLLs. |
| Pilot fixtures and disposable RVTs | KL&A tools owner supplies non-sensitive `.docx`/`.xlsx`, `.rfa` library, and disposable target models | Do not test against production models or production family library roots. |
| Startup model mutation contract | KL&A tools owner approves seed RVT location, catalog format, Extensible Storage GUID/version, and update/rebuild semantics | This blocks mutation implementation; retain the current read-only command regardless of packaging success. |
| Duplicate-family/load behavior | KL&A tools owner defines the pilot's expected existing-family result | Record the observed behavior; do not change duplicate handling during smoke testing. |

## Execution checkpoints

| Step | Exact files/surfaces | Behavior guarantee | Test-first evidence | Verification | Rollback/containment |
| --- | --- | --- | --- | --- | --- |
| 1. Establish the Windows test baseline | Windows workstation; `version.json`; `KL&A Tools_dev.tab/05 DevSandbox.panel/bundle.yaml`; both `.invokebutton/bundle.yaml` files | The operator knows the precise repo commit, extension path, Revit/pyRevit/.NET versions, and API paths before any package build. | Record `git status --short`, `git rev-parse HEAD`, installed Revit versions, and `Test-Path` results for each `RevitAPI.dll` / `RevitAPIUI.dll`. | Worktree is clean or user-owned changes are documented; bundle assembly/class metadata match the current source. | Stop if API paths, host versions, or extension path are ambiguous; change nothing. |
| 2. Restore source-level baseline | `tests/custom_alert_integration_test.py`; `src/KLCode.FamilyStudio/KLCode.FamilyStudio.sln`; `src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.Tests/KLA.ModelStartupImporter.Tests.csproj` | Host-independent code retains passing behavior before host execution. | First run `python -m unittest discover -s tests -p '*_test.py'`, Family Studio `dotnet test`, and Startup Importer `dotnet test`; retain raw output. | If the Python failure is addressed in a separate scoped change, rerun it green. Record source-test results separately from Revit gates. | Do not alter command behavior merely to satisfy a test. If any .NET test fails, stop packaging that component and triage it first. |
| 3. Package Startup Importer for both hosts | `src/KLA.ModelStartupImporter/KLA.ModelStartupImporter.Packaging.proj`; `Startup Importer.invokebutton/bin/` | The bundle contains `KLA.ModelStartupImporter.Revit_2024.dll`, `KLA.ModelStartupImporter.Revit.dll`, Core, and OpenXML runtime dependencies. | Run `dotnet msbuild .\\KLA.ModelStartupImporter.Packaging.proj -restore -t:Package -p:Revit2024ApiPath="<2024 Revit dir>" -p:Revit2025ApiPath="<2025+ Revit dir>"` from `src\\KLA.ModelStartupImporter`. | Inspect exact files in the owned `bin/` folder; confirm no Autodesk API DLL was copied. | Delete only the newly generated owned `bin/` contents if a rebuild must be discarded; never delete source or unrelated bundle files. |
| 4. Package Family Studio for both hosts | `src/KLCode.FamilyStudio/Revit/KLCode.FamilyStudio.Revit/KLCode.FamilyStudio.Revit.csproj`; `Family Studio.invokebutton/bin/` | The 2024 package uses `KLCode.FamilyStudio.Revit_2024.dll`; 2025+ uses `KLCode.FamilyStudio.Revit.dll`, with required runtime files. | Run, from the Revit project directory, `dotnet build -p:RevitVersion=2024 -p:RevitApiDir="<2024 Revit dir>" -p:PackagePyRevit=true`, then the same command with `RevitVersion=2025` (or `2026`) and its matching path. | Inspect each package directory after each build and record assembly timestamps/names; confirm Autodesk API DLLs remain external. | Preserve the prior known-good package before replacing it. If one host fails, remove only artifacts produced for that failed build and keep the other host result isolated. |
| 5. Execute Startup Importer smoke suite | `Startup Importer.invokebutton`; supplied Word/Excel fixtures; disposable RVTs | The command remains a read-only parser/preflight adapter in every tested host. | Before each case, record a model fingerprint (path, central/workshared state, and element count or equivalent); execute cancel, valid selected items, invalid schema/value, and zero-selected cases. | Verify expected summary/error for each case, no model changes after each run, correct assembly resolution for 2024 and 2025+, and pyRevit reload success. Capture screenshots/logs. | On any unexpected mutation, close the disposable model without saving, retain evidence, and stop further Importer testing. |
| 6. Run Family Studio pilot | `src/KLCode.FamilyStudio/App/KLCode.FamilyStudio.Indexer/appsettings.example.json` copied to an operator-owned config; `Family Studio.invokebutton`; owner-provided pilot `.rfa` root; disposable RVTs | Indexing is bounded to the approved pilot root; UI search, load, and valid placement work without touching production content. | Create an operator-owned config pointing only to the pilot root/cache. Run the indexer, then test empty search, exact-name search, no-result search, load, duplicate-family behavior, load-and-place, and placement cancel in each host. | Record index totals/errors/database path; verify the right family/type appears in Revit and a canceled placement does not leave an unintended instance. Confirm Family Editor documents are rejected. | Keep pilot cache separate from production cache. If a bad family loads or placement is unexpected, close the disposable model without saving and quarantine that pilot fixture. |
| 7. Review and decide promotion | This plan; both SPECs; captured test evidence | Promotion is an explicit owner decision, not inferred from successful builds. | Review each acceptance criterion and classify it PASS, FAIL, or UNAVAILABLE. | Owner records one of: retain DevSandbox, promote Family Studio only, promote Startup Importer read-only only, or authorize a separately specified mutation phase. | Retaining DevSandbox is the default safe state; promotion requires a separate scoped change and live regression evidence. |

## Evidence to retain

- Windows environment record: machine identifier, checkout path, Git SHA, Revit/pyRevit/.NET SDK versions, and installed API directories.
- Build transcripts and inventory of both generated `bin/` directories, including confirmation that `RevitAPI*.dll` was not packaged.
- One result sheet per command/host/case: input fixture identifier, expected result, observed result, screenshots/log paths, model-change check, and operator/date.
- Family Studio pilot configuration with sensitive paths redacted before it is shared or committed.
- Owner's promotion decision and any remaining blocked decision.

## Promotion rules

- **Family Studio:** eligible only after all source tests, dual-host packaging, pilot indexing, search, Load, and safe placement checks pass; retain documented limitations around filesystem-only indexing and Revit metadata extraction.
- **Startup Importer:** eligible only as a **read-only DevSandbox preflight** after all smoke cases pass. Model mutation remains not ready until the owner supplies and approves the seed/catalog/metadata/update contracts and a new implementation plan covers transactions and rollback.
- No binaries, pilot libraries, databases, user settings, or test documents are committed unless an owner explicitly authorizes that separate scope.

## Applicable rules and open decisions

- Applicable: repository `AGENTS.md`; PM-01 through PM-09; ARCH-01 through ARCH-08; and the version/release process in `RELEASING.md` if either tool is formally released.
- Material open decisions: pilot owner and library/checklist locations; 2025 versus 2026 as the second host; expected duplicate-family policy; and, for any Startup Importer mutation work, the controlled seed RVT, catalog, metadata schema, update/rebuild semantics, and rollout owner.

