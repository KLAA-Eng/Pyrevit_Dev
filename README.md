# KL&A Tools for pyRevit

KL&A Tools is a pyRevit extension for KL&A Revit workflows. This repository
contains Python commands, shared helpers, compiled C# tools, and their
documentation. Development uses `master-dev` and the **KL&A Tools_dev** ribbon
tab (`KL&A Tools_dev.tab/`). Releases use `main` and **KL&A Tools**
(`KL&A Tools.tab/`).

> **Development checkout.** The latest published release is
> [`0.0.13-beta`](https://github.com/KLAA-Eng/Pyrevit_Dev/releases/tag/v0.0.13-beta),
> dated October 22, 2026. This checkout identifies itself as `v0.0.14-dev`.

## Ribbon tour

| Ribbon panel | What you will find |
| --- | --- |
| **KL&A Resources** | Links to General Notes Type Details and Revit Standards. |
| **KL&A Tools** | Engineering-note visibility controls and Carbon GWP Pull. |
| **Core Tools** | View and sheet renaming, revision utilities, 2D overrides, sheet duplication, view-range tools, legend copying, and model-history helpers. |
| **Outreach/Feedback** | Build details, feedback, and a prototype request form. |
| **Dev-Sandbox** | Development prototypes, compiled tools, diagnostics, Dynamo access, and the UI Gallery. |

## Command catalog

**Maturity labels describe intended placement, not a production guarantee.**
`Core` is a primary ribbon tool, `Beta` is a packaged development tool, and
`Prototype` is under evaluation in Dev-Sandbox. Commands marked **Yes** or
**Graphics** can persist a change in the active Revit document; test them on an
appropriate model before project use.

| Command or group | Panel | Purpose | Maturity | Changes Revit model? |
| --- | --- | --- | --- | --- |
| Resource links | KL&A Resources | Open KL&A reference resources. | Core | No |
| Hide Engineering Notes | KL&A Tools | Hide or unhide eligible engineering-note text in supported views. | Beta | Graphics |
| Find & Replace in Views / Sheets | Core Tools > Rename | Rename selected views or sheets. | Core | Yes |
| Revision search tools | Core Tools > Revision | Find revised sheets or revision clouds on views. | Core | No |
| Revision change tools | Core Tools > Revision | Add or remove additional sheet revisions. | Core | Yes |
| Hide/Unhide Revision Clouds | Core Tools > Revision | Hide or unhide revision clouds on selected sheets and placed views; report revision schedule changes. | Core | Graphics and revision schedule edits |
| Highlight 2D | Core Tools | Toggle red graphic overrides for 2D elements. | Core | Graphics |
| Duplicate Sheets | Core Tools | Duplicate selected sheets and their selected content. | Core | Yes |
| ViewRange | Core Tools | Review or adjust active-view range settings. | Core | Yes |
| Copy Legends to Other Documents | Core Tools | Copy selected legends into open destination documents. | Core | Yes, in destination document |
| Who Did That | Core Tools | Inspect available model-history information. | Core | No |
| About KL&A Tools | Outreach/Feedback | Show version, Git, pyRevit, Revit, and loaded-path details. | Beta | No |
| Suggestions | Outreach/Feedback | Open the KL&A feedback form with optional context prefilled. | Beta | No |
| Prototype Request | Outreach/Feedback | Open the KL&A prototype request form in the default browser. | Core | No |
| Carbon GWP Pull | KL&A Tools | Export selected material schedules and create or update GWP and material-volume charts on the active SYNC TO CENTRAL sheet. | Beta | Yes |
| Beam Reaction Declutter | Dev-Sandbox > Prototypes | Move overlapping reaction tags along their tagged beams in eligible plan views. | Prototype | Yes |
| Concrete Mix Header | Dev-Sandbox > Prototypes | Import `tblMixHistory` Excel data into a selected schedule header. | Prototype | Yes |
| Create View Detail Folders | Dev-Sandbox > Prototypes | Export matching detail/drafting views as PDF, JPEG, and HTML packages. | Prototype | No; writes files |
| Highlight Changed Elements | Dev-Sandbox > Prototypes | Compare selected content against a baseline RVT and apply review overrides. | Prototype | Graphics |
| Element Takeoff | Dev-Sandbox > Prototypes | Report accumulated length and volume for interactively selected elements. | Prototype | No |
| Steel PSF | Dev-Sandbox > Prototypes | Report steel pounds per floor area; optionally write CSV/Excel history. | Prototype | No; optional file output |
| Excel COM Smoke Test | Dev-Sandbox > Prototypes | Diagnose Excel automation with a disposable workbook and report script, helper, and assembly identity. | Prototype | No; creates temporary files and an Excel process |
| Inspect Schedule Header | Dev-Sandbox > Prototypes | Export a selected schedule header's layout and cells to JSON and CSV. | Prototype | No; writes files |
| Family Studio | Dev-Sandbox > Prototypes | Browse a local family catalog and load or place indexed families. | Prototype | Yes; also updates local catalog data |
| Startup Importer | Dev-Sandbox > Prototypes | Review a Word/Excel startup checklist and import supported content from a controlled seed model and catalog. | Prototype | Yes |
| Launch Dynamo Script | Dev-Sandbox > Prototypes | Launch the bundled Dynamo graph. Model effects depend on the graph. | Prototype | Depends on graph |
| Launch Dynamo Player | Dev-Sandbox | Open Revit's Dynamo Player. Model effects depend on the graph subsequently run. | Prototype | No; launcher only |
| Open Keynote File | Dev-Sandbox > Prototypes | Open the active project's existing keynote file in its default application. | Prototype | No |
| URL Button | Dev-Sandbox > Prototypes | Open the configured Microsoft Forms trial link. | Prototype | No |
| UI Gallery | Dev-Sandbox > Prototypes | Open safe, seeded previews of supported dialog families. | Prototype | No |

Hidden templates under `KL&A Tools_dev.tab/05 DevSandbox.panel/_Templates/`
are development assets. Start new commands from the
[command template](<KL&A Tools_dev.tab/05 DevSandbox.panel/_Templates/_Template.pushbutton/SPEC.md>).

Each user-facing command has a neighboring `SPEC.md` that documents its
inputs, outputs, exclusions, and validation boundary. For example:

- [Carbon GWP Pull specification](<KL&A Tools_dev.tab/02 KL&A Tools.panel/Carbon GWP Pull.pushbutton/SPEC.md>)
- [Create View Detail Folders specification](<KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Create Detail Folders.pushbutton/SPEC.md>)
- [UI Gallery specification](<KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/SPEC.md>)

## Install for development

### Prerequisites

- Windows with Autodesk Revit 2024 or later; see the compatibility limits below.
- pyRevit installed and available in Revit.
- Git and access to this repository for development.
- Python 3 for the host-independent repository checks. This is separate from
  the Python engine used to run commands inside pyRevit.
- Microsoft Excel for the Excel COM workflows. Dynamo is needed for the Dynamo
  launchers. Compiled-tool configuration and build requirements are documented
  in the corresponding command specifications and source projects.

### Clone the development branch

From your chosen parent folder, run:

```powershell
git clone --branch master-dev https://github.com/KLAA-Eng/Pyrevit_Dev.git KLCode.pyRevit.dev.extension
cd KLCode.pyRevit.dev.extension
```

The explicit folder name preserves pyRevit's `.extension` convention. GitHub's
default branch is `main`, so select `master-dev` explicitly for development.
Create a separate topic branch from current `master-dev` for each task, as
described in [Contributing](docs/CONTRIBUTING.md).

### Load the extension

1. In pyRevit settings, add the parent directory containing the cloned
   `.extension` folder to the custom extension search paths.
2. Reload pyRevit in Revit and look for the **KL&A Tools_dev** ribbon tab.
3. Use **KL&A Tools_dev > Outreach/Feedback > About KL&A Tools** to confirm
   the version, Git information, and loaded extension path.

The loaded path is the key support check: it confirms that Revit is using this
checkout rather than another installed copy.

## Quick start

1. Load the extension and confirm its path through **About KL&A Tools**.
2. Start with **Dev-Sandbox > Prototypes > UI Gallery** to preview dialogs with
   seeded sample data; it does not start a Revit transaction or change a model.
3. Review a command's `SPEC.md` before using a tool that changes the model or
   writes files.
4. Run the selected command on an appropriate project fixture and review its
   pyRevit output before using it on a deliverable model.

## Compatibility and requirements

| Area | Current requirement or boundary |
| --- | --- |
| Host | Autodesk Revit 2024 or later with pyRevit. A release may claim only the versions live-tested for its changed behavior. |
| Command Python | IronPython/Python 2.7-compatible by default, unless a command explicitly opts into CPython. |
| Create View Detail Folders | Native PDF export requires Revit 2022 or later. |
| Highlight Changed Elements | Prototype currently targets Revit 2024 or later. |
| Steel PSF | Its fixture validation currently targets Revit 2024 or later. |
| Excel-based tools | Carbon GWP Pull and Concrete Mix Header require Microsoft Excel COM interop. Steel PSF can create its companion workbook only when Excel COM is available. Run the Dev-Sandbox > Prototypes > Excel COM Smoke Test first when validating Revit 25/26 compatibility. |
| Compiled DevSandbox tools | Family Studio and Startup Importer include host-specific assemblies for Revit 2024 and Revit 2025/2026. Source/build reconciliation and live acceptance remain tracked in the [compiled-tools acceptance plan](docs/plans/compiled-tools-acceptance.md). |
| Live acceptance | Unit tests and static checks do not prove Revit transactions, native dialogs, Excel automation, or exported deliverables. |

## Troubleshooting and support

| Symptom | First check |
| --- | --- |
| The KL&A Tools_dev tab is missing | Confirm the clone's parent directory is a pyRevit custom extension search path, then reload pyRevit. |
| Revit is loading the wrong copy | Open **About KL&A Tools** and compare **Loaded Extension Path** with this checkout. |
| An Excel workflow cannot start or create a workbook | Confirm Microsoft Excel is installed and that the selected workbook/path is accessible from the Revit workstation. |
| A model-writing tool does not produce the expected result | Review its `SPEC.md`, pyRevit output, selected inputs, and the model's Revit version before retrying. |

Use **Outreach/Feedback > Suggestions** for a bug report, suggestion, or
general feedback. Include the command name, the result you expected, the result
you saw, your Revit version/build, and a screenshot or output text when safe to
share. **About KL&A Tools** provides the build and loaded-path details needed
for a useful report.

## Security and data handling

- Review the command catalog before running a tool marked **Yes** or
  **Graphics**; it can persist a change in the active document.
- Excel-based tools read user-selected workbooks. Carbon GWP Pull also
  refreshes and saves the selected post-processing workbook. Carbon GWP Pull
  and Concrete Mix Header can write to the active Revit document.
- Create View Detail Folders and Steel PSF can create files in a folder you
  select. Check the destination and its existing content before proceeding.
- Highlight Changed Elements opens a separately selected baseline RVT for
  comparison and is designed not to save either document.
- The Suggestions button opens a Microsoft Forms feedback page and can prefill
  feedback type, subject, user name, Revit build, and worksharing status. Review
  the submission before sending it and do not include confidential project data.

## Release status

| Version | Channel | Release date | Notes |
| --- | --- | --- | --- |
| `0.0.13-beta` | Beta | 2026-10-22 | Latest published release; representative Carbon/Excel workflow and other documented live-acceptance limits remain open. |
| `0.0.14-dev` | Dev | Not released | Current development identity on `master-dev`. |

`version.json` is the single human-edited extension version source. After
changing it, regenerate `lib/build_info.py` with the provided script; do not
edit the generated file directly. Release versions, beta-to-stable promotion,
tags, validation evidence, and in-Revit verification are defined in
[Release workflow](docs.ai/RELEASING.md). Published release notes live in
[CHANGELOG.md](CHANGELOG.md).

## Prototype promotion roadmap

Dev-Sandbox prototypes are candidates for promotion only when their operational
contract is stable and they have been validated in the intended Revit context.
Before moving a prototype into a primary panel:

1. Confirm its `SPEC.md` describes inputs, exclusions, outputs, and model/file
   effects accurately.
2. Test a representative Revit fixture, including empty or cancelled input.
3. Verify transactions, native dialogs, Excel COM behavior, and external file
   outputs when the command uses them.
4. Resolve or document compatibility limits and failure reporting.
5. Keep host-independent logic covered by focused tests where practical.

## Repository layout

```text
KL&A Tools_dev.tab/  development ribbon tab, panels, command bundles, and command specs
startup.py           Host-specific dependency setup for compiled DevSandbox commands
lib/                 Shared Python helpers and reusable WPF/UI components
src/                 C# source and tests for Family Studio, Startup Importer, and shared WPF
checks/              Audit checks
tests/               Host-independent unit tests
scripts/             Developer utilities, including build-metadata generation
commands/            Supporting command code outside the visible ribbon bundles
setup files/         Existing Windows installation and extension-registration helpers
docs/                Contributor/design guides, active plans, and durable knowledge
docs/plans/          Active plans and task ledgers
docs/knowledge/      Reusable knowledge, decisions, and new handoff snapshots
version.json         Human-edited version source
docs.ai/             Agent documentation routing and authoritative release governance
```

Command entry points should stay thin: they adapt pyRevit/Revit, WPF, Excel,
and filesystem interactions, while deterministic logic belongs in `lib/` where
it can be tested without Revit.

## Contributing

Before changing a command:

1. For ordinary contributions, create a short-lived topic branch from `master-dev`.
   The release owner may prepare releases and the next development cycle directly
   on `master-dev`; releases reach `main` only through the owner-merged release PR.
2. Read its adjacent `SPEC.md` and `bundle.yaml`. For a new command, start with
   the hidden DevSandbox template and give the command a stable Tool ID.
3. Preserve the established pyRevit bundle hierarchy and command metadata.
4. Keep command-path Python compatible with the pyRevit engine unless the
   command explicitly opts into CPython.
5. Put reusable, host-independent behavior in `lib/` and cover it with a
   focused test when practical.
6. Keep script titles/versions, bundle metadata, and the SPEC synchronized;
   follow [tool version rules](docs.ai/TOOL_VERSIONING.md).
7. Check the final diff, record the applicable automated and live-Revit
   validation, and open a pull request into `master-dev`. The technical owner
   or backup reviewer reviews and merges it.

For the complete team workflow, see
[Contributing](docs/CONTRIBUTING.md), [Release workflow](docs.ai/RELEASING.md),
[team documentation](docs/README.md), and [agent documentation](docs.ai/README.md).

## Test locally

The Python tests run outside Revit and use the Python standard library. Create
a local environment from an installed Python 3 interpreter, then run checks
from the repository root. Activation is optional when using its interpreter
directly:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "*_test.py"
.\.venv\Scripts\python.exe scripts\check_tool_metadata.py
git diff --check
```

Use focused tests for ordinary edits, as described in the contributor guide.
For release preparation and post-release verification, run the consolidated
check described in the [release workflow](docs.ai/RELEASING.md):

```powershell
.\.venv\Scripts\python.exe scripts\release_check.py
```

The Python suite does not build or execute the C# projects under `src/`.
Their source tests, host-specific builds, packaging, and live acceptance need
separate evidence; see the [compiled-tools acceptance plan](docs/plans/compiled-tools-acceptance.md).

These checks do not replace testing commands in Revit. Validate model changes,
transactions, native dialogs, Excel COM behavior, and exported deliverables in
the intended Revit environment.

## References and standards

- [Python Script Guide](docs/knowledge/python-pyrevit.md) - command organization and
  pyRevit script structure.
- [Comment and Docstring Guide](docs/knowledge/python-comments.md) - comments,
  docstrings, command metadata, and section dividers.
- [Contributor Guide](docs/CONTRIBUTING.md) - GitHub workflow,
  validation evidence, and SPEC requirements.
- [Release History](CHANGELOG.md) - published extension releases and known
  limits.
- [KLCode Standards](https://www.notion.so/KLCode-Standards-3e95b7f93e0c80c1bda4f1eaf7f89b62?source=copy_link) -
  team-facing standards handbook and navigation hub.
- [pyRevit Labs](https://pyrevitlabs.notion.site/) - pyRevit documentation and
  resources.
- [Revit API Docs](https://www.revitapidocs.com/) - Revit API reference.
- [RVTDocs](https://rvtdocs.com/) - searchable Revit API reference with version
  comparisons and Python examples.
- [Lucide Icons](https://lucide.dev/icons/) - icon-design reference.

## License

See [LICENSE.md](LICENSE.md).
