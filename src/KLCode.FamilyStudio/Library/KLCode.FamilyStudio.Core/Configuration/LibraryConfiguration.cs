using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace KLCode.FamilyStudio.Core.Configuration;

public sealed class LibraryRoot
{
    public LibraryRoot(string path, bool isEnabled, string? discipline, string? defaultStatus)
    {
        Path = path ?? throw new ArgumentNullException(nameof(path));
        IsEnabled = isEnabled;
        Discipline = discipline;
        DefaultStatus = defaultStatus;
    }

    public string Path { get; }
    public bool IsEnabled { get; }
    public string? Discipline { get; }
    public string? DefaultStatus { get; }
}

public sealed class LibraryConfiguration
{
    public LibraryConfiguration(
        IReadOnlyList<LibraryRoot> libraryRoots,
        string databasePath,
        string thumbnailDirectory)
    {
        if (libraryRoots is null)
        {
            throw new ArgumentNullException(nameof(libraryRoots));
        }

        LibraryRoot[] roots = libraryRoots.ToArray();
        if (roots.Any(root => root is null))
        {
            throw new ArgumentException("Library roots cannot contain null values.", nameof(libraryRoots));
        }

        LibraryRoots = new ReadOnlyCollection<LibraryRoot>(roots);
        DatabasePath = databasePath ?? throw new ArgumentNullException(nameof(databasePath));
        ThumbnailDirectory = thumbnailDirectory ?? throw new ArgumentNullException(nameof(thumbnailDirectory));
    }

    public IReadOnlyList<LibraryRoot> LibraryRoots { get; }
    public string DatabasePath { get; }
    public string ThumbnailDirectory { get; }
}

public sealed class ConfigurationException : Exception
{
    public ConfigurationException(string message)
        : base(message)
    {
    }

    public ConfigurationException(string message, Exception innerException)
        : base(message, innerException)
    {
    }
}
