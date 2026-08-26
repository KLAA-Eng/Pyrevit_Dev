using System;

namespace KLCode.FamilyStudio.Core.Search;

public sealed class FamilySearchQuery
{
    public FamilySearchQuery(string? text, string? category, string? status, string? discipline, int limit)
    {
        Text = text;
        Category = category;
        Status = status;
        Discipline = discipline;
        Limit = limit;
    }

    public string? Text { get; }
    public string? Category { get; }
    public string? Status { get; }
    public string? Discipline { get; }
    public int Limit { get; }
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
        string? thumbnailPath)
    {
        Id = id;
        FamilyName = familyName;
        FilePath = filePath;
        Category = category;
        Status = status;
        Discipline = discipline;
        ThumbnailPath = thumbnailPath;
    }

    public long Id { get; }
    public string FamilyName { get; }
    public string FilePath { get; }
    public string? Category { get; }
    public string? Status { get; }
    public string? Discipline { get; }
    public string? ThumbnailPath { get; }
}
