# Carbon GWP Pull

## Purpose

Prototype pyRevit replacement for the Dynamo `x_Team Carbon GWP Pull_RVT 24.dyn` workflow.

The command exports selected Revit schedule table data to an Excel container workbook, reads calculated GWP values from a post-processing workbook, and writes those values to parameters on the `Carbon Pie.JMP` family types in the active Revit model.

## Inputs

- Three Revit schedules selected from the active model. The selector pre-checks these Dynamo defaults when present:
  - `Material Classfication, Area, and Volume`
  - `2x Wood Wall Volume`
  - `Composite Deck Volume`
- Export container workbook selected by file picker.
- Post-processing workbook selected by file picker.

The tool prompts every run. It does not save paths.

## Excel Contract

- Each selected schedule is exported to a worksheet named `DYN Out - <clean schedule title>`.
- Schedule title cleanup removes Dynamo-style text before `=` and `)` markers, trims whitespace, removes Excel-invalid sheet-name characters, and limits names to Excel's 31-character worksheet limit.
- The post-processing workbook must contain a worksheet named `Export`.
- The `Export` worksheet is read as two columns:
  - Column A: Revit family type parameter name.
  - Column B: value to write.

Blank parameter names are skipped and reported.

## Model Changes

The command writes only inside one Revit transaction named `Carbon GWP Pull - Write Family Type Parameters`.

It finds family `Carbon Pie.JMP`, collects its family symbols/types, and writes every imported parameter/value pair to each type when the parameter exists and is writable.

The schedule export and Excel reads do not change the Revit model.

## Output

The pyRevit output window reports:

- Selected schedules.
- Export and post-processing workbook paths.
- Exported worksheet names.
- Family type count.
- Attempted parameter writes.
- Successful writes.
- Skipped Excel rows.
- Missing or read-only parameters.
- Runtime errors.

## Prototype Limits

- Requires Microsoft Excel COM interop on the Revit workstation.
- Requires the post-processing workbook formulas or macros to already produce the `Export` worksheet values after schedule export.
- Does not run workbook macros directly.
- Does not validate that the exported schedule workbook and post-processing workbook are formula-linked correctly.
- Stops before Revit writes if the target family or `Export` worksheet is missing.

