using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;

namespace KLA.ModelStartupImporter.Core;

public enum StartupSourceType
{
    Word,
    Excel,
}

public enum StartupItemCategory
{
    Detail,
    GeneralNote,
    Schedule,
    Other,
}

public sealed class StartupItem
{
    public StartupItem(
        string itemId,
        string title,
        StartupItemCategory category,
        bool isSelected,
        string engineerComment,
        string sourceLocation,
        string placementHint)
    {
        ItemId = Required(itemId, nameof(itemId));
        Title = Required(title, nameof(title));
        Category = category;
        IsSelected = isSelected;
        EngineerComment = engineerComment?.Trim() ?? string.Empty;
        SourceLocation = Required(sourceLocation, nameof(sourceLocation));
        PlacementHint = placementHint?.Trim() ?? string.Empty;
    }

    public string ItemId { get; }

    public string Title { get; }

    public StartupItemCategory Category { get; }

    public bool IsSelected { get; }

    public string EngineerComment { get; }

    public string SourceLocation { get; }

    public string PlacementHint { get; }

    private static string Required(string value, string parameterName)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new ArgumentException("A non-empty value is required.", parameterName);
        }

        return value.Trim();
    }
}

public sealed class StartupDocumentModel
{
    public StartupDocumentModel(
        string sourcePath,
        StartupSourceType sourceType,
        DateTime modifiedUtc,
        string fileHash,
        IEnumerable<StartupItem> items)
    {
        if (string.IsNullOrWhiteSpace(sourcePath))
        {
            throw new ArgumentException("A source path is required.", nameof(sourcePath));
        }

        if (modifiedUtc.Kind != DateTimeKind.Utc)
        {
            throw new ArgumentException("The modified time must be UTC.", nameof(modifiedUtc));
        }

        if (fileHash == null || fileHash.Length != 64 || fileHash.Any(character => !Uri.IsHexDigit(character)))
        {
            throw new ArgumentException("A SHA-256 file hash is required.", nameof(fileHash));
        }

        SourcePath = Path.GetFullPath(sourcePath);
        SourceType = sourceType;
        ModifiedUtc = modifiedUtc;
        FileHash = fileHash.ToUpperInvariant();
        Items = Copy(items, nameof(items));
    }

    public string SourcePath { get; }

    public StartupSourceType SourceType { get; }

    public DateTime ModifiedUtc { get; }

    public string FileHash { get; }

    public IReadOnlyList<StartupItem> Items { get; }

    private static IReadOnlyList<StartupItem> Copy(IEnumerable<StartupItem> items, string parameterName)
    {
        if (items == null)
        {
            throw new ArgumentNullException(parameterName);
        }

        var values = items.ToList();
        if (values.Any(item => item == null))
        {
            throw new ArgumentException("Items cannot contain null values.", parameterName);
        }

        return new ReadOnlyCollection<StartupItem>(values);
    }
}

public sealed class CatalogItem
{
    public CatalogItem(
        string itemId,
        string sourceViewName,
        string targetName,
        StartupItemCategory contentType,
        IEnumerable<string>? requiredTextTypeNames = null,
        IEnumerable<string>? requiredLineStyleNames = null)
    {
        ItemId = Required(itemId, nameof(itemId));
        SourceViewName = Required(sourceViewName, nameof(sourceViewName));
        TargetName = Required(targetName, nameof(targetName));
        ContentType = contentType;
        RequiredTextTypeNames = CopyNames(requiredTextTypeNames);
        RequiredLineStyleNames = CopyNames(requiredLineStyleNames);
    }

    public string ItemId { get; }

    public string SourceViewName { get; }

    public string TargetName { get; }

    public StartupItemCategory ContentType { get; }

    public IReadOnlyList<string> RequiredTextTypeNames { get; }

    public IReadOnlyList<string> RequiredLineStyleNames { get; }

    private static string Required(string value, string parameterName)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new ArgumentException("A non-empty value is required.", parameterName);
        }

        return value.Trim();
    }

    private static IReadOnlyList<string> CopyNames(IEnumerable<string>? values)
    {
        var names = (values ?? Array.Empty<string>())
            .Select(value => Required(value, nameof(values)))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();
        return new ReadOnlyCollection<string>(names);
    }
}

public sealed class ImportMatch
{
    public ImportMatch(StartupItem item, CatalogItem catalogItem)
    {
        Item = item ?? throw new ArgumentNullException(nameof(item));
        CatalogItem = catalogItem ?? throw new ArgumentNullException(nameof(catalogItem));
    }

    public StartupItem Item { get; }

    public CatalogItem CatalogItem { get; }
}

public sealed class ImportPlan
{
    public ImportPlan(
        IEnumerable<ImportMatch> matches,
        IEnumerable<StartupItem> skippedItems,
        IEnumerable<StartupItem> unknownItems,
        IEnumerable<StartupItem> duplicateItems)
    {
        Matches = Copy(matches, nameof(matches));
        SkippedItems = Copy(skippedItems, nameof(skippedItems));
        UnknownItems = Copy(unknownItems, nameof(unknownItems));
        DuplicateItems = Copy(duplicateItems, nameof(duplicateItems));
    }

    public IReadOnlyList<ImportMatch> Matches { get; }

    public IReadOnlyList<StartupItem> SkippedItems { get; }

    public IReadOnlyList<StartupItem> UnknownItems { get; }

    public IReadOnlyList<StartupItem> DuplicateItems { get; }

    public bool HasBlockingIssues => UnknownItems.Count > 0 || DuplicateItems.Count > 0;

    private static IReadOnlyList<T> Copy<T>(IEnumerable<T> values, string parameterName)
        where T : class
    {
        if (values == null)
        {
            throw new ArgumentNullException(parameterName);
        }

        var copy = values.ToList();
        if (copy.Any(value => value == null))
        {
            throw new ArgumentException("Values cannot contain null entries.", parameterName);
        }

        return new ReadOnlyCollection<T>(copy);
    }
}
