# KL&A Tools for pyRevit

KL&A Tools is a development pyRevit extension for KL&A Revit workflows. It
adds a **KL&A Tools** ribbon tab with resource links, document utilities,
feedback tools, and a DevSandbox for prototypes and safe UI exploration.

> **Development / beta extension.** The current release is
> [`0.0.5.beta`](version.json), dated August 19, 2026. Validate every command
> in a representative Revit model before relying on it for project deliverables.

## Ribbon tour

The ribbon is intentionally split between routine tools and work still being
evaluated. The tour below is the current source-based guide; use the **UI
Gallery** in Dev-Sandbox for safe, seeded dialog previews.

| Ribbon panel | What you will find |
| --- | --- |
| **KL&A Resources** | Links to General Notes Type Details and Revit Standards. |
| **KL&A Tools** | Engineering-note visibility controls. |
| **Core Tools** | View and sheet renaming, revision utilities, 2D overrides, sheet duplication, view-range tools, legend copying, and model-history helpers. |
| **Outreach/Feedback** | Build details, a feedback form, and a prototype entry point. |
| **Dev-Sandbox** | Development prototypes, Dynamo access, templates, and the UI Gallery. |

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
| Revision change tools | Core Tools > Revision | Set, remove, or turn off sheet revisions. | Core | Yes |
| Highlight 2D | Core Tools | Toggle red graphic overrides for 2D elements. | Core | Graphics |
| Duplicate Sheets | Core Tools | Duplicate selected sheets and their selected content. | Core | Yes |
| ViewRange | Core Tools | Review or adjust active-view range settings. | Core | Yes |
| Copy Legends to Other Documents | Core Tools | Copy selected legends into open destination documents. | Core | Yes, in destination document |
| Who Did That | Core Tools | Inspect available model-history information. | Core | No |
| About KL&A Tools | Outreach/Feedback | Show version, Git, pyRevit, Revit, and loaded-path details. | Beta | No |
| Suggestions | Outreach/Feedback | Open the KL&A feedback form with optional context prefilled. | Beta | No |
| Carbon GWP Pull | Dev-Sandbox > Prototypes | Import calculated GWP values from Excel into eligible family-type parameters. | Prototype | Yes |
| Concrete Mix Header | Dev-Sandbox > Prototypes | Import `tblMixHistory` Excel data into a selected schedule header. | Prototype | Yes |
| Create View Detail Folders | Dev-Sandbox > Prototypes | Export matching detail/drafting views as PDF, JPEG, and HTML packages. | Prototype | No; writes files |
| Hide Revision Clouds | Dev-Sandbox > Prototypes | Hide matching revision clouds on selected sheets and placed views. | Prototype | Graphics |
| Highlight Changed Elements | Dev-Sandbox > Prototypes | Compare selected content against a baseline RVT and apply review overrides. | Prototype | Graphics |
| Steel PSF | Dev-Sandbox > Prototypes | Report steel pounds per floor area; optionally write CSV/Excel history. | Prototype | No; optional file output |
| UI Gallery | Dev-Sandbox > Prototypes | Open safe, seeded previews of supported dialog families. | Prototype | No |

Each user-facing command should have a neighboring `SPEC.md` that documents its
inputs, outputs, exclusions, and validation boundary. For example:

- [Carbon GWP Pull specification](<KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Carbon GWP Pull.pushbutton/SPEC.md>)
- [Create View Detail Folders specification](<KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Create Detail Folders.pushbutton/SPEC.md>)
- [UI Gallery specification](<KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/UI Gallery.pushbutton/SPEC.md>)

## Install for development

### Prerequisites

- Autodesk Revit.
- pyRevit installed and available in Revit.
- Access to this repository.

### Load the extension

1. Clone this repository to a stable local location. Its folder already uses
   pyRevit's `.extension` naming convention.
2. In pyRevit settings, add the cloned folder as a custom/development extension.
3. Reload pyRevit, then open Revit and look for the **KL&A Tools** ribbon tab.
4. Use **KL&A Tools > Outreach/Feedback > About KL&A Tools** to confirm the
   version, Git information, and--most importantly--the loaded extension path.

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
| Host | Autodesk Revit with pyRevit. This repository does not declare one global minimum Revit version. |
| Command Python | IronPython/Python 2.7-compatible by default, unless a command explicitly opts into CPython. |
| Create View Detail Folders | Native PDF export requires Revit 2022 or later. |
| Highlight Changed Elements | Prototype currently targets Revit 2024 or later. |
| Steel PSF | Its fixture validation currently targets Revit 2024 or later. |
| Excel-based tools | Carbon GWP Pull and Concrete Mix Header require Microsoft Excel COM interop. Steel PSF can create its companion workbook only when Excel COM is available. |
| Live acceptance | Unit tests and static checks do not prove Revit transactions, native dialogs, Excel automation, or exported deliverables. |

## Troubleshooting and support

| Symptom | First check |
| --- | --- |
| The KL&A Tools tab is missing | Confirm the folder is registered as a custom/development extension, then reload pyRevit. |
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
- Excel-based prototypes read user-selected workbooks. Carbon GWP Pull and
  Concrete Mix Header can write to the active Revit document after their input
  checks and confirmation paths complete.
- Create View Detail Folders and Steel PSF can create files in a folder you
  select. Check the destination and its existing content before proceeding.
- Highlight Changed Elements opens a separately selected baseline RVT for
  comparison and is designed not to save either document.
- The Suggestions button opens a Microsoft Forms feedback page and can prefill
  feedback type, subject, user name, Revit build, and worksharing status. Review
  the submission before sending it and do not include confidential project data.

## Release status and highlights

| Current version | Channel | Release date | Notes |
| --- | --- | --- | --- |
| `0.0.5.beta` | Beta | 2026-08-19 | Current source version; validate changes in Revit before deployment. |

`version.json` is the single human-edited version source. After changing it,
regenerate `lib/build_info.py` with the provided script; do not edit the
generated file directly. The full steps, including release tagging and in-Revit
verification, are in [RELEASING.md](RELEASING.md).

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
KL&A Tools_dev.tab/  pyRevit ribbon tab, panels, command bundles, and command specs
lib/                 Shared Python helpers and reusable WPF/UI components
checks/              Audit checks
tests/               Host-independent unit tests
scripts/             Developer utilities, including build-metadata generation
docs/guides/         Python and comment/documentation standards
version.json         Human-edited version source
RELEASING.md         Release and metadata-generation workflow
```

Command entry points should stay thin: they adapt pyRevit/Revit, WPF, Excel,
and filesystem interactions, while deterministic logic belongs in `lib/` where
it can be tested without Revit.

## Contributing

Before changing a command:

1. Read its `SPEC.md` and the adjacent `bundle.yaml` when present.
2. Preserve the established pyRevit bundle hierarchy and command metadata.
3. Keep command-path Python compatible with the pyRevit engine unless the
   command explicitly opts into CPython.
4. Put reusable, host-independent behavior in `lib/` and cover it with a
   focused test when practical.
5. Check the final diff and run the narrowest relevant validation.

For repository-specific contributor requirements, see [AGENTS.md](AGENTS.md).

## Test locally

The tests focus on logic that can run outside Revit. From the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "*_test.py"
```

This does not replace testing commands in Revit. Validate model changes,
transactions, native dialogs, Excel COM behavior, and exported deliverables in
the intended Revit environment.

## References and standards

- [Python Script Guide](docs/guides/SCRIPTS.md) - command organization and
  pyRevit script structure.
- [Comment and Docstring Guide](docs/guides/COMMENTS.md) - comments,
  docstrings, command metadata, and section dividers.
- [pyRevit Labs](https://pyrevitlabs.notion.site/) - pyRevit documentation and
  resources.
- [Revit API Docs](https://www.revitapidocs.com/) - Revit API reference.
- [RVTDocs](https://rvtdocs.com/) - searchable Revit API reference with version
  comparisons and Python examples.
- [Lucide Icons](https://lucide.dev/icons/) - icon-design reference.

## License

See [LICENSE.md](LICENSE.md).
