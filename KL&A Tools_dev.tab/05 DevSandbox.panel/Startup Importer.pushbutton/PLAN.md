# KL&A Model Startup Importer

## Summary
Build a compiled C#/.NET importer surfaced inside the KL&A pyRevit extension. The first version will replace the current Bluebeam/PDF startup workflow with a structured Word/Excel startup checklist that tells the tool which standard KL&A details and general notes to import from a controlled seed RVT.

The Office document is the intake source, not the drafting source. Revit content comes from KL&A’s standard Revit seed/template model so imported details and notes remain native, editable, and predictable.

## Key Decisions
- Host both paths in the architecture, but ship the first UI through a pyRevit DevSandbox button that invokes a compiled DLL via `assembly` / `command_class`.
- Target Revit 2024 and up:
  - Revit 2024 build: `.NET Framework 4.8`.
  - Revit 2025+ build: `net8.0-windows`.
  - Keep one source tree with multi-targeted project files where practical.
- MVP mode is “create/import only.” It imports selected items into the active model but does not auto-place views on sheets yet.
- Build both Word and Excel intake adapters behind one interface, then choose the production format after testing with engineers.
- Prefer Open XML SDK for `.docx` and `.xlsx` parsing. Use ClosedXML for Excel if the workbook checklist needs easier table/cell handling. Avoid EPPlus unless its license is explicitly approved.

References checked:
[Revit 2024 API .NET 4.8 requirements](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-API/files/Revit_API_Developers_Guide/Introduction/Getting_Started/Welcome_to_the_Revit_Platform_API/Revit_API_Revit_API_Developers_Guide_Introduction_Getting_Started_Welcome_to_the_Revit_Platform_API_Development_Requirements_html.html), [Revit 2025+ .NET 8 migration](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API/files/Revit_API_Developers_Guide/Introduction/Getting_Started/Using_the_Autodesk_Revit_API/Revit_API_Revit_API_Developers_Guide_Introduction_Getting_Started_Using_the_Autodesk_Revit_API_NET8_Update_html.html), [Revit add-in registration](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-API/files/Revit_API_Developers_Guide/Introduction/Add_In_Integration/Revit_API_Revit_API_Developers_Guide_Introduction_Add_In_Integration_Add_in_Registration_html.html), [TextNote creation API](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/7dddec5f-15a3-f835-85ab-0ff677b564db.htm).

## Project Structure
Add a compiled solution under a new repo folder such as `src/KLA.ModelStartupImporter/`:

- `KLA.ModelStartupImporter.Core`
  - `StartupDocumentReader`
  - `WordStartupReader`
  - `ExcelStartupReader`
  - `StartupDocumentModel`
  - `StartupItem`
  - `ContentCatalog`
  - `ImportPlanBuilder`
  - `ImportResult`
- `KLA.ModelStartupImporter.Revit`
  - `StartupImportCommand`
  - `UpdateStartupLinksCommand`
  - `SeedModelReader`
  - `ViewCopyManager`
  - `NoteImportManager`
  - `LinkMetadataStore`
  - `RevitTypeMapper`
- `KLA.ModelStartupImporter.UI`
  - WPF startup-file picker
  - item review/selection dialog
  - seed model/settings selector
  - import summary dialog
- `KLA.ModelStartupImporter.Tests`
  - host-independent tests for Word/Excel parsing, catalog matching, duplicate handling, and import-plan creation.

Expose DevSandbox buttons under the existing pyRevit layout:
- `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Model Startup Import.pushbutton`
- `KL&A Tools_dev.tab/05 DevSandbox.panel/Prototype.pulldown/Update Startup Links.pushbutton`

Later promotion can move those buttons to the production KL&A Tools panel after live validation.

## Core Models And Pipeline
Core model:

- `StartupDocumentModel`
  - `SourcePath`
  - `SourceType`: `Word` or `Excel`
  - `ModifiedUtc`
  - `FileHash`
  - `Items`
- `StartupItem`
  - `ItemId`
  - `Title`
  - `Category`: detail, general note, schedule, other future type
  - `Selected`
  - `EngineerComment`
  - `SourceLocation`: sheet/table/bookmark/paragraph/cell reference
  - `PlacementHint`: optional sheet/detail number/zone for future v2
- `CatalogItem`
  - `ItemId`
  - `SourceViewName`
  - `TargetName`
  - `ContentType`
  - `RequiredTextTypeNames`
  - `RequiredLineStyleNames`
- `ImportPlan`
  - selected items matched to seed-model source views/content
  - skipped/unknown/duplicate items
  - required source model path
  - required Revit resources
- `LinkMetadata`
  - startup file path/hash/modified date
  - source document format
  - selected item ids
  - seed model path/hash/version
  - created Revit element/view ids
  - import settings version

Pipeline:
1. User launches `Model Startup Import`.
2. UI asks for startup `.docx` or `.xlsx`.
3. Reader parses checked/selected items into `StartupDocumentModel`.
4. Catalog matcher validates each selected `ItemId` against KL&A’s content catalog.
5. UI shows selected, unknown, duplicate, and skipped items before import.
6. Revit importer opens or references the KL&A seed RVT, copies selected drafting/detail/legend content into the active model, and applies naming rules.
7. Link metadata is stored on created views/elements using Extensible Storage.
8. Import summary reports created items, skipped items, missing catalog entries, and manual follow-up.

## Revit Behavior
- Use `ElementTransformUtils.CopyElements` for seed drafting/detail/legend view content, following the repo’s existing copy-legend pattern.
- Use destination types for duplicate type names unless a KL&A mapping requires a specific type replacement.
- Preserve source view scale and content where possible.
- Do not auto-place on sheets in MVP.
- Use transactions grouped by import run so a failed item can be reported clearly and serious preflight failures stop before modifying the model.
- `Update Startup Links` scans stored metadata, recomputes the startup document hash, reports changed/stale imports, and offers rebuild for selected import groups.

## Required Packages
- `DocumentFormat.OpenXml` for `.docx` and low-level `.xlsx` access.
- `ClosedXML` for Excel checklist parsing if table/range handling is cleaner than raw Open XML.
- `Newtonsoft.Json` or `System.Text.Json`, depending on target compatibility, for settings/catalog serialization.
- Revit references from installed Revit folders:
  - `RevitAPI.dll`
  - `RevitAPIUI.dll`
  - `CopyLocal=false`

## Test Plan
- Unit tests for Word checklist parsing from fixture `.docx`.
- Unit tests for Excel checklist parsing from fixture `.xlsx`.
- Unit tests for checked/unchecked, duplicate ids, unknown ids, blank rows, comments, and placement hints.
- Unit tests for catalog matching and import-plan warnings.
- Static build for Revit 2024 target and Revit 2025+ target.
- Live Revit validation:
  - import a small fixture startup document;
  - confirm selected views/notes are created;
  - confirm native Revit elements remain editable;
  - confirm metadata is present;
  - modify the startup document and verify `Update Startup Links` detects the change.

## Assumptions
- KL&A standard details/general notes will live in a controlled seed RVT/template, not inside the startup Word/Excel document.
- The startup document will contain stable item ids that map to catalog entries.
- Automatic sheet placement is v2 unless a very small placement-hint proof of concept is needed during MVP testing.
- The first implementation stays under DevSandbox until live Revit testing proves the workflow.
