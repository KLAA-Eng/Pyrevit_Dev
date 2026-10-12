# Comprehensive design system, GUI, and tools review

**Review date:** 2026-10-05 (America/Denver). **Reviewed source:** `1562e96a5f6e23b7368c80e317868a0c059dc165`, extension `0.0.11-dev`. **Review branch:** `codex/comprehensive-design-tools-review`.

The repository has a coherent visual identity, reusable legacy and compiled GUI foundations, complete metadata for its 36 visible tools, and meaningful automated tests. The most important findings concern **correct model outcomes and trustworthy reporting**, followed by keyboard accessibility, text readability, long-message handling, and the gaps in compiled release validation. Cosmetic normalization should follow those repairs.

This review produced documents and supporting evidence only. It did not implement fixes, alter logos/icons, change model content, run real Excel workflows, deploy assemblies, or prepare a release. Findings are proposed work for review, not automatic authorization to implement them.

## Read the review

| Document | Purpose |
| --- | --- |
| [Design system and GUI](design-system-and-gui.md) | All 53 XAML sources, resource boundaries, interaction/accessibility findings, ten provisional design dimensions |
| [Production tools](production-tools.md) | All 19 visible tools in panels 01–04; correctness, reporting, transactions, Excel, revisions and view workflows |
| [Prototypes and Family Studio](prototypes-and-family-studio.md) | All 17 DevSandbox tools, Family Studio backend, prototype readiness and acceptance requirements |
| [Repository, Startup Importer, checks and assets](repository-and-assets.md) | Startup Importer backend, startup/dependency behavior, 11 preflight checks, metadata/governance, PNG audit |
| [Support components](support-components.md) | Non-ribbon shared/docked helpers and their actual activation/consumer boundaries |
| [Validation and acceptance](validation-and-acceptance.md) | Exact checks/results, read-only live host evidence, coverage limits and host acceptance plan |
| [Prioritized finding register](finding-register.md) | All finding IDs, priorities, owning report and recommended implementation order |

The detailed reports give each finding a concrete trigger, consequence, evidence location, proposed remedy, and acceptance criteria. Their inventories also record tools/surfaces where no new defect was established. An empty finding entry does not mean the workflow received live acceptance.

The register contains **54 findings: six P1, 36 P2, and 12 P3**. Inferred host risks and dormant-component prerequisites are labeled separately from reproduced failures. The [ribbon contact sheet](evidence/ribbon-contact-sheet.png) provides an inspected comparison of the actual asset files, not a Revit screenshot.

## Coverage and method

| Scope | Coverage |
| --- | --- |
| Visible ribbon commands | 36/36: two Resource Links, two KL&A Tools, 12 Core Tools, three Outreach, 17 DevSandbox |
| XAML | 53/53 tracked sources: 20 Windows, two Pages, one UserControl, 30 ResourceDictionaries |
| Compiled source families | Shared WPF, Family Studio, Model Startup Importer; source and targeted tests, no deployment |
| Preflight checks | All 11 identified, with review depth disclosed; independently discoverable through pyRevit |
| PNG assets | 428 reusable source PNGs + 76 ribbon/template PNGs decoded and measured; no replacements |
| Metadata/SPEC contracts | All 36 visible bundles passed the repository's metadata checker; behavioral claims additionally checked against source |
| Shared support | Active high-risk helpers traced with their consumers; dormant/general-purpose helpers assessed separately |

Three focused subagents reviewed GUI/design, production tools, and prototypes/Family Studio. The coordinating pass audited inventory, assets, compiled Startup Importer, preflight, tests, and report consistency. The GUI reviewer also challenged the coordinating findings independently and reviewed ancillary support components. The review used the code-review-and-quality, design-system, and accessibility skills, adapted to IronPython/Revit and WPF rather than applying web/mobile rules literally.

Evidence was drawn from the actual checkout, adjacent specifications, installed pyRevit implementation, primary Autodesk/Microsoft/W3C sources where needed, isolated reproductions, and the repository's existing tests. Prior design notes informed where to look; their old counts and architecture descriptions were not treated as current evidence.

The review favors findings with a demonstrable failure path. For example, it excludes a suspected View Range Unlimited/InvalidElementId defect after the live Revit constants proved equal. It also treats multicolor button diagrams and branding as potential intentional exceptions rather than counting every pixel outside a named token as a violation.

## Validation outcome

| Validation | Result |
| --- | --- |
| Python tests | 195 run: **194 passed, one skipped**, zero failures |
| Five .NET test projects | 57 run: **56 passed, one failed** |
| Visible command metadata | **36 checked, zero errors** |
| Local version/build/changelog identity | **Passed** |
| Tracked XAML XML parsing | **53 passed** |
| PNG decoding and inventory | **504 measured** |

The .NET failure is a palette-contract mismatch: the test requires a legacy shared-palette merge that the current implementation and design guide do not yet claim. The Python-only consolidated release checker does not run that test project. The skip is a Windows privilege restriction preventing the symlink-escape test from creating a symlink.

The actual connected host reported Revit **2024 build 24.3.50.51**, IronPython **2.7.12**, and pyRevit **6.5.3.26176+2017:**. Only version/API constants were read. Availability is not GUI or model-workflow acceptance. No live Revit window, screen reader, Excel workbook, family load, import, or model transaction was exercised. The isolated WPF control-layout reproduction is explicitly distinguished from an actual Revit alert.

## Recommended order of work

1. **Correctness and trust:** address macro-security fail-open behavior, failed-family-load fallback, stale concrete requirements, incorrect Steel PSF history, Startup Importer cross-document IDs/schedule fidelity/commit outcomes, and misleading revision/view reports. Validate each fix with a narrowly targeted reproduction and host acceptance.
2. **Shared GUI usability:** restore keyboard-focus feedback, make enabled text readable on actual backgrounds, bound long alerts, and repair the Gallery Recall preview. Verify UI Automation names before making blanket label changes.
3. **Coverage and release gates:** reconcile the palette contract, include affected compiled suites in validation, and record exact supported-host evidence. Correct startup dependency error handling and preflight lifecycle/cancellation issues.
4. **Consistency and maintenance:** align stale behavior documentation, make large-window sizing and result truncation usable, then address approved token/icon exceptions, shared patterns, and command decomposition in focused changes.

Do not combine these into one sweeping redesign. Preserve native pyRevit forms, intentional prototype isolation, compiled/legacy resource boundaries, unrelated work, and the established ribbon hierarchy. Tool versions should follow meaningful mainline deliveries, not increment once per review finding.

## Limits and interpretation

This is a comprehensive repository review with complete command and GUI-source inventories and explicit depth boundaries. It is **not** proof of defect absence, a full formal audit of every generic snippet, translation certification, dependency vulnerability clearance, binary/source attestation, a performance benchmark, or release acceptance. The detailed matrix identifies larger supporting modules that received risk-focused rather than line-by-line review.

P1 means a high-impact correctness/security or misleading-success issue that should be addressed before relying on the affected workflow; P2 is an actionable bounded functional/usability/validation issue; P3 is lower-priority consistency, documentation, or dormant-component work. Prototype status is preserved and does not imply production readiness. Source-confirmed mechanisms can still require live host reproduction to establish their exact external effect.

The acceptance plan is intentionally separate from completed evidence. Close a finding only after its proposed fix and relevant real-host scenarios have been verified; do not relabel pending live checks as passed because source tests are green.

## Final document validation

All eight review documents were checked for local link/anchor resolution, source-line bounds, unique finding IDs, and whitespace. The 19 production plus 17 DevSandbox command inventory reconciles with the metadata inventory, and the 53-XAML inventory reconciles with the GUI report. All 54 finding IDs are unique. Tracked and staged source diffs are empty; new files are confined to this review folder. The final [document-check record](evidence/document-validation.json) contains the measured totals and no unresolved document issues. No commit, push, PR, release, or implementation change was made.
