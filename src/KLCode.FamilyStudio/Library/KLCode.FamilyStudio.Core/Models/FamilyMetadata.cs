using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace KLCode.FamilyStudio.Core.Models;

public sealed class FamilyParameter
{
    public FamilyParameter(string name, string? value, string? storageType, bool isTypeParameter)
    {
        Name = name ?? throw new ArgumentNullException(nameof(name));
        Value = value;
        StorageType = storageType;
        IsTypeParameter = isTypeParameter;
    }

    public string Name { get; }
    public string? Value { get; }
    public string? StorageType { get; }
    public bool IsTypeParameter { get; }
}

public sealed class FamilyMetadata
{
    public FamilyMetadata(
        string sourcePath,
        string displayName,
        string? category,
        string? revitVersion,
        IReadOnlyList<string> typeNames,
        IReadOnlyList<FamilyParameter> parameters,
        IReadOnlyList<string> tags,
        string? status,
        string? discipline)
    {
        SourcePath = sourcePath ?? throw new ArgumentNullException(nameof(sourcePath));
        DisplayName = displayName ?? throw new ArgumentNullException(nameof(displayName));
        Category = category;
        RevitVersion = revitVersion;
        TypeNames = Copy(typeNames, nameof(typeNames));
        Parameters = Copy(parameters, nameof(parameters));
        Tags = Copy(tags, nameof(tags));
        Status = status;
        Discipline = discipline;
    }

    public string SourcePath { get; }
    public string DisplayName { get; }
    public string? Category { get; }
    public string? RevitVersion { get; }
    public IReadOnlyList<string> TypeNames { get; }
    public IReadOnlyList<FamilyParameter> Parameters { get; }
    public IReadOnlyList<string> Tags { get; }
    public string? Status { get; }
    public string? Discipline { get; }

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
