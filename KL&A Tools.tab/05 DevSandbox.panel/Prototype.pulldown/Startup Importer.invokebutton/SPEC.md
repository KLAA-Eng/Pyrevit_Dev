# KL&A Model Startup Importer — DevSandbox MVP Contract

Status: provisional Wave 2 implementation, approved for DevSandbox validation only.

## Outcome

The compiled command accepts a `.docx` or `.xlsx` KL&A startup checklist, validates and parses it deterministically, computes its SHA-256 hash, and uses an operator-selected settings JSON to resolve a controlled seed RVT and versioned catalog. It presents a review before creating any model content.

Host-independent code can match selected item ids to an in-memory content catalog and produce an import plan. Selected unknown ids and every occurrence of a selected duplicate id are excluded from actionable matches. Unchecked items are reported as skipped.

## Checklist schema

At least one Word table or Excel worksheet must use these six headers in its first row. Header order is flexible and comparison is case-insensitive after trimming:

1. `ItemId`
2. `Title`
3. `Category`
4. `Selected`
5. `EngineerComment`
6. `PlacementHint`

Every nonblank data row requires `ItemId`, `Title`, and `Category`. Supported categories are `detail`, `general note`, `schedule`, and `other` (case-insensitive). Selection values are:

- selected: `x`, `true`, `yes`, `1`;
- unchecked: blank, `false`, `no`, `0`.

Any other selection/category value or a partially populated row without an item id fails the read with its Word table row or Excel cell location. `.docm`, `.xls`, `.xlsm`, files larger than 25 MiB, missing files, empty files, and malformed packages are rejected.

The reader snapshots the source bytes once, then parses and hashes that same immutable snapshot. It compares file length and UTC modification time before and after the read and fails closed if either changes.

Word documents may contain other tables; only tables with the complete header contract are parsed. Excel workbooks may contain other sheets; only worksheets with the complete first-row header contract are parsed. Matching tables/sheets are processed in document/workbook order and data rows retain source order.

## Import-plan classification

- `Matches`: selected ids appearing exactly once in the checklist and once in the case-insensitive catalog.
- `UnknownItems`: unique selected ids absent from the catalog; blocking.
- `DuplicateItems`: all selected rows sharing an id case-insensitively; blocking and excluded from matches.
- `SkippedItems`: unchecked rows.

The catalog constructor rejects duplicate catalog ids case-insensitively.

## Wave 2 import contract

The settings JSON is external to the extension and names `seedModelPath` and
`catalogPath`. The catalog JSON declares a non-empty `version` and maps each
stable item id to `sourceViewName`, `targetName`, `contentType`, and optional
resource requirements. The command validates all selected seed sources before
opening a transaction group.

`settings.json`

```json
{ "seedModelPath": "C:\\Controlled Content\\KL&A Seed.rvt", "catalogPath": "startup-catalog.json" }
```

`startup-catalog.json`

```json
{
  "version": "2026.08",
  "items": [{
    "itemId": "D-001",
    "sourceViewName": "D-001 Seed Detail",
    "targetName": "D-001 Detail",
    "contentType": "detail",
    "requiredTextTypeNames": ["3/32 in Arial"],
    "requiredLineStyleNames": ["Thin Lines"]
  }]
}
```

Details and general notes are imported from named seed drafting views into new
destination drafting views. Schedules are recreated from named seed schedules
only when their definitions use supported regular fields, string filters,
sort/group rules, headings, and grid column widths. Unsupported schedule
features fail closed before model writes.

Selected unknown or duplicate ids block Import. Destination views/schedules
already named by the catalog target are skipped and reported. This wave never
overwrites, refreshes, rebuilds, or stores link metadata. Any failure after the
transaction group starts rolls the full import back.

## Deferred contracts and live gates

No seed RVT or content catalog file is invented or committed by this slice. The
controlled Revit copy/translation path is implemented, while resource/type
mapping beyond the declared catalog requirements, Extensible Storage,
created-element tracking, and update/rebuild semantics remain deferred.

Before promotion beyond DevSandbox, validate on Windows with Revit 2024 and at least one Revit 2025+ version:

- build both target frameworks against matching installed Revit references;
- verify pyRevit selects the versioned 2024 assembly and .NET 8 fallback;
- exercise cancel, valid, invalid, and zero-selected checklist paths;
- approve a real catalog/seed fixture before live model mutation;
- test model mutations and rollback in representative disposable Revit projects.
