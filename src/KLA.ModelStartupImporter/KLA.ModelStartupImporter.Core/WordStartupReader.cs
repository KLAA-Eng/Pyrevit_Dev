using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;

namespace KLA.ModelStartupImporter.Core;

internal sealed class WordStartupReader : IStartupFormatReader
{
    public string Extension => ".docx";

    public StartupSourceType SourceType => StartupSourceType.Word;

    public IReadOnlyList<StartupItem> ReadItems(Stream source)
    {
        try
        {
            using var document = WordprocessingDocument.Open(source, false);
            var body = document.MainDocumentPart?.Document?.Body;
            if (body == null)
            {
                throw new StartupFormatException("The Word document has no document body.");
            }

            return ReadTables(body.Elements<Table>());
        }
        catch (StartupFormatException exception)
        {
            throw new InvalidDataException(exception.Message, exception);
        }
        catch (Exception exception) when (IsPackageFailure(exception))
        {
            throw new InvalidDataException("The Word startup document could not be read.", exception);
        }
    }

    private static IReadOnlyList<StartupItem> ReadTables(IEnumerable<Table> tables)
    {
        var items = new List<StartupItem>();
        var matchingTableCount = 0;
        var tableNumber = 0;
        foreach (var table in tables)
        {
            tableNumber++;
            var rows = table.Elements<TableRow>().ToList();
            if (rows.Count == 0 || !StartupRowParser.TryCreateHeaderMap(Values(rows[0]), out var headerMap))
            {
                continue;
            }

            matchingTableCount++;
            for (var rowIndex = 1; rowIndex < rows.Count; rowIndex++)
            {
                var location = "Table " + tableNumber + ", row " + (rowIndex + 1);
                var item = StartupRowParser.Parse(Values(rows[rowIndex]), headerMap, location);
                if (item != null)
                {
                    items.Add(item);
                }
            }
        }

        if (matchingTableCount == 0)
        {
            throw new StartupFormatException("No Word table contains all required startup headers.");
        }

        return items;
    }

    private static IReadOnlyList<string> Values(TableRow row)
    {
        return row.Elements<TableCell>().Select(cell => cell.InnerText.Trim()).ToList();
    }

    private static bool IsPackageFailure(Exception exception)
    {
        return exception is OpenXmlPackageException ||
               exception is InvalidDataException ||
               exception is IOException ||
               exception is FormatException;
    }
}
