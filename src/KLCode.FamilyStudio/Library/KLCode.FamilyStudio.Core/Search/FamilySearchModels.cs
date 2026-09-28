using System;

namespace KLCode.FamilyStudio.Core.Search;

public sealed class FamilySearchQuery
{
    public FamilySearchQuery(string? text, string? category, string? status, string? discipline, int limit)
        : this(text, category, status, discipline, null, null, null, false, limit)
    {
    }

    public FamilySearchQuery(
        string? text,
        string? category,
        string? status,
        string? discipline,
        string? typeName,
        string? parameterName,
        string? rootPath,
        bool duplicatesOnly,
        int limit)
    {
        Text = text;
        Category = category;
        Status = status;
        Discipline = discipline;
        TypeName = typeName;
        ParameterName = parameterName;
        RootPath = rootPath;
        DuplicatesOnly = duplicatesOnly;
        Limit = limit;
    }

    public string? Text { get; }
    public string? Category { get; }
    public string? Status { get; }
    public string? Discipline { get; }
    public string? TypeName { get; }
    public string? ParameterName { get; }
    public string? RootPath { get; }
    public bool DuplicatesOnly { get; }
    public int Limit { get; }
}

public sealed class FamilyCatalogFilterOptions
{
    public FamilyCatalogFilterOptions(
        System.Collections.Generic.IReadOnlyList<string> categories,
        System.Collections.Generic.IReadOnlyList<string> typeNames,
        System.Collections.Generic.IReadOnlyList<string> parameterNames,
        System.Collections.Generic.IReadOnlyList<string> rootPaths)
    {
        Categories = categories ?? throw new ArgumentNullException(nameof(categories));
        TypeNames = typeNames ?? throw new ArgumentNullException(nameof(typeNames));
        ParameterNames = parameterNames ?? throw new ArgumentNullException(nameof(parameterNames));
        RootPaths = rootPaths ?? throw new ArgumentNullException(nameof(rootPaths));
    }

    public System.Collections.Generic.IReadOnlyList<string> Categories { get; }
    public System.Collections.Generic.IReadOnlyList<string> TypeNames { get; }
    public System.Collections.Generic.IReadOnlyList<string> ParameterNames { get; }
    public System.Collections.Generic.IReadOnlyList<string> RootPaths { get; }
}

public sealed class FamilySearchResult
{
    public FamilySearchResult(
        long id,
        string familyName,
        string filePath,
        string? category,
        string? status,
        string? discipline,
        string? thumbnailPath,
        int exactDuplicateCount = 1,
        int nameVariantCount = 1,
        string? fileHash = null,
        DateTimeOffset? modifiedUtc = null,
        string? revitVersion = null)
    {
        Id = id;
        FamilyName = familyName;
        FilePath = filePath;
        Category = category;
        Status = status;
        Discipline = discipline;
        ThumbnailPath = thumbnailPath;
        ExactDuplicateCount = exactDuplicateCount;
        NameVariantCount = nameVariantCount;
        FileHash = fileHash;
        ModifiedUtc = modifiedUtc;
        RevitVersion = revitVersion;
    }

    public long Id { get; }
    public string FamilyName { get; }
    public string FilePath { get; }
    public string? Category { get; }
    public string? Status { get; }
    public string? Discipline { get; }
    public string? ThumbnailPath { get; }
    public int ExactDuplicateCount { get; }
    public int NameVariantCount { get; }
    public string? FileHash { get; }
    public DateTimeOffset? ModifiedUtc { get; }
    public string? RevitVersion { get; }
    public bool HasExactDuplicates => ExactDuplicateCount > 1;
    public bool HasNameVariants => NameVariantCount > 1;
    public string DuplicateLabel => HasExactDuplicates
        ? "Exact copy (" + ExactDuplicateCount + " paths)"
        : HasNameVariants
            ? "Same-name variant (" + NameVariantCount + " versions)"
            : "Unique";
    public string DisplayLabel => FamilyName +
        (string.IsNullOrWhiteSpace(Category) ? string.Empty : "  •  " + Category) +
        (HasExactDuplicates || HasNameVariants ? "  •  " + DuplicateLabel : string.Empty);
}
