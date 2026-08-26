using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace KLCode.FamilyStudio.Core.Configuration;

public sealed class JsonLibraryConfigurationProvider
{
    private const long MaximumConfigurationBytes = 1024 * 1024;

    public LibraryConfiguration Load(string configurationPath)
    {
        string fullPath = ValidateConfigurationPath(configurationPath);
        string baseDirectory = Path.GetDirectoryName(fullPath)!;

        try
        {
            ConfigurationDocument? document = JsonSerializer.Deserialize<ConfigurationDocument>(
                File.ReadAllText(fullPath),
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            return CreateConfiguration(document, baseDirectory);
        }
        catch (ConfigurationException)
        {
            throw;
        }
        catch (Exception exception) when (exception is IOException || exception is JsonException)
        {
            throw new ConfigurationException("Family Studio configuration could not be read.", exception);
        }
    }

    private static string ValidateConfigurationPath(string path)
    {
        if (string.IsNullOrWhiteSpace(path))
        {
            throw new ConfigurationException("A configuration file path is required.");
        }

        string fullPath = Path.GetFullPath(path);
        FileInfo file = new FileInfo(fullPath);
        if (!file.Exists)
        {
            throw new ConfigurationException("The Family Studio configuration file does not exist.");
        }

        if (file.Length > MaximumConfigurationBytes)
        {
            throw new ConfigurationException("The Family Studio configuration file exceeds 1 MB.");
        }

        return fullPath;
    }

    private static LibraryConfiguration CreateConfiguration(ConfigurationDocument? document, string baseDirectory)
    {
        if (document?.LibraryRoots is null)
        {
            throw new ConfigurationException("The configuration must declare libraryRoots.");
        }

        LibraryRoot[] roots = document.LibraryRoots.Select(root => CreateRoot(root, baseDirectory)).ToArray();
        if (!roots.Any(root => root.IsEnabled))
        {
            throw new ConfigurationException("At least one library root must be enabled.");
        }

        string databasePath = NormalizeRequiredPath(document.DatabasePath, baseDirectory, "databasePath");
        string thumbnailPath = NormalizeRequiredPath(document.ThumbnailDirectory, baseDirectory, "thumbnailDirectory");
        return new LibraryConfiguration(Array.AsReadOnly(roots), databasePath, thumbnailPath);
    }

    private static LibraryRoot CreateRoot(LibraryRootDocument root, string baseDirectory)
    {
        string path = NormalizeRequiredPath(root.Path, baseDirectory, "libraryRoots.path");
        return new LibraryRoot(path, root.Enabled, TrimToNull(root.Discipline), TrimToNull(root.DefaultStatus));
    }

    private static string NormalizeRequiredPath(string? path, string baseDirectory, string propertyName)
    {
        if (string.IsNullOrWhiteSpace(path))
        {
            throw new ConfigurationException(propertyName + " must be a non-empty path.");
        }

        string candidate = Path.IsPathRooted(path!) ? path! : Path.Combine(baseDirectory, path!);
        return Path.GetFullPath(candidate);
    }

    private static string? TrimToNull(string? value)
    {
        return string.IsNullOrWhiteSpace(value) ? null : value!.Trim();
    }

    private sealed class ConfigurationDocument
    {
        public List<LibraryRootDocument>? LibraryRoots { get; set; }
        public string? DatabasePath { get; set; }
        public string? ThumbnailDirectory { get; set; }
    }

    private sealed class LibraryRootDocument
    {
        public string? Path { get; set; }
        public bool Enabled { get; set; }
        public string? Discipline { get; set; }
        public string? DefaultStatus { get; set; }
    }
}
