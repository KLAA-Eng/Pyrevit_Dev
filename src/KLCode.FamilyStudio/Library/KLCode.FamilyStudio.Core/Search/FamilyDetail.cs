using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using KLCode.FamilyStudio.Core.Models;

namespace KLCode.FamilyStudio.Core.Search;

public enum FamilyUseAction
{
    Loaded,
    Placed,
}

public sealed class FamilyTypeDetail
{
    public FamilyTypeDetail(string name, IReadOnlyList<FamilyParameter> parameters)
    {
        Name = string.IsNullOrWhiteSpace(name)
            ? throw new ArgumentException("A family type name is required.", nameof(name))
            : name.Trim();
        Parameters = Copy(parameters, nameof(parameters));
    }

    public string Name { get; }
    public IReadOnlyList<FamilyParameter> Parameters { get; }

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

public sealed class FamilyDetail
{
    public FamilyDetail(
        FamilySearchResult summary,
        IReadOnlyList<FamilyTypeDetail> types,
        IReadOnlyList<FamilyParameter> parameters,
        IReadOnlyList<string> tags,
        bool isFavorite,
        DateTimeOffset? lastUsedUtc)
    {
        Summary = summary ?? throw new ArgumentNullException(nameof(summary));
        Types = Copy(types, nameof(types));
        Parameters = Copy(parameters, nameof(parameters));
        Tags = Copy(tags, nameof(tags));
        IsFavorite = isFavorite;
        LastUsedUtc = lastUsedUtc;
    }

    public FamilySearchResult Summary { get; }
    public IReadOnlyList<FamilyTypeDetail> Types { get; }
    public IReadOnlyList<FamilyParameter> Parameters { get; }
    public IReadOnlyList<string> Tags { get; }
    public bool IsFavorite { get; }
    public DateTimeOffset? LastUsedUtc { get; }

    private static IReadOnlyList<T> Copy<T>(IReadOnlyList<T> values, string parameterName)
    {
        if (values is null)
        {
            throw new ArgumentNullException(nameof(values));
        }

        T[] copy = values.ToArray();
        if (copy.Any(value => value is null))
        {
            throw new ArgumentException("Collection values cannot contain null entries.", parameterName);
        }

        return new ReadOnlyCollection<T>(copy);
    }
}
