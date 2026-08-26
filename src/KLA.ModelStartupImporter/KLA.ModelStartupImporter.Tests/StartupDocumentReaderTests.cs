using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Spreadsheet;
using DocumentFormat.OpenXml.Wordprocessing;
using System.IO.Compression;
using KLA.ModelStartupImporter.Core;
using W = DocumentFormat.OpenXml.Wordprocessing;

namespace KLA.ModelStartupImporter.Tests;

public sealed class StartupDocumentReaderTests : IDisposable
{
    private readonly string fixtureDirectory = Path.Combine(Path.GetTempPath(), "kla-startup-importer-tests", Guid.NewGuid().ToString("N"));

    [Fact]
    public void Read_WordTable_ReturnsNormalizedItemsAndSourceMetadata()
    {
        var path = Path.Combine(fixtureDirectory, "startup.docx");
        CreateWordDocument(path, new[]
        {
            Headers,
            new[] { "D-001", "Base Plate", "Detail", "x", "Coordinate with arch", "A5.1 / 3" },
            new[] { "GN-001", "Notes", "General Note", "no", "", "" },
        });

        var document = new StartupDocumentReader().Read(path);

        Assert.Equal(StartupSourceType.Word, document.SourceType);
        Assert.Equal(Path.GetFullPath(path), document.SourcePath);
        Assert.Matches("^[A-F0-9]{64}$", document.FileHash);
        Assert.Collection(
            document.Items,
            first =>
            {
                Assert.Equal("D-001", first.ItemId);
                Assert.True(first.IsSelected);
                Assert.Equal(StartupItemCategory.Detail, first.Category);
                Assert.Equal("Table 1, row 2", first.SourceLocation);
                Assert.Equal("A5.1 / 3", first.PlacementHint);
            },
            second => Assert.False(second.IsSelected));
    }

    [Fact]
    public void Read_ExcelWorksheet_ReturnsCheckedAndUncheckedRows()
    {
        var path = Path.Combine(fixtureDirectory, "startup.xlsx");
        CreateExcelDocument(path, new[]
        {
            Headers,
            new[] { "D-001", "Base Plate", "detail", "TRUE", "", "" },
            new[] { "D-002", "Anchor", "detail", "0", "review", "" },
            new[] { "", "", "", "", "", "" },
        });

        var document = new StartupDocumentReader().Read(path);

        Assert.Equal(StartupSourceType.Excel, document.SourceType);
        Assert.Equal(2, document.Items.Count);
        Assert.True(document.Items[0].IsSelected);
        Assert.False(document.Items[1].IsSelected);
        Assert.Equal("Checklist!A2", document.Items[0].SourceLocation);
    }

    [Fact]
    public void Read_RejectsUnsupportedMissingAndMalformedInputs()
    {
        Directory.CreateDirectory(fixtureDirectory);
        var unsupported = Path.Combine(fixtureDirectory, "startup.xlsm");
        File.WriteAllText(unsupported, "not a workbook");
        var malformed = Path.Combine(fixtureDirectory, "startup.docx");
        File.WriteAllText(malformed, "not a document");

        Assert.Throws<NotSupportedException>(() => new StartupDocumentReader().Read(unsupported));
        Assert.Throws<FileNotFoundException>(() => new StartupDocumentReader().Read(Path.Combine(fixtureDirectory, "missing.xlsx")));
        Assert.Throws<InvalidDataException>(() => new StartupDocumentReader().Read(malformed));
    }

    [Fact]
    public void Read_RejectsRowsWithInvalidSelectionOrCategory()
    {
        var path = Path.Combine(fixtureDirectory, "invalid.xlsx");
        CreateExcelDocument(path, new[]
        {
            Headers,
            new[] { "D-001", "Base Plate", "detail", "maybe", "", "" },
        });

        var selectionException = Assert.Throws<InvalidDataException>(() => new StartupDocumentReader().Read(path));
        Assert.Contains("selection", selectionException.Message, StringComparison.OrdinalIgnoreCase);

        CreateExcelDocument(path, new[]
        {
            Headers,
            new[] { "D-001", "Base Plate", "unsupported", "x", "", "" },
        });

        var categoryException = Assert.Throws<InvalidDataException>(() => new StartupDocumentReader().Read(path));
        Assert.Contains("category", categoryException.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void Read_ExcelSharedStringsAndCellReferences_AreResolvedByColumn()
    {
        var path = Path.Combine(fixtureDirectory, "shared-strings.xlsx");
        CreateSharedStringExcelDocument(path);

        var document = new StartupDocumentReader().Read(path);

        var item = Assert.Single(document.Items);
        Assert.Equal("D-010", item.ItemId);
        Assert.Equal("Shared title", item.Title);
        Assert.Equal(StartupItemCategory.Detail, item.Category);
        Assert.True(item.IsSelected);
    }

    [Fact]
    public void Read_DocumentsWithoutChecklistHeaders_FailClearly()
    {
        var wordPath = Path.Combine(fixtureDirectory, "no-checklist.docx");
        CreateWordDocument(wordPath, new[] { new[] { "Unrelated", "Table" } });
        var excelPath = Path.Combine(fixtureDirectory, "no-checklist.xlsx");
        CreateExcelDocument(excelPath, new[] { new[] { "Unrelated", "Sheet" } });

        Assert.Contains(
            "required startup headers",
            Assert.Throws<InvalidDataException>(() => new StartupDocumentReader().Read(wordPath)).Message,
            StringComparison.OrdinalIgnoreCase);
        Assert.Contains(
            "required startup headers",
            Assert.Throws<InvalidDataException>(() => new StartupDocumentReader().Read(excelPath)).Message,
            StringComparison.OrdinalIgnoreCase);
    }

    [Theory]
    [InlineData("malformed.docx")]
    [InlineData("malformed.xlsx")]
    public void Read_ZipValidMalformedOpenXmlPackage_IsNormalized(string fileName)
    {
        var path = Path.Combine(fixtureDirectory, fileName);
        CreateMalformedPackage(path);

        var exception = Assert.Throws<InvalidDataException>(() => new StartupDocumentReader().Read(path));

        Assert.NotNull(exception.InnerException);
        Assert.Contains("could not be read", exception.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void Read_WhenFileMetadataChangesDuringSnapshot_FailsClosed()
    {
        var timestamp = new DateTime(2026, 8, 26, 12, 0, 0, DateTimeKind.Utc);
        var fileAccess = new ChangingStartupFileAccess(
            new byte[] { 1, 2, 3 },
            new StartupFileMetadata(3, timestamp),
            new StartupFileMetadata(4, timestamp.AddSeconds(1)));
        var reader = new StartupDocumentReader(fileAccess);

        var exception = Assert.Throws<InvalidDataException>(() => reader.Read("/virtual/startup.xlsx"));

        Assert.Contains("changed while it was being read", exception.Message, StringComparison.OrdinalIgnoreCase);
    }

    public void Dispose()
    {
        if (Directory.Exists(fixtureDirectory))
        {
            Directory.Delete(fixtureDirectory, recursive: true);
        }
    }

    private static readonly string[] Headers =
    {
        "ItemId", "Title", "Category", "Selected", "EngineerComment", "PlacementHint",
    };

    private static void CreateWordDocument(string path, IEnumerable<string[]> rows)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        using var document = WordprocessingDocument.Create(path, WordprocessingDocumentType.Document);
        var mainPart = document.AddMainDocumentPart();
        mainPart.Document = new W.Document(new Body(new W.Table(rows.Select(CreateWordRow))));
        mainPart.Document.Save();
    }

    private static TableRow CreateWordRow(string[] values)
    {
        return new TableRow(values.Select(value => new TableCell(new Paragraph(new W.Run(new W.Text(value))))));
    }

    private static void CreateExcelDocument(string path, IEnumerable<string[]> rows)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        using var document = SpreadsheetDocument.Create(path, SpreadsheetDocumentType.Workbook);
        var workbookPart = document.AddWorkbookPart();
        workbookPart.Workbook = new Workbook();
        var worksheetPart = workbookPart.AddNewPart<WorksheetPart>();
        worksheetPart.Worksheet = new Worksheet(new SheetData(rows.Select(CreateSpreadsheetRow)));
        var sheets = workbookPart.Workbook.AppendChild(new Sheets());
        sheets.Append(new Sheet
        {
            Id = workbookPart.GetIdOfPart(worksheetPart),
            SheetId = 1,
            Name = "Checklist",
        });
        workbookPart.Workbook.Save();
    }

    private static void CreateSharedStringExcelDocument(string path)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        using var document = SpreadsheetDocument.Create(path, SpreadsheetDocumentType.Workbook);
        var workbookPart = document.AddWorkbookPart();
        workbookPart.Workbook = new Workbook();
        var sharedStrings = workbookPart.AddNewPart<SharedStringTablePart>();
        var values = Headers.Concat(new[] { "D-010", "Shared title", "detail", "yes", "", "" }).ToArray();
        sharedStrings.SharedStringTable = new SharedStringTable(
            values.Select(value => new SharedStringItem(new DocumentFormat.OpenXml.Spreadsheet.Text(value))));
        var worksheetPart = workbookPart.AddNewPart<WorksheetPart>();
        worksheetPart.Worksheet = new Worksheet(new SheetData(
            SharedStringRow(1, Enumerable.Range(0, Headers.Length).ToArray()),
            SharedStringRow(2, Enumerable.Range(Headers.Length, Headers.Length).ToArray())));
        workbookPart.Workbook.AppendChild(new Sheets()).Append(new Sheet
        {
            Id = workbookPart.GetIdOfPart(worksheetPart),
            SheetId = 1,
            Name = "Shared",
        });
        workbookPart.Workbook.Save();
    }

    private static Row SharedStringRow(uint rowIndex, IReadOnlyList<int> indexes)
    {
        var cells = indexes.Select((index, column) => new Cell
        {
            CellReference = ((char)('A' + column)).ToString() + rowIndex,
            DataType = CellValues.SharedString,
            CellValue = new CellValue(index.ToString()),
        });
        return new Row(cells) { RowIndex = rowIndex };
    }

    private static void CreateMalformedPackage(string path)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        using var archive = ZipFile.Open(path, ZipArchiveMode.Create);
        var isWord = Path.GetExtension(path).Equals(".docx", StringComparison.OrdinalIgnoreCase);
        var folder = isWord ? "word" : "xl";
        var contentType = isWord
            ? "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
            : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml";
        WriteArchiveEntry(
            archive,
            "[Content_Types].xml",
            "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">" +
            "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>" +
            "<Default Extension=\"xml\" ContentType=\"application/xml\"/>" +
            "<Override PartName=\"/" + folder + "/main1.xml\" ContentType=\"" + contentType + "\"/>" +
            "<Override PartName=\"/" + folder + "/main2.xml\" ContentType=\"" + contentType + "\"/>" +
            "</Types>");
        WriteArchiveEntry(
            archive,
            "_rels/.rels",
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">" +
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"/" + folder + "/main1.xml\"/>" +
            "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"/" + folder + "/main2.xml\"/>" +
            "</Relationships>");
        WriteArchiveEntry(archive, folder + "/main1.xml", "<root/>");
        WriteArchiveEntry(archive, folder + "/main2.xml", "<root/>");
    }

    private static void WriteArchiveEntry(ZipArchive archive, string name, string content)
    {
        using var writer = new StreamWriter(archive.CreateEntry(name).Open());
        writer.Write(content);
    }

    private sealed class ChangingStartupFileAccess : IStartupFileAccess
    {
        private readonly byte[] bytes;
        private readonly StartupFileMetadata before;
        private readonly StartupFileMetadata after;
        private int metadataReadCount;

        internal ChangingStartupFileAccess(
            byte[] bytes,
            StartupFileMetadata before,
            StartupFileMetadata after)
        {
            this.bytes = bytes;
            this.before = before;
            this.after = after;
        }

        public bool Exists(string path)
        {
            return true;
        }

        public StartupFileMetadata GetMetadata(string path)
        {
            metadataReadCount++;
            return metadataReadCount == 1 ? before : after;
        }

        public byte[] ReadAllBytes(string path)
        {
            return bytes.ToArray();
        }
    }

    private static Row CreateSpreadsheetRow(string[] values)
    {
        return new Row(values.Select(value => new Cell
        {
            DataType = CellValues.InlineString,
            InlineString = new InlineString(new DocumentFormat.OpenXml.Spreadsheet.Text(value)),
        }));
    }
}
