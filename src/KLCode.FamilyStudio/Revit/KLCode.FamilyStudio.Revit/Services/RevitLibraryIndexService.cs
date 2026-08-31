using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using System.Text;
using System.Threading;
using KLCode.FamilyStudio.Core.Configuration;
using KLCode.FamilyStudio.Core.Indexing;
using KLCode.FamilyStudio.Database.Repositories;

namespace KLCode.FamilyStudio.Revit.Services;

internal sealed class RevitLibraryIndexService
{
    private readonly Autodesk.Revit.ApplicationServices.Application _application;

    internal RevitLibraryIndexService(Autodesk.Revit.ApplicationServices.Application application)
    {
        _application = application ?? throw new ArgumentNullException(nameof(application));
    }

    internal IndexRunSummary Refresh(string configurationPath, string expectedDatabasePath, CancellationToken cancellationToken)
    {
        LibraryConfiguration configuration = new RevitLibraryConfigurationProvider().Load(configurationPath);
        string configuredDatabasePath = Path.GetFullPath(configuration.DatabasePath);
        string activeDatabasePath = Path.GetFullPath(expectedDatabasePath);
        if (!string.Equals(
                configuredDatabasePath,
                activeDatabasePath,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new ConfigurationException(
                "The selected configuration must use the Family Studio database currently open in Revit.\n\n" +
                "Active database:\n" + activeDatabasePath + "\n\n" +
                "Configuration database:\n" + configuredDatabasePath);
        }

        using SqliteFamilyRepository repository = new SqliteFamilyRepository(configuration.DatabasePath);
        LibraryIndexer indexer = new LibraryIndexer(
            new FileSystemLibraryScanner(),
            new RevitFullRefreshChangeDetector(),
            new RevitFamilyMetadataExtractor(_application),
            new RevitThumbnailService(_application),
            repository,
            () => DateTimeOffset.UtcNow);
        return indexer.RunAsync(configuration, cancellationToken).GetAwaiter().GetResult();
    }
}

internal sealed class RevitLibraryConfigurationProvider
{
    internal LibraryConfiguration Load(string configurationPath)
    {
        if (string.IsNullOrWhiteSpace(configurationPath))
        {
            throw new ConfigurationException("A Family Studio configuration path is required.");
        }

        string fullPath = Path.GetFullPath(configurationPath);
        if (!File.Exists(fullPath))
        {
            throw new ConfigurationException("The Family Studio configuration file does not exist.");
        }

        if (new FileInfo(fullPath).Length > 1024 * 1024)
        {
            throw new ConfigurationException("The Family Studio configuration file exceeds 1 MB.");
        }

        try
        {
            using FileStream stream = File.OpenRead(fullPath);
            var serializer = new DataContractJsonSerializer(typeof(ConfigurationDocument));
            var document = (ConfigurationDocument?)serializer.ReadObject(stream);
            return CreateConfiguration(document, Path.GetDirectoryName(fullPath)!);
        }
        catch (ConfigurationException)
        {
            throw;
        }
        catch (Exception exception) when (exception is IOException || exception is SerializationException)
        {
            throw new ConfigurationException("The Family Studio configuration could not be read.", exception);
        }
    }

    private static LibraryConfiguration CreateConfiguration(ConfigurationDocument? document, string baseDirectory)
    {
        if (document?.LibraryRoots is null || document.LibraryRoots.Count == 0)
        {
            throw new ConfigurationException("The configuration must declare libraryRoots.");
        }

        LibraryRoot[] roots = document.LibraryRoots.Select(root => new LibraryRoot(
            ResolvePath(root.Path, baseDirectory, "libraryRoots.path"),
            root.Enabled,
            TrimToNull(root.Discipline),
            TrimToNull(root.DefaultStatus))).ToArray();
        if (!roots.Any(root => root.IsEnabled))
        {
            throw new ConfigurationException("At least one library root must be enabled.");
        }

        return new LibraryConfiguration(
            roots,
            ResolvePath(document.DatabasePath, baseDirectory, "databasePath"),
            ResolvePath(document.ThumbnailDirectory, baseDirectory, "thumbnailDirectory"));
    }

    private static string ResolvePath(string? path, string baseDirectory, string name)
    {
        if (string.IsNullOrWhiteSpace(path))
        {
            throw new ConfigurationException(name + " must be a non-empty path.");
        }

        return Path.GetFullPath(Path.IsPathRooted(path) ? path : Path.Combine(baseDirectory, path));
    }

    private static string? TrimToNull(string? value)
    {
        return string.IsNullOrWhiteSpace(value) ? null : value!.Trim();
    }

    [DataContract]
    private sealed class ConfigurationDocument
    {
        [DataMember(Name = "libraryRoots")]
        public List<LibraryRootDocument>? LibraryRoots { get; set; }

        [DataMember(Name = "databasePath")]
        public string? DatabasePath { get; set; }

        [DataMember(Name = "thumbnailDirectory")]
        public string? ThumbnailDirectory { get; set; }
    }

    [DataContract]
    private sealed class LibraryRootDocument
    {
        [DataMember(Name = "path")]
        public string? Path { get; set; }

        [DataMember(Name = "enabled")]
        public bool Enabled { get; set; }

        [DataMember(Name = "discipline")]
        public string? Discipline { get; set; }

        [DataMember(Name = "defaultStatus")]
        public string? DefaultStatus { get; set; }
    }
}
