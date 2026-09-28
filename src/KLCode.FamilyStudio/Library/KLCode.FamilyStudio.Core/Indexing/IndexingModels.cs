using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace KLCode.FamilyStudio.Core.Indexing;

public sealed class LibraryFileCandidate
{
    public LibraryFileCandidate(string filePath, long fileSize, DateTimeOffset modifiedUtc, string? fileHash = null)
    {
        FilePath = filePath ?? throw new ArgumentNullException(nameof(filePath));
        FileSize = fileSize >= 0 ? fileSize : throw new ArgumentOutOfRangeException(nameof(fileSize));
        ModifiedUtc = modifiedUtc;
        FileHash = fileHash;
    }

    public string FilePath { get; }
    public long FileSize { get; }
    public DateTimeOffset ModifiedUtc { get; }
    public string? FileHash { get; }
}

public sealed class IndexedFileState
{
    public IndexedFileState(string filePath, long fileSize, DateTimeOffset modifiedUtc, string? fileHash, string? thumbnailPath = null)
    {
        FilePath = filePath ?? throw new ArgumentNullException(nameof(filePath));
        FileSize = fileSize;
        ModifiedUtc = modifiedUtc;
        FileHash = fileHash;
        ThumbnailPath = thumbnailPath;
    }

    public string FilePath { get; }
    public long FileSize { get; }
    public DateTimeOffset ModifiedUtc { get; }
    public string? FileHash { get; }
    public string? ThumbnailPath { get; }
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
    private ThumbnailResult(string? filePath, IReadOnlyList<FamilyPreview> previews)
    {
        FilePath = filePath;
        Previews = Copy(previews, nameof(previews));
    }

    public static ThumbnailResult None { get; } = new ThumbnailResult(null, Array.Empty<FamilyPreview>());
    public string? FilePath { get; }
    public IReadOnlyList<FamilyPreview> Previews { get; }

    public static ThumbnailResult Created(string filePath)
    {
        return FromPreviews(new[] { new FamilyPreview(null, filePath) });
    }

    public static ThumbnailResult FromPreviews(IReadOnlyList<FamilyPreview> previews)
    {
        IReadOnlyList<FamilyPreview> copy = Copy(previews, nameof(previews));
        if (copy.Count == 0)
        {
            return None;
        }

        FamilyPreview primary = copy.FirstOrDefault(preview => preview.TypeName is null) ?? copy[0];
        return new ThumbnailResult(primary.FilePath, copy);
    }

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

public sealed class FamilyPreview
{
    public FamilyPreview(string? typeName, string filePath)
    {
        TypeName = string.IsNullOrWhiteSpace(typeName) ? null : typeName!.Trim();
        FilePath = string.IsNullOrWhiteSpace(filePath)
            ? throw new ArgumentException("A preview path is required.", nameof(filePath))
            : filePath;
    }

    public string? TypeName { get; }
    public string FilePath { get; }
}
