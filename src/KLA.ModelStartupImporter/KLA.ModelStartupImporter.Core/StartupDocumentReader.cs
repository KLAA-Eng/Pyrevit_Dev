using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;

namespace KLA.ModelStartupImporter.Core;

public interface IStartupDocumentReader
{
    StartupDocumentModel Read(string sourcePath);
}

public sealed class StartupDocumentReader : IStartupDocumentReader
{
    private const long MaximumFileBytes = 25L * 1024L * 1024L;
    private readonly IReadOnlyDictionary<string, IStartupFormatReader> readers;
    private readonly IStartupFileAccess fileAccess;

    public StartupDocumentReader()
        : this(
            new IStartupFormatReader[] { new WordStartupReader(), new ExcelStartupReader() },
            new PhysicalStartupFileAccess())
    {
    }

    internal StartupDocumentReader(IStartupFileAccess fileAccess)
        : this(new IStartupFormatReader[] { new WordStartupReader(), new ExcelStartupReader() }, fileAccess)
    {
    }

    internal StartupDocumentReader(
        IEnumerable<IStartupFormatReader> readers,
        IStartupFileAccess fileAccess)
    {
        this.readers = readers.ToDictionary(reader => reader.Extension, StringComparer.OrdinalIgnoreCase);
        this.fileAccess = fileAccess ?? throw new ArgumentNullException(nameof(fileAccess));
    }

    public StartupDocumentModel Read(string sourcePath)
    {
        var fullPath = ValidatePath(sourcePath);
        var extension = Path.GetExtension(fullPath);
        if (!readers.TryGetValue(extension, out var reader))
        {
            throw new NotSupportedException("Only .docx and .xlsx startup documents are supported.");
        }

        if (!fileAccess.Exists(fullPath))
        {
            throw new FileNotFoundException("The startup document was not found.", fullPath);
        }

        var before = fileAccess.GetMetadata(fullPath);
        ValidateLength(before.Length);
        var bytes = fileAccess.ReadAllBytes(fullPath);
        var after = fileAccess.GetMetadata(fullPath);
        if (!before.Equals(after) || bytes.LongLength != before.Length)
        {
            throw new InvalidDataException("The startup document changed while it was being read. Try again after saving it.");
        }

        IReadOnlyList<StartupItem> items;
        using (var stream = new MemoryStream(bytes, writable: false))
        {
            items = reader.ReadItems(stream);
        }

        return new StartupDocumentModel(
            fullPath,
            reader.SourceType,
            before.ModifiedUtc,
            ComputeSha256(bytes),
            items);
    }

    private static string ValidatePath(string sourcePath)
    {
        if (string.IsNullOrWhiteSpace(sourcePath))
        {
            throw new ArgumentException("A startup document path is required.", nameof(sourcePath));
        }

        var fullPath = Path.GetFullPath(sourcePath);
        return fullPath;
    }

    private static void ValidateLength(long length)
    {
        if (length <= 0 || length > MaximumFileBytes)
        {
            throw new InvalidDataException("The startup document must be between 1 byte and 25 MiB.");
        }
    }

    private static string ComputeSha256(byte[] bytes)
    {
        using var sha256 = SHA256.Create();
        return string.Concat(sha256.ComputeHash(bytes).Select(value => value.ToString("X2")));
    }
}

internal interface IStartupFormatReader
{
    string Extension { get; }

    StartupSourceType SourceType { get; }

    IReadOnlyList<StartupItem> ReadItems(Stream source);
}
