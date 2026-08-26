using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace KLCode.FamilyStudio.Core.Indexing;

public sealed class LibraryFileCandidate
{
    public LibraryFileCandidate(string filePath, long fileSize, DateTimeOffset modifiedUtc)
    {
        FilePath = filePath ?? throw new ArgumentNullException(nameof(filePath));
        FileSize = fileSize >= 0 ? fileSize : throw new ArgumentOutOfRangeException(nameof(fileSize));
        ModifiedUtc = modifiedUtc;
    }

    public string FilePath { get; }
    public long FileSize { get; }
    public DateTimeOffset ModifiedUtc { get; }
}

public sealed class IndexedFileState
{
    public IndexedFileState(string filePath, long fileSize, DateTimeOffset modifiedUtc, string? fileHash)
    {
        FilePath = filePath ?? throw new ArgumentNullException(nameof(filePath));
        FileSize = fileSize;
        ModifiedUtc = modifiedUtc;
        FileHash = fileHash;
    }

    public string FilePath { get; }
    public long FileSize { get; }
    public DateTimeOffset ModifiedUtc { get; }
    public string? FileHash { get; }
}

public sealed class LibraryScanIssue
{
    public LibraryScanIssue(string path, string message)
    {
        Path = path;
        Message = message;
    }

    public string Path { get; }
    public string Message { get; }
}

public sealed class LibraryScanResult
{
    public LibraryScanResult(IReadOnlyList<LibraryFileCandidate> files, IReadOnlyList<LibraryScanIssue> issues)
    {
        Files = Copy(files, nameof(files));
        Issues = Copy(issues, nameof(issues));
    }

    public IReadOnlyList<LibraryFileCandidate> Files { get; }
    public IReadOnlyList<LibraryScanIssue> Issues { get; }

    private static IReadOnlyList<T> Copy<T>(IReadOnlyList<T> values, string parameterName)
    {
        if (values is null)
        {
            throw new ArgumentNullException(parameterName);
        }

        T[] copy = values.ToArray();
        if (copy.Any(value => value is null))
        {
            throw new ArgumentException("Collection values cannot contain null entries.", parameterName);
        }

        return new ReadOnlyCollection<T>(copy);
    }
}

public enum IndexDecision
{
    New,
    Changed,
    Unchanged
}

public sealed class ThumbnailResult
{
    private ThumbnailResult(string? filePath)
    {
        FilePath = filePath;
    }

    public static ThumbnailResult None { get; } = new ThumbnailResult(null);
    public string? FilePath { get; }

    public static ThumbnailResult Created(string filePath)
    {
        if (string.IsNullOrWhiteSpace(filePath))
        {
            throw new ArgumentException("A thumbnail path is required.", nameof(filePath));
        }

        return new ThumbnailResult(filePath);
    }
}
