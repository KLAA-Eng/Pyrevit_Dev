# Concrete Mix Header

## Purpose

`Concrete Mix Header` is a DevSandbox pyRevit prototype for importing a
specific Excel block into the writable header section of a Revit schedule.

The initial reference workbook used to identify the source table is:

`J:\Standards Committees\Team Dynamo\_Scripting\Script Sandbox\LTM Sandbox\24_Conc Mix Table\Concrete Mix Design Requirements\_260626.xlsm`

## Current workflow

The command prompts the user to pick an Excel workbook, asks for the target Revit
schedule, reads the data rows from the configured Excel table with Microsoft
Excel COM, prints a preview in the pyRevit output window, asks for confirmation,
then writes the values into the schedule's `SectionType.Header` table section.

The schedule body is not edited. Normal Revit schedule rows generated from
elements remain untouched.

The command imports `tblMixHistory` data rows only. Excel table header cells are
used to map columns, but the Excel headers themselves are not imported.

## Configuration

Edit the constants at the top of `script.py` while the prototype is being tuned:

- `EXAMPLE_EXCEL_PATH`
- `EXCEL_TABLE_NAME`
- `EXCEL_WORKSHEET_NAME`
- `IMPORT_START_ROW_OFFSET`
- `IMPORT_START_COLUMN_OFFSET`
- `TEMPLATE_MIX_ROW_COUNT`
- `TEMPLATE_COLUMN_COUNT`
- `PRESERVE_NOTES_START_ROW_OFFSET`
- `COLUMN_WIDTHS_FEET`
- `CLEAR_EXISTING_HEADER_TEXT`

The example workbook path is only used to seed the file picker folder when that
mapped drive is available. The command always prompts for an `.xlsm` or `.xlsx`
file.

## Header behavior

The command uses `ViewSchedule.GetTableData()` and edits
`SectionType.Header`. It uses `FirstRowNumber` and `FirstColumnNumber` when
addressing cells so the code does not assume that Revit table sections are
zero-based.

The current template inspection shows:

- 68 header rows;
- 11 header columns;
- title/column header content in row offsets 0-2;
- mix-history rows in row offsets 3-32;
- notes beginning at row offset 33.

The command currently updates only row offsets 3-32 and column offsets 0-10.
It maps each `tblMixHistory` data row into the schedule's paired-row layout,
then searches the existing Revit schedule mix rows by normalized `Element` text.
Matching elements are updated in place. Unmatched Excel rows are added only when
an empty paired mix row exists in the template region. The title/header rows,
unmatched existing mix rows, and notes below row offset 33 are preserved.

## Excel-to-Revit Mapping

The Excel table is not a direct match to the Revit schedule header. Each Excel
data row becomes two Revit header rows:

- Excel `Elements` -> Revit top row column 0, which is merged through column 1
  and the paired row below.
- Excel `f'c (psi)` -> Revit top row column 2.
- Excel `Cement Type` -> Revit top row column 3.
- Excel `Max (w/c)` -> Revit top row column 4.
- Excel `Max Agg` -> Revit top row column 5.
- Excel `Air Content (%)` -> Revit top row column 6.
- Excel `Slump` -> Revit top row column 7.
- Excel `(F)` -> Revit top row column 8.
- Excel `(C)` -> Revit top row column 9.
- Excel `(S)` -> Revit bottom row column 8.
- Excel `(W)` -> Revit bottom row column 9.
- Excel `Delete` -> ignored.

Revit column 10 is left blank by the current mapping because the shown Excel
table does not include the template's note-reference column.

Matching ignores punctuation and parenthetical suffixes, so an Excel element
such as `Interior Slab on Grade` can update the Revit row
`Interior Slab on Grade (SOG)`.

If the selected schedule header has fewer rows or columns than the template
import region, the command tries to insert enough rows/columns before writing.
If the Excel table has more data rows than the 30-row paired template region can
hold, the command stops instead of overwriting the notes area.
If an Excel element does not match an existing Revit row and no empty paired mix
row exists, the command stops instead of overwriting another element.

Formatting is intentionally limited in this prototype:

- column widths are reapplied from the inspected template;
- existing schedule row heights, merged cells, and styles are otherwise
  preserved;
- guarded calls only, so unsupported style APIs report as warnings instead of
  stopping the import.

## Validation limits

The reference workbook path is on a mapped `J:` drive and may only be reachable
from the user's Revit session. Static tests cover the host-independent range and
mapping helpers, but live acceptance requires running the button in Revit against
the actual workbook and target schedule.

Final row deletion, row insertion policy, merge behavior, and exact formatting
are intentionally not locked yet. The current version does not delete rows or
shift the notes upward.
