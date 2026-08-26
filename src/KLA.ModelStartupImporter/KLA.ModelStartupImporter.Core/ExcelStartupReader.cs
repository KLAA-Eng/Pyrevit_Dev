using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Spreadsheet;

namespace KLA.ModelStartupImporter.Core;

internal sealed class ExcelStartupReader : IStartupFormatReader
{
    public string Extension => ".xlsx";

    public StartupSourceType SourceType => StartupSourceType.Excel;

    public IReadOnlyList<StartupItem> ReadItems(Stream source)
    {
        try
        {
            using var document = SpreadsheetDocument.Open(source, false);
            return ReadWorkbook(document);
        }
        catch (StartupFormatException exception)
        {
            throw new InvalidDataException(exception.Message, exception);
        }
        catch (Exception exception) when (IsPackageFailure(exception))
        {
            throw new InvalidDataException("The Excel startup document could not be read.", exception);
        }
    }

    private static IReadOnlyList<StartupItem> ReadWorkbook(SpreadsheetDocument document)
    {
        var workbookPart = document.WorkbookPart;
        var sheets = workbookPart?.Workbook?.Sheets?.Elements<Sheet>().ToList();
        if (workbookPart == null || sheets == null)
        {
            throw new StartupFormatException("The Excel workbook has no sheets.");
        }

        var items = new List<StartupItem>();
        var matchingSheetCount = 0;
        foreach (var sheet in sheets)
        {
            var worksheetPart = workbookPart.GetPartById(sheet.Id?.Value ?? string.Empty) as WorksheetPart;
            var rows = worksheetPart?.Worksheet?.GetFirstChild<SheetData>()?.Elements<Row>().ToList();
            if (rows == null || rows.Count == 0)
            {
                continue;
            }

            var headerValues = Values(rows[0], workbookPart);
            if (!StartupRowParser.TryCreateHeaderMap(headerValues, out var headerMap))
            {
                continue;
            }

            matchingSheetCount++;
            ReadRows(sheet.Name?.Value ?? "Sheet", rows, workbookPart, headerMap, items);
        }

        if (matchingSheetCount == 0)
        {
            throw new StartupFormatException("No Excel worksheet contains all required startup headers.");
        }

        return items;
    }

    private static void ReadRows(
        string sheetName,
        IReadOnlyList<Row> rows,
        WorkbookPart workbookPart,
        IReadOnlyDictionary<string, int> headerMap,
        ICollection<StartupItem> items)
    {
        for (var rowIndex = 1; rowIndex < rows.Count; rowIndex++)
        {
            var location = sheetName + "!A" + RowNumber(rows[rowIndex], rowIndex + 1);
            var item = StartupRowParser.Parse(Values(rows[rowIndex], workbookPart), headerMap, location);
            if (item != null)
            {
                items.Add(item);
            }
        }
    }

    private static uint RowNumber(Row row, int fallback)
    {
        return row.RowIndex?.Value ?? (uint)fallback;
    }

    private static IReadOnlyList<string> Values(Row row, WorkbookPart workbookPart)
    {
        var cells = new SortedDictionary<int, string>();
        var fallbackColumn = 0;
        foreach (var cell in row.Elements<Cell>())
        {
            var column = ColumnIndex(cell.CellReference?.Value) ?? fallbackColumn;
            cells[column] = CellText(cell, workbookPart);
            fallbackColumn = column + 1;
        }

        if (cells.Count == 0)
        {
            return Array.Empty<string>();
        }

        var values = Enumerable.Repeat(string.Empty, cells.Keys.Max() + 1).ToArray();
        foreach (var entry in cells)
        {
            values[entry.Key] = entry.Value;
        }

        return values;
    }

    private static string CellText(Cell cell, WorkbookPart workbookPart)
    {
        if (cell.DataType?.Value == CellValues.InlineString)
        {
            return cell.InlineString?.InnerText ?? string.Empty;
        }

        var rawValue = cell.CellValue?.InnerText ?? string.Empty;
        if (cell.DataType?.Value != CellValues.SharedString)
        {
            return rawValue;
        }

        if (!int.TryParse(rawValue, NumberStyles.None, CultureInfo.InvariantCulture, out var index))
        {
            throw new StartupFormatException("An Excel shared-string cell has an invalid index.");
        }

        var values = workbookPart.SharedStringTablePart?.SharedStringTable?.Elements<SharedStringItem>().ToList();
        if (values == null || index < 0 || index >= values.Count)
        {
            throw new StartupFormatException("An Excel shared-string cell references a missing value.");
        }

        return values[index].InnerText;
    }

    private static int? ColumnIndex(string? cellReference)
    {
        if (string.IsNullOrWhiteSpace(cellReference))
        {
            return null;
        }

        var index = 0;
        var letterCount = 0;
        foreach (var character in cellReference!.ToUpperInvariant())
        {
            if (character < 'A' || character > 'Z')
            {
                break;
            }

            index = (index * 26) + (character - 'A' + 1);
            letterCount++;
        }

        return letterCount == 0 ? null : index - 1;
    }

    private static bool IsPackageFailure(Exception exception)
    {
        return exception is OpenXmlPackageException ||
               exception is InvalidDataException ||
               exception is IOException ||
               exception is FormatException;
    }
}
